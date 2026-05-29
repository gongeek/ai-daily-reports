"""
Reddit data source implementation using public JSON API
No OAuth required, directly access Reddit's .json endpoints
"""
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base import BaseSource


class RedditSource(BaseSource):
    """
    Fetch AI-related posts from Reddit subreddits using public JSON API
    No authentication required - uses Reddit's open .json endpoints
    """

    # Default AI-related subreddits
    DEFAULT_SUBREDDITS = [
        'LocalLLaMA',
        'MachineLearning',
        'artificial',
        'ArtificialIntelligence',
        'deeplearning',
        'LLMDevs',
        'OpenAI'
    ]

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.subreddits = config.get('subreddits', self.DEFAULT_SUBREDDITS)
        self.limit = config.get('limit', 25)

        # No need for client_id/client_secret with JSON API
        self.logger.info(f"Reddit JSON API initialized for subreddits: {self.subreddits}")

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch hot posts from configured subreddits

        Returns:
            List of Reddit post dictionaries
        """
        if not self.enabled:
            self.logger.info("Reddit source is disabled")
            return []

        self.logger.info(f"Fetching posts from Reddit: {self.subreddits}")

        all_posts = []

        for subreddit_name in self.subreddits:
            try:
                posts = self._fetch_subreddit_posts(subreddit_name)
                all_posts.extend(posts)
                self.logger.info(f"Found {len(posts)} posts in r/{subreddit_name}")
            except Exception as e:
                self.logger.error(f"Failed to fetch r/{subreddit_name}: {e}")

        # Sort by score and limit
        all_posts.sort(key=lambda x: x.get('score', 0), reverse=True)
        all_posts = self._limit_items(all_posts)

        self.logger.info(f"Total Reddit posts: {len(all_posts)}")
        return all_posts

    def _fetch_subreddit_posts(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Fetch hot posts from a specific subreddit using JSON API

        Args:
            subreddit_name: Name of the subreddit

        Returns:
            List of post dictionaries
        """
        # Reddit's public JSON API endpoint
        url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit={self.limit}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json,text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }

        response = self._retry_request(
            lambda: requests.get(url, headers=headers, timeout=15)
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code} - Failed to fetch r/{subreddit_name}")

        data = response.json()

        if 'data' not in data or 'children' not in data['data']:
            self.logger.warning(f"Unexpected JSON structure for r/{subreddit_name}")
            return []

        posts = []
        for child in data['data']['children']:
            if child['kind'] == 't3':  # t3 is a post
                post_data = child['data']
                post = self._format_post(post_data, subreddit_name)
                posts.append(post)

        return posts

    def _format_post(self, post_data: Dict, subreddit_name: str) -> Dict[str, Any]:
        """
        Format Reddit post data into standard dictionary

        Args:
            post_data: Raw post data from Reddit JSON API
            subreddit_name: Subreddit name

        Returns:
            Post dictionary
        """
        # Extract basic info
        title = post_data.get('title', '')
        score = post_data.get('score', 0)
        num_comments = post_data.get('num_comments', 0)
        author = post_data.get('author', '[deleted]')
        created_utc = post_data.get('created_utc', 0)

        # Links
        permalink = post_data.get('permalink', '')
        reddit_link = f"https://reddit.com{permalink}"

        # External link if it's a link post
        external_url = post_data.get('url', '') if not post_data.get('is_self', True) else None

        # Use external URL if available, otherwise use Reddit permalink
        main_link = external_url if external_url else reddit_link

        # Selftext (post body text)
        selftext = post_data.get('selftext', '')

        return {
            'id': post_data.get('id', ''),
            'title': title,
            'link': main_link,
            'reddit_link': reddit_link,
            'external_url': external_url,
            'score': score,
            'comments': num_comments,
            'author': author,
            'subreddit': subreddit_name,
            'timestamp': datetime.fromtimestamp(created_utc),
            'source': f'Reddit r/{subreddit_name}',
            'is_self': post_data.get('is_self', True),
            'selftext': selftext[:500] if selftext else None,  # Limit text length
            'domain': post_data.get('domain', 'self.' + subreddit_name)
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
        'subreddits': ['LocalLLaMA', 'MachineLearning'],
        'limit': 10,
        'max_posts': 20
    }

    source = RedditSource(config)
    posts = source.fetch()

    print(f"\nFound {len(posts)} Reddit posts:\n")
    for i, post in enumerate(posts, 1):
        print(f"{i}. [{post['subreddit']}] {post['title'][:60]}...")
        print(f"   Score: {post['score']}, Comments: {post['comments']}")
        print(f"   Author: {post['author']}")
        print(f"   Link: {post['link']}")
        print(f"   Reddit: {post['reddit_link']}")
        print()