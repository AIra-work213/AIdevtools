# UI Test Verification

To verify that Selenium and UI test generation are working correctly in the Docker environment, follow these steps:

1. **Rebuild the Backend Container**:
   Since `requirements.txt` and `Dockerfile` have changed, you must rebuild.
   ```bash
   docker-compose build backend
   docker-compose up -d backend
   ```

2. **Run the Verification Script**:
   Execute the included verification script inside the backend container.
   ```bash
   docker-compose exec backend python3 verify_selenium.py
   ```

   **Expected Output**:
   ```
   Starting Selenium Verification...
   Chrome Binary: /usr/bin/chromium
   ChromeDriver: /usr/lib/chromium/chromedriver
   ...
   SUCCESS: Selenium is working correctly!
   ```

3. **Troubleshooting**:
   - If it fails with "SessionNotCreated", check the versions:
     ```bash
     docker-compose exec backend chromium --version
     docker-compose exec backend chromedriver --version
     ```
   - Ensure they match (e.g., both 119.x or 120.x).

## Changes Made
- **Dockerfile**: Added `chromium`, `chromium-driver`, and symlinks for standard paths.
- **requirements.txt**: Added `selenium` package.
- **ai_service.py**: Added Headless Chrome configuration to generated tests.
- **code_validator.py**: Increased error log size for better debugging.
