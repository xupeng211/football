#!/usr/bin/env python3
"""Simplified Context Detection Engine for AI Context Guardian."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DetectionResult:
    """Result of context detection analysis."""

    triggered: bool
    trigger_type: str
    confidence: float
    related_files: List[str]
    dependencies: Dict[str, List[str]]
    priority: int
    reason: str
    metadata: Dict[str, str]


class ContextDetector:
    """Simplified context detection engine."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> None:
        """Initialize context detector."""
        self.config = self._load_default_config()
        self.project_root = Path(project_root or os.getcwd())

    def detect_context_needs(
        self,
        current_file: str,
        changes: List[str],
        change_type: str = "modification",
    ) -> DetectionResult:
        """Analyze code changes and determine context injection needs."""
        result = DetectionResult(
            triggered=False,
            trigger_type="none",
            confidence=0.0,
            related_files=[],
            dependencies={},
            priority=0,
            reason="",
            metadata={},
        )

        try:
            # Check for import changes
            imports = self._extract_imports(changes)
            if imports:
                result.triggered = True
                result.trigger_type = "cross_file_dependency"
                result.confidence = 1.0
                result.priority = 5
                result.reason = f"Detected {len(imports)} import changes"
                result.dependencies["imports"] = imports

            # Check config file changes
            if self._is_config_file(current_file):
                result.triggered = True
                result.trigger_type = "config_change"
                result.confidence = 0.9
                result.priority = 8
                result.reason = "Configuration file modification"

            return result

        except Exception as e:
            result.reason = f"Detection failed: {e}"
            return result

    def _extract_imports(self, changes: List[str]) -> List[str]:
        """Extract import statements from changes."""
        imports = []
        import_pattern = re.compile(r"^\s*(?:import|from)\s+(\w+)")

        for change in changes:
            matches = import_pattern.findall(change)
            imports.extend(matches)

        return imports

    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        config_extensions = [".yml", ".yaml", ".json", ".toml", ".ini"]
        config_names = ["Makefile", "Dockerfile"]

        file_path_obj = Path(file_path)
        return (
            file_path_obj.suffix in config_extensions
            or file_path_obj.name in config_names
            or "requirements" in file_path_obj.name
        )

    def _load_default_config(self) -> Dict[str, object]:
        """Load default configuration."""
        return {
            "max_inject_files": 5,
            "max_tokens_per_inject": 2000,
            "log_level": "INFO",
            "detection_sensitivity": "medium",
            "detect_cross_file_deps": True,
            "detect_config_changes": True,
            "detect_ci_changes": True,
            "detect_test_changes": True,
        }
