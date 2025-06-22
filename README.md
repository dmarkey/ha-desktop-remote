# Home Assistant Desktop Remote Control

<div align="center">
  <img src="images/logo.png" alt="Home Assistant Desktop Remote Control Logo" width="128" height="128">
  
  <h3>🏠 A Beautiful Desktop Remote Control for Home Assistant</h3>
  
  <p>Control your Home Assistant media players and devices with an intuitive, cross-platform desktop application.</p>
  
  [![PyPI version](https://badge.fury.io/py/ha-desktop-remote.svg)](https://badge.fury.io/py/ha-desktop-remote)
  [![Python Support](https://img.shields.io/pypi/pyversions/ha-desktop-remote.svg)](https://pypi.org/project/ha-desktop-remote/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Platform Support](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/dmarkey/ha-desktop-remote)
</div>

## ✨ Features

- **🎮 Intuitive Remote Interface**: Clean, modern UI with familiar remote control layout
- **⌨️ Keyboard Shortcuts**: Full keyboard navigation support for quick control
- **🌈 System Theme Integration**: Automatically adapts to your system's light/dark theme
- **🔧 Easy Setup Wizard**: Step-by-step configuration with automatic entity discovery
- **📱 Multiple Remote Support**: Manage and switch between multiple Home Assistant remotes
- **🔒 Secure Authentication**: Uses Home Assistant's long-lived access tokens
- **🖥️ Cross-Platform**: Works on Windows, macOS, and Linux
- **⚡ Responsive Design**: Fast, non-blocking command execution

## 📸 Screenshot

<div align="center">
  <img src="images/screenshot.png" alt="Home Assistant Desktop Remote Control Interface" width="600">
  <p><em>Clean, intuitive remote control interface with familiar button layout</em></p>
</div>

## 🚀 Quick Start

### Installation

Install from PyPI using pip:

```bash
pip install ha-desktop-remote
```

### Launch the Application

After installation, you can launch the application:

```bash
ha-desktop-remote
```

### First-Time Setup

1. **Launch the application** - You'll see the main remote interface
2. **Click the "+" button** to add your first remote
3. **Enter your Home Assistant details**:
   - Home Assistant URL (e.g., `https://homeassistant.local:8123`)
   - Long-lived access token (create one in HA: Profile → Security → Long-Lived Access Tokens)
4. **Select your remote entity** from the discovered devices
5. **Give your remote a name** and you're ready to go!

## 🎮 Usage

### Remote Controls

The application provides a full-featured remote control interface:

#### Physical Buttons
- **Power Button**: Turn devices on/off
- **Volume Controls**: Volume up/down and mute
- **D-Pad Navigation**: Up, down, left, right, and OK/Enter
- **Navigation**: Back and Home buttons
- **Media Controls**: Play/pause, stop, rewind, fast forward

#### Keyboard Shortcuts
- **Arrow Keys**: Navigate (↑↓←→)
- **Enter/Space**: OK/Select
- **Escape/Backspace**: Back
- **Home**: Home button
- **M**: Menu
- **P**: Power
- **+/-**: Volume up/down

### Managing Remotes

- **Add Remote**: Click the "+" button to add a new remote
- **Edit Remote**: Click the "✎" button to modify an existing remote
- **Delete Remote**: Click the "🗑️" button to remove a remote
- **Switch Remotes**: Use the dropdown to switch between configured remotes

## 🔧 Configuration

### Home Assistant Setup

1. **Create a Long-Lived Access Token**:
   - Go to your Home Assistant profile
   - Navigate to Security → Long-Lived Access Tokens
   - Click "Create Token"
   - Give it a descriptive name like "Desktop Remote"
   - Copy the generated token

2. **Ensure Remote Entities are Available**:
   - Your media players should appear as `remote.*` entities
   - Common examples: `remote.living_room_tv`, `remote.bedroom_chromecast`

### Application Configuration

Configuration files are stored in platform-appropriate locations:

- **Windows**: `%APPDATA%\HomeAssistantDesktopRemote\remotes.json`
- **macOS**: `~/Library/Application Support/HomeAssistantDesktopRemote/remotes.json`
- **Linux**: `~/.config/ha-desktop-remote/remotes.json`

## 🛠️ Development

### Prerequisites

- Python 3.8 or higher
- PySide6
- requests

### Setting up Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dmarkey/ha-desktop-remote.git
   cd ha-desktop-remote
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python -m ha_desktop_remote.main
   ```

### Building for Distribution

```bash
# Install build dependencies
pip install build twine

# Build the package
python -m build

# Upload to PyPI (maintainers only)
twine upload dist/*
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests if applicable
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to new functions and classes
- Test your changes on multiple platforms if possible
- Update documentation for new features

## 📋 Requirements

- **Python**: 3.8 or higher
- **PySide6**: Qt6 bindings for Python
- **requests**: HTTP library for API communication
- **Home Assistant**: Compatible with Home Assistant Core

### Supported Platforms

- **Windows**: Windows 10/11
- **macOS**: macOS 10.14 (Mojave) or later
- **Linux**: Most modern distributions with Qt6 support

## 🐛 Troubleshooting

### Common Issues

**Connection Failed**
- Verify your Home Assistant URL is correct and accessible
- Check that your access token is valid and not expired
- Ensure Home Assistant is running and reachable from your network

**No Remote Entities Found**
- Make sure your media players are configured in Home Assistant
- Check that they appear as `remote.*` entities in Developer Tools → States
- Some devices may need specific integrations to expose remote functionality

**Application Won't Start**
- Ensure Python 3.8+ is installed
- Try reinstalling: `pip uninstall ha-desktop-remote && pip install ha-desktop-remote`
- Check for Qt6/PySide6 compatibility issues on your system

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/dmarkey/ha-desktop-remote/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dmarkey/ha-desktop-remote/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Home Assistant Team**: For creating an amazing home automation platform
- **Qt/PySide6**: For providing excellent cross-platform GUI framework
- **Contributors**: Everyone who has contributed to making this project better

## 🔗 Links

- **PyPI Package**: [ha-desktop-remote](https://pypi.org/project/ha-desktop-remote/)
- **GitHub Repository**: [dmarkey/ha-desktop-remote](https://github.com/dmarkey/ha-desktop-remote)
- **Home Assistant**: [home-assistant.io](https://www.home-assistant.io/)

---

<div align="center">
  <p>Made with ❤️ for the Home Assistant community</p>
</div>