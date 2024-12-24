import pytest
import sys

if __name__ == "__main__":
    # Run the tests with verbose output
    sys.exit(pytest.main(["-v", "src/tests/test_bot.py"]))