"""
NSFW content checking services (text + image).

Cross-platform (macOS / Windows / Linux). Models auto-download to the
repo's ckpts/ folder on first use and are unloaded after each call to
free up RAM.
"""
from __future__ import annotations

import base64
import gc
import io
import json
import threading
from pathlib import Path

import torch
from PIL import Image, ImageFilter, ImageOps

_TEXT_NSFW_THRESHOLD = 0.5
_IMAGE_NSFW_THRESHOLD = 0.5

# Detoxify "unbiased" model checkpoint (GitHub release asset, per detoxify v0.5.3 source)
_DETOXIFY_CKPT_URL = (
    "https://github.com/unitaryai/detoxify/releases/download/"
    "v0.3-alpha/toxic_debiased-c7548aa0.ckpt"
)
_DETOXIFY_CKPT_FILENAME = "toxic_debiased-c7548aa0.ckpt"
_TEXT_TOKENIZER_REPO = "roberta-base"
_IMAGE_MODEL_REPO = "Falconsai/nsfw_image_detection"
# Only the files needed for inference (repo also contains huge .bin/.pt files)
_IMAGE_MODEL_ALLOW_PATTERNS = [
    "model.safetensors",
    "config.json",
    "preprocessor_config.json",
    "labels.json",
]

_lock = threading.RLock()


def _ckpts_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "ckpts"


def _device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _ensure_detoxify_assets() -> tuple[str, str]:
    """Download the Detoxify checkpoint + roberta-base tokenizer into ckpts if missing."""
    ckpts = _ckpts_dir()
    ckpt_dir = ckpts / "detoxify"
    ckpt_path = ckpt_dir / _DETOXIFY_CKPT_FILENAME
    if not ckpt_path.exists():
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        from urllib.request import urlretrieve

        print(f"[NSFW] Downloading Detoxify checkpoint (~500 MB) to {ckpt_path} ...")
        urlretrieve(_DETOXIFY_CKPT_URL, ckpt_path)

    tok_dir = ckpts / "roberta-base"
    if not (tok_dir / "tokenizer.json").exists():
        from huggingface_hub import snapshot_download

        print(f"[NSFW] Downloading roberta-base tokenizer to {tok_dir} ...")
        snapshot_download(_TEXT_TOKENIZER_REPO, local_dir=str(tok_dir))

    # detoxify v0.5.3's offline path loads the config from huggingface_config_path,
    # so config.json in the tokenizer dir must declare the checkpoint's output size.
    # roberta-base's vanilla config has no num_labels (defaults to 2), which breaks
    # the 16-class "unbiased" checkpoint. Patch it idempotently.
    tok_config_path = tok_dir / "config.json"
    tok_config = json.loads(tok_config_path.read_text())
    if tok_config.get("num_labels") != 16:
        tok_config["num_labels"] = 16
        tok_config_path.write_text(json.dumps(tok_config, indent=2, sort_keys=True))

    return str(ckpt_path), str(tok_dir)


def _ensure_image_model_dir() -> str:
    """Download the Falconsai NSFW image model into ckpts if missing."""
    ckpts = _ckpts_dir()
    model_dir = ckpts / "nsfw_image_detection"
    if not (model_dir / "model.safetensors").exists():
        from huggingface_hub import snapshot_download

        print(f"[NSFW] Downloading image model (~330 MB) to {model_dir} ...")
        snapshot_download(
            _IMAGE_MODEL_REPO,
            local_dir=str(model_dir),
            allow_patterns=_IMAGE_MODEL_ALLOW_PATTERNS,
        )
    return str(model_dir)


def check_text_nsfw(text: str) -> bool:
    """Return True if the text is sexual in nature (Detoxify sexual_explicit score)."""
    if not text or not text.strip():
        return False
    with _lock:
        model = None
        try:
            ckpt_path, tok_dir = _ensure_detoxify_assets()
            from detoxify import Detoxify

            model = Detoxify(
                "unbiased",
                checkpoint=ckpt_path,
                device=_device(),
                huggingface_config_path=tok_dir,
            )
            result = model.predict(text)
            score = float(result["sexual_explicit"])
            print(f"[NSFW] text sexual_explicit={score:.4f}")
            return score > _TEXT_NSFW_THRESHOLD
        finally:
            if model is not None:
                del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


def check_image_nsfw(image_bytes: bytes) -> tuple[bool, str | None]:
    """Return (is_nsfw, blurred_image_data_url_or_None).

    When NSFW, a GaussianBlur(radius=10) JPEG copy of the image is returned
    as a base64 data URL. Raises ValueError for invalid image input.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception as e:
        raise ValueError(f"Invalid image: {e}")

    with _lock:
        pipe = None
        try:
            model_dir = _ensure_image_model_dir()
            from transformers import pipeline

            pipe = pipeline(
                "image-classification",
                model=model_dir,
                device=0 if torch.cuda.is_available() else -1,
            )
            preds = pipe(img)
            scores = {p["label"]: float(p["score"]) for p in preds}
            is_nsfw = scores.get("nsfw", 0.0) > _IMAGE_NSFW_THRESHOLD
            print(f"[NSFW] image scores={scores}")

            blurred = None
            if is_nsfw:
                blurred_img = img.filter(ImageFilter.GaussianBlur(radius=10))
                buf = io.BytesIO()
                blurred_img.save(buf, format="JPEG", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode()
                blurred = f"data:image/jpeg;base64,{b64}"
            return is_nsfw, blurred
        finally:
            if pipe is not None:
                del pipe
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
