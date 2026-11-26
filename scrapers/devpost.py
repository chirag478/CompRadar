"""
Devpost Scraper Module
Scrapes global tech hackathons, AI challenges, and product builds.
"""
import urllib.request
import urllib.parse
import json
import re

class DevpostScraper:
    BASE_URL = "https://devpost.com/api/hackathons"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://devpost.com/hackathons"
    }

    @staticmethod
    def _fetch_url(url, timeout=10):
        req = urllib.request.Request(url, headers=DevpostScraper.DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"[DevpostScraper] Error fetching {url}: {e}")
            return None

    @staticmethod
    def _clean_html(raw_html):
        if not raw_html:
            return ""
        clean = re.sub(r'<[^>]+>', '', str(raw_html))
        return clean.strip()

    @staticmethod
    def _normalize_item(raw):
        opp_id = str(raw.get('id') or "")
        title = raw.get('title', 'Untitled Hackathon').strip()
        url = raw.get('url', 'https://devpost.com')
        organizer = raw.get('organization_name') or "Devpost Community"
        location = raw.get('displayed_location', {}).get('location') if isinstance(raw.get('displayed_location'), dict) else (raw.get('displayed_location') or "Online")

        # Prize cleaning
        raw_prize = raw.get('prize_amount')
        prize_clean = DevpostScraper._clean_html(raw_prize)
        if not prize_clean or prize_clean == "$0":
            prize_summary = "Prizes & Swag"
        else:
            prize_summary = prize_clean

        # Submission dates & deadline
        dates = raw.get('submission_period_dates') or ""
        time_left = raw.get('time_left_to_submission') or "Open"
        
        # Estimate days left
        days_left_num = 999
        match = re.search(r'(\d+)\s+day', time_left.lower())
        if match:
            days_left_num = int(match.group(1))
        elif "hour" in time_left.lower():
            days_left_num = 0

        # Tags & Themes
        themes = raw.get('themes') or []
        tags = []
        for t in themes:
            if isinstance(t, dict) and t.get('name'):
                tags.append(t.get('name'))
            elif isinstance(t, str):
                tags.append(t)
        
        # Inferred category
        title_lower = title.lower()
        if "product" in title_lower or "design" in title_lower:
            cat = "Product & Design"
        elif "ai" in title_lower or "machine learning" in title_lower:
            cat = "AI & Tech Hackathon"
        else:
            cat = "Tech Hackathon"

        thumbnail = raw.get('thumbnail_url')
        if thumbnail and thumbnail.startswith("//"):
            thumbnail = f"https:{thumbnail}"

        return {
            "id": f"devpost_{opp_id}",
            "source": "Devpost",
            "title": title,
            "category": cat,
            "organizer": organizer,
            "deadline": dates,
            "deadline_raw": dates,
            "days_left": time_left,
            "days_left_num": days_left_num,
            "prize": prize_summary,
            "url": url,
            "location": location,
            "tags": tags[:5],
            "banner": thumbnail,
            "status": "Closing Soon" if (0 <= days_left_num <= 3) else "Open"
        }

    def scrape(self, query=None, limit=20):
        url = f"{self.BASE_URL}?page=1&status[]=upcoming&status[]=open"
        if query:
            url += f"&search={urllib.parse.quote(query)}"

        data = self._fetch_url(url)
        if not data:
            return []

        raw_list = data.get('hackathons', [])
        results = []
        for item in raw_list[:limit]:
            results.append(self._normalize_item(item))

        return results
