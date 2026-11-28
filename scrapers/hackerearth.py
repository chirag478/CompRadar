"""
HackerEarth Scraper
Fetches live hackathons and corporate hiring challenges from HackerEarth's public events feed.
"""
import urllib.request
import json
import re
from datetime import datetime, timezone


class HackerEarthScraper:
    def __init__(self):
        self.source = "HackerEarth"
        self.endpoint = "https://www.hackerearth.com/chrome-extension/events/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

    def scrape(self, category="all", query=None, limit=25):
        results = []
        try:
            req = urllib.request.Request(self.endpoint, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[HackerEarthScraper] Fetch error: {e}")
            return results

        events = data.get("response") or []
        now = datetime.now(timezone.utc)

        for ev in events:
            status_raw = (ev.get("status") or "").upper()
            if status_raw not in ("ONGOING", "UPCOMING"):
                continue

            title = (ev.get("title") or "").strip()
            url = (ev.get("url") or "").strip()
            if not title or not url:
                continue

            if query and query.lower() not in f"{title} {ev.get('description', '')}".lower():
                continue

            ctype = (ev.get("challenge_type") or "").lower()
            if "hiring" in ctype or "hiring" in title.lower():
                opp_cat = "Hiring Challenge"
            else:
                opp_cat = "Tech Hackathon"

            if category == "hiring" and opp_cat != "Hiring Challenge":
                continue
            if category == "hackathons" and opp_cat != "Tech Hackathon":
                continue

            end_tz = ev.get("end_tz") or ""
            deadline_str = ev.get("end_date") or "Ongoing"
            days_left = "Open"
            days_left_num = 30

            if end_tz:
                try:
                    dt = datetime.fromisoformat(end_tz.replace(" ", "T"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    delta = (dt - now).days
                    if delta < 0:
                        continue
                    days_left_num = delta
                    deadline_str = dt.strftime("%b %d, %Y")
                    days_left = "Ends today!" if delta == 0 else ("1 day left" if delta == 1 else f"{delta} days left")
                except Exception:
                    pass

            tags = [opp_cat, "HackerEarth"]
            if opp_cat == "Hiring Challenge" or "hire" in title.lower() or "job" in title.lower():
                tags.append("PPO / PPI")

            slug = re.sub(r"[^a-zA-Z0-9]+", "_", title.lower())[:36]
            results.append({
                "id": f"hackerearth_{slug}",
                "source": self.source,
                "title": title,
                "category": opp_cat,
                "organizer": "HackerEarth Partner",
                "deadline": deadline_str,
                "deadline_raw": end_tz,
                "days_left": days_left,
                "days_left_num": days_left_num,
                "prize": "PPO / Cash Prizes" if opp_cat == "Hiring Challenge" else "Cash & Swag",
                "url": url,
                "location": "Online",
                "tags": tags,
                "banner": ev.get("thumbnail") or ev.get("cover_image"),
                "status": "Closing Soon" if 0 <= days_left_num <= 3 else "Open"
            })

            if len(results) >= limit:
                break

        return results
