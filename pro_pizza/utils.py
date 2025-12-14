# utils.py
import requests, time
from django.conf import settings

def get_tokens_from_session(request):
    return request.session.get("tokens")

def refresh_tokens_if_needed(request):
    tokens = get_tokens_from_session(request)
    if not tokens:
        return None
    # naive check: refresh if expiry near
    # tokens returned contain 'expires_in' (seconds) at exchange time; we should stash expiry timestamp
    expires_at = tokens.get('expires_at')  # assume we stored it earlier
    now = int(time.time())
    if not expires_at or now >= expires_at - 30:
        # refresh
        data = {
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": "django-bff",
            "client_secret": "<CLIENT_SECRET>",
        }
        r = requests.post(settings.KEYCLOAK_TOKEN_ENDPOINT, data=data)
        if r.status_code != 200:
            # refresh failed -> force re-login
            request.session.pop('tokens', None)
            return None
        new = r.json()
        # compute expires_at (now + expires_in)
        new['expires_at'] = int(time.time()) + int(new.get('expires_in', 0))
        request.session['tokens'] = new
        return new
    return tokens
