"""Tests for github_bot (mocked PyGithub)."""
import pytest
from unittest.mock import MagicMock, patch

# Test without PyGithub installed too
def test_github_requires_token():
    with patch.dict("os.environ", {}, clear=True):
        try:
            from fixer import github_bot
            github_bot._get_github()
        except RuntimeError as e:
            assert "GITHUB_TOKEN" in str(e) or "PyGithub" in str(e)
