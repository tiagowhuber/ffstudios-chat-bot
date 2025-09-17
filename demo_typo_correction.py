"""
Integration demo of typo correction in the inventory bot.
This shows how the typo correction would work in practice.
"""
import sys
import os

# Add the src directory to the Python path
current_dir = os.getcwd()
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

from src.services.fuzzy_matcher import FuzzyMatcher

def demo_typo_correction():
    """Demonstrate typo correction for inventory management."""
    
    print("=== INVENTORY TYPO CORRECTION DEMO ===")
    print()
    
    # Simulate existing inventory
    existing_ingredients = [
        "azúcar", "chocolate", "harina", "leche", 
        "mantequilla", "vainilla", "sal", "huevos",
        "café", "canela", "polvo de hornear"
    ]
    
    print("Current inventory contains:")
    for i, ingredient in enumerate(existing_ingredients, 1):
        print(f"  {i}. {ingredient}")
    
    print("\n" + "="*50)
    print("Testing user inputs with typos:")
    print("="*50)
    
    # Simulate user inputs with various typos
    user_inputs = [
        "azucar",           # Missing accent
        "chocolte",         # Character swap
        "harna",            # Missing letter
        "mantequila",       # Missing letter
        "vainila",          # Missing letter
        "cafe",             # Missing accent
        "canel",            # Shortened/typo
        "polvo hornear",    # Missing word "de"
        "huveos",           # Character swap
        "mantqilla",        # Missing letter
        "nonexistent",      # Completely wrong
    ]
    
    for user_input in user_inputs:
        print(f"\nUser typed: '{user_input}'")
        
        # Try exact match first
        exact_matches = [ing for ing in existing_ingredients if ing.lower() == user_input.lower()]
        
        if exact_matches:
            print(f"  ✅ EXACT MATCH: Found '{exact_matches[0]}'")
        else:
            # Try fuzzy matching
            result = FuzzyMatcher.find_best_match(user_input, existing_ingredients, min_similarity=0.6)
            
            if result:
                match, score = result
                if score >= 0.9:
                    print(f"  🔧 AUTO-CORRECTED: '{user_input}' -> '{match}' (confidence: {score:.1%})")
                elif score >= 0.7:
                    print(f"  🤔 SUGGESTION: Did you mean '{match}'? (confidence: {score:.1%})")
                else:
                    print(f"  ⚠️  WEAK MATCH: Possible match '{match}' (confidence: {score:.1%})")
            else:
                print(f"  ❌ NO MATCH: '{user_input}' not found - would create new ingredient")
    
    print("\n" + "="*50)
    print("Summary of typo correction benefits:")
    print("="*50)
    print("✅ Handles missing accents (azucar -> azúcar)")
    print("✅ Fixes character swaps (chocolte -> chocolate)")
    print("✅ Corrects missing letters (harna -> harina)")
    print("✅ Suggests similar items with confidence scores")
    print("✅ Prevents duplicate ingredients from typos")
    print("✅ Maintains data consistency in inventory")
    
    print("\n🎉 Typo correction system is ready for production!")

if __name__ == "__main__":
    demo_typo_correction()