#!/usr/bin/env python3
"""
Enhanced AI Backends for File Organization

This module provides improved AI backend integration with:
- Better error handling and retry logic
- Enhanced prompt optimization
- Improved response validation
- Context-aware querying
"""

import requests
import json
import time
import re
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

# Request timeouts
OLLAMA_TIMEOUT = 30
API_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# Common model configurations
MODEL_CONFIGS = {
    "ollama": {
        "llama3.1": {"temperature": 0.1, "top_p": 0.9, "top_k": 40},
        "llama3.2": {"temperature": 0.1, "top_p": 0.9, "top_k": 40},
        "codellama": {"temperature": 0.05, "top_p": 0.95, "top_k": 50},
        "mistral": {"temperature": 0.1, "top_p": 0.9, "top_k": 40},
        "deepseek": {"temperature": 0.1, "top_p": 0.9, "top_k": 40}
    },
    "openai": {
        "gpt-4o-mini": {"temperature": 0.1, "max_tokens": 50},
        "gpt-4o": {"temperature": 0.1, "max_tokens": 50},
        "gpt-3.5-turbo": {"temperature": 0.1, "max_tokens": 50}
    },
    "grok": {
        "grok-2-mini": {"temperature": 0.1, "max_tokens": 50},
        "grok-beta": {"temperature": 0.1, "max_tokens": 50}
    }
}

def list_ollama_models() -> List[str]:
    """Get list of available Ollama models with enhanced error handling"""
    try:
        url = "http://localhost:11434/api/tags"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        models = data.get("models", [])
        model_names = []
        
        for model in models:
            if "name" in model:
                model_names.append(model["name"])
        
        return sorted(model_names)
        
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to Ollama. Make sure Ollama is running on localhost:11434")
        return []
    except requests.exceptions.Timeout:
        print("Error: Timeout connecting to Ollama")
        return []
    except Exception as e:
        print(f"Error listing Ollama models: {e}")
        return []

def query_ollama(model: str, prompt: str, **kwargs) -> str:
    """Query Ollama model with enhanced configuration and error handling"""
    try:
        url = "http://localhost:11434/api/generate"
        
        # Get model-specific configuration
        config = MODEL_CONFIGS.get("ollama", {}).get(model, {})
        config.update(kwargs)
        
        # Optimized parameters for file organization
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.get("temperature", 0.1),
                "top_p": config.get("top_p", 0.9),
                "top_k": config.get("top_k", 40),
                "num_predict": config.get("num_predict", 50),
                "stop": config.get("stop", ["\n\n", "Path:", "Folder:", "Directory:", "Response:"]),
                "num_ctx": config.get("num_ctx", 2048)
            }
        }
        
        response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "").strip()
        
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama"
    except requests.exceptions.Timeout:
        return "Error: Ollama request timeout"
    except Exception as e:
        return f"Error: {str(e)}"

