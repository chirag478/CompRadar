import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database
from scrapers.aggregator import OpportunityAggregator

print("=== 1. TESTING DB INIT ===")
database.init_db()

print("\n=== 2. TESTING AGGREGATOR SCRAPE ===")
agg = OpportunityAggregator()
res = agg.scrape_all(category="all", limit=5)
print(f"Scraped count: {res['scraped_count']}, Saved count: {res['saved_count']}")

print("\n=== 3. TESTING DB QUERY & FIELDS ===")
items = database.get_opportunities()
print(f"Total retrieved from DB: {len(items)}")
for it in items[:4]:
    print(f"- [{it['source']}] ({it['category']}) {it['title'][:45]} | Org: {it['organizer'][:30]} | Prize: {it['prize']} | Deadline: {it['days_left']}")

print("\n=== 4. TESTING BOOKMARKS ===")
if items:
    first_id = items[0]['id']
    new_state = database.toggle_bookmark(first_id)
    print(f"Toggled bookmark for {first_id} -> {new_state}")
    bookmarked_items = database.get_opportunities(bookmarked_only=True)
    print(f"Bookmarked items count: {len(bookmarked_items)}")

print("\n=== 5. TESTING EXPORT ===")
csv_sample = agg.export_csv(items[:3])
print(f"CSV Header & first row:\n{csv_sample.splitlines()[:2]}")

print("\n=== 6. STATS ===")
print(database.get_stats())
print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
