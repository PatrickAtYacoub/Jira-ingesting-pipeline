"""
This module provides a function to send HTTP requests with authentication.
It uses JWT (JSON Web Token) for authentication and allows for both GET and POST requests.
It also includes a function to generate a URL with query parameters for the request.
"""

import urllib.parse
import time
import requests
import jwt
from cryptography.hazmat.primitives import serialization


def send_request(url, asset, user, file=None):
    """
    Send a GET or POST request to the specified URL with authentication.
    If a file is provided, a POST request is sent; otherwise, a GET request is sent.
    The URL is generated using the provided asset and user information.
    
    Args:
        url (str): The base URL to send the request to.
        asset (str): The asset identifier to include in the URL.
        user (str): The username for authentication.
        file (str, optional): The path to the file to be sent in a POST request.
        Defaults to None.
        
        Returns:
            requests.Response: The response object from the request.
    """
    def generate_url(url, asset, user, **kwargs):
        def load_key(path, password=None):
            return serialization.load_ssh_private_key(open(path, "rb").read(), password)

        def sign_jwt(user, key):
            return jwt.encode(
                {"username": user, "timestamp": str(time.time())},
                key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ).decode(),
                algorithm="EdDSA",
            )

        key = load_key(f"credentials/{user}")
        token = urllib.parse.quote(sign_jwt(user, key))
        url += ("?" if "?" not in url else "&") + f"asset={asset}&html=1&user={user}"
        url += "".join(f"&{k}={urllib.parse.quote(v)}" for k, v in kwargs.items())
        return f"{url}&auth={token}"

    files = {"file": open(file, "rb")} if file else None
    return (
        requests.post(generate_url(url, asset, user), files=files, timeout=10)
        if file
        else requests.get(generate_url(url, asset, user), timeout=10)
    )
