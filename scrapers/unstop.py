"""
Unstop (formerly Dare2Compete) Scraper Module
Scrapes tech hackathons, case study competitions, product challenges, and hiring challenges.
"""
import urllib.request
import urllib.parse
import json
import re
from datetime import datetime

class UnstopScraper:
    BASE_URL = "https://unstop.com/api/public/opportunity/search-result"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://unstop.com/"
    }

    @staticmethod
    def _fetch_url(url, timeout=10):
        req = urllib.request.Request(url, headers=UnstopScraper.DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"[UnstopScraper] Error fetching {url}: {e}")
            return None

    @staticmethod
    def _format_prize(prizes_list):
        if not prizes_list or not isinstance(prizes_list, list):
            return "Certificate & Recognition"
        
        cash_prizes = []
        other_perks = []
        for p in prizes_list:
            if not isinstance(p, dict):
                continue
            cash = p.get('cash')
            max_cash = p.get('max_cash')
            curr = p.get('currencyCode') or "INR"
            symbol = "₹" if curr == "INR" else ("$" if curr == "USD" else curr)

            if cash:
                try:
                    cash_prizes.append(f"{symbol}{int(float(cash)):,}")
                except Exception:
                    cash_prizes.append(f"{symbol}{cash}")
            elif max_cash:
                try:
                    cash_prizes.append(f"Up to {symbol}{int(float(max_cash)):,}")
                except Exception:
                    cash_prizes.append(f"Up to {symbol}{max_cash}")
            
            others = p.get('others')
            if others:
                other_perks.append(others.strip())
        
        if cash_prizes:
            main_cash = cash_prizes[0]
            if len(cash_prizes) > 1:
                return f"{main_cash} (Total {len(cash_prizes)} prizes)"
            return main_cash
        
        if other_perks:
            return other_perks[0][:40] + ("..." if len(other_perks[0]) > 40 else "")
            
        return "Awards & Certificates"

    @staticmethod
    def _normalize_item(raw, inferred_category="Hackathon"):
        opp_id = str(raw.get('id') or raw.get('short_id') or "")
        title = raw.get('title', 'Untitled Opportunity').strip()
        
        # Link URL
        raw_url = raw.get('seo_url') or raw.get('public_url') or ""
        if raw_url.startswith("http"):
            url = raw_url
        elif raw_url:
            url = f"https://unstop.com/{raw_url.lstrip('/')}"
        else:
            url = f"https://unstop.com/o/{opp_id}"

        # Organizer
        org_data = raw.get('organisation')
        organizer = "Unstop Host"
        if isinstance(org_data, dict):
            organizer = org_data.get('name') or org_data.get('short_name') or "Unstop Host"
        elif isinstance(org_data, str) and org_data.strip():
            organizer = org_data.strip()

        # Location (check locations array, city, and organizer institute hints)
        location = "Online"
        locations = raw.get('locations')
        if locations and isinstance(locations, list) and len(locations) > 0:
            first_loc = locations[0]
            if isinstance(first_loc, dict):
                city = first_loc.get('city') or ""
                state = first_loc.get('state') or ""
                country = first_loc.get('country') or ""
                location = ", ".join([x for x in (city, state) if x]) or country or "Online"
            elif isinstance(first_loc, str) and first_loc.strip():
                location = first_loc.strip()
        if location == "Online":
            org_low = organizer.lower()
            if any(k in org_low for k in ("bangalore", "bengaluru", "iimb", "iisc", "sibm bengaluru")):
                location = "Bengaluru / Online"

        # Dates & Deadline
        reg_req = raw.get('regnRequirements') or {}
        end_date_str = reg_req.get('end_regn_dt') or raw.get('end_date') or ""
        remaining_days_text = reg_req.get('remain_days') or ""
        reg_status = reg_req.get('reg_status') or ""
        
        deadline_formatted = "Ongoing"
        days_left_num = 999
        if end_date_str:
            try:
                # ISO parsing e.g. 2026-12-08T00:00:00+05:30
                clean_dt = end_date_str.split('+')[0].split('.')[0]
                dt = datetime.fromisoformat(clean_dt)
                deadline_formatted = dt.strftime("%b %d, %Y")
                now = datetime.now()
                delta = (dt - now).days
                days_left_num = delta
                if not remaining_days_text:
                    if delta > 1:
                        remaining_days_text = f"{delta} days left"
                    elif delta == 1:
                        remaining_days_text = "1 day left"
                    elif delta == 0:
                        remaining_days_text = "Ends today!"
                    else:
                        remaining_days_text = "Closed"
            except Exception:
                deadline_formatted = end_date_str[:10]

        # Status calculation
        if reg_status == "FINISHED" or remaining_days_text.lower() == "ended" or days_left_num < 0:
            status = "Closed"
        elif 0 <= days_left_num <= 3 or "hour" in remaining_days_text.lower():
            status = "Closing Soon"
        else:
            status = "Open"

        # Category determination
        title_lower = title.lower()
        cat = inferred_category
        if "marketing" in title_lower or "brand" in title_lower or "ad-venture" in title_lower:
            cat = "Marketing & Brand"
        elif "strategy" in title_lower or "consulting" in title_lower or "foresight" in title_lower:
            cat = "Strategy & Consulting"
        elif "case study" in title_lower or "case comp" in title_lower or "case challenge" in title_lower:
            cat = "Product Case Study"
        elif "product" in title_lower or "pm " in title_lower:
            cat = "Product Management"
        elif "hackathon" in title_lower or "code" in title_lower:
            cat = "Tech Hackathon"
        elif "hiring" in title_lower or "job" in title_lower:
            cat = "Hiring Challenge"

        # Tags
        tags = []
        if cat != "Hackathon":
            tags.append(cat)
        filters = raw.get('filters') or []
        for f in filters:
            if isinstance(f, dict) and f.get('name') and f.get('name') not in ['All']:
                tags.append(f.get('name'))
        
        # Add quick domain tags
        for kw in ["AI", "ML", "Web3", "Product", "UI/UX", "Coding", "Finance", "Consulting"]:
            if kw.lower() in title_lower and kw not in tags:
                tags.append(kw)

        # Prize & PPO/PPI detection
        prizes_raw = raw.get('prizes')
        prize_summary = UnstopScraper._format_prize(prizes_raw)
        prizes_blob = json.dumps(prizes_raw or "").lower()
        if any(k in prizes_blob or k in title_lower for k in ("ppo", "ppi", "pre-placement", "internship")):
            if "PPO / PPI" not in tags:
                tags.append("PPO / PPI")
        filters_blob = json.dumps(filters or "").lower()
        if any(k in filters_blob for k in ("mba", "postgraduate", "pg", "management")):
            if "MBA / PG" not in tags:
                tags.append("MBA / PG")

        # Banner/thumbnail
        banner = None
        thumb = raw.get('thumb')
        if thumb and isinstance(thumb, str) and thumb.startswith("http"):
            banner = thumb
        elif raw.get('banner_mobile') and isinstance(raw.get('banner_mobile'), dict):
            banner = raw.get('banner_mobile').get('image_url')

        return {
            "id": f"unstop_{opp_id}",
            "source": "Unstop",
            "title": title,
            "category": cat,
            "organizer": organizer,
            "deadline": deadline_formatted,
            "deadline_raw": end_date_str,
            "days_left": remaining_days_text or (f"{days_left_num} days" if days_left_num < 365 else "Open"),
            "days_left_num": days_left_num,
            "prize": prize_summary,
            "url": url,
            "location": location,
            "tags": tags[:5],
            "banner": banner,
            "status": status
        }

    def scrape(self, category="all", query=None, limit=20):
        results = []
        endpoints = []

        if category in ["all", "hackathons", "tech"]:
            url = f"{self.BASE_URL}?opportunity=hackathons&per_page={limit}"
            if query:
                url += f"&searchTerm={urllib.parse.quote(query)}"
            endpoints.append((url, "Tech Hackathon"))

        if category in ["all", "case_study", "product"]:
            # Query competitions with case study or product keywords
            term = query if query else "case study"
            url_case = f"{self.BASE_URL}?opportunity=competitions&searchTerm={urllib.parse.quote(term)}&per_page={limit}"
            endpoints.append((url_case, "Product Case Study"))

            if not query or "product" in query.lower():
                url_pm = f"{self.BASE_URL}?opportunity=competitions&searchTerm=product%20management&per_page={limit}"
                endpoints.append((url_pm, "Product Management"))

        if category in ["all", "strategy"]:
            url_strat = f"{self.BASE_URL}?opportunity=competitions&searchTerm=strategy&per_page={limit}"
            endpoints.append((url_strat, "Strategy & Consulting"))

        if category in ["all", "marketing"]:
            url_mkt = f"{self.BASE_URL}?opportunity=competitions&searchTerm=marketing&per_page={limit}"
            endpoints.append((url_mkt, "Marketing & Brand"))

        if category in ["all", "hiring"]:
            url_hiring = f"{self.BASE_URL}?opportunity=hiring-challenges&per_page={limit}"
            if query:
                url_hiring += f"&searchTerm={urllib.parse.quote(query)}"
            endpoints.append((url_hiring, "Hiring Challenge"))

        seen_ids = set()
        for url, default_cat in endpoints:
            data = self._fetch_url(url)
            if not data:
                continue
            items = data.get('data', {}).get('data', [])
            for raw in items:
                norm = self._normalize_item(raw, inferred_category=default_cat)
                # Filter out ended / closed competitions
                if norm['status'] == "Closed" or norm.get('days_left_num', 0) < 0 or "ended" in str(norm.get('days_left', '')).lower():
                    continue
                if norm['id'] not in seen_ids:
                    seen_ids.add(norm['id'])
                    results.append(norm)

        return results
