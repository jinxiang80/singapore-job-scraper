Singapore Job Scraper
A Python-based web application that scrapes job listings from multiple Singapore job portals and filters them based on keywords. This platform helps job seekers efficiently find relevant positions without having to search across multiple websites.

Features
Multi-source Scraping: Collects jobs from multiple Singapore job portals
Careers@Gov.sg (Singapore Government Jobs)
MyCareersFuture.sg
JobsDB Singapore
Keyword-based Filtering: Only returns jobs matching your skills and interests
User-friendly Web Interface: Easy-to-use search form and results display
Multiple Export Formats: Download results as CSV, Excel, or JSON
Background Processing: Handles scraping in the background so the UI remains responsive
Getting Started
Prerequisites
Python 3.8 or higher
Chrome browser (for Selenium WebDriver)
Installation
Clone this repository
git clone https://github.com/yourusername/singapore-job-scraper.git
cd singapore-job-scraper
Install required packages
pip install -r requirements.txt
Create necessary directories
mkdir -p job_results templates
Create the required files
Copy singapore_job_scraper.py to the project directory
Copy job_app.py to the project directory
Create a templates directory and copy index.html into it
Run the application
python job_app.py
Open your browser and navigate to http://localhost:5000
Usage
Enter keywords that match your skills (e.g., "python", "data science", "marketing")
Optionally enter a general job title search term (e.g., "developer", "analyst")
Click "Find Matching Jobs"
View results categorized by source
Export results in your preferred format
Requirements
The application requires the following Python packages:

flask
requests
beautifulsoup4
pandas
selenium
webdriver_manager
You can install all requirements with:

pip install flask requests beautifulsoup4 pandas selenium webdriver_manager
Customization
Adding New Job Sources
To add a new job source, extend the SingaporeJobScraper class in singapore_job_scraper.py with a new method following the pattern of the existing scrapers. Then, update the run method to include your new scraper.

Modifying Keyword Matching
The keyword matching logic is in the _matches_keywords method of the SingaporeJobScraper class. You can modify this to implement more sophisticated matching algorithms.

Changing the UI
The UI is built with Bootstrap 5 and can be customized by editing the index.html template.

Privacy and Legal Considerations
When scraping websites, always:

Respect the website's robots.txt file
Include delays between requests to avoid overwhelming servers
Review the Terms of Service of the websites you're scraping
Use the data responsibly and for personal use only
Limitations
Job descriptions may not be fully scraped due to dynamic content loading
Some job sites may implement anti-scraping measures
The scraper may need updates if websites change their structure
License
This project is licensed under the MIT License - see the LICENSE file for details.

Support
For questions, suggestions, or issues, please open an issue in the GitHub repository.

