import os
import pytest

from ..app.services.extract import extract_action_items


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


def test_empty_input():
    assert extract_action_items("") == []


def test_no_action_items():
    text = "We had a great meeting today. Everyone agreed on the direction."
    items = extract_action_items(text)
    assert items == []


def test_keyword_prefixed_lines():
    text = """
    TODO: Send follow-up email
    Action: Schedule code review
    Next: Deploy to staging
    """.strip()

    items = extract_action_items(text)
    assert any("Send follow-up email" in item for item in items)
    assert any("Schedule code review" in item for item in items)
    assert any("Deploy to staging" in item for item in items)


def test_mixed_bullet_styles():
    text = """
    - Fix login bug
    • Update documentation
    * Refactor auth module
    """.strip()

    items = extract_action_items(text)
    assert "Fix login bug" in items
    assert "Update documentation" in items
    assert "Refactor auth module" in items


def test_numbered_list():
    text = """
    1. Write unit tests
    2. Run linter
    3. Open pull request
    """.strip()

    items = extract_action_items(text)
    assert "Write unit tests" in items
    assert "Run linter" in items
    assert "Open pull request" in items


def test_checkbox_todo_marker():
    text = """
    [todo] Review PR comments
    [todo] Update changelog
    """.strip()

    items = extract_action_items(text)
    assert "Review PR comments" in items
    assert "Update changelog" in items


def test_deduplication():
    text = """
    - Fix the bug
    - Fix the bug
    - fix the bug
    """.strip()

    items = extract_action_items(text)
    assert items.count("Fix the bug") == 1


def test_whitespace_only_input():
    assert extract_action_items("   \n\n\t  ") == []


def test_narrative_imperative_fallback():
    text = "Implement the new caching layer. Fix the memory leak."
    items = extract_action_items(text)
    assert any("Implement" in item for item in items)
    assert any("Fix" in item for item in items)
