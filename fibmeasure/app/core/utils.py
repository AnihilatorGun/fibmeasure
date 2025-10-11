import base64
import io
import numpy as np
from PIL import Image


def np_grayscale_to_base64(img):
    img_min, img_max = float(img.min()), float(img.max())
    if img_max == img_min:
        img8 = np.zeros_like(img, dtype=np.uint8)
    else:
        img8 = ((img - img_min) / (img_max - img_min) * 255).astype(np.uint8)

    buf = io.BytesIO()
    Image.fromarray(img8, mode="L").save(buf, format="PNG")

    return base64.b64encode(buf.getvalue()).decode("utf-8")
