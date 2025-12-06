import type { RefObject } from 'react'
import { SparklesIcon } from '@heroicons/react/24/outline'
import { ChatMessage } from './ChatMessage'

interface ChatInterfaceProps {
  messages: any[]
  isLoading: boolean
  messagesEndRef: RefObject<HTMLDivElement>
  onCodeGenerated: (code: string) => void
}

export function ChatInterface({
  messages,
  isLoading,
  messagesEndRef,
  onCodeGenerated,
}: ChatInterfaceProps) {
  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin">
      <div className="space-y-4 p-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <SparklesIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              Начните диалог
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Опишите требования к тестам или загрузите файл с документацией
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onCodeGenerated={onCodeGenerated}
            />
          ))
        )}

        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-primary-100 dark:bg-primary-900/20 flex items-center justify-center">
                <SparklesIcon className="h-4 w-4 text-primary-600 dark:text-primary-400" />
              </div>
            </div>
            <div className="flex-1">
              <div className="chat-message assistant">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-pulse" />
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-pulse delay-75" />
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-pulse delay-150" />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}