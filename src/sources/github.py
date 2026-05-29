"""
GitHub Trending data source implementation
"""
import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseSource


class GitHubSource(BaseSource):
    """
    Fetch trending AI projects from GitHub Trending page
    No API required, scrapes the trending page directly
    """

    TRENDING_URL = "https://github.com/trending"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.languages = config.get('languages', ['Python', 'Jupyter Notebook'])
        self.keywords = config.get('keywords', [
            'AI', 'machine-learning', 'deep-learning',
            'neural-network', 'NLP', 'GPT', 'LLM'
        ])

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch trending repositories from GitHub

        Returns:
            List of trending repository dictionaries
        """
        if not self.enabled:
            self.logger.info("GitHub source is disabled")
            return []

        self.logger.info("Fetching trending repositories from GitHub")

        # Fetch trending page
        html = self._fetch_trending_page()

        # Parse repositories
        repos = self._parse_repositories(html)

        # Filter by keywords and languages
        filtered_repos = self._filter_repos(repos)

        # Limit results
        filtered_repos = self._limit_items(filtered_repos)

        self.logger.info(f"Found {len(filtered_repos)} trending AI repositories")
        return filtered_repos

    def _fetch_trending_page(self) -> str:
        """
        Fetch GitHub trending page HTML

        Returns:
            HTML content string
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AI Daily Report Bot)'
        }

        response = self._retry_request(
            lambda: requests.get(self.TRENDING_URL, headers=headers, timeout=15)
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch GitHub trending: HTTP {response.status_code}")

        return response.text

    def _parse_repositories(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse repository information from HTML

        Args:
            html: GitHub trending page HTML

        Returns:
            List of repository dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        repos = []

        # Find all repository articles
        articles = soup.find_all('article', class_='Box-row')

        for article in articles:
            try:
                repo_info = self._parse_repo_article(article)
                if repo_info:
                    repos.append(repo_info)
            except Exception as e:
                self.logger.warning(f"Failed to parse repository: {e}")

        return repos

    def _parse_repo_article(self, article) -> Dict[str, Any]:
        """
        Parse individual repository article

        Args:
            article: BeautifulSoup article element

        Returns:
            Repository information dictionary
        """
        # Repository name and link
        h2 = article.find('h2', class_='h3')
        if not h2:
            return None

        link = h2.find('a')
        if not link:
            return None

        repo_path = link.get('href', '').strip('/')
        repo_name = repo_path.split('/')[-1] if repo_path else ''
        full_link = f"https://github.com/{repo_path}"

        # Description
        description_elem = article.find('p', class_='col-9')
        description = description_elem.text.strip() if description_elem else ''

        # Language
        lang_elem = article.find('span', itemprop='programmingLanguage')
        language = lang_elem.text.strip() if lang_elem else ''

        # Stars
        stars_elem = article.find('a', href=f'/{repo_path}/stargazers')
        stars_text = stars_elem.text.strip() if stars_elem else '0'
        total_stars = self._parse_star_count(stars_text)

        # Stars today
        stars_today_elem = article.find('span', class_='float-sm-right')
        stars_today = 0
        if stars_today_elem:
            stars_today_text = stars_today_elem.text.strip()
            match = re.search(r'(\d+)', stars_today_text)
            if match:
                stars_today = int(match.group(1))

        return {
            'name': repo_name,
            'full_name': repo_path,
            'title': repo_name,
            'description': description,
            'link': full_link,
            'language': language,
            'stars': total_stars,
            'stars_today': stars_today,
            'score': stars_today,
            'timestamp': datetime.now(),
            'source': 'GitHub Trending'
        }

    def _parse_star_count(self, text: str) -> int:
        """
        Parse star count from text (handles 'k' suffix)

        Args:
            text: Star count text like '1,234' or '12.3k'

        Returns:
            Integer star count
        """
        text = text.replace(',', '').strip()

        if 'k' in text.lower():
            match = re.search(r'(\d+\.?\d*)k', text.lower())
            if match:
                return int(float(match.group(1)) * 1000)

        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0

    def _filter_repos(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter repositories by keywords and languages

        Args:
            repos: List of repository dictionaries

        Returns:
            Filtered list
        """
        filtered = []

        for repo in repos:
            # Check language filter
            language = repo.get('language', '')
            if language not in self.languages:
                # Allow repos without language specified or with related languages
                if language and language not in ['', 'Unknown']:
                    continue

            # Check keyword filter
            combined_text = (
                repo.get('name', '') + ' ' +
                repo.get('description', '')
            ).lower()

            if any(keyword.lower() in combined_text for keyword in self.keywords):
                filtered.append(repo)

        return filtered


# For testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = {
        'enabled': True,
        'languages': ['Python', 'Jupyter Notebook'],
        'keywords': ['AI', 'machine-learning', 'deep-learning', 'NLP', 'GPT'],
        'max_repos': 10
    }

    source = GitHubSource(config)
    repos = source.fetch()

    print(f"\nFound {len(repos)} trending AI repositories:\n")
    for i, repo in enumerate(repos, 1):
        print(f"{i}. {repo['full_name']}")
        print(f"   {repo['description'][:80]}...")
        print(f"   Language: {repo['language']}, Stars: {repo['stars']}, Today: +{repo['stars_today']}")
        print(f"   Link: {repo['link']}")
        print()