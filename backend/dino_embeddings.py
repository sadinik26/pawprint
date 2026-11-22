
import torch
from transformers import AutoImageProcessor, AutoModel

MODEL_NAME = "facebook/dinov2-base"

# Load image processor and model
processor = AutoImageProcessor.from_pretrained(MODEL_NAME)

model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()


@torch.no_grad()
def embed(img):
    inputs = processor(images=img, return_tensors="pt")

    out = model(**inputs).last_hidden_state[:, 0]

    return torch.nn.functional.normalize(
        out, dim=-1
    )[0].cpu().numpy()
