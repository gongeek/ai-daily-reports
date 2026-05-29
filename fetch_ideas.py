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
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from sources.hackernews import HackerNewsSource
from sources.github import GitHubSource
from sources.producthunt import ProductHuntSource
from sources.rss_feed import RSSSource
from generator import MarkdownGenerator
from git_handler import GitHandler
from translator import mock_translate_for_testing


def fetch_ai_ideas():
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

    # Initialize sources
    hn_source = HackerNewsSource(hn_config)
    github_source = GitHubSource(github_config)
    ph_source = ProductHuntSource(producthunt_config)
    rss_source = RSSSource(rss_config)

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

    # Generate ideas report
    total_ideas = sum(len(items) for items in ideas_data.values())
    if total_ideas == 0:
        logger.warning("No AI ideas collected")
        return False

    logger.info(f"Total AI ideas collected: {total_ideas}")

    # Translate
    translations = mock_translate_for_testing(ideas_data)

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
    content = build_ideas_report(ideas_data, date_str, translations)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"AI ideas report generated: {filepath}")

    # Git commit
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


def build_ideas_report(data, date_str, translations):
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

    # Hacker News creative projects
    if 'Hacker News创意项目' in data and data['Hacker News创意项目']:
        lines.append("## 💡 Hacker News创意项目")
        lines.append("")
        lines.append("*来自技术社区的AI创新应用展示*")
        lines.append("")

        for i, item in enumerate(data['Hacker News创意项目'], 1):
            title_en = item.get('title', 'Untitled')
            title_cn = translations.get(title_en, title_en)
            link = item.get('link', '')
            score = item.get('score', 0)
            comments = item.get('comments', 0)

            lines.append(f"{i}. **{title_cn}**")
            if title_cn != title_en:
                lines.append(f"   - 原标题: {title_en}")
            lines.append(f"   - 链接: [{link}]({link})")
            lines.append(f"   - 关注度: {score}点 | 讨论: {comments}条")
            lines.append(f"   - 💭 创意类型: 新AI应用/工具展示")
            lines.append("")

    # GitHub AI tools
    if 'GitHub AI工具' in data and data['GitHub AI工具']:
        lines.append("## 🔧 GitHub热门AI工具")
        lines.append("")
        lines.append("*开源AI工具和自动化项目*")
        lines.append("")

        for i, item in enumerate(data['GitHub AI工具'], 1):
            full_name = item.get('full_name', '')
            link = item.get('link', '')
            description_en = item.get('description', 'No description')
            description_cn = translations.get(description_en, description_en)
            language = item.get('language', 'Unknown')
            stars = item.get('stars', 0)
            stars_today = item.get('stars_today', 0)

            lines.append(f"{i}. **[{full_name}]({link})**")
            lines.append(f"   - 功能: {description_cn}")
            if description_cn != description_en:
                lines.append(f"   - 原描述: {description_en}")
            lines.append(f"   - 技术栈: {language}")
            lines.append(f"   - Stars: {stars} | 今日+{stars_today}")
            lines.append(f"   - 💭 创意类型: AI工具/自动化实现")
            lines.append("")

    # Product Hunt products
    if 'Product Hunt新产品' in data and data['Product Hunt新产品']:
        lines.append("## 🚀 Product Hunt热门AI产品")
        lines.append("")
        lines.append("*最新发布的AI产品和创新应用*")
        lines.append("")

        for i, item in enumerate(data['Product Hunt新产品'], 1):
            name = item.get('name', 'Unknown')
            description_en = item.get('description', '')
            description_cn = translations.get(description_en, description_en)
            link = item.get('link', '')
            upvotes = item.get('upvotes', 0)

            lines.append(f"{i}. **{name}**")
            lines.append(f"   - 产品描述: {description_cn}")
            if description_cn != description_en and description_en:
                lines.append(f"   - 英文描述: {description_en}")
            lines.append(f"   - 产品链接: [{link}]({link})")
            lines.append(f"   - 用户投票: {upvotes}票")
            lines.append(f"   - 💭 创意类型: 新AI产品发布")
            lines.append("")

    # AI Blog articles
    if 'AI博客文章' in data and data['AI博客文章']:
        lines.append("## 📰 AI博客精选文章")
        lines.append("")
        lines.append("*来自AI公司和研究机构的技术文章*")
        lines.append("")

        for i, item in enumerate(data['AI博客文章'], 1):
            title_en = item.get('title', 'Untitled')
            title_cn = translations.get(title_en, title_en)
            link = item.get('link', '')
            source = item.get('source', 'Unknown')

            lines.append(f"{i}. **{title_cn}**")
            if title_cn != title_en:
                lines.append(f"   - 原标题: {title_en}")
            lines.append(f"   - 文章链接: [{link}]({link})")
            lines.append(f"   - 来源: {source}")
            lines.append(f"   - 💭 创意类型: AI技术洞察")
            lines.append("")

    # Summary
    lines.append("## 🎯 创意趋势分析")
    lines.append("")
    lines.append("### 热门创意方向")
    lines.append("")
    lines.append("根据今日收集的AI创意，可以看到以下趋势：")
    lines.append("")
    lines.append("- **AI工具开发**: 各种AI辅助工具和自动化脚本")
    lines.append("- **应用创新**: 将AI应用于特定领域的创新方案")
    lines.append("- **开源项目**: 基于LLM的开源工具和框架")
    lines.append("- **创意实现**: 独特的AI应用场景和解决方案")
    lines.append("- **新产品发布**: Product Hunt上的AI创新产品")
    lines.append("- **技术洞察**: AI公司和研究机构的最新动态")
    lines.append("")

    lines.append("### 💡 启发价值")
    lines.append("")
    lines.append("这些创意展示了AI技术在不同领域的应用可能性，可以激发：")
    lines.append("")
    lines.append("- 产品创新思路")
    lines.append("- 技术实现方案")
    lines.append("- 商业应用场景")
    lines.append("- 开源项目灵感")
    lines.append("- 市场趋势洞察")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*本报告专注于AI创意应用，由AI创意点子日报系统生成*")
    lines.append("")
    lines.append(f"[查看所有报告](../ideas-reports/)")
    lines.append("")

    return '\n'.join(lines)


if __name__ == "__main__":
    fetch_ai_ideas()