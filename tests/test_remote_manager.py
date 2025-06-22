"""
Tests for the remote manager module
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from ha_desktop_remote.remote_manager import (
    RemoteManager,
    load_remotes,
    save_remotes,
    get_config_dir,
    get_remotes_file
)


def test_get_config_dir():
    """Test that config directory is determined correctly"""
    config_dir = get_config_dir()
    assert isinstance(config_dir, Path)
    assert config_dir.exists()


def test_load_remotes_empty():
    """Test loading remotes when file doesn't exist"""
    with patch('ha_desktop_remote.remote_manager.get_remotes_file') as mock_file:
        mock_file.return_value = Path("/nonexistent/file.json")
        remotes = load_remotes()
        assert remotes == []


def test_save_and_load_remotes():
    """Test saving and loading remotes"""
    test_remotes = [
        {
            "name": "Test Remote",
            "ha_url": "https://test.local:8123",
            "token": "test_token",
            "entity_id": "remote.test"
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = Path(f.name)
    
    try:
        with patch('ha_desktop_remote.remote_manager.get_remotes_file') as mock_file:
            mock_file.return_value = temp_file
            
            # Test saving
            save_remotes(test_remotes)
            assert temp_file.exists()
            
            # Test loading
            loaded_remotes = load_remotes()
            assert loaded_remotes == test_remotes
    finally:
        temp_file.unlink(missing_ok=True)


def test_remote_manager():
    """Test RemoteManager class functionality"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = Path(f.name)
    
    try:
        with patch('ha_desktop_remote.remote_manager.get_remotes_file') as mock_file:
            mock_file.return_value = temp_file
            
            # Initialize with empty file
            temp_file.write_text("[]")
            
            manager = RemoteManager()
            assert manager.get_remotes() == []
            
            # Add a remote
            test_remote = {
                "name": "Test Remote",
                "ha_url": "https://test.local:8123",
                "token": "test_token",
                "entity_id": "remote.test"
            }
            
            manager.add_remote(test_remote)
            assert len(manager.get_remotes()) == 1
            assert manager.get_remotes()[0] == test_remote
            
            # Update the remote
            updated_remote = test_remote.copy()
            updated_remote["name"] = "Updated Remote"
            
            manager.update_remote(0, updated_remote)
            assert manager.get_remotes()[0]["name"] == "Updated Remote"
            
            # Delete the remote
            manager.delete_remote(0)
            assert manager.get_remotes() == []
            
    finally:
        temp_file.unlink(missing_ok=True)


def test_remote_manager_invalid_operations():
    """Test RemoteManager with invalid operations"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = Path(f.name)
    
    try:
        with patch('ha_desktop_remote.remote_manager.get_remotes_file') as mock_file:
            mock_file.return_value = temp_file
            temp_file.write_text("[]")
            
            manager = RemoteManager()
            
            # Try to update/delete non-existent remote
            manager.update_remote(999, {"name": "test"})  # Should not crash
            manager.delete_remote(999)  # Should not crash
            
            assert manager.get_remotes() == []
            
    finally:
        temp_file.unlink(missing_ok=True)