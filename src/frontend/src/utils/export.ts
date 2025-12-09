import { ChatMessage } from '@/stores/chatStore'

interface ExportOptions {
  format: 'json' | 'markdown' | 'text'
  title: string
  messages: ChatMessage[]
  metadata?: any
}

export function exportChat({ format, title, messages, metadata }: ExportOptions): string {
  switch (format) {
    case 'json':
      return exportAsJSON(title, messages, metadata)
    case 'markdown':
      return exportAsMarkdown(title, messages)
    case 'text':
      return exportAsText(title, messages)
    default:
      return exportAsJSON(title, messages, metadata)
  }
}

function exportAsJSON(title: string, messages: ChatMessage[], metadata?: any): string {
  return JSON.stringify(
    {
      title,
      exportedAt: new Date().toISOString(),
      messagesCount: messages.length,
      messages: messages.map((msg) => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp,
        metadata: msg.metadata,
      })),
      metadata,
    },
    null,
    2
  )
}

function exportAsMarkdown(title: string, messages: ChatMessage[]): string {
  let markdown = `# ${title}\n\n`
  markdown += `*Exported: ${new Date().toLocaleString('ru-RU')}*\n\n`
  markdown += `---\n\n`

  messages.forEach((msg) => {
    const role = msg.type === 'user' ? '👤 User' : '🤖 Assistant'
    markdown += `## ${role}\n\n`
    markdown += `${msg.content}\n\n`

    if (msg.metadata?.code) {
      markdown += '```python\n'
      markdown += msg.metadata.code
      markdown += '\n```\n\n'
    }

    if (msg.metadata?.testCases && msg.metadata.testCases.length > 0) {
      markdown += `### Test Cases (${msg.metadata.testCases.length})\n\n`
      msg.metadata.testCases.forEach((tc: any, idx: number) => {
        markdown += `${idx + 1}. **${tc.title}** (${tc.priority})\n`
        markdown += `   - ${tc.description || 'No description'}\n\n`
      })
    }

    markdown += `---\n\n`
  })

  return markdown
}

function exportAsText(title: string, messages: ChatMessage[]): string {
  let text = `${title}\n`
  text += `${'='.repeat(title.length)}\n\n`
  text += `Exported: ${new Date().toLocaleString('ru-RU')}\n\n`
  text += `${'='.repeat(50)}\n\n`

  messages.forEach((msg, idx) => {
    const role = msg.type === 'user' ? 'USER' : 'ASSISTANT'
    text += `[${idx + 1}] ${role}:\n`
    text += `${msg.content}\n\n`

    if (msg.metadata?.code) {
      text += 'Generated Code:\n'
      text += `${'-'.repeat(40)}\n`
      text += `${msg.metadata.code}\n`
      text += `${'-'.repeat(40)}\n\n`
    }

    text += `\n`
  })

  return text
}

export function downloadFile(content: string, filename: string, mimeType: string = 'text/plain') {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
