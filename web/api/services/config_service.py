"""Utilities for loading and updating configuration files."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


CONFIG_FILENAME = Path("config.yaml")
CONFIG_EXAMPLE_FILENAME = Path("config.example.yaml")
SENSITIVE_KEYS = {"api_key", "api_secret", "secret", "token"}


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""


def _mask_secret(value: str) -> str:
    """Mask a secret value while preserving hint of presence."""
    if not value:
        return value
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def _redact(obj: Any) -> Any:
    """Recursively redact sensitive values in the configuration."""
    if isinstance(obj, dict):
        redacted = {}
        for key, value in obj.items():
            if key in SENSITIVE_KEYS and isinstance(value, str):
                redacted[key] = _mask_secret(value)
            else:
                redacted[key] = _redact(value)
        return redacted
    if isinstance(obj, list):
        return [_redact(item) for item in obj]
    return obj


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file into dictionary."""
    if not path.exists():
        raise FileNotFoundError(str(path))
    
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration file {path} must contain a mapping object")
    
    return data


def _validate_config(config: Dict[str, Any]) -> None:
    """Perform lightweight validation on the configuration structure."""
    required_top_level = {"base_url", "master", "followers"}
    missing_top = required_top_level - set(config.keys())
    if missing_top:
        raise ConfigError(f"Missing required fields: {', '.join(sorted(missing_top))}")
    
    master = config["master"]
    if not isinstance(master, dict):
        raise ConfigError("master section must be a mapping")
    
    master_required = {"api_key", "api_secret"}
    missing_master = master_required - set(master.keys())
    if missing_master:
        raise ConfigError(f"master section missing fields: {', '.join(sorted(missing_master))}")
    
    followers = config["followers"]
    if not isinstance(followers, list):
        raise ConfigError("followers section must be a list")
    
    for follower in followers:
        if not isinstance(follower, dict):
            raise ConfigError("each follower entry must be a mapping")
        for field in ("name", "api_key", "api_secret"):
            if field not in follower:
                raise ConfigError(f"follower entry missing field: {field}")


def resolve_config_path() -> Tuple[Path, bool]:
    """
    Resolve the configuration file path.
    
    Returns:
        Tuple[path, is_example] indicating the file used and whether it's the example config.
    """
    if CONFIG_FILENAME.exists():
        return CONFIG_FILENAME, False
    if CONFIG_EXAMPLE_FILENAME.exists():
        return CONFIG_EXAMPLE_FILENAME, True
    # Default to config.yaml when nothing exists so callers can create it later.
    return CONFIG_FILENAME, False


def load_config(redact: bool = True) -> Tuple[Dict[str, Any], Path, bool]:
    """
    Load configuration data.
    
    Args:
        redact: Whether to mask sensitive fields.
    
    Returns:
        (config_data, path, is_example)
    """
    path, is_example = resolve_config_path()
    try:
        config = _load_yaml(path)
    except FileNotFoundError:
        config = {}
    
    data = deepcopy(config)
    if redact:
        data = _redact(data)
    return data, path, is_example


def load_raw_config() -> Tuple[Dict[str, Any], Path, bool]:
    """Load configuration without redaction."""
    return load_config(redact=False)


def update_config(config: Dict[str, Any]) -> Path:
    """
    Persist configuration to disk after validation.
    
    Args:
        config: Configuration dictionary to write.
    
    Returns:
        Path written to.
    """
    _validate_config(config)
    
    output_path = CONFIG_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(
            config,
            fh,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False
        )
    
    return output_path
