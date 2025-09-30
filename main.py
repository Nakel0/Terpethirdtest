# main.py - COMPLETE WORKING VERSION
from flask import Flask, request, jsonify
import requests
import time
import base64
import os
from urllib.parse import unquote

app = Flask(__name__)

# Environment variables
ONCEAPI_USERNAME = os.getenv("ONCEAPI_USERNAME", "okunleyenakky@gmail.com")
ONCEAPI_PASSWORD = os.getenv("ONCEAPI_PASSWORD", "")

# Global token storage
access_token = None
token_expires_at = 0

def get_access_token():
    """Get or refresh the 1NCE access token using client_credentials"""
    global access_token, token_expires_at
    
    print(f"[AUTH] Starting authentication for user: {ONCEAPI_USERNAME}")
    print(f"[AUTH] Password present: {'YES' if ONCEAPI_PASSWORD else 'NO'}")
    
    # Check if token is still valid (5 minute buffer)
    if access_token and time.time() < (token_expires_at - 300):
        print("[AUTH] Using existing valid token")
        return access_token
    
    print("[AUTH] Getting new token from 1NCE...")
    
    # Encode credentials for Basic Auth
    credentials = base64.b64encode(f"{ONCEAPI_USERNAME}:{ONCEAPI_PASSWORD}".encode()).decode()
    print(f"[AUTH] Basic Auth credentials prepared for: {ONCEAPI_USERNAME}")
    
    # 1NCE OAuth endpoint
    token_url = "https://api.1nce.com/management-api/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {credentials}"
    }
    data = {
        "grant_type": "client_credentials"
    }
    
    try:
        print(f"[AUTH] POST {token_url}")
        print(f"[AUTH] Headers: Content-Type: application/x-www-form-urlencoded, Authorization: Basic ***")
        print(f"[AUTH] Data: grant_type=client_credentials")
        
        response = requests.post(token_url, headers=headers, data=data)
        
        print(f"[AUTH] Response Status: {response.status_code}")
        print(f"[AUTH] Response Body: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            token_expires_at = time.time() + expires_in
            
            if access_token:
                print(f"[AUTH] SUCCESS! Token obtained, expires in {expires_in} seconds")
                return access_token
            else:
                print("[AUTH] ERROR: No access_token in response")
                return None
        else:
            print(f"[AUTH] ERROR: HTTP {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"[AUTH] EXCEPTION: {str(e)}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with token validation"""
    print("[HEALTH] Health check requested")
    
    # Force token check
    token = get_access_token()
    token_valid = token is not None
    
    result = {
        "service": "1NCE SMS Middleware",
        "status": "healthy",
        "token_valid": token_valid,
        "username": ONCEAPI_USERNAME,
        "password_set": bool(ONCEAPI_PASSWORD),
        "timestamp": time.time()
    }
    
    if token_valid:
        result["token_expires_in"] = int(token_expires_at - time.time()) if token_expires_at else 0
    
    print(f"[HEALTH] Returning: {result}")
    return jsonify(result)

@app.route('/sms', methods=['POST', 'GET'])
def send_sms():
    """Send SMS via 1NCE API"""
    print("[SMS] SMS request received")
    
    # Get access token
    token = get_access_token()
    if not token:
        print("[SMS] ERROR: Failed to get access token")
        return jsonify({"error": "Authentication failed"}), 401
    
    # Extract parameters
    phone_number = unquote(request.args.get('to', ''))
    message = unquote(request.args.get('message', ''))
    
    print(f"[SMS] To: {phone_number}")
    print(f"[SMS] Message: {message}")
    
    if not phone_number or not message:
        return jsonify({"error": "Missing phone number or message"}), 400
    
    # 1NCE SMS endpoint
    iccid = "8988228066614198736"
    sms_url = f"https://api.1nce.com/management-api/v1/sims/{iccid}/sms"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "sourceAddress": "",
        "payload": message,
        "submitSm": {
            "destAddrNpi": 1,
            "destAddrTon": 1
        }
    }
    
    try:
        print(f"[SMS] Sending to 1NCE: {sms_url}")
        response = requests.post(sms_url, headers=headers, json=payload)
        
        print(f"[SMS] 1NCE Response: {response.status_code} - {response.text}")
        
        if response.status_code in [200, 201, 202]:
            return jsonify({
                "status": "success",
                "message": "SMS sent successfully",
                "to": phone_number,
                "text": message
            })
        else:
            return jsonify({
                "error": f"1NCE SMS API error: {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"[SMS] Exception: {str(e)}")
        return jsonify({"error": "SMS sending failed"}), 500

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        "service": "1NCE SMS Middleware v2.0",
        "status": "online",
        "endpoints": {
            "health": "/health - Check authentication status",
            "sms": "/sms?to=PHONE&message=MESSAGE - Send SMS"
        },
        "timestamp": time.time()
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify deployment"""
    return jsonify({
        "test": "DEPLOYMENT SUCCESSFUL",
        "username": ONCEAPI_USERNAME,
        "password_configured": bool(ONCEAPI_PASSWORD),
        "version": "2.0-FIXED"
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"Starting 1NCE SMS Middleware on port {port}")
    print(f"Username: {ONCEAPI_USERNAME}")
    print(f"Password configured: {'YES' if ONCEAPI_PASSWORD else 'NO'}")
    app.run(host='0.0.0.0', port=port)
