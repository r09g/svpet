from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPixmap, QPainter, QMouseEvent, QImage, QBitmap, QRegion
from pet_data import Pet
from animation_system import AnimationManager
from pet_state_machine import PetStateMachine
from config import DEBUG_SETTINGS
import random

class PetWidget(QWidget):
    pet_clicked = Signal()
    pet_double_clicked = Signal()
    
    def __init__(self, pet: Pet, sprite_sheet_path: str):
        super().__init__()
        
        self.pet = pet
        self.sprite_sheet_path = sprite_sheet_path
        self.scale_factor = 4  # 16x16 -> 64x64  
        self.pet_size = 16 * self.scale_factor
        
        # Animation system
        self.animation_manager = AnimationManager()
        self.animation_manager.load_sprite_sheet("chicken", sprite_sheet_path, 16, 16)
        
        # State machine
        self.state_machine = PetStateMachine(pet, self.animation_manager)
        
        # Setup widget
        self.setup_widget()
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_pet)
        self.update_timer.start(50)  # 20 FPS
        
        # Dragging and clicking
        self.is_dragging = False
        self.drag_offset = QPoint()
        self.drag_start_pos = QPoint()
        self.drag_threshold = 5  # Minimum pixels to move before considering it a drag
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.handle_single_click)
        self.click_count = 0
        
        
        # Position widget
        self.move(*self.pet.position)
    
    def setup_widget(self):
        """Setup widget properties"""
        self.setFixedSize(self.pet_size, self.pet_size)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        
        # Force window to stay on top on macOS
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        
        # Make background transparent and click-through for non-pet areas
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
    
    def ensure_always_on_top(self):
        """Ensure widget stays on top by raising and activating"""
        self.raise_()
        self.activateWindow()
        # Re-apply window flags to enforce always-on-top
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.show()
    
    def update_pet(self):
        """Update pet state and animation"""
        # Always update state machine (emotes shouldn't block state changes)
        self.state_machine.update()
        
        # Update animations (pet animations continue during emotes)
        self.animation_manager.update()
        
        # Update widget position if pet moved
        if not self.is_dragging:
            x, y = self.pet.position
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                self.move(int(x), int(y))
        
        # Repaint
        self.update()
    
    def paintEvent(self, event):
        """Paint the pet sprite"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Get current frame based on state
        current_pixmap = None
        
        if self.animation_manager.current_animation or self.animation_manager.held_frame_data:
            current_pixmap = self.animation_manager.get_current_pixmap("chicken")
        else:
            # Default frame when no animation is playing or frame held
            current_pixmap = self.animation_manager.hold_frame("chicken", 0)
        
        if current_pixmap:
            # Scale the pixmap
            scaled_pixmap = current_pixmap.scaled(
                self.pet_size, self.pet_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            
            # SHAPE THE WINDOW TO THE SPRITE ALPHA - kills the halo
            img = scaled_pixmap.toImage()
            mask = QRegion(QBitmap.fromImage(img.createAlphaMask()))
            self.setMask(mask)
        
            painter.drawPixmap(0, 0, scaled_pixmap)
            
        painter.end()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.click_count += 1
            
            if self.click_count == 1:
                # Start timer for single click detection
                self.click_timer.start(300)  # 300ms for double-click detection
                self.drag_offset = event.position().toPoint()
                self.drag_start_pos = event.position().toPoint()
                
            elif self.click_count == 2:
                # Double click - cancel single click timer
                self.click_timer.stop()
                self.click_count = 0
                self.pet_double_clicked.emit()
    
    def handle_single_click(self):
        """Handle single click after timer expires"""
        if self.click_count == 1 and not self.is_dragging:
            # Only emit click if we're not dragging
            self.pet_clicked.emit()
            self.pet.memory.pet_interaction()
        self.click_count = 0
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events (dragging)"""
        if event.buttons() & Qt.LeftButton:
            # Check if we've moved enough to start dragging
            current_pos = event.position().toPoint()
            distance = (current_pos - self.drag_start_pos).manhattanLength()
            
            if not self.is_dragging and distance > self.drag_threshold:
                # Start dragging - cancel any pending click events
                self.is_dragging = True
                self.pet.is_dragging = True
                self.click_timer.stop()  # Cancel pending single click
                self.click_count = 0     # Reset click count
                if DEBUG_SETTINGS["enable_state_logging"]:
                    print(f"[DEBUG] Dragging {self.pet.memory.name} started")
                
                # Cancel any ongoing animations
                if self.animation_manager.current_animation:
                    self.animation_manager.animations[self.animation_manager.current_animation].stop()
            
            if self.is_dragging:
                # Move widget and update pet position
                new_pos = self.mapToParent(current_pos - self.drag_offset)
                self.move(new_pos)
                self.pet.position = (new_pos.x(), new_pos.y())
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton:
            if self.is_dragging:
                # End dragging
                self.is_dragging = False
                self.pet.is_dragging = False
                if DEBUG_SETTINGS["enable_state_logging"]:
                    print(f"[DEBUG] Dragging {self.pet.memory.name} stopped at ({self.pet.position[0]}, {self.pet.position[1]})")
    
    def show_emote(self, emote_type: str):
        """Show emote animation"""
        # This will be implemented when we add the emote system
        pass
    
    def get_emote_based_on_mood(self) -> str:
        """Get random emote based on pet mood"""
        mood = self.pet.memory.mood
        
        if mood >= 75:
            return random.choice(["happy", "love", "important", "sleepy"])
        elif mood <= 50:
            return random.choice(["angry", "sad", "confused", "speechless", "sleepy"])
        else:
            return random.choice(["confused", "angry", "important", "sleepy", "speechless"])
    
    def update_screen_size(self, width: int, height: int):
        """Update screen size for state machine"""
        self.state_machine.update_screen_size(width, height)
    
