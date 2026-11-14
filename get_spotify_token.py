#!/usr/bin/env python3
"""
One-time helper: gets the Spotify refresh token that the music card needs.

1. https://developer.spotify.com/dashboard -> Create app -> Web API
2. Add this exact Redirect URI:  http://127.0.0.1:8888/callback
   (Spotify wants 127.0.0.1 here, not "localhost")
3. Run:  python3 scripts/get_spotify_token.py
4. Log in in the browser tab that opens, click Agree, copy the token it prints
   into a repo secret called SPOTIFY_REFRESH_TOKEN.

Heads up: Spotify dev apps need the app owner to have Premium. If you don't,
use Last.fm instead (see top of music.py).
"""
import base64
import http.server
import json
import os
import secrets
import urllib.parse
import urllib.request
import webbrowser

REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "user-read-currently-playing user-read-recently-played user-top-read"

cid = os.environ.get("SPOTIFY_CLIENT_ID") or input("Client ID: ").strip()
secret = os.environ.get("SPOTIFY_CLIENT_SECRET") or input("Client secret: ").strip()
state = secrets.token_urlsafe(12)
got = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        q = urllib.parse.parse_qs(u.query)
        got.update({k: v[0] for k, v in q.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Done. You can close this tab and go back to the terminal.")

    def log_message(self, *args):
        pass


url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
    {"client_id": cid, "response_type": "code", "redirect_uri": REDIRECT, "scope": SCOPES, "state": state}
)
server = http.server.HTTPServer(("127.0.0.1", 8888), Handler)
print("Opening your browser. If nothing opens, paste this into it:\n\n" + url + "\n")
webbrowser.open(url)
while not got:
    server.handle_request()

if got.get("state") != state or "code" not in got:
    raise SystemExit(f"Login failed: {got.get('error', 'state mismatch')}")

basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
req = urllib.request.Request(
    "https://accounts.spotify.com/api/token",
    data=urllib.parse.urlencode(
        {"grant_type": "authorization_code", "code": got["code"], "redirect_uri": REDIRECT}
    ).encode(),
    headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(req, timeout=20) as r:
    tok = json.loads(r.read())

print("Your refresh token (keep it secret, it goes in a repo secret, never in a file):\n")
print(tok["refresh_token"])
