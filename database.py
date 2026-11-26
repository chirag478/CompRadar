"""
SQLite Database persistence for Scraped Opportunities & User Bookmarks
"""
import sqlite3
import json
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "opportunities.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        id TEXT PRIMARY KEY,
        source TEXT,
        title TEXT,
        category TEXT,
        organizer TEXT,
        deadline TEXT,
        deadline_raw TEXT,
        days_left TEXT,
        days_left_num INTEGER,
        prize TEXT,
        url TEXT,
        location TEXT,
        tags TEXT,
        banner TEXT,
        status TEXT,
        is_bookmarked INTEGER DEFAULT 0,
        application_status TEXT DEFAULT 'None',
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_opportunities(opportunities):
    """
    Inserts or updates opportunities while preserving user bookmarks and application status.
    """
    if not opportunities:
        return 0

    conn = get_connection()
    cursor = conn.cursor()
    saved_count = 0

    for opp in opportunities:
        tags_json = json.dumps(opp.get('tags', []))
        # Keep existing bookmark and application status if already present
        cursor.execute("""
        INSERT INTO opportunities (
            id, source, title, category, organizer, deadline, deadline_raw,
            days_left, days_left_num, prize, url, location, tags, banner, status, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            category=excluded.category,
            organizer=excluded.organizer,
            deadline=excluded.deadline,
            deadline_raw=excluded.deadline_raw,
            days_left=excluded.days_left,
            days_left_num=excluded.days_left_num,
            prize=excluded.prize,
            url=excluded.url,
            location=excluded.location,
            tags=excluded.tags,
            banner=excluded.banner,
            status=excluded.status,
            scraped_at=CURRENT_TIMESTAMP
        """, (
            opp['id'],
            opp['source'],
            opp['title'],
            opp['category'],
            opp['organizer'],
            opp['deadline'],
            opp.get('deadline_raw', ''),
            opp['days_left'],
            opp.get('days_left_num', 999),
            opp['prize'],
            opp['url'],
            opp['location'],
            tags_json,
            opp.get('banner'),
            opp['status']
        ))
        saved_count += 1

    conn.commit()
    conn.close()
    return saved_count

