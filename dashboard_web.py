from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import glob
import csv
import requests
import ollama

RAG_ENDPOINT = os.getenv("RAG_ENDPOINT", "http://localhost:9000/v1/retrieve")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = "phi3"
ALERTS_PATH = "live_alerts.csv"

app = Flask(__name__, template_folder='.')
CORS(app)

def get_alerts():
    files = []
    if os.path.isdir(ALERTS_PATH):
        files = glob.glob(os.path.join(ALERTS_PATH, "*.csv"))
    elif os.path.isfile(ALERTS_PATH):
        files = [ALERTS_PATH]

    if not files:
        return []

    threat_map = {}
    for file in files:
        try:
            with open(file, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 3: continue
                    raw_word, raw_count = row[0], row[1]
                    if raw_word and raw_count.replace('.', '', 1).isdigit():
                        clean_word = raw_word.lower()
                        current_total = threat_map.get(clean_word, 0)
                        threat_map[clean_word] = current_total + int(float(raw_count))
        except Exception:
            pass

    alerts = sorted(threat_map.items(), key=lambda x: x[1], reverse=True)
    return [{"word": word, "count": count} for word, count in alerts[:20]]

def process_query(query: str) -> str:
    try:
        payload = {"query": query, "k": 3}
        try:
            rag_resp = requests.post(RAG_ENDPOINT, json=payload, timeout=5)
            rag_resp.raise_for_status()
            docs = rag_resp.json()
        except requests.exceptions.RequestException as e:
            return f"**ERROR:** Could not connect to RAG service: {e}"

        context_blocks = []
        source_links = []
        if docs:
            for idx, item in enumerate(docs):
                meta = item.get("metadata", {})
                text = item.get("text", "")[:300].replace("\n", " ")
                title = meta.get("title", "Unknown")
                url = meta.get("url", "#")
                context_blocks.append(f"REPORT {idx+1}: {text}")
                if url != "#":
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
        
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/alerts')
def alerts_endpoint():
    return jsonify(get_alerts())

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "Empty query"}), 400
    
    response = process_query(query)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
