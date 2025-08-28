#!/usr/bin/env python3
"""
Desktop Pet Configuration File

This file contains all tunables and settings that users can easily modify
to customize their desktop pet experience.
"""

# =============================================================================
# ANIMATION SETTINGS
# =============================================================================

# Frame durations (in seconds)
ANIMATION_DURATIONS = {
    "walk": 0.25,        # Walk animation frame duration
    "sit": 0.3,         # Sit/Stand animation frame duration  
    "eat": 0.2,        # Eat animation frame duration
    "emote": 0.15,      # Emote animation frame duration
    "default": 0.1      # Default animation frame duration
}

# Animation update frequency
ANIMATION_UPDATE_FPS = 20  # Frames per second for animation updates (50ms intervals)

# =============================================================================
# SPRITE FRAME MAPPINGS
# =============================================================================

# Animal animation frame mappings (applies to chicken, cat, dog, duck)
ANIMAL_ANIMATIONS = {
    "walk_up": [8, 9, 10, 11],
    "walk_right": [4, 5, 6, 7],   
    "walk_down": [0, 1, 2, 3],    
    "walk_left": [12, 13, 14, 15],
    "sit_down": [16, 17], 
    "sit_right": [18, 19], 
    "sit_up": [21, 20], 
    "sit_left": [23, 22], 
    "stand_down": [17, 16],  # Reverse of sit_down
    "stand_right": [19, 18], # Reverse of sit_right
    "stand_up": [20, 21],    # Reverse of sit_up
    "stand_left": [22, 23],  # Reverse of sit_left
    "eat": [24, 25, 26, 27]
}

# Emote animation frame mappings
EMOTE_ANIMATIONS = {
    "enter": [0, 1, 2, 3],
    "exit": [3, 2, 1, 0],  # Reverse of enter
    "confused": [8, 9, 10, 11],
    "angry": [12, 13, 14, 15],
    "important": [16, 17, 18, 19],
    "love": [20, 21, 22, 23],
    "sleepy": [24, 25, 26, 27],
    "sad": [28, 29, 30, 31],
    "happy": [32, 33, 34, 35],
    "speechless": [40, 41, 42, 43]
}

# Animation loop settings
ANIMATION_LOOPS = {
    "walk_up": True, "walk_right": True, "walk_down": True, "walk_left": True,
    "eat": True,
    "sit_down": False, "sit_right": False, "sit_up": False, "sit_left": False,
    "stand_down": False, "stand_right": False, "stand_up": False, "stand_left": False,
    "enter": False, "exit": False, "confused": False, "angry": False,
    "important": False, "love": False, "sleepy": False, "sad": False,
    "happy": False, "speechless": False
}

# =============================================================================
# PET BEHAVIOR SETTINGS
# =============================================================================

# State duration ranges (in seconds)
STATE_DURATIONS = {
    # "IDLE": (10, 10),   # How long pet stays idle
    # "SIT": (10, 30),    # How long pet sits
    # "EAT": (5, 5),     # How long pet eats
    # "WALK": (0, 0)      # Variable based on distance
    "IDLE": (5, 5),   # How long pet stays idle
    "SIT": (5, 5),    # How long pet sits
    "EAT": (5, 5),     # How long pet eats
    "WALK": (0, 0)      # Variable based on distance
}

