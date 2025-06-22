"""
Remote Wizard for Home Assistant Desktop Remote Control

Setup wizard for configuring new remote connections to Home Assistant.
"""

import requests
from PySide6.QtWidgets import (QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget,
                                QPushButton, QLabel, QLineEdit, QListWidget,
                                QListWidgetItem, QMessageBox, QProgressBar, QTextEdit, QFrame,
                                QCheckBox)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QPalette

class ConnectionTestThread(QThread):
    """Thread for testing Home Assistant connection without blocking UI"""
    connection_result = Signal(bool, str, list)  # success, message, entities
    
    def __init__(self, ha_url, token):
        super().__init__()
        self.ha_url = ha_url
        self.token = token
    
    def run(self):
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "content-type": "application/json",
            }
            response = requests.get(f"{self.ha_url}/api/states", headers=headers, timeout=10)
            response.raise_for_status()
            states = response.json()
            
            remote_entities_data = []
            for state in states:
                entity_id = state["entity_id"]
                if entity_id.startswith("remote."):
                    attributes = state.get("attributes", {})
                    friendly_name = attributes.get("friendly_name", entity_id)
                    entity_state = state.get("state", "unknown")
                    
                    # Include state information in display
                    status_indicator = "🟢" if entity_state != "unavailable" else "🔴"
                    display_name = f"{status_indicator} {friendly_name} - {entity_id}"
                    
                    remote_entities_data.append((display_name, entity_id, entity_state))
            
            if remote_entities_data:
                self.connection_result.emit(True, "Connection successful!", remote_entities_data)
            else:
                self.connection_result.emit(False, "No remote entities found in Home Assistant.", [])
                
        except requests.exceptions.ConnectionError:
            self.connection_result.emit(False, "Could not connect to Home Assistant. Check URL and network.", [])
        except requests.exceptions.Timeout:
            self.connection_result.emit(False, "Request to Home Assistant timed out.", [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.connection_result.emit(False, "Authentication failed. Check your access token.", [])
            else:
                self.connection_result.emit(False, f"HTTP Error {e.response.status_code}: {e}", [])
        except requests.exceptions.RequestException as e:
            self.connection_result.emit(False, f"Error connecting to Home Assistant: {e}", [])
        except Exception as e:
            self.connection_result.emit(False, f"Unexpected error: {e}", [])

class RemoteWizard(QDialog):
    remote_saved = Signal(dict, int) # Signal to emit when a remote is saved (added or edited)

    def __init__(self, remote_data=None, remote_index=-1, parent=None):
        super().__init__(parent)
        self.remote_data = remote_data
        self.remote_index = remote_index
        self.connection_thread = None
        self.current_step = 0
        self.total_steps = 3
        self.all_entities_data = []  # Store all entities for filtering

        if self.remote_data:
            self.setWindowTitle("Edit Remote Configuration - Home Assistant Desktop Remote")
            self.ha_url = self.remote_data.get("ha_url", "")
            self.token = self.remote_data.get("token", "")
            self.entity_id = self.remote_data.get("entity_id", "")
            self.remote_name = self.remote_data.get("name", "")
        else:
            self.setWindowTitle("Add New Remote - Home Assistant Desktop Remote")
            self.ha_url = ""
            self.token = ""
            self.entity_id = ""
            self.remote_name = ""

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }
        
        # Set dialog properties for better UX
        self.setModal(True)
        self.setFixedSize(500, 650)
        
        self.stacked_widget = QStackedWidget()
        self.init_ui()
        self.apply_styles()
        self.setup_input_validation()
        
        # Set initial focus
        QTimer.singleShot(100, lambda: self.ha_url_input.setFocus())
        
        # Note: Removed event filter as it was causing unresponsiveness on theme changes
        # The wizard will respect the initial theme when opened

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Progress indicator at the top
        self.progress_frame = QFrame()
        self.progress_frame.setProperty("class", "progress-frame")
        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(15, 10, 15, 10)
        
        self.progress_label = QLabel("Step 1 of 3: Connection Details")
        self.progress_label.setProperty("class", "progress-label")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.total_steps)
        self.progress_bar.setValue(1)
        self.progress_bar.setProperty("class", "progress-bar")
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(self.progress_frame)
        main_layout.addWidget(self.stacked_widget)

        # Page 1: Connection Details
        self.page1 = QWidget()
        page1_layout = QVBoxLayout()
        page1_layout.setSpacing(15)
        page1_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title and description
        title_label = QLabel("🏠 Home Assistant Connection")
        title_label.setProperty("class", "page-title")
        page1_layout.addWidget(title_label)
        
        desc_label = QLabel("Connect to your Home Assistant instance to discover remote entities.")
        desc_label.setProperty("class", "page-description")
        desc_label.setWordWrap(True)
        page1_layout.addWidget(desc_label)
        
        # URL input with help text
        url_label = QLabel("Home Assistant URL:")
        url_label.setProperty("class", "field-label")
        page1_layout.addWidget(url_label)
        
        self.ha_url_input = QLineEdit(self.ha_url)
        self.ha_url_input.setPlaceholderText("https://homeassistant.local:8123")
        self.ha_url_input.setProperty("class", "input-field")
        page1_layout.addWidget(self.ha_url_input)
        
        url_help = QLabel("💡 Include the full URL with protocol (http:// or https://)")
        url_help.setProperty("class", "help-text")
        page1_layout.addWidget(url_help)

        # Token input with help text
        token_label = QLabel("Long-Lived Access Token:")
        token_label.setProperty("class", "field-label")
        page1_layout.addWidget(token_label)
        
        self.token_input = QLineEdit(self.token)
        self.token_input.setPlaceholderText("Enter your Home Assistant access token")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setProperty("class", "input-field")
        page1_layout.addWidget(self.token_input)
        
        token_help = QLabel("💡 Create this in Home Assistant: Profile → Security → Long-Lived Access Tokens")
        token_help.setProperty("class", "help-text")
        token_help.setWordWrap(True)
        page1_layout.addWidget(token_help)
        
        # Connection status area
        self.connection_status = QLabel("")
        self.connection_status.setProperty("class", "status-message")
        self.connection_status.setWordWrap(True)
        self.connection_status.hide()
        page1_layout.addWidget(self.connection_status)
        
        # Progress bar for connection testing
        self.connection_progress = QProgressBar()
        self.connection_progress.setRange(0, 0)  # Indeterminate progress
        self.connection_progress.hide()
        page1_layout.addWidget(self.connection_progress)

        page1_layout.addStretch()
        
        # Buttons
        page1_buttons_layout = QHBoxLayout()
        self.next_button_page1 = QPushButton("Test Connection & Continue")
        self.next_button_page1.setProperty("class", "primary-button")
        self.next_button_page1.clicked.connect(self.validate_page1)
        page1_buttons_layout.addStretch()
        page1_buttons_layout.addWidget(self.next_button_page1)
        page1_layout.addLayout(page1_buttons_layout)
        
        self.page1.setLayout(page1_layout)
        self.stacked_widget.addWidget(self.page1)

        # Page 2: Entity Selection
        self.page2 = QWidget()
        page2_layout = QVBoxLayout()
        page2_layout.setSpacing(15)
        page2_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title and description
        title_label2 = QLabel("📺 Select Remote Entity")
        title_label2.setProperty("class", "page-title")
        page2_layout.addWidget(title_label2)
        
        desc_label2 = QLabel("Choose the remote entity you want to control from the list below.")
        desc_label2.setProperty("class", "page-description")
        desc_label2.setWordWrap(True)
        page2_layout.addWidget(desc_label2)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        entity_label = QLabel("Available Remote Entities:")
        entity_label.setProperty("class", "field-label")
        filter_layout.addWidget(entity_label)
        
        filter_layout.addStretch()
        
        self.show_active_only = QCheckBox("Show active entities only")
        self.show_active_only.setProperty("class", "filter-checkbox")
        self.show_active_only.setChecked(True)  # Default to showing active only
        self.show_active_only.stateChanged.connect(self.filter_entities)
        filter_layout.addWidget(self.show_active_only)
        
        page2_layout.addLayout(filter_layout)
        
        self.entity_list = QListWidget()
        self.entity_list.setProperty("class", "entity-list")
        self.entity_list.itemDoubleClicked.connect(self.select_entity_from_list)
        self.entity_list.setMinimumHeight(200)
        page2_layout.addWidget(self.entity_list)
        
        entity_help = QLabel("💡 Double-click an entity to select it, or click once and press Next")
        entity_help.setProperty("class", "help-text")
        page2_layout.addWidget(entity_help)
        
        page2_layout.addStretch()

        page2_buttons_layout = QHBoxLayout()
        self.back_button_page2 = QPushButton("← Back")
        self.back_button_page2.setProperty("class", "secondary-button")
        self.back_button_page2.clicked.connect(self.go_back_to_page1)
        self.next_button_page2 = QPushButton("Continue →")
        self.next_button_page2.setProperty("class", "primary-button")
        self.next_button_page2.clicked.connect(self.validate_page2)
        self.next_button_page2.setEnabled(False)
        page2_buttons_layout.addWidget(self.back_button_page2)
        page2_buttons_layout.addStretch()
        page2_buttons_layout.addWidget(self.next_button_page2)
        page2_layout.addLayout(page2_buttons_layout)
        self.page2.setLayout(page2_layout)
        self.stacked_widget.addWidget(self.page2)

        # Page 3: Remote Name
        self.page3 = QWidget()
        page3_layout = QVBoxLayout()
        page3_layout.setSpacing(15)
        page3_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title and description
        title_label3 = QLabel("🏷️ Name Your Remote")
        title_label3.setProperty("class", "page-title")
        page3_layout.addWidget(title_label3)
        
        desc_label3 = QLabel("Give your remote a friendly name to easily identify it.")
        desc_label3.setProperty("class", "page-description")
        desc_label3.setWordWrap(True)
        page3_layout.addWidget(desc_label3)
        
        # Name input
        name_label = QLabel("Remote Name:")
        name_label.setProperty("class", "field-label")
        page3_layout.addWidget(name_label)
        
        self.remote_name_input = QLineEdit(self.remote_name)
        self.remote_name_input.setPlaceholderText("e.g., Living Room TV, Bedroom Android TV")
        self.remote_name_input.setProperty("class", "input-field")
        page3_layout.addWidget(self.remote_name_input)
        
        name_help = QLabel("💡 Choose a descriptive name to distinguish this remote from others")
        name_help.setProperty("class", "help-text")
        page3_layout.addWidget(name_help)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setProperty("class", "summary-frame")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(15, 15, 15, 15)
        
        summary_title = QLabel("📋 Configuration Summary")
        summary_title.setProperty("class", "summary-title")
        summary_layout.addWidget(summary_title)
        
        self.summary_text = QTextEdit()
        self.summary_text.setProperty("class", "summary-text")
        self.summary_text.setMaximumHeight(120)
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        page3_layout.addWidget(summary_frame)
        page3_layout.addStretch()

        page3_buttons_layout = QHBoxLayout()
        self.back_button_page3 = QPushButton("← Back")
        self.back_button_page3.setProperty("class", "secondary-button")
        self.back_button_page3.clicked.connect(self.go_back_to_page2)
        
        finish_text = "Update Remote" if self.remote_data else "Create Remote"
        self.finish_button = QPushButton(f"✓ {finish_text}")
        self.finish_button.setProperty("class", "success-button")
        self.finish_button.clicked.connect(self.finish_wizard, Qt.ConnectionType.UniqueConnection)
        
        page3_buttons_layout.addWidget(self.back_button_page3)
        page3_buttons_layout.addStretch()
        page3_buttons_layout.addWidget(self.finish_button)
        page3_layout.addLayout(page3_buttons_layout)
        self.page3.setLayout(page3_layout)
        self.stacked_widget.addWidget(self.page3)

        self.setLayout(main_layout)

    def validate_page1(self):
        self.ha_url = self.ha_url_input.text().strip()
        self.token = self.token_input.text().strip()

        if not self.ha_url or not self.token:
            self.show_connection_status("❌ Please fill in both URL and token fields", "error")
            return

        # Basic URL validation
        if not (self.ha_url.startswith("http://") or self.ha_url.startswith("https://")):
            self.show_connection_status("❌ URL must start with http:// or https://", "error")
            return

        # Remove trailing slash if present
        self.ha_url = self.ha_url.rstrip('/')

        # Start connection test
        self.test_connection()

    def show_connection_status(self, message, status_type="info"):
        """Show connection status with appropriate styling"""
        self.connection_status.setText(message)
        self.connection_status.setProperty("status_type", status_type)
        self.connection_status.style().unpolish(self.connection_status)
        self.connection_status.style().polish(self.connection_status)
        self.connection_status.show()
        
        # Ensure the widget is properly sized and visible
        self.connection_status.adjustSize()
        self.connection_status.update()
        
        # Force layout update to prevent UI displacement
        parent = self.connection_status.parent()
        if parent and isinstance(parent, QWidget):
            layout = parent.layout()
            if layout:
                layout.activate()

    def test_connection(self):
        """Test connection to Home Assistant in a separate thread"""
        self.next_button_page1.setEnabled(False)
        self.next_button_page1.setText("Testing Connection...")
        self.connection_progress.show()
        self.show_connection_status("🔄 Testing connection to Home Assistant...", "info")
        
        # Start connection test thread
        self.connection_thread = ConnectionTestThread(self.ha_url, self.token)
        self.connection_thread.connection_result.connect(self.handle_connection_result)
        self.connection_thread.start()

    def handle_connection_result(self, success, message, entities):
        """Handle the result of the connection test"""
        self.connection_progress.hide()
        self.next_button_page1.setEnabled(True)
        self.next_button_page1.setText("Test Connection & Continue")
        
        if success:
            self.show_connection_status(f"✅ {message}", "success")
            self.populate_entity_list(entities)
            self.go_to_page2()
        else:
            self.show_connection_status(f"❌ {message}", "error")

    def populate_entity_list(self, entities_data):
        """Populate the entity list with discovered entities"""
        self.all_entities_data = entities_data  # Store all entities for filtering
        self.filter_entities()  # Apply current filter
        
    def filter_entities(self):
        """Filter entities based on active status"""
        self.entity_list.clear()
        
        if not self.all_entities_data:
            self.entity_list.addItem("No remote entities found.")
            self.next_button_page2.setEnabled(False)
            return
            
        show_active_only = self.show_active_only.isChecked()
        filtered_entities = []
        
        for display_name, entity_id, entity_state in sorted(self.all_entities_data):
            if show_active_only:
                # Only show entities that are not unavailable
                if entity_state != "unavailable":
                    filtered_entities.append((display_name, entity_id))
            else:
                # Show all entities
                filtered_entities.append((display_name, entity_id))
        
        if filtered_entities:
            for display_name, entity_id in filtered_entities:
                item = QListWidgetItem(display_name)
                item.setData(Qt.ItemDataRole.UserRole, entity_id)
                self.entity_list.addItem(item)
            self.next_button_page2.setEnabled(True)
        else:
            if show_active_only:
                self.entity_list.addItem("No active remote entities found. Try unchecking 'Show active entities only'.")
            else:
                self.entity_list.addItem("No remote entities found.")
            self.next_button_page2.setEnabled(False)

    def go_to_page2(self):
        """Navigate to page 2 and update progress"""
        self.current_step = 2
        self.update_progress()
        self.stacked_widget.setCurrentWidget(self.page2)

    def go_back_to_page1(self):
        """Navigate back to page 1"""
        self.current_step = 1
        self.update_progress()
        self.stacked_widget.setCurrentWidget(self.page1)

    def go_back_to_page2(self):
        """Navigate back to page 2"""
        self.current_step = 2
        self.update_progress()
        self.stacked_widget.setCurrentWidget(self.page2)

    def update_progress(self):
        """Update the progress indicator"""
        step_names = ["Connection Details", "Select Entity", "Name & Finish"]
        self.progress_label.setText(f"Step {self.current_step} of {self.total_steps}: {step_names[self.current_step-1]}")
        self.progress_bar.setValue(self.current_step)

    def select_entity_from_list(self, item):
        """Handle double-click on entity list item"""
        self.entity_list.setCurrentItem(item)
        self.validate_page2()

    def validate_page2(self):
        """Validate entity selection and move to page 3"""
        selected_item = self.entity_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select an entity from the list.")
            return
        
        self.entity_id = selected_item.data(Qt.ItemDataRole.UserRole)
        self.current_step = 3
        self.update_progress()
        self.update_summary()
        self.stacked_widget.setCurrentWidget(self.page3)

    def update_summary(self):
        """Update the configuration summary on page 3"""
        selected_item = self.entity_list.currentItem()
        entity_display = selected_item.text() if selected_item else "None selected"
        
        summary = f"""Home Assistant URL: {self.ha_url}
Entity: {entity_display}
Token: {'*' * 20} (hidden)"""
        
        self.summary_text.setPlainText(summary)

    def finish_wizard(self):
        """Complete the wizard and save the remote configuration"""
        # Prevent multiple calls to finish_wizard (Windows-specific issue)
        if hasattr(self, '_wizard_finished') and self._wizard_finished:
            return
        
        self.remote_name = self.remote_name_input.text().strip()
        if not self.remote_name:
            QMessageBox.warning(self, "Input Error", "Remote name cannot be empty.")
            return

        # Disable the finish button to prevent multiple clicks
        self.finish_button.setEnabled(False)
        self.finish_button.setText("Creating...")
        
        self._wizard_finished = True
        
        saved_remote = {
            "name": self.remote_name,
            "ha_url": self.ha_url,
            "token": self.token,
            "entity_id": self.entity_id
        }
        self.remote_saved.emit(saved_remote, self.remote_index)
        self.accept()

    def apply_styles(self):
        """Apply styling that respects the KDE system theme"""
        # Get the current palette to detect theme
        palette = self.palette()
        is_dark_theme = palette.color(QPalette.ColorRole.Window).lightness() < 128
        
        # Base styling that uses system palette colors
        base_styles = """
            QDialog {
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: palette(window);
                color: palette(window-text);
            }
            
            QFrame[class="progress-frame"] {
                background-color: palette(alternate-base);
                border: 1px solid palette(mid);
                border-radius: 8px;
                margin-bottom: 10px;
                padding: 5px;
            }
            
            QLabel[class="progress-label"] {
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 5px;
                color: palette(text);
            }
            
            QProgressBar[class="progress-bar"] {
                border-radius: 4px;
                text-align: center;
                height: 8px;
                background-color: palette(base);
                border: 1px solid palette(mid);
            }
            
            QProgressBar[class="progress-bar"]::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            
            QLabel[class="page-title"] {
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 8px;
                color: palette(highlight);
            }
            
            QLabel[class="page-description"] {
                font-size: 13px;
                margin-bottom: 20px;
                line-height: 1.4;
                color: palette(text);
            }
            
            QLabel[class="field-label"] {
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 5px;
                margin-top: 10px;
                color: palette(text);
            }
            
            QLineEdit[class="input-field"] {
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                border: 2px solid palette(mid);
                background-color: palette(base);
                color: palette(text);
            }
            
            QLineEdit[class="input-field"]:focus {
                border-color: palette(highlight);
                outline: none;
            }
            
            QLabel[class="help-text"] {
                font-size: 11px;
                margin-bottom: 15px;
                font-style: italic;
                color: palette(dark);
            }
            
            QLabel[class="status-message"] {
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
                margin: 10px 0;
                min-height: 20px;
            }
            
            QListWidget[class="entity-list"] {
                border-radius: 6px;
                font-size: 12px;
                padding: 5px;
                border: 2px solid palette(mid);
                background-color: palette(base);
                color: palette(text);
            }
            
            QListWidget[class="entity-list"]::item {
                padding: 8px 12px;
                border-radius: 3px;
                margin: 1px;
            }
            
            QListWidget[class="entity-list"]::item:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            
            QFrame[class="summary-frame"] {
                background-color: palette(alternate-base);
                border-radius: 8px;
                margin: 15px 0;
                border: 1px solid palette(mid);
            }
            
            QLabel[class="summary-title"] {
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 10px;
                color: palette(text);
            }
            
            QTextEdit[class="summary-text"] {
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
                border: 1px solid palette(mid);
                background-color: palette(base);
                color: palette(text);
            }
            
            QPushButton[class="primary-button"] {
                background-color: palette(highlight);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
                min-width: 120px;
            }
            
            QPushButton[class="primary-button"]:hover {
                background-color: palette(dark);
                color: #ffffff;
            }
            
            QPushButton[class="primary-button"]:pressed {
                background-color: palette(shadow);
                color: #ffffff;
            }
            
            QPushButton[class="primary-button"]:disabled {
                background-color: palette(mid);
                color: palette(dark);
            }
            
            QPushButton[class="secondary-button"] {
                color: palette(text);
                border: 2px solid palette(mid);
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
                min-width: 100px;
                background-color: palette(base);
            }
            
            QPushButton[class="secondary-button"]:hover {
                border-color: palette(highlight);
                background-color: palette(alternate-base);
                color: palette(text);
            }
            
            QPushButton[class="success-button"] {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
                min-width: 140px;
            }
            
            QPushButton[class="success-button"]:hover {
                background-color: #45A049;
            }
            
            QPushButton[class="success-button"]:pressed {
                background-color: #3D8B40;
            }
            
            QCheckBox[class="filter-checkbox"] {
                font-size: 12px;
                color: palette(text);
                spacing: 8px;
            }
            
            QCheckBox[class="filter-checkbox"]::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid palette(mid);
                background-color: palette(base);
            }
            
            QCheckBox[class="filter-checkbox"]::indicator:checked {
                background-color: palette(highlight);
                border-color: palette(highlight);
            }
            
            QCheckBox[class="filter-checkbox"]::indicator:checked:hover {
                background-color: palette(dark);
            }
        """
        
        # Theme-specific status message colors
        if is_dark_theme:
            theme_specific = """
                QLabel[class="status-message"][status_type="success"] {
                    background-color: #1B5E20;
                    color: #A5D6A7;
                    border: 1px solid #2E7D32;
                    font-weight: 600;
                }
                
                QLabel[class="status-message"][status_type="error"] {
                    background-color: #B71C1C;
                    color: #FFCDD2;
                    border: 1px solid #D32F2F;
                    font-weight: 600;
                }
                
                QLabel[class="status-message"][status_type="info"] {
                    background-color: #0D47A1;
                    color: #BBDEFB;
                    border: 1px solid #1976D2;
                    font-weight: 600;
                }
            """
        else:
            theme_specific = """
                QLabel[class="status-message"][status_type="success"] {
                    background-color: #E8F5E8;
                    color: #2E7D32;
                    border: 1px solid #C8E6C9;
                    font-weight: 600;
                }
                
                QLabel[class="status-message"][status_type="error"] {
                    background-color: #FFEBEE;
                    color: #C62828;
                    border: 1px solid #FFCDD2;
                    font-weight: 600;
                }
                
                QLabel[class="status-message"][status_type="info"] {
                    background-color: #E3F2FD;
                    color: #1565C0;
                    border: 1px solid #BBDEFB;
                    font-weight: 600;
                }
            """
        
        self.setStyleSheet(base_styles + theme_specific)

    def setup_input_validation(self):
        """Setup input validation and keyboard shortcuts for better UX"""
        # Enable Enter key to proceed to next step
        self.ha_url_input.returnPressed.connect(self.token_input.setFocus)
        self.token_input.returnPressed.connect(self.validate_page1)
        self.remote_name_input.returnPressed.connect(self.finish_wizard, Qt.ConnectionType.UniqueConnection)
        
        # Real-time validation feedback
        self.ha_url_input.textChanged.connect(self.validate_url_input)
        self.token_input.textChanged.connect(self.validate_token_input)
        self.remote_name_input.textChanged.connect(self.validate_name_input)
        
        # Entity list selection handling
        self.entity_list.itemSelectionChanged.connect(self.on_entity_selection_changed)

    def validate_url_input(self, text):
        """Provide real-time feedback for URL input"""
        if not text:
            return
        
        if not (text.startswith("http://") or text.startswith("https://")):
            self.ha_url_input.setStyleSheet("""
                QLineEdit[class="input-field"] {
                    border: 2px solid #f44336;
                    border-radius: 6px;
                    padding: 10px 12px;
                    font-size: 13px;
                }
            """)
        else:
            self.ha_url_input.setStyleSheet("")  # Reset to default

    def validate_token_input(self, text):
        """Provide real-time feedback for token input"""
        if len(text) > 0 and len(text) < 20:
            self.token_input.setStyleSheet("""
                QLineEdit[class="input-field"] {
                    border: 2px solid #ff9800;
                    border-radius: 6px;
                    padding: 10px 12px;
                    font-size: 13px;
                }
            """)
        else:
            self.token_input.setStyleSheet("")  # Reset to default

    def validate_name_input(self, text):
        """Provide real-time feedback for name input"""
        if len(text.strip()) == 0:
            self.finish_button.setEnabled(False)
        else:
            self.finish_button.setEnabled(True)

    def on_entity_selection_changed(self):
        """Handle entity selection changes"""
        has_selection = bool(self.entity_list.currentItem())
        self.next_button_page2.setEnabled(has_selection)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for better navigation"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_F1:
            self.show_help()
        else:
            super().keyPressEvent(event)

    def show_help(self):
        """Show help dialog with wizard instructions"""
        help_text = """
<h3>Remote Setup Wizard Help</h3>

<p><b>Step 1: Connection Details</b></p>
<ul>
<li>Enter your Home Assistant URL (e.g., https://homeassistant.local:8123)</li>
<li>Create a Long-Lived Access Token in Home Assistant: Profile → Security → Long-Lived Access Tokens</li>
<li>Press Enter or click "Test Connection" to proceed</li>
</ul>

<p><b>Step 2: Select Entity</b></p>
<ul>
<li>Choose the remote entity you want to control</li>
<li>Double-click an entity or select and click Continue</li>
</ul>

<p><b>Step 3: Name Your Remote</b></p>
<ul>
<li>Give your remote a descriptive name</li>
<li>Review the configuration summary</li>
<li>Click "Create Remote" to finish</li>
</ul>

<p><b>Keyboard Shortcuts:</b></p>
<ul>
<li>Enter: Proceed to next step</li>
<li>Escape: Cancel wizard</li>
<li>F1: Show this help</li>
</ul>
        """
        
        help_dialog = QMessageBox(self)
        help_dialog.setWindowTitle("Wizard Help")
        help_dialog.setTextFormat(Qt.TextFormat.RichText)
        help_dialog.setText(help_text)
        help_dialog.setIcon(QMessageBox.Icon.Information)
        help_dialog.exec()


if __name__ == "__main__":
    app = QApplication([])
    wizard = RemoteWizard()
    if wizard.exec() == QDialog.DialogCode.Accepted:
        print("Wizard finished. New remote added.")
    else:
        print("Wizard cancelled.")