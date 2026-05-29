"""
Hugging Face Daily Papers source.
"""
import requests
from dateutil import parser as date_parser
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseSource


class HuggingFacePapersSource(BaseSource):
    """
    Fetch papers selected by the Hugging Face Daily Papers community.
    """

    API_URL = "https://huggingface.co/api/daily_papers"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_papers = config.get('max_papers', self.max_items)

    def fetch(self) -> List[Dict[str, Any]]:
        if not self.enabled:
            self.logger.info("Hugging Face papers source is disabled")
            return []

        self.logger.info("Fetching Hugging Face Daily Papers")
        response = self._retry_request(
            lambda: requests.get(self.API_URL, timeout=15),
            max_retries=2,
            delay=2
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch Hugging Face papers: HTTP {response.status_code}")

        papers = []
        for item in response.json()[:self.max_papers]:
            paper = self._format_item(item)
            if paper:
                papers.append(paper)

        papers = self._limit_items(papers)
        self.logger.info(f"Found {len(papers)} Hugging Face papers")
        return papers

    def _format_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        paper = item.get('paper') or {}
        paper_id = paper.get('id', '')
        title = paper.get('title') or item.get('title') or ''
        summary = paper.get('summary') or item.get('summary') or ''
        upvotes = paper.get('upvotes') or 0

        if not title or not paper_id:
            return None

        published_at = (
            paper.get('submittedOnDailyAt')
            or item.get('publishedAt')
            or paper.get('publishedAt')
        )
        try:
            timestamp = date_parser.parse(published_at).replace(tzinfo=None) if published_at else datetime.now()
        except Exception:
            timestamp = datetime.now()

        authors = []
        for author in paper.get('authors', []):
            name = author.get('name')
            if name:
                authors.append(name)

        return {
            'id': paper_id,
            'title': title,
            'description': summary[:500],
            'link': f"https://huggingface.co/papers/{paper_id}",
            'score': upvotes,
            'comments': item.get('numComments', 0),
            'author': ', '.join(authors[:3]) if authors else 'Unknown',
            'timestamp': timestamp,
            'source': 'Hugging Face Daily Papers',
            'category': 'AI Research Paper'
        }
