#!/usr/bin/env python3
"""
ChatGPT Data Extractor via Firefox DevTools Protocol

This script connects to a running Firefox instance with remote debugging enabled
and extracts localStorage data saved by the ChatGPT bookmarklet.

Usage:
1. Launch Firefox with: firefox --start-debugger-server=9222
2. Run this script: python chatgpt_data_extractor.py
"""

import json
import websocket
import requests
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
import csv
import os


class FirefoxDevToolsClient:
    """Client for interacting with Firefox DevTools Protocol"""
    
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self.base_url = f"http://localhost:{debug_port}"
        self.ws_url = None
        self.ws = None
        self.message_id = 0
        self.responses = {}
        self.response_event = threading.Event()
        
    def get_tabs(self) -> List[Dict]:
        """Get list of all open tabs"""
        try:
            # Firefox uses /json/list endpoint
            response = requests.get(f"{self.base_url}/json/list")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching tabs: {e}")
            return []
    
    def find_chatgpt_tab(self) -> Optional[Dict]:
        """Find the ChatGPT tab"""
        tabs = self.get_tabs()
        for tab in tabs:
            url = tab.get('url', '')
            if 'chat.openai.com' in url or 'chatgpt.com' in url:
                return tab
        return None
    
    def connect_to_tab(self, tab: Dict) -> bool:
        """Connect to a specific tab via WebSocket"""
        # Firefox uses 'webSocketURL' instead of 'webSocketDebuggerUrl'
        self.ws_url = tab.get('webSocketURL') or tab.get('webSocketDebuggerUrl')
        if not self.ws_url:
            print("No WebSocket URL found for tab")
            return False
            
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start WebSocket in a separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error connecting to tab: {e}")
            return False
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_id = data.get('id')
            if message_id in self.responses:
                self.responses[message_id] = data
                self.response_event.set()
        except json.JSONDecodeError:
            pass
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        print("WebSocket connection closed")
    
    def send_command(self, method: str, params: Dict = None) -> Optional[Dict]:
        """Send a command to Firefox DevTools"""
        if not self.ws:
            print("Not connected to Firefox")
            return None
            
        self.message_id += 1
        command = {
            "id": self.message_id,
            "method": method,
            "params": params or {}
        }
        
        self.responses[self.message_id] = None
        self.response_event.clear()
        
        try:
            self.ws.send(json.dumps(command))
            
            # Wait for response with timeout
            if self.response_event.wait(timeout=10):
                response = self.responses.get(self.message_id)
                if response and 'error' in response:
                    print(f"Command error: {response['error']}")
                    return None
                return response
            else:
                print("Command timeout")
                return None
                
        except Exception as e:
            print(f"Error sending command: {e}")
            return None
    
    def enable_runtime(self) -> bool:
        """Enable Runtime domain"""
        response = self.send_command("Runtime.enable")
        return response is not None
    
    def evaluate_javascript(self, expression: str) -> Optional[Any]:
        """Execute JavaScript in the page context"""
        response = self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True
        })
        
        if response and 'result' in response:
            result = response['result']
            if result.get('exceptionDetails'):
                print(f"JavaScript error: {result['exceptionDetails']}")
                return None
            return result.get('value')
        
        return None
    
    def get_localstorage_data(self) -> Optional[Dict]:
        """Get all localStorage data"""
        js_code = """
        Object.fromEntries(
            Object.keys(localStorage).map(key => [key, localStorage.getItem(key)])
        )
        """
        return self.evaluate_javascript(js_code)
    
    def close(self):
        """Close the WebSocket connection"""
        if self.ws:
            self.ws.close()


