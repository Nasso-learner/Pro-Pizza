# views_auth.py

import time, secrets, requests
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from rest_framework.response import Response

# 🔧 Replace these with your environment or settings
KEYCLOAK_BASE = "http://localhost:8080"
REALM = "prowork"
CLIENT_ID = "pro-pizza-app"
CLIENT_SECRET = "5dUetKXdMULxjJHode8u64cpnhFwpk12"
REDIRECT_URI = "http://localhost:8099/auth/callback"
SPA_HOME = "http://localhost:3000/deliveries"

# Keycloak Endpoints
AUTH_URL = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_URL = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"
USERINFO_URL = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/userinfo"
LOGOUT_URL = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/logout"


# -------------------------------------------------------------
# 1️⃣ Step 1: User clicks login -> redirect to Keycloak
# -------------------------------------------------------------
# @csrf_exempt
@api_view(["GET"])
def login_redirect(request):
    print("api call")
    state = secrets.token_urlsafe(16)
    request.session['oauth_state'] = state

    auth_url = (
        f"{AUTH_URL}?"
        f"client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid profile email"
        f"&state={state}"
    )
    print(auth_url,"auth url")
    return redirect(auth_url)


# -------------------------------------------------------------
# 2️⃣ Step 2: Keycloak callback -> exchange code for tokens
# -------------------------------------------------------------

def callback_view(request):
    print("call back call")
    code = request.GET.get("code")
    state = request.GET.get("state")
    print("its call for code change",code,state)
    if not code:
        return HttpResponse("Missing authorization code", status=400)
    if request.session.get("oauth_state") != state:
        return HttpResponse("Invalid state", status=400)

    # Exchange code for tokens (server → Keycloak)
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    print(TOKEN_URL,data)
    token_resp = requests.post(TOKEN_URL, data=data)
    if token_resp.status_code != 200:
        return HttpResponse("Token exchange failed", status=token_resp.status_code)

    tokens = token_resp.json()
    print(token_resp.status_code)
    print(tokens,"tokens")
    tokens["expires_at"] = time.time() + int(tokens.get("expires_in", 300))

    # Optionally fetch user info
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    userinfo_resp = requests.get(USERINFO_URL, headers=headers)
    print(userinfo_resp.json(),"respe")
    userinfo = userinfo_resp.json() if userinfo_resp.status_code == 200 else {}

    # Store tokens + user in Django session
    request.session["tokens"] = tokens
    request.session["userinfo"] = userinfo

    # Redirect to SPA
    return redirect(SPA_HOME)


# -------------------------------------------------------------
# 3️⃣ Step 3: Auto token refresh helper
# -------------------------------------------------------------
def refresh_tokens_if_needed(request):
    tokens = request.session.get("tokens")
    if not tokens:
        return None

    now = time.time()
    # Check if access_token is near expiry (<60s remaining)
    if tokens.get("expires_at", 0) - now > 60:
        return tokens  # Still valid

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        request.session.flush()
        return None

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r = requests.post(TOKEN_URL, data=data)
    if r.status_code != 200:
        request.session.flush()
        return None

    new_tokens = r.json()
    new_tokens["expires_at"] = time.time() + int(new_tokens.get("expires_in", 300))
    request.session["tokens"] = new_tokens
    return new_tokens


# -------------------------------------------------------------
# 4️⃣ Step 4: SPA calls protected API (session-based)
# -------------------------------------------------------------
@require_GET
def profile_view(request):
    tokens = refresh_tokens_if_needed(request)
    if not tokens:
        return JsonResponse({"authenticated": False}, status=401)

    userinfo = request.session.get("userinfo")
    return JsonResponse({"authenticated": True, "user": userinfo})


# -------------------------------------------------------------
# 5️⃣ Step 5: Logout (revoke + clear session)
# -------------------------------------------------------------
@csrf_exempt
@api_view(["POST"])
def logout_view(request):
    tokens = request.session.get("tokens")
    if tokens:
        refresh_token = tokens.get("refresh_token")
        if refresh_token:
            data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
            }
            requests.post(LOGOUT_URL, data=data)

    request.session.flush()
    return Response({"message": "Logged out successfully"})
