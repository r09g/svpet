import time
from typing import Dict, List, Optional, Tuple
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QRect
from config import DEBUG_SETTINGS

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
        self.held_frame_data: Optional[Tuple[str, int]] = None
        
    def load_sprite_sheet(self, name: str, image_path: str, tile_width: int, tile_height: int):
        """Load a sprite sheet"""
        self.sprite_sheets[name] = SpriteSheet(image_path, tile_width, tile_height)
    
    def create_animation(self, name: str, frames: List[int], duration_per_frame: float = 0.1, loop: bool = True):
        """Create an animation"""
        self.animations[name] = Animation(frames, duration_per_frame, loop)
    
    def play_animation(self, name: str, *, force: bool=False) -> None:
        # starting a new animation should clear any hold
        if not force and self.current_animation == name:
            return False

        if name not in self.animations:
            return False
        
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"[DEBUG] play_animation called: {name}")

        # Clear held frame when starting animation
        self.held_frame_data = None
        
        # Don't interrupt current animation unless forced - if not forced, drop the animation
        if self.current_animation and not force:
            current_anim = self.animations[self.current_animation]
            if current_anim.is_playing and not current_anim.is_finished():
                return False  # Drop the animation instead of queuing
        
        self.current_animation = name
        self.animations[name].start()
        return True
    
    
    def update(self):
        """Update animation state - call this every frame"""
        if self.current_animation:
            current_anim = self.animations[self.current_animation]
            
            if not current_anim.loop and current_anim.is_finished():
                self.current_animation = None
    
    def get_current_pixmap(self, sprite_sheet_name) -> Optional[QPixmap]:
        # 1) honor hold first
        if self.held_frame_data:
            sheet_name, idx = self.held_frame_data
            sheet = self.sprite_sheets.get(sheet_name)
            return sheet.get_frame(idx) if sheet else None

        # 2) otherwise use current animation
        if not self.current_animation or sprite_sheet_name not in self.sprite_sheets:
            return None

        animation = self.animations[self.current_animation]
        frame_index = animation.get_current_frame()
        sprite_sheet = self.sprite_sheets[sprite_sheet_name]

        return sprite_sheet.get_frame(frame_index)
    
    def hold_frame(self, sprite_sheet_name: str, frame_index: int) -> Optional[QPixmap]:
        # stop any running animation and set the hold
        if self.current_animation:
            self.animations[self.current_animation].stop()
            self.current_animation = None

        self.held_frame_data = (sprite_sheet_name, frame_index)
        sheet = self.sprite_sheets.get(sprite_sheet_name)

        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"[DEBUG] hold_frame called: {sprite_sheet_name} {frame_index}")
        
        return sheet.get_frame(frame_index) if sheet else None
    
