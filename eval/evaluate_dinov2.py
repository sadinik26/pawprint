
import faiss
import numpy as np
import pandas as pd
from pathlib import Path

# ==========================================
# File paths
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "dog_embeddings.npy"
METADATA_PATH = PROJECT_ROOT / "data" / "embedding_metadata.csv"

OUTPUT_PATH = PROJECT_ROOT / "eval" / "dinov2_baseline_results.csv"


# ==========================================
# Load embeddings and metadata
# ==========================================

print("Loading embeddings and metadata...")

embeddings = np.load(EMBEDDINGS_PATH).astype("float32")

metadata = pd.read_csv(
    METADATA_PATH,
    encoding="utf-8-sig"
)

metadata.columns = [
    str(col).replace("\ufeff", "").strip().strip('"')
    for col in metadata.columns
]

if len(embeddings) != len(metadata):
    raise ValueError(
        "Embedding and metadata counts do not match."
    )

if "dog_id" not in metadata.columns:
    raise ValueError("dog_id column is missing.")

print("Total images:", len(embeddings))
print("Embedding dimensions:", embeddings.shape[1])
print("Unique dog identities:", metadata["dog_id"].nunique())


# ==========================================
# Create FAISS index
# ==========================================

print("\nCreating FAISS index...")

dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)
index.add(embeddings)

print("FAISS index created successfully!")


# ==========================================
# Top-1 and Top-5 Evaluation
# ==========================================

print("\nStarting DINOv2 evaluation...")
print("Self-matches will be excluded.")

total_queries = len(embeddings)

top1_correct = 0
top5_correct = 0

evaluation_results = []

# Retrieve enough candidates to allow removal
# of the query image itself.
search_k = min(10, index.ntotal)

for query_idx in range(total_queries):

    query_embedding = embeddings[
        query_idx:query_idx + 1
    ]

    query_dog_id = str(
        metadata.iloc[query_idx]["dog_id"]
    ).strip()

    # Search similar images
    scores, ids = index.search(
        query_embedding,
        search_k
    )

    # Exclude the exact query image
    candidates = []

    for score, candidate_idx in zip(
        scores[0],
        ids[0]
    ):

        if candidate_idx == -1:
            continue

        if candidate_idx == query_idx:
            continue

        candidates.append(
            (int(candidate_idx), float(score))
        )

    # Use the first five remaining candidates
    top5_candidates = candidates[:5]

    if not top5_candidates:
        continue

    # Top-1 evaluation
    top1_idx, top1_score = top5_candidates[0]

    top1_dog_id = str(
        metadata.iloc[top1_idx]["dog_id"]
    ).strip()

    top1_match = top1_dog_id == query_dog_id

    if top1_match:
        top1_correct += 1

    # Top-5 evaluation
    top5_dog_ids = [
        str(metadata.iloc[idx]["dog_id"]).strip()
        for idx, score in top5_candidates
    ]

    top5_match = query_dog_id in top5_dog_ids

    if top5_match:
        top5_correct += 1

    evaluation_results.append({
        "query_image": metadata.iloc[query_idx]["image_path"],
        "query_dog_id": query_dog_id,
        "top1_retrieved_dog_id": top1_dog_id,
        "top1_similarity": top1_score,
        "top1_correct": top1_match,
        "top5_correct": top5_match
    })

    # Display progress
    if (query_idx + 1) % 500 == 0:
        print(
            f"Processed {query_idx + 1}/{total_queries} images"
        )


# ==========================================
# Calculate Evaluation Metrics
# ==========================================

evaluated_queries = len(evaluation_results)

if evaluated_queries == 0:
    raise RuntimeError("No queries were evaluated.")

top1_accuracy = (
    top1_correct / evaluated_queries
) * 100

top5_accuracy = (
    top5_correct / evaluated_queries
) * 100


# ==========================================
# Save Detailed Evaluation Results
# ==========================================

results_df = pd.DataFrame(evaluation_results)

results_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ==========================================
# Display Final Results
# ==========================================

print("\n" + "=" * 55)
print("DINOv2 BASELINE EVALUATION RESULTS")
print("=" * 55)

print("Total dataset images:", total_queries)
print("Successfully evaluated queries:", evaluated_queries)

print("\nEvaluation Metrics")
print("-" * 55)

print(f"Top-1 Accuracy: {top1_accuracy:.2f}%")
print(f"Top-5 Accuracy: {top5_accuracy:.2f}%")

print("\nCorrect Matches")
print("-" * 55)

print(f"Top-1 correct: {top1_correct}")
print(f"Top-5 correct: {top5_correct}")

print("\nDetailed results saved to:")
print(OUTPUT_PATH)

print("\nDINOv2 baseline evaluation completed!")
