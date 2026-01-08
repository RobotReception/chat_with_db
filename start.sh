#!/bin/bash

echo "========================================"
echo "Starting PostgreSQL Chat API"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Check Python version
python3 --version

# Start the application
echo ""
echo "Starting application on http://localhost:3300"
echo "Press CTRL+C to stop"
echo ""

python3 -m app.main
