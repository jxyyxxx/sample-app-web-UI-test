import pytest

if __name__ == "__main__":
    pytest.main([
        "-v",
        "--alluredir=reports/allure-results",
        "--clean-alluredir",
    ])
