import { useState, useRef, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { PaperAirplaneIcon, DocumentIcon, CogIcon } from '@heroicons/react/24/outline'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { CodeEditor } from '@/components/editor/CodeEditor'
import { GenerationSettings } from '@/components/chat/GenerationSettings'
import { useChatStore } from '@/stores/chatStore'
import { toast } from 'react-hot-toast'

const messageSchema = z.object({
  content: z.string().min(1, 'Сообщение не может быть пустым'),
})

type MessageFormData = z.infer<typeof messageSchema>

export function Chat() {
  const [generatedCode, setGeneratedCode] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | undefined>(undefined)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { messages, isLoading, sendMessage, clearChat } = useChatStore()

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
                onClick={() => setShowSettings(!showSettings)}
                className="btn-ghost p-2"
                title="Настройки генерации"
              >
                <CogIcon className="h-5 w-5" />
              </button>
              <button
                onClick={clearChat}
                className="btn-ghost text-sm"
                disabled={messages.length === 0}
              >
                Очистить
              </button>
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
                <input
                  {...register('content')}
                  type="text"
                  placeholder="Введите требования или описание теста..."
                  className="input"
                  disabled={isLoading}
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
      </div>

      {/* Code Editor Section */}
      {generatedCode && (
        <div className="w-1/2">
          <div className="card h-[calc(100vh-10rem)]">
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