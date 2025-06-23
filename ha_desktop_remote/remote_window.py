"""
Remote Window for Home Assistant Desktop Remote Control

Main window interface for the Home Assistant Desktop Remote Control application.
"""

import sys
import requests
import threading
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QGridLayout,
                               QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, QMessageBox)
from PySide6.QtGui import QKeyEvent, QPalette, QIcon
from PySide6.QtCore import Qt, QTimer

from .remote_manager import load_remotes, save_remotes
from .remote_wizard import RemoteWizard
from . import __version__

class RemoteWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Home Assistant Desktop Remote Control v{__version__}")
        self.setFixedSize(350, 600)  # Increased width and height for dropdown
        
        # Set window icon if available
        try:
            icon_path = "images/logo.png"
            if QIcon(icon_path).isNull() == False:
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass  # Icon not found, continue without it
        
        # Load remotes and initialize connection variables
        self.remotes = load_remotes()
        self.ha_url = None
        self.headers = {}
        self.entity_id = None
        self.session = requests.Session()
        
        # Dictionary to store button references for visual feedback
        self.command_buttons = {}
        
        # Initialize feedback state
        self._showing_feedback = False
        
        self.init_ui()
        self.apply_styles()
        # Enable keyboard focus so the widget can receive key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Ensure the window gets focus when shown
        self.setFocus()
        
        # Install event filter to ensure keyboard events always reach the main window
        self.installEventFilter(self)
        
        # Note: Removed theme event filter as it was causing unresponsiveness on theme changes
        # The application will respect the initial theme when started

    def showEvent(self, event):
        """Override showEvent to ensure keyboard focus when window is shown"""
        super().showEvent(event)
        # Use a timer to ensure focus is set after the window is fully shown
        QTimer.singleShot(100, self.ensure_keyboard_focus)

    def changeEvent(self, event):
        """Override changeEvent to handle window activation"""
        super().changeEvent(event)
        if event.type() == event.Type.ActivationChange and self.isActiveWindow():
            self.ensure_keyboard_focus()
        

    def send_remote_command(self, command):
        # Send command asynchronously to avoid blocking the UI
        def send_async():
            try:
                data = {
                    "entity_id": self.entity_id,
                    "command": command
                }
                response = self.session.post(
                    f"{self.ha_url}/api/services/remote/send_command",
                    json=data,
                    timeout=1  # Reduced timeout for faster response
                )
                print(f"Sent: {command} - Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending command {command}: {e}")
        
        # Run in background thread so UI stays responsive
        thread = threading.Thread(target=send_async, daemon=True)
        thread.start()

    def send_command_and_refocus(self, command):
        """Send command and return focus to main window for keyboard input"""
        self.send_remote_command(command)
        self.ensure_keyboard_focus()

    def ensure_keyboard_focus(self):
        """Ensure the main window has keyboard focus for remote control"""
        self.setFocus()
        self.activateWindow()
        self.raise_()

    def animate_button_press(self, button):
        """Add visual feedback when button is pressed"""
        # Prevent multiple animations on the same button
        if hasattr(button, '_animating') and button._animating:
            return
            
        button._animating = True
        original_style = button.styleSheet()
        
        # Get button class for appropriate feedback color
        button_class = button.property("class")
        feedback_color = "#66BB6A"  # Default green
        
        # Use different colors based on button type for better visual distinction
        if button_class == "power":
            feedback_color = "#FF5722"  # Bright orange for power
        elif button_class == "dpad" or button_class == "dpad-center":
            feedback_color = "#2196F3"  # Bright blue for navigation
        elif button_class == "volume":
            feedback_color = "#FF9800"  # Orange for volume
        elif button_class == "media":
            feedback_color = "#9C27B0"  # Purple for media
        elif button_class == "app":
            feedback_color = "#E91E63"  # Pink for apps
        
        # Change button appearance temporarily - no layout-affecting properties
        button.setStyleSheet(original_style + f"""
            QPushButton {{
                background-color: {feedback_color};
                border-color: {feedback_color};
            }}
        """)
        
        # Reset after 150ms and clear animation flag
        def reset_button():
            button.setStyleSheet(original_style)
            button._animating = False
            
        QTimer.singleShot(150, reset_button)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input for remote control"""
        key = event.key()
        
        # Map keyboard keys to remote commands
        key_mappings = {
            int(Qt.Key.Key_Up): "DPAD_UP",
            int(Qt.Key.Key_Down): "DPAD_DOWN",
            int(Qt.Key.Key_Left): "DPAD_LEFT",
            int(Qt.Key.Key_Right): "DPAD_RIGHT",
            int(Qt.Key.Key_Return): "DPAD_CENTER",
            int(Qt.Key.Key_Enter): "DPAD_CENTER",
            int(Qt.Key.Key_Space): "DPAD_CENTER",
            int(Qt.Key.Key_Backspace): "BACK",
            int(Qt.Key.Key_Escape): "BACK",
            int(Qt.Key.Key_Home): "HOME",
            int(Qt.Key.Key_M): "MENU",
            int(Qt.Key.Key_P): "POWER",
            int(Qt.Key.Key_Plus): "VOLUME_UP",
            int(Qt.Key.Key_Minus): "VOLUME_DOWN",
            int(Qt.Key.Key_Equal): "VOLUME_UP",  # For + without shift
            int(Qt.Key.Key_Underscore): "VOLUME_DOWN"  # For -
        }
        
        # Send the command if the key is mapped
        if key in key_mappings:
            command = key_mappings[key]
            self.send_remote_command(command)
            
            # Update status label with current command
            self.update_status_label(command)
            
            # Trigger visual feedback for the corresponding button
            button = self.get_button_for_command(command)
            if button:
                self.animate_button_press(button)
            else:
                # Show visual feedback even if no button exists (e.g., for unmapped commands)
                self.show_keyboard_feedback(command)
            
            print(f"Keyboard shortcut: {event.text()} -> {command}")
        else:
            # Call parent implementation for unhandled keys
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Event filter to ensure keyboard events are handled by the main window"""
        if event.type() == event.Type.KeyPress:
            # Check if this is a key we want to handle for remote control
            key = event.key()
            remote_keys = {
                int(Qt.Key.Key_Up), int(Qt.Key.Key_Down), int(Qt.Key.Key_Left), int(Qt.Key.Key_Right),
                int(Qt.Key.Key_Return), int(Qt.Key.Key_Enter), int(Qt.Key.Key_Space),
                int(Qt.Key.Key_Backspace), int(Qt.Key.Key_Escape), int(Qt.Key.Key_Home),
                int(Qt.Key.Key_M), int(Qt.Key.Key_P), int(Qt.Key.Key_Plus), int(Qt.Key.Key_Minus),
                int(Qt.Key.Key_Equal), int(Qt.Key.Key_Underscore)
            }
            
            if key in remote_keys:
                # Handle the key event directly in the main window
                self.keyPressEvent(event)
                return True  # Event handled, don't pass to other widgets
        
        # For all other events, use default handling
        return super().eventFilter(obj, event)

    def get_button_for_command(self, command):
        """Get the button widget associated with a command for visual feedback"""
        return self.command_buttons.get(command)

    def update_status_label(self, command):
        """Update status label to show the current command"""
        if hasattr(self, 'status_label'):
            # Show the command briefly, then return to help text
            self.status_label.setText(f"Command: {command}")
            self.status_label.setStyleSheet("""
                QLabel[class="status"] {
                    background-color: #4CAF50;
                    border: 1px solid #66BB6A;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 9px;
                    color: #ffffff;
                    margin: 10px 0;
                }
            """)
            
            # Reset after 500ms
            def reset_status():
                self.status_label.setText("Use keyboard: ↑↓←→ Enter Esc Home M P +/-")
                self.status_label.setStyleSheet("")  # Reset to default styling
                
            QTimer.singleShot(500, reset_status)

    def show_keyboard_feedback(self, command):
        """Show visual feedback for keyboard commands without corresponding buttons"""
        # Prevent multiple feedback animations
        if hasattr(self, '_showing_feedback') and self._showing_feedback:
            return
            
        self._showing_feedback = True
        
        # Create a temporary visual indicator in the window title
        original_title = f"Home Assistant Desktop Remote Control v{__version__}"
        self.setWindowTitle(f"Home Assistant Desktop Remote Control v{__version__} - {command}")
        
        # Reset title and clear flag after 250ms
        def reset_feedback():
            self.setWindowTitle(original_title)
            self._showing_feedback = False
            
        QTimer.singleShot(250, reset_feedback)

    def create_button(self, text, command, style_class="normal"):
        """Create a styled button with command binding"""
        button = QPushButton(text)
        button.clicked.connect(lambda: self.button_pressed(button, command))
        button.setProperty("class", style_class)
        
        # Prevent buttons from stealing keyboard focus
        button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        
        # Store button reference for keyboard visual feedback
        self.command_buttons[command] = button
        
        return button

    def button_pressed(self, button, command):
        """Handle button press with animation and command"""
        self.animate_button_press(button)
        self.send_command_and_refocus(command)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Remote selection dropdown at the top
        remote_selection_layout = QVBoxLayout()
        remote_selection_layout.setSpacing(5)
        
        # Dropdown and buttons row
        dropdown_layout = QHBoxLayout()
        dropdown_layout.setSpacing(8)
        
        self.remote_dropdown = QComboBox()
        self.remote_dropdown.currentIndexChanged.connect(self.on_remote_selected)
        self.remote_dropdown.setMinimumHeight(30)
        self.remote_dropdown.setMinimumWidth(200)
        # Prevent dropdown from stealing focus for keyboard navigation
        self.remote_dropdown.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        dropdown_layout.addWidget(self.remote_dropdown, 1)  # Give it stretch factor
        
        self.add_remote_button = QPushButton("+")
        self.add_remote_button.setObjectName("add_remote_button")
        self.add_remote_button.clicked.connect(self.add_remote_with_focus_restore)
        self.add_remote_button.setFixedSize(30, 30)
        self.add_remote_button.setToolTip("Add Remote")
        self.add_remote_button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        dropdown_layout.addWidget(self.add_remote_button)
        
        self.edit_remote_button = QPushButton("✎")
        self.edit_remote_button.setObjectName("edit_remote_button")
        self.edit_remote_button.clicked.connect(self.edit_remote_with_focus_restore)
        self.edit_remote_button.setEnabled(False)
        self.edit_remote_button.setFixedSize(30, 30)
        self.edit_remote_button.setToolTip("Edit Remote")
        self.edit_remote_button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        dropdown_layout.addWidget(self.edit_remote_button)

        self.delete_remote_button = QPushButton("🗑️")
        self.delete_remote_button.setObjectName("delete_remote_button")
        self.delete_remote_button.clicked.connect(self.delete_remote_with_focus_restore)
        self.delete_remote_button.setEnabled(False)
        self.delete_remote_button.setFixedSize(30, 30)
        self.delete_remote_button.setToolTip("Delete Selected Remote")
        self.delete_remote_button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        dropdown_layout.addWidget(self.delete_remote_button)
        
        remote_selection_layout.addLayout(dropdown_layout)
        main_layout.addLayout(remote_selection_layout)
        
        # Populate the dropdown
        self.populate_remote_dropdown()

        # Top row with Power, Volume and Menu controls - align with D-pad frame
        from PySide6.QtWidgets import QSizePolicy

        # Use a QHBoxLayout for the top row, matching the implementation of the bottom button rows
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setSpacing(10)
        # Use the same margins as the nav/media rows for visual alignment
        top_controls_layout.setContentsMargins(0, 0, 0, 0)

        power_button = self.create_button("⏻", "POWER", "power")
        vol_down = self.create_button("VOL-", "VOLUME_DOWN", "volume")
        mute = self.create_button("MUTE", "MUTE", "volume")
        vol_up = self.create_button("VOL+", "VOLUME_UP", "volume")
        menu_button = self.create_button("MENU", "MENU", "menu")

        # Set all top row buttons to expanding horizontally and preferred vertically
        for btn in [power_button, vol_down, mute, vol_up, menu_button]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btn.setMinimumHeight(35)  # Match nav/media button height

        top_controls_layout.addWidget(power_button)
        top_controls_layout.addWidget(vol_down)
        top_controls_layout.addWidget(mute)
        top_controls_layout.addWidget(vol_up)
        top_controls_layout.addWidget(menu_button)
        main_layout.addLayout(top_controls_layout)

        # D-Pad section - using simple grid layout
        dpad_frame = QFrame()
        dpad_frame.setProperty("class", "dpad-frame")
        dpad_grid = QGridLayout(dpad_frame)
        dpad_grid.setHorizontalSpacing(10)  # Horizontal spacing between columns
        dpad_grid.setVerticalSpacing(15)    # Consistent vertical spacing
        dpad_grid.setContentsMargins(20, 20, 20, 20)  # Consistent padding around the frame
        
        # Create D-pad buttons
        up_button = self.create_button("▲", "DPAD_UP", "dpad")
        left_button = self.create_button("◀", "DPAD_LEFT", "dpad")
        center_button = self.create_button("OK", "DPAD_CENTER", "dpad-center")
        right_button = self.create_button("▶", "DPAD_RIGHT", "dpad")
        down_button = self.create_button("▼", "DPAD_DOWN", "dpad")
        
        # Add to grid - simple 3x3 layout
        dpad_grid.addWidget(up_button, 0, 1)
        dpad_grid.addWidget(left_button, 1, 0)
        dpad_grid.addWidget(center_button, 1, 1)
        dpad_grid.addWidget(right_button, 1, 2)
        dpad_grid.addWidget(down_button, 2, 1)
        
        # Set equal column widths and row heights
        dpad_grid.setColumnStretch(0, 1)
        dpad_grid.setColumnStretch(1, 1)
        dpad_grid.setColumnStretch(2, 1)
        dpad_grid.setRowStretch(0, 1)
        dpad_grid.setRowStretch(1, 1)
        dpad_grid.setRowStretch(2, 1)
        
        main_layout.addWidget(dpad_frame)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        back_button = self.create_button("BACK", "BACK", "nav")
        home_button = self.create_button("HOME", "HOME", "nav")
        nav_layout.addWidget(back_button)
        nav_layout.addWidget(home_button)
        main_layout.addLayout(nav_layout)

        # Media controls
        media_layout = QHBoxLayout()
        media_layout.setSpacing(10)
        rewind = self.create_button("⏪", "MEDIA_REWIND", "media")
        play_pause = self.create_button("⏯", "MEDIA_PLAY_PAUSE", "media")
        stop = self.create_button("⏹", "MEDIA_STOP", "media")
        fast_forward = self.create_button("⏩", "MEDIA_FAST_FORWARD", "media")
        
        media_layout.addWidget(rewind)
        media_layout.addWidget(play_pause)
        media_layout.addWidget(stop)
        media_layout.addWidget(fast_forward)
        main_layout.addLayout(media_layout)

        # Add keyboard status label at the bottom
        self.status_label = QLabel("Use keyboard: ↑↓←→ Enter Esc Home M P +/-")
        self.status_label.setProperty("class", "status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Add version label at the very bottom (discreet)
        self.version_label = QLabel(f"v{__version__}")
        self.version_label.setProperty("class", "version")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.version_label)

        self.setLayout(main_layout)

    def apply_styles(self):
        """Apply styling that respects the KDE system theme"""
        # Get the current palette to detect theme
        palette = self.palette()
        is_dark_theme = palette.color(QPalette.ColorRole.Window).lightness() < 128
        
        # Base styling that uses system palette colors
        base_styles = """
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: palette(window);
                color: palette(window-text);
            }
            
            QComboBox {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 4px 8px;
                color: palette(text);
                font-size: 10px;
                min-height: 20px;
            }
            
            QComboBox::drop-down {
                border-left: 1px solid palette(mid);
                width: 20px;
            }
            
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            
            QComboBox QAbstractItemView {
                background-color: palette(base);
                border: 1px solid palette(mid);
                selection-background-color: palette(highlight);
                color: palette(text);
            }
            
            QPushButton {
                border: 1px solid palette(mid);
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                font-weight: 500;
                background-color: palette(button);
                color: palette(button-text);
                min-height: 32px;
            }
            
            QPushButton:hover {
                background-color: palette(light);
                border-color: palette(dark);
            }
            
            QPushButton:pressed {
                background-color: palette(mid);
            }
            
            QPushButton[class="power"] {
                background-color: #d32f2f;
                border-color: #d32f2f;
                font-size: 24px;
                font-weight: bold;
                min-height: 30px;
                color: #ffffff;
            }
            
            QPushButton[class="power"]:hover {
                background-color: #c62828;
            }
            
            QPushButton[class="volume"] {
                background-color: palette(dark);
                border-color: palette(dark);
                font-size: 10px;
                min-height: 30px;
                color: #ffffff;
            }
            
            QPushButton[class="volume"]:hover {
                background-color: palette(shadow);
                color: #ffffff;
            }
            
            QPushButton[class="menu"] {
                background-color: #1976d2;
                border-color: #1976d2;
                font-size: 10px;
                min-height: 30px;
                color: #ffffff;
            }
            
            QPushButton[class="menu"]:hover {
                background-color: #1565c0;
            }
            
            QPushButton[class="dpad"] {
                background-color: palette(dark);
                border-color: palette(dark);
                font-size: 30px;
                min-width: 45px;
                min-height: 45px;
                border-radius: 4px;
                color: #ffffff;
            }
            
            QPushButton[class="dpad"]:hover {
                background-color: palette(shadow);
                color: #ffffff;
            }
            
            QPushButton[class="dpad-center"] {
                background-color: #388e3c;
                border-color: #388e3c;
                font-size: 11px;
                font-weight: bold;
                min-width: 45px;
                min-height: 45px;
                border-radius: 4px;
                color: #ffffff;
            }
            
            QPushButton[class="dpad-center"]:hover {
                background-color: #2e7d32;
            }
            
            QFrame[class="dpad-frame"] {
                background-color: palette(alternate-base);
                border: 1px solid palette(mid);
                border-radius: 8px;
                margin: 10px 0;
            }
            
            QPushButton[class="nav"] {
                background-color: palette(dark);
                border-color: palette(dark);
                min-width: 100px;
                font-size: 10px;
                min-height: 30px;
                color: #ffffff;
            }
            
            QPushButton[class="nav"]:hover {
                background-color: palette(shadow);
                color: #ffffff;
            }
            
            QPushButton[class="media"] {
                background-color: #5d4037;
                border-color: #5d4037;
                font-size: 28px;
                min-width: 50px;
                min-height: 35px;
                color: #ffffff;
            }
            
            QPushButton[class="media"]:hover {
                background-color: #6d4c41;
            }
            
            QPushButton[class="app"] {
                background-color: #7b1fa2;
                border-color: #7b1fa2;
                min-width: 100px;
                font-weight: bold;
                font-size: 11px;
                min-height: 35px;
                color: #ffffff;
            }
            
            QPushButton[class="app"]:hover {
                background-color: #8e24aa;
            }
            
            QLabel[class="status"] {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px;
                font-size: 9px;
                color: palette(text);
                margin: 10px 0;
            }
            
            QLabel[class="version"] {
                background-color: transparent;
                border: none;
                padding: 2px 8px;
                font-size: 8px;
                color: palette(mid);
                margin: 0px;
            }
            
            /* Specific styling for management buttons */
            QPushButton#add_remote_button,
            QPushButton#edit_remote_button,
            QPushButton#delete_remote_button {
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
                max-height: 30px;
                min-width: 30px;
                max-width: 30px;
                padding: 0px;
                color: palette(button-text);
            }
            
            QPushButton#add_remote_button:hover,
            QPushButton#edit_remote_button:hover,
            QPushButton#delete_remote_button:hover {
                background-color: palette(light);
            }
            
            QPushButton#add_remote_button:disabled,
            QPushButton#edit_remote_button:disabled,
            QPushButton#delete_remote_button:disabled {
                background-color: palette(mid);
                color: palette(dark);
            }
        """
        
        # Apply theme-specific adjustments if needed
        if is_dark_theme:
            # For dark themes, we might want to adjust some colors slightly
            theme_adjustments = """
                QLabel[class="status"] {
                    color: palette(bright-text);
                }
            """
        else:
            # For light themes
            theme_adjustments = """
                QLabel[class="status"] {
                    color: palette(dark);
                }
            """
        
        self.setStyleSheet(base_styles + theme_adjustments)

    def populate_remote_dropdown(self):
        """Populate the dropdown with available remotes"""
        self.remote_dropdown.clear()
        
        if not self.remotes:
            self.remote_dropdown.addItem("No remotes configured")
            self.edit_remote_button.setEnabled(False)
            self.delete_remote_button.setEnabled(False)
        else:
            for remote in self.remotes:
                self.remote_dropdown.addItem(remote["name"], remote)
            self.edit_remote_button.setEnabled(True)
            self.delete_remote_button.setEnabled(True)
            # Auto-select first remote if available
            if len(self.remotes) > 0:
                self.remote_dropdown.setCurrentIndex(0)
                self.on_remote_selected(0)

    def on_remote_selected(self, index):
        """Handle remote selection from dropdown"""
        if index >= 0 and self.remotes:
            selected_remote = self.remote_dropdown.currentData()
            if selected_remote:
                self.ha_url = selected_remote["ha_url"]
                self.entity_id = selected_remote["entity_id"]
                self.headers = {
                    "Authorization": f"Bearer {selected_remote['token']}",
                    "content-type": "application/json",
                }
                self.session.headers.update(self.headers)
                print(f"Connected to remote: {selected_remote['name']}")
        else:
            self.ha_url = None
            self.entity_id = None
            self.headers = {}
        
        # Restore keyboard focus after dropdown selection
        self.ensure_keyboard_focus()

    def add_remote_with_focus_restore(self):
        """Open wizard to add a new remote and restore focus"""
        self.add_remote()
        self.ensure_keyboard_focus()

    def edit_remote_with_focus_restore(self):
        """Open wizard to edit the selected remote and restore focus"""
        self.edit_remote()
        self.ensure_keyboard_focus()

    def delete_remote_with_focus_restore(self):
        """Delete the currently selected remote and restore focus"""
        self.delete_remote()
        self.ensure_keyboard_focus()

    def add_remote(self):
        """Open wizard to add a new remote"""
        wizard = RemoteWizard(parent=self)
        wizard.remote_saved.connect(self.handle_remote_saved, Qt.ConnectionType.UniqueConnection)
        result = wizard.exec()
        # Explicitly disconnect to prevent multiple connections on Windows
        wizard.remote_saved.disconnect(self.handle_remote_saved)

    def edit_remote(self):
        """Open wizard to edit the selected remote"""
        current_index = self.remote_dropdown.currentIndex()
        if current_index >= 0 and self.remotes:
            remote_to_edit = self.remotes[current_index]
            wizard = RemoteWizard(remote_data=remote_to_edit, remote_index=current_index, parent=self)
            wizard.remote_saved.connect(self.handle_remote_saved, Qt.ConnectionType.UniqueConnection)
            result = wizard.exec()
            # Explicitly disconnect to prevent multiple connections on Windows
            wizard.remote_saved.disconnect(self.handle_remote_saved)

    def handle_remote_saved(self, saved_remote, remote_index):
        """Handle when a remote is saved from the wizard"""
        # Prevent multiple dialogs by checking if we're already processing
        if hasattr(self, '_processing_remote_save') and self._processing_remote_save:
            return
        
        self._processing_remote_save = True
        
        try:
            if remote_index == -1:  # New remote
                self.remotes.append(saved_remote)
                message = f"Remote '{saved_remote['name']}' added successfully!"
            else:  # Existing remote edited
                self.remotes[remote_index] = saved_remote
                message = f"Remote '{saved_remote['name']}' updated successfully!"
            
            save_remotes(self.remotes)
            self.populate_remote_dropdown()
            
            # Select the newly added/edited remote
            if remote_index == -1:
                self.remote_dropdown.setCurrentIndex(len(self.remotes) - 1)
            else:
                self.remote_dropdown.setCurrentIndex(remote_index)
            
            
            # Restore keyboard focus after dialog closes
            self.ensure_keyboard_focus()
        finally:
            # Always reset the flag
            self._processing_remote_save = False

    def delete_remote(self):
        """Delete the currently selected remote"""
        current_index = self.remote_dropdown.currentIndex()
        if current_index >= 0 and self.remotes:
            remote_to_delete = self.remotes[current_index]
            
            reply = QMessageBox.question(self, "Delete Remote",
                                        f"Are you sure you want to delete '{remote_to_delete['name']}'?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                del self.remotes[current_index]
                save_remotes(self.remotes)
                self.populate_remote_dropdown()
                
                # If there are still remotes, select the first one, otherwise show "No remotes"
                if self.remotes:
                    self.remote_dropdown.setCurrentIndex(0)
                    self.on_remote_selected(0)
                else:
                    self.on_remote_selected(-1) # Clear current selection
                
                QMessageBox.information(self, "Success", f"Remote '{remote_to_delete['name']}' deleted successfully!")
                
                # Restore keyboard focus after dialog closes
                self.ensure_keyboard_focus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RemoteWindow()
    window.show()
    sys.exit(app.exec())