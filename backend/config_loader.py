"""Configuration loader with environment variable substitution."""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Dict

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file with env var substitution."""
    config_file = Path(__file__).parent / config_path
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Recursively substitute environment variables
    config = _substitute_env_vars(config)
    
    return config

def _substitute_env_vars(obj: Any) -> Any:
    """Recursively substitute ${VAR_NAME} with environment variables."""
    if isinstance(obj, dict):
        return {k: _substitute_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_substitute_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        var_name = obj[2:-1]
        return os.getenv(var_name, obj)
    else:
        return obj

# Global config instance
CONFIG = load_config()
