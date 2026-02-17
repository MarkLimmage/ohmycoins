# Add this file to override the default database fixture
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session


@pytest.fixture(scope="session", autouse=True)
def db():
    """Mock database fixture to avoid connection errors during unit tests."""
    mock_session = MagicMock(spec=Session)
    yield mock_session
