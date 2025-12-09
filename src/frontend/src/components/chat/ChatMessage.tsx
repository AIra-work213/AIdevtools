import { UserCircleIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { MarkdownRenderer } from '@/components/MarkdownRenderer'

interface ChatMessageProps {
  message: {
    id: string
    type: 'user' | 'assistant'
    content: string
    metadata?: {
      code?: string
      validation?: any
    }
  }
  onCodeGenerated?: (code: string) => void
}

export function ChatMessage({ message, onCodeGenerated }: ChatMessageProps) {
  const isUser = message.type === 'user'

  return (
    <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      <div className="flex-shrink-0">
        {isUser ? (
          <UserCircleIcon className="h-8 w-8 text-gray-400" />
        ) : (
          <div className="h-8 w-8 rounded-full bg-primary-100 dark:bg-primary-900/20 flex items-center justify-center">
            <SparklesIcon className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          </div>
        )}
      </div>

      <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
        <div className={`chat-message ${message.type}`}>
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <MarkdownRenderer>{message.content}</MarkdownRenderer>
          )}

          {message.metadata?.code && onCodeGenerated && (
            <div className="mt-3">
              <button
                onClick={() => onCodeGenerated(message.metadata!.code!)}
                className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
              >
                Показать код →
              </button>
            </div>
          )}

          {message.metadata?.validation && (
            <div className="mt-3 rounded bg-gray-50 p-3 dark:bg-gray-900">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Результат валидации:
              </p>
              <div className="mt-1 space-y-1">
                {message.metadata.validation.errors?.length > 0 && (
                  <p className="text-sm text-red-600 dark:text-red-400">
                    {message.metadata.validation.errors.length} ошибок
                  </p>
                )}
                {message.metadata.validation.warnings?.length > 0 && (
                  <p className="text-sm text-yellow-600 dark:text-yellow-400">
                    {message.metadata.validation.warnings.length} предупреждений
                  </p>
                )}
                {message.metadata.validation.is_valid && (
                  <p className="text-sm text-green-600 dark:text-green-400">
                    Код валиден
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}