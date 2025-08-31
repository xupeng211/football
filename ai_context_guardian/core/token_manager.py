#!/usr/bin/env python3
"""Token Manager for AI Context Guardian.

Intelligent token counting and content trimming for context injection.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TokenBudget:
    """Token budget management."""

    max_tokens: int
    used_tokens: int
    remaining_tokens: int
    utilization_rate: float


class TokenManager:
    """Smart token management for context injection."""

    def __init__(self, config: Dict[str, int]) -> None:
        """Initialize token manager with configuration.

        Args:
            config: Configuration dictionary with token limits.
        """
        self.config = config
        self.max_tokens = config.get("max_tokens_per_inject", 2000)

        # Token estimation rules for different content types
        self.token_rules = {
            "chinese_char": 1.5,
            "english_word": 1.0,
            "code_token": 1.2,
            "special_char": 0.5,
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count for given text.

        Args:
            text: Text to analyze.

        Returns:
            Estimated number of tokens.
        """
        if not text:
            return 0

        total_chars = len(text)
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        english_words = len(re.findall(r"\b[a-zA-Z]+\b", text))
        code_features = len(re.findall(r"[{}()\[\];,.]", text))
        special_chars = len(re.findall(r"[!@#$%^&*+=<>?/\\|`~]", text))

        # Weighted calculation
        estimated_tokens = (
            chinese_chars * self.token_rules["chinese_char"]
            + english_words * self.token_rules["english_word"]
            + code_features * self.token_rules["code_token"]
            + special_chars * self.token_rules["special_char"]
        )

        # Ensure minimum tokens based on character count
        min_tokens = total_chars // 4

        return max(int(estimated_tokens), min_tokens)

    def create_budget(self, available_tokens: Optional[int] = None) -> TokenBudget:
        """Create a token budget for context injection.

        Args:
            available_tokens: Maximum tokens available, defaults to config.

        Returns:
            TokenBudget instance.
        """
        max_tokens = available_tokens or self.max_tokens

        return TokenBudget(
            max_tokens=max_tokens,
            used_tokens=0,
            remaining_tokens=max_tokens,
            utilization_rate=0.0,
        )

    def update_budget(self, budget: TokenBudget, used_tokens: int) -> TokenBudget:
        """Update token budget with used tokens.

        Args:
            budget: Current budget to update.
            used_tokens: Number of tokens consumed.

        Returns:
            Updated budget.
        """
        budget.used_tokens += used_tokens
        budget.remaining_tokens = budget.max_tokens - budget.used_tokens
        budget.utilization_rate = budget.used_tokens / budget.max_tokens

        return budget

    def can_afford(self, budget: TokenBudget, required_tokens: int) -> bool:
        """Check if budget can afford the required tokens.

        Args:
            budget: Current token budget.
            required_tokens: Tokens needed.

        Returns:
            True if budget allows the consumption.
        """
        return budget.remaining_tokens >= required_tokens

    def trim_to_budget(self, text: str, max_tokens: int) -> str:
        """Trim text to fit within token budget.

        Args:
            text: Original text to trim.
            max_tokens: Maximum allowed tokens.

        Returns:
            Trimmed text that fits within budget.
        """
        current_tokens = self.count_tokens(text)

        if current_tokens <= max_tokens:
            return text

        # Calculate proportional trim ratio
        keep_ratio = max_tokens / current_tokens

        # Trim by lines to preserve structure
        lines = text.split("\n")
        target_lines = max(1, int(len(lines) * keep_ratio))

        # Prioritize important lines
        important_lines = []
        regular_lines = []

        for line in lines:
            if self._is_important_line(line):
                important_lines.append(line)
            else:
                regular_lines.append(line)

        # Combine important lines with regular lines
        result_lines = important_lines[:]
        remaining_slots = target_lines - len(important_lines)

        if remaining_slots > 0:
            result_lines.extend(regular_lines[:remaining_slots])

        trimmed_text = "\n".join(result_lines)

        # Final safety check for token count
        if self.count_tokens(trimmed_text) > max_tokens:
            char_ratio = max_tokens / current_tokens * 0.8
            char_limit = int(len(text) * char_ratio)
            trimmed_text = text[:char_limit]

        return trimmed_text

    def _is_important_line(self, line: str) -> bool:
        """Determine if a line contains important content.

        Args:
            line: Line to evaluate.

        Returns:
            True if line is considered important.
        """
        line = line.strip()

        # Function and class definitions
        if line.startswith(("def ", "class ", "async def ")):
            return True

        # Import statements
        if line.startswith(("import ", "from ")):
            return True

        # Comments and docstrings
        if line.startswith(("#", '"""', "'''")):
            return True

        # Configuration items (key-value pairs)
        if ":" in line and not line.startswith(" "):
            return True

        return False

    def get_token_stats(self, contents: List[str]) -> Dict[str, float]:
        """Get token statistics for a list of content items.

        Args:
            contents: List of text content to analyze.

        Returns:
            Dictionary with token statistics.
        """
        if not contents:
            return {
                "total_tokens": 0,
                "avg_tokens": 0,
                "max_tokens": 0,
                "min_tokens": 0,
                "content_count": 0,
            }

        token_counts = [self.count_tokens(content) for content in contents]

        return {
            "total_tokens": sum(token_counts),
            "avg_tokens": sum(token_counts) / len(token_counts),
            "max_tokens": max(token_counts),
            "min_tokens": min(token_counts),
            "content_count": len(contents),
        }
