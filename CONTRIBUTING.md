# Contributing to TradeEngine

Thank you for your interest in contributing to TradeEngine!

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS, broker)
- Error messages or logs

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature already exists
- Describe the use case
- Explain why it would be useful
- Provide examples if possible

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test thoroughly
5. Commit: `git commit -m "Add: description of changes"`
6. Push: `git push origin feature/your-feature-name`
7. Create a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/Itszeeshanrajput/TradeEngine.git
cd TradeEngine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python start_with_eventlet.py
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Comment complex logic

## Testing

- Test with demo accounts before live trading
- Verify all endpoints work correctly
- Check WebSocket connections
- Test backtesting functionality

## Security

- Never commit real trading credentials
- Use environment variables for sensitive data
- Test with demo accounts only
- Review code for security issues

## Questions?

Feel free to open an issue for any questions about contributing!

Thank you for helping make TradeEngine better! 🚀
