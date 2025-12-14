# import requests
# from django.conf import settings
# from django.shortcuts import redirect
# from django.http import JsonResponse, HttpResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_GET

# # === Keycloak Config ===
# KEYCLOAK_SERVER_URL = "http://localhost:8080"
# REALM = "master"
# CLIENT_ID = "pro-worker-client"
# CLIENT_SECRET = "V9fYcQLx1TtKfmnymD7cehS5WWKIxVmQ"
# REDIRECT_URI = "http://localhost:8099/auth/callback"


# # -------------------------
# # STEP 1: Login redirect
# # -------------------------
# def login_view(request):
#     """
#     Redirects user to Keycloak login page.
#     """
#     scope = "openid profile email"
#     auth_url = (
#         f"{KEYCLOAK_SERVER_URL}/realms/{REALM}/protocol/openid-connect/auth"
#         f"?client_id={CLIENT_ID}"
#         f"&redirect_uri={REDIRECT_URI}"
#         f"&response_type=code"
#         f"&scope={scope}"
#     )
#     return redirect(auth_url)


# # -------------------------
# # STEP 2: Callback from Keycloak
# # -------------------------
# @csrf_exempt
# def callback_view(request):
#     """
#     Handles Keycloak callback, exchanges the code for tokens, and stores session.
#     """
#     try:
#         code = request.GET.get("code")
#         if not code:
#             return HttpResponse("Missing 'code' parameter", status=400)
#         print("coming here to code",code)
#         token_url = f"{KEYCLOAK_SERVER_URL}/realms/{REALM}/protocol/openid-connect/token"
#         token_data = {
#             "grant_type": "authorization_code",
#             "code": code,
#             "redirect_uri": REDIRECT_URI,
#             "client_id": CLIENT_ID,
#             "client_secret": CLIENT_SECRET,
#         }

#         # Exchange code for tokens
#         token_response = requests.post(token_url, data=token_data)
#         print(token_response.status_code)
#         if token_response.status_code != 200:
#             print("Token exchange failed:", token_response.text)
#             return HttpResponse("Token exchange failed", status=502)

#         tokens = token_response.json()
#         # print(tokens,"tokens")
#         access_token = tokens.get("access_token")
#         refresh_token = tokens.get("refresh_token")

#         # Store tokens in session
#         request.session["tokens"] = tokens

#         # Fetch user info
#         userinfo_url = f"{KEYCLOAK_SERVER_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
#         headers = {"Authorization": f"Bearer {access_token}"}
#         userinfo = requests.get(userinfo_url, headers=headers).json()
#         print(userinfo,"user info")
#         request.session["userinfo"] = userinfo
#         print("✅ User logged in:", userinfo)

#         # Redirect to frontend
#         return redirect("http://localhost:3000/profile")

#     except Exception as e:
#         print("❌ Error in callback:", e)
#         return HttpResponse(f"Error in callback: {e}", status=500)


# # -------------------------
# # STEP 3: API endpoint to get profile
# # -------------------------
# @require_GET
# def profile_view(request):
#     """
#     Example endpoint to fetch user info (requires valid session).
#     """
#     tokens = request.session.get("tokens")
#     if not tokens:
#         return JsonResponse({"authenticated": False, "error": "No session found"}, status=401)

#     access_token = tokens.get("access_token")
#     userinfo_url = f"{KEYCLOAK_SERVER_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
#     headers = {"Authorization": f"Bearer {access_token}"}
#     userinfo_response = requests.get(userinfo_url, headers=headers)

#     if userinfo_response.status_code != 200:
#         return JsonResponse({"authenticated": False, "error": "Invalid token"}, status=401)

#     userinfo = userinfo_response.json()
#     return JsonResponse({"authenticated": True, "user": userinfo})



# from django.views.decorators.http import require_POST

