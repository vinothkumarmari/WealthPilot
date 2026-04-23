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


def _extract_name_from_url(url):
    """Extract a readable product name from the URL slug (last resort fallback).
    
    E.g. https://www.amazon.in/Sony-HT-S20R-Soundbar-SA-RS3S/dp/B07T1... 
    -> 'Sony HT S20R Soundbar SA RS3S'
    """
    try:
        path = urlparse(url).path
        # Remove /dp/ASIN, /p/... tails
        path = re.sub(r'/(?:dp|gp/product|p)/[A-Za-z0-9]+.*$', '', path)
        # Take the last meaningful path segment
        segments = [s for s in path.strip('/').split('/') if s and len(s) > 3]
        if not segments:
            return None
        slug = segments[-1]
        # Convert slug to readable text
        name = re.sub(r'[-_]+', ' ', slug)
        name = re.sub(r'%[0-9A-Fa-f]{2}', ' ', name)  # URL encoded chars
        name = re.sub(r'\s+', ' ', name).strip()
        # Skip if it's just a product ID or too short
        if len(name) < 5 or name.replace(' ', '').isdigit():
            return None
        return name[:200]
    except Exception:
        return None


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
        # Try JSON-LD structured data first (more reliable)
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

    if not price:
        for el in soup.find_all(['span', 'div', 'p', 'strong']):
            text = el.get_text(strip=True)
            if re.match(r'^[₹Rs.\s]*[\d,]+(\.\d{1,2})?$', text) and len(text) < 20:
                p = _clean_price(text)
                if p and 10 < p < 10_000_000:
                    price = p
                    break

    # JSON-LD structured data — name/image fallback
    if raw_html and (not name or not image):
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '')
                if isinstance(data, list):
                    data = data[0]
                if isinstance(data, dict):
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

        # Fallback: extract name from URL slug if scraping got nothing useful
        if not name or name in ('Unknown Product', platform):
            url_name = _extract_name_from_url(url)
            if url_name:
                name = url_name

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


# ── Cross-platform price comparison ───────────────────────────

# Search URL templates for each platform
_SEARCH_URLS = {
    'Amazon': 'https://www.amazon.in/s?k={q}',
    'Flipkart': 'https://www.flipkart.com/search?q={q}',
    'Myntra': 'https://www.myntra.com/{q}',
    'Ajio': 'https://www.ajio.com/search/?text={q}',
    'Meesho': 'https://www.meesho.com/search?q={q}',
    'Croma': 'https://www.croma.com/search/?q={q}',
    'Reliance Digital': 'https://www.reliancedigital.in/search?q={q}',
    'Vijay Sales': 'https://www.vijaysales.com/search/{q}',
    'JioMart': 'https://www.jiomart.com/search/{q}',
    'Snapdeal': 'https://www.snapdeal.com/search?keyword={q}',
    'Nykaa': 'https://www.nykaa.com/search/result/?q={q}',
    'Tata CLiQ': 'https://www.tatacliq.com/search/?searchCategory=all&text={q}',
}

# Map domain fragments to platform names for Google Shopping results
_DOMAIN_TO_PLATFORM = {
    'amazon': 'Amazon', 'flipkart': 'Flipkart', 'myntra': 'Myntra',
    'ajio': 'Ajio', 'meesho': 'Meesho', 'croma': 'Croma',
    'tatacliq': 'Tata CLiQ', 'snapdeal': 'Snapdeal', 'jiomart': 'JioMart',
    'nykaa': 'Nykaa', 'reliancedigital': 'Reliance Digital',
    'vijaysales': 'Vijay Sales',
}


