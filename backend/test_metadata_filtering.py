
from PIL import Image
from dino_embeddings import embed
from vector_search import search

# ==========================================
# Load query image and generate embedding
# ==========================================

image_path = "../data/after_4_bis/0/0.0.jpg"

img = Image.open(image_path).convert("RGB")
query_embedding = embed(img)

print("Query embedding generated successfully!")


# ==========================================
# Test 1: Location filtering
# ==========================================

print("\nTEST 1: LOCATION FILTERING")
print("=" * 50)

location_results = search(
    query_embedding,
    k=10,
    location=(7.8731, 80.7718),
    max_distance_km=100
)

print("Results found:", len(location_results))

for result in location_results:
    print(
        "Dog ID:", result["metadata"]["dog_id"],
        "| Distance:", result["distance_km"], "km",
        "| Similarity:", round(result["similarity"], 4)
    )


# ==========================================
# Test 2: Date filtering
# ==========================================

print("\nTEST 2: DATE FILTERING")
print("=" * 50)

date_results = search(
    query_embedding,
    k=10,
    date_from="2026-01-01",
    date_to="2026-12-31"
)

print("Results found:", len(date_results))

for result in date_results:
    print(
        "Dog ID:", result["metadata"]["dog_id"],
        "| Date:", result["metadata"]["date"],
        "| Similarity:", round(result["similarity"], 4)
    )


# ==========================================
# Test 3: Size filtering
# ==========================================

print("\nTEST 3: SIZE FILTERING")
print("=" * 50)

size_results = search(
    query_embedding,
    k=10,
    size="medium"
)

print("Results found:", len(size_results))

for result in size_results:
    print(
        "Dog ID:", result["metadata"]["dog_id"],
        "| Size:", result["metadata"]["size"],
        "| Similarity:", round(result["similarity"], 4)
    )


# ==========================================
# Test 4: Combined metadata filtering
# ==========================================

print("\nTEST 4: COMBINED FILTERING")
print("=" * 50)

combined_results = search(
    query_embedding,
    k=10,
    location=(7.8731, 80.7718),
    max_distance_km=100,
    date_from="2026-01-01",
    date_to="2026-12-31",
    size="medium"
)

print("Results found:", len(combined_results))

for result in combined_results:
    print(
        "Dog ID:", result["metadata"]["dog_id"],
        "| Distance:", result["distance_km"], "km",
        "| Date:", result["metadata"]["date"],
        "| Size:", result["metadata"]["size"],
        "| Similarity:", round(result["similarity"], 4)
    )


# ==========================================
# Verify filter conditions
# ==========================================

print("\nFILTER VALIDATION")
print("=" * 50)

assert all(
    result["distance_km"] <= 100
    for result in location_results
)

assert all(
    "2026-01-01" <= str(result["metadata"]["date"])[:10]
    <= "2026-12-31"
    for result in date_results
)

assert all(
    str(result["metadata"]["size"]).strip().lower() == "medium"
    for result in size_results
)

assert all(
    result["distance_km"] <= 100
    and "2026-01-01" <= str(result["metadata"]["date"])[:10]
    <= "2026-12-31"
    and str(result["metadata"]["size"]).strip().lower() == "medium"
    for result in combined_results
)

print("All returned results satisfy their filter conditions!")
