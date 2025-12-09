import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import {
  ChatBubbleLeftRightIcon,
  TrashIcon,
  DocumentArrowDownIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline'
import { useHistoryStore } from '@/stores/historyStore'
import { useChatStore } from '@/stores/chatStore'
import { exportChat, downloadFile } from '@/utils/export'
import { toast } from 'react-hot-toast'

export function History() {
  const { chatHistory, deleteChat, exportChat, updateChatTitle } = useHistoryStore()
  const { messages, clearChat } = useChatStore()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')

  const handleLoadChat = (chatId: string) => {
    const chat = chatHistory.find(c => c.id === chatId)
    if (!chat) return

    // Clear current chat and load history
    clearChat()

    // Load messages into chat store
    chat.messages.forEach(msg => {
      useChatStore.getState().appendMessage(msg)
    })

    toast.success('Диалог загружен')
  }

  const handleDeleteChat = (chatId: string, title: string) => {
    if (window.confirm(`Удалить диалог "${title}"?`)) {
      deleteChat(chatId)
      toast.success('Диалог удален')
    }
  }

  const handleExportChat = (chatId: string, title: string, format: 'json' | 'markdown' | 'text' = 'json') => {
    const chat = chatHistory.find(c => c.id === chatId)
    if (!chat) return

    const exportContent = exportChat({
      format,
      title,
      messages: chat.messages,
      metadata: chat.metadata
    })

    const extensions = {
      json: 'json',
      markdown: 'md',
      text: 'txt'
    }

    const mimeTypes = {
      json: 'application/json',
      markdown: 'text/markdown',
      text: 'text/plain'
    }

    const filename = `${title.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.${extensions[format]}`
    downloadFile(exportContent, filename, mimeTypes[format])
    
    toast.success(`Экспортировано как ${format.toUpperCase()}`)
  }

  const handleStartEdit = (chatId: string, currentTitle: string) => {
    setEditingId(chatId)
    setEditingTitle(currentTitle)
  }

  const handleSaveTitle = () => {
    if (editingId && editingTitle.trim()) {
      updateChatTitle(editingId, editingTitle.trim())
      setEditingId(null)
      setEditingTitle('')
      toast.success('Название изменено')
    }
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditingTitle('')
  }

  if (chatHistory.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
          История диалогов
        </h1>
        <div className="card">
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            У вас пока нет сохраненных диалогов
          </p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          История диалогов
        </h1>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Всего диалогов: {chatHistory.length}
        </div>
      </div>

      <div className="space-y-4">
        {chatHistory.map((chat) => (
          <div
            key={chat.id}
            className="card hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => handleLoadChat(chat.id)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {editingId === chat.id ? (
                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSaveTitle()}
                      className="input text-sm"
                      autoFocus
                    />
                    <button
                      onClick={handleSaveTitle}
                      className="text-green-600 hover:text-green-700"
                    >
                      <CheckIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="text-red-600 hover:text-red-700"
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    {chat.title}
                  </h3>
                )}
                <div className="mt-1 flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                  <span className="flex items-center gap-1">
                    <ChatBubbleLeftRightIcon className="h-4 w-4" />
                    {chat.messages.length} сообщений
                  </span>
                  <span>
                    Создан: {format(chat.createdAt, 'dd MMM yyyy, HH:mm', { locale: ru })}
                  </span>
                  {chat.updatedAt.getTime() !== chat.createdAt.getTime() && (
                    <span>
                      Обновлен: {format(chat.updatedAt, 'dd MMM yyyy, HH:mm', { locale: ru })}
                    </span>
                  )}
                </div>
                {chat.metadata?.generationSettings && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                      {chat.metadata.generationSettings.detail_level === 'detailed' ? 'Детально' :
                       chat.metadata.generationSettings.detail_level === 'minimal' ? 'Минимум' : 'Стандарт'}
                    </span>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                      {chat.metadata.generationSettings.framework}
                    </span>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2 ml-4" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => handleStartEdit(chat.id, chat.title)}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Изменить название"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleExportChat(chat.id, chat.title)}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Экспортировать"
                >
                  <DocumentArrowDownIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDeleteChat(chat.id, chat.title)}
                  className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Удалить"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}