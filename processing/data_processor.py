import pandas as pd
from models import db, JobListing, ScrapeTask

class DataProcessor:
    @staticmethod
    def get_job_data(user_id=None):
        """Fetch all job listings into a Pandas DataFrame."""
        if user_id:
            jobs = JobListing.query.join(ScrapeTask).filter(ScrapeTask.user_id == user_id).all()
        else:
            jobs = JobListing.query.all()
            
        data = [{
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "date_posted": job.date_posted,
            "source": job.source
        } for job in jobs]
        
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)

    @staticmethod
    def get_location_counts(df):
        """Aggregate data to get count of jobs per location."""
        if df.empty:
            return pd.DataFrame()
        return df['location'].value_counts().reset_index().rename(columns={'count': 'job_count', 'location': 'Location'})

    @staticmethod
    def get_company_counts(df):
        """Aggregate data to get count of jobs per company (top 10)."""
        if df.empty:
            return pd.DataFrame()
        return df['company'].value_counts().head(10).reset_index().rename(columns={'count': 'job_count', 'company': 'Company'})
