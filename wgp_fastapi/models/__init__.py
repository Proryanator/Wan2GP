"""
Pydantic models for the FastAPI wrapper.

Exports:
    - Text to Image models (t2i.py)
    - Image to Image models (i2i.py)
    - Image to Video models (i2v.py)
"""

from wgp_fastapi.models.t2i import (
    TextToImageRequest,
    TextToImageResponse,
    FluxModel,
)
from wgp_fastapi.models.i2i import (
    ImageToImageRequest,
    ImageToImageResponse,
    I2VModel as I2VImageModel,
)
from wgp_fastapi.models.i2v import (
    ImageToVideoRequest,
    ImageToVideoResponse,
    I2VVideoModel,
)
from wgp_fastapi.models.flux_image import (
    FluxImageRequest,
    FluxImageResponse,
    FluxImageModel,
    TaskStatus,
    FluxImageTaskResponse,
)

__all__ = [
    # T2I
    "TextToImageRequest",
    "TextToImageResponse",
    "FluxModel",
    # I2I
    "ImageToImageRequest",
    "ImageToImageResponse",
    "I2VModel",
    # I2V
    "ImageToVideoRequest",
    "ImageToVideoResponse",
    "I2VVideoModel",
    # Flux Image
    "FluxImageRequest",
    "FluxImageResponse",
    "FluxImageModel",
    # Task Status
    "TaskStatus",
]
