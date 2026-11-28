"""
Aggregator Module: coordinates multi-platform scraping, merging, and exports.
Includes Unstop, Devpost, Kaggle, B-School Fests, and Curated Feeds.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import io
import json
from scrapers.unstop import UnstopScraper
from scrapers.devpost import DevpostScraper
from scrapers.devfolio import DevfolioScraper
from scrapers.hackerearth import HackerEarthScraper
from scrapers.superteam import SuperteamScraper
from scrapers.kaggle import KaggleScraper
from scrapers.bschool_fests import BSchoolFestScraper
from scrapers.corporate_flagships import CorporateFlagshipScraper
from scrapers.curated import CuratedFeedScraper
import database

class OpportunityAggregator:
    def __init__(self):
        self.unstop = UnstopScraper()
        self.devpost = DevpostScraper()
        self.devfolio = DevfolioScraper()
        self.hackerearth = HackerEarthScraper()
        self.superteam = SuperteamScraper()
        self.kaggle = KaggleScraper()
        self.bschool_fests = BSchoolFestScraper()
        self.corporate = CorporateFlagshipScraper()
        self.curated = CuratedFeedScraper()

    def scrape_all(self, category="all", query=None, limit=25):
        """
        Executes all platform scrapers concurrently and persists fresh opportunities into DB.
        """
        results = []
        futures = []

        with ThreadPoolExecutor(max_workers=9) as executor:
            # 1. Unstop Scraper (All domains)
            futures.append(executor.submit(self.unstop.scrape, category=category, query=query, limit=limit))
            
            # 2. Devpost Scraper (Tech, Hackathons, Product)
            if category in ["all", "hackathons", "tech", "product"]:
                futures.append(executor.submit(self.devpost.scrape, query=query, limit=limit))

            # 3. Devfolio Scraper (Indian & Bengaluru Hackathons)
            if category in ["all", "hackathons", "tech", "product"]:
                futures.append(executor.submit(self.devfolio.scrape, query=query, limit=limit))

            # 4. HackerEarth Scraper (Hackathons & Hiring Challenges)
            if category in ["all", "hackathons", "tech", "hiring"]:
                futures.append(executor.submit(self.hackerearth.scrape, category=category, query=query, limit=limit))

            # 5. Superteam Earn Scraper (Product, Growth, Design & Dev Bounties)
            if category in ["all", "hackathons", "product", "marketing", "tech"]:
                futures.append(executor.submit(self.superteam.scrape, category=category, query=query, limit=limit))

            # 6. Kaggle Scraper (Tech, AI/ML, Data Science, Hackathons)
            if category in ["all", "hackathons", "tech", "ml", "ai"]:
                futures.append(executor.submit(self.kaggle.scrape, category=category, query=query, limit=limit))

            # 7. Premier B-School Fests Scraper (Case Studies, Strategy, Marketing)
            if category in ["all", "case_studies", "case_study", "strategy", "marketing", "product", "business"]:
                futures.append(executor.submit(self.bschool_fests.scrape, category=category, query=query, limit=limit))

            # 8. Corporate Flagships & DrivenData ML
            futures.append(executor.submit(self.corporate.scrape, category=category, query=query, limit=limit))

            # 9. Curated Feed Scraper
            futures.append(executor.submit(self.curated.scrape, category=category, query=query, limit=limit))

            for future in as_completed(futures):
                try:
                    data = future.result()
                    if data:
                        results.extend(data)
                except Exception as e:
                    print(f"[Aggregator] Scraper execution error: {e}")

        # Save to database (deduplicates automatically)
        saved_count = database.save_opportunities(results)
        return {
            "scraped_count": len(results),
            "saved_count": saved_count,
            "opportunities": results
        }

    def import_custom_csv(self, csv_text):
        """
        Ingests custom CSV text, parses opportunities and stores into database.
        """
        items = self.curated.parse_csv_content(csv_text)
        saved = database.save_opportunities(items)
        return {
            "parsed_count": len(items),
            "saved_count": saved,
            "items": items
        }

    @staticmethod
    def export_csv(opportunities):
        output = io.StringIO()
        fieldnames = [
            "id", "source", "title", "category", "organizer",
            "deadline", "days_left", "prize", "location", "url", "tags", "status"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for opp in opportunities:
            row = dict(opp)
            if isinstance(row.get('tags'), list):
                row['tags'] = ", ".join(row['tags'])
            writer.writerow(row)
        return output.getvalue()

    @staticmethod
    def export_json(opportunities):
        return json.dumps(opportunities, indent=2)
