#!/bin/bash

# Function to check and install a package
install_if_missing() {
    if ! command -v "$1" &> /dev/null; then
        echo "$1 not found. Attempting to install..."
        apt-get update
        apt-get install -y "$2" || exit 1
    else
        echo "$1 is already installed."
    fi
}

# Check for system dependencies
install_if_missing "node" "nodejs"
install_if_missing "npm" "npm"
install_if_missing "python3" "python3"
install_if_missing "make" "build-essential"

# Navigate to s1panel directory
cd "$(dirname "$0")/s1panel" || exit 1

# Check for node_modules
if [ ! -d "node_modules" ]; then
    echo "Installing application dependencies..."
    npm install || exit 1
fi

# Check for built GUI
if [ ! -d "gui/dist" ]; then
    echo "GUI build not found. Building GUI..."
    cd gui || exit 1
    if [ ! -d "node_modules" ]; then
        echo "Installing GUI dependencies..."
        npm install || exit 1
    fi
    npm run build || exit 1
    cd ..
fi

# Start the application
echo "Starting s1panel on port 1234..."
node main.js