# State transition probabilities
STATE_TRANSITIONS = {
    # "IDLE": {
    #     "IDLE": 0.1,    # Probability of staying in IDLE
    #     "WALK": 0.4,    # Probability of transitioning to WALK
    #     "SIT": 0.4,     # Probability of transitioning to SIT
    #     "EAT": 0.1      # Probability of transitioning to EAT
    # },
    # "SIT": {
    #     "IDLE": 0.4,    # Probability of transitioning to IDLE
    #     "WALK": 0.1,    # Probability of transitioning to WALK
    #     "SIT": 0.5      # Probability of staying in SIT
    # },
    # "WALK": {
    #     "IDLE": 0.5,    # Probability of transitioning to IDLE
    #     "SIT": 0.3,     # Probability of transitioning to SIT
    #     "EAT": 0.1,     # Probability of transitioning to EAT
    #     "WALK": 0.1     # Probability of continuing to walk (new destination)
    # },
    # "EAT": {
    #     "IDLE": 0.4,    # Probability of transitioning to IDLE
    #     "WALK": 0.3,    # Probability of transitioning to WALK
    #     "SIT": 0.3      # Probability of transitioning to SIT
    # }
    "IDLE": {
        "IDLE": 0,    # Probability of staying in IDLE
        "WALK": 1,    # Probability of transitioning to WALK
        "SIT": 0,     # Probability of transitioning to SIT
        "EAT": 0      # Probability of transitioning to EAT
    },
    "SIT": {
        "IDLE": 0.4,    # Probability of transitioning to IDLE
        "WALK": 0.1,    # Probability of transitioning to WALK
        "SIT": 0.5      # Probability of staying in SIT
    },
    "WALK": {
        "IDLE": 0,    # Probability of transitioning to IDLE
        "SIT": 0,     # Probability of transitioning to SIT
        "EAT": 0,     # Probability of transitioning to EAT
        "WALK": 1     # Probability of continuing to walk (new destination)
    },
    "EAT": {
        "IDLE": 0.4,    # Probability of transitioning to IDLE
        "WALK": 0.3,    # Probability of transitioning to WALK
        "SIT": 0.3      # Probability of transitioning to SIT
    }
}

# Movement speed (pixels per update)
MOVEMENT_SPEED = 1  # How many pixels pet moves per frame when walking


# =============================================================================
# MOOD SYSTEM SETTINGS
# =============================================================================

# Mood settings
MOOD_SETTINGS = {
    "initial": 50,          # Starting mood for new pets
    "min": 0,               # Minimum mood value
    "max": 100,             # Maximum mood value
    "pet_increase": 1,      # Mood increase per pet interaction
    "decay_per_hour": 1,    # Mood decay per hour
    "daily_reset_min": 40,  # Minimum mood on daily reset
    "daily_reset_max": 60   # Maximum mood on daily reset
}

# Emote selection based on mood
MOOD_EMOTES = {
    "high": ["happy", "love", "important", "sleepy"],           # Mood >= 75
    "low": ["angry", "sad", "confused", "speechless", "sleepy"], # Mood <= 50  
    "medium": ["confused", "angry", "important", "sleepy", "speechless"]  # 50 < Mood < 75
}

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================

# Default scaling
DEFAULT_SCALE_FACTOR = 4  # Default sprite scale (16x16 -> 64x64)

# Sprite dimensions
SPRITE_SIZE = 16  # Base sprite size in pixels

# Window settings
WINDOW_UPDATE_FPS = 20  # Main window update frequency

# =============================================================================
# SAVE SYSTEM SETTINGS
# =============================================================================

# Auto-save interval (milliseconds)
AUTO_SAVE_INTERVAL = 60000  # Save every 60 seconds

# Save directory
SAVE_DIRECTORY = "pet_saves"

# =============================================================================
# ASSET PATHS
# =============================================================================

# Sprite sheet paths
SPRITE_PATHS = {
    "base_directory": "prompts/base_prompt/visualization/sprite_sheets",
    "animals": {
        "chicken": "chicken_brown.png",
        "cat": "cat_grey.png", 
        "dog": "dog_brown.png",
        "duck": "duck.png"
    },
    "emote": "emote.png",
    "chatbox": "chatbox.png"
}

# =============================================================================
# CHAT SYSTEM SETTINGS  
# =============================================================================

# Chat settings
CHAT_SETTINGS = {
    "scale_factor": 4,              # Chatbox scale multiplier
    "double_click_timeout": 300,    # Double-click detection timeout (ms)
    "default_responses": {          # Fallback responses when no LLM
        "chicken": ["Cluck cluck!", "Bawk bawk!", "Clucky cluck!", "Baaawk!"],
        "cat": ["Meow!", "Purr purr!", "Mrow!", "Mew mew!"],
        "dog": ["Woof!", "Bark bark!", "Wag wag!", "Arf arf!"],
        "duck": ["Quack quack!", "Quaaack!", "Quack!", "Quack quack quack!"]
    }
}

