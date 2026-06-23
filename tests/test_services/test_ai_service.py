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


@pytest.mark.asyncio
@patch("app.services.ai_service.print")
@patch("app.services.ai_service.types.GenerateContentConfig")
@patch("app.services.ai_service.types.ThinkingConfig")
@patch("app.services.ai_service.genai.Client")
async def test_get_char_made_by_ai_replaces_unspecified_attributes_and_returns_text(
    mock_client_class,
    mock_thinking_config,
    mock_generate_config,
    mock_print
):
    attributes = make_attributes(
        name=None,
        race=None,
        god=None
    )
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(
        text="{'name': 'Aria'}"
    )
    mock_client_class.return_value = client
    mock_thinking_config.return_value = "thinking-config"
    mock_generate_config.return_value = "generate-config"

    result = await get_char_made_by_ai(attributes)

    assert result == "{'name': 'Aria'}"
    assert attributes["name"] == "Not specified"
    assert attributes["race"] == "Not specified"
    assert attributes["god"] == "Not specified"

    mock_print.assert_called_once_with(attributes)
    mock_client_class.assert_called_once_with()
    mock_thinking_config.assert_called_once_with(thinking_level="low")
    mock_generate_config.assert_called_once_with(
        thinking_config="thinking-config"
    )

    client.models.generate_content.assert_called_once()
    call_kwargs = client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-3-flash-preview"
    assert call_kwargs["config"] == "generate-config"
    assert "Character Name: Not specified;" in call_kwargs["contents"]
    assert "Race: Not specified;" in call_kwargs["contents"]
    assert "Please answer only EXACTLY in this format" in (
        call_kwargs["contents"]
    )


@pytest.mark.asyncio
@patch("app.services.ai_service.print")
@patch("app.services.ai_service.genai.Client")
async def test_get_char_made_by_ai_keeps_provided_attributes_in_prompt(
    mock_client_class,
    mock_print
):
    attributes = make_attributes()
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(
        text="{'name': 'Aria'}"
    )
    mock_client_class.return_value = client

    result = await get_char_made_by_ai(attributes)

    assert result == "{'name': 'Aria'}"

    prompt = client.models.generate_content.call_args.kwargs["contents"]
    assert "Game System: D&D;" in prompt
    assert "Character Name: Aria;" in prompt
    assert "Class: Mage;" in prompt
    assert "Race: Elf;" in prompt
    assert "Origin: Forest;" in prompt
    assert "Favorite Weapon: Staff;" in prompt
    assert "Planned build: Fire mage;" in prompt
    assert "Not specified" not in prompt

    mock_print.assert_called_once_with(attributes)


@pytest.mark.asyncio
@patch("app.services.ai_service.print")
@patch("app.services.ai_service.genai.Client")
async def test_get_char_made_by_ai_reraises_generate_content_error(
    mock_client_class,
    mock_print
):
    attributes = make_attributes()
    client = MagicMock()
    client.models.generate_content.side_effect = RuntimeError("ai failed")
    mock_client_class.return_value = client

    with pytest.raises(RuntimeError, match="ai failed"):
        await get_char_made_by_ai(attributes)

    mock_print.assert_called_once_with(attributes)
