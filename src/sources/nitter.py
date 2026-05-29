"""
Twitter/X data source using Nitter instances
Nitter is an open-source Twitter frontend that allows access without API
"""
import requests
from bs4 import BeautifulSoup
import logging
import random
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseSource


class NitterSource(BaseSource):
    """
    Fetch AI-related tweets using Nitter instances
    No API key required, but instances may be blocked occasionally
    """

    # List of public Nitter instances (some may be blocked)
    NITTER_INSTANCES = [
        'https://nitter.net',
        'https://nitter.poast.org',
        'https://nitter.privacydev.net',
        'https://nitter.d420.de',
        'https://nitter.nohost.network',
        'https://nitter.rawbit.io',
        'https://nitter.ktachibana.com',
        'https://nitter.unixfox.eu',
    ]

    # AI-related Twitter accounts to follow
    AI_ACCOUNTS = [
        'OpenAI',
        'AnthropicAI',
        'GoogleAI',
        'DeepMindAI',
        'MicrosoftAI',
        'ylecun',  # Yann LeCun
        'karpathy',  # Andrej Karpathy
        'goodfellow_ian',  # Ian Goodfellow
        'soumithchintala',  # Soumith Chintala
        'AndrewYNg',  # Andrew Ng
        'demishassabis',  # Demis Hassabis
        'satelliteoflove',  # Mike Butcher (TechCrunch AI)
    ]

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.accounts = config.get('accounts', self.AI_ACCOUNTS)
        self.max_tweets = config.get('max_tweets', 20)
        self.use_instances = config.get('instances', self.NITTER_INSTANCES)

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch tweets from AI-related accounts via Nitter

        Returns:
            List of tweet dictionaries
        """
        if not self.enabled:
            self.logger.info("Nitter source is disabled")
            return []

        self.logger.info("Fetching tweets via Nitter instances")

        tweets = []

        # Try multiple instances in case some are blocked
        for instance in self.use_instances[:3]:  # Try top 3 instances
            try:
                instance_tweets = self._fetch_from_instance(instance)
                if instance_tweets:
                    tweets.extend(instance_tweets)
                    self.logger.info(f"Fetched {len(instance_tweets)} tweets from {instance}")
                    break  # Success, no need to try other instances
            except Exception as e:
                self.logger.warning(f"Failed to fetch from {instance}: {e}")
                continue

        # Sort by engagement and limit
        tweets.sort(key=lambda x: x.get('score', 0), reverse=True)
        tweets = self._limit_items(tweets)

        self.logger.info(f"Total tweets collected: {len(tweets)}")
        return tweets

    def _fetch_from_instance(self, instance_url: str) -> List[Dict[str, Any]]:
        """
        Fetch tweets from a specific Nitter instance

        Args:
            instance_url: Nitter instance URL

        Returns:
            List of tweet dictionaries
        """
        tweets = []

        for account in self.accounts[:5]:  # Limit accounts to avoid overload
            try:
                account_tweets = self._fetch_account_tweets(instance_url, account)
                tweets.extend(account_tweets)
            except Exception as e:
                self.logger.warning(f"Failed to fetch @{account}: {e}")

        return tweets

    def _fetch_account_tweets(self, instance_url: str, account: str) -> List[Dict[str, Any]]:
        """
        Fetch tweets from a specific account

        Args:
            instance_url: Nitter instance URL
            account: Twitter account name

        Returns:
            List of tweet dictionaries
        """
        url = f"{instance_url}/{account}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AI Daily Report Bot)',
            'Accept': 'text/html,application/xhtml+xml',
        }

        response = self._retry_request(
            lambda: requests.get(url, headers=headers, timeout=15)
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        tweets = []

        # Find tweet items
        tweet_items = soup.find_all('div', class_='timeline-item')

        for item in tweet_items[:10]:  # Limit per account
            tweet = self._parse_tweet_item(item, account)
            if tweet:
                tweets.append(tweet)

        return tweets

    def _parse_tweet_item(self, item, account: str) -> Dict[str, Any]:
        """
        Parse a tweet item from HTML

        Args:
            item: BeautifulSoup tweet element
            account: Account name

        Returns:
            Tweet dictionary or None
        """
        try:
            # Tweet content
            content_elem = item.find('div', class_='tweet-content')
            if not content_elem:
                return None

            text = content_elem.get_text(strip=True)

            # Tweet link
            link_elem = item.find('a', class_='tweet-link')
            if link_elem:
                tweet_path = link_elem.get('href', '')
                tweet_link = f"https://twitter.com{tweet_path}"
            else:
                tweet_link = f"https://twitter.com/{account}"

            # Stats (likes, retweets, replies)
            stats = {}
            stats_items = item.find_all('div', class_='tweet-stat')
            for stat in stats_items:
                icon = stat.find('span', class_='tweet-stat-icon')
                if icon:
                    icon_class = icon.get('class', [])
                    if 'icon-heart' in icon_class:
                        stats['likes'] = self._parse_stat_number(stat.get_text(strip=True))
                    elif 'icon-retweet' in icon_class:
                        stats['retweets'] = self._parse_stat_number(stat.get_text(strip=True))
                    elif 'icon-comment' in icon_class:
                        stats['replies'] = self._parse_stat_number(stat.get_text(strip=True))

            # Timestamp
            date_elem = item.find('span', class_='tweet-date')
            timestamp = datetime.now()
            if date_elem:
                date_link = date_elem.find('a')
                if date_link:
                    date_text = date_link.get('title', '')
                    # Nitter format: "May 29, 2026 · 2:30 PM UTC"
                    try:
                        # Simplified parsing - just use current time
                        pass
                    except:
                        pass

            # Calculate engagement score
            score = stats.get('likes', 0) + stats.get('retweets', 0) * 2

            return {
                'id': f"{account}-{len(text)}",
                'title': text[:100],  # Use first 100 chars as title
                'text': text,
                'link': tweet_link,
                'author': account,
                'score': score,
                'likes': stats.get('likes', 0),
                'retweets': stats.get('retweets', 0),
                'replies': stats.get('replies', 0),
                'timestamp': timestamp,
                'source': 'Twitter',
                'account': account
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse tweet: {e}")
            return None

    def _parse_stat_number(self, text: str) -> int:
        """
        Parse stat number from text (handles K and M suffixes)

        Args:
            text: Stat text like '1.2K' or '500'

        Returns:
            Integer number
        """
        text = text.strip()

        if 'K' in text:
            match = self._extract_number(text)
            return int(match * 1000) if match else 0
        elif 'M' in text:
            match = self._extract_number(text)
            return int(match * 1000000) if match else 0
        else:
            try:
                return int(text)
            except:
                return 0

    def _extract_number(self, text: str) -> float:
        """
        Extract number from text

        Args:
            text: Text containing number

        Returns:
            Float number or 0
        """
        import re
        match = re.search(r'(\d+\.?\d*)', text)
        return float(match.group(1)) if match else 0


# For testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = {
        'enabled': True,
        'accounts': ['OpenAI', 'AnthropicAI'],
        'max_tweets': 10,
        'instances': NitterSource.NITTER_INSTANCES
    }

    source = NitterSource(config)
    tweets = source.fetch()

    print(f"\nFound {len(tweets)} tweets:\n")
    for i, tweet in enumerate(tweets, 1):
        print(f"{i}. @{tweet['author']}: {tweet['title'][:80]}...")
        print(f"   Likes: {tweet['likes']}, Retweets: {tweet['retweets']}")
        print(f"   Link: {tweet['link']}")
        print()