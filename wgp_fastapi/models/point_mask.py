"""
Pydantic models for point-mask endpoint.
"""

from pydantic import BaseModel, Field


class PointMaskResponse(BaseModel):
    """Response model for point-click mask generation."""

    model_config = {"protected_namespaces": ()}

    image_url: str = Field(..., description="URL to the generated mask image")
    maskOverlay: str = Field(
        ..., description="URL to the overlay image (original image + white mask composited on top)"
    )
