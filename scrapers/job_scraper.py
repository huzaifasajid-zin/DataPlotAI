import urllib.parse
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from models import db, JobListing, ScrapeTask

class JobScraper(BaseScraper):
    def __init__(self, task_id):
        # We will dynamically set the base URL during the scrape method based on the keyword
        super().__init__(base_url="")
        self.task_id = task_id

    def scrape(self, keyword):
        """
        Scrapes real live job listings related to the keyword from LinkedIn's public jobs portal.
        This provides actual live data instead of mock job postings.
        """
        # We will fetch the actual model to use the advanced filters
        task = ScrapeTask.query.get(self.task_id)
        if not task:
            print(f"[Scraper] Task {self.task_id} not found.")
            return 0
            
        search_query = keyword
        if task.company:
            search_query += f" {task.company}"
        if task.salary:
            search_query += f" {task.salary}"
            
        # URL encode the keyword for the search query
        encoded_keyword = urllib.parse.quote(search_query)
        
        # Target the public LinkedIn jobs search endpoint 
        target_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_keyword}&refresh=true"
        
        if task.location:
            target_url += f"&location={urllib.parse.quote(task.location)}"
            
        if task.time_period:
            # f_TPR parameter values: r86400 (24h), r604800 (week), r2592000 (month)
            target_url += f"&f_TPR={task.time_period}"
            
        self.base_url = target_url
        
        # BaseScraper fetches with a generic User-Agent to avoid initial basic blocks
        html = self.fetch_page(target_url)
        soup = self.parse_html(html)
        
        if not soup:
            print(f"[Scraper] Failed to parse HTML for keyword: {keyword}")
            return 0

        # LinkedIn uses specific classes for their public unauthenticated job cards
        job_elements = soup.find_all("div", class_="base-card")
        count = 0

        for job_element in job_elements:
            try:
                title_element = job_element.find("h3", class_="base-search-card__title")
                company_element = job_element.find("h4", class_="base-search-card__subtitle")
                location_element = job_element.find("span", class_="job-search-card__location")
                date_element = job_element.find("time", class_="job-search-card__listdate")
                
                # The link is usually attached to an anchor tag wrapping the card or title
                link_element = job_element.find("a", class_="base-card__full-link")
                
                title = title_element.text.strip() if title_element else "Unknown Title"
                company = company_element.text.strip() if company_element else "Unknown Company"
                location = location_element.text.strip() if location_element else "Unknown Location"
                
                # Extract date, if recently posted it might use 'job-search-card__listdate--new'
                if not date_element:
                    date_element = job_element.find("time", class_="job-search-card__listdate--new")
                
                date_posted = date_element['datetime'] if date_element and date_element.has_attr('datetime') else (date_element.text.strip() if date_element else "Recent")
                
                link = link_element["href"] if link_element and link_element.has_attr("href") else ""
                
                # Exclude completely broken extractions
                if title == "Unknown Title" and company == "Unknown Company":
                    continue

                # Save the real data to the database
                job = JobListing(
                    task_id=self.task_id,
                    title=title,
                    company=company,
                    location=location,
                    price_or_salary="Not Disclosed", # LinkedIn usually hides salary on the search page
                    link=link,
                    date_posted=date_posted,
                    source="LinkedIn Public"
                )
                db.session.add(job)
                count += 1
                
                # Throttle to max 25 jobs per run to avoid flooding the DB / looking suspicious
                if count >= 25:
                    break
                    
            except Exception as e:
                print(f"[Scraper] Error parsing a job card: {e}")
                continue
            
        db.session.commit()
        return count
