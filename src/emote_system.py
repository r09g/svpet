from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap, QPainter
from animation_system import AnimationManager
from config import ANIMATION_DURATIONS, EMOTE_ANIMATIONS, ANIMATION_LOOPS, MOOD_EMOTES, DEBUG_SETTINGS
import random

class EmoteWidget(QWidget):
    def __init__(self, emote_sprite_path: str, parent_widget: QWidget, scale_factor: float = 4.0):
        super().__init__()
        
        self.parent_widget = parent_widget
        self.emote_sprite_path = emote_sprite_path
        self.scale_factor = scale_factor
        self.emote_size = int(16 * self.scale_factor)
        
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
        self.last_valid_pixmap = None  # Cache last valid frame to prevent flashing
    
    def _init_emote_animations(self):
        """Initialize emote animations from config"""
        # Create all emote animations from config
        for anim_name, frames in EMOTE_ANIMATIONS.items():
            duration = ANIMATION_DURATIONS["emote"]
            loop = ANIMATION_LOOPS.get(anim_name, False)
            self.animation_manager.create_animation(anim_name, frames, duration_per_frame=duration, loop=loop)
    
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
    
    def ensure_always_on_top(self):
        """Ensure emote widget stays on top"""
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
        
        # Get valid emotes from config (exclude enter/exit which are special)
        valid_emotes = [emote for emote in EMOTE_ANIMATIONS.keys() if emote not in ["enter", "exit"]]
        if emote_type not in valid_emotes:
            return
        
        self.is_showing = True
        self.sequence_index = 0
        
        # Create emote sequence: enter -> emote (3 loops) -> exit
        self.current_emote_sequence = [
            ("enter", False),  # (animation_name, is_loop)
            (emote_type, False),
            (emote_type, False), 
            (emote_type, False),
            ("exit", False)
        ]
        
        # Position emote widget
        self.update_position()
        self.show()
        # Ensure emote stays on top
        self.ensure_always_on_top()
        
        # Start animation sequence
        self.play_next_in_sequence()
        
        # Start update timer
        self.update_timer.start(50)  # 20 FPS
    
    def play_next_in_sequence(self):
        """Play next animation in sequence"""
        if self.sequence_index >= len(self.current_emote_sequence):
            if DEBUG_SETTINGS["enable_state_logging"]:
                print(f"[DEBUG] Emote sequence complete")
            self.hide_emote()
            return
        
        anim_name, is_loop = self.current_emote_sequence[self.sequence_index]
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"[DEBUG] Playing emote animation: {anim_name} (step {self.sequence_index + 1}/{len(self.current_emote_sequence)})")
        
        # Modify animation to not loop for this sequence
        if anim_name in self.animation_manager.animations:
            self.animation_manager.animations[anim_name].loop = is_loop
        
        success = self.animation_manager.play_animation(anim_name, force=True)
        if success:
            self.sequence_index += 1
        else:
            if DEBUG_SETTINGS["enable_state_logging"]:
                print(f"[DEBUG] Failed to play animation: {anim_name}")
            self.hide_emote()
    
    def update_emote(self):
        """Update emote animation"""
        # Store current animation state before update
        was_playing = self.animation_manager.current_animation is not None
        
        self.animation_manager.update()
        
        # Check if animation just finished (was playing, now not playing)
        is_playing = self.animation_manager.current_animation is not None
        
        if was_playing and not is_playing and self.is_showing:
            # Animation just finished, play next in sequence immediately
            if DEBUG_SETTINGS["enable_state_logging"]:
                print(f"[DEBUG] Animation finished, playing next in sequence")
            self.play_next_in_sequence()  # No delay for seamless transitions
        
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
        
        # Clear cached pixmap
        self.last_valid_pixmap = None
    
    def update_scale_factor(self, new_scale_factor: float):
        """Update the scale factor and resize the emote widget"""
        self.scale_factor = new_scale_factor
        self.emote_size = int(16 * self.scale_factor)
        self.setFixedSize(self.emote_size, self.emote_size)
    
    def paintEvent(self, event):
        """Paint the emote sprite"""
        if not self.is_showing:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Get current frame
        current_pixmap = self.animation_manager.get_current_pixmap("emote")
        
        # Use current pixmap if available, otherwise use last valid pixmap to prevent flashing
        if current_pixmap:
            self.last_valid_pixmap = current_pixmap
            pixmap_to_use = current_pixmap
        elif self.last_valid_pixmap:
            pixmap_to_use = self.last_valid_pixmap
        else:
            return  # No pixmap available
        
        # Scale and draw the pixmap
        scaled_pixmap = pixmap_to_use.scaled(
            self.emote_size, self.emote_size,
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.FastTransformation
        )
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()

class EmoteManager:
    def __init__(self):
        self.emote_widgets = {}  # pet_id -> EmoteWidget
    
    def create_emote_widget(self, pet_id: str, emote_sprite_path: str, parent_widget: QWidget, scale_factor: float = 4.0):
        """Create emote widget for a pet"""
        emote_widget = EmoteWidget(emote_sprite_path, parent_widget, scale_factor)
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
            return random.choice(MOOD_EMOTES["high"])
        elif mood <= 50:
            return random.choice(MOOD_EMOTES["low"])
        else:
            return random.choice(MOOD_EMOTES["medium"])
    
    def update_all_scales(self, new_scale_factor: float):
        """Update scale factor for all emote widgets"""
        for emote_widget in self.emote_widgets.values():
            emote_widget.update_scale_factor(new_scale_factor)