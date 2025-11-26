import pathway as pw
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.embedders import SentenceTransformerEmbedder


# --------------------------------------------------------------------------
# SCHEMA
# --------------------------------------------------------------------------
class SecurityFeedSchema(pw.Schema):
    url: str
    full_text: str
    page_title: str
    timestamp: float
    source_type: str


# --------------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------------
def split_text(text: str) -> list[str]:
    return text.split()

def is_security_keyword(word: str) -> bool:
    keywords = {
        "buffer", "overflow", "heap", "stack", "rop", "shellcode", "uaf",
        "free", "kernel", "driver", "dma", "ebpf", "kvm", "hypervisor",
        "rootkit", "boot", "firmware", "bios", "uefi", "ring0", "cve",
        "zeroday", "0day", "rce", "lpe", "bypass", "injection", "linux",
        "windows", "android", "ios", "chrome", "ssh", "ssl", "tls"
    }
    return word.lower() in keywords

# FIX 1: Helper to pack columns into a single metadata dictionary
def pack_metadata(url: str, title: str, ts: float) -> dict:
    return {"url": url, "title": title, "timestamp": ts}

def run_pipeline():
    # 1. INGESTION
    t = pw.io.jsonlines.read("stream_buffer.jsonl",
                             schema=SecurityFeedSchema,
                             mode="streaming")

    # 2. TOKENIZATION
    words_table = t.select(word_list=pw.apply(split_text, t.full_text),
                           timestamp=t.timestamp)

    # 3. FLATTENING
    flattened = words_table.flatten(words_table.word_list)

    words = flattened.select(word=flattened.word_list,
                             timestamp=flattened.timestamp)

    # 4. FILTERING
    filtered_words = words.filter(pw.apply(is_security_keyword, words.word))

    # 5. BUCKETING
    # Using pw.cast to fix the previous AttributeError
    words_with_bucket = filtered_words.select(word=filtered_words.word, bucket=pw.cast(int, filtered_words.timestamp // 60))

    # 6. AGGREGATION
    stats = words_with_bucket.groupby(
        words_with_bucket.word, 
        words_with_bucket.bucket
    ).reduce(
        count=pw.reducers.count()
    )

    # 7. OUTPUT ANALYTICS (FIXED)
    # Filter for hits
    raw_alerts = stats.filter(stats.count > 0)
    
    # CRITICAL FIX: Explicitly select columns to ensure CSV structure
    # We force the order: word, count, bucket
    formatted_alerts = raw_alerts.select(
        word=raw_alerts.word,
        count=raw_alerts.count,
        bucket=raw_alerts.bucket
    )
    pw.io.csv.write(formatted_alerts, "live_alerts.csv")

    # 8. RAG ENGINE PREPARATION (The Fix)
    # We create a new view 'rag_table' that matches what VectorStoreServer expects.
    # 1. Rename 'full_text' -> 'data'
    # 2. Pack other columns -> '_metadata'
    rag_table = t.select(data=t.full_text, _metadata=pw.apply(pack_metadata, t.url, t.page_title, t.timestamp))

    # 9. START RAG SERVER
    vector_server = VectorStoreServer(
        rag_table,  # Now passing the correctly formatted table
        embedder=SentenceTransformerEmbedder(model="all-MiniLM-L6-v2"),
    )

    print("[Pathway Pipeline] Starting RAG Server on 0.0.0.0:9000...")
    vector_server.run_server(host="0.0.0.0", port=9000, threaded=False)

    # pw.run()


if __name__ == "__main__":
    run_pipeline()
