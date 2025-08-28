import time
from typing import Dict, List, Optional, Tuple
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QRect

class SpriteSheet:
    def __init__(self, image_path: str, tile_width: int, tile_height: int):
        self.image_path = image_path
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.pixmap = QPixmap(image_path)
        
        if self.pixmap.isNull():
            raise ValueError(f"Could not load sprite sheet: {image_path}")
    
    def get_frame(self, frame_index: int) -> QPixmap:
        """Extract a single frame from the sprite sheet"""
        cols = self.pixmap.width() // self.tile_width
        row = frame_index // cols
        col = frame_index % cols
        
        x = col * self.tile_width
        y = row * self.tile_height
        
        rect = QRect(x, y, self.tile_width, self.tile_height)
        return self.pixmap.copy(rect)

class Animation:
    def __init__(self, frames: List[int], duration_per_frame: float = 0.1, loop: bool = True):
        self.frames = frames
        self.duration_per_frame = duration_per_frame
        self.loop = loop
        self.start_time = 0.0
        self.is_playing = False
        self.current_frame_index = 0
    
    def start(self):
        """Start the animation"""
        self.start_time = time.time()
        self.is_playing = True
        self.current_frame_index = 0
    
    def stop(self):
        """Stop the animation"""
        self.is_playing = False
    
    def get_current_frame(self) -> int:
        """Get current frame index"""
        if not self.is_playing:
            return self.frames[0] if self.frames else 0
        
        elapsed = time.time() - self.start_time
        total_frames = len(self.frames)
        
        if total_frames == 0:
            return 0
        
        frame_time_index = int(elapsed / self.duration_per_frame)
        
        if not self.loop and frame_time_index >= total_frames:
            self.is_playing = False
            return self.frames[-1]
        
        self.current_frame_index = frame_time_index % total_frames
        return self.frames[self.current_frame_index]
    
    def is_finished(self) -> bool:
        """Check if non-looping animation is finished"""
        if self.loop:
            return False
        
        elapsed = time.time() - self.start_time
        total_duration = len(self.frames) * self.duration_per_frame
        return elapsed >= total_duration

class AnimationManager:
    def __init__(self):
        self.sprite_sheets: Dict[str, SpriteSheet] = {}
        self.animations: Dict[str, Animation] = {}
        self.current_animation: Optional[str] = None
        self.animation_queue: List[str] = []
        self.held_frame_data: Optional[tuple] = None  # (sprite_sheet_name, frame_index)
        
    def load_sprite_sheet(self, name: str, image_path: str, tile_width: int, tile_height: int):
        """Load a sprite sheet"""
        self.sprite_sheets[name] = SpriteSheet(image_path, tile_width, tile_height)
    
    def create_animation(self, name: str, frames: List[int], duration_per_frame: float = 0.1, loop: bool = True):
        """Create an animation"""
        self.animations[name] = Animation(frames, duration_per_frame, loop)
    
    def play_animation(self, name: str, force: bool = False):
        """Play an animation"""
        if name not in self.animations:
            return False
        
        # Clear held frame when starting animation
        self.held_frame_data = None
        
        # Don't interrupt current animation unless forced
        if self.current_animation and not force:
            current_anim = self.animations[self.current_animation]
            if current_anim.is_playing and not current_anim.is_finished():
                self.animation_queue.append(name)
                return False
        
        self.current_animation = name
        self.animations[name].start()
        return True
    
    def queue_animation(self, name: str):
        """Queue an animation to play after current one finishes"""
        if name in self.animations:
            self.animation_queue.append(name)
    
    def update(self):
        """Update animation state - call this every frame"""
        if self.current_animation:
            current_anim = self.animations[self.current_animation]
            
            if not current_anim.loop and current_anim.is_finished():
                self.current_animation = None
                
                # Play next queued animation
                if self.animation_queue:
                    next_anim = self.animation_queue.pop(0)
                    self.play_animation(next_anim, force=True)
    
    def get_current_pixmap(self, sprite_sheet_name: str) -> Optional[QPixmap]:
        """Get current frame as pixmap"""
        # Check if we're holding a frame
        if self.held_frame_data:
            held_sprite_sheet, held_frame_index = self.held_frame_data
            if held_sprite_sheet == sprite_sheet_name and held_sprite_sheet in self.sprite_sheets:
                sprite_sheet = self.sprite_sheets[held_sprite_sheet]
                return sprite_sheet.get_frame(held_frame_index)
        
        # Otherwise get from current animation
        if not self.current_animation or sprite_sheet_name not in self.sprite_sheets:
            return None
        
        animation = self.animations[self.current_animation]
        frame_index = animation.get_current_frame()
        sprite_sheet = self.sprite_sheets[sprite_sheet_name]
        
        return sprite_sheet.get_frame(frame_index)
    
    def hold_frame(self, sprite_sheet_name: str, frame_index: int) -> Optional[QPixmap]:
        """Hold a specific frame without animation"""
        if sprite_sheet_name not in self.sprite_sheets:
            return None
        
        # Stop current animation
        if self.current_animation:
            self.animations[self.current_animation].stop()
            self.current_animation = None
        
        # Set held frame data
        self.held_frame_data = (sprite_sheet_name, frame_index)
        
        sprite_sheet = self.sprite_sheets[sprite_sheet_name]
        return sprite_sheet.get_frame(frame_index)