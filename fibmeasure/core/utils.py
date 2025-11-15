import base64
import io
import numpy as np
from PIL import Image
import cv2


def np_image_to_base64(img):
    if img.ndim == 2:
        mode = "L"
    elif img.ndim == 3 and img.shape[2] == 3:
        mode = "RGB"
    else:
        raise ValueError(f"Expected 2D grayscale or 2D RGB image, got shape {img.shape}")

    if img.dtype != np.uint8:
        img_min, img_max = float(img.min()), float(img.max())
        if img_max == img_min:
            img8 = np.zeros_like(img, dtype=np.uint8)
        else:
            img8 = ((img - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    else:
        img8 = img

    buf = io.BytesIO()
    Image.fromarray(img8, mode=mode).save(buf, format="PNG")

    return base64.b64encode(buf.getvalue()).decode("utf-8")


def draw_segments_on_image(image, segments, color=(255, 0, 0), thickness=1):
    img = image.astype(float)
    img = 255 * img
    img = img.astype(np.uint8)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    for (y1, x1), (y2, x2) in segments:
        p1 = (int(round(x1)), int(round(y1)))
        p2 = (int(round(x2)), int(round(y2)))
        cv2.line(img_rgb, p1, p2, color, thickness, lineType=cv2.LINE_AA)

    return img_rgb
