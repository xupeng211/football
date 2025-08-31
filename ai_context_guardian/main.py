#!/usr/bin/env python3
"""AI Context Guardian - Main Entry Point.

Intelligent context management for AI programming assistants.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from core.detector import ContextDetector, DetectionResult
from core.token_manager import TokenManager


class ContextGuardian:
    """Main controller for AI context management."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> None:
        """Initialize Context Guardian.

        Args:
            config_path: Path to configuration file.
            project_root: Root directory of the project.
        """
        self.project_root = Path(project_root or os.getcwd())
        self.config_path = config_path or self._find_config_file()

        # Load configuration
        self.config = self._load_config()

        # Initialize core components
        self.detector = ContextDetector(self.config_path, str(self.project_root))
        self.token_manager = TokenManager(
            {
                k: int(v) if isinstance(v, (int, str)) and str(v).isdigit() else 2000
                for k, v in self.config.items()
            }
        )

    def auto_inject_context(
        self,
        current_file: str,
        changes: List[str],
        change_type: str = "modification",
    ) -> Dict[str, object]:
        """Automatically inject context for code changes.

        Args:
            current_file: Path to the file being modified.
            changes: List of changes made to the file.
            change_type: Type of change (modification, creation, deletion).

        Returns:
            Dictionary with injection results.
        """
        try:
            # Detect context needs
            detection_result = self.detector.detect_context_needs(
                current_file, changes, change_type
            )

            if not detection_result.triggered:
                return {
                    "triggered": False,
                    "reason": detection_result.reason,
                    "confidence": detection_result.confidence,
                    "injected_context": None,
                }

            # For now, return detection results
            # In a full implementation, this would include context injection
            return {
                "triggered": True,
                "success": True,
                "detection_result": {
                    "trigger_type": detection_result.trigger_type,
                    "confidence": detection_result.confidence,
                    "related_files": detection_result.related_files,
                    "reason": detection_result.reason,
                },
                "injected_context": self._format_context_preview(detection_result),
            }

        except Exception as e:
            return {
                "triggered": False,
                "success": False,
                "error": str(e),
                "injected_context": None,
            }

    def _format_context_preview(self, detection_result: DetectionResult) -> str:
        """Format detection results as context preview.

        Args:
            detection_result: Results from context detection.

        Returns:
            Formatted context preview string.
        """
        if not detection_result.related_files:
            return "# No context files identified"

        context_parts = []
        context_parts.append("# AI Context Guardian - Context Preview")
        context_parts.append(
            f"# Trigger: {detection_result.trigger_type} "
            f"(confidence: {detection_result.confidence:.2f})"
        )
        context_parts.append("")

        context_parts.append("## Related Files:")
        for i, file_path in enumerate(detection_result.related_files[:5], 1):
            context_parts.append(f"{i}. {file_path}")

        if detection_result.dependencies:
            context_parts.append("")
            context_parts.append("## Dependencies:")
            for dep_type, deps in detection_result.dependencies.items():
                context_parts.append(f"- {dep_type}: {', '.join(deps[:3])}")

        return "\n".join(context_parts)

    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in project.

        Returns:
            Path to configuration file if found.
        """
        config_paths = [
            self.project_root / "ai-context-guardian" / "config" / "default.yml",
            self.project_root / ".ai-context-guardian.yml",
            self.project_root / "config" / "ai-context-guardian.yml",
        ]

        for config_path in config_paths:
            if config_path.exists():
                return str(config_path)

        return None

    def _load_config(self) -> Dict[str, object]:
        """Load configuration.

        Returns:
            Configuration dictionary.
        """
        import yaml

        default_config = {
            "max_inject_files": 5,
            "max_tokens_per_inject": 2000,
            "log_level": "INFO",
            "detection_sensitivity": "medium",
            "detect_cross_file_deps": True,
            "detect_config_changes": True,
            "detect_ci_changes": True,
            "detect_test_changes": True,
        }

        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                    if "context_guardian" in user_config:
                        default_config.update(user_config["context_guardian"])
                    else:
                        default_config.update(user_config)
            except Exception as e:
                print(f"Config load failed, using defaults: {e}")

        return default_config


def main() -> None:
    """Command line entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Context Guardian - Smart context management"
    )
    parser.add_argument("--file", required=True, help="File being modified")
    parser.add_argument("--changes", nargs="+", required=True, help="List of changes")
    parser.add_argument("--type", default="modification", help="Change type")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    # Create guardian instance
    guardian = ContextGuardian(config_path=args.config)

    # Process context injection
    result = guardian.auto_inject_context(args.file, args.changes, args.type)

    # Output results
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
