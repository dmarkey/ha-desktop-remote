# Contributing to Home Assistant Desktop Remote Control

Thank you for your interest in contributing to the Home Assistant Desktop Remote Control project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A Home Assistant instance for testing (optional but recommended)

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/dmarkey/ha-desktop-remote.git
   cd ha-desktop-remote
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

5. **Run the application**:
   ```bash
   python -m ha_desktop_remote.main
   # or
   ha-desktop-remote
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ha_desktop_remote

# Run specific test file
pytest tests/test_remote_manager.py
```

### Manual Testing

1. **Test the setup wizard**:
   - Delete your config file (see README for location)
   - Run the application and go through the setup process

2. **Test remote functionality**:
   - Configure a remote pointing to your Home Assistant
   - Test all buttons and keyboard shortcuts

3. **Test cross-platform compatibility** (if possible):
   - Test on different operating systems
   - Verify config directory creation works correctly

## 🎨 Code Style

We use several tools to maintain code quality:

### Formatting

```bash
# Format code with Black
black ha_desktop_remote/ tests/

# Sort imports with isort
isort ha_desktop_remote/ tests/
```

### Linting

```bash
# Check code style with flake8
flake8 ha_desktop_remote/ tests/

# Type checking with mypy
mypy ha_desktop_remote/
```

### Pre-commit Hooks

We recommend using pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 📝 Coding Guidelines

### Python Code

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Qt/PySide6 Code

- Use proper signal/slot connections
- Handle Qt events appropriately
- Ensure UI remains responsive (use threads for long operations)
- Follow Qt naming conventions for UI elements

### Example Code Style

```python
def send_remote_command(self, command: str) -> None:
    """Send a command to the Home Assistant remote entity.
    
    Args:
        command: The remote command to send (e.g., 'POWER', 'VOLUME_UP')
    """
    def send_async() -> None:
        try:
            data = {
                "entity_id": self.entity_id,
                "command": command
            }
            response = self.session.post(
                f"{self.ha_url}/api/services/remote/send_command",
                json=data,
                timeout=1
            )
            print(f"Sent: {command} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending command {command}: {e}")
    
    # Run in background thread so UI stays responsive
    thread = threading.Thread(target=send_async, daemon=True)
    thread.start()
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**:
   - Operating system and version
   - Python version
   - PySide6 version
   - Home Assistant version

2. **Steps to reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior
   - Screenshots if applicable

3. **Logs and error messages**:
   - Console output
   - Error tracebacks
   - Home Assistant logs if relevant

## ✨ Feature Requests

When suggesting new features:

1. **Describe the use case**: Why is this feature needed?
2. **Provide examples**: How would it work?
3. **Consider alternatives**: Are there other ways to achieve the same goal?
4. **Think about implementation**: How complex would this be to implement?

## 🔄 Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**:
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black --check ha_desktop_remote/ tests/
   flake8 ha_desktop_remote/ tests/
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

### PR Guidelines

- **Clear title and description**: Explain what the PR does and why
- **Reference issues**: Link to related issues using `#issue-number`
- **Keep PRs focused**: One feature or fix per PR
- **Update documentation**: Include README updates if needed
- **Add tests**: Ensure new code is tested

## 📚 Documentation

### Code Documentation

- Use clear, descriptive docstrings
- Include parameter and return type information
- Provide usage examples for complex functions

### User Documentation

- Update README.md for user-facing changes
- Include screenshots for UI changes
- Update installation instructions if needed

## 🏗️ Architecture

### Project Structure

```
ha-desktop-remote/
├── ha_desktop_remote/          # Main package
│   ├── __init__.py            # Package initialization
│   ├── main.py                # Application entry point
│   ├── remote_manager.py      # Configuration management
│   ├── remote_window.py       # Main UI window
│   └── remote_wizard.py       # Setup wizard
├── tests/                     # Test suite
├── images/                    # Application assets
├── README.md                  # User documentation
├── CONTRIBUTING.md           # This file
├── setup.py                  # Package setup
├── pyproject.toml           # Modern Python packaging
└── requirements.txt         # Dependencies
```

### Key Components

1. **RemoteManager**: Handles configuration loading/saving with cross-platform support
2. **RemoteWindow**: Main application window with remote control interface
3. **RemoteWizard**: Multi-step setup wizard for adding new remotes
4. **Main**: Application entry point and Qt setup

## 🤝 Community

- **Be respectful**: Follow the code of conduct
- **Be helpful**: Assist other contributors when possible
- **Be patient**: Reviews and responses may take time
- **Be collaborative**: Work together to improve the project

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in the project README and release notes. Thank you for helping make this project better!