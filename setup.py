#!/usr/bin/env python3
"""
Setup script for Home Assistant Desktop Remote Control
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="ha-desktop-remote",
    version="1.0.0",
    author="David Markey",
    author_email="david@dmarkey.com",
    description="Desktop remote control application for Home Assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dmarkey/ha-desktop-remote",
    project_urls={
        "Bug Reports": "https://github.com/dmarkey/ha-desktop-remote/issues",
        "Source": "https://github.com/dmarkey/ha-desktop-remote",
        "Documentation": "https://github.com/dmarkey/ha-desktop-remote#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Home Automation",
        "Topic :: Multimedia",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    keywords="home-assistant remote control desktop gui qt pyside6 automation smart-home",
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-qt>=4.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
    },
    entry_points={
        "gui_scripts": [
            "ha-desktop-remote=ha_desktop_remote.main:main",
        ],
    },
    package_data={
        "ha_desktop_remote": ["*.png", "*.ico", "*.svg"],
    },
    include_package_data=True,
    zip_safe=False,
    platforms=["any"],
)