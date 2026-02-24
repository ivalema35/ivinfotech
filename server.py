"""
Local dev server — mimics Apache mod_rewrite for clean URLs.
  /index        → serves index.html  (internally)
  /index.html   → 301 redirect to /index
  /about        → serves about.html  (internally)
Usage:  python server.py
Then open: http://localhost:5500
"""

import http.server
import os

PORT = 8080
ROOT = os.path.dirname(os.path.abspath(__file__))


class CleanURLHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0]  # strip query/hash

        # 1. Redirect /page.html → /page  (301, like Apache)
        if path.endswith(".html") and not path.startswith("/components/"):
            clean = path[:-5] or "/"
            qs = self.path[len(path):]          # preserve ?query or #hash
            self.send_response(301)
            self.send_header("Location", clean + qs)
            self.end_headers()
            return

        # 2. Resolve clean URL → .html file  (internal, like mod_rewrite)
        if path != "/" and "." not in os.path.basename(path):
            candidate = os.path.join(ROOT, path.lstrip("/") + ".html")
            if os.path.isfile(candidate):
                # Rewrite path internally so SimpleHTTPRequestHandler serves it
                self.path = path + ".html" + self.path[len(path):]

        # 3. Root "/" → index.html
        super().do_GET()

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} → {fmt % args}")


if __name__ == "__main__":
    os.chdir(ROOT)
    server = http.server.HTTPServer(("", PORT), CleanURLHandler)
    print(f"\n  IV Infotech Dev Server")
    print(f"  ─────────────────────────────────────")
    print(f"  Local:   http://localhost:{PORT}")
    print(f"  Network: http://127.0.0.1:{PORT}")
    print(f"  Clean URLs: /about  /services  /contact")
    print(f"  Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
