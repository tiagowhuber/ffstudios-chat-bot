"""
Demo script to test conversation flow with missing fields.

This script simulates the conversation flow where:
1. User sends incomplete purchase information
2. Bot asks for missing details
3. User provides the missing details
4. Bot completes the registration
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.smart_inventory_service import SmartInventoryService
from src.bot.config import Config
from src.bot.conversation_state import PendingAction


def print_separator():
    print("\n" + "="*60 + "\n")


def simulate_conversation():
    """Simulate a multi-turn conversation."""
    
    # Initialize service
    config = Config()
    if not config.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not configured!")
        return
    
    smart_inventory = SmartInventoryService(config.OPENAI_API_KEY)
    
    print("🤖 Conversation Flow Demo")
    print("="*60)
    print("Simulating: User registers a purchase with missing details\n")
    
    # Turn 1: User sends incomplete purchase
    user_message_1 = "compre un vino blanco 1 litro en $1790"
    print(f"👤 User: {user_message_1}")
    
    success, bot_response, pending = smart_inventory.process_natural_language_command(user_message_1)
    
    print(f"🤖 Bot: {bot_response}")
    
    if pending:
        print(f"\n📋 Pending Action Details:")
        print(f"   Action: {pending.action}")
        print(f"   Product: {pending.ingredient_name}")
        print(f"   Quantity: {pending.quantity} {pending.unit}")
        print(f"   Cost: ${pending.cost}")
        print(f"   Missing fields: {pending.missing_fields}")
        
        print_separator()
        
        # Turn 2: User provides missing info
        user_message_2 = "lider, débito"
        print(f"👤 User: {user_message_2}")
        
        success, bot_response, new_pending = smart_inventory.process_natural_language_command(
            user_message_2,
            pending_action=pending
        )
        
        print(f"🤖 Bot: {bot_response}")
        
        if new_pending:
            print(f"\n📋 Still Missing: {new_pending.missing_fields}")
        else:
            print(f"\n✅ Action Completed Successfully!")
            
    else:
        print("\n⚠️ No pending action created (all fields were present or action failed)")
    
    print_separator()
    
    # Example 2: Expense with missing fields
    print("\n🤖 Example 2: Expense with Missing Fields")
    print("="*60)
    
    user_message_1 = "gasté 35000 en luz"
    print(f"👤 User: {user_message_1}")
    
    success, bot_response, pending = smart_inventory.process_natural_language_command(user_message_1)
    print(f"🤖 Bot: {bot_response}")
    
    if pending:
        print(f"\n📋 Missing fields: {pending.missing_fields}")
        print_separator()
        
        user_message_2 = "CGE con transferencia"
        print(f"👤 User: {user_message_2}")
        
        success, bot_response, new_pending = smart_inventory.process_natural_language_command(
            user_message_2,
            pending_action=pending
        )
        
        print(f"🤖 Bot: {bot_response}")
        
        if not new_pending:
            print(f"\n✅ Expense Registered!")
    
    print_separator()
    
    # Example 3: Complete purchase (no missing fields)
    print("\n🤖 Example 3: Complete Purchase (No Missing Fields)")
    print("="*60)
    
    user_message = "compre 2 kg de azúcar por $5000 en santa isabel con tarjeta de crédito"
    print(f"👤 User: {user_message}")
    
    success, bot_response, pending = smart_inventory.process_natural_language_command(user_message)
    print(f"🤖 Bot: {bot_response}")
    
    if pending:
        print(f"\n📋 Missing fields: {pending.missing_fields}")
    else:
        print(f"\n✅ Direct Registration (no follow-up needed)")
    
    print_separator()


if __name__ == "__main__":
    try:
        simulate_conversation()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
