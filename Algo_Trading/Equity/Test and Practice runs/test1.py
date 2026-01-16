```python
# python
import os
import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import queue

HOST, PORT = "127.0.0.1", 8000
# Set this to exactly the redirect URI registered in Upstox (include or omit trailing slash to match registration)
REDIRECT_URI = f"http://{HOST}:{PORT}"  # update to http://127.0.0.1:8000/ if registration includes trailing slash

API_KEY = os.getenv("18185106-6257-4a85-a84a-2ea314f91927") or input("Enter UPSTOX API_KEY (client_id): ").strip()

code_q = queue.Queue()

class DebugHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        print("Incoming request line:", self.requestline)
        print("Path:", parsed.path)
        print("Query params:", qs)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Captured request. You can close this tab.")
        if "code" in qs:
            code_q.put(qs["code"][0])

    def log_message(self, fmt, *args):
        return

def run_server():
    server = HTTPServer((HOST, PORT), DebugHandler)
    print(f"Listening on {REDIRECT_URI} — start this before authorizing")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

print("Using REDIRECT_URI:", REDIRECT_URI)
auth_url = (
    "https://api.upstox.com/v2/login/authorization/dialog?"
    f"client_id={urllib.parse.quote(API_KEY)}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code"
)
print("Open this URL in your browser (server must be running):")
print(auth_url)
webbrowser.open(auth_url)

try:
    code = code_q.get(timeout=180)
    print("Captured authorization code:", code)
except Exception:
    print("No authorization code received (timed out).")