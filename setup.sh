#!/bin/bash

# AI Daily Report Generator Setup Script
# This script installs dependencies and initializes the project

set -e

echo "========================================="
echo "AI Daily Report Generator Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.6 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Found: $PYTHON_VERSION"
echo ""

# Check pip
echo "Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 not found. Please install pip."
    exit 1
fi
echo "pip3 found"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt --user
echo ""

# Create config file if not exists
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from template..."
    cp config.example.yaml config.yaml
    echo ""
    echo "IMPORTANT: Please edit config.yaml and fill in your API keys:"
    echo "  - Reddit: client_id and client_secret from https://www.reddit.com/prefs/apps"
    echo "  - GitHub: repository URL for storing reports"
    echo "  - Twitter (optional): RapidAPI key"
    echo ""
fi

# Create directories
echo "Creating directories..."
mkdir -p reports logs
echo ""

# Setup Git
echo "Setting up Git repository..."
if [ ! -d ".git" ]; then
    git init
    echo "Git repository initialized"
    echo ""
    echo "To configure GitHub remote:"
    echo "  1. Create a new repository on GitHub"
    echo "  2. Run: git remote add origin <your-repo-url>"
    echo "  3. Or set repo_url in config.yaml"
    echo ""
else
    echo "Git repository already exists"
fi
echo ""

# Instructions for Reddit API
echo "========================================="
echo "Reddit API Setup (Required for Reddit source)"
echo "========================================="
echo ""
echo "To setup Reddit API (free):"
echo "  1. Go to https://www.reddit.com/prefs/apps"
echo "  2. Click 'create another app...'"
echo "  3. Choose 'script' type"
echo "  4. Set name: 'AI Daily Report Bot'"
echo "  5. Set redirect uri: http://localhost:8080"
echo "  6. Copy client_id (under the app name) and client_secret"
echo "  7. Add them to config.yaml under reddit section"
echo ""

# Instructions for SSH key (for Git push)
echo "========================================="
echo "SSH Key Setup (For GitHub Push)"
echo "========================================="
echo ""
echo "To setup SSH key for GitHub:"
echo "  1. Generate SSH key: ssh-keygen -t rsa -b 4096 -C 'your_email@example.com'"
echo "  2. Copy public key: cat ~/.ssh/id_rsa.pub"
echo "  3. Add to GitHub: https://github.com/settings/ssh/new"
echo "  4. Test connection: ssh -T git@github.com"
echo ""

# Instructions for Cron job
echo "========================================="
echo "Cron Job Setup (For Daily Execution)"
echo "========================================="
echo ""
echo "To setup automatic daily execution:"
echo "  1. Run: crontab -e"
echo "  2. Add line (runs at 8:00 AM daily):"
echo "     0 8 * * * cd $(pwd) && /usr/bin/python3 src/main.py >> logs/cron.log 2>&1"
echo ""

# Test run
echo "========================================="
echo "Test Run"
echo "========================================="
echo ""
echo "To test the generator:"
echo "  python3 src/main.py --dry-run"
echo ""
echo "For full test with Git commit:"
echo "  python3 src/main.py"
echo ""

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml with your credentials"
echo "  2. Test run: python3 src/main.py --dry-run"
echo "  3. Configure GitHub remote if needed"
echo "  4. Setup cron job for automation"
echo ""
echo "For help, see README.md"
echo ""