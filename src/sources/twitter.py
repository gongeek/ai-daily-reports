"""
Twitter/X data source implementation (optional)
Uses RapidAPI for Twitter data
"""
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseSource


class TwitterSource(BaseSource):
    """
    Fetch AI-related tweets using RapidAPI
    Optional source - gracefully disabled if API key not configured
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('rapidapi_key')
        self.enabled = config.get('enabled', False)

        # RapidAPI configuration
        self.api_host = "twitter-api45.p.rapidapi.com"
        self.base_url = f"https://{self.api_host}"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch tweets related to AI topics

        Returns:
            List of tweet dictionaries
        """
        if not self.enabled or not self.api_key or 'YOUR_' in self.api_key:
            self.logger.info("Twitter source is disabled or not configured")
            return []

        self.logger.info("Fetching tweets from Twitter via RapidAPI")

        # Try to fetch trending tweets
        tweets = self._fetch_tweets()

        # Limit results
        tweets = self._limit_items(tweets)

        self.logger.info(f"Found {len(tweets)} tweets")
        return tweets

    def _fetch_tweets(self) -> List[Dict[str, Any]]:
        """
        Fetch tweets using RapidAPI

        Returns:
            List of tweet dictionaries
        """
        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }

        # Search for AI-related tweets
        search_terms = ['AI', 'machine learning', 'GPT', 'LLM', 'artificial intelligence']

        tweets = []

        for term in search_terms[:3]:  # Limit searches to avoid quota exhaustion
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