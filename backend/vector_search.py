
import faiss
import numpy as np

from database import get_dog_embeddings


# DINOv2-base produces 768-dimensional embeddings.
EMBEDDING_DIMENSION = 768

# Separate indexes for lost and found dogs.
lost_index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
found_index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)

# Metadata order must always match the corresponding FAISS index.
lost_metadata = []
found_metadata = []


def _prepare_embedding(embedding):
    """Validate and normalize one DINOv2 embedding."""

    if isinstance(embedding, bytes):
        vector = np.frombuffer(embedding, dtype=np.float32)
    else:
        vector = np.asarray(
            embedding,
            dtype=np.float32
        ).reshape(-1)

    if vector.size != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} embedding values, "
            f"received {vector.size}."
        )

    if not np.all(np.isfinite(vector)):
        raise ValueError("Embedding contains invalid numeric values.")

    vector = vector.reshape(1, -1).copy()

    norm = np.linalg.norm(vector)

    if norm == 0:
        raise ValueError("Cannot index a zero-magnitude embedding.")

    faiss.normalize_L2(vector)

    return np.ascontiguousarray(vector, dtype=np.float32)


def _get_index_and_metadata(status):
    """Return the appropriate FAISS index and metadata list."""

    if status == "lost":
        return lost_index, lost_metadata

    if status == "found":
        return found_index, found_metadata

    raise ValueError("Status must be either 'lost' or 'found'.")


def rebuild_indexes():
    """
    Rebuild both FAISS indexes using embeddings stored in SQLite.

    database.get_dog_embeddings() returns:
        {
            "report_id": ...,
            "embedding": ...,
            "metadata": {...}
        }
    """

    global lost_index, found_index
    global lost_metadata, found_metadata

    lost_index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
    found_index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)

    lost_metadata = []
    found_metadata = []

    for status in ("lost", "found"):

        records = get_dog_embeddings(status)

        index, metadata_list = _get_index_and_metadata(status)

        for record in records:

            vector = _prepare_embedding(record["embedding"])

            # The database stores report details inside record["metadata"].
            metadata = dict(record["metadata"])

            # Add the report ID at the top level.
            metadata["id"] = record["report_id"]
            metadata["status"] = status

            # Do not keep the embedding BLOB or private contact details
            # inside the in-memory search metadata.
            metadata.pop("embedding", None)
            metadata.pop("contact", None)

            index.add(vector)
            metadata_list.append(metadata)

    print(
        "FAISS indexes rebuilt successfully. "
        f"Lost dogs: {lost_index.ntotal}, "
        f"Found dogs: {found_index.ntotal}"
    )


def add_dog_embedding(status, report_id, embedding, metadata=None):
    """
    Add a newly saved report to the appropriate FAISS index.
    """

    index, metadata_list = _get_index_and_metadata(status)

    vector = _prepare_embedding(embedding)

    report_metadata = dict(metadata or {})

    report_metadata["id"] = report_id
    report_metadata["status"] = status

    report_metadata.pop("embedding", None)
    report_metadata.pop("contact", None)

    index.add(vector)
    metadata_list.append(report_metadata)


def search_opposite_category(
    query_embedding,
    new_status,
    k=10,
    district=None,
    date=None,
    size=None
):
    """
    Search for visually similar reports in the opposite category.

    Lost searches Found.
    Found searches Lost.

    District provides a small ranking preference.
    Size is used as an optional filter when both sizes are known.

    The similarity value is the cosine similarity of normalized
    DINOv2 embeddings. It is not a probability.
    """

    if new_status == "lost":
        target_status = "found"

    elif new_status == "found":
        target_status = "lost"

    else:
        raise ValueError(
            "new_status must be either 'lost' or 'found'."
        )

    if k < 1:
        raise ValueError("k must be at least 1.")

    index, metadata_list = _get_index_and_metadata(target_status)

    if index.ntotal == 0:
        return []

    query_vector = _prepare_embedding(query_embedding)

    # Search all records so other districts remain eligible.
    similarities, positions = index.search(
        query_vector,
        index.ntotal
    )

    candidates = []

    for similarity, position in zip(
        similarities[0],
        positions[0]
    ):

        if position < 0:
            continue

        metadata = metadata_list[position]

        # Apply size filtering only when both values are available.
        if (
            size
            and metadata.get("size")
            and str(metadata["size"]).strip().lower()
            != str(size).strip().lower()
        ):
            continue

        similarity = float(similarity)

        same_district = (
            bool(district)
            and bool(metadata.get("district"))
            and str(district).strip().lower()
            == str(metadata["district"]).strip().lower()
        )

        # Small district preference; original similarity stays unchanged.
        ranking_score = similarity

        if same_district:
            ranking_score += 0.03

        result = dict(metadata)

        result["similarity"] = similarity
        result["same_district"] = same_district
        result["ranking_score"] = ranking_score

        candidates.append(result)

    candidates.sort(
        key=lambda item: item["ranking_score"],
        reverse=True
    )

    return candidates[:k]
