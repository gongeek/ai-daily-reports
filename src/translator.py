"""
Translation helper using Claude Code API
"""
import subprocess
import json
import logging
from typing import Dict, List


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

    # Prepare translation prompt
    prompt = f"""Translate the following English titles to Chinese. Keep technical terms in English when appropriate (like AI, GPT, LLM, API, etc.). Return a JSON array with format: [{"original": "English title", "translated": "Chinese translation"}]

Titles to translate:
{json.dumps(titles, ensure_ascii=False)}

Only return the JSON array, no additional text."""

    try:
        # Call Claude Code via subprocess
        # Note: This assumes Claude Code CLI is available
        # In production, you might want to use the Anthropic API directly
        result = subprocess.run(
            ['claude', '--prompt', prompt, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # Parse JSON response
            response_data = json.loads(result.stdout)
            for item in response_data:
                translations[item['original']] = item['translated']
            logger.info(f"Successfully translated {len(translations)} titles")
        else:
            logger.warning(f"Translation failed: {result.stderr}")
            # Fallback: return original titles
            for title in titles:
                translations[title] = title

    except Exception as e:
        logger.error(f"Translation error: {e}")
        # Fallback: return original titles
        for title in titles:
            translations[title] = title

    return translations


def translate_batch_with_claode(data: Dict[str, List[Dict]]) -> Dict[str, str]:
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

    if not all_texts:
        logger.info("No text to translate")
        return {}

    # Translate in batches to avoid overwhelming
    translations = {}

    # Process in batches of 20
    batch_size = 20
    for i in range(0, len(all_texts), batch_size):
        batch = all_texts[i:i+batch_size]
        batch_translations = translate_titles_with_claude(batch)
        translations.update(batch_translations)

    return translations


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