"""Validation functions for the Trading Journey Database."""

import re

from app.models import MARKET_TYPES, TIMEFRAMES


# Pattern: alphanumeric, hyphens, and spaces only
TAG_PATTERN = re.compile(r'^[a-zA-Z0-9\- ]+$')


def validate_trade_enhanced_fields(form_data: dict) -> tuple[dict, list[str]]:
    """
    Validates enhanced trade fields. Returns (cleaned_data, errors).

    - market_type: must be in MARKET_TYPES or empty
    - timeframe: must be in TIMEFRAMES or empty
    - tags: comma-separated, max 5 items, each ≤30 chars, alphanumeric/hyphens/spaces only
    - screenshot_url: must start with http:// or https://, max 2048 chars, or empty
    - risk_reward_ratio: float in [0.1, 100.0] with ≤2 decimal places, or empty
    """
    cleaned_data = {}
    errors = []

    # Validate market_type
    market_type = form_data.get('market_type', '').strip()
    if market_type:
        if market_type not in MARKET_TYPES:
            errors.append(f"Market type must be one of: {', '.join(MARKET_TYPES)}")
        else:
            cleaned_data['market_type'] = market_type
    else:
        cleaned_data['market_type'] = None

    # Validate timeframe
    timeframe = form_data.get('timeframe', '').strip()
    if timeframe:
        if timeframe not in TIMEFRAMES:
            errors.append(f"Timeframe must be one of: {', '.join(TIMEFRAMES)}")
        else:
            cleaned_data['timeframe'] = timeframe
    else:
        cleaned_data['timeframe'] = None

    # Validate tags
    tags_raw = form_data.get('tags', '').strip()
    if tags_raw:
        tag_list = [t.strip() for t in tags_raw.split(',')]
        # Remove empty tags from splitting
        tag_list = [t for t in tag_list if t]

        if len(tag_list) > 5:
            errors.append("Tags: each tag must be ≤30 characters, maximum 5 tags allowed")
        else:
            tag_errors = False
            for tag in tag_list:
                if len(tag) > 30:
                    errors.append("Tags: each tag must be ≤30 characters, maximum 5 tags allowed")
                    tag_errors = True
                    break
                if not TAG_PATTERN.match(tag):
                    errors.append("Tags: only letters, numbers, hyphens, and spaces allowed")
                    tag_errors = True
                    break

            if not tag_errors:
                cleaned_data['tags'] = ','.join(tag_list)
    else:
        cleaned_data['tags'] = None

    # Validate screenshot_url
    screenshot_url = form_data.get('screenshot_url', '').strip()
    if screenshot_url:
        if not (screenshot_url.startswith('http://') or screenshot_url.startswith('https://')):
            errors.append("Screenshot URL must start with http:// or https://")
        elif len(screenshot_url) > 2048:
            errors.append("Screenshot URL must not exceed 2,048 characters")
        else:
            cleaned_data['screenshot_url'] = screenshot_url
    else:
        cleaned_data['screenshot_url'] = None

    # Validate risk_reward_ratio
    risk_reward_raw = form_data.get('risk_reward_ratio', '').strip()
    if risk_reward_raw:
        try:
            risk_reward = float(risk_reward_raw)

            # Check decimal places (≤2)
            if '.' in risk_reward_raw:
                decimal_part = risk_reward_raw.split('.')[1]
                if len(decimal_part) > 2:
                    errors.append("Risk-reward ratio must have at most 2 decimal places")
                    return cleaned_data, errors

            if risk_reward < 0.1 or risk_reward > 100.0:
                errors.append("Risk-reward ratio must be between 0.1 and 100.0")
            else:
                cleaned_data['risk_reward_ratio'] = risk_reward
        except ValueError:
            errors.append("Risk-reward ratio must be a valid number")
    else:
        cleaned_data['risk_reward_ratio'] = None

    return cleaned_data, errors


def validate_reflection(form_data: dict) -> tuple[dict, list[str]]:
    """
    Validates reflection fields. Returns (cleaned_data, errors).

    - lessons_learned: required, max 2000 chars
    - reflection_text, mistakes_made, what_went_well: optional, max 2000 chars each
    """
    cleaned_data = {}
    errors = []

    # Validate lessons_learned (required)
    lessons_learned = form_data.get('lessons_learned', '').strip()
    if not lessons_learned:
        errors.append("Lessons learned is required for reflections")
    elif len(lessons_learned) > 2000:
        errors.append("Lessons learned must not exceed 2,000 characters")
    else:
        cleaned_data['lessons_learned'] = lessons_learned

    # Validate optional fields
    optional_fields = ['reflection_text', 'mistakes_made', 'what_went_well']
    field_labels = {
        'reflection_text': 'Reflection text',
        'mistakes_made': 'Mistakes made',
        'what_went_well': 'What went well',
    }

    for field in optional_fields:
        value = form_data.get(field, '').strip()
        if value:
            if len(value) > 2000:
                errors.append(f"{field_labels[field]} must not exceed 2,000 characters")
            else:
                cleaned_data[field] = value
        else:
            cleaned_data[field] = None

    return cleaned_data, errors