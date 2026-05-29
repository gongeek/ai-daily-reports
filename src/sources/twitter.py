"""
Twitter/X data source implementation (optional).
Uses the official X API when X_BEARER_TOKEN is configured, with RapidAPI as
legacy fallback.
"""
import requests
import logging
import os
from typing import List, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser
from .base import BaseSource


class TwitterSource(BaseSource):
    """
    Fetch AI-related posts using X API or legacy RapidAPI.
    Optional source - gracefully disabled if no API key is configured.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bearer_token = config.get('bearer_token') or os.environ.get('X_BEARER_TOKEN')
        self.api_key = config.get('rapidapi_key') or os.environ.get('RAPIDAPI_KEY')
        self.enabled = config.get('enabled', False)
        self.search_terms = config.get('search_terms', [
            'AI', 'machine learning', 'GPT', 'LLM', 'artificial intelligence'
        ])

        self.api_host = "twitter-api45.p.rapidapi.com"
        self.base_url = f"https://{self.api_host}"
        self.x_api_url = "https://api.x.com/2/tweets/search/recent"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch tweets related to AI topics

        Returns:
            List of tweet dictionaries
        """
        if not self.enabled:
            self.logger.info("Twitter source is disabled or not configured")
            return []

        if self.bearer_token and 'YOUR_' not in self.bearer_token:
            self.logger.info("Fetching posts from X API")
            tweets = self._fetch_x_api_posts()
        elif self.api_key and 'YOUR_' not in self.api_key:
            self.logger.info("Fetching tweets from legacy RapidAPI")
            tweets = self._fetch_rapidapi_tweets()
        else:
            self.logger.info("Twitter/X source enabled but no API key is configured")
            return []

        tweets = self._limit_items(tweets)

        self.logger.info(f"Found {len(tweets)} tweets")
        return tweets

    def _fetch_x_api_posts(self) -> List[Dict[str, Any]]:
        """
        Fetch recent posts from the official X API.

        Returns:
            List of post dictionaries
        """
        headers = {'Authorization': f'Bearer {self.bearer_token}'}
        posts = []

        for term in self.search_terms[:3]:
            query = f'({term}) lang:en -is:retweet'
            params = {
                'query': query,
                'max_results': min(max(self.max_items, 10), 100),
                'tweet.fields': 'created_at,public_metrics,author_id'
            }

            try:
                response = self._retry_request(
                    lambda: requests.get(self.x_api_url, headers=headers, params=params, timeout=15)
                )

                if response.status_code == 200:
                    data = response.json()
                    for tweet_data in data.get('data', []):
                        posts.append(self._format_x_api_post(tweet_data, term))
                elif response.status_code == 429:
                    self.logger.warning("X API rate limit reached")
                    break
                elif response.status_code in (401, 403):
                    self.logger.warning("X API token is invalid or lacks access")
                    break
                else:
                    self.logger.warning(f"X API returned {response.status_code}: {response.text[:200]}")

            except Exception as e:
                self.logger.warning(f"Failed to fetch X posts for '{term}': {e}")

        posts.sort(key=lambda x: x.get('score', 0), reverse=True)
        return posts

    def _format_x_api_post(self, tweet_data: Dict, search_term: str) -> Dict[str, Any]:
        text = tweet_data.get('text', '')
        metrics = tweet_data.get('public_metrics') or {}
        tweet_id = tweet_data.get('id', '')
        created_at = tweet_data.get('created_at')

        try:
            timestamp = date_parser.parse(created_at).replace(tzinfo=None) if created_at else datetime.now()
        except Exception:
            timestamp = datetime.now()

        return {
            'id': tweet_id,
            'title': text[:120],
            'text': text,
            'link': f"https://x.com/i/web/status/{tweet_id}" if tweet_id else 'https://x.com',
            'score': metrics.get('like_count', 0) + metrics.get('retweet_count', 0),
            'retweets': metrics.get('retweet_count', 0),
            'author': tweet_data.get('author_id', 'unknown'),
            'timestamp': timestamp,
            'source': 'X',
            'search_term': search_term
        }

    def _fetch_rapidapi_tweets(self) -> List[Dict[str, Any]]:
        """
        Fetch tweets using RapidAPI

        Returns:
            List of tweet dictionaries
        """
        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }

        tweets = []

        for term in self.search_terms[:3]:  # Limit searches to avoid quota exhaustion
            try:
                url = f"{self.base_url}/search.php"
                params = {'query': term}

                response = self._retry_request(
                    lambda: requests.get(url, headers=headers, params=params, timeout=15)
                )

                if response.status_code == 200:
                    data = response.json()
                    if 'timeline' in data:
                        for tweet_data in data['timeline'][:20]:
                            tweet = self._format_tweet(tweet_data, term)
                            tweets.append(tweet)
                elif response.status_code == 403:
                    self.logger.warning("RapidAPI quota exhausted or invalid key")
                    break
                else:
                    self.logger.warning(f"Twitter API returned {response.status_code}")

            except Exception as e:
                self.logger.warning(f"Failed to fetch tweets for '{term}': {e}")

        return tweets

    def _format_tweet(self, tweet_data: Dict, search_term: str) -> Dict[str, Any]:
        """
        Format tweet data into standard dictionary

        Args:
            tweet_data: Raw tweet data from API
            search_term: Search term used

        Returns:
            Tweet dictionary
        """
        return {
            'id': tweet_data.get('tweet_id', ''),
            'title': tweet_data.get('text', '')[:100],
            'text': tweet_data.get('text', ''),
            'link': f"https://twitter.com/{tweet_data.get('user_name', '')}/status/{tweet_data.get('tweet_id', '')}",
            'score': tweet_data.get('favorites', 0),
            'retweets': tweet_data.get('retweets', 0),
            'author': tweet_data.get('user_name', 'unknown'),
            'timestamp': datetime.now(),
            'source': 'Twitter',
            'search_term': search_term
        }


# For testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = {
        'enabled': False,  # Enable if you have RapidAPI key
        'rapidapi_key': 'YOUR_RAPIDAPI_KEY',
        'max_tweets': 10
    }

    source = TwitterSource(config)
    tweets = source.fetch()

    print(f"\nFound {len(tweets)} tweets:\n")
    for i, tweet in enumerate(tweets, 1):
        print(f"{i}. @{tweet['author']}: {tweet['title']}...")
        print(f"   Likes: {tweet['score']}, Retweets: {tweet['retweets']}")
        print()
