#!/usr/bin/env python3
"""
Test different markdown features in the chat interface.
"""

test_markdown_content = """Here's a comprehensive test of markdown features:

# Heading 1
## Heading 2
### Heading 3

**Bold text** and *italic text* and ~~strikethrough~~

### Lists
Unordered list:
- Item 1
- Item 2
  - Nested item 1
  - Nested item 2
- Item 3

Ordered list:
1. First step
2. Second step
3. Third step

### Code Examples
Inline code: `const x = 10`

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

```javascript
function greet(name) {
    return \`Hello, \${name}!\`;
}
```

### Tables
| Feature | Status | Notes |
|---------|--------|-------|
| Headers | ✅ | Support for H1-H6 |
| Code | ✅ | Syntax highlighting |
| Tables | ✅ | Responsive tables |
| Links | ✅ | Auto-linking |

### Blockquotes
> This is a blockquote.
>
> It can span multiple lines.

### Links
- Regular link: https://example.com
- Named link: [OpenAI](https://openai.com)

### Task Lists (GFM)
- [x] Completed task
- [ ] Pending task
- [ ] Another task

### Emojis (if supported)
- Rocket: 🚀
- Check: ✅
- Warning: ⚠️

That's all! This should render properly with all markdown features."""

# Write the test content to a file that can be used for testing
with open("markdown_test_content.txt", "w") as f:
    f.write(test_markdown_content)

print("Created markdown_test_content.txt")
print("\nYou can use this content to test markdown rendering in the chat interface.")