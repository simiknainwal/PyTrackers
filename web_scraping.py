import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from datetime import datetime
import os
import hashlib
import random


class WebScraper:
    def __init__(self):
        # Enhanced headers to better mimic a real browser
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
            "DNT": "1",
        }
        # Use session for better cookie/connection handling
        self.session = requests.Session()

    def detect_source(self, url):
        if "amazon" in url.lower():
            return "Amazon"
        return None

    def generate_product_id(self, url):
        amazon_match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if amazon_match:
            return f"AMZ_{amazon_match.group(1)}"
        return f"AMZ_{hashlib.md5(url.encode()).hexdigest()[:10]}"

    def scrape_product(self, url):
        """Scrape product name and price from an Amazon product URL."""
        try:
            source = self.detect_source(url)
            if source != "Amazon":
                print("❌ Only Amazon URLs are supported right now.")
                return None

            # Simulate human delay
            time.sleep(random.uniform(2.0, 4.0))

            # Use session for better handling
            response = self.session.get(url, headers=self.headers, timeout=15)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"⚠️ HTTP {response.status_code}: Failed to fetch page.")
                if response.status_code == 503:
                    print("🤖 Bot detected! Amazon is blocking automated requests.")
                    print("💡 Try: 1) Wait longer between requests 2) Use different IP 3) Use Selenium")
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Debug: Save HTML to file for inspection
            debug_dir = 'debug'
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, 'amazon_page.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"💾 Saved page HTML to {debug_file} for inspection")

            product_id = self.generate_product_id(url)
            product_name = self._extract_title(soup)
            price = self._extract_price(soup)

            if not product_name:
                print("⚠️ Could not find product name with primary methods.")
                product_name = self._extract_title_fallback(soup)
                if product_name:
                    print(f"✅ Found title using fallback: {product_name[:50]}...")
                
            if not price or price <= 0:
                print("⚠️ Could not find price with primary selectors, trying fallbacks...")
                price = self._extract_fallback_price(soup)

            if not price or price <= 0:
                print("❌ Price extraction failed completely.")
                print(f"💡 Check {debug_file} to see the actual HTML structure")
                print("💡 Amazon might be showing a CAPTCHA or blocking page")
                return None

            print(f"✅ Successfully scraped: {product_name[:50]}... @ ₹{price}")

            return {
                "product_id": product_id,
                "url": url,
                "product_name": product_name or "Unknown Product",
                "price": round(price, 2),
                "source": source,
            }

        except requests.exceptions.Timeout:
            print("⚠️ Request timeout - Amazon took too long to respond")
            return None
        except requests.exceptions.ConnectionError:
            print("⚠️ Connection error - Check your internet connection")
            return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error: {e}")
            return None
        except Exception as e:
            print(f"⚠️ Unexpected scraping error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_title(self, soup):
        """Try to extract the product title using multiple selectors."""
        title_selectors = [
            ("span", {"id": "productTitle"}),
            ("span", {"id": "title"}),
            ("span", {"class": "a-size-large product-title-word-break"}),
            ("h1", {"id": "title"}),
            ("h1", {"class": "a-size-large a-spacing-none"}),
        ]
        
        for tag, attrs in title_selectors:
            el = soup.find(tag, attrs)
            if el:
                title = el.get_text(strip=True)
                if title:
                    return title
        return None

    def _extract_title_fallback(self, soup):
        """Fallback method to extract title from meta tags or headings"""
        # Try meta tags
        meta_selectors = [
            ("meta", {"property": "og:title"}),
            ("meta", {"name": "title"}),
        ]
        
        for tag, attrs in meta_selectors:
            meta = soup.find(tag, attrs)
            if meta and meta.get("content"):
                return meta.get("content").strip()
        
        # Try any h1 tag
        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(strip=True)
            if text:
                return text
        
        return None

    def _extract_price(self, soup):
        """Extract price from various Amazon price containers."""
        # Updated selectors for current Amazon structure
        price_attempts = []
        
        # Method 1: Try common price classes
        price_classes = [
            "a-price-whole",
            "a-offscreen",
            "priceToPay",
            "apexPriceToPay",
            "a-price",
        ]
        
        for class_name in price_classes:
            elements = soup.find_all("span", class_=class_name)
            for el in elements:
                price_text = el.get_text(strip=True)
                price = self._parse_price_text(price_text)
                if price and price > 0:
                    price_attempts.append((class_name, price))
        
        # Method 2: Try legacy IDs
        price_ids = [
            "priceblock_ourprice",
            "priceblock_dealprice", 
            "priceblock_saleprice",
            "price_inside_buybox",
        ]
        
        for price_id in price_ids:
            el = soup.find("span", id=price_id)
            if el:
                price_text = el.get_text(strip=True)
                price = self._parse_price_text(price_text)
                if price and price > 0:
                    price_attempts.append((price_id, price))
        
        # Return the most common price found (or first valid one)
        if price_attempts:
            price = price_attempts[0][1]
            print(f"✅ Found price using {price_attempts[0][0]}: ₹{price}")
            return price
        
        return 0.0

    def _extract_fallback_price(self, soup):
        """Search entire HTML text for price patterns with various formats."""
        text = soup.get_text()
        
        # Multiple regex patterns for Indian pricing
        patterns = [
            (r"₹\s?([\d,]+\.?\d*)", "Rupee symbol"),
            (r"Rs\.?\s?([\d,]+\.?\d*)", "Rs. prefix"),
            (r"INR\s?([\d,]+\.?\d*)", "INR prefix"),
            (r"Price:\s*₹?\s?([\d,]+\.?\d*)", "Price: label"),
            (r"MRP:?\s*₹?\s?([\d,]+\.?\d*)", "MRP label"),
            (r"Deal Price:?\s*₹?\s?([\d,]+\.?\d*)", "Deal Price label"),
        ]
        
        found_prices = []
        
        for pattern, description in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    price = float(match.replace(",", ""))
                    # Sanity check: price should be reasonable (₹1 to ₹10 crores)
                    if 1 <= price <= 100000000:
                        found_prices.append((price, description))
                except ValueError:
                    continue
        
        if found_prices:
            # Return the most reasonable price (usually the first occurrence)
            price = found_prices[0][0]
            print(f"✅ Found price using fallback ({found_prices[0][1]}): ₹{price}")
            return price
        
        print("❌ No valid price found in page text")
        return 0.0

    def _parse_price_text(self, text):
        """Extract numeric value from price string."""
        # Remove currency symbols and common words
        cleaned = text.replace("₹", "").replace("Rs", "").replace("INR", "")
        cleaned = cleaned.replace("Price", "").replace("MRP", "").strip()
        
        # Extract number with optional commas and decimal
        match = re.search(r"([\d,]+\.?\d*)", cleaned)
        if match:
            try:
                price_str = match.group(1).replace(",", "")
                price = float(price_str)
                # Sanity check
                if 1 <= price <= 100000000:
                    return price
            except ValueError:
                pass
        return 0.0


def log_to_csv_row(filename, rowdict):
    """Append a product price record to CSV."""
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
    fieldnames = ['product_id', 'product_name', 'date', 'time', 'price', 'source', 'url']
    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(rowdict)
        f.flush()