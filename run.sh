#!/bin/bash

# Desktop Pet Game Launch Script

echo "🎮 Starting Desktop Pet Game..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.py first."
    echo "   python setup.py"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found in current directory"
    exit 1
fi

# Run the application
echo "🚀 Launching application..."
python main.py

# Deactivate virtual environment when done
deactivate

echo "👋 Desktop Pet Game closed"