class ChatGPTDataExtractor:
    """Extract and process ChatGPT data from localStorage"""
    
    def __init__(self, debug_port: int = 9222):
        self.client = FirefoxDevToolsClient(debug_port)
        self.chatgpt_data = []
        
    def connect(self) -> bool:
        """Connect to ChatGPT tab"""
        print("🔍 Looking for ChatGPT tab...")
        tab = self.client.find_chatgpt_tab()
        
        if not tab:
            print("❌ No ChatGPT tab found. Make sure ChatGPT is open in Firefox.")
            return False
        
        print(f"✅ Found ChatGPT tab: {tab.get('title', 'Unknown')}")
        print(f"   URL: {tab.get('url', 'Unknown')}")
        
        if not self.client.connect_to_tab(tab):
            print("❌ Failed to connect to tab")
            return False
        
        if not self.client.enable_runtime():
            print("❌ Failed to enable Runtime domain")
            return False
        
        print("✅ Connected to ChatGPT tab")
        return True
    
    def extract_data(self) -> List[Dict]:
        """Extract ChatGPT data from localStorage"""
        print("📊 Extracting localStorage data...")
        
        localstorage_data = self.client.get_localstorage_data()
        if not localstorage_data:
            print("❌ Failed to read localStorage")
            return []
        
        print(f"📁 Found {len(localstorage_data)} localStorage entries")
        
        # Filter for ChatGPT response files
        chatgpt_files = []
        for key, value in localstorage_data.items():
            if key.startswith('chatgpt-response-') and key.endswith('.json'):
                try:
                    data = json.loads(value)
                    chatgpt_files.append(data)
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON in {key}")
        
        # Also check for the file list
        file_list_key = 'chatgpt-files'
        if file_list_key in localstorage_data:
            try:
                file_list = json.loads(localstorage_data[file_list_key])
                print(f"📋 File list contains {len(file_list)} entries")
            except json.JSONDecodeError:
                print("⚠️  Invalid file list JSON")
        
        self.chatgpt_data = chatgpt_files
        print(f"✅ Extracted {len(chatgpt_files)} ChatGPT responses")
        return chatgpt_files
    
    def display_data(self):
        """Display extracted data in a readable format"""
        if not self.chatgpt_data:
            print("📭 No ChatGPT data found")
            return
        
        print(f"\n📊 Found {len(self.chatgpt_data)} ChatGPT responses:")
        print("=" * 80)
        
        for i, data in enumerate(self.chatgpt_data, 1):
            print(f"\n📝 Response #{i}")
            print(f"   🕒 Time: {data.get('timestamp', 'Unknown')}")
            print(f"   🌐 URL: {data.get('url', 'Unknown')}")
            print(f"   ❓ Prompt: {data.get('prompt', 'Unknown')[:100]}{'...' if len(data.get('prompt', '')) > 100 else ''}")
            print(f"   💬 Response: {data.get('response', 'Unknown')[:200]}{'...' if len(data.get('response', '')) > 200 else ''}")
            print("-" * 40)
    
    def export_json(self, filename: str = None):
        """Export data to JSON file"""
        if not self.chatgpt_data:
            print("📭 No data to export")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chatgpt_responses_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.chatgpt_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Data exported to {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def export_csv(self, filename: str = None):
        """Export data to CSV file"""
        if not self.chatgpt_data:
            print("📭 No data to export")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chatgpt_responses_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'URL', 'Prompt', 'Response'])
                
                for data in self.chatgpt_data:
                    writer.writerow([
                        data.get('timestamp', ''),
                        data.get('url', ''),
                        data.get('prompt', ''),
                        data.get('response', '')
                    ])
            print(f"✅ Data exported to {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        self.client.close()


def main():
    parser = argparse.ArgumentParser(description='Extract ChatGPT data via Firefox DevTools Protocol')
    parser.add_argument('--port', type=int, default=9222, help='Firefox debug port (default: 9222)')
    parser.add_argument('--export-json', help='Export to JSON file')
    parser.add_argument('--export-csv', help='Export to CSV file')
    parser.add_argument('--quiet', action='store_true', help='Suppress output except errors')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🚀 ChatGPT Data Extractor (Firefox)")
        print("=" * 50)
        print("Make sure Firefox is running with:")
        print("firefox --start-debugger-server=9222")
        print()
    
    extractor = ChatGPTDataExtractor(args.port)
    
    try:
        if not extractor.connect():
            return 1
        
        data = extractor.extract_data()
        
        if not args.quiet:
            extractor.display_data()
        
        # Export options
        if args.export_json:
            extractor.export_json(args.export_json)
        elif args.export_csv:
            extractor.export_csv(args.export_csv)
        elif not args.quiet and data:
            print(f"\n💡 Use --export-json or --export-csv to save data to files")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    finally:
        extractor.cleanup()


if __name__ == "__main__":
    exit(main())