def _search_duckduckgo(query):
    """Search DuckDuckGo HTML for product prices across e-commerce platforms.
    
    Retries once on rate-limit (202). Returns list of: [{name, price, url, platform}]
    """
    import time as _time
    from urllib.parse import quote_plus, unquote
    search_url = f'https://html.duckduckgo.com/html/?q={quote_plus(query)}+price+buy+India'
    
    results = []
    for attempt in range(2):
        try:
            resp = requests.get(search_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            }, timeout=8)
            if resp.status_code == 202 and attempt == 0:
                _time.sleep(1)  # Rate limited, brief pause and retry
                continue
            if resp.status_code != 200:
                log.debug('DDG returned %s on attempt %d', resp.status_code, attempt)
                if attempt == 0:
                    continue
                return results
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for item in soup.select('.result')[:15]:
                title_el = item.select_one('.result__a')
                snippet_el = item.select_one('.result__snippet')
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                snippet = snippet_el.get_text(strip=True) if snippet_el else ''
                
                href = title_el.get('href', '')
                um = re.search(r'uddg=([^&]+)', href)
                actual_url = unquote(um.group(1)) if um else href
                
                if not actual_url or 'duckduckgo.com' in actual_url:
                    continue
                
                platform = 'Other'
                url_lower = actual_url.lower()
                for domain_frag, plat_name in _DOMAIN_TO_PLATFORM.items():
                    if domain_frag in url_lower:
                        platform = plat_name
                        break
                if platform == 'Other':
                    continue
                
                # Collect ALL prices from snippet and pick the LOWEST (offered/sale price, not MRP)
                all_prices = []
                combined = title + ' ' + snippet
                for pm in re.finditer(r'(?:₹|Rs\.?\s*)([\d,]+(?:\.\d{1,2})?)', combined):
                    p = _clean_price(pm.group(1))
                    if p and 100 < p < 10_000_000:
                        all_prices.append(p)
                price = min(all_prices) if all_prices else None
                
                results.append({
                    'name': title[:120],
                    'price': price,
                    'url': actual_url,
                    'platform': platform,
                })
            
            break  # Success, no need to retry
            
        except Exception as e:
            log.debug('DDG search failed (attempt %d): %s', attempt, e)
    
    return results


def _search_bing(query):
    """Search Bing for product URLs. Bing may be more lenient with cloud IPs.
    
    Returns list of: [{name, price, url, platform}]
    """
    from urllib.parse import quote_plus
    search_url = f'https://www.bing.com/search?q={quote_plus(query)}+price+buy+India&count=20'
    
    results = []
    try:
        resp = requests.get(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'en-IN,en;q=0.9',
        }, timeout=6)
        if resp.status_code != 200:
            return results
        
        # Parse any e-commerce URLs from the page
        for m in re.finditer(r'href="(https?://(?:www\.)?(?:amazon\.in|flipkart\.com|reliancedigital\.in|vijaysales\.com|croma\.com|jiomart\.com|snapdeal\.com|myntra\.com|ajio\.com|meesho\.com|nykaa\.com|tatacliq\.com)[^"]*)"', resp.text):
            url = m.group(1)
            platform = 'Other'
            for domain_frag, plat_name in _DOMAIN_TO_PLATFORM.items():
                if domain_frag in url.lower():
                    platform = plat_name
                    break
            if platform != 'Other' and not any(r['url'] == url for r in results):
                # Extract surrounding text for price
                idx = m.start()
                context = resp.text[max(0, idx-200):idx+200]
                price = None
                for pm in re.finditer(r'(?:₹|Rs\.?\s*)([\d,]+(?:\.\d{1,2})?)', context):
                    p = _clean_price(pm.group(1))
                    if p and 100 < p < 10_000_000:
                        price = p
                        break
                results.append({
                    'name': platform,
                    'price': price,
                    'url': url,
                    'platform': platform,
                })
    except Exception as e:
        log.debug('Bing search failed: %s', e)
    
    return results


def _search_google_web(query):
    """Search Google Web for product URLs.
    
    Returns list of: [{name, price, url, platform}]
    """
    from urllib.parse import quote_plus, unquote
    search_url = f'https://www.google.com/search?q={quote_plus(query)}+price+buy+India&num=15&hl=en'
    
    results = []
    try:
        resp = requests.get(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }, timeout=6)
        if resp.status_code != 200:
            return results
        
        # Google wraps URLs as /url?q=<actual>&... or direct href
        ecom_pattern = r'(?:amazon\.in|flipkart\.com|reliancedigital\.in|vijaysales\.com|croma\.com|jiomart\.com|snapdeal\.com|myntra\.com|ajio\.com|meesho\.com|nykaa\.com|tatacliq\.com)'
        
        for m in re.finditer(r'/url\?q=(https?://(?:www\.)?' + ecom_pattern + r'[^&"]*)', resp.text):
            url = unquote(m.group(1))
            platform = 'Other'
            for domain_frag, plat_name in _DOMAIN_TO_PLATFORM.items():
                if domain_frag in url.lower():
                    platform = plat_name
                    break
            if platform != 'Other' and not any(r['url'] == url for r in results):
                idx = m.start()
                context = resp.text[max(0, idx-200):idx+200]
                price = None
                for pm in re.finditer(r'(?:₹|Rs\.?\s*)([\d,]+(?:\.\d{1,2})?)', context):
                    p = _clean_price(pm.group(1))
                    if p and 100 < p < 10_000_000:
                        price = p
                        break
                results.append({
                    'name': platform,
                    'price': price,
                    'url': url,
                    'platform': platform,
                })
        
    except Exception as e:
        log.debug('Google web search failed: %s', e)
    
    return results


