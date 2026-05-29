"""
arXiv research paper source for AI daily reports.
"""
import requests
import feedparser
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseSource


class ArxivSource(BaseSource):
    """
    Fetch recent AI/ML/NLP papers from the arXiv API.
    """

    API_URL = "https://export.arxiv.org/api/query"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.categories = config.get('categories', ['cs.AI', 'cs.CL', 'cs.LG', 'stat.ML'])
        self.keywords = config.get('keywords', [
            'language model', 'llm', 'agent', 'gpt', 'transformer',
            'machine learning', 'deep learning', 'reinforcement learning',
            'retrieval', 'multimodal', 'computer vision'
        ])
        self.max_results = config.get('max_results', self.max_items)
        self.timeout = config.get('timeout', 12)

    def fetch(self) -> List[Dict[str, Any]]:
        if not self.enabled:
            self.logger.info("arXiv source is disabled")
            return []

        self.logger.info("Fetching recent AI papers from arXiv")
        try:
            response = self._retry_request(self._request_arxiv, max_retries=1, delay=2)
        except Exception as e:
            self.logger.warning(f"arXiv API unavailable this run; skipping arXiv papers: {e}")
            return []

        if response.status_code == 429:
            self.logger.warning("arXiv API rate limited this run; skipping arXiv papers")
            return []

        if response.status_code != 200:
            raise Exception(f"Failed to fetch arXiv papers: HTTP {response.status_code}")

        feed = feedparser.parse(response.content)
        papers = []

        for entry in feed.entries:
            paper = self._format_entry(entry)
            if paper:
                papers.append(paper)

        papers = self._filter_by_keywords(papers, self.keywords)
        papers = self._limit_items(papers)
        self.logger.info(f"Found {len(papers)} AI papers from arXiv")
        return papers

    def _request_arxiv(self):
        category_query = ' OR '.join(f'cat:{category}' for category in self.categories)
        params = {
            'search_query': category_query,
            'start': 0,
            'max_results': self.max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        headers = {'User-Agent': 'AI Daily Report Bot/1.0'}
        return requests.get(self.API_URL, params=params, headers=headers, timeout=self.timeout)

    def _format_entry(self, entry) -> Dict[str, Any]:
        title = ' '.join(entry.get('title', '').split())
        summary = ' '.join(entry.get('summary', '').split())
        link = entry.get('link', '')
        published = entry.get('published_parsed') or entry.get('updated_parsed')

        if not title or not link:
            return None

        authors = []
        for author in entry.get('authors', []):
            name = author.get('name')
            if name:
                authors.append(name)

        return {
            'id': entry.get('id', '').rsplit('/', 1)[-1],
            'title': title,
            'description': summary[:500],
            'link': link,
            'score': 0,
            'comments': 0,
            'author': ', '.join(authors[:3]) if authors else 'Unknown',
            'timestamp': datetime(*published[:6]) if published else datetime.now(),
            'source': 'arXiv',
            'category': 'AI Research Paper'
        }
