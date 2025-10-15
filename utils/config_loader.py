"""Configuration loading utilities."""

import os
from pathlib import Path
from typing import Dict, Any

import yaml


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from config.yaml with environment variable substitution.
    
    Args:
        config_path: Path to config file (default: config/config.yaml)
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    else:
        config_path = Path(config_path)
    
    with open(config_path, 'r') as f:
        config_str = f.read()
        
    # Replace environment variables
    for key, value in os.environ.items():
        config_str = config_str.replace(f'${{{key}}}', value)
    
    return yaml.safe_load(config_str)


def load_subnets(subnets_path: str = None) -> list:
    """
    Load subnet configurations.
    
    Args:
        subnets_path: Path to subnets file (default: config/subnets.yaml)
        
    Returns:
        List of subnet configurations
    """
    if subnets_path is None:
        subnets_path = Path(__file__).parent.parent / 'config' / 'subnets.yaml'
    else:
        subnets_path = Path(subnets_path)
    
    with open(subnets_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return data.get('subnets', [])

