import os
import glob
import csv
import requests
import datetime
import ollama
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container, Horizontal
from textual.widgets import Header, Footer, Input, Static, Markdown, DataTable
from textual import work

# --- CONFIGURATION ---
RAG_ENDPOINT = "http://localhost:9000/v1/retrieve"
OLLAMA_HOST = "http://localhost:11434"
LLM_MODEL = "phi3"
ALERTS_PATH = "live_alerts.csv" 

# --- WIDGETS ---

class ChatMessage(Container):
    def __init__(self, text: str, sender: str, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.sender = sender
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.header = f"{sender} • {time_str}"
        
        self.add_class("message-container")
        if sender == "You":
            self.add_class("user-message")
        else:
            self.add_class("ai-message")

    def compose(self) -> ComposeResult:
        yield Static(self.header, classes="message-header")
        yield Markdown(self.text, classes="message-body")

class SecurityDashboard(App):
    CSS = """
    Screen { layout: vertical; background: #0d1117; }
    Header { background: #161b22; color: #58a6ff; dock: top; }
    Footer { background: #161b22; dock: bottom; }
    
    /* LAYOUT */
    #main-layout {
        height: 1fr;
        width: 100%;
    }
    
    #chat-section {
        width: 70%;
        height: 100%;
        border-right: solid #30363d;
    }
    
    #alert-section {
        width: 30%;
        height: 100%;
        background: #0d1117;
    }

    /* INPUT */
    #input-container {
        dock: bottom;
        height: auto;
        padding: 1 2;
        background: #0d1117;
        border-top: solid #30363d;
    }
    Input {
        background: #0d1117;
        border: solid #30363d;
        color: #c9d1d9;
    }
    Input:focus { border: solid #58a6ff; }

    /* CHAT */
    #chat-scroll {
        height: 1fr;
        padding: 1;
        overflow-y: scroll; 
    }
    
    .message-container {
        margin-bottom: 2;
        padding: 1;
        width: 100%;
        height: auto;
    }
    .message-header { color: #8b949e; text-style: bold; margin-bottom: 1; }
    .user-message { background: #161b22; border-left: solid #58a6ff; }
    .ai-message { background: #0d1117; border-left: solid #238636; }
    .message-body { color: #c9d1d9; }
    
    /* STATUS INDICATOR */
    .status-text {
        color: #e3b341;
        text-style: italic;
        margin: 1;
        padding-left: 1;
    }

    /* ALERTS TABLE */
    DataTable {
        background: #0d1117;
        color: #c9d1d9;
        height: 1fr;
        border: none;
    }
    
    /* NEW: Correct class for the right-pane header */
    .section-header {
        text-align: center; 
        padding: 1; 
        background: #161b22;
        color: #8b949e; 
        text-style: bold;
    }
    """

    TITLE = "KERNEL PANIC DASHBOARD"
    SUB_TITLE = "Live Intelligence Stream"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="main-layout"):
            # LEFT: Chat
            with VerticalScroll(id="chat-section"):
                yield VerticalScroll(id="chat-scroll")
            
            # RIGHT: Alerts
            with Container(id="alert-section"):
                # FIXED: Removed 'style' arg, used 'classes' instead
                yield Static(" 🚨 THREAT MONITOR", classes="section-header")
                yield DataTable(id="alerts-table", zebra_stripes=True)

        with Container(id="input-container"):
            yield Input(placeholder="COMMAND >> (e.g. 'new linux heap exploits')")
        
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Input).focus()
        
        welcome = ChatMessage(
            f"**UPLINK ESTABLISHED.**\nPipeline: `{RAG_ENDPOINT}`\nModel: `{LLM_MODEL}`", 
            "SYSTEM"
        )
        self.query_one("#chat-scroll").mount(welcome)

        table = self.query_one(DataTable)
        table.add_columns("THREAT", "COUNT")
        
        self.set_interval(2.0, self.update_alerts)

    def update_alerts(self):
        """Reads CSV and Aggregates counts by Threat Name."""
        table = self.query_one(DataTable)
        
        files = []
        if os.path.isdir(ALERTS_PATH):
            files = glob.glob(os.path.join(ALERTS_PATH, "*.csv"))
        elif os.path.isfile(ALERTS_PATH):
            files = [ALERTS_PATH]
        
        if not files:
            return

        # Use a Dictionary to aggregate duplicates
        # Format: {"threat_name": total_count}
        threat_map = {}

        for file in files:
            try:
                with open(file, "r") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) < 3: continue
                        
                        raw_word = row[0]
                        raw_count = row[1]
                        
                        # Data Validation
                        if raw_word and raw_count.replace('.', '', 1).isdigit():
                            # 1. Normalize Case (Kernel -> kernel)
                            clean_word = raw_word.lower()
                            
                            # 2. Accumulate Counts instead of appending rows
                            current_total = threat_map.get(clean_word, 0)
                            threat_map[clean_word] = current_total + int(float(raw_count))
            except Exception:
                pass

        # Convert Dict back to List for sorting
        alerts = [(word, count) for word, count in threat_map.items()]

        # Sort by Count DESC
        alerts.sort(key=lambda x: x[1], reverse=True)
        
        table.clear()
        if not alerts:
             table.add_row("Scanning...", "0")
        else:
            for word, count in alerts[:20]:
                # Color Styling
                if count > 100:
                    styled_word = f"[bold red]{word.upper()}[/]"
                elif count > 20:
                    styled_word = f"[bold yellow]{word}[/]"
                else:
                    styled_word = word
                
                table.add_row(styled_word, str(count))

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        query = message.value.strip()
        if not query: return
        message.input.value = ""

        scroll = self.query_one("#chat-scroll")
        
        await scroll.mount(ChatMessage(query, "You"))
        scroll.scroll_end(animate=False)

        self.status = Static(" ⚡ Analyzing neural stream...", classes="status-text")
        await scroll.mount(self.status)
        scroll.scroll_end()
        
        self.process_query(query)

    @work(exclusive=True, thread=True)
    def process_query(self, query: str):
        try:
            payload = {"query": query, "k": 3}
            try:
                rag_resp = requests.post(RAG_ENDPOINT, json=payload, timeout=5)
                rag_resp.raise_for_status()
                docs = rag_resp.json()
            except:
                docs = []

            context_blocks = []
            source_links = []
            if docs:
                for idx, item in enumerate(docs):
                    meta = item.get("metadata", {})
                    text = item.get("text", "")[:300].replace("\n", " ")
                    title = meta.get("title", "Unknown")
                    url = meta.get("url", "#")
                    
                    context_blocks.append(f"REPORT {idx+1}: {text}")
                    source_links.append(f"{idx+1}. [{title}]({url})")

            context = "\n".join(context_blocks) if context_blocks else "NO SIGNAL"
            
            sys_msg = "You are a security analyst. Use the REPORTS to answer. Be brief."
            prompt = f"REPORTS:\n{context}\n\nQUERY: {query}"
            
            client = ollama.Client(host=OLLAMA_HOST)
            stream = client.chat(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt}
                ]
            )
            response = stream["message"]["content"]
            
            if source_links:
                response += "\n\n**SOURCES:**\n" + "\n".join(source_links)
                
        except Exception as e:
            response = f"**ERROR:** {str(e)}"
            
        self.call_from_thread(self.finish_turn, response)

    def finish_turn(self, response: str):
        self.status.remove()
        scroll = self.query_one("#chat-scroll")
        scroll.mount(ChatMessage(response, "ORACLE"))
        scroll.scroll_end(animate=True)

if __name__ == "__main__":
    app = SecurityDashboard()
    app.run()
