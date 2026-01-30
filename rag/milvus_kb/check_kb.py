import os, sys
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)
from client_manager import client,load_user_collection,COLLECTION_PREFIX,load_public_collection
from collections import Counter

def get_all_user_ids(prefix="kb_user_"):
    all_collections = client.list_collections()
    user_ids = [
        name.replace(prefix, "") for name in all_collections
        if name.startswith(prefix)
    ]
    return user_ids

def get_user_files(user_id):
    load_user_collection(user_id)
    collection_name = f"{COLLECTION_PREFIX}user_{user_id}"
    res = client.query(
        collection_name=collection_name,
        filter="",
        output_fields=["source"],
        limit=10000
    )
    print(len(res))
    sources = [r["source"] for r in res]
    source_counts = {}
    for r in res:
        src = r["source"]
        if src not in source_counts:
            source_counts[src] = 1
        else:
            source_counts[src] += 1
    def strip_prefix(src):
        prefix = f"{user_id}_"
        return src[len(prefix):] if src.startswith(prefix) else src

    return [
        {"source": strip_prefix(src), "chunk_count": count}
        for src, count in source_counts.items()
    ]



def get_public_files():
    load_public_collection()
    collection_name = f"{COLLECTION_PREFIX}admin_public"
    res = client.query(
        collection_name=collection_name,
        filter="",
        output_fields=["source"],
        limit=10000
    )
    print(len(res))
    sources = [r["source"] for r in res]
    counts = Counter(sources)
  
    return [{"source": src, "chunk_count": count} for src, count in counts.items()]

print(get_public_files())
print(get_all_user_ids())
