import time
import random
import json
from scraper import UniversalScraper

OUTPUT_FILE = "stream_buffer.jsonl"
TARGET_URLS = [
    "https://googleprojectzero.blogspot.com/",
    "https://www.exploit-db.com/rss.xml",
    "https://packetstormsecurity.com/",
    "https://lwn.net/Kernel/",
    "https://kernelnewbies.org/LinuxChanges",
    "https://grsecurity.net/blog",
    "https://www.openwall.com/lists/oss-security/",
    "https://research.checkpoint.com/",
    "https://vx-underground.org/",
    "https://hex-rays.com/blog/",
    "https://news.ycombinator.com",
    "https://www.reddit.com/r/netsec/",
    "https://www.reddit.com/r/kernel/",
    "https://github.com/trending/c?since=daily",
    "https://github.com/trending/rust?since=daily"
]

def run_producer():
    print(f"[Producer] writing to {OUTPUT_FILE}...")
    
    while True:
        url = random.choice(TARGET_URLS)
        try:
            print(f"[Producer] Scraping {url}...")
            scraper = UniversalScraper(url, js=False) # Keep it fast
            data = scraper.scrape()
            
            # Atomic Append to file (simulates a stream)
            with open(OUTPUT_FILE, "a") as f:
                json.dump(data, f)
                f.write("\n")
                
            print(f"[Producer] Appended {len(data['full_text'])} chars.")
        except Exception as e:
            print(f"[Producer] Error: {e}")

        time.sleep(5)

if __name__ == "__main__":
    run_producer()
