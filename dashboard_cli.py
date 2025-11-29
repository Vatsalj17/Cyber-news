import os
import glob
import csv
import requests
import datetime
import ollama
import sys

# --- CONFIGURATION ---
RAG_ENDPOINT = os.getenv("RAG_ENDPOINT", "http://localhost:9000/v1/retrieve")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = "phi3"
ALERTS_PATH = "live_alerts.csv"

# --- MINIMAL UTILS ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(msg, color=None):
    if color:
        print(f"{color}{msg}{Colors.END}")
    else:
        print(msg)

def show_help():
    print(f"\n{Colors.HEADER}--- AVAILABLE COMMANDS ---{Colors.END}")
    print(f"{Colors.BOLD}/alerts{Colors.END}   : Show current threat counts from CSV files")
    print(f"{Colors.BOLD}/config{Colors.END}   : Show current connection settings")
    print(f"{Colors.BOLD}/clear{Colors.END}    : Clear the terminal screen")
    print(f"{Colors.BOLD}/quit{Colors.END}     : Exit the application")
    print(f"{Colors.BOLD}[text]{Colors.END}    : Anything else is sent as a query to the AI\n")

def get_alerts():
    """Reads CSVs and prints a simple formatted list."""
    files = []
    if os.path.isdir(ALERTS_PATH):
        files = glob.glob(os.path.join(ALERTS_PATH, "*.csv"))
    elif os.path.isfile(ALERTS_PATH):
        files = [ALERTS_PATH]

    if not files:
        log("No alert files found.", Colors.RED)
        return

    threat_map = {}
    for file in files:
        try:
            with open(file, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 2: continue
                    word, count = row[0], row[1]
                    if word and count.replace('.', '', 1).isdigit():
                        clean_word = word.lower()
                        threat_map[clean_word] = threat_map.get(clean_word, 0) + int(float(count))
        except Exception:
            continue

    sorted_alerts = sorted(threat_map.items(), key=lambda x: x[1], reverse=True)[:20]

    log(f"\n--- THREAT MONITOR ({datetime.datetime.now().strftime('%H:%M:%S')}) ---", Colors.BOLD)
    print(f"{'THREAT':<25} | {'COUNT':<10}")
    print("-" * 40)
    for word, count in sorted_alerts:
        c_code = Colors.RED if count > 100 else (Colors.BLUE if count > 20 else "")
        print(f"{c_code}{word:<25} | {count:<10}{Colors.END}")
    print("")

def run_query(query):
    """Handles RAG retrieval and LLM generation."""
    log("... Analyzing ...", Colors.BLUE)
    
    # 1. RAG Retrieval
    context = "NO SIGNAL"
    sources = []
    
    try:
        payload = {"query": query, "k": 3}
        rag_resp = requests.post(RAG_ENDPOINT, json=payload, timeout=5)
        rag_resp.raise_for_status()
        docs = rag_resp.json()
        
        if docs:
            context_blocks = []
            for idx, item in enumerate(docs):
                text = item.get("text", "")[:300].replace("\n", " ")
                meta = item.get("metadata", {})
                context_blocks.append(f"REPORT {idx+1}: {text}")
                if meta.get("url"):
                    sources.append(f"{idx+1}. {meta['title']} ({meta['url']})")
            context = "\n".join(context_blocks)
            
    except Exception as e:
        log(f"Warning: RAG Retrieval failed ({str(e)})", Colors.RED)

    # 2. LLM Inference
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        sys_msg = "You are a security analyst. Use REPORTS to answer. Be brief. Plain text only."
        prompt = f"REPORTS:\n{context}\n\nQUERY: {query}"
        
        stream = client.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt}
            ]
        )
        response = stream["message"]["content"]
        
        log("\n>> ORACLE RESPONSE:", Colors.GREEN)
        print(response.strip())
        
        if sources:
            print("\nSources:")
            for s in sources: print(s)
        print("")
        
    except Exception as e:
        log(f"Error: LLM Generation failed ({str(e)})", Colors.RED)

# --- MAIN LOOP ---
def main():
    print(f"{Colors.BOLD}Security CLI v1.0{Colors.END} | Type {Colors.BOLD}/help{Colors.END} for commands")
    
    while True:
        try:
            user_input = input(f"{Colors.BOLD}command > {Colors.END}").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["/quit", "exit", "quit"]:
                log("Shutting down.", Colors.RED)
                break
            elif user_input.lower() in ["/help", "help"]:
                show_help()
            elif user_input.lower() == "/alerts":
                get_alerts()
            elif user_input.lower() == "/clear":
                os.system('cls' if os.name == 'nt' else 'clear')
            elif user_input.lower() == "/config":
                print(f"RAG: {RAG_ENDPOINT}\nLLM: {OLLAMA_HOST}/{LLM_MODEL}")
            else:
                run_query(user_input)
                
        except KeyboardInterrupt:
            print("\nUse /quit to exit.")
        except EOFError:
            break

if __name__ == "__main__":
    main()
