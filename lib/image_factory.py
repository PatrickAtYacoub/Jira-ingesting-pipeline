"""
Image factory for generating images from base64 encoded strings.
"""

import base64

def decode_base64_image(image_uri: str) -> bytes:
    """
    Decode a base64 encoded image string into bytes.
    Args:
        image_uri (str): The base64 encoded image string.
    """
    if "," in image_uri:
        image_uri = image_uri.split(",")[1]
    image_uri = image_uri.strip()
    image_uri += '=' * (-len(image_uri) % 4)  # Padding correction
    return base64.b64decode(image_uri)

def imagebytes_to_base64(image_bytes: bytes) -> str:
    """
    Convert image bytes to a base64 encoded string.
    Args:
        image_bytes (bytes): The image bytes to encode.
    Returns:
        str: The base64 encoded image string.
    """
    return base64.b64encode(image_bytes).decode("utf-8")