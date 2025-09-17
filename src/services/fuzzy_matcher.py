"""
Fuzzy string matching utility for handling typos in ingredient names.
"""
import re
import unicodedata
from typing import List, Tuple, Optional
from difflib import SequenceMatcher


class FuzzyMatcher:
    """Utility class for fuzzy string matching with Spanish language support."""
    
    @staticmethod
    def normalize_string(text: str) -> str:
        """
        Normalize a string by removing accents and converting to lowercase.
        
        Args:
            text: Input string
            
        Returns:
            Normalized string without accents and in lowercase
        """
        if not text:
            return ""
        
        # Normalize unicode characters (decompose accented characters)
        normalized = unicodedata.normalize('NFD', text.lower())
        
        # Remove accent marks (combining characters)
        without_accents = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'
        )
        
        # Remove extra whitespace and special characters, keep only letters, numbers, and spaces
        cleaned = re.sub(r'[^a-z0-9\s]', '', without_accents)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using SequenceMatcher.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        if not str1 or not str2:
            return 0.0
        
        # Compare normalized strings
        norm1 = FuzzyMatcher.normalize_string(str1)
        norm2 = FuzzyMatcher.normalize_string(str2)
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    @staticmethod
    def find_best_matches(
        target: str, 
        candidates: List[str], 
        min_similarity: float = 0.6,
        max_results: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Find the best matching strings from a list of candidates.
        
        Args:
            target: String to match against
            candidates: List of candidate strings
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            max_results: Maximum number of results to return
            
        Returns:
            List of (candidate, similarity_score) tuples, sorted by similarity
        """
        if not target or not candidates:
            return []
        
        # Calculate similarities
        similarities = []
        for candidate in candidates:
            similarity = FuzzyMatcher.calculate_similarity(target, candidate)
            if similarity >= min_similarity:
                similarities.append((candidate, similarity))
        
        # Sort by similarity (highest first) and limit results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:max_results]
    
    @staticmethod
    def find_best_match(
        target: str, 
        candidates: List[str], 
        min_similarity: float = 0.6
    ) -> Optional[Tuple[str, float]]:
        """
        Find the single best matching string from a list of candidates.
        
        Args:
            target: String to match against
            candidates: List of candidate strings
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            Tuple of (best_match, similarity_score) or None if no good match
        """
        matches = FuzzyMatcher.find_best_matches(
            target, candidates, min_similarity, max_results=1
        )
        
        return matches[0] if matches else None
    
    @staticmethod
    def is_close_match(str1: str, str2: str, min_similarity: float = 0.8) -> bool:
        """
        Check if two strings are close matches (useful for typo detection).
        
        Args:
            str1: First string
            str2: Second string
            min_similarity: Minimum similarity threshold
            
        Returns:
            True if strings are similar enough to be considered a match
        """
        return FuzzyMatcher.calculate_similarity(str1, str2) >= min_similarity


# Example usage and test cases
if __name__ == "__main__":
    # Test cases for Spanish ingredients with common typos
    test_cases = [
        ("azucar", "azúcar"),  # Missing accent
        ("azucar", "azucar"),  # Same normalized
        ("chocolte", "chocolate"),  # Character swap
        ("harna", "harina"),  # Typo
        ("leche", "leche"),  # Exact match
        ("vanil", "vainilla"),  # Partial/abbreviation
        ("mantequilla", "mantquilla"),  # Missing letter
    ]
    
    print("Fuzzy Matching Test Results:")
    print("=" * 40)
    
    for target, candidate in test_cases:
        similarity = FuzzyMatcher.calculate_similarity(target, candidate)
        is_match = FuzzyMatcher.is_close_match(target, candidate, 0.7)
        print(f"'{target}' vs '{candidate}': {similarity:.3f} - Match: {is_match}")
    
    print("\nIngredient Matching Example:")
    print("=" * 40)
    
    ingredients = ["azúcar", "chocolate", "harina", "leche", "mantequilla", "vainilla", "sal"]
    user_inputs = ["azucar", "chocolte", "harna", "vanil"]
    
    for user_input in user_inputs:
        best_match = FuzzyMatcher.find_best_match(user_input, ingredients, 0.6)
        if best_match:
            match, score = best_match
            print(f"'{user_input}' -> '{match}' (score: {score:.3f})")
        else:
            print(f"'{user_input}' -> No good match found")