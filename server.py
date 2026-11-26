"""
CompRadar - API & Web Server
Zero-dependency, multi-threaded HTTP server for CompRadar
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import os
import mimetypes
import database
from scrapers.aggregator import OpportunityAggregator

PORT = 5000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
aggregator = OpportunityAggregator()

class ScraperHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath, content_type=None):
        if not os.path.exists(filepath):
            self.send_error(404, "File Not Found")
            return
        
        if not content_type:
            content_type, _ = mimetypes.guess_type(filepath)
            if not content_type:
                content_type = "application/octet-stream"

        with open(filepath, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # API Endpoints
        if path == "/api/opportunities":
            source = query_params.get("source", [None])[0]
            category = query_params.get("category", [None])[0]
            query = query_params.get("query", [None])[0]
            sort_by = query_params.get("sort", ["deadline"])[0]
            bookmarked = query_params.get("bookmarked", ["false"])[0].lower() == "true"
            include_ended = query_params.get("include_ended", ["false"])[0].lower() == "true"
            urgent_only = query_params.get("urgent", ["false"])[0].lower() == "true"
            high_prize_only = query_params.get("high_prize", ["false"])[0].lower() == "true"
            app_status = query_params.get("app_status", [None])[0]

            results = database.get_opportunities(
                source=source,
                category=category,
                query=query,
                bookmarked_only=bookmarked,
                sort_by=sort_by,
                include_ended=include_ended,
                urgent_only=urgent_only,
                high_prize_only=high_prize_only,
                app_status=app_status
            )
            self._send_json({"count": len(results), "opportunities": results})
            return

        elif path == "/api/stats":
            stats = database.get_stats()
            self._send_json(stats)
            return

        elif path == "/api/export":
            fmt = query_params.get("format", ["csv"])[0].lower()
            source = query_params.get("source", [None])[0]
            category = query_params.get("category", [None])[0]
            query = query_params.get("query", [None])[0]
            bookmarked = query_params.get("bookmarked", ["false"])[0].lower() == "true"
            include_ended = query_params.get("include_ended", ["false"])[0].lower() == "true"

            items = database.get_opportunities(
                source=source,
                category=category,
                query=query,
                bookmarked_only=bookmarked,
                include_ended=include_ended
            )

            if fmt == "json":
                content = aggregator.export_json(items).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Disposition", "attachment; filename=opportunities.json")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                csv_str = aggregator.export_csv(items)
                content = csv_str.encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", "attachment; filename=opportunities.csv")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            return

        # Serve Frontend Static Assets
        if path == "/" or path == "/index.html":
            self._send_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")
        else:
            rel_path = path.lstrip("/")
            file_path = os.path.join(STATIC_DIR, rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self._send_file(file_path)
            else:
                self._send_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
        
        try:
            payload = json.loads(post_data) if post_data else {}
        except Exception:
            payload = {}

        if path == "/api/scrape":
            cat = payload.get("category", "all")
            query = payload.get("query", None)
            limit = int(payload.get("limit", 25))

            result = aggregator.scrape_all(category=cat, query=query, limit=limit)
            self._send_json(result)
            return

        elif path == "/api/bookmark":
            opp_id = payload.get("id")
            if not opp_id:
                self._send_json({"error": "Missing id"}, status=400)
                return
            new_state = database.toggle_bookmark(opp_id)
            self._send_json({"id": opp_id, "is_bookmarked": new_state})
            return

        elif path == "/api/status":
            opp_id = payload.get("id")
            new_status = payload.get("status", "None")
            if not opp_id:
                self._send_json({"error": "Missing id"}, status=400)
                return
            saved_status = database.update_application_status(opp_id, new_status)
            self._send_json({"id": opp_id, "application_status": saved_status})
            return

        elif path == "/api/import-csv":
            csv_text = payload.get("csv_text", "")
            if not csv_text:
                # Fallback to direct raw body if posted as plain text
                csv_text = post_data
            if not csv_text.strip():
                self._send_json({"error": "Missing csv content"}, status=400)
                return
            result = aggregator.import_custom_csv(csv_text)
            self._send_json(result)
            return

        else:
            self.send_error(404, "Endpoint Not Found")

def run(port=PORT):
    # Initialize DB and run initial seed scrape if empty
    database.init_db()
    stats = database.get_stats()
    if stats['total'] == 0:
        print("[Startup] Performing initial scrape to populate catalog...")
        try:
            aggregator.scrape_all(category="all", limit=15)
            print("[Startup] Initial catalog populated successfully!")
        except Exception as e:
            print(f"[Startup] Initial scrape notice: {e}")

    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, ScraperHandler)
    print(f"\n========================================================")
    print(f"  Opportunity Scraper Web Interface Running!")
    print(f"  Local URL:  http://localhost:{port}")
    print(f"========================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
