import re
import os
import urllib.parse
import requests
from scrapers.base_scraper import BaseScraper
from models import db, JobListing, ScrapeTask


class JobScraper(BaseScraper):
    def __init__(self, task_id):
        super().__init__(base_url="")
        self.task_id = task_id

    # ------------------------------------------------------------------
    # Searlo search (same pattern as ProfileScraper)
    # ------------------------------------------------------------------

    def _searlo_search(self, query: str) -> list[dict]:
        api_key = os.getenv("SEARLO_API_KEY")
        if not api_key:
            print("[JobScraper] Missing SEARLO_API_KEY in .env")
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
                res = requests.get(
                    f"{url}?q={urllib.parse.quote(query)}",
                    headers=headers,
                    timeout=15,
                )
                if res.status_code == 200:
                    return self._extract_items(res.json())

                res = requests.post(
                    url,
                    headers=headers,
                    json={"query": query},
                    timeout=15,
                )
                if res.status_code == 200:
                    return self._extract_items(res.json())

            except Exception as e:
                print(f"[JobScraper] Searlo request error: {e}")
                continue

        print("[JobScraper] All Searlo header variants failed.")
        return []

    @staticmethod
    def _extract_items(data) -> list[dict]:
        if isinstance(data, list):
            return data
        for key in ("results", "organic", "items", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return []

    # ------------------------------------------------------------------
    # Title parser — extracts job title + company
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_job_title(raw_title: str) -> tuple[str, str]:
        """
        Returns (job_title, company).
        LinkedIn job titles look like:
          "Software Engineer at Google - LinkedIn"
          "Google is hiring Data Scientist | LinkedIn"
          "Backend Developer - Acme Corp - LinkedIn"
        """
        title = re.sub(r"[\|\-·]\s*LinkedIn\s*$", "", raw_title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s*LinkedIn\s*$", "", title, flags=re.IGNORECASE).strip()

        company = "Unknown Company"

        # "X is hiring Y" pattern
        hiring_match = re.search(r"^(.+?)\s+is hiring\s+(.+)$", title, re.IGNORECASE)
        if hiring_match:
            return hiring_match.group(2).strip(), hiring_match.group(1).strip()

        # "Job Title at Company" pattern
        if " at " in title:
            parts = title.split(" at ", 1)
            return parts[0].strip(), parts[1].strip()

        # Fallback: split on " - " or " | "
        for sep in (" - ", " | "):
            if sep in title:
                parts = title.split(sep, 1)
                return parts[0].strip(), parts[1].strip()

        return title.strip(), company

    # ------------------------------------------------------------------
    # Main scrape
    # ------------------------------------------------------------------

    def scrape(self, keyword: str) -> int:
        task = ScrapeTask.query.get(self.task_id)
        if not task:
            print(f"[JobScraper] Task {self.task_id} not found.")
            return 0

        # Build search query
        search_query = f'site:linkedin.com/jobs/view/ {keyword}'
        if task.company:
            search_query += f' "{task.company}"'
        if task.location:
            search_query += f' "{task.location}"'
        if task.salary:
            search_query += f' "{task.salary}"'

        print(f"[JobScraper] Querying: {search_query}")
        items = self._searlo_search(search_query)
        print(f"[JobScraper] Searlo returned {len(items)} items")

        count = 0
        TARGET = 10

        for item in items:
            if count >= TARGET:
                break

            link      = item.get("link") or item.get("url") or ""
            raw_title = item.get("title") or ""
            snippet   = item.get("snippet") or item.get("description") or ""

            if "linkedin.com/jobs/view/" not in link:
                continue

            link = link.split("?")[0].rstrip("/")

            job_title, company = self._parse_job_title(raw_title)

            if not job_title:
                continue

            # Override company from task if explicitly set
            if task.company:
                company = task.company

            location = task.location or "Unknown Location"

            job = JobListing(
                task_id=self.task_id,
                title=job_title[:255],
                company=company[:255],
                location=location,
                price_or_salary=task.salary if task.salary else "Not Disclosed",
                link=link,
                date_posted="Recent",
                source="LinkedIn",
            )
            db.session.add(job)
            count += 1
            print(f"  ✓ [{count}] {job_title} @ {company}")

        db.session.commit()
        print(f"[JobScraper] Done — saved {count} jobs.")
        return count