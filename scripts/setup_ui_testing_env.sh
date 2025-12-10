#!/bin/bash
# Setup Global UI Testing Environment
# This script creates a global virtual environment with all UI testing frameworks pre-installed

set -e  # Exit on error

VENV_PATH="$HOME/ui-testing-env"
PYTHON_VERSION="python3"

echo "========================================="
echo "  UI Testing Environment Setup"
echo "========================================="
echo ""
echo "This will create a global environment at: $VENV_PATH"
echo "with all UI testing frameworks pre-installed:"
echo "  - Playwright (with browsers)"
echo "  - Selenium (with WebDriver Manager)"
echo "  - pytest + Allure"
echo ""

# Check if venv already exists
if [ -d "$VENV_PATH" ]; then
    read -p "Environment already exists. Recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing old environment..."
        rm -rf "$VENV_PATH"
    else
        echo "✅ Using existing environment"
        exit 0
    fi
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_VERSION -m venv "$VENV_PATH"

# Activate environment
echo "🔧 Activating environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Playwright dependencies
echo "🎭 Installing Playwright..."
pip install pytest==7.4.3
pip install pytest-playwright==0.4.3
pip install playwright==1.40.0
pip install pytest-asyncio==0.21.1
pip install pytest-xdist==3.5.0

# Install browsers for Playwright
echo "🌐 Installing Playwright browsers (this may take a few minutes)..."
playwright install

# Install Selenium dependencies
echo "🔍 Installing Selenium..."
pip install selenium==4.15.2
pip install webdriver-manager==4.0.1

# Install Allure
echo "📊 Installing Allure..."
pip install allure-pytest==2.15.2

# Install additional utilities
echo "🛠️  Installing utilities..."
pip install python-dotenv==1.0.0
pip install Pillow==10.1.0
pip install requests==2.31.0

# Create activation helper script
ACTIVATE_SCRIPT="$HOME/activate-ui-testing.sh"
cat > "$ACTIVATE_SCRIPT" << 'EOF'
#!/bin/bash
# Quick activation script for UI testing environment

source ~/ui-testing-env/bin/activate

echo "✅ UI Testing environment activated!"
echo ""
echo "Available frameworks:"
echo "  - Playwright: pytest --browser chromium test_*.py"
echo "  - Selenium: pytest test_*.py"
echo ""
echo "To deactivate: deactivate"
EOF

chmod +x "$ACTIVATE_SCRIPT"

# Create Windows activation script
ACTIVATE_BAT="$HOME/activate-ui-testing.bat"
cat > "$ACTIVATE_BAT" << 'EOF'
@echo off
call %USERPROFILE%\ui-testing-env\Scripts\activate.bat
echo.
echo UI Testing environment activated!
echo.
echo Available frameworks:
echo   - Playwright: pytest --browser chromium test_*.py
echo   - Selenium: pytest test_*.py
echo.
echo To deactivate: deactivate
EOF

# Verify installation
echo ""
echo "========================================="
echo "  Verifying Installation"
echo "========================================="
echo ""

echo "Python version:"
python --version

echo ""
echo "Installed packages:"
pip list | grep -E "playwright|selenium|pytest|allure"

echo ""
echo "========================================="
echo "  ✅ Setup Complete!"
echo "========================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "  1. Activate the environment:"
echo "     source ~/activate-ui-testing.sh"
echo "     # or on Windows: activate-ui-testing.bat"
echo ""
echo "  2. Run your UI tests:"
echo "     pytest test_ui.py -v"
echo ""
echo "  3. Deactivate when done:"
echo "     deactivate"
echo ""
echo "💡 Tip: Add this to your ~/.bashrc or ~/.zshrc:"
echo "   alias ui-test='source ~/activate-ui-testing.sh'"
echo ""

deactivate
