import requests
import json
import time
from typing import List, Optional, Dict, Set
from pathlib import Path

# Request timeouts
OLLAMA_TIMEOUT = 30
API_TIMEOUT = 60

def list_ollama_models() -> List[str]:
    """Get list of available Ollama models"""
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

def analyze_folder_structure(folder_path: Path) -> Dict[str, any]:
    """Analyze the existing folder structure to understand organization patterns"""
    structure = {
        "existing_folders": set(),
        "folder_patterns": {},
        "file_types_by_folder": {},
        "common_extensions": set(),
        "depth_info": {"max_depth": 0, "common_depth": 1}
    }
    
    try:
        # Collect existing folders and their contents
        for root, dirs, files in folder_path.walk():
            relative_root = root.relative_to(folder_path)
            depth = len(relative_root.parts) if relative_root != Path('.') else 0
            structure["depth_info"]["max_depth"] = max(structure["depth_info"]["max_depth"], depth)
            
            # Add folder names
            for d in dirs:
                folder_name = d.lower()
                structure["existing_folders"].add(folder_name)
                
            # Analyze files in this directory
            if files:
                folder_key = str(relative_root) if relative_root != Path('.') else "root"
                structure["file_types_by_folder"][folder_key] = []
                
                for f in files:
                    file_path = Path(f)
                    ext = file_path.suffix.lower()
                    if ext:
                        structure["common_extensions"].add(ext)
                        structure["file_types_by_folder"][folder_key].append(ext)
                        
        # Identify common folder patterns
        common_folders = {
            "documents": ["documents", "docs", "papers", "files", "pdfs"],
            "images": ["images", "photos", "pictures", "pics", "img"],
            "videos": ["videos", "movies", "clips", "media"],
            "audio": ["audio", "music", "sounds", "mp3s"],
            "archives": ["archives", "compressed", "zip", "backups"],
            "code": ["code", "src", "source", "projects", "dev"],
            "data": ["data", "datasets", "csv", "json"],
            "temp": ["temp", "tmp", "temporary", "cache"]
        }
        
        for category, patterns in common_folders.items():
            for pattern in patterns:
                if pattern in structure["existing_folders"]:
                    if category not in structure["folder_patterns"]:
                        structure["folder_patterns"][category] = []
                    structure["folder_patterns"][category].append(pattern)
                    
    except Exception as e:
        print(f"Error analyzing folder structure: {e}")
        
    return structure

def build_context_prompt(file_path: Path, hint: str, folder_structure: Dict[str, any], root_name: str) -> str:
    """Build a context-aware prompt that includes folder structure information"""
    
    # Extract relevant information
    existing_folders = list(folder_structure.get("existing_folders", []))[:20]  # Limit to avoid prompt bloat
    folder_patterns = folder_structure.get("folder_patterns", {})
    common_extensions = folder_structure.get("common_extensions", set())
    
    # Build context string
    context_parts = []
    
    if existing_folders:
        context_parts.append(f"Existing folders: {', '.join(sorted(existing_folders))}")
    
    if folder_patterns:
        pattern_info = []
        for category, folders in folder_patterns.items():
            pattern_info.append(f"{category}: {', '.join(folders)}")
        context_parts.append(f"Folder patterns: {'; '.join(pattern_info)}")
    
    # File extension context
    file_ext = file_path.suffix.lower()
    if file_ext in common_extensions:
        context_parts.append(f"Similar files ({file_ext}) already exist in this structure")
    
    context_str = " | ".join(context_parts) if context_parts else "No existing structure"
    
    return f"""File to organize: {file_path.name}
File info: {hint}
Target folder context: {context_str}
Root folder: {root_name}

Provide a folder path (1-3 levels max) that fits the existing organization pattern.
Use existing folder names when appropriate, or create logical new ones.
Format: ParentFolder/SubFolder (use forward slashes, no extra text)"""

def query_ollama(model: str, prompt: str) -> str:
    """Query Ollama model with enhanced error handling"""
    try:
        url = "http://localhost:11434/api/generate"
        
        # Optimized parameters for file organization
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,  # Slightly higher for some creativity
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 100,  # Allow more tokens for better responses
                "stop": ["\n\n", "Explanation:", "Note:", "Path:", "Folder:", "Directory:", "Answer:"],
                "num_ctx": 4096  # Larger context window
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

def query_openai(api_key: str, model: str, prompt: str) -> str:
    """Query OpenAI API with enhanced prompting"""
    try:
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = """You are an expert file organizer. Your task is to suggest folder paths that fit existing organizational patterns.

Rules:
1. Return ONLY the folder path (e.g., "Documents/Reports" or "Media/Images")
2. Use existing folder names when they make sense
3. Create logical new folders if needed
4. Maximum 3 levels deep
5. Use forward slashes, no extra text or explanations
6. If uncertain, prefer broader categories over specific ones"""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.2,
            "stop": ["\n\n", "Explanation:", "Note:"]
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

def query_grok(api_key: str, model: str, prompt: str) -> str:
    """Query Grok API (xAI) with enhanced prompting"""
    try:
        url = "https://api.x.ai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = """You are a file organization expert. Analyze the file and existing folder structure to suggest the best organization path.

