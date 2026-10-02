from typing import Optional

from pydantic import BaseModel


class NsfwTextRequest(BaseModel):
    """Request body for the text NSFW check."""
    text: str


class NsfwTextResponse(BaseModel):
    """Response for the text NSFW check."""
    nsfw: bool


class NsfwImageResponse(BaseModel):
    """Response for the image NSFW check."""
    nsfw: bool
    blurred_image: Optional[str] = None  # base64 data URL, only present when nsfw=True