def _multi_search(query):
    """Try multiple search engines to find product URLs and prices.
    
    Returns list of: [{name, price, url, platform}]
    Uses first engine that returns results.
    """
    # Strategy 1: DuckDuckGo (best for price extraction)
    results = _search_duckduckgo(query)
    if results:
        log.debug('DDG returned %d results', len(results))
        return results
    
    # Strategy 2: Bing (more lenient with cloud IPs)
    results = _search_bing(query)
    if results:
        log.debug('Bing returned %d results', len(results))
        return results
    
    # Strategy 3: Google Web (often blocked but worth trying)
    results = _search_google_web(query)
    if results:
        log.debug('Google returned %d results', len(results))
        return results
    
    log.warning('All search engines returned 0 results for: %s', query)
    return []


def _shorten_query(product_name):
    """Shorten a long product name to key search terms (first 6-8 meaningful words)."""
    if not product_name:
        return ''
    # Remove common noise words and special chars
    name = re.sub(r'\([^)]*\)', '', product_name)  # Remove parenthesized text
    name = re.sub(r'[,|/\-–—]', ' ', name)
    # Remove filler words
    stopwords = {'with', 'and', 'for', 'the', 'from', 'its', 'that', 'this', 'set', 'pack', 'combo'}
    words = [w for w in name.split() if w.lower() not in stopwords and len(w) > 1]
    # Take brand + model + key descriptors (first 7 words)
    return ' '.join(words[:7]).strip()


def _parse_amazon_search(soup):
    """Extract first product result from Amazon search page."""
    results = []
    for item in soup.select('[data-component-type="s-search-result"]')[:3]:
        name_el = item.select_one('h2 a span') or item.select_one('h2 span')
        price_el = item.select_one('.a-price-whole') or item.select_one('.a-offscreen')
        link_el = item.select_one('h2 a')

        name = name_el.get_text(strip=True) if name_el else None
        price = _clean_price(price_el.get_text()) if price_el else None
        link = 'https://www.amazon.in' + link_el['href'] if link_el and link_el.get('href') else None

        if name and price:
            results.append({'name': name[:120], 'price': price, 'url': link})

    return results


def _parse_flipkart_search(soup):
    """Extract first product result from Flipkart search page."""
    results = []
    # Flipkart uses dynamic class names, try multiple patterns
    for item in soup.select('[data-id]')[:5]:
        name_el = item.select_one('a[title]') or item.select_one('.KzDlHZ') or item.select_one('.IRpwTa') or item.select_one('.s1Q9rs')
        price_el = item.select_one('.Nx9bqj') or item.select_one('._30jeq3')
        link_el = item.select_one('a[href*="/p/"]') or item.select_one('a[href*="pid="]')

        name = (name_el.get('title') or name_el.get_text(strip=True)) if name_el else None
        price = _clean_price(price_el.get_text()) if price_el else None
        link = None
        if link_el and link_el.get('href'):
            href = link_el['href']
            link = ('https://www.flipkart.com' + href) if href.startswith('/') else href

        if name and price:
            results.append({'name': name[:120], 'price': price, 'url': link})

    return results


def _parse_generic_search(soup, base_url):
    """Try to extract search results from generic e-commerce search pages."""
    results = []

    # Strategy 1: JSON-LD product data
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '')
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get('@type') in ('Product', 'ItemList'):
                    if item.get('@type') == 'ItemList':
                        for elem in (item.get('itemListElement') or [])[:3]:
                            ie = elem.get('item', elem) if isinstance(elem, dict) else {}
                            n = ie.get('name')
                            o = ie.get('offers', {})
                            if isinstance(o, list):
                                o = o[0] if o else {}
                            p = _clean_price(str(o.get('price', '')))
                            u = ie.get('url')
                            if n and p:
                                results.append({'name': n[:120], 'price': p, 'url': u})
                    else:
                        n = item.get('name')
                        o = item.get('offers', {})
                        if isinstance(o, list):
                            o = o[0] if o else {}
                        p = _clean_price(str(o.get('price', '')))
                        u = item.get('url')
                        if n and p:
                            results.append({'name': n[:120], 'price': p, 'url': u})
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 2: Find product-like links with prices nearby
    if not results:
        for a_tag in soup.find_all('a', href=True)[:50]:
            href = a_tag['href']
            if '/product' in href or '/p/' in href or '/dp/' in href:
                parent = a_tag.find_parent(['div', 'li', 'article'])
                if parent:
                    text = parent.get_text()
                    price_match = re.search(r'₹\s*([\d,]+)', text)
                    name_text = a_tag.get_text(strip=True)
                    if price_match and name_text and len(name_text) > 10:
                        p = _clean_price(price_match.group(1))
                        if p and 10 < p < 10_000_000:
                            full_url = href if href.startswith('http') else (base_url.rstrip('/') + '/' + href.lstrip('/'))
                            results.append({'name': name_text[:120], 'price': p, 'url': full_url})
                            if len(results) >= 3:
                                break

    return results[:3]


