from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# Mapping from API model IDs to WanGP model_type strings
V2V_MODEL_TYPE_MAP = {
    "bernini_14b": "bernini",
    "bernini_1_3b": "bernini_1.3B",
}


class V2VModel(str, Enum):
    """Supported models for video-to-video generation (Bernini)."""
    BERNINI_14B = "bernini_14b"
    BERNINI_1_3B = "bernini_1_3b"

    @property
    def model_type(self) -> str:
        """Get the WanGP model_type string for this model."""
        return V2V_MODEL_TYPE_MAP.get(self.value, self.value)


class V2VLoRA(str, Enum):
    """Optional LoRA accelerator presets for v2v generation."""
    CAUSVID_RANK32_8_STEPS = "causvid_rank32_8_steps"
    LIGHTNING_V2025_10_14_2_PHASES_4_STEPS = "lightning_v2025_10_14_2_phases_4_steps"
    LIGHTNING_V2025_10_14_3_PHASES_8_STEPS = "lightning_v2025_10_14_3_phases_8_steps"
    LIGHTNING_V1_0_2_PHASES_4_STEPS = "lightning_v1_0_2_phases_4_steps"
    LIGHTNING_V1_0_3_PHASES_8_STEPS = "lightning_v1_0_3_phases_8_steps"

    @property
    def display_name(self) -> str:
        return {
            V2VLoRA.CAUSVID_RANK32_8_STEPS: "Causvid Rank32 - 8 Steps",
            V2VLoRA.LIGHTNING_V2025_10_14_2_PHASES_4_STEPS: "Lightning i2v v2025-10-14 2 Phases - 4 Steps",
            V2VLoRA.LIGHTNING_V2025_10_14_3_PHASES_8_STEPS: "Lightning i2v v2025-10-14 3 Phases - 8 Steps",
            V2VLoRA.LIGHTNING_V1_0_2_PHASES_4_STEPS: "Lightning i2v v1.0 2 Phases - 4 Steps",
            V2VLoRA.LIGHTNING_V1_0_3_PHASES_8_STEPS: "Lightning i2v v1.0 3 Phases - 8 Steps",
        }[self]

    def to_profile_settings(self) -> dict:
        """Get the WanGP settings overrides for this LoRA preset."""
        profiles = {
            V2VLoRA.CAUSVID_RANK32_8_STEPS: {
                "num_inference_steps": 8,
                "guidance_phases": 1,
                "guidance_scale": 1,
                "sample_solver": "causvid",
                "flow_shift": 2,
                "activated_loras": [
                    "https://huggingface.co/DeepBeepMeep/Wan2.1/resolve/main/loras_accelerators/Wan21_CausVid_bidirect2_T2V_1_3B_lora_rank32.safetensors"
                ],
                "loras_multipliers": "1",
            },
            V2VLoRA.LIGHTNING_V2025_10_14_2_PHASES_4_STEPS: {
                "num_inference_steps": 4,
                "guidance_scale": 1,
                "guidance2_scale": 1,
                "switch_threshold": 876,
                "model_switch_phase": 1,
                "guidance_phases": 2,
                "flow_shift": 5,
                "sample_solver": "euler",
                "loras_multipliers": "1;0 0;1",
                "activated_loras": [
                    "https://huggingface.co/DeepBeepMeep/Wan2.2/resolve/main/loras_accelerators/Wan2.2_I2V_A14B_HIGH_lightx2v_MoE_distill_lora_rank_64_bf16.safetensors",
                    "https://huggingface.co/DeepBeepMeep/Wan2.2/resolve/main/loras_accelerators/Wan2.2_I2V_A14B_LOW_4steps_lora_rank64_Seko_V1_forKJ.safetensors",
                ],
            },
            V2VLoRA.LIGHTNING_V2025_10_14_3_PHASES_8_STEPS: {
                "num_inference_steps": 8,
                "guidance_scale": 3.5,
                "guidance2_scale": 1,
                "guidance3_scale": 1,
                "switch_threshold": 985,
                "switch_threshold2": 800,
                "guidance_phases": 3,
                "model_switch_phase": 2,
                "flow_shift": 5,
                "sample_solver": "euler",
                "activated_loras": [
                    "https://huggingface.co/DeepBeepMeep/Wan2.2/resolve/main/loras_accelerators/Wan2.2_I2V_A14B_HIGH_lightx2v_MoE_distill_lora_rank_64_bf16.safetensors",
                    "https://huggingface.co/DeepBeepMeep/Wan2.2/resolve/main/loras_accelerators/Wan2.2_I2V_A14B_LOW_4steps_lora_rank64_Seko_V1_forKJ.safetensors",
                ],
                "loras_multipliers": "0;1;0 0;0;1",
            },
            V2VLoRA.LIGHTNING_V1_0_2_PHASES_4_STEPS: {
                "num_inference_steps": 4,
                "guidance_scale": 1,
                "guidance2_scale": 1,
                "switch_threshold": 876,
                "model_switch_phase": 1,
                "guidance_phases": 2,
                "flow_shift": 3,
                "sample_solver": "euler",
                "loras_multipliers": "1;0 0;1",
                "activated_loras": [
                    "https://huggingface.co/DeepBeepMeep/Wan2.2/resolve/main/loras_accelerators/Wan2.2_I2V_A14B_HIGH_4steps_lora_rank64_Seko_V1_forKJ.safetensors",
                    "https://huggingface.co/DeepBeepMeep/Wan2.2/resolve/main/loras_accelerators/Wan2.2_I2V_A14B_LOW_4steps_lora_rank64_Seko_V1_forKJ.safetensors",
                ],
            },
            V2VLoRA.LIGHTNING_V1_0_3_PHASES_8_STEPS: {
                "num_inference_steps": 8,
                "guidance_scale": 3.5,
                "guidance2_scale": 1,
                "guidance3_scale": 1,
                "switch_threshold": 965,
                "switch_threshold2": 800,
                "guidance_phases": 3,
                "model_switch_phase": 2,
                "flow_shift": 3,
                "sample_solver": "euler",
                "activated_loras": [
                    "https://huggingface.co/DeepBeepMeep/Wan2.2/resolve/main/loras_accelerators/Wan2.2_I2V_A14B_HIGH_4steps_lora_rank64_Seko_V1_forKJ.safetensors",
                    "https://huggingface.co/DeepBeepMeep/Wan2.2/resolve/main/loras_accelerators/Wan2.2_I2V_A14B_LOW_4steps_lora_rank64_Seko_V1_forKJ.safetensors",
                ],
                "loras_multipliers": "0;1;0 0;0;1",
            },
        }
        return profiles[self]


