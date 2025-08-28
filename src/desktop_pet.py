import os
import time
from typing import List, Dict, Optional
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtGui import QScreen

from pet_data import Pet, PetMemory, PetType, ChickenState, Direction
from pet_widget import PetWidget
from emote_system import EmoteManager
from chat_system import ChatWidget
from system_tray import SystemTrayMenu
from save_system import SaveSystem
from config import (
    DEFAULT_SCALE_FACTOR, AUTO_SAVE_INTERVAL, get_full_sprite_path, 
    get_emote_sprite_path, get_chatbox_sprite_path, DEBUG_SETTINGS
)

class DesktopPetApp(QObject):
    def __init__(self):
        super().__init__()
        
        # Core components
        self.pets: List[Pet] = []
        self.pet_widgets: Dict[str, PetWidget] = {}
        self.chat_widgets: Dict[str, ChatWidget] = {}
        self.emote_manager = EmoteManager()
        self.save_system = SaveSystem()
        
        # Application state
        self.scale_factor = DEFAULT_SCALE_FACTOR
        self.llm_model_path: Optional[str] = None
        
        # Asset paths from config
        self.sprite_paths = {
            'chicken': get_full_sprite_path('chicken'),
            'cat': get_full_sprite_path('cat'),
            'dog': get_full_sprite_path('dog'),
            'duck': get_full_sprite_path('duck')
        }
        self.emote_sprite_path = get_emote_sprite_path()
        self.chatbox_sprite_path = get_chatbox_sprite_path()
        
        # Verify required assets exist
        self.verify_assets_exist()
        
        # System tray
        tray_icon_path = self.sprite_paths['chicken']
        self.system_tray = SystemTrayMenu(tray_icon_path)
        self.setup_tray_connections()
        
        # Timers
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_pets)
        self.auto_save_timer.start(AUTO_SAVE_INTERVAL)  # Auto-save from config
        
        # Screen size tracking
        self.update_screen_size()
        
        # Load existing pets
        self.load_pets_from_save()
        
        if DEBUG_SETTINGS["enable_state_logging"]:
            print("Desktop Pet application started!")
            print(f"Loaded {len(self.pets)} pets from save file")
    
    def verify_assets_exist(self):
        """Verify that all required Stardew Valley sprite sheets exist"""
        required_sprites = [
            (self.emote_sprite_path, "Emote sprite sheet"), 
            (self.chatbox_sprite_path, "Chatbox sprite sheet")
        ]
        
        # Add all animal sprite sheets
        for pet_type, sprite_path in self.sprite_paths.items():
            required_sprites.append((sprite_path, f"{pet_type.title()} sprite sheet"))
        
        missing_sprites = []
        for sprite_path, sprite_name in required_sprites:
            if not os.path.exists(sprite_path):
                missing_sprites.append((sprite_path, sprite_name))
        
        if missing_sprites:
            error_msg = "Missing required Stardew Valley sprite sheets:\n\n"
            for sprite_path, sprite_name in missing_sprites:
                error_msg += f"• {sprite_name}: {sprite_path}\n"
            error_msg += "\nPlease add the Stardew Valley sprite sheets to continue."
            
            print("Error: " + error_msg)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Missing Sprite Sheets", error_msg)
            raise FileNotFoundError(f"Required sprite sheets missing: {[path for path, _ in missing_sprites]}")
        
        if DEBUG_SETTINGS["enable_state_logging"]:
            print("All required Stardew Valley sprite sheets found")
    
    
    def setup_tray_connections(self):
        """Setup system tray signal connections"""
        self.system_tray.add_pet_requested.connect(self.add_pet)
        self.system_tray.remove_pet_requested.connect(self.remove_pet)
        self.system_tray.zoom_in_requested.connect(self.zoom_in)
        self.system_tray.zoom_out_requested.connect(self.zoom_out)
        self.system_tray.connect_llm_requested.connect(self.connect_llm_model)
        self.system_tray.quit_requested.connect(self.quit_application)
    
    def update_screen_size(self):
        """Update screen size information"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            self.screen_width = geometry.width()
            self.screen_height = geometry.height()
            
            # Update all pet widgets with new screen size
            for pet_widget in self.pet_widgets.values():
                pet_widget.update_screen_size(self.screen_width, self.screen_height)
    
    def load_pets_from_save(self):
        """Load pets from save file"""
        try:
            saved_pets = self.save_system.load_all_pets()
            for pet in saved_pets:
                self.create_pet_widget(pet)
                self.pets.append(pet)
            
            self.update_tray_pets_list()
        except Exception as e:
            if DEBUG_SETTINGS["enable_state_logging"]:
                print(f"Error loading pets from save: {e}")
    
    def create_pet_widget(self, pet: Pet):
        """Create widget for a pet"""
        pet_id = self.get_pet_id(pet)
        
        # Get sprite path for pet type
        sprite_path = self.sprite_paths.get(pet.memory.pet_type.value, self.sprite_paths['chicken'])
        
        # Create pet widget
        pet_widget = PetWidget(pet, sprite_path)
        pet_widget.pet_clicked.connect(lambda: self.handle_pet_clicked(pet))
        pet_widget.pet_double_clicked.connect(lambda: self.handle_pet_double_clicked(pet))
        pet_widget.update_screen_size(self.screen_width, self.screen_height)
        pet_widget.show()
        # Ensure the widget is always on top from creation
        pet_widget.ensure_always_on_top()
        
        self.pet_widgets[pet_id] = pet_widget
        
        # Create emote widget for this pet
        emote_widget = self.emote_manager.create_emote_widget(pet_id, self.emote_sprite_path, pet_widget)
        
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"[DEBUG] Created {pet.memory.name} the {pet.memory.pet_type.value}")
            print(f"[DEBUG] Position: ({pet.position[0]}, {pet.position[1]}), State: {pet.current_state.value}, Mood: {pet.memory.mood}")
    
    def get_pet_id(self, pet: Pet) -> str:
        """Get unique ID for a pet"""
        return f"{pet.memory.name}_{pet.memory.pet_type.value}"
    
    def handle_pet_clicked(self, pet: Pet):
        """Handle pet click (show emote)"""
        pet_id = self.get_pet_id(pet)
        
        # Get emote based on mood
        emote_type = self.emote_manager.get_random_emote_by_mood(pet.memory.mood)
        
        # Show emote
        self.emote_manager.show_emote(pet_id, emote_type)
        
        if DEBUG_SETTINGS["enable_interaction_logging"]:
            print(f"[DEBUG] {pet.memory.name} petted, mood {pet.memory.mood} -> {pet.memory.mood + 1}, emote: {emote_type}")
            print(f"[DEBUG] Total pets: {pet.memory.pet_count + 1}")
    
    def handle_pet_double_clicked(self, pet: Pet):
        """Handle pet double-click (open chat)"""
        pet_id = self.get_pet_id(pet)
        
        # Close existing chat if open
        if pet_id in self.chat_widgets:
            self.chat_widgets[pet_id].close_chat()
            del self.chat_widgets[pet_id]
        
        # Create chat widget
        pet_widget = self.pet_widgets[pet_id]
        chat_widget = ChatWidget(pet, self.chatbox_sprite_path, pet_widget)
        chat_widget.chat_closed.connect(lambda: self.handle_chat_closed(pet_id))
        chat_widget.update_position()
        chat_widget.show()
        # Ensure chat widget is always on top
        chat_widget.ensure_always_on_top()
        
        self.chat_widgets[pet_id] = chat_widget
        
        if DEBUG_SETTINGS["enable_interaction_logging"]:
            print(f"Chat opened with {pet.memory.name} (mood: {pet.memory.mood})")
    
    def handle_chat_closed(self, pet_id: str):
        """Handle chat widget closed"""
        if pet_id in self.chat_widgets:
            del self.chat_widgets[pet_id]
        if DEBUG_SETTINGS["enable_interaction_logging"]:
            print("Chat closed")
    
    def add_pet(self, pet_type: PetType, name: str):
        """Add a new pet"""
        if not name:
            QMessageBox.warning(None, "Invalid Name", "Pet name cannot be empty.")
            return
        
        # Check if pet already exists
        if self.save_system.pet_exists(name, pet_type):
            QMessageBox.warning(None, "Pet Exists", f"A {pet_type.value} named {name} already exists.")
            return
        
        # Create pet memory
        memory = PetMemory(
            name=name,
            pet_type=pet_type,
            creation_time=time.time()
        )
        
        # Create pet
        pet = Pet(memory=memory)
        
        # Create pet widget
        self.create_pet_widget(pet)
        
        # Add to pets list
        self.pets.append(pet)
        
        # Save pet
        self.save_system.save_pet(pet)
        
        # Update tray menu
        self.update_tray_pets_list()
        
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"Added new pet: {name} the {pet_type.value}")
        
        # Show welcome message
        QMessageBox.information(
            None, 
            "Pet Added", 
            f"Welcome {name} the {pet_type.value.title()}!\n\nClick to interact and double-click to chat."
        )
    
    def remove_pet(self, pet: Pet):
        """Remove a pet"""
        pet_id = self.get_pet_id(pet)
        
        # Close chat if open
        if pet_id in self.chat_widgets:
            self.chat_widgets[pet_id].close_chat()
            del self.chat_widgets[pet_id]
        
        # Remove pet widget
        if pet_id in self.pet_widgets:
            self.pet_widgets[pet_id].close()
            del self.pet_widgets[pet_id]
        
        # Remove emote widget
        self.emote_manager.remove_emote_widget(pet_id)
        
        # Remove from pets list
        if pet in self.pets:
            self.pets.remove(pet)
        
        # Remove from save system
        self.save_system.remove_pet(pet)
        
        # Update tray menu
        self.update_tray_pets_list()
        
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"Removed pet: {pet.memory.name} the {pet.memory.pet_type.value}")
    
    def zoom_in(self):
        """Zoom in all pets by 2x"""
        old_scale = self.scale_factor
        self.scale_factor *= 2
        self.apply_zoom_to_pets()
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"Zoomed in from {old_scale}x to {self.scale_factor}x")
    
    def zoom_out(self):
        """Zoom out all pets by 2x"""
        old_scale = self.scale_factor
        self.scale_factor /= 2
        self.apply_zoom_to_pets()
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"Zoomed out from {old_scale}x to {self.scale_factor}x")
    
    def apply_zoom_to_pets(self):
        """Apply current zoom factor to all pet widgets"""
        new_size = int(16 * self.scale_factor)
        for pet_widget in self.pet_widgets.values():
            pet_widget.pet_size = new_size
            pet_widget.setFixedSize(new_size, new_size)
    
    def connect_llm_model(self, model_path: str):
        """Connect LLM model"""
        self.llm_model_path = model_path
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"Connected LLM model: {model_path}")
        
        # Test model loading
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            QMessageBox.information(
                None,
                "LLM Connected",
                f"Successfully connected to LLM model:\n{model_path}\n\nYou can now chat with your pets!"
            )
        except Exception as e:
            QMessageBox.warning(
                None,
                "LLM Connection Failed", 
                f"Failed to load model from:\n{model_path}\n\nError: {str(e)}\n\nPets will use simple responses instead."
            )
            self.llm_model_path = None
    
    def auto_save_pets(self):
        """Auto-save all pets"""
        if self.pets:
            self.save_system.auto_save_pets(self.pets)
    
    def update_tray_pets_list(self):
        """Update the pets list in system tray menu"""
        self.system_tray.update_pets_list(self.pets)
    
    def quit_application(self):
        """Quit the application"""
        if DEBUG_SETTINGS["enable_state_logging"]:
            print("Shutting down desktop pet application...")
        
        # Save all pets before quitting
        if self.pets:
            self.save_system.save_all_pets(self.pets)
            if DEBUG_SETTINGS["enable_state_logging"]:
                print(f"Saved {len(self.pets)} pets")
        
        # Close all widgets
        for chat_widget in self.chat_widgets.values():
            chat_widget.close_chat()
        
        for pet_widget in self.pet_widgets.values():
            pet_widget.close()
        
        # Quit application
        QApplication.quit()