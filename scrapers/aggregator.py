"""
Aggregator Module: coordinates multi-platform scraping, merging, and exports.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import io
import json
from scrapers.unstop import UnstopScraper
from scrapers.devpost import DevpostScraper
from scrapers.curated import CuratedFeedScraper
import database

class OpportunityAggregator:
    def __init__(self):
        self.unstop = UnstopScraper()
        self.devpost = DevpostScraper()
        self.curated = CuratedFeedScraper()

    def scrape_all(self, category="all", query=None, limit=20):
        """
        Executes scrapers concurrently and persists fresh opportunities into DB.
        """
        results = []
        futures = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            # Unstop scraper task
            futures.append(executor.submit(self.unstop.scrape, category=category, query=query, limit=limit))
            
            # Devpost scraper task (Devpost mainly hosts hackathons & AI/product challenges)
            if category in ["all", "hackathons", "tech", "product"]:
                futures.append(executor.submit(self.devpost.scrape, query=query, limit=limit))

            # Curated Feed scraper task
            futures.append(executor.submit(self.curated.scrape, category=category, query=query, limit=limit))

            for future in as_completed(futures):
                try:
                    data = future.result()
                    if data:
                        results.extend(data)
                except Exception as e:
                    print(f"[Aggregator] Scraper execution error: {e}")

        # Save to database
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
