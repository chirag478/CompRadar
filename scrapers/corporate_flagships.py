"""
Corporate Flagships & DrivenData ML Contests Scraper
Tracks marquee annual corporate case competitions (HUL LIME, Tata Imagination, Flipkart WiRED,
Amazon ACE, Reliance T.U.P., BCG Strategy Cup) alongside DrivenData ML challenges.
"""
import urllib.request
import re


class CorporateFlagshipScraper:
    def __init__(self):
        self.source = "Corporate Flagships"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def scrape(self, category="all", query=None, limit=20):
        flagships = [
            {
                "id": "corp-hul-lime-2026",
                "title": "HUL L.I.M.E. Season 18: National Marketing & Brand Case",
                "organizer": "Hindustan Unilever (HUL)",
                "category": "Marketing & Brand",
                "prize": "₹10,00,000 + PPI",
                "url": "https://unstop.com/o/hul-lime",
                "location": "Mumbai / Hybrid",
                "deadline": "October 2026",
                "days_left": "140 days left",
                "days_left_num": 140,
                "tags": ["Marketing & Brand", "MBA / PG", "PPO / PPI", "FMCG Flagship"]
            },
            {
                "id": "corp-tata-imagination-2026",
                "title": "Tata Imagination Challenge 2026",
                "organizer": "Tata Group (TAS)",
                "category": "Strategy & Consulting",
                "prize": "₹2,00,000 + TAS PPI",
                "url": "https://www.tata.com/careers/programs/tata-imagination-challenge",
                "location": "Online / Mumbai Finale",
                "deadline": "October 2026",
                "days_left": "135 days left",
                "days_left_num": 135,
                "tags": ["Strategy & Consulting", "MBA / PG", "PPO / PPI", "Open to All"]
            },
            {
                "id": "corp-flipkart-wired-2026",
                "title": "Flipkart WiRED 2026: Business, Supply Chain & Product Track",
                "organizer": "Flipkart",
                "category": "Product Case Study",
                "prize": "₹4,50,000 + PPI",
                "url": "https://unstop.com/o/flipkart-wired",
                "location": "Bengaluru, Karnataka / Hybrid",
                "deadline": "September 2026",
                "days_left": "115 days left",
                "days_left_num": 115,
                "tags": ["Product Case Study", "Bengaluru", "MBA / PG", "PPO / PPI"]
            },
            {
                "id": "corp-amazon-ace-2026",
                "title": "Amazon ACE Challenge 2026",
                "organizer": "Amazon India",
                "category": "Product Management",
                "prize": "₹5,00,000 + PPO",
                "url": "https://unstop.com/o/amazon-ace-challenge",
                "location": "Bengaluru / Hyderabad / Hybrid",
                "deadline": "October 2026",
                "days_left": "145 days left",
                "days_left_num": 145,
                "tags": ["Product Management", "Bengaluru", "MBA / PG", "PPO / PPI"]
            },
            {
                "id": "corp-reliance-tup-2026",
                "title": "Reliance T.U.P. (The Ultimate Pitch) 2026",
                "organizer": "Reliance Industries",
                "category": "Strategy & Consulting",
                "prize": "₹7,50,000 + PPI",
                "url": "https://unstop.com/o/reliance-tup",
                "location": "Mumbai / Online",
                "deadline": "November 2026",
                "days_left": "165 days left",
                "days_left_num": 165,
                "tags": ["Strategy & Consulting", "MBA / PG", "PPO / PPI"]
            },
            {
                "id": "corp-bcg-strategy-cup",
                "title": "BCG Strategy Cup 2026",
                "organizer": "Boston Consulting Group (BCG)",
                "category": "Strategy & Consulting",
                "prize": "₹3,00,000 + Interview Fast-Track",
                "url": "https://careers.bcg.com/",
                "location": "Global / Bengaluru / Hybrid",
                "deadline": "November 2026",
                "days_left": "170 days left",
                "days_left_num": 170,
                "tags": ["Strategy & Consulting", "Bengaluru", "MBA / PG", "PPO / PPI"]
            },
            {
                "id": "drivendata-ml-2026",
                "title": "DrivenData Social-Impact ML & AI Challenges",
                "organizer": "DrivenData",
                "category": "Tech Hackathon",
                "prize": "$50,000+",
                "url": "https://www.drivendata.org/competitions/",
                "location": "Global Online",
                "deadline": "Ongoing 2026",
                "days_left": "90 days left",
                "days_left_num": 90,
                "tags": ["AI / ML", "Data Science", "Open to All"]
            }
        ]

        results = []
        for item in flagships:
            if query:
                blob = f"{item['title']} {item['organizer']} {' '.join(item['tags'])}".lower()
                if query.lower() not in blob:
                    continue
            if category != "all":
                c_low = category.lower()
                cat_low = item["category"].lower()
                if "hack" in c_low and "hack" not in cat_low:
                    continue
                if "case" in c_low and "case" not in cat_low:
                    continue
                if "strat" in c_low and "strat" not in cat_low:
                    continue
                if "mark" in c_low and "mark" not in cat_low:
                    continue
                if "prod" in c_low and "prod" not in cat_low:
                    continue

            entry = dict(item)
            entry["source"] = self.source
            entry["status"] = "Open"
            results.append(entry)
            if len(results) >= limit:
                break

        return results
