"""Quick auth diagnostic — prints masked key + endpoint, then tests the connection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import cfg

endpoint = cfg.doc_intelligence_endpoint
key = cfg.doc_intelligence_key

print("=== Document Intelligence config ===")
print(f"Endpoint : {endpoint!r}")
if key:
    print(f"Key      : {key[:4]}...{key[-4:]}  (length={len(key)})")
else:
    print("Key      : (empty — not loaded from .env)")

print()

# Quick live test using the same auth path as the real pipeline
try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential

    if key:
        print("Auth method: AzureKeyCredential")
        credential = AzureKeyCredential(key)
    else:
        print("Auth method: DefaultAzureCredential (az login)")
        credential = DefaultAzureCredential()

    client = DocumentIntelligenceClient(endpoint=endpoint, credential=credential)
    # Analyze a tiny inline document to confirm auth end-to-end
    import base64
    tiny_pdf = base64.b64decode(
        "JVBERi0xLjAKMSAwIG9iajw8L1R5cGUvQ2F0YWxvZy9QYWdlcyAyIDAgUj4"
        "+"
        "CmVuZG9iagoyIDAgb2JqPDwvVHlwZS9QYWdlcy9LaWRzWzMgMCBSXS9Db3Vu"
        "dCAxPj4KZW5kb2JqCjMgMCBvYmo8PC9UeXBlL1BhZ2UvTWVkaWFCb3hbMCAw"
        "IDMgM10+PgplbmRvYmoKeHJlZgowIDQKMDAwMDAwMDAwMCA2NTUzNSBmIAow"
        "MDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMD"
        "ExNSAwMDAwMCBuIAp0cmFpbGVyPDwvU2l6ZSA0L1Jvb3QgMSAwIFI+PgpzdGFy"
        "dHhyZWYKMTUzCiUlRU9G"
    )
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        AnalyzeDocumentRequest(bytes_source=tiny_pdf),
    )
    poller.result()
    print("✅ Auth OK — Document Intelligence call succeeded")
except Exception as e:
    print(f"❌ Failed: {e}")
