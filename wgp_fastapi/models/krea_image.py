"""
Pydantic models for KREA text-to-image generation endpoint.

Supports KREA2 Turbo and RAW model variants.
"""

from enum import Enum
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class KreaImageModel(str, Enum):
    """Supported models for KREA text-to-image generation."""

    KREA2_TURBO = "krea2_turbo"
    KREA2_RAW = "krea2_raw"

    @property
    def model_type(self) -> str:
        """Get the WanGP model_type string for this model."""
        return self.value

    @property
    def default_guidance_scale(self) -> float:
        """Default guidance scale for this model variant."""
        if self == KreaImageModel.KREA2_TURBO:
            return 0.0
        return 3.5

    @property
    def default_num_inference_steps(self) -> int:
        """Default inference steps for this model variant."""
        if self == KreaImageModel.KREA2_TURBO:
            return 8
        return 52


class InpaintPreset(int, Enum):
    """LanPaint inpainting presets for KREA2. Values match the underlying model_mode."""

    EASY = 2       # ~2x slower
    MEDIUM = 3     # ~5x slower
    HARD = 4       # ~10x slower
    VERY_HARD = 5  # ~15x slower


class KreaImageTaskResponse(BaseModel):
    """Response for async task submission."""

    task_id: str = Field(..., description="Task ID for polling status")


class KreaImageRequest(BaseModel):
    """Request model for KREA text-to-image generation."""

    model_config = {"protected_namespaces": ()}

    # Core parameters
    prompt: str = Field(..., description="Text prompt for image generation")
    seed: int = Field(
        default=-1, description="Random seed for reproducibility (-1 for random)"
    )
    num_inference_steps: int = Field(
        default=8,
        ge=1,
        le=100,
        description="Number of inference steps (default: 8 for Turbo, 52 for RAW)",
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
    model: KreaImageModel = Field(
        default=KreaImageModel.KREA2_TURBO,
        description="Model to use: krea2_turbo or krea2_raw",
    )
    guidance_scale: Optional[float] = Field(
        default=None,
        description="Guidance scale (defaults to 0 for Turbo, 3.5 for RAW)",
    )
    # Inpainting (optional — all three required to trigger inpaint mode)
    mask_path: Optional[str] = Field(
        default=None, description="Path to mask image for inpainting"
    )
    inpaint_reference_path: Optional[str] = Field(
        default=None,
        description="Path to reference image used to fill the masked area",
    )
    inpaint_preset: Optional[InpaintPreset] = Field(
        default=None,
        description="LanPaint step preset. If unset with mask+ref, defaults to EASY (2 steps).",
    )
    low_quality: Optional[bool] = Field(
        default=False,
        description="Use GGUF Q4 quantized model for lower VRAM usage. Only applies to krea2_turbo.",
    )

    def to_wgp_settings(self) -> dict:
        """Convert to WanGP task settings dict."""

        # Default LoRA for krea2 models
        loras_list = ["krea2_improved.safetensors"]

        # Determine if inpainting: all three inputs must be present
        inpainting = self.mask_path and self.inpaint_reference_path and self.inpaint_preset

        settings = {
            # Core parameters
            "prompt": self.prompt,
            "seed": self.seed,
            "num_inference_steps": self.num_inference_steps,
            "resolution": f"{self.width}x{self.height}",
            "batch_size": self.batch_size,
            "model_type": self.model.model_type,
            "image_mode": 2 if inpainting else 1,  # 2 = inpaint, 1 = t2i
            "image_prompt_type": "I",
            # Output - auto-generate uuid filename
            "output_filename": f"{uuid.uuid4()}.png",
            # LoRA settings
            "activated_loras": loras_list,
            "loras_multipliers": ["1.0"],
        }

        if inpainting:
            assert self.inpaint_preset is not None  # guarded by `inpainting`
            settings["image_mask"] = self.mask_path  # str, not list — generate_media expects str
            settings["image_guide"] = self.inpaint_reference_path
            settings["video_prompt_type"] = "VA"  # krea2 inpaint prompt type
            settings["model_mode"] = self.inpaint_preset.value
            # LanPaint requires full denoise/mask strength
            settings["denoising_strength"] = 1.0
            settings["masking_strength"] = 1.0

        # Apply model-appropriate guidance scale
        gs = (
            self.guidance_scale
            if self.guidance_scale is not None
            else self.model.default_guidance_scale
        )
        settings["guidance_scale"] = gs

        # Pass low_quality flag through for GGUF model override
        if self.low_quality:
            settings["low_quality"] = True

        return settings


class KreaImageResponse(BaseModel):
    """Response model for KREA text-to-image generation."""

    model_config = {"protected_namespaces": ()}

    status: str = Field(..., description="Generation status: pending, success, failed")
    task_id: Optional[str] = Field(default=None, description="Task ID for tracking")
    images: Optional[list[str]] = Field(
        default=None, description="URLs to generated images (filled on completion)"
    )
    seed_used: Optional[int] = Field(
        default=None, description="Seed that was used for generation"
    )
    model_used: Optional[str] = Field(
        default=None, description="Model that was used for generation"
    )
    steps: Optional[int] = Field(
        default=None, description="Number of inference steps used"
    )
    resolution: Optional[str] = Field(default=None, description="Output resolution")
    batch_size: Optional[int] = Field(
        default=None, description="Number of images generated"
    )
    progress: Optional[int] = Field(
        default=None, description="Progress percentage (0-100)"
    )
    preview_image: Optional[str] = Field(
        default=None, description="Base64 encoded preview image (during generation)"
    )
    finished_image: Optional[str] = Field(
        default=None, description="URL to the finished image (on completion)"
    )
