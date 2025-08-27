import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QPixmap
from pet_data import PetType, PetMemory, Pet
import time

class AddPetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Pet")
        self.setModal(True)
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        
        # Pet type selection
        layout.addWidget(QLabel("Pet Type:"))
        self.type_combo = QComboBox()
        for pet_type in PetType:
            self.type_combo.addItem(pet_type.value.title(), pet_type)
        layout.addWidget(self.type_combo)
        
        # Pet name input
        layout.addWidget(QLabel("Pet Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter pet name...")
        layout.addWidget(self.name_input)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        add_button = QPushButton("Add Pet")
        add_button.clicked.connect(self.accept)
        button_layout.addWidget(add_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Focus on name input
        self.name_input.setFocus()
    
    def get_pet_data(self):
        """Get the entered pet data"""
        pet_type = self.type_combo.currentData()
        pet_name = self.name_input.text().strip()
        return pet_type, pet_name
    
    def accept(self):
        """Validate input before accepting"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please enter a pet name.")
            return
        super().accept()

class RemovePetDialog(QDialog):
    def __init__(self, pets, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Remove Pet")
        self.setModal(True)
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        
        if not pets:
            layout.addWidget(QLabel("No pets to remove."))
            close_button = QPushButton("Close")
            close_button.clicked.connect(self.reject)
            layout.addWidget(close_button)
            return
        
        # Warning
        warning_label = QLabel("⚠️ Warning: This action cannot be undone!")
        warning_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # Pet selection
        layout.addWidget(QLabel("Select pet to remove:"))
        self.pet_combo = QComboBox()
        for pet in pets:
            display_name = f"{pet.memory.name} the {pet.memory.pet_type.value.title()}"
            self.pet_combo.addItem(display_name, pet)
        layout.addWidget(self.pet_combo)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        remove_button = QPushButton("Remove Pet")
        remove_button.setStyleSheet("background-color: #d32f2f; color: white;")
        remove_button.clicked.connect(self.accept)
        button_layout.addWidget(remove_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def get_selected_pet(self):
        """Get the selected pet to remove"""
        return self.pet_combo.currentData()

class SystemTrayMenu(QSystemTrayIcon):
    add_pet_requested = Signal(PetType, str)  # pet_type, name
    remove_pet_requested = Signal(object)  # pet object
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    connect_llm_requested = Signal(str)  # model_path
    animation_tester_requested = Signal()
    quit_requested = Signal()
    
    def __init__(self, icon_path: str):
        super().__init__()
        
        self.pets = []  # Will be updated by the main app
        self.current_zoom = 4.0
        
        # Setup tray icon
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Extract first frame (16x16) as icon
            icon_pixmap = pixmap.copy(0, 0, 16, 16)
            self.setIcon(QIcon(icon_pixmap))
        else:
            # Fallback icon
            self.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        # Setup menu
        self.setup_menu()
        
        # Set tooltip
        self.setToolTip("Desktop Pet")
        
        # Show tray icon
        self.show()
    
    def setup_menu(self):
        """Setup the context menu"""
        menu = QMenu()
        
        # Add Pet
        add_pet_action = menu.addAction("Add Pet")
        add_pet_action.triggered.connect(self.show_add_pet_dialog)
        
        # Remove Pet
        self.remove_pet_action = menu.addAction("Remove Pet")
        self.remove_pet_action.triggered.connect(self.show_remove_pet_dialog)
        self.remove_pet_action.setEnabled(False)  # Disabled until pets exist
        
        menu.addSeparator()
        
        # Zoom controls
        self.zoom_in_action = menu.addAction("Zoom In (2x)")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        
        self.zoom_out_action = menu.addAction("Zoom Out (0.5x)")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        
        menu.addSeparator()
        
        # Connect LLM
        connect_llm_action = menu.addAction("Connect LLM")
        connect_llm_action.triggered.connect(self.show_connect_llm_dialog)
        
        menu.addSeparator()
        
        # Animation Tester
        animation_tester_action = menu.addAction("Animation Tester")
        animation_tester_action.triggered.connect(self.open_animation_tester)
        
        menu.addSeparator()
        
        # Quit
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        
        self.setContextMenu(menu)
    
    def update_pets_list(self, pets):
        """Update the pets list for remove pet functionality"""
        self.pets = pets
        self.remove_pet_action.setEnabled(len(pets) > 0)
    
    def show_add_pet_dialog(self):
        """Show dialog to add a new pet"""
        dialog = AddPetDialog()
        if dialog.exec() == QDialog.Accepted:
            pet_type, pet_name = dialog.get_pet_data()
            self.add_pet_requested.emit(pet_type, pet_name)
    
    def show_remove_pet_dialog(self):
        """Show dialog to remove a pet"""
        if not self.pets:
            QMessageBox.information(None, "No Pets", "No pets available to remove.")
            return
        
        dialog = RemovePetDialog(self.pets)
        if dialog.exec() == QDialog.Accepted:
            selected_pet = dialog.get_selected_pet()
            if selected_pet:
                self.remove_pet_requested.emit(selected_pet)
    
    def zoom_in(self):
        """Request zoom in"""
        self.current_zoom *= 2
        self.zoom_in_requested.emit()
    
    def zoom_out(self):
        """Request zoom out"""
        self.current_zoom /= 2
        self.zoom_out_requested.emit()
    
    def show_connect_llm_dialog(self):
        """Show dialog to connect LLM model"""
        model_path, _ = QFileDialog.getExistingDirectory(
            None,
            "Select LLM Model Directory",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if model_path:
            # Validate that this looks like a model directory
            required_files = ["config.json"]  # Basic check for model directory
            if any(os.path.exists(os.path.join(model_path, f)) for f in required_files):
                self.connect_llm_requested.emit(model_path)
            else:
                QMessageBox.warning(
                    None,
                    "Invalid Model Directory", 
                    "The selected directory does not appear to contain a valid LLM model.\n\n"
                    "Please select a directory containing a HuggingFace model."
                )
    
    def quit_application(self):
        """Request application quit"""
        reply = QMessageBox.question(
            None,
            "Quit Application",
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.quit_requested.emit()
    
    def open_animation_tester(self):
        """Open the animation tester window"""
        self.animation_tester_requested.emit()