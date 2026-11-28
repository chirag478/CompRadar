"""
Superteam Earn Scraper
Fetches live Product, Growth, Design, and Engineering bounties from Superteam Earn's public API.
High relevance for Bengaluru builders, PMs, and growth/design teams.
"""
import urllib.request
import json
from datetime import datetime, timezone


class SuperteamScraper:
    def __init__(self):
        self.source = "Superteam Earn"
        self.endpoint = "https://earn.superteam.fun/api/listings/?take=25"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

    def scrape(self, category="all", query=None, limit=20):
        results = []
        try:
            req = urllib.request.Request(self.endpoint, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                listings = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[SuperteamScraper] Fetch error: {e}")
            return results

        if not isinstance(listings, list):
            return results

        now = datetime.now(timezone.utc)
        for item in listings:
            if item.get("isWinnersAnnounced") or (item.get("status") or "").upper() != "OPEN":
                continue

            title = (item.get("title") or "").strip()
            slug = (item.get("slug") or "").strip()
            if not title or not slug:
                continue

            if query and query.lower() not in title.lower():
                continue

            t_low = title.lower()
            if any(k in t_low for k in ("growth", "marketing", "video", "writing", "content", "community", "meme", "thread")):
                opp_cat = "Marketing & Brand"
            elif any(k in t_low for k in ("product", "ui", "ux", "design", "figma", "research", "strategy")):
                opp_cat = "Product Management"
            else:
                opp_cat = "Tech Hackathon"

            deadline_raw = item.get("deadline") or ""
            deadline_str = "Ongoing"
            days_left = "Open"
            days_left_num = 30
            if deadline_raw:
                try:
                    dt = datetime.fromisoformat(deadline_raw.replace("Z", "+00:00"))
                    delta = (dt - now).days
                    if delta < 0:
                        continue
                    days_left_num = delta
                    deadline_str = dt.strftime("%b %d, %Y")
                    days_left = "Ends today!" if delta == 0 else ("1 day left" if delta == 1 else f"{delta} days left")
                except Exception:
                    pass

            amt = item.get("rewardAmount")
            token = (item.get("token") or "USDC").upper()
            if amt:
                prize_str = f"${int(amt):,} {token}" if token in ("USDC", "USDT", "USD") else f"{amt} {token}"
            else:
                prize_str = "Bounty Reward"

            sponsor = item.get("sponsor") or {}
            organizer = sponsor.get("name") or "Superteam Partner"

            results.append({
                "id": f"superteam_{item.get('id', slug)}",
                "source": self.source,
                "title": title,
                "category": opp_cat,
                "organizer": organizer,
                "deadline": deadline_str,
                "deadline_raw": deadline_raw,
                "days_left": days_left,
                "days_left_num": days_left_num,
                "prize": prize_str,
                "url": f"https://earn.superteam.fun/listing/{slug}",
                "location": "Global Online / Bengaluru Hub",
                "tags": [opp_cat, "Bounty", "Open to All"],
                "banner": None,
                "status": "Closing Soon" if 0 <= days_left_num <= 3 else "Open"
            })

            if len(results) >= limit:
                break

        return results
