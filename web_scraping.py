import requests
from bs4 import BeautifulSoup
import re

class WebScraper:
    """
    Handles web scraping operations using Requests and BeautifulSoup
    Extracts product details and prices from e-commerce platforms
    """
    
    def __init__(self):
        # Headers to mimic real browser request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-IN,en;q=0.9',
        }
    
    def scrape_product(self, url):
        """
        Main scraping function - fetches and extracts product data
        Returns: dictionary with product_name, price, url
        """
        try:
            print("🔍 Scraping product data...")
            
            # Fetch the webpage
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product details
            product_data = self._extract_details(soup, url)
            
            return product_data
        
        except Exception as e:
            print(f"Error during scraping: {e}")
            return None
    
    def _extract_details(self, soup, url):
        """
        Extracts product name and price from parsed HTML
        """
        product_data = {
            'url': url,
            'product_name': 'Unknown Product',
            'price': 0.0
        }
        
        # Extract Product Title
        title_element = soup.find('span', {'id': 'productTitle'})
        if title_element:
            product_data['product_name'] = title_element.get_text().strip()
        
        # Extract Price - trying multiple selectors
        price_selectors = [
            {'class': 'a-price-whole'},
            {'class': 'a-offscreen'},
            {'id': 'priceblock_ourprice'},
            {'id': 'priceblock_dealprice'}
        ]
        
        for selector in price_selectors:
            price_element = soup.find('span', selector)
            if price_element:
                price_text = price_element.get_text().strip()
                
                # Extract numbers from price text
                price_match = re.search(r'[\d,]+\.?\d*', price_text)
                if price_match:
                    clean_price = price_match.group().replace(',', '')
                    product_data['price'] = float(clean_price)
                    break
        
        return product_data
