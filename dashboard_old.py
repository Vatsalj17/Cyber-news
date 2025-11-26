import requests
import datetime
import ollama
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container
from textual.widgets import Header, Footer, Input, Static, Markdown, LoadingIndicator
from textual import work

# Configuration
RAG_ENDPOINT = "http://localhost:9000/v1/retrieve"
OLLAMA_HOST = "http://localhost:11434"
LLM_MODEL = "phi3" 

class ChatMessage(Container):
    """A widget to hold a single message (User or AI)."""
    
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
    Screen { layout: vertical; background: #000000; }
    Header { background: #0d1117; color: #58a6ff; dock: top; }
    Footer { background: #0d1117; dock: bottom; }
    
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

    #chat-scroll {
        height: 1fr;
        padding: 1;
    }

    .message-container {
        margin-bottom: 2;
        padding: 1;
        width: 100%;
        height: auto;
    }
    .message-header { color: #8b949e; text-style: bold; margin-bottom: 1; }
    
    /* GitHub Dark Mode Theme Colors */
    .user-message { 
        background: #161b22; 
        border-left: solid #58a6ff; 
    }
    .ai-message { 
        background: #0d1117; 
        border-left: solid #238636; 
    }
    
    .message-body { color: #c9d1d9; }
    LoadingIndicator { height: auto; color: #58a6ff; margin: 1; }
    """

    TITLE = "KERNEL PANIC DASHBOARD"
    SUB_TITLE = "Live Intelligence Stream"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield VerticalScroll(id="chat-scroll")
        with Container(id="input-container"):
            yield Input(placeholder="COMMAND >> (e.g. 'new linux heap exploits')")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Input).focus()
        welcome = ChatMessage(
            f"**UPLINK ESTABLISHED.**\nPipeline: `{RAG_ENDPOINT}`\nNeural Net: `{LLM_MODEL}`\n\n*Waiting for input...*", 
            "SYSTEM"
        )
        self.query_one("#chat-scroll").mount(welcome)

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        query = message.value.strip()
        if not query: return
        message.input.value = ""

        scroll = self.query_one("#chat-scroll")
        await scroll.mount(ChatMessage(query, "You"))
        scroll.scroll_end(animate=False)

        self.loader = LoadingIndicator()
        await scroll.mount(self.loader)
        scroll.scroll_end()
        
        self.process_query(query)

    @work(exclusive=True, thread=True)
    def process_query(self, query: str):
        try:
            # 1. RAG Retrieval
            payload = {"query": query, "k": 4} # Increased k to get more technical details
            try:
                rag_resp = requests.post(RAG_ENDPOINT, json=payload, timeout=5)
                rag_resp.raise_for_status()
                docs = rag_resp.json()
            except Exception:
                docs = []

            # 2. Context Builder (With Metadata)
            context_blocks = []
            source_links = []
            
            if docs:
                for idx, item in enumerate(docs):
                    meta = item.get("metadata", {})
                    raw_text = item.get("text", "")[:400].replace("\n", " ") # Compressed text
                    
                    url = meta.get('url', 'N/A')
                    title = meta.get('title', 'Unknown Intel')
                    
                    context_blocks.append(f"REPORT {idx+1} [{title}]: {raw_text}")
                    # Markdown Link for display
                    source_links.append(f"{idx+1}. [{title}]({url})")
            
            context_text = "\n\n".join(context_blocks)

            # 3. System Prompt (The Persona)
            if context_text:
                system_instruction = (
                    "You are an elite low-level security researcher. "
                    "Use the provided REPORTS to answer the user's technical query. "
                    "Focus on technical details (POCs, CVE IDs, affected versions). "
                    "Be brief and direct. No fluff."
                )
                footer = "\n\n---\n**INTEL SOURCES:**\n" + "\n".join(source_links)
            else:
                context_text = "NO SIGNAL."
                system_instruction = (
                    "No live intelligence found on this specific vector. "
                    "Provide general technical knowledge on the topic instead. "
                    "Mark response as **[OFFLINE ARCHIVE]**."
                )
                footer = ""

            final_prompt = f"REPORTS:\n{context_text}\n\nQUERY: {query}\nANALYSIS:"

            # 4. Inference
            client = ollama.Client(host=OLLAMA_HOST)
            stream = client.chat(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": final_prompt}
                ],
                options={"stop": ["QUERY:", "REPORTS:"]}
            )
            response = stream["message"]["content"] + footer
        except Exception as e:
            response = f"**KERNEL ERROR:** {str(e)}"
        
        self.call_from_thread(self.finish_turn, response)

    def finish_turn(self, response: str):
        self.loader.remove()
        scroll = self.query_one("#chat-scroll")
        scroll.mount(ChatMessage(response, "ORACLE"))
        scroll.scroll_end(animate=True)

if __name__ == "__main__":
    app = SecurityDashboard()
    app.run()
