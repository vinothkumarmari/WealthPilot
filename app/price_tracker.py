"""Product price tracker — fetches prices from Indian e-commerce sites."""

import re
import json
import logging
from urllib.parse import urlparse, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_HEADERS_BROWSER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Chromium";v="125", "Not.A/Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
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


def _fetch_page(url, platform='Other'):
    """Fetch HTML content from URL with session-based approach."""
    session = requests.Session()
    session.headers.update(_HEADERS_BROWSER)

    if platform == 'Amazon':
        # Visit homepage first to get cookies, then product page
        try:
            session.get('https://www.amazon.in/', timeout=10)
        except Exception:
            pass
        session.headers['Referer'] = 'https://www.amazon.in/'

    resp = session.get(url, timeout=20, allow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser'), resp.text


def _extract_asin(url):
    """Extract ASIN from Amazon URL."""
    # /dp/B0XXXXX or /gp/product/B0XXXXX
    m = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
    return m.group(1) if m else None


def _parse_amazon(soup, raw_html='', url=''):
    """Parse product info from Amazon.in page with multiple strategies."""
    name = None
    price = None
    mrp = None
    image = None
    discount = None

    # Strategy 1: Standard DOM parsing
    el = soup.find('span', id='productTitle')
    if el:
        name = el.get_text(strip=True)

    # Price: multiple selectors (Amazon changes frequently)
    for selector in [
        ('span', {'class': 'a-price-whole'}),
        ('span', {'id': 'priceblock_dealprice'}),
        ('span', {'id': 'priceblock_ourprice'}),
        ('span', {'id': 'tp_price_block_total_price_wc'}),
    ]:
        el = soup.find(*selector)
        if el:
            p = _clean_price(el.get_text())
            if p:
                price = p
                break

    # If no price from whole, try a-offscreen (first occurrence in price container)
    if not price:
        price_container = soup.find('div', id='corePriceDisplay_desktop_feature_div') or \
                          soup.find('div', id='corePrice_desktop') or \
                          soup.find('div', class_='a-section a-spacing-none aok-align-center')
        if price_container:
            offscreen = price_container.find('span', class_='a-offscreen')
            if offscreen:
                price = _clean_price(offscreen.get_text())

    # MRP (original price)
    mrp_el = soup.find('span', class_='a-price a-text-price')
    if mrp_el:
        offscreen = mrp_el.find('span', class_='a-offscreen')
        if offscreen:
            mrp = _clean_price(offscreen.get_text())

    # Discount percentage
    disc_el = soup.find('span', class_='a-size-large a-color-price savingPriceOverride') or \
              soup.find('span', string=re.compile(r'-\d+%'))
    if disc_el:
        dm = re.search(r'-?(\d+)%', disc_el.get_text())
        if dm:
            discount = int(dm.group(1))

    # Image
    el = soup.find('img', id='landingImage')
    if el:
        image = el.get('data-old-hires') or el.get('src')
    if not image:
        el = soup.find('img', id='imgBlkFront')
        if el:
            image = el.get('src')

    # Strategy 2: Parse from embedded JSON data (more reliable)
    if raw_html and (not name or not price):
        # Look for twister data or inline JSON
        for pattern in [
            r'"title"\s*:\s*"([^"]{10,300})"',
        ]:
            if not name:
                m = re.search(pattern, raw_html)
                if m:
                    candidate = m.group(1)
                    # Skip generic/short strings
                    if len(candidate) > 15 and 'amazon' not in candidate.lower():
                        name = candidate

        if not price:
            # Look for price in various JSON patterns
            for pattern in [
                r'"priceAmount"\s*:\s*([\d.]+)',
                r'"price"\s*:\s*"?([\d,]+\.?\d*)"?',
                r'"buyingPrice"\s*:\s*([\d.]+)',
            ]:
                m = re.search(pattern, raw_html)
                if m:
                    p = _clean_price(m.group(1))
                    if p and 10 < p < 10_000_000:
                        price = p
                        break

    # Strategy 3: og:title fallback for name
    if not name:
        og = soup.find('meta', property='og:title')
        if og:
            n = og.get('content', '').strip()
            # Remove " : Amazon.in" suffix
            n = re.sub(r'\s*[:\-|]\s*Amazon\.in.*$', '', n)
            if len(n) > 5:
                name = n

    return name, price, mrp, discount, image


def _parse_flipkart(soup, raw_html=''):
    """Parse product info from Flipkart page."""
    name = None
    price = None
    mrp = None
    discount = None
    image = None

    # Name — Flipkart uses dynamic class names
    for tag, cls_list in [
        ('span', ['VU-ZEz', 'B_NuCI', 'yhB1nd', '_35KyD6']),
        ('h1', ['VU-ZEz', 'yhB1nd', '_35KyD6']),
    ]:
        for cls in cls_list:
            el = soup.find(tag, class_=cls)
            if el:
                name = el.get_text(strip=True)
                break
        if name:
            break

    # Price
    for cls in ['Nx9bqj CxhGGd', '_30jeq3 _16Jk6d', 'Nx9bqj', '_30jeq3']:
        el = soup.find('div', class_=cls)
        if el:
            p = _clean_price(el.get_text())
            if p:
                price = p
                break

    # MRP
    for cls in ['yRaY8j A6+E6v', '_3I9_wc _2p6lqe', 'yRaY8j']:
        el = soup.find('div', class_=cls)
        if el:
            m = _clean_price(el.get_text())
            if m and m > (price or 0):
                mrp = m
                break

    # Discount
    for cls in ['UkUFwK', '_3Ay6sb _31Dcoz']:
        el = soup.find('div', class_=cls) or soup.find('span', class_=cls)
        if el:
            dm = re.search(r'(\d+)%', el.get_text())
            if dm:
                discount = int(dm.group(1))
                break

    # Image
    for cls in ['DByuf4', '_396cs4', '_2r_T1I', 'CXW8mj', '_0DkuPH']:
        el = soup.find('img', class_=cls)
        if el:
            image = el.get('src')
            break

    # Fallback: og:title, og:image
    if not name:
        og = soup.find('meta', property='og:title')
        if og:
            n = og.get('content', '').strip()
            n = re.sub(r'\s*[|\-]\s*Flipkart\.com.*$', '', n)
            if len(n) > 5:
                name = n

    if not image:
        og = soup.find('meta', property='og:image')
        if og:
            image = og.get('content')

    # JSON fallback
    if raw_html and not price:
        for pattern in [
            r'"sellingPrice"\s*:\s*([\d.]+)',
            r'"price"\s*:\s*([\d.]+)',
            r'"finalPrice"\s*:\s*([\d.]+)',
        ]:
            m = re.search(pattern, raw_html)
            if m:
                p = _clean_price(m.group(1))
                if p and 10 < p < 10_000_000:
                    price = p
                    break

    return name, price, mrp, discount, image


def _parse_generic(soup, raw_html=''):
    """Generic parser using og: meta tags — works for most e-commerce sites."""
    name = None
    price = None
    mrp = None
    discount = None
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

    # Fallback: find price patterns in page (look for ₹ symbol first)
    if not price:
        for el in soup.find_all(['span', 'div', 'p', 'strong']):
            text = el.get_text(strip=True)
            if re.match(r'^[₹Rs.\s]*[\d,]+(\.\d{1,2})?$', text) and len(text) < 20:
                p = _clean_price(text)
                if p and 10 < p < 10_000_000:
                    price = p
                    break

    # JSON-LD structured data (many sites use this)
    if raw_html:
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '')
                if isinstance(data, list):
                    data = data[0]
                if isinstance(data, dict):
                    offers = data.get('offers', data)
                    if isinstance(offers, list):
                        offers = offers[0]
                    if isinstance(offers, dict):
                        if not price:
                            p = _clean_price(str(offers.get('price', '')))
                            if p:
                                price = p
                        if not name and data.get('name'):
                            name = data['name']
                        if not image and data.get('image'):
                            img = data['image']
                            image = img[0] if isinstance(img, list) else img
            except (json.JSONDecodeError, TypeError, IndexError):
                pass

    return name, price, mrp, discount, image


