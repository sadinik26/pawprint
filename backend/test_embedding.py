from PIL import Image
from dino_embeddings import embed

image_path = "../data/after_4_bis/0/0.0.jpg"

img = Image.open(image_path).convert("RGB")
embedding = embed(img)

print("Embedding generated successfully!")
print("Embedding shape:", embedding.shape)
print("Embedding data type:", embedding.dtype)
print("First 10 values:", embedding[:10])