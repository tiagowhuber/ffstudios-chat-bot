"""
Test cases for typo correction functionality in the inventory system.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.fuzzy_matcher import FuzzyMatcher


class TestFuzzyMatcher:
    """Test cases for the FuzzyMatcher utility."""
    
    def test_normalize_string(self):
        """Test string normalization (accent removal and cleaning)."""
        test_cases = [
            ("azúcar", "azucar"),
            ("Azúcar", "azucar"),
            ("AZÚCAR", "azucar"),
            ("azúcar blanca", "azucar blanca"),
            ("café", "cafe"),
            ("niño", "nino"),
            ("cañón", "canon"),
            ("jalapeño", "jalapeno"),
            ("", ""),
            ("   espacios   ", "espacios"),
            ("números123", "numeros123"),
        ]
        
        for input_str, expected in test_cases:
            result = FuzzyMatcher.normalize_string(input_str)
            assert result == expected, f"normalize_string('{input_str}') = '{result}', expected '{expected}'"
    
    def test_calculate_similarity(self):
        """Test similarity calculation between strings."""
        test_cases = [
            ("azucar", "azúcar", 1.0),  # Same when normalized
            ("azucar", "azucar", 1.0),   # Identical
            ("chocolate", "chocolte", 0.8),  # High similarity (typo)
            ("harina", "harna", 0.8),    # High similarity (missing letter)
            ("leche", "agua", 0.0),      # No similarity
            ("vainilla", "vanil", 0.7),  # Partial match
            ("mantequilla", "mantquilla", 0.9),  # Missing letter
        ]
        
        for str1, str2, min_expected in test_cases:
            similarity = FuzzyMatcher.calculate_similarity(str1, str2)
            assert similarity >= min_expected, f"similarity('{str1}', '{str2}') = {similarity:.3f}, expected >= {min_expected}"
    
    def test_find_best_match(self):
        """Test finding the best match from a list of candidates."""
        ingredients = ["azúcar", "chocolate", "harina", "leche", "mantequilla", "vainilla", "sal"]
        
        test_cases = [
            ("azucar", "azúcar"),      # Missing accent
            ("chocolte", "chocolate"),  # Typo
            ("harna", "harina"),       # Missing letter
            ("vanil", "vainilla"),     # Abbreviation
            ("mantqilla", "mantequilla"), # Typo
            ("inexistente", None),     # No good match
        ]
        
        for user_input, expected in test_cases:
            result = FuzzyMatcher.find_best_match(user_input, ingredients, 0.6)
            
            if expected is None:
                assert result is None, f"find_best_match('{user_input}') should return None"
            else:
                assert result is not None, f"find_best_match('{user_input}') should not return None"
                match, score = result
                assert match == expected, f"find_best_match('{user_input}') = '{match}', expected '{expected}'"
                assert score >= 0.6, f"Score should be >= 0.6, got {score}"
    
    def test_find_best_matches_multiple(self):
        """Test finding multiple matches."""
        ingredients = ["azúcar moreno", "azúcar blanco", "azúcar glass", "chocolate", "harina"]
        
        result = FuzzyMatcher.find_best_matches("azucar", ingredients, 0.6, max_results=3)
        
        assert len(result) >= 2, "Should find multiple azúcar matches"
        
        # All results should be azúcar variants
        for match, score in result:
            assert "azúcar" in match.lower(), f"Match '{match}' should contain 'azúcar'"
            assert score >= 0.6, f"Score should be >= 0.6, got {score}"
    
    def test_is_close_match(self):
        """Test close match detection."""
        test_cases = [
            ("azucar", "azúcar", True),    # Should be close
            ("chocolte", "chocolate", True), # Should be close  
            ("harina", "agua", False),     # Should not be close
            ("", "", False),               # Empty strings
        ]
        
        for str1, str2, expected in test_cases:
            result = FuzzyMatcher.is_close_match(str1, str2, 0.8)
            assert result == expected, f"is_close_match('{str1}', '{str2}') = {result}, expected {expected}"


def test_fuzzy_matcher_real_scenarios():
    """Test realistic scenarios with Spanish ingredient names."""
    
    # Common Spanish ingredients
    ingredients = [
        "azúcar", "chocolate", "harina", "leche", "mantequilla", 
        "vainilla", "sal", "huevos", "café", "canela"
    ]
    
    # Common typos users might make
    typos_and_corrections = [
        ("azucar", "azúcar"),           # Missing accent
        ("chocolte", "chocolate"),       # Letter swap
        ("harna", "harina"),            # Missing letter
        ("vainila", "vainilla"),        # Missing letter
        ("mantequila", "mantequilla"),  # Missing letter
        ("cafe", "café"),               # Missing accent
        ("canela", "canela"),           # Exact match
        ("huveos", "huevos"),           # Letter swap
    ]
    
    for typo, expected in typos_and_corrections:
        result = FuzzyMatcher.find_best_match(typo, ingredients, 0.6)
        
        if expected in ingredients:
            assert result is not None, f"Should find a match for '{typo}'"
            match, score = result
            assert match == expected, f"'{typo}' should match '{expected}', got '{match}'"
        else:
            # For exact matches, should still work
            assert result is not None, f"Should find exact match for '{typo}'"


if __name__ == "__main__":
    # Run tests manually if executed directly
    print("Running Fuzzy Matcher Tests...")
    
    # Test normalize_string
    print("\n1. Testing normalize_string...")
    test_normalize = TestFuzzyMatcher()
    test_normalize.test_normalize_string()
    print("✅ normalize_string tests passed")
    
    # Test calculate_similarity
    print("\n2. Testing calculate_similarity...")
    test_normalize.test_calculate_similarity()
    print("✅ calculate_similarity tests passed")
    
    # Test find_best_match
    print("\n3. Testing find_best_match...")
    test_normalize.test_find_best_match()
    print("✅ find_best_match tests passed")
    
    # Test multiple matches
    print("\n4. Testing find_best_matches...")
    test_normalize.test_find_best_matches_multiple()
    print("✅ find_best_matches tests passed")
    
    # Test close match
    print("\n5. Testing is_close_match...")
    test_normalize.test_is_close_match()
    print("✅ is_close_match tests passed")
    
    # Test real scenarios
    print("\n6. Testing real scenarios...")
    test_fuzzy_matcher_real_scenarios()
    print("✅ Real scenario tests passed")
    
    print("\n🎉 All fuzzy matcher tests passed!")
    
    # Demo with example usage
    print("\n" + "="*50)
    print("DEMO: Typo Correction Examples")
    print("="*50)
    
    ingredients = ["azúcar", "chocolate", "harina", "leche", "mantequilla", "vainilla"]
    user_inputs = ["azucar", "chocolte", "harna", "vanil", "mantqilla"]
    
    for user_input in user_inputs:
        result = FuzzyMatcher.find_best_match(user_input, ingredients, 0.6)
        if result:
            match, score = result
            print(f"'{user_input}' → '{match}' (confianza: {score:.1%})")
        else:
            print(f"'{user_input}' → Sin coincidencias encontradas")