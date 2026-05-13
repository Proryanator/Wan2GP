"""
Pydantic models for text-to-image generation endpoints.

Supports: Flux 1 Kontext, Flux 1 Dev, Flux 2 Klein
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# Mapping from API model IDs to WanGP model_type strings
FLUX_MODEL_TYPE_MAP = {
    "flux_1_kontext": "flux_dev_kontext_dreamomni2",
    "flux_1_dev": "flux",
    "flux_2_klein": "flux2_klein_9b",
    "flux_2_klein_4b": "flux2_klein_4b",
}


class FluxModel(str, Enum):
    """Supported Flux models for text-to-image generation."""

    FLUX_1_KONTEXT = "flux_1_kontext"
    FLUX_1_DEV = "flux_1_dev"
    FLUX_2_KLEIN = "flux_2_klein"
    FLUX_2_KLEIN_4B = "flux_2_klein_4b"

    @property
    def model_type(self) -> str:
        """Get the WanGP model_type string for this model."""
        return FLUX_MODEL_TYPE_MAP.get(self.value, self.value)


class TextToImageRequest(BaseModel):
    """Request model for text-to-image generation."""

    prompt: str = Field(..., description="Text prompt for image generation")
    seed: int = Field(default=0, description="Random seed for reproducibility")
    num_inference_steps: int = Field(
        default=30, ge=1, le=100, description="Number of inference steps"
    )
    width: int = Field(
        default=1024, ge=256, le=4096, description="Image width in pixels"
    )
    height: int = Field(
        default=1024, ge=256, le=4096, description="Image height in pixels"
    )
    batch_size: int = Field(
        default=1, ge=1, le=16, description="Number of images to generate"
    )
    model: FluxModel = Field(
        default=FluxModel.FLUX_1_DEV, description="Flux model to use"
    )
    guidance_scale: Optional[float] = Field(
        default=7.0, ge=1.0, le=20.0, description="Guidance scale"
    )

    def to_wgp_settings(self) -> dict:
        """Convert to WanGP task settings dict."""
        return {
            "prompt": self.prompt,
            "seed": self.seed,
            "num_inference_steps": self.num_inference_steps,
            "resolution": f"{self.width}x{self.height}",
            "batch_size": self.batch_size,
            "model_type": self.model.model_type,
            "guidance_scale": self.guidance_scale,
            "image_mode": 1,  # Image generation mode
        }


class TextToImageResponse(BaseModel):
    """Response model for text-to-image generation."""

    model_config = {"protected_namespaces": ()}

    status: str = Field(..., description="Generation status")
    task_id: Optional[str] = Field(default=None, description="Task ID for tracking")
    images: Optional[list[str]] = Field(
        default=None, description="Base64 encoded generated images"
    )
    seed_used: int = Field(..., description="Seed that was used for generation")
    model_used: str = Field(..., description="Model that was used for generation")
    steps: int = Field(..., description="Number of inference steps used")
    resolution: str = Field(..., description="Output resolution")
    batch_size: int = Field(..., description="Number of images generated")