Important guidelines:
- Return ONLY the folder path (no explanations)
- Respect existing folder naming patterns
- Use forward slashes for path separation
- Maximum 3 folder levels
- Be consistent with similar file types"""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.2,
            "stop": ["\n\n", "Explanation:", "Note:"]
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

def test_ai_connection(backend: str, model: str, api_key: str = "") -> tuple[bool, str]:
    """Test connection to AI backend"""
    test_prompt = "File to organize: test.txt\nFile info: Type=Doc; Name=test.txt\nTarget folder context: documents, images, data\nRoot folder: MyProject\n\nProvide a folder path for this file."
    
    try:
        if backend == "Local (Ollama)":
            if not model:
                return False, "No model selected"
            
            # First check if Ollama is running
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                response.raise_for_status()
            except:
                return False, "Cannot connect to Ollama server"
            
            # Test with a simple query
            result = query_ollama(model, test_prompt)
            if result.startswith("Error:"):
                return False, result
            return True, f"Connected successfully. Test response: {result[:50]}..."
            
        elif backend == "OpenAI":
            if not api_key or not model:
                return False, "API key and model required"
            
            result = query_openai(api_key, model, test_prompt)
            if result.startswith("OpenAI Error:") or result.startswith("Error:"):
                return False, result
            return True, f"Connected successfully. Test response: {result[:50]}..."
            
        elif backend == "Grok":
            if not api_key or not model:
                return False, "API key and model required"
                
            result = query_grok(api_key, model, test_prompt)
            if result.startswith("Grok Error:") or result.startswith("Error:"):
                return False, result
            return True, f"Connected successfully. Test response: {result[:50]}..."
        
        return False, "Unknown backend"
        
    except Exception as e:
        return False, f"Connection test error: {e}"

def extract_clean_path(ai_response: str, fallback: str = "Uncategorized") -> str:
    """Extract and clean the folder path from AI response with improved parsing"""
    if not ai_response or ai_response.startswith("Error"):
        return fallback
    
    # Clean the response
    text = ai_response.strip()
    
    # Remove common prefixes that AI might add
    prefixes_to_remove = [
        "folder path:", "path:", "suggested path:", "organize in:", 
        "move to:", "location:", "destination:", "folder:", "directory:",
        "answer:", "result:", "output:"
    ]
    
    for prefix in prefixes_to_remove:
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()
    
    # Take only the first line to avoid explanations
    text = text.split('\n')[0].strip()
    
    # Remove quotes and other wrapper characters
    text = text.strip('"\'`()[]{}')
    
    # Clean path separators
    text = text.replace('\\', '/').strip('/')
    
    # Remove invalid characters for folder names
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        text = text.replace(char, '')
    
    # Validate path structure (max 3 levels)
    parts = [part.strip() for part in text.split('/') if part.strip()]
    if len(parts) > 3:
        parts = parts[:3]
    
    # Ensure each part is valid
    valid_parts = []
    for part in parts:
        # Remove extra spaces and ensure it's not empty
        clean_part = ' '.join(part.split())
        if clean_part and len(clean_part) <= 50:  # Reasonable length limit
            valid_parts.append(clean_part)
    
    if not valid_parts:
        return fallback
    
    return '/'.join(valid_parts)

def validate_folder_path(path: str) -> str:
    """Enhanced folder path validation"""
    if not path or path.lower() in ['error', 'none', 'null', 'unknown']:
        return "Uncategorized"
    
    # Clean the path
    path = extract_clean_path(path)
    
    # Additional validation
    if len(path) > 200:  # Very long paths
        return "Uncategorized"
    
    # Check for reasonable folder names
    parts = path.split('/')
    for part in parts:
        if len(part) > 50 or not part.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            # If any part is too long or has too many special characters, fallback
            return "Uncategorized"
    
    return path

# Utility functions for error handling and retry logic
def with_retry(func, max_retries: int = 2, delay: float = 1.0):
    """Execute function with retry logic"""
    for attempt in range(max_retries + 1):
        try:
            result = func()
            if not result.startswith("Error:"):
                return result
        except Exception as e:
            if attempt == max_retries:
                return f"Error after {max_retries + 1} attempts: {str(e)}"
        
        if attempt < max_retries:
            time.sleep(delay)
    
    return "Error: Max retries exceeded"

def get_model_info(backend: str, model: str) -> dict:
    """Get information about a specific model"""
    info = {
        "backend": backend,
        "model": model,
        "available": False,
        "description": "Unknown model"
    }
    
    try:
        if backend == "Local (Ollama)":
            # Check if model exists in Ollama
            models = list_ollama_models()
            if model in models:
                info["available"] = True
                info["description"] = f"Local Ollama model: {model}"
        
        elif backend == "OpenAI":
            # Common OpenAI models
            openai_models = {
                "gpt-3.5-turbo": "GPT-3.5 Turbo - Fast and efficient",
                "gpt-4": "GPT-4 - Most capable model",
                "gpt-4-turbo": "GPT-4 Turbo - Latest GPT-4 variant",
                "gpt-4o-mini": "GPT-4o Mini - Optimized for efficiency"
            }
            if model in openai_models:
                info["available"] = True
                info["description"] = openai_models[model]
        
        elif backend == "Grok":
            # Grok models
            grok_models = {
                "grok-beta": "Grok Beta - xAI's conversational AI",
                "grok-2-mini": "Grok 2 Mini - Efficient model"
            }
            if model in grok_models:
                info["available"] = True
                info["description"] = grok_models[model]
    
    except Exception as e:
        print(f"Error getting model info: {e}")
    
    return info