def get_opportunities(source=None, category=None, query=None, bookmarked_only=False, sort_by="deadline", include_ended=False, app_status=None, urgent_only=False, high_prize_only=False, location=None):
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    # Exclude ended/expired opportunities by default
    if not include_ended:
        conditions.append("(status != 'Closed' AND days_left_num >= 0 AND LOWER(days_left) NOT LIKE '%ended%' AND LOWER(days_left) NOT LIKE '%closed%')")

    if urgent_only:
        conditions.append("days_left_num >= 0 AND days_left_num <= 3")

    if high_prize_only:
        conditions.append("(prize LIKE '%lakh%' OR prize LIKE '%$%' OR prize LIKE '%50,000%' OR prize LIKE '%1,00,000%' OR prize LIKE '%25,000%')")

    if app_status and app_status.lower() != "all":
        conditions.append("LOWER(application_status) = LOWER(?)")
        params.append(app_status)

    if location and location.lower() != "all":
        loc = location.lower().strip()
        if loc in ("bengaluru", "bangalore", "blr"):
            conditions.append("(LOWER(location) LIKE '%bengaluru%' OR LOWER(location) LIKE '%bangalore%' OR LOWER(title) LIKE '%bengaluru%' OR LOWER(title) LIKE '%bangalore%' OR LOWER(organizer) LIKE '%bangalore%' OR LOWER(organizer) LIKE '%bengaluru%' OR LOWER(tags) LIKE '%bengaluru%')")
        elif loc == "online":
            conditions.append("(LOWER(location) LIKE '%online%' OR LOWER(location) LIKE '%global%' OR LOWER(location) LIKE '%remote%' OR LOWER(location) LIKE '%virtual%')")
        elif loc == "hybrid":
            conditions.append("(LOWER(location) LIKE '%hybrid%' OR (LOWER(location) NOT IN ('online', 'global online') AND LOWER(location) NOT LIKE 'online;%'))")
        elif loc == "delhi":
            conditions.append("(LOWER(location) LIKE '%delhi%' OR LOWER(location) LIKE '%gurgaon%' OR LOWER(location) LIKE '%ncr%' OR LOWER(location) LIKE '%noida%')")
        elif loc == "mumbai":
            conditions.append("(LOWER(location) LIKE '%mumbai%' OR LOWER(location) LIKE '%bombay%')")
        elif loc == "hyderabad":
            conditions.append("(LOWER(location) LIKE '%hyderabad%')")
        else:
            conditions.append("LOWER(location) LIKE LOWER(?)")
            params.append(f"%{loc}%")

    if source and source.lower() != "all":
        src_clean = source.lower().replace("-", "").replace("_", "")
        if "bschool" in src_clean:
            conditions.append("(LOWER(source) LIKE '%b-school%' OR LOWER(source) LIKE '%bschool%' OR LOWER(source) LIKE '%fest%')")
        else:
            conditions.append("LOWER(source) LIKE LOWER(?)")
            params.append(f"%{source}%")

    if category and category.lower() != "all":
        if category == "hackathons":
            conditions.append("(category LIKE '%Hackathon%' OR category LIKE '%Code%')")
        elif category == "case_study":
            conditions.append("(category LIKE '%Case%' OR category LIKE '%Study%')")
        elif category == "product":
            conditions.append("(category LIKE '%Product%' OR title LIKE '%Product%')")
        elif category == "strategy":
            conditions.append("(category LIKE '%Strategy%' OR category LIKE '%Consulting%' OR title LIKE '%Strategy%')")
        elif category == "marketing":
            conditions.append("(category LIKE '%Marketing%' OR category LIKE '%Brand%' OR title LIKE '%Marketing%' OR title LIKE '%Brand%')")
        elif category == "hiring":
            conditions.append("(category LIKE '%Hiring%')")

    if query and query.strip():
        q = f"%{query.strip()}%"
        conditions.append("(title LIKE ? OR organizer LIKE ? OR tags LIKE ? OR category LIKE ?)")
        params.extend([q, q, q, q])

    if bookmarked_only:
        conditions.append("is_bookmarked = 1")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Sort order
    if sort_by == "deadline":
        order_clause = "ORDER BY days_left_num ASC, scraped_at DESC"
    elif sort_by == "deadline_desc":
        order_clause = "ORDER BY days_left_num DESC, scraped_at DESC"
    elif sort_by == "prize":
        order_clause = "ORDER BY prize DESC, days_left_num ASC"
    elif sort_by == "title":
        order_clause = "ORDER BY title ASC"
    elif sort_by == "organizer":
        order_clause = "ORDER BY organizer ASC"
    elif sort_by == "newest":
        order_clause = "ORDER BY scraped_at DESC"
    else:
        order_clause = "ORDER BY days_left_num ASC"

    query_str = f"SELECT * FROM opportunities {where_clause} {order_clause}"
    cursor.execute(query_str, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        try:
            d['tags'] = json.loads(d['tags'])
        except Exception:
            d['tags'] = []
        d['is_bookmarked'] = bool(d['is_bookmarked'])
        results.append(d)

    conn.close()
    return results

def toggle_bookmark(opp_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_bookmarked FROM opportunities WHERE id = ?", (opp_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    new_state = 0 if row['is_bookmarked'] else 1
    cursor.execute("UPDATE opportunities SET is_bookmarked = ? WHERE id = ?", (new_state, opp_id))
    conn.commit()
    conn.close()
    return bool(new_state)

def update_application_status(opp_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE opportunities SET application_status = ? WHERE id = ?", (status, opp_id))
    conn.commit()
    conn.close()
    return status

def compute_total_prize_pool(cursor, active_cond):
    import re
    cursor.execute(f"SELECT prize FROM opportunities WHERE {active_cond}")
    rows = cursor.fetchall()
    total_inr = 0.0

    for (p,) in rows:
        if not p:
            continue
        s = p.lower().replace(',', '')
        # USD
        usd_m = re.search(r'\$\s*([0-9]+(?:\.[0-9]+)?)', s)
        if usd_m:
            total_inr += float(usd_m.group(1)) * 85.0
            continue
        # Crore
        cr_m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:crore|cr)', s)
        if cr_m:
            total_inr += float(cr_m.group(1)) * 10000000.0
            continue
        # Lakh
        lakh_m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:lakh|lac)', s)
        if lakh_m:
            total_inr += float(lakh_m.group(1)) * 100000.0
            continue
        # Plain INR
        inr_m = re.search(r'(?:₹|rs\.?|inr)\s*([0-9]+)', s)
        if inr_m:
            total_inr += float(inr_m.group(1))

    if total_inr >= 10000000.0:
        return f"₹{total_inr / 10000000.0:.2f} Cr+"
    elif total_inr >= 100000.0:
        return f"₹{total_inr / 100000.0:.1f}L+"
    elif total_inr > 0:
        return f"₹{int(total_inr):,}"
    return "₹10L+"

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    active_cond = "status != 'Closed' AND days_left_num >= 0 AND LOWER(days_left) NOT LIKE '%ended%'"
    
    cursor.execute(f"SELECT COUNT(*) FROM opportunities WHERE {active_cond}")
    total = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM opportunities WHERE category LIKE '%Hackathon%' AND {active_cond}")
    hackathons = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM opportunities WHERE (category LIKE '%Case%' OR category LIKE '%Product%') AND {active_cond}")
    case_studies = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM opportunities WHERE (category LIKE '%Strategy%' OR category LIKE '%Consulting%') AND {active_cond}")
    strategy = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM opportunities WHERE (category LIKE '%Marketing%' OR category LIKE '%Brand%') AND {active_cond}")
    marketing = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM opportunities WHERE is_bookmarked = 1 AND {active_cond}")
    bookmarks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT source) FROM opportunities")
    sources = cursor.fetchone()[0]

    prize_pool = compute_total_prize_pool(cursor, active_cond)

    conn.close()
    return {
        "total": total,
        "hackathons": hackathons,
        "case_studies": case_studies,
        "strategy": strategy,
        "marketing": marketing,
        "bookmarks": bookmarks,
        "sources": sources,
        "total_prize_pool": prize_pool
    }

init_db()
