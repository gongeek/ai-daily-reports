"""
Markdown report generator with Chinese translation support
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
from collections import Counter


class MarkdownGenerator:
    """
    Generate daily AI trends report in Markdown format with bilingual support
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize generator with configuration

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.output_dir = config.get('output_dir', 'reports')
        self.date_format = config.get('date_format', '%Y-%m-%d')
        self.logger = logging.getLogger('MarkdownGenerator')
        self.translate_to_chinese = config.get('translate_to_chinese', True)

        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"Created output directory: {self.output_dir}")

    def generate(self, data: Dict[str, List[Dict]], date: datetime = None, translated_titles: Dict[str, str] = None, ai_summary: str = None) -> str:
        """
        Generate daily report from collected data with bilingual support

        Args:
            data: Dictionary with source names as keys and item lists as values
            date: Report date (defaults to today)
            translated_titles: Dictionary mapping original titles to Chinese translations

        Returns:
            Path to generated report file
        """
        if not date:
            date = datetime.now()

        report_date = date.strftime(self.date_format)
        filename = f"{report_date}.md"
        filepath = os.path.join(self.output_dir, filename)

        self.logger.info(f"Generating report for {report_date}")

        # Generate Markdown content with bilingual support
        content = self._build_report_content(data, report_date, translated_titles or {}, ai_summary=ai_summary)

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info(f"Report saved to {filepath}")
        return filepath

    def _build_report_content(self, data: Dict[str, List[Dict]], date_str: str, translated_titles: Dict[str, str] = None, ai_summary: str = None) -> str:
        """
        Build Markdown report content with bilingual support

        Args:
            data: Collected data from sources
            date_str: Date string for report
            translated_titles: Dictionary of translated titles

        Returns:
            Markdown content string
        """
        translated_titles = translated_titles or {}
        lines = []

        # Header - bilingual
        lines.append(f"# AI趋势日报 - {date_str}")
        lines.append("")
        lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Overview section - bilingual
        lines.append("## 📊 数据概览")
        overview_stats = self._generate_overview(data)
        lines.extend(overview_stats)
        lines.append("")

        if ai_summary:
            lines.append("## 📌 今日中文总结")
            lines.append("")
            lines.append(ai_summary)
            lines.append("")

        # Hacker News section
        if 'Hacker News' in data and data['Hacker News']:
            lines.append("## 🔥 Hacker News热门AI文章")
            lines.append("")
            hn_items = self._format_hackernews_items(data['Hacker News'], translated_titles)
            lines.extend(hn_items)
            lines.append("")

        # Reddit section
        if 'Reddit' in data and data['Reddit']:
            lines.append("## 💬 Reddit热门帖子")
            lines.append("")
            reddit_items = self._format_reddit_items(data['Reddit'], translated_titles)
            lines.extend(reddit_items)
            lines.append("")

        # GitHub Trending section
        if 'GitHub Trending' in data and data['GitHub Trending']:
            lines.append("## 💻 GitHub热门AI项目")
            lines.append("")
            github_items = self._format_github_items(data['GitHub Trending'], translated_titles)
            lines.extend(github_items)
            lines.append("")

        # Twitter section (optional)
        if 'Twitter' in data and data['Twitter']:
            lines.append("## 🐦 AI Tweets")
            twitter_items = self._format_twitter_items(data['Twitter'])
            lines.extend(twitter_items)
            lines.append("")

        rendered_sources = set([
            'Hacker News',
            'Reddit',
            'GitHub Trending',
            'Twitter'
        ])
        for source_name, items in data.items():
            if source_name in rendered_sources or not items:
                continue
            lines.append(f"## {source_name}")
            lines.append("")
            lines.extend(self._format_generic_items(items, translated_titles))
            lines.append("")

        # Summary section
        if self.config.get('include_summary', True):
            lines.append("## 📈 Summary & Key Trends")
            summary = self._generate_summary(data)
            lines.extend(summary)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*This report is automatically generated by AI Daily Report Generator.*")
        lines.append("")
        lines.append(f"[View all reports](../)")
        lines.append("")

        return '\n'.join(lines)

    def _generate_overview(self, data: Dict[str, List[Dict]]) -> List[str]:
        """
        Generate overview statistics

        Args:
            data: Collected data

        Returns:
            List of overview lines
        """
        total_items = sum(len(items) for items in data.values())
        sources = [name for name, items in data.items() if items]

        lines = []
        lines.append(f"**Total items collected:** {total_items}")
        lines.append("")
        lines.append("**Active sources:**")

        for source in sources:
            count = len(data[source])
            lines.append(f"- {source}: {count} items")

        lines.append("")

        return lines

    def _format_hackernews_items(self, items: List[Dict], translated_titles: Dict[str, str] = None) -> List[str]:
        """
        Format Hacker News items with bilingual support

        Args:
            items: List of HN story dictionaries
            translated_titles: Dictionary of translated titles

        Returns:
            List of formatted lines
        """
        translated_titles = translated_titles or {}
        lines = []

        for i, item in enumerate(items, 1):
            title_en = item.get('title', 'Untitled')
            title_cn = translated_titles.get(title_en, title_en)
            link = item.get('link', '')
            score = item.get('score', 0)
            comments = item.get('comments', 0)

            # Bilingual format
            lines.append(f"{i}. **{title_cn}**")
            if self.translate_to_chinese and title_cn != title_en:
                lines.append(f"   - 英文标题: {title_en}")
            lines.append(f"   - 链接: [{link}]({link})")
            lines.append(f"   - 得分: {score} 点 | 评论: {comments} 条")
            lines.append("")

        return lines

    def _format_reddit_items(self, items: List[Dict], translated_titles: Dict[str, str] = None) -> List[str]:
        """
        Format Reddit items grouped by subreddit with bilingual support

        Args:
            items: List of Reddit post dictionaries
            translated_titles: Dictionary of translated titles

        Returns:
            List of formatted lines
        """
        translated_titles = translated_titles or {}
        lines = []

        # Group by subreddit
        by_subreddit = {}
        for item in items:
            subreddit = item.get('subreddit', 'unknown')
            if subreddit not in by_subreddit:
                by_subreddit[subreddit] = []
            by_subreddit[subreddit].append(item)

        for subreddit, posts in by_subreddit.items():
            lines.append(f"### r/{subreddit}")
            lines.append("")

            for i, post in enumerate(posts[:10], 1):  # Limit per subreddit
                title_en = post.get('title', 'Untitled')[:100]
                title_cn = translated_titles.get(post.get('title', ''), title_en)
                link = post.get('link', '')
                score = post.get('score', 0)
                comments = post.get('comments', 0)

                lines.append(f"{i}. **{title_cn}**")
                if self.translate_to_chinese and title_cn != title_en:
                    lines.append(f"   - 英文标题: {title_en}")
                lines.append(f"   - 链接: [{link}]({link})")
                lines.append(f"   - 赞同: {score} | 评论: {comments} 条")
                lines.append("")

        return lines

    def _format_github_items(self, items: List[Dict], translated_titles: Dict[str, str] = None) -> List[str]:
        """
        Format GitHub Trending items with bilingual support

        Args:
            items: List of GitHub repo dictionaries
            translated_titles: Dictionary of translated descriptions

        Returns:
            List of formatted lines
        """
        translated_titles = translated_titles or {}
        lines = []

        for i, item in enumerate(items, 1):
            full_name = item.get('full_name', 'unknown/unknown')
            link = item.get('link', '')
            description_en = item.get('description', 'No description')[:150]
            description_cn = translated_titles.get(description_en, description_en)
            language = item.get('language', 'Unknown')
            stars = item.get('stars', 0)
            stars_today = item.get('stars_today', 0)

            lines.append(f"{i}. **[{full_name}]({link})**")
            lines.append(f"   - 描述: {description_cn}")
            if self.translate_to_chinese and description_cn != description_en:
                lines.append(f"   - 英文描述: {description_en}")
            lines.append(f"   - 语言: {language}")
            lines.append(f"   - Stars: {stars} 总计 | ⭐ 今日 +{stars_today}")
            lines.append("")

        return lines

    def _format_twitter_items(self, items: List[Dict]) -> List[str]:
        """
        Format Twitter items

        Args:
            items: List of tweet dictionaries

        Returns:
            List of formatted lines
        """
        lines = []

        for i, item in enumerate(items, 1):
            author = item.get('author', 'unknown')
            text = item.get('text', '')[:100]
            link = item.get('link', '')
            likes = item.get('score', 0)
            retweets = item.get('retweets', 0)

            lines.append(f"{i}. [@{author}]({link})")
            lines.append(f"   - {text}...")
            lines.append(f"   - **Likes:** {likes}, **Retweets:** {retweets}")
            lines.append("")

        return lines

    def _format_generic_items(self, items: List[Dict], translated_titles: Dict[str, str] = None) -> List[str]:
        """
        Format sources that do not have a custom renderer yet.

        Args:
            items: List of standardized item dictionaries
            translated_titles: Dictionary of translated titles/descriptions

        Returns:
            List of formatted lines
        """
        translated_titles = translated_titles or {}
        lines = []

        for i, item in enumerate(items, 1):
            title_en = item.get('title') or item.get('full_name') or item.get('name') or 'Untitled'
            title_cn = translated_titles.get(title_en, title_en)
            link = item.get('link', '')
            description_en = item.get('description', '')
            description_cn = translated_titles.get(description_en, description_en)
            score = item.get('score', 0)
            comments = item.get('comments', 0)
            author = item.get('author', '')

            if link:
                lines.append(f"{i}. **[{title_cn}]({link})**")
            else:
                lines.append(f"{i}. **{title_cn}**")

            if self.translate_to_chinese and title_cn != title_en:
                lines.append(f"   - 英文标题: {title_en}")
            if description_cn:
                lines.append(f"   - 摘要: {description_cn[:240]}")
            if self.translate_to_chinese and description_cn != description_en and description_en:
                lines.append(f"   - 英文摘要: {description_en[:240]}")
            if author:
                lines.append(f"   - 作者/来源: {author}")
            if score or comments:
                lines.append(f"   - 热度: {score} | 评论: {comments}")
            lines.append("")

        return lines

    def _generate_summary(self, data: Dict[str, List[Dict]]) -> List[str]:
        """
        Generate summary and key trends

        Args:
            data: Collected data

        Returns:
            List of summary lines
        """
        lines = []

        # Collect all titles/descriptions for analysis
        all_text = []
        for source, items in data.items():
            for item in items:
                all_text.append(item.get('title', '').lower())
                if 'description' in item:
                    all_text.append(item['description'].lower())

        # Extract trending topics (simple keyword frequency)
        keywords = [
            'GPT', 'LLM', 'neural', 'transformer', 'training',
            'model', 'dataset', 'NLP', 'vision', 'generative',
            'reinforcement', 'embedding', 'RAG', 'agents'
        ]

        keyword_counts = Counter()
        for text in all_text:
            for keyword in keywords:
                if keyword.lower() in text:
                    keyword_counts[keyword] += 1

        if keyword_counts:
            lines.append("**Popular topics today:**")
            for keyword, count in keyword_counts.most_common(5):
                lines.append(f"- {keyword}: {count} mentions")
            lines.append("")

        # Source highlights
        lines.append("**Highlights by source:**")
        lines.append("")

        if 'Hacker News' in data and data['Hacker News']:
            top_hn = data['Hacker News'][0] if data['Hacker News'] else None
            if top_hn:
                lines.append(f"- Hacker News: Top story \"{top_hn['title'][:50]}...\" with {top_hn['score']} points")

        if 'GitHub Trending' in data and data['GitHub Trending']:
            top_repo = data['GitHub Trending'][0] if data['GitHub Trending'] else None
            if top_repo:
                lines.append(f"- GitHub: Most trending repo \"{top_repo['full_name']}\" with +{top_repo['stars_today']} stars today")

        if 'Reddit' in data and data['Reddit']:
            top_reddit = data['Reddit'][0] if data['Reddit'] else None
            if top_reddit:
                lines.append(f"- Reddit: Top post from r/{top_reddit['subreddit']} with {top_reddit['score']} upvotes")

        lines.append("")

        return lines


# For testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test data
    test_data = {
        'Hacker News': [
            {
                'title': 'New GPT-4 model released',
                'link': 'https://example.com/1',
                'score': 500,
                'comments': 150
            }
        ],
        'Reddit': [
            {
                'title': 'Discussion on neural networks',
                'link': 'https://reddit.com/r/MachineLearning/test',
                'score': 200,
                'comments': 50,
                'subreddit': 'MachineLearning'
            }
        ],
        'GitHub Trending': [
            {
                'full_name': 'openai/gpt-code',
                'link': 'https://github.com/openai/gpt-code',
                'description': 'GPT code generation tool',
                'language': 'Python',
                'stars': 5000,
                'stars_today': 200
            }
        ]
    }

    config = {
        'output_dir': 'reports',
        'date_format': '%Y-%m-%d',
        'include_summary': True
    }

    generator = MarkdownGenerator(config)
    filepath = generator.generate(test_data)

    print(f"\nReport generated: {filepath}\n")

    # Display content
    with open(filepath, 'r') as f:
        print(f.read())
