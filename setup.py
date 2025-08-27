#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command with description"""
    print(f"\n{'='*50}")
    print(f"🔧 {description}")
    print(f"{'='*50}")
    print(f"Running: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} completed successfully!")
        if result.stdout:
            print("Output:", result.stdout)
    else:
        print(f"❌ {description} failed!")
        if result.stderr:
            print("Error:", result.stderr)
        return False
    return True

def setup_virtual_environment():
    """Setup Python virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    if not run_command("uv venv venv", "Creating virtual environment"):
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    activate_cmd = "source venv/bin/activate" if sys.platform != "win32" else "venv\\Scripts\\activate"
    install_cmd = f"{activate_cmd} && uv pip install -r requirements.txt"
    
    return run_command(install_cmd, "Installing dependencies")

def create_directories():
    """Create necessary directories"""
    directories = [
        "src",
        "prompts/base_prompt/visualization/sprite_sheets",
        "prompts/base_prompt/llm_chat/visualization/sprite_sheets",
        "pet_saves"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version {sys.version} is compatible")
    return True

def main():
    """Main setup function"""
    print("🎮 Desktop Pet Game Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Setup virtual environment
    if not setup_virtual_environment():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("=" * 50)
    print("\nTo run the application:")
    print("1. Activate virtual environment: source venv/bin/activate")
    print("2. Run the application: python main.py")
    print("\nNote: You'll need to add your own Stardew Valley sprite sheets")
    print("or use the placeholder sprites that will be generated automatically.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
