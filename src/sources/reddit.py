"""
Reddit data source implementation
"""
import praw
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base import BaseSource


class RedditSource(BaseSource):
    """
    Fetch AI-related posts from Reddit subreddits
    Uses PRAW (Python Reddit API Wrapper)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.subreddits = config.get('subreddits', [
            'MachineLearning', 'artificial',
            'ArtificialIntelligence', 'deeplearning'
        ])
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.user_agent = config.get('user_agent', 'AI Daily Report Bot 1.0')

        # Initialize Reddit client
        self.reddit = None
        if self.client_id and self.client_secret and 'YOUR_' not in self.client_id:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                self.logger.info("Reddit client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Reddit client: {e}")

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch hot posts from configured subreddits

        Returns:
            List of Reddit post dictionaries
        """
        if not self.enabled:
            self.logger.info("Reddit source is disabled")
            return []

        if not self.reddit:
            self.logger.warning(
                "Reddit client not initialized. "
                "Please configure client_id and client_secret in config.yaml"
            )
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
        Fetch hot posts from a specific subreddit

        Args:
            subreddit_name: Name of the subreddit

        Returns:
            List of post dictionaries
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []

        # Fetch hot posts
        for submission in subreddit.hot(limit=50):
            # Filter for recent posts (within last 24 hours or highly scored)
            post_time = datetime.fromtimestamp(submission.created_utc)
            time_diff = datetime.now() - post_time

            # Include posts from last 24 hours or with high score
            if time_diff <= timedelta(hours=24) or submission.score >= 100:
                posts.append(self._format_post(submission, subreddit_name))

        return posts

    def _format_post(self, submission, subreddit_name: str) -> Dict[str, Any]:
        """
        Format Reddit submission into standard dictionary

        Args:
            submission: PRAW submission object
            subreddit_name: Subreddit name

        Returns:
            Post dictionary
        """
        return {
            'id': submission.id,
            'title': submission.title,
            'link': f"https://reddit.com{submission.permalink}",
            'url': submission.url if submission.url.startswith('http') else None,
            'score': submission.score,
            'comments': submission.num_comments,
            'author': str(submission.author) if submission.author else '[deleted]',
            'subreddit': subreddit_name,
            'timestamp': datetime.fromtimestamp(submission.created_utc),
            'source': f'Reddit r/{subreddit_name}',
            'is_self': submission.is_self
        }


# For testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test with your Reddit API credentials
    config = {
        'enabled': True,
        'subreddits': ['MachineLearning', 'artificial'],
        'client_id': 'YOUR_CLIENT_ID',  # Replace with actual ID
        'client_secret': 'YOUR_CLIENT_SECRET',  # Replace with actual secret
        'user_agent': 'AI Daily Report Bot 1.0',
        'max_posts': 10
    }

    source = RedditSource(config)
    posts = source.fetch()

    print(f"\nFound {len(posts)} Reddit posts:\n")
    for i, post in enumerate(posts, 1):
        print(f"{i}. [{post['subreddit']}] {post['title'][:60]}...")
        print(f"   Score: {post['score']}, Comments: {post['comments']}")
        print(f"   Link: {post['link']}")
        print()