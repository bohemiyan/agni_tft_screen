#!/bin/bash

# Function to check and install a package
install_if_missing() {
    if ! command -v "$1" &> /dev/null; then
        echo "$1 not found. Attempting to install..."
        sudo apt-get update
        sudo apt-get install -y "$2" || exit 1
    else
        echo "$1 is already installed."
    fi
}

# Check for system dependencies
install_if_missing "node" "nodejs"
install_if_missing "npm" "npm"
install_if_missing "python3" "python3"
install_if_missing "pip" "python3-pip"
install_if_missing "python3-venv" "python3-venv"
install_if_missing "make" "build-essential"

# Navigate to application root
BASE_DIR="$(dirname "$0")"
cd "$BASE_DIR" || exit 1

# Check for built GUI
if [ ! -d "client/dist" ]; then
    echo "GUI build not found. Building GUI..."
    cd client || exit 1
    if [ ! -d "node_modules" ]; then
        echo "Installing GUI dependencies..."
        npm install || exit 1
    fi
    npm run build || exit 1
    cd ..
fi

echo "Setting up Python backend..."
cd pyserver || exit 1

# Check for python venv
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv || exit 1
    echo "Installing Python dependencies..."
    ./venv/bin/pip install -r requirements.txt || exit 1
fi

# Start the application
echo "Starting s1panel Python backend on port 1234..."
./venv/bin/python main.py
