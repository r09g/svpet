import json
import time
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum

class PetType(Enum):
    CHICKEN = "chicken"
    CAT = "cat" 
    DOG = "dog"
    DUCK = "duck"

class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

class ChickenState(Enum):
    IDLE = "IDLE"
    WALK = "WALK"
    SIT = "SIT"
    EAT = "EAT"

@dataclass
class PetMemory:
    name: str
    pet_type: PetType
    creation_time: float
    pet_count: int = 0
    total_living_time: float = 0.0
    chat_summary: str = ""
    mood: int = 50
    last_mood_reset: float = 0.0
    
    def get_total_living_time(self) -> float:
        """Get total time pet has been alive"""
        return time.time() - self.creation_time + self.total_living_time
    
    def update_mood(self):
        """Update mood based on time decay"""
        current_time = time.time()
        hours_passed = (current_time - self.last_mood_reset) / 3600
        
        # Check if it's been 24 hours or app restart (simple daily reset)
        if hours_passed >= 24:
            self.mood = random.randint(40, 60)
            self.last_mood_reset = current_time
        else:
            # Decay by 1 per hour
            decay = int(hours_passed)
            self.mood = max(0, self.mood - decay)
    
    def pet_interaction(self):
        """Handle petting interaction"""
        self.pet_count += 1
        self.mood = min(100, self.mood + 1)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "pet_type": self.pet_type.value,
            "creation_time": self.creation_time,
            "pet_count": self.pet_count,
            "total_living_time": self.total_living_time,
            "chat_summary": self.chat_summary,
            "mood": self.mood,
            "last_mood_reset": self.last_mood_reset
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PetMemory':
        return cls(
            name=data["name"],
            pet_type=PetType(data["pet_type"]),
            creation_time=data["creation_time"],
            pet_count=data["pet_count"],
            total_living_time=data["total_living_time"],
            chat_summary=data["chat_summary"],
            mood=data["mood"],
            last_mood_reset=data.get("last_mood_reset", time.time())
        )

@dataclass 
class Pet:
    memory: PetMemory
    position: tuple[int, int] = (100, 100)
    direction: Direction = Direction.DOWN
    current_state: ChickenState = ChickenState.IDLE
    state_start_time: float = 0.0
    target_position: Optional[tuple[int, int]] = None
    is_dragging: bool = False
    state_target_duration: float = 0.0  # Target duration for current state
    is_sitting_down: bool = False  # True during sit animation, False when holding sit pose
    walking_path: List[tuple[int, int]] = None  # Manhattan path for walking
    path_index: int = 0  # Current position in walking path
    
    def __post_init__(self):
        if self.state_start_time == 0.0:
            self.state_start_time = time.time()
        if self.walking_path is None:
            self.walking_path = []
    
