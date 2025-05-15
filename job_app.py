import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
from datetime import datetime
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("job_scraper.log"),
        logging.StreamHandler()
    ]
)

class SingaporeJobScraper:
    def __init__(self, keywords, output_dir='job_results'):
        """
        Initialize the job scraper with keywords to filter jobs.
        
        Args:
            keywords (list): List of keywords to filter jobs
            output_dir (str): Directory to save results
        """
        self.keywords = [keyword.lower() for keyword in keywords]
        self.output_dir = output_dir
        self.results = []
        self.setup_directories()
        
        # Setup for Selenium (for JavaScript-heavy sites)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
    def setup_directories(self):
        """Create necessary directories for output files."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    def scrape_careers_gov_sg(self, num_pages=5):
        """
        Scrape jobs from Careers@Gov.
        
        Args:
            num_pages (int): Number of pages to scrape
        """
        logging.info("Starting to scrape Careers@Gov.sg")
        base_url = "https://careers.pageuppeople.com/688/cwlive/en/listing/"
        
        for page in range(1, num_pages + 1):
            try:
                logging.info(f"Scraping page {page} of Careers@Gov.sg")
                url = f"{base_url}?page={page}"
                self.driver.get(url)
                
                # Wait for the job listings to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "recruitment-template"))
                )
                
                # Extract job listings
                job_elements = self.driver.find_elements(By.CLASS_NAME, "recruitment-template")
                
                for job in job_elements:
                    try:
                        title_element = job.find_element(By.CLASS_NAME, "job-title")
                        title = title_element.text.strip()
                        link = title_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                        
                        # Extract other job details
                        organization = job.find_element(By.CLASS_NAME, "job-client-name").text.strip()
                        location = job.find_element(By.CLASS_NAME, "job-location").text.strip()
                        closing_date_text = job.find_element(By.CLASS_NAME, "job-close-date").text.strip()
                        closing_date = closing_date_text.replace("Closing Date: ", "")
                        
                        job_data = {
                            'title': title,
                            'organization': organization,
                            'location': location,
                            'closing_date': closing_date,
                            'url': link,
                            'source': 'Careers@Gov.sg'
                        }
                        
                        # Check if job matches keywords
                        if self._matches_keywords(job_data):
                            self.results.append(job_data)
                            logging.info(f"Found matching job: {title} at {organization}")
                            
                    except Exception as e:
                        logging.error(f"Error extracting job details: {e}")
                
                # Sleep to avoid overwhelming the server
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error scraping page {page} of Careers@Gov.sg: {e}")
                
        logging.info(f"Completed scraping Careers@Gov.sg. Found {len(self.results)} matching jobs.")
    
    def scrape_mycareersfuture(self, search_term="", num_pages=5):
        """
        Scrape jobs from MyCareersFuture.sg using their API.
        
        Args:
            search_term (str): Search term for jobs
            num_pages (int): Number of pages to scrape
        """
        logging.info(f"Starting to scrape MyCareersFuture.sg for '{search_term}'")
        
        # MyCareersFuture uses an API for search results
        base_api_url = "https://api.mycareersfuture.gov.sg/v2/search"
        
        for page in range(num_pages):
            try:
                logging.info(f"Scraping page {page+1} of MyCareersFuture.sg")
                
                params = {
                    "limit": 20,
                    "page": page,
                    "search": search_term,
                    "sortBy": "new_posting_date"
                }
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                response = requests.get(base_api_url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get('results', [])
                    
                    for job in jobs:
                        try:
                            job_data = {
                                'title': job.get('title', ''),
                                'organization': job.get('postedCompany', {}).get('name', ''),
                                'location': ', '.join(job.get('addressLocations', [])),
                                'salary_min': job.get('salary', {}).get('min', ''),
                                'salary_max': job.get('salary', {}).get('max', ''),
                                'posting_date': job.get('postedDate', ''),
                                'url': f"https://www.mycareersfuture.gov.sg/job/{job.get('uuid', '')}",
                                'source': 'MyCareersFuture.sg'
                            }
                            
                            # Check if job matches keywords
                            if self._matches_keywords(job_data):
                                self.results.append(job_data)
                                logging.info(f"Found matching job: {job_data['title']} at {job_data['organization']}")
                                
                        except Exception as e:
                            logging.error(f"Error extracting job details: {e}")
                    
                    # If no more jobs, break the loop
                    if len(jobs) < 20:
                        break
                        
                else:
                    logging.error(f"Error with MyCareersFuture API: {response.status_code}")
                    break
                    
                # Sleep to avoid overwhelming the server
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error scraping page {page+1} of MyCareersFuture.sg: {e}")
                
        logging.info(f"Completed scraping MyCareersFuture.sg. Found {len(self.results)} matching jobs.")
    
    def scrape_jobsdb(self, search_term="", num_pages=5):
        """
        Scrape jobs from JobsDB Singapore.
        
        Args:
            search_term (str): Search term for jobs
            num_pages (int): Number of pages to scrape
        """
        logging.info(f"Starting to scrape JobsDB for '{search_term}'")
        
        for page in range(1, num_pages + 1):
            try:
                logging.info(f"Scraping page {page} of JobsDB")
                
                # Construct URL with search term
                url = f"https://sg.jobsdb.com/jobs-in-singapore/{page}"
                if search_term:
                    url = f"https://sg.jobsdb.com/jobs-in-singapore/{search_term}/{page}"
                
                # Use Selenium for JavaScript rendering
                self.driver.get(url)
                
                # Wait for job cards to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "job-card"))
                )
                
                # Extract job listings
                job_elements = self.driver.find_elements(By.CLASS_NAME, "job-card")
                
                for job in job_elements:
                    try:
                        title = job.find_element(By.CSS_SELECTOR, "h3.job-title").text.strip()
                        company = job.find_element(By.CSS_SELECTOR, "span.company-name").text.strip()
                        
                        # Extract location if available
                        try:
                            location = job.find_element(By.CSS_SELECTOR, "span.location").text.strip()
                        except:
                            location = "Singapore"
                            
                        # Get the job URL
                        link = job.find_element(By.CSS_SELECTOR, "a.job-link").get_attribute("href")
                        
                        job_data = {
                            'title': title,
                            'organization': company,
                            'location': location,
                            'url': link,
                            'source': 'JobsDB'
                        }
                        
                        # Check if job matches keywords
                        if self._matches_keywords(job_data):
                            self.results.append(job_data)
                            logging.info(f"Found matching job: {title} at {company}")
                            
                    except Exception as e:
                        logging.error(f"Error extracting JobsDB job details: {e}")
                
                # Sleep to avoid overwhelming the server
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error scraping page {page} of JobsDB: {e}")
                
        logging.info(f"Completed scraping JobsDB. Found {len(self.results)} matching jobs.")
    
    def _matches_keywords(self, job_data):
        """
        Check if a job matches any of the keywords.
        
        Args:
            job_data (dict): Job information dictionary
            
        Returns:
            bool: True if job matches keywords, False otherwise
        """
        # Convert relevant job data to lowercase for case-insensitive matching
        job_text = ' '.join([
            str(job_data.get('title', '')).lower(),
            str(job_data.get('organization', '')).lower(),
            str(job_data.get('description', '')).lower()
        ])
        
        # Check if any keyword is in the job text
        return any(keyword in job_text for keyword in self.keywords)
    
    def export_results(self, format='csv'):
        """
        Export results to a file.
        
        Args:
            format (str): Export format ('csv', 'json', or 'excel')
        """
        if not self.results:
            logging.warning("No results to export")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == 'csv':
            filename = f"{self.output_dir}/jobs_{timestamp}.csv"
            pd.DataFrame(self.results).to_csv(filename, index=False)
            
        elif format.lower() == 'json':
            filename = f"{self.output_dir}/jobs_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=4)
                
        elif format.lower() == 'excel':
            filename = f"{self.output_dir}/jobs_{timestamp}.xlsx"
            pd.DataFrame(self.results).to_excel(filename, index=False)
            
        logging.info(f"Exported {len(self.results)} jobs to {filename}")
        return filename
    
    def run(self, search_term="", export_format='csv'):
        """
        Run the complete scraping process.
        
        Args:
            search_term (str): Search term for job sites that require it
            export_format (str): Export format ('csv', 'json', or 'excel')
        """
        try:
            # Run scrapers for each site
            self.scrape_careers_gov_sg()
            self.scrape_mycareersfuture(search_term)
            self.scrape_jobsdb(search_term)
            
            # Export results
            output_file = self.export_results(format=export_format)
            
            logging.info(f"Scraping complete. Found {len(self.results)} matching jobs.")
            return output_file
            
        finally:
            # Clean up Selenium resources
            self.driver.quit()

# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Singapore job sites for matching jobs")
    parser.add_argument("--keywords", nargs="+", required=True, help="Keywords to filter jobs")
    parser.add_argument("--search", default="", help="Search term for sites that require it")
    parser.add_argument("--format", choices=['csv', 'json', 'excel'], default='csv', help="Export format")
    parser.add_argument("--output", default="job_results", help="Output directory")
    
    args = parser.parse_args()
    
    scraper = SingaporeJobScraper(args.keywords, output_dir=args.output)
    output_file = scraper.run(args.search, args.format)
    
    print(f"\nScraping complete! Results saved to: {output_file}")