#!/bin/bash
set -e

# Setup dotfiles for the devcontainer user
# Checks for USER_DOTFILES_URL environment variable and clones/updates dotfiles repository

DOTFILES_DIR="$HOME/.dotfiles"

if [ -z "$USER_DOTFILES_URL" ]; then
    echo "USER_DOTFILES_URL not set, skipping dotfiles setup"
    exit 0
fi

echo "Setting up dotfiles from: $USER_DOTFILES_URL"

# Clone or update dotfiles repository
NEED_INSTALL=false

if [ -d "$DOTFILES_DIR" ]; then
    echo "Dotfiles directory exists, updating..."
    cd "$DOTFILES_DIR"
    
    # Check if there are any uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo "Uncommitted changes detected, checking if they're just VS Code .gitconfig helpers..."
        
        # Get list of modified files
        MODIFIED_FILES=$(git diff-index --name-only HEAD --)
        
        # Check if only .gitconfig is modified
        if [ "$MODIFIED_FILES" = ".gitconfig" ] || [ "$MODIFIED_FILES" = "git/.gitconfig" ] || [ "$MODIFIED_FILES" = "gitconfig" ]; then
            # Check if changes are only VS Code credential helper additions
            if git diff HEAD -- "$MODIFIED_FILES" | grep -q "helper.*vscode" && \
               ! git diff HEAD -- "$MODIFIED_FILES" | grep -v -E "(helper.*vscode|^\+\+\+|^---|^@@|^\+.*helper|^\-.*helper)" | grep -q "^[\+\-]"; then
                echo "Only VS Code credential helper changes detected, resetting..."
                git reset --hard HEAD
            else
                echo "Non-VS Code changes detected in .gitconfig, keeping changes and attempting pull..."
            fi
        else
            echo "Changes to files other than .gitconfig detected, keeping changes and attempting pull..."
        fi
    fi
    
    # Capture current HEAD before pull
    OLD_HEAD=$(git rev-parse HEAD)
    
    git pull || {
        echo "Failed to update dotfiles repository"
        exit 1
    }
    
    # Check if pull resulted in new commits
    NEW_HEAD=$(git rev-parse HEAD)
    if [ "$OLD_HEAD" != "$NEW_HEAD" ]; then
        echo "Updates pulled successfully"
        NEED_INSTALL=true
    else
        echo "No updates available"
    fi
else
    echo "Cloning dotfiles repository..."
    git clone "$USER_DOTFILES_URL" "$DOTFILES_DIR" || {
        echo "Failed to clone dotfiles repository"
        exit 1
    }
    cd "$DOTFILES_DIR"
    echo "Repository cloned successfully"
    NEED_INSTALL=true
fi

# Look for and run install script only if we cloned or pulled updates
if [ "$NEED_INSTALL" = true ]; then
    echo "Running install script due to new/updated dotfiles..."
    INSTALL_SCRIPTS=("install.sh" "install" "bootstrap.sh" "bootstrap" "setup.sh" "setup")

    for script in "${INSTALL_SCRIPTS[@]}"; do
        if [ -f "$script" ] && [ -x "$script" ]; then
            echo "Running install script: $script"
            ./"$script" || {
                echo "Install script failed, but continuing..."
            }
            break
        elif [ -f "$script" ]; then
            echo "Running install script: $script (making executable)"
            chmod +x "$script"
            ./"$script" || {
                echo "Install script failed, but continuing..."
            }
            break
        fi
    done
else
    echo "No changes detected, skipping install script"
fi

echo "Dotfiles setup complete"
