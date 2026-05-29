"""
Translation helper using Claude Code API
"""
import subprocess
import json
import logging
import os
import re
import shutil
from typing import Dict, List


def _get_claude_binary():
    return os.environ.get('CLAUDE_BIN') or shutil.which('claude')


def _is_claude_enabled() -> bool:
    return os.environ.get('CLAUDE_TRANSLATION_ENABLED', 'true').lower() not in ('0', 'false', 'no')


def _run_claude_prompt(prompt: str, max_budget: str = None) -> str:
    claude_bin = _get_claude_binary()
    if not _is_claude_enabled():
        raise RuntimeError("Claude disabled by CLAUDE_TRANSLATION_ENABLED")
    if not claude_bin:
        raise RuntimeError("Claude CLI not found")

    command = [
        claude_bin,
        '-p',
        prompt,
        '--output-format',
        'text',
        '--permission-mode',
        'dontAsk',
        '--max-budget-usd',
        max_budget or os.environ.get('CLAUDE_TRANSLATION_MAX_BUDGET_USD', '0.30')
    ]

    model = os.environ.get('CLAUDE_TRANSLATION_MODEL')
    if model:
        command.extend(['--model', model])

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=int(os.environ.get('CLAUDE_TRANSLATION_TIMEOUT', '120'))
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Claude command failed")

    return result.stdout.strip()


def translate_titles_with_claude(titles: List[str]) -> Dict[str, str]:
    """
    Translate English titles to Chinese using Claude Code

    Args:
        titles: List of English titles to translate

    Returns:
        Dictionary mapping original titles to Chinese translations
    """
    logger = logging.getLogger('TranslationHelper')
    logger.info(f"Translating {len(titles)} titles to Chinese")

    translations = {}
    if not _is_claude_enabled():
        logger.info("Claude translation disabled by CLAUDE_TRANSLATION_ENABLED")
        return _identity_translations(titles)
    if not _get_claude_binary():
        logger.warning("Claude CLI not found; using original text")
        return _identity_translations(titles)

    # Prepare translation prompt
    prompt = f"""Translate the following English titles to Chinese. Keep technical terms in English when appropriate (like AI, GPT, LLM, API, etc.). Return a JSON array with format: [{{"original": "English title", "translated": "Chinese translation"}}]

Titles to translate:
{json.dumps(titles, ensure_ascii=False)}

Only return the JSON array, no additional text."""

    try:
        response_data = _parse_json_array(_run_claude_prompt(prompt))
        for item in response_data:
            translations[item['original']] = item['translated']
        logger.info(f"Successfully translated {len(translations)} titles")

    except Exception as e:
        logger.error(f"Translation error: {e}")
        # Fallback: return original titles
        for title in titles:
            translations[title] = title

    return translations


def summarize_report_with_claude(data: Dict[str, List[Dict]], report_name: str) -> str:
    """
    Generate a concise Chinese summary before the report is written and committed.
    Falls back to a deterministic local summary if Claude is unavailable.
    """
    logger = logging.getLogger('TranslationHelper')
    compact_items = []

    for source, items in data.items():
        for item in items[:12]:
            title = item.get('title') or item.get('full_name') or item.get('name') or ''
            description = item.get('description', '')
            if title:
                compact_items.append({
                    'source': source,
                    'title': title[:180],
                    'description': description[:260],
                    'score': item.get('score', 0),
                    'comments': item.get('comments', 0)
                })

    if not compact_items:
        return "今日未收集到足够内容，无法形成趋势总结。"

    prompt = f"""你是AI行业研究助手。请基于以下{report_name}素材，生成中文总结。

要求：
1. 输出 Markdown。
2. 先给出 3-5 条「核心观察」。
3. 再给出 3 条「值得关注」。
4. 语言简洁，不要编造素材中没有的信息。

素材：
{json.dumps(compact_items, ensure_ascii=False)}
"""

    try:
        summary = _run_claude_prompt(
            prompt,
            max_budget=os.environ.get('CLAUDE_SUMMARY_MAX_BUDGET_USD', '0.30')
        )
        logger.info("Successfully generated Claude summary")
        return summary.strip()
    except Exception as e:
        logger.warning(f"Claude summary failed; using local summary: {e}")
        return _local_summary(data)


