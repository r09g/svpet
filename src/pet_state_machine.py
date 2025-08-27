import random
import time
import math
from typing import Tuple, Optional
from pet_data import Pet, ChickenState, Direction
from animation_system import AnimationManager
from config import (
    ANIMATION_DURATIONS, STATE_DURATIONS, STATE_TRANSITIONS, 
    MOVEMENT_SPEED, STATUS_LOG_INTERVAL, DEBUG_SETTINGS
)

class ChickenStateMachine:
    def __init__(self, pet: Pet, animation_manager: AnimationManager):
        self.pet = pet
        self.animation_manager = animation_manager
        self.screen_width = 1920  # Will be updated based on actual screen size
        self.screen_height = 1080
        self.pet_width = 32  # Scaled sprite size
        self.pet_height = 32
        
        # Load state transition probabilities from config
        self.state_transitions = {
            ChickenState.STAND: {
                ChickenState.STAND: STATE_TRANSITIONS["STAND"]["STAND"],
                ChickenState.WALK: STATE_TRANSITIONS["STAND"]["WALK"], 
                ChickenState.SIT: STATE_TRANSITIONS["STAND"]["SIT"],
                ChickenState.EAT: STATE_TRANSITIONS["STAND"]["EAT"]
            },
            ChickenState.SIT: {
                ChickenState.STAND: STATE_TRANSITIONS["SIT"]["STAND"],
                ChickenState.WALK: STATE_TRANSITIONS["SIT"]["WALK"],
                ChickenState.SIT: STATE_TRANSITIONS["SIT"]["SIT"]
            },
            ChickenState.EAT: {
                ChickenState.STAND: STATE_TRANSITIONS["EAT"]["STAND"],
                ChickenState.WALK: STATE_TRANSITIONS["EAT"]["WALK"],
                ChickenState.SIT: STATE_TRANSITIONS["EAT"]["SIT"]
            }
        }
        
        # Load state duration ranges from config
        self.state_durations = {
            ChickenState.STAND: STATE_DURATIONS["STAND"],
            ChickenState.SIT: STATE_DURATIONS["SIT"], 
            ChickenState.EAT: STATE_DURATIONS["EAT"],
            ChickenState.WALK: STATE_DURATIONS["WALK"]
        }
        
        self._init_animations()
    
    def _init_animations(self):
        """Initialize chicken animations with durations from config"""
        # Walk animations
        walk_duration = ANIMATION_DURATIONS["walk"]
        self.animation_manager.create_animation("walk_up", [8, 9, 10, 11], duration_per_frame=walk_duration, loop=True)
        self.animation_manager.create_animation("walk_right", [4, 5, 6, 7], duration_per_frame=walk_duration, loop=True) 
        self.animation_manager.create_animation("walk_down", [0, 1, 2, 3], duration_per_frame=walk_duration, loop=True)
        self.animation_manager.create_animation("walk_left", [12, 13, 14, 15], duration_per_frame=walk_duration, loop=True)
        
        # Sit animations
        sit_duration = ANIMATION_DURATIONS["sit"]
        self.animation_manager.create_animation("sit_down", [16, 17], duration_per_frame=sit_duration, loop=False)
        self.animation_manager.create_animation("sit_right", [18, 19], duration_per_frame=sit_duration, loop=False)
        self.animation_manager.create_animation("sit_up", [20, 21], duration_per_frame=sit_duration, loop=False)
        self.animation_manager.create_animation("sit_left", [22, 23], duration_per_frame=sit_duration, loop=False)
        
        # Stand animations (reverse of sit)
        self.animation_manager.create_animation("stand_down", [17, 16], duration_per_frame=sit_duration, loop=False)
        self.animation_manager.create_animation("stand_right", [19, 18], duration_per_frame=sit_duration, loop=False)
        self.animation_manager.create_animation("stand_up", [21, 20], duration_per_frame=sit_duration, loop=False)
        self.animation_manager.create_animation("stand_left", [23, 22], duration_per_frame=sit_duration, loop=False)
        
        # Eat animation
        eat_duration = ANIMATION_DURATIONS["eat"]
        self.animation_manager.create_animation("eat", [24, 25, 26, 27], duration_per_frame=eat_duration, loop=True)
    
    def update_screen_size(self, width: int, height: int):
        """Update screen dimensions for boundary checks"""
        self.screen_width = width
        self.screen_height = height
    
    def get_random_screen_position(self) -> Tuple[int, int]:
        """Get a random valid position on screen"""
        x = random.randint(0, max(0, self.screen_width - self.pet_width))
        y = random.randint(0, max(0, self.screen_height - self.pet_height))
        return (x, y)
    
    def calculate_manhattan_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> list[Tuple[int, int]]:
        """Calculate manhattan path with minimum turns"""
        start_x, start_y = start
        end_x, end_y = end
        
        path = [start]
        
        # Move horizontally first, then vertically (or vice versa randomly)
        if random.choice([True, False]):
            # Horizontal first
            if start_x != end_x:
                step = 1 if end_x > start_x else -1
                for x in range(start_x + step, end_x + step, step):
                    path.append((x, start_y))
            
            if start_y != end_y:
                step = 1 if end_y > start_y else -1
                for y in range(start_y + step, end_y + step, step):
                    path.append((end_x, y))
        else:
            # Vertical first
            if start_y != end_y:
                step = 1 if end_y > start_y else -1
                for y in range(start_y + step, end_y + step, step):
                    path.append((start_x, y))
            
            if start_x != end_x:
                step = 1 if end_x > start_x else -1
                for x in range(start_x + step, end_x + step, step):
                    path.append((x, end_y))
        
        return path
    
    def get_direction_to_target(self, current: Tuple[int, int], target: Tuple[int, int]) -> Direction:
        """Get direction from current position to target"""
        dx = target[0] - current[0]
        dy = target[1] - current[1]
        
        if abs(dx) > abs(dy):
            return Direction.RIGHT if dx > 0 else Direction.LEFT
        else:
            return Direction.DOWN if dy > 0 else Direction.UP
    
    def should_transition_state(self) -> bool:
        """Check if enough time has passed to transition state"""
        if self.pet.is_dragging:
            return False
        
        elapsed = time.time() - self.pet.state_start_time
        
        if self.pet.current_state == ChickenState.WALK:
            # Walk state ends when reaching target
            return self.pet.target_position is None
        
        duration_range = self.state_durations.get(self.pet.current_state, (5, 15))
        target_duration = random.uniform(duration_range[0], duration_range[1])
        
        return elapsed >= target_duration
    
    def get_next_state(self) -> ChickenState:
        """Get next state based on transition probabilities"""
        if self.pet.current_state not in self.state_transitions:
            return ChickenState.STAND
        
        transitions = self.state_transitions[self.pet.current_state]
        states = list(transitions.keys())
        probabilities = list(transitions.values())
        
        return random.choices(states, weights=probabilities)[0]
    
    def transition_to_state(self, new_state: ChickenState):
        """Transition to a new state"""
        old_state = self.pet.current_state
        self.pet.current_state = new_state
        self.pet.state_start_time = time.time()
        
        if DEBUG_SETTINGS["enable_state_logging"]:
            print(f"{self.pet.memory.name}: {old_state.value} -> {new_state.value}")
        
        # Log state-specific information
        self._log_state_details(new_state)
        
        if new_state == ChickenState.WALK:
            # Set random target position
            self.pet.target_position = self.get_random_screen_position()
            print(f"  Target: ({self.pet.target_position[0]}, {self.pet.target_position[1]})")
        elif new_state == ChickenState.SIT:
            # Randomly pick a direction for sitting
            self.pet.direction = random.choice(list(Direction))
            print(f"  Sitting facing: {self.pet.direction.value}")
            # Play sit animation
            sit_anim = f"sit_{self.pet.direction.value}"
            self.animation_manager.play_animation(sit_anim, force=True)
        elif new_state == ChickenState.STAND:
            if old_state == ChickenState.SIT:
                # Play stand animation
                stand_anim = f"stand_{self.pet.direction.value}"
                self.animation_manager.play_animation(stand_anim, force=True)
        elif new_state == ChickenState.EAT:
            # Play eat animation
            self.animation_manager.play_animation("eat", force=True)
    
    def update_walk_state(self):
        """Update walking behavior"""
        if not self.pet.target_position:
            return
        
        current_pos = self.pet.position
        target_pos = self.pet.target_position
        
        # Calculate direction and move towards target
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        
        if abs(dx) <= 1 and abs(dy) <= 1:
            # Reached target
            self.pet.position = target_pos
            print(f"  {self.pet.memory.name} reached target")
            self.pet.target_position = None
            return
        
        # Update direction based on movement
        self.pet.direction = self.get_direction_to_target(current_pos, target_pos)
        
        # Move towards target at configured speed
        move_x = MOVEMENT_SPEED if dx > 0 else -MOVEMENT_SPEED if dx < 0 else 0
        move_y = MOVEMENT_SPEED if dy > 0 else -MOVEMENT_SPEED if dy < 0 else 0
        
        new_x = current_pos[0] + move_x
        new_y = current_pos[1] + move_y
        
        # Clamp to screen bounds
        new_x = max(0, min(new_x, self.screen_width - self.pet_width))
        new_y = max(0, min(new_y, self.screen_height - self.pet_height))
        
        self.pet.position = (new_x, new_y)
        
        # Play walk animation continuously while walking
        walk_anim = f"walk_{self.pet.direction.value}"
        if self.animation_manager.current_animation != walk_anim:
            self.animation_manager.play_animation(walk_anim, force=True)
    
    def _log_state_details(self, state: ChickenState):
        """Log detailed information about current state"""
        current_pos = self.pet.position
        
        if state == ChickenState.WALK and self.pet.target_position:
            distance = abs(self.pet.target_position[0] - current_pos[0]) + abs(self.pet.target_position[1] - current_pos[1])
            print(f"  Distance: {distance}px")
        elif state in [ChickenState.STAND, ChickenState.SIT, ChickenState.EAT]:
            duration_range = self.state_durations.get(state, (0, 0))
            print(f"  Duration: {duration_range[0]}-{duration_range[1]}s")
        
        print(f"  Position: ({current_pos[0]}, {current_pos[1]}), Facing: {self.pet.direction.value}, Mood: {self.pet.memory.mood}")

    def update(self):
        """Update state machine"""
        if self.pet.is_dragging:
            return
        
        # Log periodic status (every 5 seconds)
        current_time = time.time()
        if not hasattr(self, '_last_status_log'):
            self._last_status_log = current_time
        elif current_time - self._last_status_log >= STATUS_LOG_INTERVAL:
            self._log_periodic_status()
            self._last_status_log = current_time
        
        # Update current state behavior
        if self.pet.current_state == ChickenState.WALK:
            self.update_walk_state()
        
        # Check for state transitions
        if self.should_transition_state():
            next_state = self.get_next_state()
            self.transition_to_state(next_state)
    
    def _log_periodic_status(self):
        """Log periodic status update"""
        if not DEBUG_SETTINGS["enable_periodic_status"]:
            return
            
        elapsed = time.time() - self.pet.state_start_time
        state = self.pet.current_state.value
        pos = self.pet.position
        
        status_msg = f"{self.pet.memory.name} {state} {elapsed:.1f}s at ({pos[0]}, {pos[1]})"
        
        if self.pet.current_state == ChickenState.WALK and self.pet.target_position:
            target = self.pet.target_position
            distance = abs(target[0] - pos[0]) + abs(target[1] - pos[1])
            status_msg += f" -> ({target[0]}, {target[1]}) dist:{distance}px"
        
        print(status_msg)