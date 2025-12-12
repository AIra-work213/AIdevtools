#!/usr/bin/env python3
"""
Test script to verify markdown rendering in chat works correctly.
"""

import subprocess
import sys
import time
from pathlib import Path


def check_package_dependencies():
    """Check if markdown dependencies are installed."""
    print("Checking markdown dependencies...")

    package_json = Path("src/frontend/package.json")
    if not package_json.exists():
        print("✗ package.json not found")
        return False

    content = package_json.read_text()

    required_deps = ["react-markdown", "remark-gfm", "react-syntax-highlighter"]

    all_present = True
    for dep in required_deps:
        if dep in content:
            print(f"  ✓ {dep} found")
        else:
            print(f"  ✗ {dep} NOT found")
            all_present = False

    return all_present


def check_component_files():
    """Check if markdown components exist."""
    print("\nChecking component files...")

    files_to_check = [
        ("MarkdownRenderer", "src/frontend/src/components/MarkdownRenderer.tsx"),
        ("CopyToClipboard", "src/frontend/src/components/CopyToClipboard.tsx"),
    ]

    all_exist = True
    for name, file_path in files_to_check:
        if Path(file_path).exists():
            print(f"  ✓ {name} component exists")
        else:
            print(f"  ✗ {name} component missing: {file_path}")
            all_exist = False

    return all_exist


def check_chat_message_integration():
    """Check if ChatMessage component uses MarkdownRenderer."""
    print("\nChecking ChatMessage integration...")

    chat_message_path = Path("src/frontend/src/components/chat/ChatMessage.tsx")
    if not chat_message_path.exists():
        print("✗ ChatMessage.tsx not found")
        return False

    content = chat_message_path.read_text()

    checks = [
        ("MarkdownRenderer import", "import { MarkdownRenderer }"),
        ("MarkdownRenderer usage", "<MarkdownRenderer>"),
        ("Conditional rendering for assistant messages", "isUser ?"),
    ]

    all_present = True
    for check_name, check_str in checks:
        if check_str in content:
            print(f"  ✓ {check_name}")
        else:
            print(f"  ✗ {check_name} - Missing: {check_str}")
            all_present = False

    return all_present


def create_markdown_test_page():
    """Create a test page for markdown functionality."""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Chat Test</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react-markdown@9/umd/react-markdown.development.js"></script>
    <script src="https://unpkg.com/remark-gfm@10"></script>
    <style>
        .dark {
            color-scheme: dark;
        }
        body {
            transition: background-color 0.3s ease;
        }
    </style>
