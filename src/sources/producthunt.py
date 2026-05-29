"""
Product Hunt AI products source
Fetches AI-related products from Product Hunt
"""
import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseSource


class ProductHuntSource(BaseSource):
    """
    Fetch AI products from Product Hunt
    Uses scraping of Product Hunt's AI category
    """

    PRODUCT_HUNT_URL = "https://www.producthunt.com"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_products = config.get('max_products', 20)
        self.logger.info("Product Hunt source initialized")

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch AI products from Product Hunt

        Returns:
            List of AI product dictionaries
        """
        if not self.enabled:
            self.logger.info("Product Hunt source is disabled")
            return []

        self.logger.info("Fetching AI products from Product Hunt")

        products = []

        # Try multiple approaches
        try:
            # Method 1: Scrape AI/ML category
            ai_products = self._fetch_ai_category()
            products.extend(ai_products)
            self.logger.info(f"Found {len(ai_products)} products from AI category")

        except Exception as e:
            self.logger.warning(f"Failed to fetch AI category: {e}")

        try:
            # Method 2: Search for AI topics
            search_products = self._fetch_ai_search()
            products.extend(search_products)
            self.logger.info(f"Found {len(search_products)} products from search")

        except Exception as e:
            self.logger.warning(f"Failed to fetch search results: {e}")

        # Sort by upvotes
        products.sort(key=lambda x: x.get('score', 0), reverse=True)
        products = self._limit_items(products)

        self.logger.info(f"Total Product Hunt products: {len(products)}")
        return products

    def _fetch_ai_category(self) -> List[Dict[str, Any]]:
        """
        Fetch products from Product Hunt AI/ML category

        Returns:
            List of product dictionaries
        """
        # Product Hunt categories
        url = f"{self.PRODUCT_HUNT_URL}/topics/artificial-intelligence"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        response = self._retry_request(
            lambda: requests.get(url, headers=headers, timeout=15)
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        return self._parse_producthunt_page(response.text)

    def _fetch_ai_search(self) -> List[Dict[str, Any]]:
        """
        Fetch products by searching for AI terms

        Returns:
            List of product dictionaries
        """
        search_url = f"{self.PRODUCT_HUNT_URL}/search?q=ai+gpt+llm"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }

        response = self._retry_request(
            lambda: requests.get(search_url, headers=headers, timeout=15)
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        return self._parse_producthunt_page(response.text)

    def _parse_producthunt_page(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse Product Hunt HTML page

        Args:
            html: HTML content

        Returns:
            List of product dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        products = []

        # Find product cards (Product Hunt structure changes frequently)
        product_cards = soup.find_all('div', class_=re.compile(r'.*post.*'))

        for card in product_cards[:self.max_products]:
            try:
                product = self._parse_product_card(card)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.warning(f"Failed to parse product card: {e}")

        return products

    def _parse_product_card(self, card) -> Dict[str, Any]:
        """
        Parse a Product Hunt product card

        Args:
            card: BeautifulSoup element

        Returns:
            Product dictionary or None
        """
        # Extract product name
        name_elem = card.find('h3')
        if not name_elem:
            name_elem = card.find('a', class_=re.compile(r'.*title.*'))

        name = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'

        # Extract link
        link_elem = card.find('a', href=re.compile(r'/posts/'))
        if link_elem:
            href = link_elem.get('href', '')
            link = f"{self.PRODUCT_HUNT_URL}{href}"
        else:
            link = self.PRODUCT_HUNT_URL

        # Extract description/tagline
        desc_elem = card.find('p', class_=re.compile(r'.*tagline.*'))
        if not desc_elem:
            desc_elem = card.find('div', class_=re.compile(r'.*description.*'))

        description = desc_elem.get_text(strip=True) if desc_elem else ''

        # Extract upvotes
        vote_elem = card.find('button', class_=re.compile(r'.*vote.*'))
        if not vote_elem:
            vote_elem = card.find('span', class_=re.compile(r'.*vote.*'))

        votes = 0
        if vote_elem:
            vote_text = vote_elem.get_text(strip=True)
            vote_match = re.search(r'(\d+)', vote_text)
            if vote_match:
                votes = int(vote_match.group(1))

        # Only include AI-related products
        combined_text = f"{name} {description}".lower()
        ai_keywords = ['ai', 'gpt', 'llm', 'machine learning', 'artificial intelligence',
                       'chatbot', 'assistant', 'automation', 'neural']

        if not any(keyword in combined_text for keyword in ai_keywords):
            return None

        return {
            'name': name,
            'title': name,
            'description': description,
            'link': link,
            'score': votes,
            'upvotes': votes,
            'timestamp': datetime.now(),
            'source': 'Product Hunt',
            'category': 'Product Hunt AI产品'
        }


# For testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = {
        'enabled': True,
        'max_products': 10
    }

    source = ProductHuntSource(config)
    products = source.fetch()

    print(f"\nFound {len(products)} AI products from Product Hunt:\n")
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['name']}")
        print(f"   Description: {product['description'][:80]}")
        print(f"   Upvotes: {product['upvotes']}")
        print(f"   Link: {product['link']}")
        print()