def _local_summary(data: Dict[str, List[Dict]]) -> str:
    total = sum(len(items) for items in data.values())
    active_sources = [source for source, items in data.items() if items]
    lines = [
        f"- 今日共收集 {total} 条内容，覆盖 {len(active_sources)} 个活跃数据源。",
        f"- 活跃来源包括：{', '.join(active_sources[:8])}。",
        "- 重点内容集中在 LLM、AI agent、模型评测、开发工具和 AI 产品应用。",
        "",
        "**值得关注**",
        "- 优先查看高热度 Hacker News 讨论和 GitHub 新增 star 明显的项目。",
        "- 论文类来源适合跟踪方法变化，产品和博客来源适合发现应用机会。",
        "- arXiv 等外部 API 偶发限流时会自动跳过，不影响报告生成。"
    ]
    return "\n".join(lines)


def _identity_translations(titles: List[str]) -> Dict[str, str]:
    return {title: title for title in titles}


def _parse_json_array(text: str):
    """
    Parse a JSON array from Claude text output, accepting fenced JSON too.
    """
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\[[\s\S]*\]', cleaned)
        if match:
            return json.loads(match.group(0))
        raise


def translate_batch_with_claude(data: Dict[str, List[Dict]]) -> Dict[str, str]:
    """
    Translate all titles and descriptions from collected data

    Args:
        data: Collected data from sources

    Returns:
        Dictionary mapping original text to Chinese translations
    """
    logger = logging.getLogger('TranslationHelper')

    all_texts = []

    # Collect all titles and descriptions
    for source, items in data.items():
        for item in items:
            if 'title' in item:
                all_texts.append(item['title'])
            if 'description' in item:
                all_texts.append(item['description'])

    all_texts = list(dict.fromkeys(text for text in all_texts if text))

    if not all_texts:
        logger.info("No text to translate")
        return {}

    # Translate in batches to avoid overwhelming
    translations = {}

    # Process in batches to avoid excessive Claude CLI startups in cron.
    batch_size = int(os.environ.get('CLAUDE_TRANSLATION_BATCH_SIZE', '60'))
    for i in range(0, len(all_texts), batch_size):
        batch = all_texts[i:i+batch_size]
        batch_translations = translate_titles_with_claude(batch)
        translations.update(batch_translations)

    return translations


def translate_batch_with_claode(data: Dict[str, List[Dict]]) -> Dict[str, str]:
    """
    Backward-compatible alias for the previous misspelled function name.
    """
    return translate_batch_with_claude(data)


# For testing without Claude Code CLI
def mock_translate_for_testing(data: Dict[str, List[Dict]]) -> Dict[str, str]:
    """
    Mock translation for testing purposes

    Args:
        data: Collected data from sources

    Returns:
        Dictionary with mock Chinese translations
    """
    translations = {}

    # Simple mock translations
    common_translations = {
        'AI': 'AI',
        'machine learning': '机器学习',
        'deep learning': '深度学习',
        'neural network': '神经网络',
        'LLM': 'LLM',
        'GPT': 'GPT',
        'model': '模型',
        'training': '训练',
        'dataset': '数据集',
        'generated': '生成',
        'video': '视频',
        'YouTube': 'YouTube',
        'GitHub': 'GitHub',
        'repository': '仓库',
        'stars': 'Stars',
        'today': '今日',
        'Python': 'Python',
        'tool': '工具',
        'crawler': '爬虫',
        'speech': '语音',
        'generation': '生成'
    }

    for source, items in data.items():
        for item in items:
            if 'title' in item:
                title = item['title']
                # Simple mock translation
                translations[title] = title  # For now, keep original
            if 'description' in item:
                desc = item['description']
                translations[desc] = desc  # For now, keep original

    return translations


if __name__ == "__main__":
    # Test translation
    test_titles = [
        "YouTube to automatically label AI-generated videos",
        "New GPT-4 model released",
        "Machine learning framework for beginners"
    ]

    translations = translate_titles_with_claude(test_titles)

    print("\nTranslations:")
    for original, translated in translations.items():
        print(f"  {original} -> {translated}")
