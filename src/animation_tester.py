#!/usr/bin/env python3

import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QSpinBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter
from animation_system import AnimationManager
from config import ANIMATION_DURATIONS, get_full_sprite_path, get_emote_sprite_path

class AnimationTester(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Desktop Pet Animation Tester")
        self.setGeometry(100, 100, 800, 600)
        
        # Animation system
        self.animation_manager = AnimationManager()
        
        # Available sprite sheets from config
        self.sprite_sheets = {
            'chicken': get_full_sprite_path('chicken'),
            'cat': get_full_sprite_path('cat'), 
            'dog': get_full_sprite_path('dog'),
            'duck': get_full_sprite_path('duck'),
            'emote': get_emote_sprite_path()
        }
        
        # Load available sprite sheets
        self.load_sprite_sheets()
        
        # Animation definitions
        self.setup_animations()
        
        # Current display
        self.current_sprite_sheet = 'chicken'
        self.scale_factor = 4
        
        # Setup UI
        self.setup_ui()
        
        # Animation update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_animation)
        self.update_timer.start(50)  # 20 FPS
    
    def load_sprite_sheets(self):
        """Load all available sprite sheets"""
        loaded_sheets = {}
        for name, path in self.sprite_sheets.items():
            if os.path.exists(path):
                try:
                    self.animation_manager.load_sprite_sheet(name, path, 16, 16)
                    loaded_sheets[name] = path
                    print(f"Loaded sprite sheet: {name}")
                except Exception as e:
                    print(f"Failed to load {name}: {e}")
            else:
                print(f"Sprite sheet not found: {path}")
        
        self.sprite_sheets = loaded_sheets
    
    def setup_animations(self):
        """Setup all animation definitions"""
        
        # Chicken/Cat/Dog/Duck animations (same layout)
        animal_animations = {
            "walk_up": [8, 9, 10, 11],
            "walk_right": [4, 5, 6, 7],   
            "walk_down": [0, 1, 2, 3],    
            "walk_left": [12, 13, 14, 15],
            "sit_down": [16, 17], 
            "sit_right": [18, 19], 
            "sit_up": [20, 21], 
            "sit_left": [22, 23], 
            "stand_down": [17, 16], 
            "stand_right": [19, 18], 
            "stand_up": [21, 20], 
            "stand_left": [23, 22],
            "eat": [24, 25, 26, 27]
        }
        
        # Emote animations  
        emote_animations = {
            "enter": [0, 1, 2, 3],
            "exit": [3, 2, 1, 0],
            "confused": [12, 13, 14, 15],
            "angry": [16, 17, 18, 19],
            "important": [20, 21, 22, 23],
            "love": [24, 25, 26, 27],
            "sleepy": [28, 29, 30, 31],
            "sad": [32, 33, 34, 35],
            "happy": [36, 37, 38, 39],
            "speechless": [44, 45, 46, 47]
        }
        
        # Create animal animations with durations from config
        for anim_name, frames in animal_animations.items():
            if anim_name.startswith("walk_") or anim_name == "eat":
                duration = ANIMATION_DURATIONS["walk"] if anim_name.startswith("walk_") else ANIMATION_DURATIONS["eat"]
            elif anim_name.startswith("sit_") or anim_name.startswith("stand_"):
                duration = ANIMATION_DURATIONS["sit"]
            else:
                duration = ANIMATION_DURATIONS["default"]
            
            loop = True if anim_name.startswith("walk_") or anim_name == "eat" else False
            self.animation_manager.create_animation(anim_name, frames, duration_per_frame=duration, loop=loop)
        
        # Create emote animations with duration from config
        for anim_name, frames in emote_animations.items():
            loop = anim_name not in ["enter", "exit"]
            self.animation_manager.create_animation(f"emote_{anim_name}", frames, duration_per_frame=ANIMATION_DURATIONS["emote"], loop=loop)
        
        # Single frame displays
        for i in range(64):  # Up to 64 frames
            self.animation_manager.create_animation(f"frame_{i}", [i], duration_per_frame=1.0, loop=True)
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QVBoxLayout()
        
        # Sprite sheet selection
        sprite_layout = QHBoxLayout()
        sprite_layout.addWidget(QLabel("Sprite Sheet:"))
        self.sprite_combo = QComboBox()
        self.sprite_combo.addItems(list(self.sprite_sheets.keys()))
        self.sprite_combo.currentTextChanged.connect(self.change_sprite_sheet)
        sprite_layout.addWidget(self.sprite_combo)
        controls_layout.addLayout(sprite_layout)
        
        # Animation selection
        anim_layout = QHBoxLayout()
        anim_layout.addWidget(QLabel("Animation:"))
        self.animation_combo = QComboBox()
        self.update_animation_list()
        self.animation_combo.currentTextChanged.connect(self.change_animation)
        anim_layout.addWidget(self.animation_combo)
        controls_layout.addLayout(anim_layout)
        
        # Scale control
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale:"))
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(1, 8)
        self.scale_spin.setValue(self.scale_factor)
        self.scale_spin.setSuffix("x")
        self.scale_spin.valueChanged.connect(self.change_scale)
        scale_layout.addWidget(self.scale_spin)
        controls_layout.addLayout(scale_layout)
        
        # Frame info
        self.frame_info = QLabel("Frame: 0")
        controls_layout.addWidget(self.frame_info)
        
        # Duration info
        self.duration_info = QLabel("Duration: -")
        controls_layout.addWidget(self.duration_info)
        
        # Animation controls
        button_layout = QHBoxLayout()
        
        play_button = QPushButton("Play")
        play_button.clicked.connect(self.play_animation)
        button_layout.addWidget(play_button)
        
        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_animation)
        button_layout.addWidget(stop_button)
        
        controls_layout.addLayout(button_layout)
        
        layout.addLayout(controls_layout)
        
        # Animation display area
        self.display_area = AnimationDisplay(self)
        layout.addWidget(self.display_area)
    
    def update_animation_list(self):
        """Update animation list based on selected sprite sheet"""
        self.animation_combo.clear()
        
        sprite_name = self.sprite_combo.currentText()
        
        if sprite_name == 'emote':
            # Emote animations
            emote_anims = ["emote_enter", "emote_exit", "emote_confused", "emote_angry", 
                          "emote_important", "emote_love", "emote_sleepy", "emote_sad", 
                          "emote_happy", "emote_speechless"]
            self.animation_combo.addItems(emote_anims)
        else:
            # Animal animations
            animal_anims = ["walk_up", "walk_right", "walk_down", "walk_left",
                           "sit_down", "sit_right", "sit_up", "sit_left", 
                           "stand_down", "stand_right", "stand_up", "stand_left", "eat"]
            self.animation_combo.addItems(animal_anims)
        
        # Add frame-by-frame options
        self.animation_combo.addItems([f"frame_{i}" for i in range(28)])  # 7x4 grid
    
    def change_sprite_sheet(self, sprite_name):
        """Change current sprite sheet"""
        if sprite_name in self.sprite_sheets:
            self.current_sprite_sheet = sprite_name
            self.update_animation_list()
            print(f"Changed to sprite sheet: {sprite_name}")
    
    def change_animation(self, anim_name):
        """Change current animation"""
        if anim_name and anim_name in self.animation_manager.animations:
            self.animation_manager.play_animation(anim_name, force=True)
            print(f"Playing animation: {anim_name}")
    
    def change_scale(self, scale):
        """Change display scale"""
        self.scale_factor = scale
        self.display_area.update()
        print(f"Scale changed to: {scale}x")
    
    def play_animation(self):
        """Play current animation"""
        anim_name = self.animation_combo.currentText()
        if anim_name:
            self.animation_manager.play_animation(anim_name, force=True)
            print(f"Playing: {anim_name}")
    
    def stop_animation(self):
        """Stop current animation"""
        if self.animation_manager.current_animation:
            self.animation_manager.animations[self.animation_manager.current_animation].stop()
            self.animation_manager.current_animation = None
            print("Animation stopped")
    
    def update_animation(self):
        """Update animation system"""
        self.animation_manager.update()
        
        # Update frame info
        if self.animation_manager.current_animation:
            current_anim = self.animation_manager.animations[self.animation_manager.current_animation]
            frame_index = current_anim.get_current_frame()
            duration_ms = int(current_anim.duration_per_frame * 1000)
            loop_status = "Loop" if current_anim.loop else "Once"
            
            self.frame_info.setText(f"Frame: {frame_index} ({self.animation_manager.current_animation})")
            self.duration_info.setText(f"Duration: {duration_ms}ms per frame, {loop_status}")
        else:
            self.frame_info.setText("Frame: - (No animation)")
            self.duration_info.setText("Duration: -")
        
        # Update display
        self.display_area.update()

