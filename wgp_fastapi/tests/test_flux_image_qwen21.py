"""Smallest check that the qwen 2.1 i2i wiring in flux_image.py stays correct."""
from wgp_fastapi.models.flux_image import FluxImageModel, FluxImageRequest


def test_qwen21_is_routed_as_an_image_edit_model():
    m = FluxImageModel.QWEN_IMAGE_21
    assert m.model_type == "qwen_image_21_7B"
    assert m.is_image_edit
    assert m.is_qwen21


def test_qwen21_keeps_base_guidance_and_prompt_type():
    s = FluxImageRequest(
        prompt="make it night", seed=1, num_inference_steps=40,
        width=1024, height=1024, model=FluxImageModel.QWEN_IMAGE_21,
    ).to_wgp_settings()
    assert s["model_type"] == "qwen_image_21_7B"
    assert s["image_prompt_type"] == "KI"
    assert s["guidance_scale"] == 1           # CFG off: 4x blows the latents out (black image)
    assert s["activated_loras"] == []         # no LoRA on the base path


def test_qwen21_low_quality_uses_viggle_lora_not_the_20b_model():
    s = FluxImageRequest(
        prompt="make it night", seed=1, num_inference_steps=40,
        width=1024, height=1024, model=FluxImageModel.QWEN_IMAGE_21, low_quality=True,
    ).to_wgp_settings()
    assert s["model_type"] == "qwen_image_21_7B"
    assert s["num_inference_steps"] == 6
    assert s["sample_solver"] == "viggle_v02"
    assert s["guidance_scale"] == 1
    assert "viggle-turbo-v0.2.1" in s["activated_loras"][0]


def test_qwen21_mask_path_matches_other_edit_models():
    s = FluxImageRequest(
        prompt="blue sky", seed=1, num_inference_steps=40, width=1024, height=1024,
        model=FluxImageModel.QWEN_IMAGE_21, mask_path="/tmp/m.png",
    ).to_wgp_settings(image_start_path="/tmp/i.png")
    assert s["video_prompt_type"] == "VAGIK"
    assert s["model_mode"] == 0
    assert s["image_guide"] == ["/tmp/i.png"]
    assert s["image_refs"] == ["/tmp/i.png"]


def test_other_edit_models_are_unchanged():
    s = FluxImageRequest(
        prompt="add a hat", seed=1, num_inference_steps=4, width=1024, height=1024,
        model=FluxImageModel.IMAGE_EDIT_PLUS_2511, low_quality=True,
    ).to_wgp_settings()
    assert s["model_type"] == "qwen_image_edit_plus2_20B"
    assert s["num_inference_steps"] == 4
    assert "Lightning-4steps" in s["activated_loras"][0]


def test_caller_supplied_loras_reach_the_task():
    s = FluxImageRequest(
        prompt="anime style", seed=1, num_inference_steps=6, width=768, height=1024,
        model=FluxImageModel.QWEN_IMAGE_21,
        activated_loras="a.safetensors,https://x.co/b.safetensors",
    ).to_wgp_settings()
    assert s["activated_loras"] == ["a.safetensors", "https://x.co/b.safetensors"]
    assert s["loras_multipliers"] == "1"


def test_flux_klein_defaults_keep_their_multipliers():
    s = FluxImageRequest(
        prompt="a cat", seed=1, num_inference_steps=4, width=1024, height=1024,
        model=FluxImageModel.FLUX_2_KLEIN,
    ).to_wgp_settings()
    assert s["activated_loras"] == [
        "improved_klein.safetensors",
        "Flux2-Klein-9B-consistency-V2.safetensors",
    ]
    assert s["loras_multipliers"] == ["1.0", "0.5"]