def compare_prices(product_name, exclude_platform=None):
    """Search for a product across multiple e-commerce platforms.

    Strategy:
    1. DuckDuckGo search (finds product links + prices from snippets)
    2. Concurrent fetch of product pages found by DDG
    3. Generate search URLs for user to click manually

    Time-budgeted to complete within 25s for Render compatibility.
    Returns dict: {platform: {results: [{name, price, url}], search_url, error}}
    """
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    TIME_BUDGET = 25  # Render free tier has 30s limit

    query = _shorten_query(product_name)
    if not query:
        return {}

    from urllib.parse import quote_plus
    encoded_q = quote_plus(query)

    # Step 1: Multi-engine search (DDG → Bing → Google)
    search_results = _multi_search(query)
    
    # Group search results by platform
    ddg_by_platform = {}
    ddg_urls_by_platform = {}
    for r in search_results:
        plat = r['platform']
        if plat not in ddg_urls_by_platform:
            ddg_urls_by_platform[plat] = r['url']
        if r.get('price'):
            if plat not in ddg_by_platform:
                ddg_by_platform[plat] = []
            ddg_by_platform[plat].append({
                'name': r['name'],
                'price': r['price'],
                'url': r['url'],
            })
    
    # Step 2: Concurrently fetch product pages to get accurate sale prices
    # Fetch ALL platforms with URLs (even those with DDG prices, since DDG may show MRP)
    urls_to_fetch = dict(ddg_urls_by_platform)
    
    def _fetch_one(plat, url):
        try:
            s = requests.Session()
            s.headers.update(_HEADERS_BROWSER)
            resp = s.get(url, timeout=6, allow_redirects=True)
            if resp.status_code == 200:
                raw = resp.text
                raw_lower = raw.lower()
                # Detect out-of-stock
                oos_signals = ['out of stock', 'currently sold out', 'currently unavailable',
                               'notify me when available', 'sold out']
                is_oos = any(sig in raw_lower for sig in oos_signals)
                
                soup = BeautifulSoup(raw, 'html.parser')
                if plat == 'Amazon':
                    name, price, mrp, disc, img = _parse_amazon(soup, raw, url)
                elif plat == 'Flipkart':
                    name, price, mrp, disc, img = _parse_flipkart(soup, raw)
                else:
                    name, price, mrp, disc, img = _parse_generic(soup, raw)
                
                if is_oos:
                    return plat, [{'name': (name or product_name)[:120], 'price': None,
                                   'mrp': mrp, 'url': url, 'out_of_stock': True}]
                if price and price > 500:
                    entry = {'name': (name or product_name)[:120], 'price': price, 'url': url}
                    if mrp and mrp > price:
                        entry['mrp'] = mrp
                        entry['discount'] = round((1 - price / mrp) * 100)
                    return plat, [entry]
        except Exception as e:
            log.debug('Page fetch failed %s: %s', plat, e)
        return plat, None
    
    if urls_to_fetch and (time.time() - start_time) < TIME_BUDGET - 8:
        remaining = max(2, int(TIME_BUDGET - 8 - (time.time() - start_time)))
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_fetch_one, p, u): p
                       for p, u in list(urls_to_fetch.items())[:6]}
            for future in as_completed(futures, timeout=remaining):
                try:
                    plat, result = future.result(timeout=1)
                    if result:
                        ddg_by_platform[plat] = result
                except Exception:
                    pass

    # Step 3: Build comparison dict
    comparison = {}
    for platform, url_tpl in _SEARCH_URLS.items():
        if platform == exclude_platform:
            continue
        search_url = url_tpl.format(q=encoded_q)
        entry = {'search_url': search_url, 'results': [], 'error': None}
        if platform in ddg_by_platform:
            entry['results'] = ddg_by_platform[platform][:3]
            if platform in ddg_urls_by_platform:
                entry['search_url'] = ddg_urls_by_platform[platform]
        comparison[platform] = entry

    # Sort platforms: those with results first, by lowest price
    comparison = dict(sorted(
        comparison.items(),
        key=lambda x: (
            0 if x[1]['results'] else 1,
            min((r['price'] for r in x[1]['results']), default=float('inf'))
        )
    ))

    return comparison
