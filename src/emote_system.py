from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap, QPainter
from src.animation_system import AnimationManager
import random

class EmoteWidget(QWidget):
    def __init__(self, emote_sprite_path: str, parent_widget: QWidget):
        super().__init__()
        
        self.parent_widget = parent_widget
        self.emote_sprite_path = emote_sprite_path
        self.scale_factor = 4  # 16x16 -> 64x64
        self.emote_size = 16 * self.scale_factor
        
        # Animation system for emotes
        self.animation_manager = AnimationManager()
        self.animation_manager.load_sprite_sheet("emote", emote_sprite_path, 16, 16)
        
        # Setup emote animations
        self._init_emote_animations()
        
        # Setup widget
        self.setup_widget()
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_emote)
        
        self.emote_timer = QTimer()
        self.emote_timer.setSingleShot(True)
        self.emote_timer.timeout.connect(self.hide_emote)
        
        self.is_showing = False
        self.current_emote_sequence = []
        self.sequence_index = 0
    
    def _init_emote_animations(self):
        """Initialize emote animations"""
        # Basic emote animations
        self.animation_manager.create_animation("enter", [0, 1, 2, 3], loop=False)
        self.animation_manager.create_animation("exit", [3, 2, 1, 0], loop=False)
        self.animation_manager.create_animation("confused", [12, 13, 14, 15], loop=True)
        self.animation_manager.create_animation("angry", [16, 17, 18, 19], loop=True)
        self.animation_manager.create_animation("important", [20, 21, 22, 23], loop=True)
        self.animation_manager.create_animation("love", [24, 25, 26, 27], loop=True)
        self.animation_manager.create_animation("sleepy", [28, 29, 30, 31], loop=True)
        self.animation_manager.create_animation("sad", [32, 33, 34, 35], loop=True)
        self.animation_manager.create_animation("happy", [36, 37, 38, 39], loop=True)
        self.animation_manager.create_animation("speechless", [44, 45, 46, 47], loop=True)
    
    def setup_widget(self):
        """Setup widget properties"""
        self.setFixedSize(self.emote_size, self.emote_size)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        
        # Force window to stay on top on macOS
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        
        # Initially hidden
        self.hide()
    
    def update_position(self):
        """Update emote position relative to parent pet widget"""
        if self.parent_widget:
            parent_pos = self.parent_widget.pos()
            parent_size = self.parent_widget.size()
            
            # Position emote directly above pet, not overlapping
            emote_x = parent_pos.x() + (parent_size.width() - self.emote_size) // 2
            emote_y = parent_pos.y() - self.emote_size - 5  # 5px gap
            
            self.move(emote_x, emote_y)
    
    def show_emote(self, emote_type: str):
        """Show emote animation sequence"""
        if self.is_showing:
            return
        
        valid_emotes = ["confused", "angry", "important", "love", "sleepy", "sad", "happy", "speechless"]
        if emote_type not in valid_emotes:
            return
        
        self.is_showing = True
        self.sequence_index = 0
        
        # Create emote sequence: enter -> emote (3 loops) -> exit
        self.current_emote_sequence = [
            ("enter", False),  # (animation_name, is_loop)
            (emote_type, True),
            (emote_type, True), 
            (emote_type, True),
            ("exit", False)
        ]
        
        # Position emote widget
        self.update_position()
        self.show()
        
        # Start animation sequence
        self.play_next_in_sequence()
        
        # Start update timer
        self.update_timer.start(50)  # 20 FPS
    
    def play_next_in_sequence(self):
        """Play next animation in sequence"""
        if self.sequence_index >= len(self.current_emote_sequence):
            self.hide_emote()
            return
        
        anim_name, is_loop = self.current_emote_sequence[self.sequence_index]
        
        # Modify animation to not loop for this sequence
        if anim_name in self.animation_manager.animations:
            self.animation_manager.animations[anim_name].loop = is_loop
        
        self.animation_manager.play_animation(anim_name, force=True)
        self.sequence_index += 1
    
    def update_emote(self):
        """Update emote animation"""
        self.animation_manager.update()
        
        # Check if current animation finished and play next in sequence
        if self.animation_manager.current_animation:
            current_anim = self.animation_manager.animations[self.animation_manager.current_animation]
            if not current_anim.loop and current_anim.is_finished():
                QTimer.singleShot(100, self.play_next_in_sequence)  # Small delay between animations
        
        # Update position to follow parent
        self.update_position()
        
        # Repaint
        self.update()
    
    def hide_emote(self):
        """Hide emote widget"""
        self.is_showing = False
        self.update_timer.stop()
        self.hide()
        
        # Reset animation states
        if self.animation_manager.current_animation:
            self.animation_manager.animations[self.animation_manager.current_animation].stop()
        self.animation_manager.current_animation = None
    
    def paintEvent(self, event):
        """Paint the emote sprite"""
        if not self.is_showing:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Get current frame
        current_pixmap = self.animation_manager.get_current_pixmap("emote")
        
        if current_pixmap:
            # Scale the pixmap
            scaled_pixmap = current_pixmap.scaled(
                self.emote_size, self.emote_size,
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.FastTransformation
            )
            painter.drawPixmap(0, 0, scaled_pixmap)
        
        painter.end()

class EmoteManager:
    def __init__(self):
        self.emote_widgets = {}  # pet_id -> EmoteWidget
    
    def create_emote_widget(self, pet_id: str, emote_sprite_path: str, parent_widget: QWidget):
        """Create emote widget for a pet"""
        emote_widget = EmoteWidget(emote_sprite_path, parent_widget)
        self.emote_widgets[pet_id] = emote_widget
        return emote_widget
    
    def show_emote(self, pet_id: str, emote_type: str):
        """Show emote for specific pet"""
        if pet_id in self.emote_widgets:
            self.emote_widgets[pet_id].show_emote(emote_type)
    
    def remove_emote_widget(self, pet_id: str):
        """Remove emote widget for pet"""
        if pet_id in self.emote_widgets:
            self.emote_widgets[pet_id].hide_emote()
            self.emote_widgets[pet_id].deleteLater()
            del self.emote_widgets[pet_id]
    
    def get_random_emote_by_mood(self, mood: int) -> str:
        """Get random emote based on mood score"""
        if mood >= 75:
            return random.choice(["happy", "love", "important", "sleepy"])
        elif mood <= 50:
            return random.choice(["angry", "sad", "confused", "speechless", "sleepy"])
        else:
            return random.choice(["confused", "angry", "important", "sleepy", "speechless"])