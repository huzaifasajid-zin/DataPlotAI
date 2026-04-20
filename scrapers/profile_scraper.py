import re
import os
import urllib.parse
import requests
from scrapers.base_scraper import BaseScraper
from models import db, ProfileListing, ScrapeTask


class ProfileScraper(BaseScraper):
    def __init__(self, task_id):
        super().__init__(base_url="")
        self.task_id = task_id

    # ------------------------------------------------------------------
    # Searlo search
    # ------------------------------------------------------------------

    def _searlo_search(self, query: str) -> list[dict]:
        """
        Call Searlo API and return a list of result dicts.
        Mirrors your test file: tries each header variant with GET then POST.
        """
        api_key = os.getenv("SEARLO_API_KEY")
        if not api_key:
            print("[ProfileScraper] Missing SEARLO_API_KEY in .env")
            return []

        url = "https://api.searlo.tech/api/v1/search"

        headers_variants = [
            {"Authorization": f"Bearer {api_key}"},
            {"x-api-key": api_key},
            {"api_key": api_key},
            {"X-API-KEY": api_key},
        ]

        for headers in headers_variants:
            try:
                # GET attempt
                res = requests.get(
                    f"{url}?q={urllib.parse.quote(query)}",
                    headers=headers,
                    timeout=15,
                )
                if res.status_code == 200:
                    return self._extract_items(res.json())

                # POST fallback (same as your test file)
                res = requests.post(
                    url,
                    headers=headers,
                    json={"query": query},
                    timeout=15,
                )
                if res.status_code == 200:
                    return self._extract_items(res.json())

            except Exception as e:
                print(f"[ProfileScraper] Searlo request error: {e}")
                continue

        print("[ProfileScraper] All Searlo header variants failed.")
        return []

    @staticmethod
    def _extract_items(data) -> list[dict]:
        """
        Normalise Searlo response — handles common shapes:
          { "results": [...] }
          { "organic": [...] }
          { "items": [...] }
          [ ... ]  (bare list)
        """
        if isinstance(data, list):
            return data
        for key in ("results", "organic", "items", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return []

    # ------------------------------------------------------------------
    # Title parser
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_title(title: str) -> tuple[str, str]:
        """Return (name, headline) from a LinkedIn search-result title."""
        title = re.sub(r"[\|\-·]\s*LinkedIn\s*$", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s*LinkedIn\s*$", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"^LinkedIn\s*[\|\-·]\s*", "", title, flags=re.IGNORECASE).strip()

        for sep in (" - ", " | ", " · ", " \u00b7 ", " ... "):
            if sep in title:
                parts = title.split(sep, 1)
                return parts[0].strip(), parts[1].strip()

        return title.strip(), ""

    # ------------------------------------------------------------------
    # Relevance check
    # ------------------------------------------------------------------

    @staticmethod
    def _is_relevant(name: str, headline: str, snippet: str, keywords: list[str]) -> bool:
        text = f"{name} {headline} {snippet}".lower()
        for k in keywords:
            if any(word in text for word in k.lower().split()):
                return True
        return False

    # ------------------------------------------------------------------
    # Main scrape
    # ------------------------------------------------------------------

    def scrape(self, keyword: str) -> int:
        task = ScrapeTask.query.get(self.task_id)
        keywords = [k.strip() for k in keyword.split(",") if k.strip()]
        location = task.location or ""
        experience = getattr(task, "experience", "") or ""

        # Build query variants to maximise results
        base = f'site:linkedin.com/in/ {keyword}'
        if location:
            base += f' "{location}"'
        if experience:
            base += f' "{experience}"'

        queries = [base]
        # Broader variant without quotes around location
        if location:
            queries.append(f'site:linkedin.com/in/ {keyword} {location}')

        seen_links: set[str] = set()
        count = 0
        TARGET = 25

        for query in queries:
            if count >= TARGET:
                break

            print(f"[ProfileScraper] Querying: {query}")
            items = self._searlo_search(query)
            print(f"[ProfileScraper] Searlo returned {len(items)} items")

            for item in items:
                if count >= TARGET:
                    break

                link    = item.get("link") or item.get("url") or ""
                title   = item.get("title") or ""
                snippet = item.get("snippet") or item.get("description") or ""

                if "linkedin.com/in/" not in link:
                    continue

                link = link.split("?")[0].rstrip("/")
                name, headline = self._parse_title(title)

                if not name:
                    continue

                if not headline and snippet:
                    headline = snippet[:300]

                if not self._is_relevant(name, headline, snippet, keywords):
                    continue

                if link in seen_links:
                    continue
                seen_links.add(link)

                if ProfileListing.query.filter_by(task_id=self.task_id, link=link).first():
                    continue

                profile = ProfileListing(
                    task_id=self.task_id,
                    name=name.strip()[:255],
                    headline=headline.strip()[:500],
                    location=location or "Unknown",
                    link=link,
                    source="LinkedIn",
                )
                db.session.add(profile)
                db.session.flush()
                count += 1
                print(f"  ✓ [{count}] {name} — {headline[:60]}")

        db.session.commit()
        print(f"[ProfileScraper] Done — saved {count} profiles.")
        return count