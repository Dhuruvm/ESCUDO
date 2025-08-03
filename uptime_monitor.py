
import requests
import time
import threading
import os

class UptimeMonitor:
    def __init__(self, url=None, interval=300):  # 5 minutes default
        self.url = url or "https://your-repl-name.your-username.repl.co/ping"
        self.interval = interval
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the uptime monitoring"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor, daemon=True)
            self.thread.start()
            print(f"🔄 Uptime monitor started - pinging every {self.interval} seconds")
    
    def stop(self):
        """Stop the uptime monitoring"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("⏹️ Uptime monitor stopped")
    
    def _monitor(self):
        """Internal monitoring loop"""
        while self.running:
            try:
                response = requests.get(self.url, timeout=30)
                if response.status_code == 200:
                    print(f"✅ Keep-alive ping successful at {time.strftime('%H:%M:%S')}")
                else:
                    print(f"⚠️ Keep-alive ping returned status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Keep-alive ping failed: {e}")
            except Exception as e:
                print(f"❌ Unexpected error in keep-alive: {e}")
            
            # Wait for the next ping
            time.sleep(self.interval)

# Auto-start the monitor if this file is run directly
if __name__ == "__main__":
    monitor = UptimeMonitor()
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
