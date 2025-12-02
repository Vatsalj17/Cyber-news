import pathway as pw
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.embedders import SentenceTransformerEmbedder

# Schema
class SecurityFeedSchema(pw.Schema):
    url: str
    full_text: str
    page_title: str
    timestamp: float
    source_type: str

# Helper functions
def split_text(text: str) -> list[str]:
    return text.split()

def is_security_keyword(word: str) -> bool:
    keywords = {
        "buffer", "overflow", "heap", "stack", "rop", "shellcode", "uaf", "free",
        "kernel", "driver", "dma", "ebpf", "kvm", "hypervisor", "rootkit", "boot",
        "firmware", "bios", "uefi", "ring0",
        "cve", "zeroday", "0day", "rce", "lpe", "bypass", "injection",
        "linux", "windows", "android", "ios", "chrome", "ssh", "ssl", "tls"
    }
    return word.lower() in keywords

def pack_metadata(url: str, title: str, ts: float) -> dict:
    return {"url": url, "title": title, "timestamp": ts}

def run_pipeline():
    # 1. Ingestion
    t = pw.io.jsonlines.read(
        "stream_buffer.jsonl",
        schema=SecurityFeedSchema,
        mode="streaming"
    )

    # 2. Tokenization
    words_table = t.select(
        word_list=pw.apply(split_text, t.full_text),
        timestamp=t.timestamp
    )

    # 3. Flattening
    flattened = words_table.flatten(words_table.word_list)
    
    words = flattened.select(
        word=flattened.word_list, 
        timestamp=flattened.timestamp
    )

    # 4. Filtering
    filtered_words = words.filter(
        pw.apply(is_security_keyword, words.word)
    )

    # 5. Bucketing
    words_with_bucket = filtered_words.select(
        word=filtered_words.word,
        bucket=pw.cast(int, filtered_words.timestamp // 60)
    )

    # 6. Aggregation (fixed)
    stats = words_with_bucket.groupby(
        words_with_bucket.word, 
        words_with_bucket.bucket
    ).reduce(
        word=pw.reducers.max(words_with_bucket.word),      
        bucket=pw.reducers.max(words_with_bucket.bucket),  
        count=pw.reducers.count()
    )

    # 7. Output analytics
    raw_alerts = stats.filter(stats.count > 0)

    formatted_alerts = raw_alerts.select(
        word=raw_alerts.word,
        count=raw_alerts.count,
        bucket=raw_alerts.bucket
    )

    pw.io.csv.write(formatted_alerts, "live_alerts.csv")

    # 8. Rag engine preparation
    rag_table = t.select(
        data=t.full_text,
        _metadata=pw.apply(pack_metadata, t.url, t.page_title, t.timestamp)
    )

    # 9. Start rag server
    vector_server = VectorStoreServer(
        rag_table, 
        embedder=SentenceTransformerEmbedder(model="all-MiniLM-L6-v2"),
    )

    print("[Pathway Pipeline] Starting RAG Server on 0.0.0.0:9000...")
    vector_server.run_server(host="0.0.0.0", port=9000, threaded=False)

if __name__ == "__main__":
    run_pipeline()
