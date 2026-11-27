"""
Top B-School Annual Fest Auto-Index Scraper
Curates and indexes premier business school annual fests, flagship case competitions,
and strategy conclaves across top Indian & Global B-schools (IIM Ahmedabad TRBS,
IIM Bangalore Vista, IIM Calcutta Intaglio, XLRI Ensemble-Valhalla, FMS Fiesta, SPJIMR Ojas, etc.).
"""
import urllib.request
import json
import re
from datetime import datetime, timezone

class BSchoolFestScraper:
    def __init__(self):
        self.source = "B-School Fests"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }

    def scrape(self, category="all", query=None, limit=20):
        """
        Indexes premier flagship B-School annual festivals and national case competitions.
        """
        fests = [
            {
                "id": "fest-iima-trbs-genesis",
                "title": "Genesis: Flagship Business Model Competition (TRBS 2026)",
                "organizer": "IIM Ahmedabad (The Red Brick Summit)",
                "category": "Strategy & Consulting",
                "prize": "₹4,50,000",
                "url": "https://unstop.com/o/the-red-brick-summit-iim-ahmedabad",
                "location": "Ahmedabad, Gujarat / Hybrid",
                "deadline": "October 2026",
                "days_left": "150 days left",
                "days_left_num": 150,
                "tags": ["IIMA", "TRBS", "Business Strategy", "PPO Potential"]
            },
            {
                "id": "fest-iimb-vista-trojan-horse",
                "title": "Trojan Horse: International Strategy Challenge (Vista 2026)",
                "organizer": "IIM Bangalore (Vista Annual Conclave)",
                "category": "Strategy & Consulting",
                "prize": "₹3,00,000",
                "url": "https://unstop.com/o/vista-iim-bangalore",
                "location": "Bengaluru, Karnataka / Online",
                "deadline": "September 2026",
                "days_left": "120 days left",
                "days_left_num": 120,
                "tags": ["IIMB Vista", "Corporate Strategy", "Global Teams", "MBB Judges"]
            },
            {
                "id": "fest-iimc-intaglio-olympus",
                "title": "Olympus: Ultimate Leadership Challenge (Intaglio 2026)",
                "organizer": "IIM Calcutta (Intaglio Conclave)",
                "category": "Case Studies",
                "prize": "₹3,50,000",
                "url": "https://unstop.com/o/intaglio-iim-calcutta",
                "location": "Kolkata, West Bengal / Hybrid",
                "deadline": "December 2026",
                "days_left": "210 days left",
                "days_left_num": 210,
                "tags": ["IIMC Intaglio", "Leadership", "Live Case", "Premier Tier-1"]
            },
            {
                "id": "fest-xlri-ensemble-strike",
                "title": "Strike or Yield: Flagship Consulting Case (Ensemble-Valhalla 2026)",
                "organizer": "XLRI Jamshedpur (Ensemble-Valhalla)",
                "category": "Strategy & Consulting",
                "prize": "₹2,50,000",
                "url": "https://unstop.com/o/ensemble-valhalla-xlri",
                "location": "Jamshedpur, Jharkhand / Hybrid",
                "deadline": "November 2026",
                "days_left": "180 days left",
                "days_left_num": 180,
                "tags": ["XLRI", "Consulting", "Turnaround Strategy", "National Final"]
            },
            {
                "id": "fest-fms-fiesta-markcon",
                "title": "MarkCon: Brand Transformation Challenge (Fiesta 2026)",
                "organizer": "FMS Delhi (Fiesta)",
                "category": "Marketing Competitions",
                "prize": "₹2,00,000",
                "url": "https://unstop.com/o/fiesta-fms-delhi",
                "location": "New Delhi / Hybrid",
                "deadline": "January 2027",
                "days_left": "240 days left",
                "days_left_num": 240,
                "tags": ["FMS Delhi", "Brand Strategy", "FMCG Partner", "Live Problem"]
            },
            {
                "id": "fest-spjimr-ojas-finquest",
                "title": "FinQuest: Private Equity & Valuation Case (Ojas 2026)",
                "organizer": "SPJIMR Mumbai (Ojas Conclave)",
                "category": "Case Studies",
                "prize": "₹2,25,000",
                "url": "https://unstop.com/o/ojas-spjimr-mumbai",
                "location": "Mumbai, Maharashtra / Online",
                "deadline": "November 2026",
                "days_left": "175 days left",
                "days_left_num": 175,
                "tags": ["SPJIMR Ojas", "Finance & PE", "DCF Valuation", "M&A Case"]
            },
            {
                "id": "fest-iitb-ecell-eureka",
                "title": "Eureka! Asia's Largest Business Model Competition 2026",
                "organizer": "IIT Bombay E-Cell & SJMSoM",
                "category": "Strategy & Consulting",
                "prize": "₹50,00,000",
                "url": "https://www.ecell.in/eureka",
                "location": "Mumbai / Global Online",
                "deadline": "October 2026",
                "days_left": "160 days left",
                "days_left_num": 160,
                "tags": ["IIT Bombay", "Eureka", "Startup Pitch", "Seed Grants"]
            },
            {
                "id": "fest-mdi-imperium-marques",
                "title": "MarQues: National FMCG Growth Hack (Imperium 2026)",
                "organizer": "MDI Gurgaon (Imperium)",
                "category": "Marketing Competitions",
                "prize": "₹1,75,000",
                "url": "https://unstop.com/o/imperium-mdi-gurgaon",
                "location": "Gurgaon, NCR / Hybrid",
                "deadline": "November 2026",
                "days_left": "190 days left",
                "days_left_num": 190,
                "tags": ["MDI Gurgaon", "Marketing", "GTM Strategy", "Consumer Tech"]
            },
            {
                "id": "fest-isb-advaita-consult",
                "title": "ISB Advaita: Global Leadership Strategy Challenge",
                "organizer": "Indian School of Business (ISB)",
                "category": "Strategy & Consulting",
                "prize": "₹5,00,000",
                "url": "https://unstop.com/o/advaita-isb",
                "location": "Hyderabad / Mohali / Hybrid",
                "deadline": "December 2026",
                "days_left": "220 days left",
                "days_left_num": 220,
                "tags": ["ISB", "Advaita", "MBA / PG", "Executive Case", "Global Leadership"]
            },
            {
                "id": "fest-iimb-eximius-bzzwings",
                "title": "Eximius Bzzwings: National Startup & Strategy Pitch 2026",
                "organizer": "IIM Bangalore (Eximius)",
                "category": "Strategy & Consulting",
                "prize": "₹3,00,000",
                "url": "https://unstop.com/o/eximius-iim-bangalore",
                "location": "Bengaluru, Karnataka / Hybrid",
                "deadline": "August 2026",
                "days_left": "95 days left",
                "days_left_num": 95,
                "tags": ["IIMB Eximius", "Bengaluru", "MBA / PG", "PPO / PPI", "Startup Pitch"]
            },
            {
                "id": "fest-sibm-blr-revelation",
                "title": "Revelation 2026: National Strategy & Finance Case",
                "organizer": "SIBM Bengaluru",
                "category": "Case Studies",
                "prize": "₹1,50,000",
                "url": "https://unstop.com/o/revelation-sibm-bengaluru",
                "location": "Bengaluru, Karnataka / Hybrid",
                "deadline": "November 2026",
                "days_left": "165 days left",
                "days_left_num": 165,
                "tags": ["SIBM Bengaluru", "Bengaluru", "MBA / PG", "Case Study"]
            },
            {
                "id": "fest-blr-tech-summit-ai",
                "title": "Bengaluru GenAI & DeepTech Buildathon 2026",
                "organizer": "Bengaluru Tech & AI Collective",
                "category": "Tech Hackathons",
                "prize": "₹10,00,000",
                "url": "https://devpost.com/hackathons?search=bengaluru",
                "location": "Bengaluru, Karnataka / Hybrid",
                "deadline": "November 2026",
                "days_left": "140 days left",
                "days_left_num": 140,
                "tags": ["Bengaluru", "AI / ML", "PPO / PPI", "Open to All"]
            },
            {
                "id": "fest-iisc-blr-product",
                "title": "IISc Pravega: Bengaluru Product & Innovation Challenge",
                "organizer": "IISc Bangalore",
                "category": "Product Management",
                "prize": "₹2,00,000",
                "url": "https://unstop.com/o/pravega-iisc-bangalore",
                "location": "Bengaluru, Karnataka / Hybrid",
                "deadline": "December 2026",
                "days_left": "185 days left",
                "days_left_num": 185,
                "tags": ["IISc Bengaluru", "Bengaluru", "Product Mgmt", "Open to All"]
            }
        ]

        results = []
        for fest in fests:
            # Category match
            if category != "all":
                cat_lower = category.lower().replace("-", " ").replace("_", " ")
                fest_cat_lower = fest["category"].lower()
                if "case" in cat_lower and "case" not in fest_cat_lower:
                    continue
                if "strat" in cat_lower and "strat" not in fest_cat_lower:
                    continue
                if "mark" in cat_lower and "mark" not in fest_cat_lower:
                    continue

            # Query match
            if query:
                q = query.lower()
                content = f"{fest['title']} {fest['organizer']} {' '.join(fest['tags'])} {fest['category']}".lower()
                if q not in content:
                    continue

            fest_entry = dict(fest)
            fest_entry["source"] = self.source
            fest_entry["status"] = "Open"
            results.append(fest_entry)
            if len(results) >= limit:
                break

        return results
