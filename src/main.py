"""
Main program entry point with bilingual support
"""
import sys
import os
import yaml
import logging
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources.hackernews import HackerNewsSource
from sources.github import GitHubSource
from sources.reddit import RedditSource
from sources.twitter import TwitterSource
from sources.nitter import NitterSource
from generator import MarkdownGenerator
from git_handler import GitHandler
from translator import mock_translate_for_testing  # Using mock for now


def setup_logging(config: dict) -> logging.Logger:
    """
    Setup logging configuration

    Args:
        config: Logging configuration dictionary

    Returns:
        Configured logger
    """
    log_config = config.get('logging', {})
    level = getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('file', 'logs/daily_report.log')
    log_format = log_config.get(
        'format',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure logging
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger('AIReportGenerator')


def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config.yaml file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file not found
        yaml.YAMLError: If YAML parsing fails
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def initialize_sources(config: dict) -> dict:
    """
    Initialize all data sources

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary of source instances
    """
    sources_config = config.get('sources', {})
    sources = {}

    # Hacker News
    if sources_config.get('hackernews', {}).get('enabled', True):
        sources['Hacker News'] = HackerNewsSource(
            sources_config['hackernews']
        )

    # GitHub Trending
    if sources_config.get('github', {}).get('enabled', True):
        sources['GitHub Trending'] = GitHubSource(
            sources_config['github']
        )

    # Reddit
    if sources_config.get('reddit', {}).get('enabled', True):
        sources['Reddit'] = RedditSource(
            sources_config['reddit']
        )

    # Twitter (optional - via Nitter)
    if sources_config.get('twitter', {}).get('enabled', False):
        # Use Nitter instead of paid API
        twitter_config = sources_config['twitter']
        twitter_config['enabled'] = True  # Force enable for Nitter
        sources['Twitter'] = NitterSource(twitter_config)

    return sources


def fetch_all_data(sources: dict, logger: logging.Logger) -> dict:
    """
    Fetch data from all sources concurrently

    Args:
        sources: Dictionary of source instances
        logger: Logger instance

    Returns:
        Dictionary with source names as keys and data lists as values
    """
    logger.info(f"Fetching data from {len(sources)} sources")
    all_data = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit fetch tasks
        future_to_source = {
            executor.submit(source.fetch): name
            for name, source in sources.items()
        }

        # Collect results
        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                data = future.result()
                all_data[source_name] = data
                logger.info(f"Fetched {len(data)} items from {source_name}")
            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}")
                all_data[source_name] = []

    return all_data


def main(config_path: str = 'config.yaml', dry_run: bool = False) -> bool:
    """
    Main execution function with bilingual support

    Args:
        config_path: Path to configuration file
        dry_run: If True, skip Git commit and push

    Returns:
        True if successful
    """
    try:
        # Load configuration
        config = load_config(config_path)

        # Setup logging
        logger = setup_logging(config)

        logger.info("=" * 50)
        logger.info("AI日报生成器 - 启动")
        logger.info("AI Daily Report Generator - Starting")
        logger.info("=" * 50)

        # Initialize sources
        sources = initialize_sources(config)

        if not sources:
            logger.error("No sources configured or enabled")
            return False

        # Fetch data
        all_data = fetch_all_data(sources, logger)

        # Check if any data collected
        total_items = sum(len(items) for items in all_data.values())
        if total_items == 0:
            logger.warning("No data collected from any source")
            return False

        logger.info(f"Total items collected: {total_items}")
        logger.info(f"总计收集: {total_items} 条内容")

        # Translate to Chinese
        logger.info("开始翻译标题和描述到中文...")
        translations = mock_translate_for_testing(all_data)
        logger.info(f"Translated {len(translations)} text items")

        # Generate report with translations
        report_config = config.get('report', {})
        report_config['translate_to_chinese'] = config.get('translate_to_chinese', True)

        generator = MarkdownGenerator(report_config)
        report_path = generator.generate(all_data, translated_titles=translations)

        logger.info(f"Report generated: {report_path}")
        logger.info(f"报告已生成: {report_path}")

        # Git commit and push
        if not dry_run:
            git_handler = GitHandler(config.get('github', {}))
            success = git_handler.full_commit_workflow(report_path)

            if success:
                logger.info("Report successfully committed and pushed to GitHub")
                logger.info("报告已成功提交到GitHub")
            else:
                logger.warning("Git commit failed, but report was generated locally")
                logger.warning("Git提交失败，但报告已在本地生成")
        else:
            logger.info("Dry run - skipping Git commit")
            logger.info("测试运行 - 跳过Git提交")

        logger.info("=" * 50)
        logger.info("AI日报生成器 - 完成")
        logger.info("AI Daily Report Generator - Completed")
        logger.info("=" * 50)

        return True

    except Exception as e:
        logging.error(f"Main execution failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate AI trends daily report'
    )

    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate report without Git commit'
    )

    args = parser.parse_args()

    success = main(config_path=args.config, dry_run=args.dry_run)

    sys.exit(0 if success else 1)