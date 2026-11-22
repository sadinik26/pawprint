
from PIL import Image
from dino_embeddings import embed
from vector_search import search

# Load a dataset image
image_path = "../data/after_4_bis/0/0.0.jpg"

img = Image.open(image_path).convert("RGB")

# Generate query embedding
query_embedding = embed(img)

# Search for top 10 matches
results = search(query_embedding, k=10)

print("\nTop 10 Similar Dog Images")
print("=" * 50)

for rank, result in enumerate(results, start=1):
    print(f"\nRank: {rank}")
    print(f"Dog ID: {result['metadata']['dog_id']}")
    print(f"Image: {result['metadata']['image_path']}")
    print(f"Similarity: {result['similarity']:.4f}")
