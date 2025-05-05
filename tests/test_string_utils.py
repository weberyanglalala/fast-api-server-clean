import pytest
from src.utils.string_utils import slugify

def test_slugify_basic():
    """Test basic slugify functionality."""
    assert slugify("Hello World") == "hello-world"
    assert slugify("This is a Test") == "this-is-a-test"

def test_slugify_special_characters():
    """Test slugify with special characters."""
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("Test@Example.com") == "testexamplecom"

def test_slugify_duplicate_spaces():
    """Test slugify with duplicate spaces."""
    assert slugify("Hello  World") == "hello-world"
    assert slugify("Multiple   Spaces") == "multiple-spaces"

def test_slugify_leading_trailing_spaces():
    """Test slugify with leading and trailing spaces."""
    assert slugify(" Hello World ") == "hello-world"
    assert slugify("  Leading and Trailing  ") == "leading-and-trailing"

def test_slugify_empty_string():
    """Test slugify with an empty string."""
    assert slugify("") == ""