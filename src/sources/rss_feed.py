"""
RSS feed source for AI blogs and newsletters
"""
import feedparser
import logging
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseSource


class RSSSource(BaseSource):
    """
    Fetch AI content from RSS feeds of AI blogs and newsletters
    """

    # Popular AI RSS feeds
    AI_RSS_FEEDS = [
        'https://openai.com/blog/rss.xml',
        'https://deepmind.google/research/rss.xml',
        'https://www.anthropic.com/rss',
        'https://blog.google/technology/ai/rss',
        'https://distill.pub/rss.xml',
        'https://ai.googleblog.com/atom.xml',
        # AI newsletters
        'https://www.importai.com/rss',
        'https://lastweekin.ai/rss',
        'https://artificialintelligence-news.com/feed',
        # Tech blogs with AI content
        'https://www.technologyreview.com/feed/',
        'https://www.wired.com/feed/rss',
    ]

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.feeds = config.get('feeds', self.AI_RSS_FEEDS)
        self.max_articles = config.get('max_articles', 30)
        self.logger.info(f"RSS source initialized with {len(self.feeds)} feeds")

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch AI articles from RSS feeds

        Returns:
            List of article dictionaries
        """
        if not self.enabled:
            self.logger.info("RSS source is disabled")
            return []

        self.logger.info(f"Fetching from {len(self.feeds)} RSS feeds")

        all_articles = []

        for feed_url in self.feeds:
            try:
                articles = self._fetch_feed(feed_url)
                all_articles.extend(articles)
                self.logger.info(f"Fetched {len(articles)} articles from {feed_url}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch {feed_url}: {e}")

        # Filter for AI-related content
        ai_articles = self._filter_ai_articles(all_articles)

        # Sort by date and limit
        ai_articles.sort(key=lambda x: x.get('timestamp', datetime.now()), reverse=True)
        ai_articles = ai_articles[:self.max_articles]

        self.logger.info(f"Total AI articles from RSS: {len(ai_articles)}")
        return ai_articles

    def _fetch_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """
        Fetch articles from a specific RSS feed

        Args:
            feed_url: RSS feed URL

        Returns:
            List of article dictionaries
        """
        try:
            feed = feedparser.parse(feed_url)

            articles = []
            for entry in feed.entries[:20]:  # Limit per feed
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('summary', entry.get('description', '')),
                    'author': entry.get('author', 'Unknown'),
                    'timestamp': datetime(*entry.get('published_parsed', datetime.now().timetuple())[:6]) if 'published_parsed' in entry else datetime.now(),
                    'source': feed.get('feed', {}).get('title', 'RSS Feed'),
                    'feed_url': feed_url
                }
                articles.append(article)

            return articles

        except Exception as e:
            self.logger.error(f"Error parsing feed {feed_url}: {e}")
            return []

    def _filter_ai_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter articles for AI-related content

        Args:
            articles: List of all articles

        Returns:
            Filtered AI articles
        """
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'deep learning',
            'gpt', 'llm', 'language model', 'neural network',
            'chatbot', 'assistant', 'automation',
            'openai', 'anthropic', 'deepmind', 'transformer'
        ]

        filtered = []
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()

            if any(keyword in text for keyword in ai_keywords):
                article['category'] = 'AI Blog文章'
                filtered.append(article)

        return filtered


# For testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = {
        'enabled': True,
        'feeds': RSSSource.AI_RSS_FEEDS[:5],  # Test with first 5 feeds
        'max_articles': 10
    }

    source = RSSSource(config)
    articles = source.fetch()

    print(f"\nFound {len(articles)} AI articles from RSS feeds:\n")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title'][:80]}...")
        print(f"   Source: {article['source']}")
        print(f"   Link: {article['link']}")
        print()