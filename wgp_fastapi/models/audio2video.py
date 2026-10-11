from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# Mapping from API model IDs to WanGP model_type strings
AUDIO2VIDEO_MODEL_TYPE_MAP = {
    "ltx2_22B_distilled_1_1": "ltx2_22B_distilled_1_1",
    "ltx2_22B_1_1": "ltx2_22B_1_1",
}

FOLEY_LORA_URL = "https://huggingface.co/FuzzPuppy/LTX-2.3-Foley-LoRA/resolve/main/ltx-2.3-foley-400-steps.safetensors"


class Audio2VideoModel(str, Enum):
    """Supported LTX-2.3 models for audio-to-video generation."""

    LTX2_22B_DISTILLED_1_1 = "ltx2_22B_distilled_1_1"
    LTX2_22B_1_1 = "ltx2_22B_1_1"

    @property
    def model_type(self) -> str:
        """Get the WanGP model_type string for this model."""
        return AUDIO2VIDEO_MODEL_TYPE_MAP.get(self.value, self.value)


class Audio2VideoRequest(BaseModel):
    """Request model for generating audio from a control video using LTX-2.3 models."""

    prompt: str
    seed: int
    model: Audio2VideoModel

    def to_wgp_settings(
        self,
        video_path: str,
        fps: int,
        video_length: int,
        width: int,
        height: int,
    ) -> dict:
        """Convert to WanGP task settings dict.

        The video resolution, frame count, and fps are derived from the input
        video file rather than user-supplied parameters.
        """
        settings = {
            "prompt": self.prompt,
            "seed": self.seed,
            "resolution": f"{width}x{height}",
            "batch_size": 1,
            "model_type": self.model.model_type,
            "video_length": video_length,
            "image_mode": 0,
            "force_fps": fps,
            "video_guide": video_path,
            # LTX2 Raw Format / Control Video for Ic Lora
            "video_prompt_type": "VG",
            # Generate Audio based on Control Video and Text Prompt
            "audio_prompt_type": "2",
            # Single phase generation
            "guidance_phases": 1,
            # Always apply foley LoRA at full strength
            "activated_loras": [FOLEY_LORA_URL],
            "loras_multipliers": "1",
            # Distilled pipeline defaults
            "num_inference_steps": 8,
            "guidance_scale": 1,
            "flow_shift": 5,
            "sample_solver": "euler",
        }

        # Model-specific overrides for dev (non-distilled) pipeline
        if self.model == Audio2VideoModel.LTX2_22B_1_1:
            settings["num_inference_steps"] = 20
            settings["sample_solver"] = "euler"

        return settings


class Audio2VideoResponse(BaseModel):
    """Response model for audio-to-video generation."""

    model_config = {"protected_namespaces": ()}

    status: str = Field(..., description="Generation status")
    task_id: Optional[str] = Field(default=None, description="Task ID for tracking")
    videos: Optional[list[str]] = Field(
        default=None, description="URLs to generated videos"
    )
    seed_used: int = Field(..., description="Seed that was used for generation")
    model_used: str = Field(..., description="Model that was used for generation")
    resolution: str = Field(..., description="Output resolution")
    video_length: int = Field(..., description="Number of frames generated")