def query_openai(model: str, prompt: str, api_key: str, **kwargs) -> str:
    """Query OpenAI API with enhanced configuration and error handling"""
    try:
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Get model-specific configuration
        config = MODEL_CONFIGS.get("openai", {}).get(model, {})
        config.update(kwargs)
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a file organization expert. Respond only with folder paths for organizing files."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": config.get("max_tokens", 50),
            "temperature": config.get("temperature", 0.1),
            "stop": config.get("stop", ["\n\n", "Path:", "Folder:", "Response:"])
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            return content.strip()
        else:
            return "Error: No response from OpenAI"
            
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_message = error_data.get('error', {}).get('message', str(e))
                return f"OpenAI Error: {error_message}"
            except:
                return f"OpenAI Error: {e.response.status_code}"
        return f"OpenAI Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def query_grok(model: str, prompt: str, api_key: str, **kwargs) -> str:
    """Query Grok API (xAI) with enhanced configuration and error handling"""
    try:
        url = "https://api.x.ai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Get model-specific configuration
        config = MODEL_CONFIGS.get("grok", {}).get(model, {})
        config.update(kwargs)
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a file organization assistant. Provide only folder paths for file organization."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": config.get("max_tokens", 50),
            "temperature": config.get("temperature", 0.1),
            "stop": config.get("stop", ["\n\n", "Path:", "Folder:", "Response:"])
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            return content.strip()
        else:
            return "Error: No response from Grok"
            
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_message = error_data.get('error', {}).get('message', str(e))
                return f"Grok Error: {error_message}"
            except:
                return f"Grok Error: {e.response.status_code}"
        return f"Grok Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def test_ai_connection(backend: str, model: str, api_key: str = "") -> Tuple[bool, str]:
    """Test connection to AI backend with enhanced error reporting"""
    test_prompt = "Organize a file named 'test.txt' containing 'Hello World'. Respond with only the folder path."
    
    try:
        if backend == "Local (Ollama)":
            if not model:
                return False, "No model specified"
            
            # First check if Ollama is running
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                response.raise_for_status()
            except:
                return False, "Ollama is not running or not accessible"
            
            # Test with a simple query
            result = query_ollama(model, test_prompt)
            if result.startswith("Error:"):
                return False, result
            return True, f"Connected to {model}"
            
        elif backend == "OpenAI":
            if not api_key or not model:
                return False, "API key and model required"
            
            result = query_openai(model, test_prompt, api_key)
            if result.startswith("OpenAI Error:") or result.startswith("Error:"):
                return False, result
            return True, f"Connected to {model}"
            
        elif backend == "Grok":
            if not api_key or not model:
                return False, "API key and model required"
                
            result = query_grok(model, test_prompt, api_key)
            if result.startswith("Grok Error:") or result.startswith("Error:"):
                return False, result
            return True, f"Connected to {model}"
        
        return False, f"Unknown backend: {backend}"
        
    except Exception as e:
        return False, f"Connection test error: {e}"

def get_model_info(backend: str, model: str) -> Dict[str, Any]:
    """Get detailed information about a specific model"""
    info = {
        "backend": backend,
        "model": model,
        "available": False,
        "description": "Unknown model",
        "capabilities": [],
        "recommended_for": []
    }
    
    try:
        if backend == "Local (Ollama)":
            # Check if model exists in Ollama
            models = list_ollama_models()
            if model in models:
                info["available"] = True
                info["description"] = f"Local Ollama model: {model}"
                
                # Model-specific recommendations
                if "llama" in model.lower():
                    info["capabilities"] = ["general", "code", "organization"]
                    info["recommended_for"] = ["file organization", "code projects"]
                elif "code" in model.lower():
                    info["capabilities"] = ["code", "technical"]
                    info["recommended_for"] = ["software projects", "code organization"]
                elif "mistral" in model.lower():
                    info["capabilities"] = ["general", "efficient"]
                    info["recommended_for"] = ["general organization", "mixed content"]
        
        elif backend == "OpenAI":
            # Common OpenAI models
            openai_models = {
                "gpt-3.5-turbo": {
                    "description": "GPT-3.5 Turbo - Fast and efficient",
                    "capabilities": ["general", "fast"],
                    "recommended_for": ["quick organization", "general files"]
                },
                "gpt-4o-mini": {
                    "description": "GPT-4o Mini - Good balance of speed and capability",
                    "capabilities": ["general", "balanced"],
                    "recommended_for": ["balanced organization", "mixed projects"]
                },
                "gpt-4o": {
                    "description": "GPT-4o - Most capable model",
                    "capabilities": ["general", "advanced", "context-aware"],
                    "recommended_for": ["complex organization", "project structure"]
                }
            }
            
            if model in openai_models:
                info["available"] = True
                info.update(openai_models[model])
        
        elif backend == "Grok":
            # Grok models
            grok_models = {
                "grok-beta": {
                    "description": "Grok Beta - xAI's conversational AI",
                    "capabilities": ["general", "conversational"],
                    "recommended_for": ["general organization", "natural language"]
                },
                "grok-2-mini": {
                    "description": "Grok 2 Mini - Efficient Grok model",
                    "capabilities": ["general", "efficient"],
                    "recommended_for": ["quick organization", "general files"]
                }
            }
            
            if model in grok_models:
                info["available"] = True
                info.update(grok_models[model])
    
    except Exception as e:
        print(f"Error getting model info: {e}")
    
    return info

