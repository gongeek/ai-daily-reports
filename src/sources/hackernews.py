"""
Hacker News data source implementation
"""
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseSource


class HackerNewsSource(BaseSource):
    """
    Fetch AI-related stories from Hacker News
    Uses the official Hacker News API (free, no API key required)
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.keywords = config.get('keywords', [
            'AI', 'ML', 'GPT', 'LLM',
            'machine learning', 'deep learning',
            'neural network', 'artificial intelligence'
        ])

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch top stories from Hacker News and filter for AI-related content

        Returns:
            List of AI-related story dictionaries
        """
        if not self.enabled:
            self.logger.info("Hacker News source is disabled")
            return []

        self.logger.info("Fetching top stories from Hacker News")

        # Get top story IDs
        story_ids = self._get_top_stories()

        # Fetch story details
        stories = []
        for story_id in story_ids[:100]:  # Check top 100 stories
            try:
                story = self._get_story_details(story_id)
                if story:
                    stories.append(story)
            except Exception as e:
                self.logger.warning(f"Failed to fetch story {story_id}: {e}")

        # Filter by keywords
        ai_stories = self._filter_by_keywords(stories, self.keywords)

        # Sort by score and limit
        ai_stories.sort(key=lambda x: x.get('score', 0), reverse=True)
        ai_stories = self._limit_items(ai_stories)

        self.logger.info(f"Found {len(ai_stories)} AI-related stories")
        return ai_stories

    def _get_top_stories(self) -> List[int]:
        """
        Get list of top story IDs

        Returns:
            List of story IDs
        """
        url = f"{self.BASE_URL}/topstories.json"

        response = self._retry_request(
            lambda: requests.get(url, timeout=10)
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get top stories: HTTP {response.status_code}")

        return response.json()

    def _get_story_details(self, story_id: int) -> Dict[str, Any]:
        """
        Get details for a specific story

        Args:
            story_id: Hacker News story ID

        Returns:
            Story details dictionary or None if not a story
        """
        url = f"{self.BASE_URL}/item/{story_id}.json"

        response = self._retry_request(
            lambda: requests.get(url, timeout=10)
        )

        if response.status_code != 200:
            self.logger.warning(f"Failed to fetch story {story_id}")
            return None

        data = response.json()

        # Skip if not a story type
        if not data or data.get('type') != 'story':
            return None

        # Skip if no URL (text-only posts)
        if not data.get('url'):
            return None

        return {
            'id': story_id,
            'title': data.get('title', ''),
            'link': data.get('url', ''),
            'score': data.get('score', 0),
            'comments': data.get('descendants', 0),
            'author': data.get('by', 'unknown'),
            'timestamp': datetime.fromtimestamp(data.get('time', 0)),
            'source': 'Hacker News'
        }


# For testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = {
        'enabled': True,
        'keywords': ['AI', 'ML', 'GPT', 'LLM', 'machine learning'],
        'max_posts': 10
    }

    source = HackerNewsSource(config)
    stories = source.fetch()

    print(f"\nFound {len(stories)} AI-related stories:\n")
    for i, story in enumerate(stories, 1):
        print(f"{i}. {story['title']}")
        print(f"   Score: {story['score']}, Comments: {story['comments']}")
        print(f"   Link: {story['link']}")
        print()