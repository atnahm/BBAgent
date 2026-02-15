# Contributing to Bharat Biz-Agent

Thank you for your interest in contributing to Bharat Biz-Agent!

## Development Setup

1. Fork the repository
2. Clone your fork
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   pip install schedule watchdog flask psutil
   ```
4. Configure environment:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```
5. Run tests:
   ```bash
   python quick_test.py
   python test_automation.py
   ```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

## Testing

- Add tests for new features
- Ensure all tests pass before submitting PR
- Test with both Gemini and HuggingFace providers

## Pull Request Process

1. Create a feature branch
2. Make your changes
3. Add/update tests
4. Update documentation
5. Submit PR with clear description

## Questions?

Open an issue or check the documentation in `docs/`
