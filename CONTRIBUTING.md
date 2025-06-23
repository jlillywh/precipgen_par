# Contributing to PrecipGenPAR

Thank you for considering contributing to PrecipGenPAR! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

1. **Search existing issues** first to see if your problem has already been reported
2. **Create a detailed issue** with:
   - Clear description of the problem
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Sample data or code if applicable

### Submitting Changes

1. **Fork the repository** and create a new branch from `main`
2. **Make your changes** with clear, concise commits
3. **Add tests** for any new functionality
4. **Run the test suite** to ensure all tests pass
5. **Update documentation** if needed
6. **Submit a pull request** with:
   - Clear description of changes
   - Reference to related issues
   - Test results

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/precipgen_par.git
   cd precipgen_par
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run tests:
   ```bash
   python -m unittest discover tests
   ```

### Code Style Guidelines

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and concise
- Include type hints where appropriate

### Testing

- Write unit tests for all new functionality
- Ensure all existing tests continue to pass
- Aim for high test coverage
- Test edge cases and error conditions

### Documentation

- Update README.md for significant changes
- Add docstrings to new functions and classes
- Update CHANGELOG.md for notable changes
- Include usage examples for new features

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment for all contributors

## Questions?

If you have questions about contributing, please:
- Check the existing documentation
- Search for similar issues or discussions
- Open an issue with the "question" label

Thank you for contributing to PrecipGenPAR!
