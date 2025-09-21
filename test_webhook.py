#!/usr/bin/env python3
"""
Test script for ChatGPT Relay API with webhook support
Usage: python test_webhook.py
"""

import requests
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys

# Configuration
API_URL = "https://chatgpt-relay-api.onrender.com"
API_KEY = "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"

# Global variable to store received webhook
received_webhook = None
webhook_received = threading.Event()


class WebhookHandler(BaseHTTPRequestHandler):
    """Simple HTTP server to receive webhook notifications"""
    
    def do_POST(self):
        global received_webhook, webhook_received
        
        # Read the request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            webhook_data = json.loads(post_data.decode('utf-8'))
            received_webhook = webhook_data
            
            print(f"\n🎉 WEBHOOK RECEIVED!")
            print(f"Request ID: {webhook_data.get('request_id')}")
            print(f"Status: {webhook_data.get('status')}")
            print(f"Prompt: {webhook_data.get('prompt')}")
            
            if webhook_data.get('status') == 'completed':
                print(f"Response: {webhook_data.get('response', 'N/A')}")
            elif webhook_data.get('status') == 'failed':
                print(f"Error: {webhook_data.get('error', 'N/A')}")
            
            print(f"Timestamp: {webhook_data.get('timestamp')}")
            print("-" * 50)
            
            # Signal that webhook was received
            webhook_received.set()
            
        except json.JSONDecodeError as e:
            print(f"Error parsing webhook JSON: {e}")
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "received"}')
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass


def start_webhook_server(port=8080):
    """Start a simple webhook server"""
    server = HTTPServer(('localhost', port), WebhookHandler)
    print(f"🌐 Webhook server started on http://localhost:{port}")
    return server


def test_webhook_functionality():
    """Test the webhook functionality"""
    print("🚀 Testing ChatGPT Relay API with Webhook Support")
    print("=" * 60)
    
    # Start webhook server
    webhook_server = start_webhook_server()
    webhook_url = "http://localhost:8080/webhook"
    
    # Start server in background thread
    server_thread = threading.Thread(target=webhook_server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # Test 1: Submit request with webhook
        print("\n📝 Test 1: Submitting request with webhook URL")
        print("-" * 40)
        
        payload = {
            "prompt": "Write a short haiku about webhooks",
            "webhook_url": webhook_url
        }
        
        response = requests.post(
            f"{API_URL}/requests",
            headers={"X-API-Key": API_KEY},
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            request_data = response.json()
            request_id = request_data["id"]
            print(f"✅ Request submitted successfully!")
            print(f"   Request ID: {request_id}")
            print(f"   Status: {request_data['status']}")
            print(f"   Webhook URL: {request_data['webhook_url']}")
            print(f"   Webhook Delivered: {request_data['webhook_delivered']}")
        else:
            print(f"❌ Failed to submit request: {response.status_code} - {response.text}")
            return
        
        # Test 2: Wait for webhook
        print(f"\n⏳ Test 2: Waiting for webhook notification...")
        print("-" * 40)
        
        # Wait up to 2 minutes for webhook
        if webhook_received.wait(timeout=120):
            print("✅ Webhook received successfully!")
            
            # Verify webhook data
            if received_webhook:
                if received_webhook.get('request_id') == request_id:
                    print("✅ Webhook contains correct request ID")
                else:
                    print(f"❌ Webhook request ID mismatch: {received_webhook.get('request_id')} != {request_id}")
                
                if received_webhook.get('status') in ['completed', 'failed']:
                    print("✅ Webhook contains final status")
                else:
                    print(f"❌ Webhook status not final: {received_webhook.get('status')}")
        else:
            print("❌ Webhook not received within timeout period")
        
        # Test 3: Check request status
        print(f"\n🔍 Test 3: Checking final request status...")
        print("-" * 40)
        
        status_response = requests.get(
            f"{API_URL}/requests/{request_id}",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        if status_response.status_code == 200:
            final_data = status_response.json()
            print(f"✅ Final status retrieved!")
            print(f"   Status: {final_data['status']}")
            print(f"   Webhook Delivered: {final_data['webhook_delivered']}")
            
            if final_data['status'] == 'completed':
                print(f"   Response: {final_data.get('response', 'N/A')[:100]}...")
            elif final_data['status'] == 'failed':
                print(f"   Error: {final_data.get('error', 'N/A')}")
        else:
            print(f"❌ Failed to get final status: {status_response.status_code}")
        
        # Test 4: Test without webhook (polling)
        print(f"\n📝 Test 4: Testing without webhook (polling)...")
        print("-" * 40)
        
        payload_no_webhook = {
            "prompt": "Write a limerick about APIs"
        }
        
        response2 = requests.post(
            f"{API_URL}/requests",
            headers={"X-API-Key": API_KEY},
            json=payload_no_webhook,
            timeout=10
        )
        
        if response2.status_code == 201:
            request_data2 = response2.json()
            request_id2 = request_data2["id"]
            print(f"✅ Request submitted (no webhook)!")
            print(f"   Request ID: {request_id2}")
            print(f"   Webhook URL: {request_data2.get('webhook_url', 'None')}")
            
            # Poll for completion
            print("   Polling for completion...")
            for i in range(24):  # Poll for up to 2 minutes
                time.sleep(5)
                status_response = requests.get(
                    f"{API_URL}/requests/{request_id2}",
                    headers={"X-API-Key": API_KEY},
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    data = status_response.json()
                    if data['status'] in ['completed', 'failed']:
                        print(f"✅ Request completed via polling!")
                        print(f"   Status: {data['status']}")
                        break
                    else:
                        print(f"   Status: {data['status']} (polling...)")
                else:
                    print(f"❌ Polling failed: {status_response.status_code}")
                    break
            else:
                print("❌ Polling timeout")
        else:
            print(f"❌ Failed to submit request: {response2.status_code}")
    
    finally:
        # Clean up
        webhook_server.shutdown()
        print(f"\n🧹 Webhook server stopped")


def test_webhook_validation():
    """Test webhook URL validation"""
    print("\n🔍 Testing webhook URL validation...")
    print("-" * 40)
    
    # Test invalid webhook URL
    invalid_payload = {
        "prompt": "Test prompt",
        "webhook_url": "not-a-valid-url"
    }
    
    response = requests.post(
        f"{API_URL}/requests",
        headers={"X-API-Key": API_KEY},
        json=invalid_payload,
        timeout=10
    )
    
    if response.status_code == 422:
        print("✅ Invalid webhook URL properly rejected")
        print(f"   Error: {response.json()}")
    else:
        print(f"❌ Invalid webhook URL not rejected: {response.status_code}")


def main():
    """Main function"""
    print("ChatGPT Relay API Webhook Tester")
    print("=" * 40)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--validation":
            test_webhook_validation()
        else:
            print("Usage:")
            print("  python test_webhook.py              # Run webhook tests")
            print("  python test_webhook.py --validation # Test webhook validation")
    else:
        # Run webhook functionality test
        test_webhook_functionality()


if __name__ == "__main__":
    main()
