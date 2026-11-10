from unittest.mock import MagicMock, patch

from tools.web_search import scrape_page, search_web


def test_search_web_returns_results_on_success():
    mock_results = [{"title": "Test", "href": "https://example.com", "body": "Snippet"}]
    mock_ddgs = MagicMock()
    mock_ddgs.__enter__.return_value.text.return_value = iter(mock_results)

    with patch("tools.web_search.DDGS", return_value=mock_ddgs):
        results = search_web("test query")

    assert len(results) == 1
    assert results[0]["title"] == "Test"


def test_search_web_returns_error_dict_on_failure():
    with patch("tools.web_search.DDGS", side_effect=RuntimeError("network down")):
        results = search_web("test query")

    assert len(results) == 1
    assert "unavailable" in results[0]["body"]
    assert "network down" not in results[0]["body"]


def test_scrape_page_returns_empty_for_blank_url():
    assert scrape_page("") == ""
