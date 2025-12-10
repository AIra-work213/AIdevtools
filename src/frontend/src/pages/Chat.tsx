import { useState, useRef, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { PaperAirplaneIcon, DocumentIcon, CogIcon, BookmarkIcon, ClipboardDocumentIcon, PlayIcon } from '@heroicons/react/24/outline'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { CodeEditor } from '@/components/editor/CodeEditor'
import { GenerationSettings } from '@/components/chat/GenerationSettings'
import { useChatStore } from '@/stores/chatStore'
import { useHistoryStore } from '@/stores/historyStore'
import { useAutoSave } from '@/hooks/useAutoSave'
import { useCopyToClipboard } from '@/hooks/useCopyToClipboard'
import { useHotkeys } from '@/hooks/useHotkeys'
import { toast } from 'react-hot-toast'

const messageSchema = z.object({
  content: z.string().min(1, 'Сообщение не может быть пустым'),
})

type MessageFormData = z.infer<typeof messageSchema>

interface ExecutionResult {
  is_valid: boolean
  can_execute: boolean
  syntax_errors: string[]
  runtime_errors: string[]
  execution_output: string | null
  execution_time: number | null
  allure_report_path: string | null
  allure_results: {
    total_tests: number
    passed: number
    failed: number
    broken: number
    skipped: number
    tests: Array<{
      name: string
      status: string
      duration: number
      fullName: string
    }>
  } | null
}

export function Chat() {
  const [generatedCode, setGeneratedCode] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | undefined>(undefined)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [chatTitle, setChatTitle] = useState('')
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { messages, isLoading, sendMessage, clearChat, currentResponse, generationProgress } = useChatStore()
  const { saveChat } = useHistoryStore()
  const { isSaved } = useAutoSave(30000) // Auto-save every 30 seconds
  const { copyToClipboard } = useCopyToClipboard()

  // Hotkeys
  useHotkeys([
    {
      key: 'k',
      ctrl: true,
      callback: () => clearChat(),
    },
    {
      key: 's',
      ctrl: true,
      callback: () => setShowSaveDialog(true),
    },
    {
      key: ',',
      ctrl: true,
      callback: () => setShowSettings(true),
    },
    {
      key: 'c',
      ctrl: true,
      shift: true,
      callback: () => currentResponse && copyToClipboard(currentResponse, 'Код скопирован'),
    },
  ])

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MessageFormData>({
    resolver: zodResolver(messageSchema),
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Update generated code when current response changes
  useEffect(() => {
    if (currentResponse) {
      setGeneratedCode(currentResponse)
    }
  }, [currentResponse])

  const onSubmit = async (data: MessageFormData) => {
    try {
      await sendMessage(data.content, selectedFile ?? undefined)
      reset()
      setSelectedFile(undefined)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      toast.error('Ошибка отправки сообщения')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(onSubmit)()
    }
    // Allow Shift+Enter for new line (default behavior)
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Check file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        toast.error('Размер файла не должен превышать 10MB')
        return
      }

      // Check file type
      const allowedTypes = ['.txt', '.py', '.yaml', '.yml', '.json']
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()

      if (!allowedTypes.includes(fileExtension)) {
        toast.error('Неподдерживаемый тип файла')
        return
      }

      setSelectedFile(file)
    }
  }

  const handleClearFile = () => {
    setSelectedFile(undefined)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSaveChat = () => {
    if (!chatTitle.trim()) {
      toast.error('Введите название диалога')
      return
    }

    if (messages.length === 0) {
      toast.error('Нет сообщений для сохранения')
      return
    }

    const metadata = {
      code: generatedCode,
      generationSettings: messages.find(m => m.metadata?.generationSettings)?.metadata?.generationSettings
    }

    saveChat(chatTitle.trim(), messages, metadata)
    setShowSaveDialog(false)
    setChatTitle('')
    toast.success('Диалог сохранен')
  }

  const handleExecuteCode = async () => {
    if (!generatedCode.trim()) {
      toast.error('Нет кода для выполнения')
      return
    }

    setIsExecuting(true)
    setExecutionResult(null)

    try {
      // Detect if code has Allure decorators
      const hasAllure = generatedCode.includes('@allure') || generatedCode.includes('import allure')

      const response = await fetch('/api/v1/generate/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: generatedCode,
          source_code: null,
          timeout: 30,  // Longer timeout for pytest
          run_with_pytest: hasAllure,  // Auto-enable pytest if Allure detected
        }),
      })

      if (!response.ok) {
        throw new Error('Ошибка выполнения кода')
      }

      const result = await response.json()
      setExecutionResult(result)

      // Enhanced toast notifications
      if (result.can_execute) {
        if (result.allure_results) {
          const { passed, failed, total_tests } = result.allure_results
          toast.success(`✅ Тесты выполнены: ${passed}/${total_tests} пройдено (${result.execution_time?.toFixed(2)}с)`)
        } else {
          toast.success(`✅ Код выполнен успешно за ${result.execution_time?.toFixed(2)}с`)
        }
      } else if (result.syntax_errors.length > 0) {
        toast.error('❌ Синтаксические ошибки в коде')
      } else {
        toast.error('❌ Ошибки выполнения')
      }
    } catch (error) {
      console.error('Execution error:', error)
      toast.error('Произошла ошибка при выполнении кода')
    } finally {
      setIsExecuting(false)
    }
  }
    }
  }

  return (
    <div className="flex h-full gap-6">
      {/* Chat Section */}
      <div className="flex-1">
        <div className="card h-[calc(100vh-10rem)] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-200 pb-4 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Чат с ассистентом
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowSaveDialog(true)}
                className="btn-ghost p-2"
                title="Сохранить диалог (Ctrl+S)"
                disabled={messages.length === 0}
              >
                <BookmarkIcon className="h-5 w-5" />
              </button>
              <button
                onClick={() => currentResponse && copyToClipboard(currentResponse, 'Код скопирован')}
                className="btn-ghost p-2"
                title="Копировать код (Ctrl+Shift+C)"
                disabled={!currentResponse}
              >
                <ClipboardDocumentIcon className="h-5 w-5" />
              </button>
              <button
                onClick={handleExecuteCode}
                className="btn-ghost p-2"
                title="Запустить код"
                disabled={!generatedCode || isExecuting}
              >
                {isExecuting ? (
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"></div>
                ) : (
                  <PlayIcon className="h-5 w-5" />
                )}
              </button>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="btn-ghost p-2"
                title="Настройки генерации (Ctrl+,)"
              >
                <CogIcon className="h-5 w-5" />
              </button>
              <button
                onClick={clearChat}
                className="btn-ghost text-sm"
                disabled={messages.length === 0}
                title="Очистить чат (Ctrl+K)"
              >
                Очистить
              </button>
              {!isSaved && messages.length > 0 && (
                <span className="text-xs text-yellow-600 dark:text-yellow-400">
                  • Несохраненные изменения
                </span>
              )}
            </div>
          </div>

          {/* Messages */}
          <ChatInterface
            messages={messages}
            isLoading={isLoading}
            messagesEndRef={messagesEndRef}
            onCodeGenerated={setGeneratedCode}
          />

          {/* Input Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-3">
            {/* Progress Bar for Streaming */}
            {isLoading && generationProgress > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">
                    Генерация тестов...
                  </span>
                  <span className="text-primary-600 dark:text-primary-400 font-medium">
                    {generationProgress}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-primary-500 to-fuchsia-500 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${generationProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* File Upload */}
            {selectedFile && (
              <div className="flex items-center gap-2 rounded-lg bg-gray-50 p-2 dark:bg-gray-800">
                <DocumentIcon className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {selectedFile.name}
                </span>
                <button
                  type="button"
                  onClick={handleClearFile}
                  className="ml-auto text-gray-400 hover:text-gray-500"
                >
                  ×
                </button>
              </div>
            )}

            <div className="flex gap-2">
              <div className="flex-1">
                <textarea
                  {...register('content')}
                  placeholder="Введите требования или описание теста... (Shift+Enter для новой строки)"
                  className="input resize-none"
                  disabled={isLoading}
                  rows={1}
                  onKeyDown={handleKeyDown}
                  onInput={(e) => {
                    // Auto-resize textarea
                    const target = e.target as HTMLTextAreaElement
                    target.style.height = 'auto'
                    target.style.height = Math.min(target.scrollHeight, 200) + 'px'
                  }}
                  style={{ minHeight: '42px', maxHeight: '200px' }}
                />
                {errors.content && (
                  <p className="mt-1 text-sm text-red-500">{errors.content.message}</p>
                )}
              </div>

              {/* File Input */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.py,.yaml,.yml,.json"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="btn-ghost cursor-pointer px-3"
                title="Прикрепить файл"
              >
                <DocumentIcon className="h-5 w-5" />
              </label>

              {/* Send Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary"
                aria-label="Отправить"
                title="Отправить"
              >
                <PaperAirplaneIcon className="h-4 w-4" />
              </button>
            </div>
          </form>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <GenerationSettings onClose={() => setShowSettings(false)} />
        )}

        {/* Save Dialog Modal */}
        {showSaveDialog && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex min-h-screen items-center justify-center p-4">
              <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowSaveDialog(false)} />

              <div className="relative w-full max-w-md transform rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Сохранить диалог
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Название диалога
                    </label>
                    <input
                      type="text"
                      value={chatTitle}
                      onChange={(e) => setChatTitle(e.target.value)}
                      placeholder="Введите название..."
                      className="mt-1 input"
                      autoFocus
                      onKeyPress={(e) => e.key === 'Enter' && handleSaveChat()}
                    />
                  </div>

                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Сообщений в диалоге: {messages.length}
                  </div>
                </div>

                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      setShowSaveDialog(false)
                      setChatTitle('')
                    }}
                    className="btn-secondary"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleSaveChat}
                    disabled={!chatTitle.trim()}
                    className="btn-primary"
                  >
                    Сохранить
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Code Editor Section */}
      {generatedCode && (
        <div className="w-1/2">
          <div className="card h-[calc(100vh-10rem)] flex flex-col">
            <CodeEditor
              code={generatedCode}
              language="python"
              title="Сгенерированный код"
            />
            
            {/* Execution Results */}
            {executionResult && (
              <div className="mt-4 border-t border-gray-200 pt-4 dark:border-gray-700">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                    Результаты выполнения
                  </h3>
                  <button
                    onClick={() => setExecutionResult(null)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                    title="Закрыть"
                  >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Status Badge */}
                <div className="mb-3">
                  {executionResult.is_valid && executionResult.can_execute ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
                      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Успешно выполнено
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800 dark:bg-red-900 dark:text-red-200">
                      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      Ошибка выполнения
                    </span>
                  )}
                  {executionResult.execution_time && (
                    <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                      ({executionResult.execution_time.toFixed(3)}s)
                    </span>
                  )}
                </div>

                {/* Syntax Errors */}
                {executionResult.syntax_errors && executionResult.syntax_errors.length > 0 && (
                  <div className="mb-3">
                    <h4 className="text-xs font-semibold text-red-600 dark:text-red-400 mb-2">
                      Синтаксические ошибки:
                    </h4>
                    <div className="max-h-32 overflow-y-auto rounded bg-red-50 p-3 text-xs font-mono text-red-900 dark:bg-red-900/20 dark:text-red-200">
                      {executionResult.syntax_errors.map((error, idx) => (
                        <div key={idx} className="mb-1">{error}</div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Runtime Errors */}
                {executionResult.runtime_errors && executionResult.runtime_errors.length > 0 && (
                  <div className="mb-3">
                    <h4 className="text-xs font-semibold text-red-600 dark:text-red-400 mb-2">
                      Ошибки выполнения:
                    </h4>
                    <div className="max-h-32 overflow-y-auto rounded bg-red-50 p-3 text-xs font-mono text-red-900 dark:bg-red-900/20 dark:text-red-200">
                      {executionResult.runtime_errors.map((error, idx) => (
                        <div key={idx} className="mb-1">{error}</div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Output */}
                {executionResult.execution_output && (
                  <div className="mb-3">
                    <h4 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Вывод:
                    </h4>
                    <div className="max-h-48 overflow-y-auto rounded bg-gray-900 p-3 text-xs font-mono text-green-400">
                      <pre className="whitespace-pre-wrap">{executionResult.execution_output}</pre>
                    </div>
                  </div>
                )}

                {/* Allure Report Results */}
                {executionResult.allure_results && (
                  <div className="mt-4 border-t border-gray-200 pt-4 dark:border-gray-700">
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <svg className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Отчет Allure
                    </h4>
                    
                    {/* Test Summary */}
                    <div className="grid grid-cols-5 gap-2 mb-3">
                      <div className="rounded bg-gray-100 p-2 text-center dark:bg-gray-700">
                        <div className="text-xs text-gray-600 dark:text-gray-400">Всего</div>
                        <div className="text-lg font-bold text-gray-900 dark:text-white">
                          {executionResult.allure_results.total_tests}
                        </div>
                      </div>
                      <div className="rounded bg-green-100 p-2 text-center dark:bg-green-900/30">
                        <div className="text-xs text-green-700 dark:text-green-400">Пройдено</div>
                        <div className="text-lg font-bold text-green-800 dark:text-green-300">
                          {executionResult.allure_results.passed}
                        </div>
                      </div>
                      <div className="rounded bg-red-100 p-2 text-center dark:bg-red-900/30">
                        <div className="text-xs text-red-700 dark:text-red-400">Провалено</div>
                        <div className="text-lg font-bold text-red-800 dark:text-red-300">
                          {executionResult.allure_results.failed}
                        </div>
                      </div>
                      <div className="rounded bg-orange-100 p-2 text-center dark:bg-orange-900/30">
                        <div className="text-xs text-orange-700 dark:text-orange-400">Сломано</div>
                        <div className="text-lg font-bold text-orange-800 dark:text-orange-300">
                          {executionResult.allure_results.broken}
                        </div>
                      </div>
                      <div className="rounded bg-gray-100 p-2 text-center dark:bg-gray-700">
                        <div className="text-xs text-gray-600 dark:text-gray-400">Пропущено</div>
                        <div className="text-lg font-bold text-gray-900 dark:text-white">
                          {executionResult.allure_results.skipped}
                        </div>
                      </div>
                    </div>

                    {/* Individual Test Results */}
                    {executionResult.allure_results.tests.length > 0 && (
                      <div>
                        <h5 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                          Результаты тестов:
                        </h5>
                        <div className="max-h-48 overflow-y-auto space-y-2">
                          {executionResult.allure_results.tests.map((test, idx) => (
                            <div
                              key={idx}
                              className={`rounded p-2 text-xs ${
                                test.status === 'passed'
                                  ? 'bg-green-50 dark:bg-green-900/20'
                                  : test.status === 'failed'
                                  ? 'bg-red-50 dark:bg-red-900/20'
                                  : test.status === 'broken'
                                  ? 'bg-orange-50 dark:bg-orange-900/20'
                                  : 'bg-gray-50 dark:bg-gray-700'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-medium text-gray-900 dark:text-white">
                                  {test.name}
                                </span>
                                <span className={`font-semibold ${
                                  test.status === 'passed' ? 'text-green-700 dark:text-green-400' :
                                  test.status === 'failed' ? 'text-red-700 dark:text-red-400' :
                                  test.status === 'broken' ? 'text-orange-700 dark:text-orange-400' :
                                  'text-gray-600 dark:text-gray-400'
                                }`}>
                                  {test.status.toUpperCase()}
                                </span>
                              </div>
                              <div className="text-gray-600 dark:text-gray-400">
                                Длительность: {(test.duration / 1000).toFixed(2)}s
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Allure Report Path */}
                    {executionResult.allure_report_path && (
                      <div className="mt-3 rounded bg-blue-50 p-2 text-xs text-blue-800 dark:bg-blue-900/20 dark:text-blue-300">
                        <strong>Путь к отчету:</strong> {executionResult.allure_report_path}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}