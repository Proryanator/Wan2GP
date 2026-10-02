from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# Mapping from API model IDs to WanGP model_type strings
I2V_MODEL_TYPE_MAP = {
    "hunyuan_1_5_480_i2v_step_distilled": "hunyuan_1_5_480_i2v_step_distilled",
    "wan2_2_i2v_14b_enhanced_lightning_v2": "i2v_2_2_Enhanced_Lightning_v2",
    "minimax_h3_fl2va": "minimax_h3_fl2va",
    "minimax_h3_fl2va_pruned": "minimax_h3_fl2va_pruned",
}


class I2VVideoModel(str, Enum):
    """Supported models for image-to-video generation."""
    HUNYUAN_1_5_480_I2V_STEP_DISTILLED = "hunyuan_1_5_480_i2v_step_distilled"
    WAN2_2_I2V_14B_ENHANCED_LIGHTNING_V2 = "wan2_2_i2v_14b_enhanced_lightning_v2"
    MINIMAX_H3_FL2VA = "minimax_h3_fl2va"
    MINIMAX_H3_FL2VA_PRUNED = "minimax_h3_fl2va_pruned"

    @property
    def model_type(self) -> str:
        """Get the WanGP model_type string for this model."""
        return I2V_MODEL_TYPE_MAP.get(self.value, self.value)


class ImageToVideoRequest(BaseModel):
    """Request model for image-to-video generation."""

    prompt: str
    seed: int
    num_inference_steps: int
    width: int
    height: int
    batch_size: int
    model: I2VVideoModel
    video_length: int
    guidance_scale: Optional[float]
    fps: int
    low_quality: Optional[bool] = Field(
        default=False,
        description="Use GGUF Q4 quantized model for lower VRAM usage (~14GB vs ~30GB). "
                    "Applies to wan2_2_i2v_14b_enhanced_lightning_v2 and minimax_h3_fl2va_pruned.",
    )
    accelerator_profile: Optional[bool] = Field(
        default=False,
        description="Apply the LightX2V FL2V accelerator profile (LoRA; inference steps capped at 4, "
                    "lower requested step counts are preserved). "
                    "Only applies to minimax_h3_fl2va and minimax_h3_fl2va_pruned.",
    )
    first_block_cache: Optional[bool] = Field(
        default=False,
        description="Enable First Block Cache step skipping at the default 0.08 threshold. "
                    "Only applies to minimax_h3_fl2va and minimax_h3_fl2va_pruned.",
    )
    prompt_enhancer: Optional[bool] = Field(
        default=False,
        description="Enable LLM-based H3 prompt enhancement (rewrites prompt into H3's structured format with soundscape tags). "
                    "Only applies to minimax_h3_fl2va and minimax_h3_fl2va_pruned.",
    )

    def to_wgp_settings(
        self,
        image_start_path: str | None = None,
        image_end_path: str | None = None,
    ) -> dict:
        """Convert to WanGP task settings dict."""
        settings = {
            "prompt": self.prompt,
            "seed": self.seed,
            "num_inference_steps": self.num_inference_steps,
            "resolution": f"{self.width}x{self.height}",
            "batch_size": self.batch_size,
            "model_type": self.model.model_type,
            "guidance_scale": self.guidance_scale,
            "video_length": self.video_length,
            "image_mode": 0,  # Video generation mode
            "force_fps": self.fps,
            "flow_shift": 5
        }

        # Model-specific settings: MiniMax H3 FL2VA is applied differently from existing models
        if self.model in (I2VVideoModel.MINIMAX_H3_FL2VA, I2VVideoModel.MINIMAX_H3_FL2VA_PRUNED):
            # MiniMax H3 sampling defaults; euler is the only solver the H3 pipeline accepts
            settings["flow_shift"] = 12
            settings["sample_solver"] = "euler"
            settings["guidance_scale"] = 1
            settings["guidance_phases"] = 0

            # LightX2V FL2V accelerator profile (mirrors profiles/minimax_h3/Lightx2v FL2V 4 Steps.json)
            if self.accelerator_profile:
                settings.update({
                    "activated_loras": [
                        "https://huggingface.co/DeepBeepMeep/MiniMax-H3/resolve/main/loras/minimax_h3_lightx2v_ref2v_turbo_4step_alpha8_v0.1_bf16.safetensors"
                    ],
                    "loras_multipliers": "0.5",
                    "guidance_scale": 1,
                })
                # Turbo LoRA caps steps at 4; lower requested step counts are preserved
                if settings["num_inference_steps"] > 4:
                    settings["num_inference_steps"] = 4

            # First Block Cache step skipping at the upstream default 0.08 threshold
            if self.first_block_cache:
                settings["skip_steps_cache_type"] = "first_block"
                settings["skip_steps_multiplier"] = 0.08

            # LLM-based H3 prompt enhancement (rewrites into structured format with soundscape/audio tags)
            if self.prompt_enhancer:
                settings["prompt_enhancer"] = "T"

            # Pass low_quality flag through for GGUF model override (minimax_h3_fl2va_pruned)
            if self.low_quality:
                settings["low_quality"] = True
        else:
            # apply some wan2.2 settings; defaults from the UI
            if self.model == I2VVideoModel.WAN2_2_I2V_14B_ENHANCED_LIGHTNING_V2:
                settings["sample_solver"] = "unipc"
                settings["guidance_scale"] = 1
                settings["guidance2_scale"] = 1
                settings["guidance3_scale"] = 5
                settings["guidance_phases"] = 2
                settings["switch_threshold"] = 900
                settings["overlap_size"] = 5

            # Pass low_quality flag through for GGUF model override
            if self.low_quality:
                settings["low_quality"] = True

        # Build image prompt type based on which images are provided
        image_prompt_chars = ""
        if image_start_path:
            settings["image_start"] = image_start_path
            image_prompt_chars += "S"
        if image_end_path:
            settings["image_end"] = image_end_path
            image_prompt_chars += "E"
        if image_prompt_chars:
            settings["image_prompt_type"] = image_prompt_chars

        return settings


class ImageToVideoResponse(BaseModel):
    """Response model for image-to-video generation."""

    model_config = {"protected_namespaces": ()}

    status: str = Field(..., description="Generation status")
    task_id: Optional[str] = Field(default=None, description="Task ID for tracking")
    videos: Optional[list[str]] = Field(
        default=None, description="Base64 encoded generated videos"
    )
    seed_used: int = Field(..., description="Seed that was used for generation")
    model_used: str = Field(..., description="Model that was used for generation")
    steps: int = Field(..., description="Number of inference steps used")
    resolution: str = Field(..., description="Output resolution")
    batch_size: int = Field(..., description="Number of videos generated")
    video_length: int = Field(..., description="Number of frames generated")
