"""Ollama API client for calling the company's Ollama server."""

import requests


def call_api(model: str, sys_prompt: str, usr_prompt: str, temperature: float = 0.3) -> str:
    """Call the company API server to generate a response.
    
    Args:
        sys_prompt: The system prompt to send to the model
        usr_prompt: The user prompt to send to the model
        temperature: Temperature parameter for generation
        
    Returns:
        The generated response text
        
    Raises:
        requests.RequestException: If the API call fails
    """
    payload = {
        "model": model,
        "system": sys_prompt,
        "prompt": usr_prompt,
        "temperature": temperature,
        "stream": False
    }
    
    API_ENDPOINT = "http://10.248.36.193:11434/api/generate"
    response = requests.post(API_ENDPOINT, json=payload)
    response.raise_for_status()
    
    result = response.json()
    return result.get("response", "")