class AnimationDisplay(QWidget):
    def __init__(self, parent_tester):
        super().__init__()
        self.parent_tester = parent_tester
        self.setMinimumSize(400, 400)
        self.setStyleSheet("background-color: #2b2b2b; border: 2px solid #555;")
    
    def paintEvent(self, event):
        """Paint the current animation frame"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Get current frame
        sprite_name = self.parent_tester.current_sprite_sheet
        current_pixmap = None
        
        if self.parent_tester.animation_manager.current_animation:
            current_pixmap = self.parent_tester.animation_manager.get_current_pixmap(sprite_name)
        else:
            # Show first frame by default
            current_pixmap = self.parent_tester.animation_manager.hold_frame(sprite_name, 0)
        
        if current_pixmap and not current_pixmap.isNull():
            # Scale the pixmap
            scale = self.parent_tester.scale_factor
            scaled_size = 16 * scale
            scaled_pixmap = current_pixmap.scaled(
                scaled_size, scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            
            # Center the sprite
            x = (self.width() - scaled_size) // 2
            y = (self.height() - scaled_size) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # Draw frame border
            painter.setPen(Qt.white)
            painter.drawRect(x-1, y-1, scaled_size+2, scaled_size+2)
        else:
            # Draw "No sprite" message
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, f"No sprite: {sprite_name}")
        
        painter.end()

# Animation tester is now integrated into the main desktop pet application
# Access it via the system tray menu -> Animation Tester