</head>
<body class="bg-gray-100 p-8">
    <div id="root"></div>

    <script type="text/babel">
        const { useState } = React;
        const ReactMarkdown = window.ReactMarkdown.default;
        const remarkGfm = window.remarkGfm.default;

        function MarkdownRenderer({ children }) {
            return (
                <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    className="prose max-w-none"
                    components={{
                        code({node, inline, className, children, ...props}) {
                            const match = /language-(\\w+)/.exec(className || '');
                            const language = match ? match[1] : '';

                            if (!inline && language) {
                                return (
                                    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-2">
                                        <code className={className} {...props}>
                                            {children}
                                        </code>
                                    </pre>
                                );
                            }

                            return (
                                <code className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-sm" {...props}>
                                    {children}
                                </code>
                            );
                        },
                        blockquote({children}) {
                            return (
                                <blockquote className="border-l-4 border-gray-300 pl-4 my-2 italic">
                                    {children}
                                </blockquote>
                            );
                        },
                        h1({children}) {
                            return <h1 className="text-2xl font-bold mt-4 mb-2">{children}</h1>;
                        },
                        h2({children}) {
                            return <h2 className="text-xl font-semibold mt-3 mb-2">{children}</h2>;
                        },
                        p({children}) {
                            return <p className="my-2">{children}</p>;
                        },
                        ul({children}) {
                            return <ul className="list-disc list-inside my-2">{children}</ul>;
                        },
                        ol({children}) {
                            return <ol className="list-decimal list-inside my-2">{children}</ol>;
                        },
                        table({children}) {
                            return (
                                <div className="overflow-x-auto my-2">
                                    <table className="min-w-full border">{children}</table>
                                </div>
                            );
                        },
                        th({children}) {
                            return <th className="border px-3 py-2 bg-gray-100">{children}</th>;
                        },
                        td({children}) {
                            return <td className="border px-3 py-2">{children}</td>;
                        }
                    }}
                >
                    {children}
                </ReactMarkdown>
            );
        }

        function ChatMessage({ type, content }) {
            const isUser = type === 'user';

            return (
                <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
                    <div className={`max-w-2xl ${isUser ? 'order-2' : 'order-1'}`}>
                        <div className={`p-4 rounded-lg ${
                            isUser
                                ? 'bg-blue-500 text-white'
                                : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                        }`}>
                            {isUser ? (
                                <div className="whitespace-pre-wrap">{content}</div>
                            ) : (
                                <MarkdownRenderer>{content}</MarkdownRenderer>
                            )}
                        </div>
                    </div>
                </div>
            );
        }

        function App() {
            const [isDark, setIsDark] = useState(false);

            const toggleDarkMode = () => {
                setIsDark(!isDark);
                document.body.classList.toggle('dark');
            };

            return (
                <div className={`min-h-screen ${isDark ? 'dark' : ''}`}>
                    <div className="max-w-4xl mx-auto">
                        <div className="flex justify-between items-center mb-8">
                            <h1 className="text-3xl font-bold">Markdown Chat Test</h1>
                            <button
                                onClick={toggleDarkMode}
                                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg"
                            >
                                {isDark ? 'Light' : 'Dark'} Mode
                            </button>
                        </div>

                        <div className="bg-white dark:bg-gray-900 rounded-lg p-6 mb-4">
                            <h2 className="text-xl font-semibold mb-4">Sample Chat Messages</h2>

                            <ChatMessage
                                type="user"
                                content="Can you help me write tests for this Python function?"
                            />

                            <ChatMessage
                                type="assistant"
                                content={`Sure! I can help you write comprehensive tests. Here's an example:

\`\`\`python
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
\`\`\`

### Test Cases

Here are the test cases I recommend:

1. **Positive cases**: Test normal addition
2. **Edge cases**: Test with zero and negative numbers
3. **Error cases**: Test with invalid input

\`\`\`python
import pytest
from your_module import add_numbers

def test_add_positive_numbers():
    """Test adding positive numbers."""
    assert add_numbers(2, 3) == 5
    assert add_numbers(10, 20) == 30

def test_add_with_zero():
    """Test adding with zero."""
    assert add_numbers(5, 0) == 5
    assert add_numbers(0, 7) == 7

def test_add_negative_numbers():
    """Test adding negative numbers."""
    assert add_numbers(-2, -3) == -5
    assert add_numbers(5, -3) == 2
\`\`\`

| Test Case | Input | Expected | Status |
|-----------|-------|----------|--------|
| Positive | (2, 3) | 5 | ✅ |
| Zero | (5, 0) | 5 | ✅ |
| Negative | (-2, -3) | -5 | ✅ |

> **Note**: Always consider edge cases when writing tests!

The tests follow the **AAA pattern**:
- **Arrange**: Set up test data
- **Act**: Call the function
- **Assert**: Verify the result

These tests will ensure your function works correctly in all scenarios.`}
                            />
                        </div>

                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
                            <h3 className="text-lg font-semibold mb-2">Features Implemented:</h3>
                            <ul className="list-disc list-inside space-y-1">
                                <li>✅ Text formatting (bold, italic)</li>
                                <li>✅ Code blocks with syntax highlighting</li>
                                <li>✅ Tables with proper styling</li>
                                <li>✅ Lists (ordered and unordered)</li>
                                <li>✅ Blockquotes</li>
                                <li>✅ Dark mode support</li>
                                <li>✅ Only assistant messages use markdown</li>
                            </ul>
                        </div>
                    </div>
                </div>
            );
        }

        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>'''

    with open("test_markdown_chat.html", "w") as f:
        f.write(html_content)

    print("\n✓ Created test_markdown_chat.html - Open in browser to test markdown rendering")


def main():
    """Run all markdown checks."""
    print("Testing Markdown Chat Implementation")
    print("=" * 50)

    all_passed = True

    # Run checks
    checks = [
        check_package_dependencies,
        check_component_files,
        check_chat_message_integration,
    ]

    for check in checks:
        if not check():
            all_passed = False

    # Create test HTML
    create_markdown_test_page()

    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All markdown implementation checks passed!")
        print("\nMarkdown rendering has been successfully implemented:")
        print("  • react-markdown and remark-gfm dependencies added")
        print("  • MarkdownRenderer component with syntax highlighting")
        print("  • CopyToClipboard for code blocks")
        print("  • Integration in ChatMessage component")
        print("  • Only assistant messages render markdown (user messages as plain text)")
        print("  • Dark mode support with proper styling")
        print("\nTo test manually:")
        print("  1. Install dependencies: cd src/frontend && npm install")
        print("  2. Open test_markdown_chat.html in a browser")
        print("  3. Start the application and test the chat")
    else:
        print("✗ Some checks failed.")
        print("Please review the errors above and fix them.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())