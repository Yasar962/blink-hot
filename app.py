import os
import time
import re
import threading
import requests
from flask import Flask

app = Flask(__name__)

# --- CONFIGURATION ---
# Use Environment Variables for security on Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LAT = os.getenv("LAT", "28.5355")
LON = os.getenv("LON", "77.3910")

PRODUCT_URLS = [
    "https://blinkit.com/prn/hot-wheels-ferrari-sf90-stradale-die-cast-car/prid/717157",
    "https://blinkit.com/prn/hot-wheels-worldwide-basic-ferrari-12cilindri-toy-car/prid/746635"
]

class BlinkitMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "lat": LAT,
            "lon": LON,
            "app_client": "1"
        })
        self.found_items = set()

    def send_telegram(self, message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        self.session.post(url, data={"chat_id": CHAT_ID, "text": message})

    def run(self):
        while True:
            for url in PRODUCT_URLS:
                pid = re.search(r"prid/(\d+)", url).group(1)
                if pid in self.found_items: continue
                
                try:
                    res = self.session.get(f"https://blinkit.com/v1/products/{pid}", timeout=10)
                    if res.status_code == 200:
                        data = res.json().get('product', {})
                        if data.get('inventory', {}).get('stock', 0) > 0:
                            self.send_telegram(f"🏎️ HOT WHEELS FOUND!\n{data.get('name')}\n{url}")
                            self.found_items.add(pid)
                except Exception as e:
                    print(f"Error: {e}")
                time.sleep(5) # Gap between items
            time.sleep(300) # Wait 5 mins before next full check

# --- FLASK ROUTES ---
@app.route('/')
def health_check():
    return "Bot is alive!", 200

# --- BACKGROUND THREAD ---
monitor = BlinkitMonitor()
threading.Thread(target=monitor.run, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
