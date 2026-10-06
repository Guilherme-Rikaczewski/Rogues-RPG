from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_service import get_char_made_by_ai


def make_attributes(**overrides):
    data = {
        "game": "D&D",
        "name": "Aria",
        "char_class": "Mage",
        "race": "Elf",
        "origin": "Forest",
        "weapon": "Staff",
        "god": "Mystra",
        "build": "Fire mage",
    }
    data.update(overrides)
    return data


@pytest.fixture
def gemini_client():
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(
        text="{'name': 'Aria'}"
    )

    with patch(
        "app.services.ai_service.genai.Client",
        return_value=client
    ):
        yield client


def get_prompt(gemini_client):
    return gemini_client.models.generate_content.call_args.kwargs["contents"]


async def test_get_char_made_by_ai_returns_model_text(gemini_client):
    result = await get_char_made_by_ai(make_attributes())

    assert result == "{'name': 'Aria'}"
    gemini_client.models.generate_content.assert_called_once()


async def test_get_char_made_by_ai_marks_missing_attributes_in_prompt(
    gemini_client
):
    await get_char_made_by_ai(
        make_attributes(name=None, race=None, god=None)
    )

    prompt = get_prompt(gemini_client)
    assert "Character Name: Not specified;" in prompt
    assert "Race: Not specified;" in prompt
    assert (
        "Serves the fictional god from the chosen system: Not specified;"
        in prompt
    )
    assert "Class: Mage;" in prompt


async def test_get_char_made_by_ai_keeps_provided_attributes_in_prompt(
    gemini_client
):
    await get_char_made_by_ai(make_attributes())

    prompt = get_prompt(gemini_client)
    assert "Game System: D&D;" in prompt
    assert "Character Name: Aria;" in prompt
    assert "Class: Mage;" in prompt
    assert "Race: Elf;" in prompt
    assert "Origin: Forest;" in prompt
    assert "Favorite Weapon: Staff;" in prompt
    assert "Planned build: Fire mage;" in prompt
    assert "Not specified" not in prompt


async def test_get_char_made_by_ai_asks_for_dict_format(gemini_client):
    await get_char_made_by_ai(make_attributes())

    prompt = get_prompt(gemini_client)
    assert "Please answer only EXACTLY in this format" in prompt
    for key in ("'lore'", "'physical_characteristics'", "'personality_traits'"):
        assert key in prompt


async def test_get_char_made_by_ai_uses_gemini_flash_with_low_thinking(
    gemini_client
):
    await get_char_made_by_ai(make_attributes())

    kwargs = gemini_client.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "gemini-3-flash-preview"
    assert kwargs["config"].thinking_config.thinking_level.lower() == "low"


async def test_get_char_made_by_ai_reraises_generate_content_error(
    gemini_client
):
    gemini_client.models.generate_content.side_effect = RuntimeError(
        "ai failed"
    )

    with pytest.raises(RuntimeError, match="ai failed"):
        await get_char_made_by_ai(make_attributes())
