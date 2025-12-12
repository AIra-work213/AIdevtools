#!/usr/bin/env python3
"""
Test script to verify smooth theme transitions work correctly.
"""

import subprocess
import time
import os
from pathlib import Path

def check_theme_transition_css():
    """Check if theme transition CSS is properly configured."""
    print("Checking theme transition CSS configuration...")

    css_file = Path("src/frontend/src/index.css")
    if not css_file.exists():
        print("✗ index.css not found")
        return False

    content = css_file.read_text()

    # Check for transition properties
    checks = [
        ("transition", "Theme transitions defined"),
        ("transition: background 0.3s", "Background transition defined"),
        ("transition-colors", "Color transitions defined"),
    ]

    all_passed = True
    for check, description in checks:
        if check in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - Missing: {check}")
            all_passed = False

    return all_passed


def check_theme_context_transitions():
    """Check if ThemeContext has transition logic."""
    print("\nChecking ThemeContext transition implementation...")

    context_file = Path("src/frontend/src/contexts/ThemeContext.tsx")
    if not context_file.exists():
        print("✗ ThemeContext.tsx not found")
        return False

    content = context_file.read_text()

    # Check for transition implementation
    checks = [
        ("transition", "Transition styles applied"),
        ("0.3s ease", "Proper transition timing"),
        ("setTimeout", "Timeout cleanup implemented"),
    ]

    all_passed = True
    for check, description in checks:
        if check in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}")
            all_passed = False

    return all_passed


def check_component_transitions():
    """Check if components use transition classes."""
    print("\nChecking component transition classes...")

    layout_file = Path("src/frontend/src/components/Layout.tsx")
    if not layout_file.exists():
        print("✗ Layout.tsx not found")
        return False

    content = layout_file.read_text()

    # Check for transition classes
    checks = [
        ("transition-theme", "Theme transition class applied"),
        ("transition-all duration-200", "All transitions with duration"),
        ("transition-colors duration-200", "Color transitions with duration"),
    ]

    all_passed = True
    for check, description in checks:
        if check in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - Missing: {check}")
            all_passed = False

    return all_passed


def check_tailwind_config():
    """Check Tailwind configuration for dark mode."""
    print("\nChecking Tailwind configuration...")

    config_file = Path("src/frontend/tailwind.config.js")
    if not config_file.exists():
        print("✗ tailwind.config.js not found")
        return False

    content = config_file.read_text()

    # Check for dark mode configuration
    checks = [
        ("darkMode: 'class'", "Dark mode configured for class-based switching"),
    ]

    all_passed = True
    for check, description in checks:
        if check in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - Missing: {check}")
            all_passed = False

    return all_passed


def create_theme_test_html():
    """Create a simple HTML file to test theme transitions."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Theme Transition Test</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
        }
    </script>
    <style>
        html {
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        body {
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        .transition-theme {
            transition: all 0.3s ease;
        }
    </style>
</head>
<body class="bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-8">
    <div class="max-w-2xl mx-auto space-y-6">
        <h1 class="text-3xl font-bold mb-6">Theme Transition Test</h1>

        <div class="transition-theme bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 class="text-xl font-semibold mb-4">Test Card</h2>
            <p class="mb-4">This card should transition smoothly when theme changes.</p>
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-gray-100 dark:bg-gray-700 p-4 rounded">
                    <h3 class="font-medium">Light/Dark Element</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        Notice the smooth transition between themes
                    </p>
                </div>
                <div class="bg-blue-100 dark:bg-blue-900 p-4 rounded">
                    <h3 class="font-medium">Colored Element</h3>
                    <p class="text-sm text-blue-800 dark:text-blue-200">
                        Colors also transition smoothly
                    </p>
                </div>
            </div>
        </div>

        <button
            onclick="toggleTheme()"
            class="px-6 py-3 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white rounded-lg transition-all duration-300 font-medium"
        >
            Toggle Theme
        </button>

        <div class="bg-yellow-50 dark:bg-gray-800 border border-yellow-200 dark:border-gray-700 p-4 rounded-lg">
            <h3 class="font-medium text-yellow-800 dark:text-yellow-200 mb-2">Instructions:</h3>
            <ol class="list-decimal list-inside text-yellow-700 dark:text-yellow-300 space-y-1">
                <li>Observe the current theme (light or dark)</li>
                <li>Click the "Toggle Theme" button</li>
                <li>Watch for smooth transitions (should take ~300ms)</li>
                <li>Verify all elements transition smoothly</li>
            </ol>
        </div>

        <div class="text-sm text-gray-500 dark:text-gray-400">
            <p>Transition Duration: 300ms</p>
            <p>Easing Function: ease-in-out</p>
        </div>
    </div>

    <script>
        // Check for saved theme preference or default to light
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.classList.add(currentTheme);

        function toggleTheme() {
            const html = document.documentElement;
            const isDark = html.classList.contains('dark');

            // Add smooth transition
            html.style.transition = 'background-color 0.3s ease, color 0.3s ease';

            // Toggle theme
            if (isDark) {
                html.classList.remove('dark');
                html.classList.add('light');
                localStorage.setItem('theme', 'light');
            } else {
                html.classList.remove('light');
                html.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            }

            // Remove transition after animation
            setTimeout(() => {
                html.style.transition = '';
            }, 300);
        }
    </script>
</body>
</html>"""

    with open("theme_test.html", "w") as f:
        f.write(html_content)

    print("\n✓ Created theme_test.html - Open in browser to test transitions")


def main():
    """Run all theme transition checks."""
    print("Testing Theme Transition Implementation")
    print("=" * 50)

    all_passed = True

    # Run checks
    checks = [
        check_theme_transition_css,
        check_theme_context_transitions,
        check_component_transitions,
        check_tailwind_config,
    ]

    for check in checks:
        if not check():
            all_passed = False

    # Create test HTML
    create_theme_test_html()

    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All theme transition checks passed!")
        print("\nThe smooth theme transition feature has been successfully implemented:")
        print("  • CSS transitions configured for 300ms duration")
        print("  • Theme context includes smooth transition logic")
        print("  • Components use appropriate transition classes")
        print("  • Tailwind configured for class-based dark mode")
        print("\nTo test manually:")
        print("  1. Open theme_test.html in a browser")
        print("  2. Click the toggle button")
        print("  3. Observe smooth 300ms transitions")
    else:
        print("✗ Some theme transition checks failed.")
        print("Please review the errors above and fix them.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())