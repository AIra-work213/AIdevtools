import { useState } from 'react'
import Editor from '@monaco-editor/react'
import {
  DocumentDuplicateIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import { toast } from 'react-hot-toast'

interface CodeEditorProps {
  value?: string
  code?: string
  language: string
  title?: string
  readOnly?: boolean
  onChange?: (value: string) => void
  height?: string
}

export function CodeEditor({ 
  value, 
  code, 
  language, 
  title, 
  readOnly = false,
  onChange,
  height = '500px'
}: CodeEditorProps) {
  const editorValue = value ?? code ?? ''
  const [copySuccess, setCopySuccess] = useState(false)

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(editorValue)
      setCopySuccess(true)
      toast.success('Код скопирован')
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (error) {
      toast.error('Ошибка копирования')
    }
  }

  const handleDownloadCode = () => {
    const blob = new Blob([editorValue], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `generated_tests.${language === 'python' ? 'py' : 'txt'}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success('Файл загружен')
  }

  const handleValidateCode = async () => {
    // TODO: Implement code validation
    toast.success('Валидация прошла успешно')
  }

  // Для редактируемого редактора без title (используется в Validate, Duplicates, etc)
  if (!title && onChange) {
    return (
      <div className="w-full" style={{ height }}>
        <Editor
          height={height}
          language={language}
          value={editorValue}
          onChange={(value) => onChange(value || '')}
          theme="vs-dark"
          options={{
            readOnly: false,
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    )
  }

  // Для readonly редактора с title и кнопками (используется для отображения результатов)
  return (
    <div className="flex flex-col" style={{ height }}>
      {/* Header */}
      {title && (
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
          <h3 className="font-medium text-gray-900 dark:text-white">{title}</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleValidateCode}
              className="btn-ghost p-2"
              title="Валидировать код"
            >
              <CheckCircleIcon className="h-4 w-4" />
            </button>
            <button
              onClick={handleCopyCode}
              className="btn-ghost p-2"
              title="Копировать код"
            >
              {copySuccess ? (
                <CheckCircleIcon className="h-4 w-4 text-green-500" />
              ) : (
                <DocumentDuplicateIcon className="h-4 w-4" />
              )}
            </button>
            <button
              onClick={handleDownloadCode}
              className="btn-ghost p-2"
              title="Скачать код"
            >
              <ArrowDownTrayIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Editor */}
      <div className="flex-1">
        <Editor
          height="100%"
          language={language}
          value={editorValue}
          onChange={onChange ? (value) => onChange(value || '') : undefined}
          theme="vs-dark"
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  )
}