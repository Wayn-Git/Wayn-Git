
"""
One-time helper: gets the Last.fm API credentials needed by the music card.

1. Visit https://www.last.fm/api/account/create
2. Create an application to get your API Key and Shared Secret.
3. Run: python3 scripts/get_lastfm_token.py
4. Enter your API Key and Shared Secret when prompted.
5. Log in to Last.fm in the browser and authorize the application.
6. Copy the session key it prints into a repo secret called LASTFM_SESSION_KEY.

Keep your API Shared Secret and Session Key private.
Unlike Spotify, Last.fm does not require a Premium subscription.
"""

import hashlib
import os
import secrets
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET

API_URL = "https://ws.audioscrobbler.com/2.0/"
AUTH_URL = "https://www.last.fm/api/auth/"

api_key = os.environ.get("LASTFM_API_KEY") or input("Last.fm API Key: ").strip()
api_secret = os.environ.get("LASTFM_API_SECRET") or input("Last.fm Shared Secret: ").strip()

if not api_key or not api_secret:
    raise SystemExit("Both API Key and Shared Secret are required.")



def api_signature(params):
    """Generate the MD5 signature required by Last.fm."""
    message = "".join(
        key + str(params[key])
        for key in sorted(params)
        if key not in ("format", "api_sig")
    ) + api_secret

    return hashlib.md5(message.encode("utf-8")).hexdigest()



def request_token(params):
    """Send a signed request to the Last.fm API."""
    data = urllib.parse.urlencode(params).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    with urllib.request.urlopen(req, timeout=20) as response:
        root = ET.fromstring(response.read())

    error = root.find("error")
    if error is not None:
        raise SystemExit(f"Last.fm API error: {error.text}")

    return root


# Step 1: Request a temporary token.
params = {
    "method": "auth.getToken",
    "api_key": api_key,
    "format": "xml",
}
params["api_sig"] = api_signature(params)

root = request_token(params)
token_element = root.find("token")

if token_element is None or not token_element.text:
    raise SystemExit("Could not obtain an authorization token.")

token = token_element.text

# Step 2: Ask the user to authorize the application.
auth_url = AUTH_URL + "?" + urllib.parse.urlencode(
    {"api_key": api_key, "token": token}
)

print("\nOpening Last.fm authorization in your browser.")
print("If it doesn't open, visit this URL:\n")
print(auth_url)

webbrowser.open(auth_url)

input(
    "\nLog in to Last.fm, approve the application, "
    "then return here and press Enter..."
)

# Step 3: Exchange the authorized token for a session key.
params = {
    "method": "auth.getSession",
    "api_key": api_key,
    "token": token,
    "format": "xml",
}
params["api_sig"] = api_signature(params)

root = request_token(params)
session_key = root.findtext("session/key")

if not session_key:
    raise SystemExit("Could not obtain a session key. Try authorizing again.")

print("\nYour Last.fm session key (keep it secret):\n")
print(session_key)
print("\nSave it as the LASTFM_SESSION_KEY repository secret.")


