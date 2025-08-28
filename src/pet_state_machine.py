import random
import time
import math
from typing import Tuple, Optional
from pet_data import Pet, ChickenState, Direction
from animation_system import AnimationManager
from config import (
    ANIMATION_DURATIONS, ANIMAL_ANIMATIONS, ANIMATION_LOOPS, 
    STATE_DURATIONS, STATE_TRANSITIONS, DEBUG_SETTINGS
)
import config

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
            ChickenState.IDLE: {
                ChickenState.IDLE: STATE_TRANSITIONS["IDLE"]["IDLE"],
                ChickenState.WALK: STATE_TRANSITIONS["IDLE"]["WALK"], 
                ChickenState.SIT: STATE_TRANSITIONS["IDLE"]["SIT"],
                ChickenState.EAT: STATE_TRANSITIONS["IDLE"]["EAT"]
            },
            ChickenState.SIT: {
                ChickenState.IDLE: STATE_TRANSITIONS["SIT"]["IDLE"],
                ChickenState.WALK: STATE_TRANSITIONS["SIT"]["WALK"],
                ChickenState.SIT: STATE_TRANSITIONS["SIT"]["SIT"]
            },
            ChickenState.EAT: {
                ChickenState.IDLE: STATE_TRANSITIONS["EAT"]["IDLE"],
                ChickenState.WALK: STATE_TRANSITIONS["EAT"]["WALK"],
                ChickenState.SIT: STATE_TRANSITIONS["EAT"]["SIT"]
            }
        }
        
        # Load state duration ranges from config
        self.state_durations = {
            ChickenState.IDLE: STATE_DURATIONS["IDLE"],
            ChickenState.SIT: STATE_DURATIONS["SIT"], 
            ChickenState.EAT: STATE_DURATIONS["EAT"],
            ChickenState.WALK: STATE_DURATIONS["WALK"]
        }
        
        # Initialize target duration for current state if not already set
        if self.pet.state_target_duration == 0.0:
            duration_range = self.state_durations.get(self.pet.current_state, (5, 15))
            self.pet.state_target_duration = random.uniform(duration_range[0], duration_range[1])
        
        self._init_animations()
    
    def _init_animations(self):
        """Initialize animal animations from config"""
        # Create all animal animations from config
        for anim_name, frames in ANIMAL_ANIMATIONS.items():
            if anim_name.startswith("walk_"):
                duration = ANIMATION_DURATIONS["walk"]
            elif anim_name.startswith("sit_") or anim_name.startswith("stand_"):
                duration = ANIMATION_DURATIONS["sit"]
            elif anim_name == "eat":
                duration = ANIMATION_DURATIONS["eat"]
            else:
                duration = ANIMATION_DURATIONS["default"]
            
            loop = ANIMATION_LOOPS.get(anim_name, False)
            self.animation_manager.create_animation(anim_name, frames, duration_per_frame=duration, loop=loop)
    
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
        
        # Horizontal first
        if start_x != end_x:
            step = 1 if end_x > start_x else -1
            for x in range(start_x + step, end_x + step, step):
                path.append((x, start_y))
        
        if start_y != end_y:
            step = 1 if end_y > start_y else -1
            for y in range(start_y + step, end_y + step, step):
                path.append((end_x, y))
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
        
        # Use the pre-calculated target duration for this state
        should_transition = elapsed >= self.pet.state_target_duration
        return should_transition
    
    def get_next_state(self) -> ChickenState:
        """Get next state based on transition probabilities"""
        if self.pet.current_state not in self.state_transitions:
            return ChickenState.IDLE
        
        transitions = self.state_transitions[self.pet.current_state]
        states = list(transitions.keys())
        probabilities = list(transitions.values())
        
        return random.choices(states, weights=probabilities)[0]
    
    def transition_to_state(self, new_state: ChickenState):
        """Transition to a new state"""
        old_state = self.pet.current_state
        self.pet.current_state = new_state
        self.pet.state_start_time = time.time()
        
        # Calculate target duration for this state (once when entering)
        duration_range = self.state_durations.get(new_state, (5, 15))
        self.pet.state_target_duration = random.uniform(duration_range[0], duration_range[1])
        
        print(f"{self.pet.memory.name}: {old_state.value} -> {new_state.value}")
        
        # Log state-specific information
        self._log_state_details(new_state)
        
        if new_state == ChickenState.WALK:
            # Set random target position and calculate Manhattan path
            self.pet.target_position = self.get_random_screen_position()
            self.pet.walking_path = self.calculate_manhattan_path(self.pet.position, self.pet.target_position)
            self.pet.path_index = 0
            
            # Set initial walking direction and animation
            if len(self.pet.walking_path) > 0:
                first_target = self.pet.walking_path[0]
                dx = first_target[0] - self.pet.position[0]
                dy = first_target[1] - self.pet.position[1]
                
                # Set direction based on first movement
                if abs(dx) > abs(dy) and dx != 0:
                    self.pet.direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                elif dy != 0:
                    self.pet.direction = Direction.DOWN if dy > 0 else Direction.UP
                
                # Start walking animation in the correct direction
                walk_anim = f"walk_{self.pet.direction.value}"
                self.animation_manager.play_animation(walk_anim, force=True)
        
        # Handle SIT state transitions (Mealy state machine)
        self._handle_sit_transitions(old_state, new_state)
        
        if new_state == ChickenState.IDLE:
            self._handle_idle_animation(old_state)
        elif new_state == ChickenState.EAT:
            # Play eat animation only if not transitioning from SIT (handled in sit transitions)
            if old_state != ChickenState.SIT:
                self.animation_manager.play_animation("eat", force=True)
    
    def update_walk_state(self):
        """Update walking behavior using Manhattan pathfinding"""
        if not self.pet.target_position or not hasattr(self.pet, 'walking_path'):
            return
        
        # Check if we've reached the end of the path
        if self.pet.path_index >= len(self.pet.walking_path):
            if DEBUG_SETTINGS["enable_state_logging"]:
                print(f"[DEBUG] {self.pet.memory.name} reached target")
            self.pet.target_position = None
            self.pet.walking_path = []
            self.pet.path_index = 0
            return
        
        # Get current and next positions in path
        current_pos = self.pet.position
        next_pos = self.pet.walking_path[self.pet.path_index]
        
        # Check if we've reached the current path step
        if abs(next_pos[0] - current_pos[0]) <= config.MOVEMENT_SPEED and abs(next_pos[1] - current_pos[1]) <= config.MOVEMENT_SPEED:
            # Move to exact position and advance to next path step
            self.pet.position = next_pos
            self.pet.path_index += 1
            
            # Update direction for the next path segment immediately
            if self.pet.path_index < len(self.pet.walking_path):
                next_target = self.pet.walking_path[self.pet.path_index]
                dx = next_target[0] - next_pos[0]
                dy = next_target[1] - next_pos[1]
                
                # Set direction based on next movement
                if abs(dx) > abs(dy) and dx != 0:
                    new_direction = Direction.RIGHT if dx > 0 else Direction.LEFT
                elif dy != 0:
                    new_direction = Direction.DOWN if dy > 0 else Direction.UP
                else:
                    new_direction = self.pet.direction  # Keep current if no movement needed
                
                # Update direction and animation if changed
                if new_direction != self.pet.direction:
                    self.pet.direction = new_direction
                    walk_anim = f"walk_{self.pet.direction.value}"
                    self.animation_manager.play_animation(walk_anim, force=True)
            
            return
        
        # Move towards next position (single axis movement)
        dx = next_pos[0] - current_pos[0]
        dy = next_pos[1] - current_pos[1]
        
        # Move only in one direction (Manhattan movement) and set direction accordingly
        if abs(dx) > abs(dy) and dx != 0:
            # Move horizontally
            move_x = config.MOVEMENT_SPEED if dx > 0 else -config.MOVEMENT_SPEED
            move_y = 0
            new_direction = Direction.RIGHT if dx > 0 else Direction.LEFT
        elif dy != 0:
            # Move vertically
            move_x = 0
            move_y = config.MOVEMENT_SPEED if dy > 0 else -config.MOVEMENT_SPEED
            new_direction = Direction.DOWN if dy > 0 else Direction.UP
        else:
            # No movement needed (shouldn't happen but safety check)
            move_x = move_y = 0
            new_direction = self.pet.direction
        
        new_x = current_pos[0] + move_x
        new_y = current_pos[1] + move_y
        
        # Clamp to screen bounds
        new_x = max(0, min(new_x, self.screen_width - self.pet_width))
        new_y = max(0, min(new_y, self.screen_height - self.pet_height))
        
        self.pet.position = (new_x, new_y)
        
        # Update direction only if it changed to match current movement
        if new_direction != self.pet.direction:
            self.pet.direction = new_direction
        
        # Play walk animation that matches current movement direction
        walk_anim = f"walk_{self.pet.direction.value}"
        if self.animation_manager.current_animation != walk_anim:
            self.animation_manager.play_animation(walk_anim, force=True)
    
    
    def _handle_idle_animation(self, old_state: ChickenState):
        """Handle IDLE state animation based on previous state - simplified"""
        if old_state == ChickenState.WALK or old_state == ChickenState.SIT:
            # If previous was walk or sit, hold first frame of animation in current direction
            walk_anim_name = f"walk_{self.pet.direction.value}"
            if walk_anim_name in self.animation_manager.animations:
                first_frame = self.animation_manager.animations[walk_anim_name].frames[0]
                self.animation_manager.hold_frame("chicken", first_frame)
        elif old_state == ChickenState.IDLE:
            # If previous was idle, randomly choose facing direction
            new_direction = random.choice([Direction.DOWN, Direction.LEFT, Direction.RIGHT, Direction.UP])
            new_idle_hold = f"walk_{new_direction.value}"
            self.pet.direction = new_direction
            anim = self.animation_manager.animations[new_idle_hold]
            first_frame = anim.frames[0]
            self.animation_manager.hold_frame("chicken", first_frame)
        else:
            # Default case: hold frame 0
            self.animation_manager.hold_frame("chicken", 0)
    
    def _log_state_details(self, state: ChickenState):
        """Log detailed information about current state"""
        if DEBUG_SETTINGS["enable_state_logging"]:
            current_pos = self.pet.position
            
            if state == ChickenState.WALK and self.pet.target_position:
                distance = abs(self.pet.target_position[0] - current_pos[0]) + abs(self.pet.target_position[1] - current_pos[1])
                print(f"[DEBUG] Distance: {distance}px")
            elif state in [ChickenState.IDLE, ChickenState.SIT, ChickenState.EAT]:
                print(f"[DEBUG] Target Duration: {self.pet.state_target_duration:.1f}s")
            
            print(f"[DEBUG] Position: ({current_pos[0]}, {current_pos[1]}), Facing: {self.pet.direction.value}, Mood: {self.pet.memory.mood}")

    def update(self):
        """Update state machine"""
        if self.pet.is_dragging:
            return
        
        # Update current state behavior
        if self.pet.current_state == ChickenState.WALK:
            self.update_walk_state()
        elif self.pet.current_state == ChickenState.SIT:
            self.update_sit_state()
        
        # Check for state transitions
        if self.should_transition_state():
            next_state = self.get_next_state()
            self.transition_to_state(next_state)
    
    def _handle_sit_transitions(self, old_state: ChickenState, new_state: ChickenState):
        """Handle SIT state transitions with proper Mealy state machine behavior"""
        
        # Case 1: Transitioning TO SIT state from non-SIT states
        if new_state == ChickenState.SIT and old_state != ChickenState.SIT:
            # Play sit animation once when entering SIT state
            sit_anim = f"sit_{self.pet.direction.value}"
            self.animation_manager.play_animation(sit_anim, force=True)
            
            # Mark that we need to hold the last frame after animation completes
            self.pet.sit_animation_playing = True
            
        # Case 2: Already IN SIT state, staying in SIT (SIT -> SIT)
        elif new_state == ChickenState.SIT and old_state == ChickenState.SIT:
            # Random facing direction 
            new_direction = random.choice([Direction.DOWN, Direction.LEFT, Direction.RIGHT, Direction.UP])
            new_sit_hold = f"sit_{new_direction.value}"
            self.pet.direction = new_direction
            anim = self.animation_manager.animations[new_sit_hold]
            last_frame = anim.frames[-1]
            self.animation_manager.hold_frame("chicken", last_frame)


        # Case 3: Transitioning FROM SIT state to non-SIT states  
        elif old_state == ChickenState.SIT and new_state != ChickenState.SIT:
            # Play stand animation once when leaving SIT state
            stand_anim = f"stand_{self.pet.direction.value}"
            self.animation_manager.play_animation(stand_anim, force=True)
            
            # Mark that we need to transition to the new state after stand animation
            self.pet.stand_animation_playing = True
            self.pet.pending_state_after_stand = new_state
    
    def update_sit_state(self):
        """Update SIT state behavior"""
        # Check if sit animation just finished
        if self.pet.sit_animation_playing:
            current_anim = self.animation_manager.current_animation
            if current_anim and current_anim in self.animation_manager.animations:
                anim = self.animation_manager.animations[current_anim]
                if anim.is_finished():
                    # Sit animation finished - hold the last frame
                    last_frame = anim.frames[-1]
                    self.animation_manager.hold_frame("chicken", last_frame)
                    self.pet.sit_animation_playing = False
                    if DEBUG_SETTINGS["enable_state_logging"]:
                        print(f"[DEBUG] Sit animation finished - holding last frame ({last_frame})")
        
        # Check if stand animation just finished (transitioning out of SIT)
        if self.pet.stand_animation_playing:
            current_anim = self.animation_manager.current_animation
            if current_anim and current_anim in self.animation_manager.animations:
                anim = self.animation_manager.animations[current_anim]
                if anim.is_finished():
                    # Stand animation finished - transition to the pending state
                    self.pet.stand_animation_playing = False
                    pending_state = self.pet.pending_state_after_stand
                    self.pet.pending_state_after_stand = None
                    print(f"  Stand animation finished - transitioning to {pending_state.value if pending_state else 'None'}")
                    
                    if pending_state == ChickenState.IDLE:
                        self._handle_idle_animation(ChickenState.SIT)
                    elif pending_state == ChickenState.EAT:
                        self.animation_manager.play_animation("eat", force=True)
                    elif pending_state == ChickenState.WALK:
                        # Walking behavior will be handled by the walk state update
                        pass
    
