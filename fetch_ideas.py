"""
AI Ideas/Creative Projects Report Generator
Focuses on innovative AI applications and creative projects
"""
import sys
import os

# Change to project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_dir)

# Add src to path
sys.path.insert(0, os.path.join(project_dir, 'src'))

import yaml
import logging
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from sources.hackernews import HackerNewsSource
from sources.github import GitHubSource
from sources.producthunt import ProductHuntSource
from sources.rss_feed import RSSSource
from sources.arxiv import ArxivSource
from sources.huggingface import HuggingFacePapersSource
from generator import MarkdownGenerator
from git_handler import GitHandler
from translator import translate_batch_with_claude, summarize_report_with_model


def deduplicate_ideas(data, logger):
    """
    Remove duplicate ideas across sections by link, falling back to title/name.
    """
    seen = set()
    deduped = {}
    duplicate_count = 0

    for section, items in data.items():
        unique_items = []
        for item in items:
            link = (item.get('link') or '').strip().lower()
            title = (item.get('title') or item.get('full_name') or item.get('name') or '').strip().lower()
            key = link or title

            if not key:
                unique_items.append(item)
                continue

            if key in seen:
                duplicate_count += 1
                continue

            seen.add(key)
            unique_items.append(item)

        deduped[section] = unique_items

    if duplicate_count:
        logger.info(f"Removed {duplicate_count} duplicate ideas")

    return deduped


