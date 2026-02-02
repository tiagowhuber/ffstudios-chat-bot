# Examples

This folder contains demo scripts and examples for testing the bot's functionality without running the full Telegram bot.

## Available Examples

### `demo_finance.py`

A comprehensive demo script that showcases the Smart Inventory Service capabilities:

- **Purchase Registration**: Track inventory purchases with financial details
- **Stock Queries**: Check current inventory levels
- **Expense Tracking**: Record general expenses
- **Usage Recording**: Track inventory consumption
- **Financial Reports**: Generate reports by supplier/category

#### Running the Demo

Make sure you have:
1. Docker PostgreSQL container running (see main README)
2. `.env` file configured with `OPENAI_API_KEY`
3. Virtual environment activated

```bash
python examples/demo_finance.py
```

## Purpose

These examples are useful for:
- Testing the service layer without Telegram integration
- Validating natural language processing capabilities
- Debugging database operations
- Demonstrating bot features to stakeholders