def fetch_product_info(url):
    """Fetch product name, price, image, MRP, and discount from a product URL.
    
    Returns dict with: name, price, mrp, discount, image, platform, success, error.
    """
    platform = detect_platform(url)
    try:
        soup, raw_html = _fetch_page(url, platform)

        mrp = None
        discount = None

        if platform == 'Amazon':
            name, price, mrp, discount, image = _parse_amazon(soup, raw_html, url)
        elif platform == 'Flipkart':
            name, price, mrp, discount, image = _parse_flipkart(soup, raw_html)
        else:
            name, price, mrp, discount, image = _parse_generic(soup, raw_html)

        # Always try generic fallback for missing fields
        if not name or not price:
            gn, gp, gm, gd, gi = _parse_generic(soup, raw_html)
            name = name or gn
            price = price or gp
            image = image or gi
            mrp = mrp or gm
            discount = discount or gd

        # Calculate discount if we have both price and MRP
        if price and mrp and mrp > price and not discount:
            discount = round(((mrp - price) / mrp) * 100)

        # Truncate long names
        if name and len(name) > 200:
            name = name[:197] + '...'

        return {
            'name': name or 'Unknown Product',
            'price': price,
            'mrp': mrp,
            'discount': discount,
            'image': image,
            'platform': platform,
            'success': bool(price),
        }
    except Exception as e:
        log.warning('Price fetch failed for %s: %s', url, e)
        return {
            'name': None,
            'price': None,
            'mrp': None,
            'discount': None,
            'image': None,
            'platform': platform,
            'success': False,
            'error': str(e),
        }
