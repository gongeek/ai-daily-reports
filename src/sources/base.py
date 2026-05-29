"""
Base class for all data sources
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime


class BaseSource(ABC):
    """
    Abstract base class for data sources
    All source implementations must inherit from this class
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize source with configuration

        Args:
            config: Source-specific configuration dictionary
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_items = (
            config.get('max_items')
            or config.get('max_posts')
            or config.get('max_repos')
            or config.get('max_products')
            or config.get('max_articles')
            or config.get('max_tweets')
            or 20
        )

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch data from the source

        Returns:
            List of standardized data items
            Each item should have at minimum:
            - title: str
            - link: str
            - score: int/float
            - source: str (source name)
            - timestamp: datetime

        Raises:
            Exception: If fetch fails after retries
        """
        pass

    def _retry_request(self, func, max_retries=3, delay=1):
        """
        Retry wrapper for network requests

        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds

        Returns:
            Result from successful function execution

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
                else:
                    self.logger.error(
                        f"All {max_retries} attempts failed for {self.__class__.__name__}"
                    )
                    raise

    def _filter_by_keywords(self, items: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Filter items by keywords in title/description

        Args:
            items: List of items to filter
            keywords: List of keywords to match

        Returns:
            Filtered list of items
        """
        filtered = []
        for item in items:
            text = item.get('title', '').lower()
            description = item.get('description', '').lower()
            combined_text = text + ' ' + description

            if any(keyword.lower() in combined_text for keyword in keywords):
                filtered.append(item)

        return filtered

    def _limit_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limit number of items to max_items

        Args:
            items: List of items

        Returns:
            Limited list
        """
        return items[:self.max_items]

    def get_source_name(self) -> str:
        """
        Get human-readable source name

        Returns:
            Source name string
        """
        return self.__class__.__name__.replace('Source', '')
