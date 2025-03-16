#!/bin/bash
# Script to handle The Blue Alliance API key and Firebase configuration
# Looks for APIKEYS.txt in the same directory
# If not found, prompts user to enter keys
# Exports the keys to appropriate environment variables

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
KEYS_FILE="$SCRIPT_DIR/APIKEYS.txt"
OLD_KEY_FILE="$SCRIPT_DIR/TBAKEY.txt"

# Function to validate TBA API key format
validate_tba_key() {
    local key=$1
    # Simple validation - TBA keys are typically alphanumeric
    if [[ ! $key =~ ^[a-zA-Z0-9]+$ ]]; then
        return 1
    fi
    return 0
}

# Check if old TBAKEY.txt exists and migrate it
if [ -f "$OLD_KEY_FILE" ] && [ ! -f "$KEYS_FILE" ]; then
    echo "Found old TBAKEY.txt file. Migrating to new format..."
    TBA_API_KEY=$(cat "$OLD_KEY_FILE")
    echo "TBA_API_KEY=$TBA_API_KEY" > "$KEYS_FILE"
    echo "FIREBASE_API_KEY=" >> "$KEYS_FILE"
    echo "FIREBASE_AUTH_DOMAIN=" >> "$KEYS_FILE"
    echo "FIREBASE_PROJECT_ID=" >> "$KEYS_FILE"
    echo "Migrated TBA key to $KEYS_FILE"
fi

# Function to load keys from file
load_keys() {
    if [ -f "$KEYS_FILE" ]; then
        # Source the file to load variables
        source "$KEYS_FILE"
        return 0
    fi
    return 1
}

# Function to save keys to file
save_keys() {
    echo "TBA_API_KEY=$TBA_API_KEY" > "$KEYS_FILE"
    echo "FIREBASE_API_KEY=$FIREBASE_API_KEY" >> "$KEYS_FILE"
    echo "FIREBASE_AUTH_DOMAIN=$FIREBASE_AUTH_DOMAIN" >> "$KEYS_FILE"
    echo "FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID" >> "$KEYS_FILE"
    echo "Keys saved to $KEYS_FILE"
}

# Check if APIKEYS.txt exists
if load_keys; then
    echo "Found existing APIKEYS.txt file."
    
    # Validate the TBA key
    if ! validate_tba_key "$TBA_API_KEY"; then
        echo "Warning: The TBA key in APIKEYS.txt appears to be invalid."
    else
        echo "Using TBA API key from APIKEYS.txt"
    fi
    
    # Check if Firebase keys are set
    if [ -z "$FIREBASE_API_KEY" ] || [ -z "$FIREBASE_AUTH_DOMAIN" ] || [ -z "$FIREBASE_PROJECT_ID" ]; then
        echo "Some Firebase configuration values are missing."
        NEED_FIREBASE=true
    else
        echo "Using Firebase configuration from APIKEYS.txt"
    fi
else
    echo "No APIKEYS.txt file found."
    NEED_TBA=true
    NEED_FIREBASE=true
fi

# Handle TBA API key if needed
if [ "$NEED_TBA" = true ]; then
    echo "Would you like to enter a The Blue Alliance API key or generate a new one?"
    echo "1. Enter an existing key"
    echo "2. Generate a new key (Note: This will require you to register on The Blue Alliance website)"
    read -r choice
    
    case $choice in
        1)
            echo "Please enter your The Blue Alliance API key:"
            read -r TBA_API_KEY
            # Validate the key
            if ! validate_tba_key "$TBA_API_KEY"; then
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
            read -r TBA_API_KEY
            # Validate the key
            if ! validate_tba_key "$TBA_API_KEY"; then
                echo "Warning: The key you entered appears to be invalid. Using it anyway."
            fi
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
fi

# Handle Firebase configuration if needed
if [ "$NEED_FIREBASE" = true ]; then
    echo "Please enter your Firebase configuration:"
    
    echo "Firebase API Key:"
    read -r FIREBASE_API_KEY
    
    echo "Firebase Auth Domain:"
    read -r FIREBASE_AUTH_DOMAIN
    
    echo "Firebase Project ID:"
    read -r FIREBASE_PROJECT_ID
fi

# Save all keys to file
save_keys

# Export the keys to environment variables
export VITE_TBA_API_READ_KEY="$TBA_API_KEY"
export VITE_FIREBASE_API_KEY="$FIREBASE_API_KEY"
export VITE_FIREBASE_AUTH_DOMAIN="$FIREBASE_AUTH_DOMAIN"
export VITE_FIREBASE_PROJECT_ID="$FIREBASE_PROJECT_ID"

echo "Exported API keys to environment variables:"
echo "- VITE_TBA_API_READ_KEY"
echo "- VITE_FIREBASE_API_KEY"
echo "- VITE_FIREBASE_AUTH_DOMAIN"
echo "- VITE_FIREBASE_PROJECT_ID"
echo ""
echo "To use these keys in your current terminal session, run:"
echo "source $0"
echo ""
echo "To make this permanent, add the following lines to your ~/.bashrc or ~/.zshrc:"
echo "export VITE_TBA_API_READ_KEY=\"$TBA_API_KEY\""
echo "export VITE_FIREBASE_API_KEY=\"$FIREBASE_API_KEY\""
echo "export VITE_FIREBASE_AUTH_DOMAIN=\"$FIREBASE_AUTH_DOMAIN\""
echo "export VITE_FIREBASE_PROJECT_ID=\"$FIREBASE_PROJECT_ID\""
