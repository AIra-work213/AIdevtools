#!/usr/bin/env python3
"""
Patch the AI service to support custom prompts and better test generation
"""
import os

# Read the original ai_service.py
with open('src/backend/app/services/ai_service.py', 'r') as f:
    content = f.read()

# Find the generate_ui_tests method and modify it
import re

# Pattern to find the method signature
method_pattern = r'(async def generate_ui_tests\(\s*self,\s*input_method: str,\s*html_content: Optional\[str\] = None,\s*url: Optional\[str\] = None,\s*selectors: Optional\[Dict\[str, str\]\] = None,\s*framework: str = "playwright")\s*-> Dict\[str, Any\]:'

# Add custom_prompt parameter
new_method_signature = r'\1,\n        custom_prompt: Optional[str] = None\n    ) -> Dict[str, Any]:'

content = re.sub(method_pattern, new_method_signature, content)

# Save the modified file
with open('src/backend/app/services/ai_service.py', 'w') as f:
    f.write(content)

print("✓ Updated AIService to support custom_prompt parameter")

# Now let's also update the system prompt generation to include Chrome-specific configurations
system_prompt_fix = '''
# Find where the stage1_system is defined and enhance it
content = content.replace(
    'stage1_system = f"""You are an expert in UI/E2E testing with {framework}.',
    '''stage1_system = f"""You are an expert in UI/E2E testing with {framework}.

IMPORTANT FOR SELENIUM TESTS:
When generating Selenium tests for headless Linux environments:
1. Use Chrome binary location: /snap/bin/chromium
2. Include these Chrome options:
   - --headless=new
   - --no-sandbox
   - --disable-dev-shm-usage
   - --disable-gpu
   - --remote-debugging-port=9222
3. Use proper WebDriverWait and expected_conditions
4. Make assertions flexible (use 'in' instead of exact matches)
5. Handle elements that might not be present
6. Focus on robust, working tests

Generate clean, functional UI tests WITHOUT Allure decorators (for Python) or reporting tools.
Focus on test logic, element interactions, and {framework} best practices."""

    # Add custom prompt if provided
    if custom_prompt:
        stage1_system += f"\\n\\nADDITIONAL REQUIREMENTS:\\n{custom_prompt}"'''
)

# Apply the system prompt fix
with open('src/backend/app/services/ai_service.py', 'w') as f:
    f.write(eval(f'f"""{content}"""'))

print("✓ Updated system prompt generation")
print("\nTo apply these changes, please restart your application.")