"""
CompRadar - API & Web Server
Zero-dependency, multi-threaded HTTP server for CompRadar
Includes automatic background scraping, PWA support, and cloud-ready port configuration.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import os
import mimetypes
import threading
import time
import gzip
import database
from scrapers.aggregator import OpportunityAggregator

PORT = int(os.environ.get("PORT", 5000))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
aggregator = OpportunityAggregator()

def _background_scraper_loop(interval_hours=6):
    """
    Silent recurring background scraper loop that keeps opportunity data fresh
    without blocking user interaction or requiring manual scraping.
    """
    while True:
        try:
            # Sleep 6 hours between automated sync cycles
            time.sleep(interval_hours * 3600)
            print("[CompRadar AutoSync] Starting scheduled background refresh across all sources...")
            res = aggregator.scrape_all(limit=30)
            print(f"[CompRadar AutoSync] Auto-refresh complete. Processed {res.get('scraped_count', 0)} entries.")
        except Exception as ex:
            print(f"[CompRadar AutoSync] Recurring background sync error: {ex}")

class ScraperHandler(BaseHTTPRequestHandler):
    def _accepts_gzip(self):
        return "gzip" in self.headers.get("Accept-Encoding", "").lower()

    def _send_compressed_or_raw(self, raw_bytes, content_type, status=200, cache_control="no-cache"):
        use_gzip = len(raw_bytes) > 512 and self._accepts_gzip()
        payload = gzip.compress(raw_bytes, compresslevel=6) if use_gzip else raw_bytes
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", cache_control)
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, data, status=200):
        body = json.dumps(data, separators=(',', ':')).encode('utf-8')
        self._send_compressed_or_raw(body, "application/json; charset=utf-8", status=status, cache_control="no-cache")

    def _send_file(self, filepath, content_type=None):
        if not os.path.exists(filepath):
            self.send_error(404, "File Not Found")
            return
        
        if not content_type:
            content_type, _ = mimetypes.guess_type(filepath)
            if not content_type:
                if filepath.endswith(".json") or filepath.endswith(".webmanifest"):
                    content_type = "application/manifest+json"
                elif filepath.endswith(".js"):
                    content_type = "application/javascript"
                else:
                    content_type = "application/octet-stream"

        with open(filepath, "rb") as f:
            content = f.read()

        # Cache static assets (CSS/JS/manifest) briefly; keep HTML/SW fresh
        is_immutable_asset = filepath.endswith((".css", ".js", ".png", ".svg", ".ico")) and not filepath.endswith("sw.js")
        cache_header = "public, max-age=3600" if is_immutable_asset else "no-cache"

        if content_type.startswith(("text/", "application/javascript", "application/json", "application/manifest+json", "image/svg+xml")):
            self._send_compressed_or_raw(content, content_type, status=200, cache_control=cache_header)
        else:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", cache_header)
            self.send_header("Access-Control-Allow-Origin", "*")
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
                self.send_header("Content-Disposition", "attachment; filename=compradar_opportunities.json")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                csv_str = aggregator.export_csv(items)
                content = csv_str.encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", "attachment; filename=compradar_opportunities.csv")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            return

        # PWA Assets Root Aliases
        if path == "/manifest.json":
            self._send_file(os.path.join(STATIC_DIR, "manifest.json"), "application/manifest+json")
            return
        elif path == "/sw.js":
            self._send_file(os.path.join(STATIC_DIR, "sw.js"), "application/javascript")
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
        print("[Startup] Performing initial multi-source scrape...")
        try:
            aggregator.scrape_all(category="all", limit=20)
            print("[Startup] Initial catalog populated successfully!")
        except Exception as e:
            print(f"[Startup] Initial scrape notice: {e}")

    # Launch daemon background scraper thread (every 6 hours)
    bg_sync = threading.Thread(target=_background_scraper_loop, args=(6,), daemon=True)
    bg_sync.start()
    print("[Startup] Background auto-sync scheduler initialized (every 6 hours).")

    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, ScraperHandler)
    print(f"\n========================================================")
    print(f"  CompRadar Server Active on port {port}")
    print(f"  Local URL:  http://localhost:{port}")
    print(f"========================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
