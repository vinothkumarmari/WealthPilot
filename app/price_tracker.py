"""Product price tracker — fetches prices from Indian e-commerce sites."""

import re
import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)
_HEADERS = {
    'User-Agent': _UA,
    'Accept-Language': 'en-IN,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
}

# Allowed domains (SSRF protection)
ALLOWED_DOMAINS = {
    'amazon.in', 'www.amazon.in',
    'flipkart.com', 'www.flipkart.com', 'dl.flipkart.com',
    'myntra.com', 'www.myntra.com',
    'ajio.com', 'www.ajio.com',
    'meesho.com', 'www.meesho.com',
    'croma.com', 'www.croma.com',
    'tatacliq.com', 'www.tatacliq.com',
    'snapdeal.com', 'www.snapdeal.com',
    'jiomart.com', 'www.jiomart.com',
    'nykaa.com', 'www.nykaa.com',
    'reliancedigital.in', 'www.reliancedigital.in',
    'vijaysales.com', 'www.vijaysales.com',
}

PLATFORM_COLORS = {
    'Amazon': '#FF9900',
    'Flipkart': '#2874F0',
    'Myntra': '#FF3F6C',
    'Ajio': '#1A1A2E',
    'Meesho': '#570A57',
    'Croma': '#00A859',
    'Tata CLiQ': '#CC0066',
    'Snapdeal': '#E40046',
    'JioMart': '#0078D4',
    'Nykaa': '#FC2779',
    'Reliance Digital': '#003DA5',
    'Vijay Sales': '#E31E24',
    'Other': '#6c757d',
}

PLATFORM_ICONS = {
    'Amazon': 'shopping_cart',
    'Flipkart': 'storefront',
    'Myntra': 'checkroom',
    'Ajio': 'style',
    'Meesho': 'local_mall',
    'Croma': 'devices',
    'Tata CLiQ': 'shopping_bag',
    'Snapdeal': 'sell',
    'JioMart': 'store',
    'Nykaa': 'spa',
    'Reliance Digital': 'phonelink',
    'Vijay Sales': 'tv',
    'Other': 'link',
}


def detect_platform(url):
    """Detect e-commerce platform from URL."""
    domain = urlparse(url).netloc.lower()
    if 'amazon' in domain:
        return 'Amazon'
    if 'flipkart' in domain:
        return 'Flipkart'
    if 'myntra' in domain:
        return 'Myntra'
    if 'ajio' in domain:
        return 'Ajio'
    if 'meesho' in domain:
        return 'Meesho'
    if 'croma' in domain:
        return 'Croma'
    if 'tatacliq' in domain:
        return 'Tata CLiQ'
    if 'snapdeal' in domain:
        return 'Snapdeal'
    if 'jiomart' in domain:
        return 'JioMart'
    if 'nykaa' in domain:
        return 'Nykaa'
    if 'reliancedigital' in domain:
        return 'Reliance Digital'
    if 'vijaysales' in domain:
        return 'Vijay Sales'
    return 'Other'


def is_allowed_url(url):
    """Validate URL is from an allowed e-commerce domain (SSRF protection)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        domain = parsed.netloc.lower().split(':')[0]  # strip port
        return domain in ALLOWED_DOMAINS
    except Exception:
        return False


def _clean_price(text):
    """Extract numeric price from text like '₹1,299.00' or 'Rs. 999'."""
    if not text:
        return None
    nums = re.sub(r'[^\d.]', '', text.replace(',', ''))
    try:
        val = float(nums)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None


def _fetch_page(url):
    """Fetch HTML content from URL with proper headers."""
    resp = requests.get(url, headers=_HEADERS, timeout=15, allow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser')


def _parse_amazon(soup):
    """Parse product info from Amazon.in page."""
    name = None
    price = None
    image = None

    el = soup.find('span', id='productTitle')
    if el:
        name = el.get_text(strip=True)

    # Try multiple price selectors (Amazon changes these)
    for selector in [
        ('span', {'class': 'a-price-whole'}),
        ('span', {'id': 'priceblock_dealprice'}),
        ('span', {'id': 'priceblock_ourprice'}),
        ('span', {'class': 'a-offscreen'}),
    ]:
        el = soup.find(*selector)
        if el:
            p = _clean_price(el.get_text())
            if p:
                price = p
                break

    el = soup.find('img', id='landingImage')
    if el:
        image = el.get('src')

    return name, price, image


def _parse_flipkart(soup):
    """Parse product info from Flipkart page."""
    name = None
    price = None
    image = None

    for cls in ['VU-ZEz', 'B_NuCI', 'yhB1nd']:
        el = soup.find('span', class_=cls) or soup.find('h1', class_=cls)
        if el:
            name = el.get_text(strip=True)
            break

    for cls in ['Nx9bqj CxhGGd', '_30jeq3 _16Jk6d', 'Nx9bqj']:
        el = soup.find('div', class_=cls)
        if el:
            p = _clean_price(el.get_text())
            if p:
                price = p
                break

    for cls in ['DByuf4', '_396cs4', '_2r_T1I']:
        el = soup.find('img', class_=cls)
        if el:
            image = el.get('src')
            break

    return name, price, image


def _parse_generic(soup):
    """Generic parser using og: meta tags — works for most e-commerce sites."""
    name = None
    price = None
    image = None

    el = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'og:title'})
    if el:
        name = el.get('content', '').strip()

    # Try og:price:amount or product:price:amount
    for prop in ['og:price:amount', 'product:price:amount', 'og:price']:
        el = soup.find('meta', property=prop)
        if el:
            p = _clean_price(el.get('content'))
            if p:
                price = p
                break

    el = soup.find('meta', property='og:image')
    if el:
        image = el.get('content')

    # Fallback: title tag
    if not name:
        el = soup.find('title')
        if el:
            name = el.get_text(strip=True)

    # Fallback: find price patterns in page
    if not price:
        for el in soup.find_all(['span', 'div', 'p', 'strong']):
            text = el.get_text(strip=True)
            if re.match(r'^[₹Rs.\s]*[\d,]+(\.\d{1,2})?$', text) and len(text) < 20:
                p = _clean_price(text)
                if p and 10 < p < 10_000_000:
                    price = p
                    break

    return name, price, image


def fetch_product_info(url):
    """Fetch product name, price, and image from a product URL.
    
    Returns dict with: name, price, image, platform, success, error.
    """
    platform = detect_platform(url)
    try:
        soup = _fetch_page(url)

        if platform == 'Amazon':
            name, price, image = _parse_amazon(soup)
        elif platform == 'Flipkart':
            name, price, image = _parse_flipkart(soup)
        else:
            name, price, image = (None, None, None)

        # Always try generic fallback for missing fields
        if not name or not price:
            gn, gp, gi = _parse_generic(soup)
            name = name or gn
            price = price or gp
            image = image or gi

        # Truncate long names
        if name and len(name) > 200:
            name = name[:197] + '...'

        return {
            'name': name or 'Unknown Product',
            'price': price,
            'image': image,
            'platform': platform,
            'success': bool(price),
        }
    except Exception as e:
        log.warning('Price fetch failed for %s: %s', url, e)
        return {
            'name': None,
            'price': None,
            'image': None,
            'platform': platform,
            'success': False,
            'error': str(e),
        }
