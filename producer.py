import time
import random
import json
from scraper import UniversalScraper

OUTPUT_FILE = "stream_buffer.jsonl"
TARGET_URLS = [
    "https://googleprojectzero.blogspot.com/",      # Deepest vulnerability research
    "https://www.exploit-db.com/rss.xml",           # Raw exploits (RSS usually easier, but main site works)
    "https://packetstormsecurity.com/",             # The old school archive
    "https://lwn.net/Kernel/",                      # The Bible of Linux Kernel news
    "https://kernelnewbies.org/LinuxChanges",       # Changelogs for new kernels
    "https://grsecurity.net/blog",                  # Hardened Linux security
    "https://www.openwall.com/lists/oss-security/", # Where 0-days are often disclosed first
    "https://research.checkpoint.com/",             # Deep malware analysis
    "https://vx-underground.org/",                  # Malware source code & papers
    "https://hex-rays.com/blog/",                   # IDA Pro devs blog
    "https://news.ycombinator.com",                 # Still useful for breaking tech discussion
    "https://www.reddit.com/r/netsec/",             # High signal security news
    "https://www.reddit.com/r/kernel/",             # Kernel specific discussion
    "https://github.com/trending/c?since=daily",    # What C projects are hot?
    "https://github.com/trending/rust?since=daily"  # What Rust projects are hot?
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
