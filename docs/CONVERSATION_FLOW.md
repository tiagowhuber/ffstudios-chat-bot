# Conversation Flow for Missing Fields

This feature enables the bot to have multi-turn conversations with users when they don't provide all required information in a single message.

## How It Works

### Example Conversation

```
👤 User: compre un vino blanco 1 litro en $1790

🤖 Bot: Por favor indícame: proveedor y medio de pago

👤 User: lider, débito

🤖 Bot: ✅ Compra registrada: 1.0 litro de vino blanco por $1790 en Líder con Débito
```

## Architecture

### Components

1. **ConversationStateManager** (`src/bot/conversation_state.py`)
   - Manages conversation state for each user
   - Stores and retrieves pending actions
   - Tracks what information is still needed

2. **PendingAction** (dataclass in `conversation_state.py`)
   - Stores partial action data
   - Tracks missing required fields
   - Merges supplemental information

3. **SmartInventoryService** (`src/services/smart_inventory_service.py`)
   - Extended to handle multi-turn conversations
   - Detects missing fields
   - Parses supplemental messages
   - Merges and completes actions

4. **Message Handlers** (`src/bot/handlers.py`)
   - Checks for pending actions before processing
   - Stores pending actions in user context
   - Clears state after completion/error

## Required Fields by Action

### Purchase (`register_purchase`)
- ✅ `ingredient_name` - Product name
- ✅ `quantity` - Numeric quantity
- ✅ `unit` - Unit of measure
- ✅ `cost` - Price
- ✅ `provider` - Store/supplier name
- ✅ `payment_method` - Payment type

### Expense (`register_expense`)
- ✅ `expense_category` - Category (luz, agua, etc.)
- ✅ `cost` - Amount
- ✅ `provider` - Service provider
- ✅ `payment_method` - Payment type

### Usage (`register_usage`)
- ✅ `ingredient_name` - Product name
- ✅ `quantity` - Amount used

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User sends message                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ Check pending action? │
         └───────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        NO               YES
        │                 │
        ▼                 ▼
┌──────────────┐   ┌──────────────────┐
│ Parse as new │   │ Parse as         │
│ action       │   │ supplement       │
└──────┬───────┘   └────────┬─────────┘
       │                    │
       │                    ▼
       │            ┌───────────────┐
       │            │ Merge data    │
       │            └───────┬───────┘
       │                    │
       └──────────┬─────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Check missing fields │
        └──────────┬───────────┘
                   │
          ┌────────┴────────┐
          │                 │
        MISSING          COMPLETE
          │                 │
          ▼                 ▼
  ┌──────────────┐   ┌──────────────┐
  │ Ask for      │   │ Execute      │
  │ missing info │   │ action       │
  │ Store state  │   │ Clear state  │
  └──────────────┘   └──────────────┘
```

## Implementation Details

### State Management

The bot uses Telegram's `context.user_data` to store conversation state per user:

```python
context.user_data = {
    'conversation_state': ConversationState.AWAITING_PURCHASE_DETAILS,
    'pending_action': {
        'action': 'register_purchase',
        'original_message': 'compre vino...',
        'ingredient_name': 'vino blanco',
        'quantity': 1.0,
        'unit': 'litro',
        'cost': 1790.0,
        'missing_fields': ['provider', 'payment_method']
    }
}
```

### Parsing Supplemental Messages

When a user provides additional information, the bot uses a targeted NLP prompt:

```python
supplement = smart_inventory.parse_supplemental_message(
    "lider, débito",
    missing_fields=['provider', 'payment_method']
)
# Returns: {'provider': 'Líder', 'payment_method': 'Débito'}
```

### Merging Data

The `PendingAction.merge_with_supplement()` method intelligently merges:

```python
pending.merge_with_supplement({
    'provider': 'Líder',
    'payment_method': 'Débito'
})
# Updates fields and removes from missing_fields list
```

## Usage Examples

### Example 1: Incomplete Purchase

```python
# Turn 1
"compre chocolate 2kg por $8000"
# Missing: provider, payment_method
# Bot asks: "Por favor indícame: proveedor y medio de pago"

# Turn 2
"santa isabel, crédito"
# Bot: "✅ Compra registrada: 2.0 kg de chocolate por $8000..."
```

### Example 2: Incomplete Expense

```python
# Turn 1
"gasté 45000 en agua"
# Missing: provider, payment_method
# Bot asks: "Por favor indícame: proveedor y medio de pago"

# Turn 2
"aguas andinas con transferencia"
# Bot: "✅ Gasto registrado: $45000 en agua..."
```

### Example 3: Complete Data (No Follow-up)

```python
# Turn 1
"compre 1kg de arroz por $2000 en líder con débito"
# All fields present
# Bot: "✅ Compra registrada: 1.0 kg de arroz por $2000..."
```

## Testing

### Run Tests

```bash
# Activate environment
.venv\Scripts\activate

# Run conversation flow tests
pytest tests/test_conversation_flow.py -v

# Run all tests
pytest tests/ -v
```

### Demo Script

```bash
# Run interactive demo
python examples/demo_conversation_flow.py
```

## Field Translations

The bot translates technical field names to user-friendly Spanish:

| Field | Spanish |
|-------|---------|
| `ingredient_name` | nombre del producto |
| `quantity` | cantidad |
| `unit` | unidad de medida |
| `cost` | precio |
| `provider` | proveedor |
| `payment_method` | medio de pago |
| `expense_category` | categoría del gasto |
| `reason` | motivo |

## Error Handling

The system includes robust error handling:

1. **Parse Errors**: If supplemental parsing fails, asks again
2. **Timeout**: No automatic timeout (stays until user completes or sends new command)
3. **New Commands**: Starting a new command clears pending state
4. **Exceptions**: Any exception clears conversation state to prevent stuck users

## Future Enhancements

Possible improvements:

- [ ] Add timeout for pending actions (e.g., 5 minutes)
- [ ] Support editing previous fields
- [ ] Add "cancel" command to abort pending actions
- [ ] Multi-language support
- [ ] Voice input for supplemental data
- [ ] Smart defaults based on user history

## API Reference

### ConversationStateManager

```python
# Get current state
state = ConversationStateManager.get_state(context)

# Set state
ConversationStateManager.set_state(context, ConversationState.AWAITING_PURCHASE_DETAILS)

# Store pending action
ConversationStateManager.set_pending_action(context, pending_action)

# Retrieve pending action
pending = ConversationStateManager.get_pending_action(context)

# Clear state
ConversationStateManager.clear_pending_action(context)

# Check if pending
has_pending = ConversationStateManager.has_pending_action(context)
```

### Helper Functions

```python
# Check missing fields
missing = check_missing_fields('register_purchase', action_data)

# Format prompt
prompt = format_missing_fields_prompt(['provider', 'payment_method'])
# Returns: "Por favor indícame: proveedor y medio de pago"
```

## Contributing

When adding new action types:

1. Add required fields to `get_required_fields()` in `conversation_state.py`
2. Add field translations to `format_missing_fields_prompt()`
3. Update this documentation
4. Add test cases

---

**Last Updated**: February 4, 2026
**Version**: 1.0.0
