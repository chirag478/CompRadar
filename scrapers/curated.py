"""
Curated Feed / CSV Scraper & Ingestor Module
Parses curated competition spreadsheets, feeds, and CSV uploads into unified Opportunity items.
"""
import csv
import os
import re
from datetime import datetime

DEFAULT_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "curated_competitions.csv"
)

class CuratedFeedScraper:
    def __init__(self, csv_path=None):
        self.csv_path = csv_path or DEFAULT_CSV_PATH

    @staticmethod
    def _parse_deadline(date_str):
        if not date_str or not str(date_str).strip():
            return "Ongoing", "", 999
        
        raw_clean = re.sub(r',.*$', '', str(date_str)).strip()
        parsed_dt = None
        for fmt in ['%d %b %Y', '%d %b %y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']:
            try:
                parsed_dt = datetime.strptime(raw_clean, fmt)
                break
            except Exception:
                pass
        
        if not parsed_dt:
            # Try fuzzy extract e.g. "2 Dec 2026"
            m = re.search(r'(\d{1,2}\s+[A-Za-z]{3,}\s+\d{2,4})', date_str)
            if m:
                for fmt in ['%d %B %Y', '%d %b %Y', '%d %b %y']:
                    try:
                        parsed_dt = datetime.strptime(m.group(1), fmt)
                        break
                    except Exception:
                        pass

        if parsed_dt:
            deadline_str = parsed_dt.strftime("%b %d, %Y")
            now = datetime.now()
            delta = (parsed_dt - now).days
            if delta > 1:
                days_left = f"{delta} days left"
            elif delta == 1:
                days_left = "1 day left"
            elif delta == 0:
                days_left = "Ends today!"
            else:
                days_left = "Closed"
            return deadline_str, days_left, delta

        return str(date_str)[:15], str(date_str)[:15], 999

    @staticmethod
    def _extract_prize(notes, title):
        text = f"{title} {notes}"
        # Look for prize pool like ₹4.5 lakh, ₹22,000, prize pool ₹18,000, etc.
        m = re.search(r'(₹\s*[\d,.]+(?:\s*(?:lakh|crore|k))?|Rs\.?\s*[\d,.]+|prize pool\s*₹?\s*[\d,.]+(?:\s*(?:lakh|k))?)', text, re.I)
        if m:
            val = m.group(0).strip()
            # Clean up redundant prefix
            val = re.sub(r'^(?:prize pool\s*)+', '', val, flags=re.I).strip()
            if not val.startswith('₹') and not val.lower().startswith('rs'):
                val = f"₹{val}"
            return val
        if "ppi" in text.lower() or "internship" in text.lower():
            return "PPI / Internship Opportunity"
        return "Certificates & Awards"

    @staticmethod
    def _extract_category(title, format_rounds, notes):
        text = f"{title} {format_rounds} {notes}".lower()
        if "marketing" in text or "brand" in text or "advertising" in text:
            return "Marketing & Brand"
        if "strategy" in text or "strategic" in text or "positioning" in text or "caseino" in text:
            return "Strategy & Consulting"
        if "supply chain" in text or "operations" in text or "analytics" in text or "quality" in text or "process" in text:
            return "Product & Operations"
        if "case" in text or "case study" in text or "casequest" in text:
            return "Product Case Study"
        if "hackathon" in text or "code" in text or "coding" in text:
            return "Tech Hackathon"
        return "Case Competition"

    @staticmethod
    def _extract_organizer(title, source_col, notes, url=""):
        # Known prominent institutes and corporate organizers
        prominent = [
            ("Grant Thornton", "Grant Thornton Bharat"),
            ("Symbiosis", "SIOM (Symbiosis)"),
            ("SIOM", "SIOM (Symbiosis)"),
            ("TAPMI", "TAPMI Manipal"),
            ("FLAME", "FLAME University"),
            ("IIM Udaipur", "IIM Udaipur"),
            ("IIM", "IIM"),
            ("IIT", "IIT"),
            ("WealthNest", "WealthNest"),
            ("GE HealthCare", "GE HealthCare"),
            ("L'Oréal", "L'Oréal"),
            ("IBS Hyderabad", "IBS Hyderabad"),
            ("Food for Thought", "Food for Thought Challenge")
        ]
        combined = f"{title} {source_col} {notes} {url}"
        for keyword, name in prominent:
            if keyword.lower() in combined.lower():
                return name

        # Look for pattern in parentheses e.g. "(FLAME University)"
        m_paren = re.search(r'\(([^)]+)\)', title)
        if m_paren and len(m_paren.group(1)) > 2 and not m_paren.group(1).isdigit():
            return m_paren.group(1).strip()
        
        # Look for dash delimiter e.g. "Event – Organizer"
        m_dash = re.search(r'[–-]\s*([^–-]+)$', title)
        if m_dash and len(m_dash.group(1)) > 2 and not m_dash.group(1).strip().isdigit():
            return m_dash.group(1).strip()

        if source_col and source_col.strip() and source_col.strip().lower() not in ["unstop", "curated"]:
            return source_col.strip()
        
        return "National B-School / Corporate"

    def parse_csv_content(self, csv_text):
        reader = csv.DictReader(csv_text.splitlines())
        results = []

        for idx, row in enumerate(reader):
            if idx >= 100:
                break

            title = (row.get('Competition / event') or row.get('title') or '').strip()
            if not title or len(title) < 3 or len(title) > 180:
                continue

            last_date = row.get('Last date to register ') or row.get('Last date to register') or row.get('deadline') or ''
            deadline_str, days_left, delta = self._parse_deadline(last_date)

            # Skip ended competitions
            if delta < 0 or days_left == "Closed":
                continue

            url = (row.get('Apply / official details') or row.get('url') or '').strip()
            if not url.startswith(('http://', 'https://')):
                continue
            notes = (row.get('Evidence / notes') or row.get('notes') or '').strip()
            format_rounds = (row.get('Format / rounds') or '').strip()
            eligibility = (row.get('First-year PG eligibility') or '').strip()
            elig_low = eligibility.lower()
            if elig_low.startswith(('no', 'ug only', 'undergraduate only', 'not eligible')):
                continue
            team_size = (row.get('Team size') or '').strip()
            location = (row.get('Bengaluru connection') or 'Online').strip()
            source_platform = (row.get('Source') or 'Curated').strip()

            category = self._extract_category(title, format_rounds, notes)
            organizer = self._extract_organizer(title, source_platform, notes, url=url)
            prize = self._extract_prize(notes, title)

            tags = [category]
            if team_size:
                tags.append(f"Team: {team_size}")
            if "pg" in eligibility.lower() or "mba" in eligibility.lower():
                tags.append("MBA / PG")
            elif "anyone" in eligibility.lower() or "all" in eligibility.lower():
                tags.append("Open to All")
            
            # Clean opp ID
            clean_slug = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower())[:30]
            opp_id = f"curated_{clean_slug}_{idx}"

            status = "Closing Soon" if (0 <= delta <= 3) else "Open"

            results.append({
                "id": opp_id,
                "source": "Curated Feed",
                "title": title,
                "category": category,
                "organizer": organizer,
                "deadline": deadline_str,
                "deadline_raw": last_date,
                "days_left": days_left,
                "days_left_num": delta,
                "prize": prize,
                "url": url if url.startswith("http") else f"https://{url}",
                "location": location[:35] if location else "Online",
                "tags": tags[:5],
                "banner": None,
                "status": status
            })

        return results

    def scrape(self, category="all", query=None, limit=50):
        if not os.path.exists(self.csv_path):
            return []

        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                content = f.read()
            items = self.parse_csv_content(content)
            
            # Apply category filtering if requested
            if category and category.lower() != "all":
                cat_lower = category.lower()
                filtered = []
                for it in items:
                    c = it['category'].lower()
                    if cat_lower in c or (cat_lower == 'strategy' and 'strategy' in c) or (cat_lower == 'marketing' and 'marketing' in c):
                        filtered.append(it)
                items = filtered

            if query and query.strip():
                q = query.strip().lower()
                items = [it for it in items if q in it['title'].lower() or q in it['organizer'].lower() or any(q in t.lower() for t in it.get('tags', []))]

            return items[:limit]
        except Exception as e:
            print(f"[CuratedFeedScraper] Error: {e}")
            return []