class VideoToVideoRequest(BaseModel):
    """Request model for video-to-video generation using Bernini models."""

    prompt: str
    seed: int
    num_inference_steps: int
    width: int
    height: int
    batch_size: int
    model: V2VModel
    video_length: int
    guidance_scale: float
    fps: int
    lora: Optional[V2VLoRA] = None

    def to_wgp_settings(
        self,
        video_path: str | None = None,
        image_ref_path: str | None = None,
    ) -> dict:
        """Convert to WanGP task settings dict."""
        # Bernini defaults
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
            "flow_shift": 5,
            "video_prompt_type": "V",
            "sample_solver": "unipc",
            "control_net_weight": 1.25,
            "alt_guidance_scale": 4.5,
            "remove_background_images_ref": 0,
            "prompt_enhancer": "",
        }

        # Model-specific Bernini defaults
        if self.model == V2VModel.BERNINI_14B:
            settings["guidance_phases"] = 2
            settings["model_switch_phase"] = 1
            settings["switch_threshold"] = 875
            settings["guidance2_scale"] = 4
        else:
            settings["guidance_phases"] = 1
            settings["switch_threshold"] = 0

        # Apply LoRA preset overrides
        if self.lora is not None:
            settings.update(self.lora.to_profile_settings())

        # Video input (required for v2v)
        if video_path:
            settings["video_guide"] = video_path

        # Optional reference image
        if image_ref_path:
            settings["image_refs"] = [image_ref_path]
            settings["video_prompt_type"] = "VI"

        return settings


class VideoToVideoResponse(BaseModel):
    """Response model for video-to-video generation."""

    model_config = {"protected_namespaces": ()}

    status: str = Field(..., description="Generation status")
    task_id: Optional[str] = Field(default=None, description="Task ID for tracking")
    videos: Optional[list[str]] = Field(
        default=None, description="URLs to generated videos"
    )
    seed_used: int = Field(..., description="Seed that was used for generation")
    model_used: str = Field(..., description="Model that was used for generation")
    steps: int = Field(..., description="Number of inference steps used")
    resolution: str = Field(..., description="Output resolution")
    batch_size: int = Field(..., description="Number of videos generated")
    video_length: int = Field(..., description="Number of frames generated")
