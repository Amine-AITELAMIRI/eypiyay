#!/usr/bin/env python3
"""
Test script for ChatGPT Relay API
Usage: python test_api.py
"""

import requests
import time
import json
import sys
from typing import Dict, Any, Optional

# Configuration
API_URL = "https://chatgpt-relay-api.onrender.com"
API_KEY = "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"

class ChatGPTRelayTester:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
    
    def check_health(self) -> bool:
        """Check if the API is healthy"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def send_prompt(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Send a prompt and return the request data"""
        try:
            response = requests.post(
                f"{self.api_url}/requests",
                headers=self.headers,
                json={"prompt": prompt},
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Prompt submitted successfully!")
                print(f"   Request ID: {data['id']}")
                print(f"   Status: {data['status']}")
                print(f"   Prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
                return data
            else:
                print(f"❌ Failed to submit prompt: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Error submitting prompt: {e}")
            return None
    
    def get_request_status(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get the status of a request"""
        try:
            response = requests.get(
                f"{self.api_url}/requests/{request_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get request status: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Error getting request status: {e}")
            return None
    
    def wait_for_completion(self, request_id: int, max_wait_time: int = 300) -> Optional[Dict[str, Any]]:
        """Wait for a request to complete and return the final result"""
        print(f"⏳ Waiting for request {request_id} to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_data = self.get_request_status(request_id)
            if not status_data:
                return None
            
            status = status_data["status"]
            print(f"   Status: {status}")
            
            if status == "completed":
                print("✅ Request completed successfully!")
                return status_data
            elif status == "failed":
                print(f"❌ Request failed: {status_data.get('error', 'Unknown error')}")
                return status_data
            elif status in ["pending", "processing"]:
                time.sleep(5)  # Wait 5 seconds before checking again
            else:
                print(f"⚠️  Unknown status: {status}")
                time.sleep(5)
        
        print(f"⏰ Timeout after {max_wait_time} seconds")
        return None
    
    def parse_chatgpt_response(self, response_data: Dict[str, Any]) -> None:
        """Parse and display the ChatGPT response"""
        try:
            response_text = response_data.get("response", "")
            if response_text:
                chatgpt_data = json.loads(response_text)
                print("\n" + "="*60)
                print("🤖 CHATGPT RESPONSE")
                print("="*60)
                print(f"Prompt: {chatgpt_data.get('prompt', 'N/A')}")
                print(f"Response: {chatgpt_data.get('response', 'N/A')}")
                print(f"Timestamp: {chatgpt_data.get('timestamp', 'N/A')}")
                print(f"URL: {chatgpt_data.get('url', 'N/A')}")
                print("="*60)
            else:
                print("❌ No response data found")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse ChatGPT response: {e}")
            print(f"Raw response: {response_data.get('response', 'N/A')}")
    
    def test_single_prompt(self, prompt: str) -> bool:
        """Test a single prompt end-to-end"""
        print(f"\n🧪 Testing prompt: '{prompt[:50]}{'...' if len(prompt) > 50 else ''}'")
        print("-" * 60)
        
        # Submit prompt
        request_data = self.send_prompt(prompt)
        if not request_data:
            return False
        
        # Wait for completion
        final_data = self.wait_for_completion(request_data["id"])
        if not final_data:
            return False
        
        # Parse and display response
        if final_data["status"] == "completed":
            self.parse_chatgpt_response(final_data)
            return True
        else:
            return False
    
    def run_test_suite(self):
        """Run a comprehensive test suite"""
        print("🚀 Starting ChatGPT Relay API Test Suite")
        print("=" * 60)
        
        # Health check
        if not self.check_health():
            print("❌ Health check failed. Exiting.")
            return
        
        # Test prompts
        test_prompts = [
            "Write a haiku about artificial intelligence",
            "Explain quantum computing in simple terms",
            "What are the benefits of renewable energy?",
            "Write a short story about a robot learning to paint",
            "List 5 interesting facts about space"
        ]
        
        successful_tests = 0
        total_tests = len(test_prompts)
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n📝 Test {i}/{total_tests}")
            if self.test_single_prompt(prompt):
                successful_tests += 1
                print("✅ Test passed")
            else:
                print("❌ Test failed")
            
            # Wait between tests to avoid overwhelming the system
            if i < total_tests:
                print("⏳ Waiting 10 seconds before next test...")
                time.sleep(10)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if successful_tests == total_tests:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")

def main():
    """Main function"""
    print("ChatGPT Relay API Tester")
    print("=" * 40)
    
    # Initialize tester
    tester = ChatGPTRelayTester(API_URL, API_KEY)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--health":
            tester.check_health()
        elif sys.argv[1] == "--prompt" and len(sys.argv) > 2:
            prompt = " ".join(sys.argv[2:])
            tester.test_single_prompt(prompt)
        else:
            print("Usage:")
            print("  python test_api.py                    # Run full test suite")
            print("  python test_api.py --health           # Check API health")
            print("  python test_api.py --prompt 'text'    # Test single prompt")
    else:
        # Run full test suite
        tester.run_test_suite()

if __name__ == "__main__":
    main()
