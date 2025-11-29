import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import re
import time
import json
from typing import List, Dict

# import socket
# class StreamSocket:
#     """
#     A low-level wrapper around a TCP socket to handle
#     connection retries and data transmission.
#     """
#     def __init__(self, host: str = "127.0.0.1", port: int = 9999):
#         self.host = host
#         self.port = port
#         self.sock = None
#         self.connect()
#
#     def connect(self):
#         """Attempts to connect to the Pathway listener with exponential backoff."""
#         while True:
#             try:
#                 # AF_INET = IPv4, SOCK_STREAM = TCP
#                 self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 self.sock.connect((self.host, self.port))
#                 print(f"[Socket] Connected to {self.host}:{self.port}")
#                 return
#             except ConnectionRefusedError:
#                 print(f"[Socket] Connection failed. Retrying in 2s...")
#                 time.sleep(2)
#
#     def send_entry(self, data: dict):
#         """
#         Serializes dict to JSON and sends it over the wire.
#         Adds a newline delimiter because TCP is a stream, not packet-based.
#         """
#         if not self.sock:
#             self.connect()
#         
#         assert self.sock is not None
#         try:
#             # json.dumps returns a string. encode() turns it into bytes (UTF-8).
#             # We add \n so the receiver knows where one message ends.
#             payload = (json.dumps(data) + "\n").encode('utf-8')
#             self.sock.sendall(payload)
#         except (BrokenPipeError, ConnectionResetError):
#             print("[Socket] Broken pipe. Reconnecting...")
#             self.connect()
#             # Retry sending once after reconnect
#             self.send_entry(data)

class UniversalScraper:
    def __init__(self, url: str, js: bool = False, timeout: int = 15000) -> None:
        self.url = url
        self.js = js
        self.timeout = timeout
        self.html = None
        self.soup = None
        self.result = {
            "url": url,
            "timestamp": time.time(),
            "source_type": "web_scrape" # Tagging the data for the RAG engine
        }

    def fetch_html(self) -> None:
        if not self.js:
            print(f"[+] Fetching {self.url} with requests...")
            r = requests.get(self.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            r.raise_for_status()
            self.html = r.text
            return

        print(f"[+] Fetching {self.url} with Playwright (JS Mode)...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0")
            page = context.new_page()
            page.goto(self.url, timeout=self.timeout)
            time.sleep(2)
            self.html = page.content()
            browser.close()

    def parse(self) -> None:
        if self.html is None:
            raise ValueError("HTML content is empty. Call fetch_html() first.")
        self.soup = BeautifulSoup(self.html, "lxml")

    def extract_text(self) -> None:
        if self.soup is None: return 
        text = self.soup.get_text(separator="\n")
        self.result["full_text"] = re.sub(r"\n\s*\n", "\n", text).strip()

    def extract_headings(self) -> None:
        if self.soup is None: return
        headings: Dict[str, List[str]] = {}
        for level in range(1, 7):
            tag = f"h{level}"
            headings[tag] = [h.get_text(strip=True) for h in self.soup.find_all(tag)]
        self.result["headings"] = headings

    def extract_links(self) -> None:
        if self.soup is None: return
        base = self.url
        links: List[str] = []
        for a in self.soup.find_all("a", href=True):
            href = a.get("href")
            if isinstance(href, (str, list)):
                clean_href = href[0] if isinstance(href, list) else href
                links.append(urljoin(base, clean_href))
        self.result["links"] = list(set(links))

    def extract_assets(self) -> None:
        if self.soup is None: return
        base = self.url
        def get_asset_urls(tag_name: str, attr_name: str) -> List[str]:
            if self.soup is None: return []
            urls = []
            for item in self.soup.find_all(tag_name, attrs={attr_name: True}):
                if isinstance(item, Tag):
                    val = item.get(attr_name)
                    if isinstance(val, (str, list)):
                        clean_val = val[0] if isinstance(val, list) else val
                        urls.append(urljoin(base, clean_val))
            return urls
        self.result["images"] = get_asset_urls("img", "src")
        self.result["scripts"] = get_asset_urls("script", "src")
        self.result["stylesheets"] = get_asset_urls("link", "href")

    def extract_metadata(self) -> None:
        if self.soup is None: return
        meta_data: Dict[str, str] = {}
        for m in self.soup.find_all("meta"):
            name = m.get("name")
            prop = m.get("property")
            content = m.get("content", "")
            content_str = str(content[0]) if isinstance(content, list) else str(content)
            if isinstance(name, str): meta_data[name] = content_str
            if isinstance(prop, str): meta_data[prop] = content_str
        
        title_tag = self.soup.title
        self.result["meta"] = meta_data
        # Ensure title is a flat string for Pathway schema simplicity
        self.result["page_title"] = str(title_tag.string) if title_tag and title_tag.string else ""

    def scrape(self) -> dict:
        self.fetch_html()
        self.parse()
        self.extract_text()
        self.extract_headings()
        self.extract_links()
        self.extract_assets()
        self.extract_metadata()
        return self.result

    def save_to_stream(self, filename: str = "stream_data.jsonl"):
        """Appends the result to a JSONL file to simulate a stream."""
        with open(filename, "a", encoding="utf-8") as f:
            json.dump(self.result, f)
            f.write("\n")
