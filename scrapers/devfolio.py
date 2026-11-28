"""
Devfolio Scraper
Fetches live open-registration hackathons from Devfolio's public search API.
Strong coverage of Indian, Bengaluru, and university hackathons.
"""
import urllib.request
import json
from datetime import datetime, timezone


class DevfolioScraper:
    def __init__(self):
        self.source = "Devfolio"
        self.endpoint = "https://api.devfolio.co/api/search/hackathons"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def scrape(self, query=None, limit=25):
        results = []
        payload = {"type": "application_open", "from": 0, "size": min(limit, 30)}
        if query:
            payload["search"] = query

        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=self.headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[DevfolioScraper] Fetch error: {e}")
            return results

        hits = (data.get("hits") or {}).get("hits") or []
        now = datetime.now(timezone.utc)

        for hit in hits:
            src = hit.get("_source") or {}
            name = (src.get("name") or "").strip()
            slug = (src.get("slug") or "").strip()
            if not name or not slug:
                continue

            # Deadline parsing
            ends_at = src.get("ends_at") or ""
            deadline_str = "Ongoing"
            days_left = "Open"
            days_left_num = 60

            if ends_at:
                try:
                    dt = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    delta = (dt - now).days
                    if delta < 0:
                        continue
                    days_left_num = delta
                    deadline_str = dt.strftime("%b %d, %Y")
                    if delta == 0:
                        days_left = "Ends today!"
                    elif delta == 1:
                        days_left = "1 day left"
                    else:
                        days_left = f"{delta} days left"
                except Exception:
                    pass

            # Location parsing
            city = (src.get("city") or "").strip()
            state = (src.get("state") or "").strip()
            is_online = bool(src.get("is_online"))
            if city and state:
                location = f"{city}, {state}" + (" / Hybrid" if is_online else "")
            elif city:
                location = f"{city}" + (" / Hybrid" if is_online else "")
            else:
                location = "Online" if is_online else (src.get("country") or "Online")

            # Organizer & Prize
            hosted_by = src.get("hosted_by")
            organizer = "Devfolio Host"
            if isinstance(hosted_by, dict):
                organizer = hosted_by.get("name") or organizer
            elif isinstance(hosted_by, str) and hosted_by.strip():
                organizer = hosted_by.strip()

            prize_str = "Prizes & Swag"
            prizes = src.get("prizes")
            if isinstance(prizes, dict) and prizes.get("amount"):
                currency = prizes.get("currency", "$")
                sym = "₹" if currency.upper() == "INR" else "$"
                prize_str = f"{sym}{int(prizes['amount']):,}"
            elif isinstance(prizes, list) and prizes:
                prize_str = f"{len(prizes)} Prize Tracks"

            tags = ["Hackathon", "Devfolio"]
            if src.get("team_size"):
                tags.append(f"Team: 1-{src['team_size']}")
            themes = src.get("themes") or []
            for t in themes[:2]:
                t_name = t.get("name") if isinstance(t, dict) else str(t)
                if t_name:
                    tags.append(t_name)

            results.append({
                "id": f"devfolio_{slug}",
                "source": self.source,
                "title": name,
                "category": "Tech Hackathon",
                "organizer": organizer,
                "deadline": deadline_str,
                "deadline_raw": ends_at,
                "days_left": days_left,
                "days_left_num": days_left_num,
                "prize": prize_str,
                "url": f"https://{slug}.devfolio.co",
                "location": location,
                "tags": tags[:5],
                "banner": src.get("cover_img"),
                "status": "Closing Soon" if 0 <= days_left_num <= 3 else "Open"
            })

            if len(results) >= limit:
                break

        return results
