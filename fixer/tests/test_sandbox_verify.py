"""Tests for sandbox_verify (mocked Daytona)."""
import pytest
from unittest.mock import MagicMock, patch


def test_verify_requires_daytona_key():
    with patch.dict("os.environ", {}, clear=True):
        try:
            from fixer import sandbox_verify
            sandbox_verify._get_daytona()
        except RuntimeError as e:
            assert "DAYTONA" in str(e) or "daytona" in str(e).lower()
