# UI Testing Environment - Quick Reference

## 📦 Installation

Run the setup script once to create a global environment with all UI testing frameworks:

```bash
cd /home/akira/Projects/AIdevtools
chmod +x scripts/setup_ui_testing_env.sh
./scripts/setup_ui_testing_env.sh
```

This will:
- Create `~/ui-testing-env/` with all dependencies
- Install Playwright + browsers (Chromium, Firefox, WebKit)
- Install Selenium + WebDriver Manager
- Install pytest, allure-pytest, and utilities
- Create quick activation scripts

**Installation time**: ~5-10 minutes (one-time setup)
**Disk space**: ~500MB

## 🚀 Usage

### Activate Environment

**Linux/Mac:**
```bash
source ~/activate-ui-testing.sh
```

**Windows:**
```bat
activate-ui-testing.bat
```

### Run Tests

Once activated, run tests normally:

```bash
# Playwright tests
pytest test_ui_playwright.py -v
pytest test_ui_playwright.py --headed
pytest test_ui_playwright.py --browser firefox

# Selenium tests
pytest test_ui_selenium.py -v

# With Allure reports
pytest test_ui.py --alluredir=./allure-results
allure serve ./allure-results
```

### Deactivate

```bash
deactivate
```

## 📋 Pre-installed Packages

| Package | Version | Purpose |
|---------|---------|---------|
| playwright | 1.40.0 | UI automation framework |
| pytest-playwright | 0.4.3 | Playwright pytest integration |
| selenium | 4.15.2 | Browser automation |
| webdriver-manager | 4.0.1 | Auto-download drivers |
| pytest | 7.4.3 | Testing framework |
| allure-pytest | 2.15.2 | Test reporting |
| pytest-xdist | 3.5.0 | Parallel execution |

## 🔄 Updating Environment

To update packages in the global environment:

```bash
source ~/ui-testing-env/bin/activate
pip install --upgrade playwright selenium pytest
playwright install  # Update browsers
deactivate
```

## 🛠️ Troubleshooting

### Environment not activating?
```bash
# Recreate the environment
rm -rf ~/ui-testing-env
./scripts/setup_ui_testing_env.sh
```

### Playwright browsers not found?
```bash
source ~/ui-testing-env/bin/activate
playwright install
```

### Permission denied?
```bash
chmod +x scripts/setup_ui_testing_env.sh
chmod +x ~/activate-ui-testing.sh
```

## 💡 Pro Tips

1. **Add alias to shell profile** (`~/.bashrc` or `~/.zshrc`):
   ```bash
   alias ui-test='source ~/activate-ui-testing.sh'
   ```
   Then use: `ui-test` to activate instantly

2. **VS Code integration**: Add to `.vscode/settings.json`:
   ```json
   {
     "python.defaultInterpreterPath": "~/ui-testing-env/bin/python"
   }
   ```

3. **Check environment status**:
   ```bash
   which python  # Should show ~/ui-testing-env/bin/python
   pip list | grep playwright
   ```

## 📊 Generated Files from UI Test Generation

When you generate UI tests via the API, you'll receive:

1. **test_ui.py** - The generated test code
2. **requirements.txt** - Framework-specific dependencies
3. **setup_instructions.md** - Detailed setup guide

**But you won't need them** if using the global environment! Just activate and run.

## 🎯 Example Workflow

```bash
# 1. One-time setup (if not done)
./scripts/setup_ui_testing_env.sh

# 2. Generate tests via TestOps Copilot UI
#    (Playwright/Selenium/Cypress)

# 3. Activate global environment
source ~/activate-ui-testing.sh

# 4. Save generated test code
cat > test_generated.py << EOF
# ... paste generated code ...
EOF

# 5. Run immediately (no pip install needed!)
pytest test_generated.py -v --headed

# 6. View Allure report if generated
pytest test_generated.py --alluredir=./allure-results
allure serve ./allure-results
```

## 🌍 Environment Variables

Optional environment variables for customization:

```bash
# Playwright options
export PLAYWRIGHT_BROWSERS_PATH=$HOME/.playwright-browsers
export PWDEBUG=1  # Enable debug mode

# Selenium options
export WDM_LOG_LEVEL=0  # Suppress WebDriver Manager logs

# Test execution
export PYTEST_TIMEOUT=30  # Default timeout in seconds
```

## 📦 Disk Space Management

The global environment uses:
- **Python packages**: ~100MB
- **Playwright browsers**: ~400MB
- **Total**: ~500MB

To clean up old browser versions:
```bash
source ~/ui-testing-env/bin/activate
playwright install --force  # Remove old, install latest
```

To completely remove:
```bash
rm -rf ~/ui-testing-env
rm ~/activate-ui-testing.sh
```