# =============================================================================
# EMOTE SYSTEM SETTINGS
# =============================================================================

# Emote sequence settings
EMOTE_SETTINGS = {
    "loops_per_emote": 3,           # How many times each emote loops
    "sequence_delay": 100,          # Delay between emote sequence parts (ms)
    "valid_emotes": [               # Available emote types
        "confused", "angry", "important", "love", 
        "sleepy", "sad", "happy", "speechless"
    ]
}

# =============================================================================
# DEBUG SETTINGS
# =============================================================================

# Global debug mode (set by command line arguments)
DEBUG_MODE = False

# Logging settings (controlled by DEBUG_MODE)
DEBUG_SETTINGS = {
    "enable_state_logging": False,       # Enable pet state transition logging
    "enable_interaction_logging": False, # Enable interaction logging
    "enable_drag_logging": False,        # Enable drag/drop logging
    "enable_animation_logging": False    # Enable animation pause/resume logging
}

def set_debug_mode(enabled: bool):
    """Enable or disable debug mode and update all debug settings"""
    import sys
    current_module = sys.modules[__name__]
    setattr(current_module, 'DEBUG_MODE', enabled)
    
    # Update all debug settings based on debug mode
    DEBUG_SETTINGS["enable_state_logging"] = enabled
    DEBUG_SETTINGS["enable_interaction_logging"] = enabled
    DEBUG_SETTINGS["enable_drag_logging"] = enabled
    DEBUG_SETTINGS["enable_animation_logging"] = enabled

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_full_sprite_path(animal_type):
    """Get full path to animal sprite sheet"""
    import os
    # Get the directory where this config.py file is located (src/)
    config_dir = os.path.dirname(__file__)
    # Go up one level to the project root, then to the sprite sheets
    base_dir = os.path.join(config_dir, "..", SPRITE_PATHS["base_directory"])
    base_dir = os.path.abspath(base_dir)
    
    if animal_type in SPRITE_PATHS["animals"]:
        filename = SPRITE_PATHS["animals"][animal_type]
        return os.path.join(base_dir, filename)
    return os.path.join(base_dir, "chicken_brown.png")  # Default fallback

def get_emote_sprite_path():
    """Get full path to emote sprite sheet"""
    import os
    config_dir = os.path.dirname(__file__)
    base_dir = os.path.join(config_dir, "..", SPRITE_PATHS["base_directory"])
    base_dir = os.path.abspath(base_dir)
    return os.path.join(base_dir, SPRITE_PATHS['emote'])

def get_chatbox_sprite_path():
    """Get full path to chatbox sprite sheet"""
    import os
    config_dir = os.path.dirname(__file__)
    base_dir = os.path.join(config_dir, "..", SPRITE_PATHS["base_directory"])
    base_dir = os.path.abspath(base_dir)
    return os.path.join(base_dir, SPRITE_PATHS['chatbox'])

def validate_config():
    """Validate configuration values"""
    errors = []
    
    # Validate animation durations
    for key, duration in ANIMATION_DURATIONS.items():
        if duration <= 0:
            errors.append(f"Animation duration '{key}' must be positive: {duration}")
    
    # Validate mood settings
    if MOOD_SETTINGS["min"] >= MOOD_SETTINGS["max"]:
        errors.append("Mood min must be less than mood max")
    
    if MOOD_SETTINGS["initial"] < MOOD_SETTINGS["min"] or MOOD_SETTINGS["initial"] > MOOD_SETTINGS["max"]:
        errors.append("Initial mood must be within min/max range")
    
    # Validate state transition probabilities
    for state, transitions in STATE_TRANSITIONS.items():
        total_prob = sum(transitions.values())
        if abs(total_prob - 1.0) > 0.01:  # Allow small floating point errors
            errors.append(f"State '{state}' transition probabilities sum to {total_prob}, should be 1.0")
    
    return errors

# Validate configuration on import
if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration validation passed!")