def optimize_prompt_for_backend(backend: str, base_prompt: str, context: Dict[str, Any] = None) -> str:
    """Optimize prompt based on the AI backend and context"""
    if backend == "Local (Ollama)":
        # Ollama works well with direct, simple prompts
        optimized = base_prompt + "\n\nRespond with only the folder path:"
        
        # Add context if available
        if context and context.get("project_type"):
            optimized += f"\n\nProject type: {context['project_type']}"
        
        return optimized
    
    elif backend == "OpenAI":
        # OpenAI benefits from structured prompts
        optimized = f"""As a file organization expert, determine the best folder structure for this file.

{base_prompt}

Rules:
- Respond with ONLY the folder path
- Use forward slashes (/)
- Be specific but concise
- If uncertain, use "Uncategorized"

Folder path:"""
        
        # Add context if available
        if context:
            if context.get("project_type"):
                optimized += f"\n\nProject context: {context['project_type']}"
            if context.get("existing_structure"):
                optimized += f"\n\nExisting structure: {context['existing_structure']}"
        
        return optimized
    
    elif backend == "Grok":
        # Grok tends to be more conversational, so be explicit
        optimized = f"""File organization task:

{base_prompt}

Important: Respond with ONLY the folder path where this file should go. Nothing else.

Folder path:"""
        
        # Add context if available
        if context and context.get("project_type"):
            optimized += f"\n\nProject context: {context['project_type']}"
        
        return optimized
    
    return base_prompt