def fetch_ai_ideas(dry_run=False):
    """
    Fetch AI creative ideas and innovative projects
    """
    # Load config
    config_path = os.path.join(project_dir, 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    logger = logging.getLogger('AIIdeasReport')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=" * 50)
    logger.info("AI创意点子报告 - 生成")
    logger.info("=" * 50)

    # Customize config for ideas-focused content
    hn_config = {
        'enabled': True,
        'keywords': [
            'Show HN', 'Ask HN', 'built with AI', 'AI app', 'AI tool',
            'GPT app', 'LLM tool', 'AI startup', 'AI project',
            'AI product', 'new AI', 'AI powered', 'using AI',
            'AI automation', 'AI agent', 'side project', 'built a'
        ],
        'max_posts': 30
    }

    github_config = {
        'enabled': True,
        'languages': ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust'],
        'keywords': [
            'AI', 'gpt', 'llm', 'chatbot', 'assistant',
            'agent', 'automation', 'tool', 'app', 'cli',
            'creative', 'innovative', 'novel'
        ],
        'max_repos': 20
    }

    producthunt_config = {
        'enabled': True,
        'max_products': 15
    }

    rss_config = {
        'enabled': True,
        'feeds': [
            'https://openai.com/blog/rss.xml',
            'https://www.anthropic.com/rss',
            'https://ai.googleblog.com/atom.xml',
            'https://www.technologyreview.com/feed/',
        ],
        'max_articles': 20
    }

    arxiv_config = {
        'enabled': True,
        'categories': ['cs.AI', 'cs.CL', 'cs.LG', 'cs.CV', 'stat.ML'],
        'keywords': [
            'language model', 'LLM', 'agent', 'GPT', 'transformer',
            'machine learning', 'deep learning', 'multimodal',
            'retrieval', 'automation', 'tool'
        ],
        'max_results': 50,
        'max_posts': 15
    }

    huggingface_config = {
        'enabled': True,
        'max_papers': 15
    }

    # Initialize sources
    hn_source = HackerNewsSource(hn_config)
    github_source = GitHubSource(github_config)
    ph_source = ProductHuntSource(producthunt_config)
    rss_source = RSSSource(rss_config)
    arxiv_source = ArxivSource(arxiv_config)
    hf_source = HuggingFacePapersSource(huggingface_config)

    ideas_data = {}

    # Fetch from Hacker News (focus on Show HN posts)
    try:
        logger.info("Fetching AI ideas from Hacker News...")
        hn_items = hn_source.fetch()

        # Filter for creative projects
        creative_items = []
        for item in hn_items:
            title = item.get('title', '').lower()
            # Look for project showcases and creative applications
            if any(keyword in title for keyword in ['show hn', 'built', 'built with', 'using', 'app', 'tool', 'project']):
                item['category'] = 'HN Creative Project'
                creative_items.append(item)

        ideas_data['Hacker News创意项目'] = creative_items
        logger.info(f"Found {len(creative_items)} creative projects on Hacker News")

    except Exception as e:
        logger.error(f"Failed to fetch from Hacker News: {e}")

    # Fetch from GitHub (focus on recently created AI tools)
    try:
        logger.info("Fetching AI tools from GitHub Trending...")
        github_items = github_source.fetch()

        # Filter for tools and applications
        tool_items = []
        for item in github_items:
            description = item.get('description', '').lower()
            name = item.get('name', '').lower()

            # Look for tools, apps, and creative implementations
            if any(keyword in description + name for keyword in ['tool', 'app', 'cli', 'assistant', 'bot', 'automation', 'agent']):
                item['category'] = 'GitHub AI Tool'
                tool_items.append(item)

        ideas_data['GitHub AI工具'] = tool_items
        logger.info(f"Found {len(tool_items)} AI tools on GitHub")

    except Exception as e:
        logger.error(f"Failed to fetch from GitHub: {e}")

    # Fetch from Product Hunt
    try:
        logger.info("Fetching AI products from Product Hunt...")
        ph_items = ph_source.fetch()

        if ph_items:
            # Mark as Product Hunt products
            for item in ph_items:
                item['category'] = 'Product Hunt AI产品'

            ideas_data['Product Hunt新产品'] = ph_items
            logger.info(f"Found {len(ph_items)} AI products on Product Hunt")

    except Exception as e:
        logger.error(f"Failed to fetch from Product Hunt: {e}")

    # Fetch from RSS feeds
    try:
        logger.info("Fetching AI articles from RSS feeds...")
        rss_items = rss_source.fetch()

        if rss_items:
            # Mark as RSS articles
            for item in rss_items:
                item['category'] = 'AI Blog文章'

            ideas_data['AI博客文章'] = rss_items
            logger.info(f"Found {len(rss_items)} AI articles from RSS feeds")

    except Exception as e:
        logger.error(f"Failed to fetch from RSS feeds: {e}")

    # Fetch from arXiv
    try:
        logger.info("Fetching AI papers from arXiv...")
        arxiv_items = arxiv_source.fetch()

        if arxiv_items:
            for item in arxiv_items:
                item['category'] = 'arXiv AI论文'

            ideas_data['arXiv AI论文'] = arxiv_items
            logger.info(f"Found {len(arxiv_items)} AI papers from arXiv")

    except Exception as e:
        logger.error(f"Failed to fetch from arXiv: {e}")

    # Fetch from Hugging Face Daily Papers
    try:
        logger.info("Fetching Hugging Face Daily Papers...")
        hf_items = hf_source.fetch()

        if hf_items:
            for item in hf_items:
                item['category'] = 'Hugging Face热门论文'

            ideas_data['Hugging Face热门论文'] = hf_items
            logger.info(f"Found {len(hf_items)} Hugging Face papers")

    except Exception as e:
        logger.error(f"Failed to fetch from Hugging Face papers: {e}")

    # Generate ideas report
    total_ideas = sum(len(items) for items in ideas_data.values())
    if total_ideas == 0:
        logger.warning("No AI ideas collected")
        return False

    ideas_data = deduplicate_ideas(ideas_data, logger)
    total_ideas = sum(len(items) for items in ideas_data.values())

    logger.info(f"Total AI ideas collected: {total_ideas}")

    # Translate
    translations = translate_batch_with_claude(ideas_data)

    # Summarize before writing and committing the report
    logger.info("Generating Chinese AI ideas summary...")
    ai_summary = summarize_report_with_model(ideas_data, 'AI创意点子日报')

    # Generate report
    report_config = {
        'output_dir': 'ideas-reports',
        'date_format': '%Y-%m-%d',
        'translate_to_chinese': True,
        'include_summary': True
    }

    generator = MarkdownGenerator(report_config)

    # Create ideas-focused report content
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"{date_str}-ai-ideas.md"
    filepath = os.path.join('ideas-reports', filename)

    logger.info(f"Generating AI ideas report: {filepath}")

    # Build custom report content
    content = build_ideas_report(ideas_data, date_str, translations, ai_summary)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"AI ideas report generated: {filepath}")

    # Git commit
    if dry_run:
        logger.info("Dry run - skipping Git commit")
    else:
        git_handler = GitHandler(config.get('github', {}))
        success = git_handler.full_commit_workflow(filepath)

        if success:
            logger.info("AI ideas report successfully pushed to GitHub")
        else:
            logger.warning("Git push failed, but report generated locally")

    logger.info("=" * 50)
    logger.info("AI创意点子报告 - 完成")
    logger.info("=" * 50)

    return True


