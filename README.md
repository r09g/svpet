# Desktop Pet Game

A desktop pet application inspired by Stardew Valley, featuring interactive virtual pets that roam freely on your desktop.

## Features

- **Virtual Pets**: Add chickens, cats, dogs, or ducks as desktop pets
- **Interactive Behavior**: Pets have moods, memories, and state-based actions (walk, sit, eat, stand)
- **Chat System**: Double-click pets to chat with them using local LLM models
- **Emote System**: Pets show emotes based on their mood when clicked
- **Drag & Drop**: Move pets around your desktop by dragging them
- **Auto-Save**: Pet data automatically saves every minute
- **Zoom Controls**: Scale pets up or down
- **Always On Top**: Pets stay visible above other applications
- **Transparent Background**: Only pet sprites are visible

## Requirements

- Python 3.8 or higher
- PySide6 (Qt for Python)
- Optional: transformers and torch for LLM chat functionality

## Installation

1. **Clone or download this repository**

2. **Run the setup script**:
   ```bash
   python setup.py
   ```

3. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Getting Started

1. **Launch the application** - A system tray icon will appear
2. **Right-click the tray icon** to access the menu
3. **Add your first pet** using "Add Pet" option
4. **Choose pet type** (chicken, cat, dog, duck) and give it a name

### Interacting with Pets

- **Single click**: Pet the animal (increases mood, shows emote)
- **Double click**: Open chat window to talk with your pet
- **Drag**: Move the pet to a new location on screen

### Chat System

- **Without LLM**: Pets respond with simple animal sounds
- **With LLM**: Connect a local LLM model via "Connect LLM" in tray menu
  - Download a HuggingFace model to your computer
  - Select the model folder through the menu
  - Chat naturally with your pets!

### System Tray Menu

- **Add Pet**: Create a new pet
- **Remove Pet**: Remove an existing pet (with confirmation)
- **Zoom In/Out**: Scale pet size
- **Connect LLM**: Connect local LLM model for chat
- **Quit**: Exit application

## Pet Mechanics

### Mood System
- New pets start with mood 50 (range: 0-100)
- Mood increases by 1 each time you pet them
- Mood decreases by 1 per hour automatically
- Mood resets randomly (40-60) each day/app restart

### State Machine (Chickens)
- **STAND**: Default idle state
- **WALK**: Moves to random screen location
- **SIT**: Sits in place for a period
- **EAT**: Eating animation

### Memory System
Each pet remembers:
- Name and type
- Total times petted
- Total living time
- Chat conversation summaries (with LLM)
- Current mood level

## Sprite Sheets

**⚠️ REQUIRED:** This application requires actual Stardew Valley sprite sheets to function. The application will not start without them.

You must place the following sprite sheets in these exact locations:
- `prompts/base_prompt/visualization/sprite_sheets/chicken_brown.png`
- `prompts/base_prompt/visualization/sprite_sheets/cat_grey.png`
- `prompts/base_prompt/visualization/sprite_sheets/dog_brown.png`
- `prompts/base_prompt/visualization/sprite_sheets/duck.png`
- `prompts/base_prompt/visualization/sprite_sheets/emote.png`
- `prompts/base_prompt/visualization/sprite_sheets/chatbox.png`

### Sprite Sheet Requirements

1. **Chicken sprites**: 7 rows × 4 columns, 16×16px frames
2. **Emote sprites**: 16 rows × 4 columns, 16×16px frames
3. **Chatbox sprite**: Any size (will be scaled automatically)

The sprite sheets must follow the exact frame layouts documented in the design specification for proper animation.

## Save System

- Pet data auto-saves every minute
- Saves include position, mood, memory, and conversation summaries
- Save files stored in `pet_saves/pets_data.json`
- Automatic backup files created on save

## LLM Integration

To enable chat functionality:

1. **Install LLM dependencies**:
   ```bash
   pip install transformers torch accelerate
   ```

2. **Download a model** from HuggingFace (e.g., microsoft/DialoGPT-small)

3. **Connect via tray menu** - select the model directory

4. **Chat with pets** by double-clicking them

## Troubleshooting

### Application Won't Start
- Check Python version (3.8+ required)
- Ensure PySide6 is installed: `pip install PySide6`
- Run from terminal to see error messages

### Pets Not Visible
- Check if pets are outside screen bounds
- Try adding a new pet
- Ensure window stays on top (restart app if needed)

### Chat Not Working
- Verify LLM model path is correct
- Check transformers/torch installation
- Monitor console for error messages

### Performance Issues
- Reduce number of pets
- Lower zoom level
- Check CPU usage (LLM models are resource-intensive)

## Development

The codebase is modular with clear separation of concerns:

- `src/pet_data.py` - Pet data models and memory
- `src/pet_widget.py` - Pet display and interaction
- `src/animation_system.py` - Sprite sheet animation
- `src/pet_state_machine.py` - Pet behavior logic
- `src/emote_system.py` - Emote display and management  
- `src/chat_system.py` - Chat UI and LLM integration
- `src/system_tray.py` - System tray menu
- `src/save_system.py` - Data persistence
- `src/desktop_pet.py` - Main application controller

## License

This project is for educational and personal use. Stardew Valley assets are property of ConcernedApe.

## Contributing

Feel free to submit issues and enhancement requests!

---

Enjoy your virtual pets! 🐔🐱🐶🦆