# @require_POST
# def logout_view(request):
#     """Logs out user by clearing session"""
#     request.session.flush()
#     return JsonResponse({"message": "Logged out"})



import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import logout

KEYCLOAK_TOKEN_URL = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
KEYCLOAK_USERINFO_URL = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
CLIENT_ID = "pro-pizza-app"
CLIENT_SECRET = "5dUetKXdMULxjJHode8u64cpnhFwpk12"


@csrf_exempt
@api_view(["POST"])
def login_view(request):
    """Login via username/password using Keycloak Direct Access Grant"""
    try :
        data = request.POST
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return Response({"error": "Missing credentials"}, status=400)

        token_data = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": username,
            "password": password,
             "scope": "openid profile email"
        }

        print(token_data)
        token_resp = requests.post(KEYCLOAK_TOKEN_URL, data=token_data)
        # print(token_resp.json(),"token_resp")
        if token_resp.status_code != 200:
            return Response({"error": "Invalid credentials"}, status=401)
        print("pass")
        tokens = token_resp.json()
        access_token = tokens["access_token"]

        # Fetch user info
        headers = {"Authorization": f"Bearer {access_token}"}
        print("getting token",access_token)
        import jwt

        decoded = jwt.decode(access_token, options={"verify_signature": False})
        print("Access token audience:", decoded.get("aud"))
        print("Realm:", decoded.get("iss"))
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_resp = requests.get(KEYCLOAK_USERINFO_URL, headers=headers)

        print("Userinfo status:", userinfo_resp.status_code,KEYCLOAK_USERINFO_URL)
        print("Userinfo text:", userinfo_resp.text)

        userinfo = userinfo_resp.json()  # <-- keep this after printing

        print("set")
        # Save tokens in session
        request.session["tokens"] = tokens
        request.session["userinfo"] = userinfo

        return Response({
            "authenticated": True,
            "user": userinfo
        })

    except Exception as e :
        print("Eroror",e)
        return Response({"Errorr":str(e)},status=500)

@require_GET
def profile_view(request):
    """Return current logged in user info"""
    userinfo = request.session.get("userinfo")
    if not userinfo:
        return JsonResponse({"authenticated": False}, status=401)
    return JsonResponse({"authenticated": True, "user": userinfo})




@csrf_exempt
@api_view(["POST"])
def logout_view(request):
    """Logout user from Keycloak and clear Django session"""
    try:
        tokens = request.session.get("tokens")
        if not tokens:
            return Response({"message": "No active session found"}, status=200)

        refresh_token = tokens.get("refresh_token")

        # Call Keycloak token revocation endpoint
        revoke_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": refresh_token,
        }

        revoke_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
        resp = requests.post(revoke_url, data=revoke_data)

        # Clear Django session regardless of KC response
        request.session.flush()
        logout(request)

        if resp.status_code in [200, 204]:
            return Response({"message": "Logged out successfully"}, status=200)
        else:
            print("Keycloak logout failed:", resp.text)
            return Response(
                {"message": "Session cleared locally, but Keycloak logout failed"},
                status=200,
            )

    except Exception as e:
        print("Logout error:", e)
        return Response({"error": str(e)}, status=500)



KEYCLOAK_INTROSPECT_URL = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token/introspect"

@api_view(["POST"])
def introspect_token_view(request):
    """Validate access token with Keycloak introspect endpoint"""
    try:
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        data = {"token": token}
        auth = (CLIENT_ID, CLIENT_SECRET)  # client credentials

        resp = requests.post(KEYCLOAK_INTROSPECT_URL, data=data, auth=auth)

        if resp.status_code != 200:
            return Response({"error": "Failed to introspect token"}, status=resp.status_code)

        introspect_data = resp.json()

        if not introspect_data.get("active"):
            return Response({"active": False, "error": "Token inactive or expired"}, status=401)

        return Response({"active": True, "data": introspect_data})

    except Exception as e:
        return Response({"error": str(e)}, status=500)