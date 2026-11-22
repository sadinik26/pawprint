
import csv
import os
import numpy as np
from PIL import Image
from tqdm import tqdm

from dino_embeddings import embed

# Project paths
CSV_PATH = "../data/dogs.csv"
OUTPUT_EMBEDDINGS = "../data/dog_embeddings.npy"
OUTPUT_METADATA = "../data/embedding_metadata.csv"

embeddings = []
metadata = []

# Read the dataset CSV
with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    rows = list(reader)

print(f"Total images to process: {len(rows)}")

# Generate one embedding per image
for row in tqdm(rows, desc="Generating embeddings"):
    image_path = row["image_path"]

    try:
        image = Image.open(image_path).convert("RGB")
        vector = embed(image)

        embeddings.append(vector)
        metadata.append(row)

    except Exception as error:
        print(f"\nError processing {image_path}: {error}")

# Save embeddings
if embeddings:
    embedding_array = np.stack(embeddings).astype("float32")
    np.save(OUTPUT_EMBEDDINGS, embedding_array)

    # Save metadata in the same order as the embeddings
    with open(OUTPUT_METADATA, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=metadata[0].keys())
        writer.writeheader()
        writer.writerows(metadata)

    print("\nEmbedding generation completed!")
    print("Embedding matrix shape:", embedding_array.shape)
    print("Embeddings saved to:", OUTPUT_EMBEDDINGS)
    print("Metadata saved to:", OUTPUT_METADATA)
else:
    print("No embeddings were generated.")