def with_retry(func, max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Execute function with retry logic and exponential backoff"""
    for attempt in range(max_retries + 1):
        try:
            result = func()
            if not result.startswith("Error:"):
                return result
        except Exception as e:
            if attempt == max_retries:
                return f"Error after {max_retries + 1} attempts: {str(e)}"
        
        if attempt < max_retries:
            # Exponential backoff
            sleep_time = delay * (2 ** attempt)
            time.sleep(sleep_time)
    
    return "Error: Max retries exceeded"

def validate_folder_path(path: str) -> str:
    """Validate and clean folder path with enhanced validation"""
    if not path or path.lower() in ['error', 'none', 'null', 'undefined']:
        return "Uncategorized"
    
    # Clean the path
    path = path.strip().strip('"\'`')
    path = path.replace('\\', '/')
    path = path.strip('/')
    
    # Remove invalid characters
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        path = path.replace(char, '')
    
    # Remove common unwanted prefixes
    unwanted_prefixes = ['the path is', 'the folder is', 'suggested path:', 'folder path:', 'path:']
    for prefix in unwanted_prefixes:
        if path.lower().startswith(prefix.lower()):
            path = path[len(prefix):].strip()
    
    # Limit path length and depth
    if len(path) > 100:
        parts = path.split('/')
        if len(parts) > 1:
            path = '/'.join(parts[:3])  # Keep first 3 parts
        else:
            path = path[:100]
    
    # Ensure it's not empty after cleaning
    if not path or path.isspace():
        return "Uncategorized"
    
    return path

def extract_path_from_response(response: str) -> str:
    """Extract folder path from AI response with enhanced parsing"""
    if not response:
        return "Uncategorized"
    
    # Try JSON extraction first
    json_match = re.search(r'{\s*"path"\s*:\s*"([^"]+)"}', response, flags=re.IGNORECASE)
    if json_match:
        return validate_folder_path(json_match.group(1))
    
    # Remove code blocks and formatting
    response = re.sub(r"```.*?```", "", response, flags=re.DOTALL)
    response = re.sub(r"<.*?>", "", response, flags=re.DOTALL)
    response = re.sub(r"^#+\s.*$", "", response, flags=re.MULTILINE)
    
    # Remove common prose phrases
    prose_patterns = [
        r"\b(the cleaned compact path would be|the path would be|the best path is|final path:)\b.*",
        r"\b(this file should go in|this belongs in|organize this as)\b.*",
        r"\b(suggested organization|recommended location)\b.*"
    ]
    
    for pattern in prose_patterns:
        response = re.sub(pattern, "", response, flags=re.IGNORECASE)
    
    # Look for path-like patterns
    path_patterns = [
        r"([A-Za-z0-9 _.-]+(?:/[A-Za-z0-9 _.-]+){0,2})",  # Basic path
        r"([A-Za-z][A-Za-z0-9_-]*(?:/[A-Za-z][A-Za-z0-9_-]*){0,2})",  # More structured
    ]
    
    for pattern in path_patterns:
        matches = re.findall(pattern, response)
        if matches:
            # Score and select the best match
            best_match = None
            best_score = -1
            
            for match in matches:
                score = _score_path_candidate(match)
                if score > best_score:
                    best_score = score
                    best_match = match
            
            if best_match:
                return validate_folder_path(best_match)
    
    # Fallback: try to extract any reasonable path
    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        if '/' in line and len(line) < 50:
            cleaned = validate_folder_path(line)
            if cleaned != "Uncategorized":
                return cleaned
    
    return "Uncategorized"

def _score_path_candidate(candidate: str) -> int:
    """Score a path candidate for quality"""
    score = 0
    
    # Prefer paths with forward slashes
    if '/' in candidate:
        score += 10
    
    # Prefer shorter paths
    score += max(0, 20 - len(candidate))
    
    # Penalize paths with too many words
    word_count = len(candidate.split())
    if word_count > 6:
        score -= (word_count - 6) * 2
    
    # Penalize paths with common prose words
    prose_words = ['is', 'are', 'the', 'this', 'that', 'here', 'would', 'should', 'could']
    for word in prose_words:
        if word in candidate.lower():
            score -= 2
    
    # Bonus for structured paths
    if re.match(r'^[A-Za-z][A-Za-z0-9_-]*(?:/[A-Za-z][A-Za-z0-9_-]*)*$', candidate):
        score += 5
    
    return score

def get_backend_status(backend: str, model: str = "", api_key: str = "") -> Dict[str, Any]:
    """Get comprehensive status information for a backend"""
    status = {
        "backend": backend,
        "available": False,
        "models": [],
        "error": None,
        "recommendations": []
    }
    
    try:
        if backend == "Local (Ollama)":
            models = list_ollama_models()
            status["available"] = len(models) > 0
            status["models"] = models
            
            if not status["available"]:
                status["error"] = "Ollama not running or no models available"
                status["recommendations"] = [
                    "Start Ollama service",
                    "Install models with: ollama pull llama3.1"
                ]
            else:
                status["recommendations"] = [
                    f"Use {models[0]} for general organization",
                    "Consider codellama for code projects"
                ]
        
        elif backend == "OpenAI":
            if not api_key:
                status["error"] = "API key required"
                status["recommendations"] = ["Add your OpenAI API key"]
            else:
                # Test with a simple query
                test_result = query_openai("gpt-4o-mini", "test", api_key)
                status["available"] = not test_result.startswith("Error:")
                
                if status["available"]:
                    status["models"] = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
                    status["recommendations"] = [
                        "Use gpt-4o-mini for cost-effective organization",
                        "Use gpt-4o for complex project structures"
                    ]
                else:
                    status["error"] = test_result
                    status["recommendations"] = ["Check your API key", "Verify OpenAI service status"]
        
        elif backend == "Grok":
            if not api_key:
                status["error"] = "API key required"
                status["recommendations"] = ["Add your Grok API key"]
            else:
                # Test with a simple query
                test_result = query_grok("grok-2-mini", "test", api_key)
                status["available"] = not test_result.startswith("Error:")
                
                if status["available"]:
                    status["models"] = ["grok-2-mini", "grok-beta"]
                    status["recommendations"] = [
                        "Use grok-2-mini for efficient organization",
                        "Use grok-beta for advanced features"
                    ]
                else:
                    status["error"] = test_result
                    status["recommendations"] = ["Check your API key", "Verify Grok service status"]
    
    except Exception as e:
        status["error"] = str(e)
        status["recommendations"] = ["Check network connection", "Verify service availability"]
    
    return status