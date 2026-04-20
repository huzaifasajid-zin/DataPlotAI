import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load .env automatically for all scrapers
load_dotenv()


class BaseScraper:
    def __init__(self, base_url, headers=None):
        self.base_url = base_url
        self.headers = headers or {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

    def fetch_page(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_html(self, html):
        if html is None:
            return None
        return BeautifulSoup(html, "html.parser")

    def scrape(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement the scrape method.")