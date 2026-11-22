
from ultralytics import YOLO
from PIL import Image

detector = YOLO("yolov8n.pt")  # COCO class 16 = dog

def crop_dog(img: Image.Image):
    res = detector(img, verbose=False)[0]
    dogs = [b for b in res.boxes if int(b.cls) == 16]

    if not dogs:
        return img  # fallback: use full image

    best = max(dogs, key=lambda b: b.conf)
    x1, y1, x2, y2 = map(int, best.xyxy[0])

    return img.crop((x1, y1, x2, y2))
