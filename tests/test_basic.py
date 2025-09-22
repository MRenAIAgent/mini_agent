"""Basic test to verify test infrastructure works."""

import pytest


def test_basic_assertion():
    """Test that basic assertions work."""
    assert True


def test_basic_math():
    """Test basic math operations."""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12


@pytest.mark.unit
def test_with_marker():
    """Test that pytest markers work."""
    assert "hello" == "hello"


class TestBasicClass:
    """Test that test classes work."""

    def test_method(self):
        """Test that test methods in classes work."""
        assert [1, 2, 3] == [1, 2, 3]

    def test_another_method(self):
        """Test another method."""
        data = {"key": "value"}
        assert data["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])