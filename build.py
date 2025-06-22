#!/usr/bin/env python3
"""
Build script for Home Assistant Desktop Remote Control

This script helps build and prepare the package for PyPI distribution.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stderr)
        return False


def clean_build():
    """Clean previous build artifacts"""
    print("\n🧹 Cleaning previous build artifacts...")
    
    dirs_to_clean = ["build", "dist", "*.egg-info"]
    for pattern in dirs_to_clean:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"   Removed directory: {path}")
            elif path.is_file():
                path.unlink()
                print(f"   Removed file: {path}")


def check_requirements():
    """Check if build requirements are installed"""
    print("\n📋 Checking build requirements...")
    
    required_packages = ["build", "twine"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        cmd = f"{sys.executable} -m pip install {' '.join(missing_packages)}"
        if not run_command(cmd, "Installing build dependencies"):
            return False
    
    return True


def build_package():
    """Build the package"""
    return run_command(f"{sys.executable} -m build", "Building package")


def check_package():
    """Check the built package"""
    return run_command("twine check dist/*", "Checking package")


def upload_to_test_pypi():
    """Upload to Test PyPI"""
    print("\n⚠️  This will upload to Test PyPI. Continue? (y/N): ", end="")
    if input().lower() != 'y':
        print("Upload cancelled.")
        return True
    
    return run_command("twine upload --repository testpypi dist/*", "Uploading to Test PyPI")


def upload_to_pypi():
    """Upload to PyPI"""
    print("\n⚠️  This will upload to PyPI. This action cannot be undone! Continue? (y/N): ", end="")
    if input().lower() != 'y':
        print("Upload cancelled.")
        return True
    
    return run_command("twine upload dist/*", "Uploading to PyPI")


def main():
    """Main build process"""
    print("🏠 Home Assistant Desktop Remote Control - Build Script")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
    else:
        print("\nAvailable actions:")
        print("  build       - Clean, build, and check package")
        print("  test-upload - Upload to Test PyPI")
        print("  upload      - Upload to PyPI")
        print("  clean       - Clean build artifacts only")
        print("\nUsage: python build.py [action]")
        action = input("\nEnter action (or press Enter for 'build'): ").lower() or "build"
    
    if action == "clean":
        clean_build()
        print("\n✅ Clean completed!")
        return
    
    # Standard build process
    if action in ["build", "test-upload", "upload"]:
        steps = [
            (clean_build, "Clean build artifacts"),
            (check_requirements, "Check requirements"),
            (build_package, "Build package"),
            (check_package, "Check package"),
        ]
        
        for step_func, step_name in steps:
            if not step_func():
                print(f"\n❌ Build failed at step: {step_name}")
                sys.exit(1)
        
        print("\n✅ Package built successfully!")
        
        # Additional actions
        if action == "test-upload":
            upload_to_test_pypi()
        elif action == "upload":
            upload_to_pypi()
    
    else:
        print(f"❌ Unknown action: {action}")
        sys.exit(1)
    
    print("\n🎉 Build process completed!")


if __name__ == "__main__":
    main()