def build_ideas_report(data, date_str, translations, ai_summary=None):
    """
    Build AI ideas report content
    """
    lines = []

    # Header
    lines.append(f"# AI创意点子日报 - {date_str}")
    lines.append("")
    lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📊 创意概览")
    lines.append("")

    total = sum(len(items) for items in data.values())
    lines.append(f"**今日收集AI创意: {total}个**")
    lines.append("")
    lines.append("### 数据来源")
    for source, items in data.items():
        lines.append(f"- {source}: {len(items)}个创意")
    lines.append("")

    if ai_summary:
        lines.append("## 📌 今日中文总结")
        lines.append("")
        lines.append(ai_summary)
        lines.append("")

    # Hacker News creative projects
    if 'Hacker News创意项目' in data and data['Hacker News创意项目']:
        lines.append("## 💡 Hacker News创意项目")
        lines.append("")

        for i, item in enumerate(data['Hacker News创意项目'], 1):
            title_en = item.get('title', 'Untitled')
            title_cn = translations.get(title_en, title_en)
            link = item.get('link', '')
            score = item.get('score', 0)
            comments = item.get('comments', 0)

            # 主标题（中文翻译）
            lines.append(f"{i}. **{title_cn}**")
            # 原文标题和链接
            lines.append(f"   - 原文: {title_en}")
            lines.append(f"   - 链接: {link}")
            # 简要统计
            lines.append(f"   - {score}点 | {comments}评论")
            lines.append("")

    # GitHub AI tools
    if 'GitHub AI工具' in data and data['GitHub AI工具']:
        lines.append("## 🔧 GitHub热门AI工具")
        lines.append("")

        for i, item in enumerate(data['GitHub AI工具'], 1):
            full_name = item.get('full_name', '')
            link = item.get('link', '')
            description_en = item.get('description', 'No description')
            description_cn = translations.get(description_en, description_en)
            language = item.get('language', 'Unknown')
            stars = item.get('stars', 0)
            stars_today = item.get('stars_today', 0)

            # 项目名
            lines.append(f"{i}. **{full_name}**")
            # 中文描述
            lines.append(f"   - {description_cn}")
            # 原描述和链接
            if description_cn != description_en:
                lines.append(f"   - 原描述: {description_en}")
            lines.append(f"   - 链接: {link}")
            lines.append(f"   - {language} | {stars} stars | 今日+{stars_today}")
            lines.append("")

    # Product Hunt products
    if 'Product Hunt新产品' in data and data['Product Hunt新产品']:
        lines.append("## 🚀 Product Hunt热门AI产品")
        lines.append("")

        for i, item in enumerate(data['Product Hunt新产品'], 1):
            name = item.get('name', 'Unknown')
            description_en = item.get('description', '')
            description_cn = translations.get(description_en, description_en)
            link = item.get('link', '')
            upvotes = item.get('upvotes', 0)

            # 产品名
            lines.append(f"{i}. **{name}**")
            # 中文描述
            if description_cn:
                lines.append(f"   - {description_cn}")
            # 原描述和链接
            if description_cn != description_en and description_en:
                lines.append(f"   - 原描述: {description_en}")
            lines.append(f"   - 链接: {link}")
            lines.append(f"   - {upvotes}票")
            lines.append("")

    # AI Blog articles
    if 'AI博客文章' in data and data['AI博客文章']:
        lines.append("## 📰 AI博客精选文章")
        lines.append("")

        for i, item in enumerate(data['AI博客文章'], 1):
            title_en = item.get('title', 'Untitled')
            title_cn = translations.get(title_en, title_en)
            link = item.get('link', '')
            source = item.get('source', 'Unknown')

            # 中文标题
            lines.append(f"{i}. **{title_cn}**")
            # 原标题和链接
            lines.append(f"   - 原标题: {title_en}")
            lines.append(f"   - 链接: {link}")
            lines.append(f"   - 来源: {source}")
            lines.append("")

    # Research papers
    for section_name in ['arXiv AI论文', 'Hugging Face热门论文']:
        if section_name in data and data[section_name]:
            lines.append(f"## 📄 {section_name}")
            lines.append("")

            for i, item in enumerate(data[section_name], 1):
                title_en = item.get('title', 'Untitled')
                title_cn = translations.get(title_en, title_en)
                link = item.get('link', '')
                description_en = item.get('description', '')
                description_cn = translations.get(description_en, description_en)
                author = item.get('author', 'Unknown')
                score = item.get('score', 0)
                comments = item.get('comments', 0)

                lines.append(f"{i}. **{title_cn}**")
                if title_cn != title_en:
                    lines.append(f"   - 原文: {title_en}")
                if description_cn:
                    lines.append(f"   - 摘要: {description_cn[:240]}")
                lines.append(f"   - 链接: {link}")
                lines.append(f"   - 作者/来源: {author}")
                if score or comments:
                    lines.append(f"   - 热度: {score} | 评论: {comments}")
                lines.append("")

    # Summary - 简化
    lines.append("## 🎯 今日创意总结")
    lines.append("")
    total = sum(len(items) for items in data.values())
    lines.append(f"收集了{total}个AI创意，涵盖:")
    lines.append("")
    lines.append("- 新AI应用和工具")
    lines.append("- 产品创新思路")
    lines.append("- 技术实现方案")
    lines.append("- AI技术洞察")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*AI创意点子日报 - 每日收集AI创新应用和创意点子*")
    lines.append("")
    lines.append(f"[查看历史报告](../ideas-reports/)")
    lines.append("")

    return '\n'.join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate AI creative ideas daily report'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate report without Git commit'
    )
    args = parser.parse_args()

    fetch_ai_ideas(dry_run=args.dry_run)
