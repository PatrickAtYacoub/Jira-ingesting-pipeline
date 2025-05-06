"""
Prompting module for interacting with the OpenAI API using LangChain.
This module provides functions to send prompts to the OpenAI model and receive responses.
It also includes functionality to handle image inputs by encoding them in base64 format.
It uses the AzureChatOpenAI class from the langchain_openai package to interact with the 
OpenAI API.
"""

import base64
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from config import Config

config = Config.load_from_env()

model = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    azure_endpoint=config.openai_base_url,
    api_version=config.openai_api_version,
    model_name="gpt-4o-mini", )

def prompt(system_prompt, user_prompt):
    """
    Send a prompt to the OpenAI model and receive a response.
    Args:
        system_prompt (str): The system prompt to set the context for the model.
        user_prompt (str): The user prompt to send to the model.
        
    Returns:
        str: The response from the model.
    """
    messages = [
        (
            "system",
            system_prompt,
        ),
        ("human", user_prompt),
    ]

    res = model.invoke(messages)
    return res.content

def prompt_with_image( image_base64, user_prompt="Beschreibe dieses Bild."):
    """
    Send a prompt to the OpenAI model with an image and receive a response.
    Args:
        image_base64 (bytes): The image in base64 format.
        user_prompt (str): The user prompt to send to the model.

    Returns:
        str: The response from the model.
    """
    image_encoding =  base64.b64encode(image_base64).decode("utf-8")
    message = HumanMessage(
        content=[
            {"type": "text", "text": user_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_encoding}"},
            },
        ]
    )
    return model.invoke([message]).content
