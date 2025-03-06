#!/bin/bash

# Script to handle The Blue Alliance API key
# Looks for TBAKEY.txt in the same directory
# If not found, prompts user to enter a key
# Exports the key to VITE_TBA_API_READ_KEY environment variable

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
KEY_FILE="$SCRIPT_DIR/TBAKEY.txt"

# Function to validate API key format
validate_key() {
    local key=$1
    # Simple validation - TBA keys are typically alphanumeric
    if [[ ! $key =~ ^[a-zA-Z0-9]+$ ]]; then
        return 1
    fi
    return 0
}

# Check if TBAKEY.txt exists
if [ -f "$KEY_FILE" ]; then
    echo "Found existing TBAKEY.txt file."
    API_KEY=$(cat "$KEY_FILE")
    
    # Validate the key from file
    if ! validate_key "$API_KEY"; then
        echo "Warning: The key in TBAKEY.txt appears to be invalid."
        echo "Would you like to enter a new key? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "Please enter your The Blue Alliance API key:"
            read -r API_KEY
            echo "$API_KEY" > "$KEY_FILE"
            echo "New key saved to TBAKEY.txt"
        fi
    else
        echo "Using API key from TBAKEY.txt"
    fi
else
    echo "No TBAKEY.txt file found."
    echo "Would you like to enter a The Blue Alliance API key or generate a new one?"
    echo "1. Enter an existing key"
    echo "2. Generate a new key (Note: This will require you to register on The Blue Alliance website)"
    read -r choice
    
    case $choice in
        1)
            echo "Please enter your The Blue Alliance API key:"
            read -r API_KEY
            # Validate the key
            if ! validate_key "$API_KEY"; then
                echo "Warning: The key you entered appears to be invalid. Using it anyway."
            fi
            ;;
        2)
            echo "To generate a new key, you need to:"
            echo "1. Visit https://www.thebluealliance.com/"
            echo "2. Create an account or login"
            echo "3. Go to your account page"
            echo "4. Request a read API key"
            echo ""
            echo "Once you have your key, please enter it below:"
            read -r API_KEY
            # Validate the key
            if ! validate_key "$API_KEY"; then
                echo "Warning: The key you entered appears to be invalid. Using it anyway."
            fi
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
    
    # Save the key to TBAKEY.txt
    echo "$API_KEY" > "$KEY_FILE"
    echo "API key saved to TBAKEY.txt"
fi

# Export the API key to the environment variable
export VITE_TBA_API_READ_KEY="$API_KEY"
echo "Exported API key to VITE_TBA_API_READ_KEY environment variable."
echo "To use this key in your current terminal session, run:"
echo "source $0"
echo ""
echo "To make this permanent, add the following line to your ~/.bashrc or ~/.zshrc:"
echo "export VITE_TBA_API_READ_KEY=\"$API_KEY\""
