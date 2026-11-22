
import faiss
import numpy as np
import pandas as pd

# ==========================================
# File paths
# ==========================================

EMBEDDINGS_PATH = "../data/dog_embeddings.npy"
METADATA_PATH = "../data/embedding_metadata.csv"


# ==========================================
# Load embeddings and metadata
# ==========================================

embeddings = np.load(EMBEDDINGS_PATH).astype("float32")

metadata = pd.read_csv(
    METADATA_PATH,
    encoding="utf-8-sig"
)

# Clean metadata column names
metadata.columns = [
    str(col).replace("\ufeff", "").strip().strip('"')
    for col in metadata.columns
]

# Validate metadata and embeddings
if len(embeddings) != len(metadata):
    raise ValueError(
        f"Mismatch between embeddings and metadata: "
        f"{len(embeddings)} embeddings, "
        f"{len(metadata)} metadata records."
    )

if embeddings.ndim != 2:
    raise ValueError("Embeddings must be a 2D array.")

if embeddings.shape[1] != 768:
    raise ValueError(
        f"Expected 768-dimensional embeddings, "
        f"received {embeddings.shape[1]}."
    )

# ==========================================
# Create FAISS index
# ==========================================

embedding_dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(embedding_dimension)

# Add embeddings to FAISS
index.add(embeddings)

print("FAISS index created successfully!")
print("Embedding dimension:", embedding_dimension)
print("Total indexed images:", index.ntotal)
print("Metadata columns:", metadata.columns.tolist())


# ==========================================
# Vector Search Function
# ==========================================

def search(query_vec, k=10):
    """
    Find the top-k most similar dog images
    using FAISS inner-product similarity.
    """

    # Convert query embedding to float32
    query_vec = np.asarray(
        query_vec,
        dtype="float32"
    ).reshape(1, -1)

    # Validate query dimensions
    if query_vec.shape[1] != embedding_dimension:
        raise ValueError(
            f"Expected query dimension {embedding_dimension}, "
            f"received {query_vec.shape[1]}."
        )

    # Search FAISS index
    k = min(k, index.ntotal)

    scores, ids = index.search(query_vec, k)

    results = []

    # Retrieve matching metadata
    for score, idx in zip(scores[0], ids[0]):

        if idx == -1:
            continue

        results.append({
            "metadata": metadata.iloc[int(idx)].to_dict(),
            "similarity": float(score)
        })

    return results
