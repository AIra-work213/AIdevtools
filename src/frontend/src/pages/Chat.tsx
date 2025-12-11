import { useState, useRef, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { PaperAirplaneIcon, DocumentIcon, CogIcon, BookmarkIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline'
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


export function Chat() {
  const [generatedCode, setGeneratedCode] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | undefined>(undefined)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [chatTitle, setChatTitle] = useState('')
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
        <div className="w-1/2 flex flex-col gap-4">
          <div className="card flex-1 flex flex-col">
            <CodeEditor
              code={generatedCode}
              language="python"
              title="Сгенерированный код"
            />
          </div>
        </div>
      )}
    </div>
  )
}