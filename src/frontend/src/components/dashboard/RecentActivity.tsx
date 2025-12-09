import { useNavigate } from 'react-router-dom'
import { ClockIcon, ChatBubbleLeftRightIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { useHistoryStore } from '@/stores/historyStore'
import { useChatStore } from '@/stores/chatStore'
import { formatDistanceToNow } from 'date-fns'
import { ru } from 'date-fns/locale'

export function RecentActivity() {
  const navigate = useNavigate()
  const { chatHistory } = useHistoryStore()
  const { messages } = useChatStore()

  // Создаем список активностей из истории чатов
  const activities = chatHistory
    .slice(0, 5)
    .map(chat => ({
      id: chat.id,
      description: chat.title,
      timestamp: formatDistanceToNow(chat.updatedAt, { addSuffix: true, locale: ru }),
      type: 'chat',
      messagesCount: chat.messages.length,
      onClick: () => navigate('/history'),
    }))

  // Если нет истории, показываем текущую активность
  if (activities.length === 0 && messages.length > 0) {
    const assistantMessages = messages.filter(m => m.type === 'assistant')
    activities.push({
      id: 'current',
      description: 'Текущий диалог с ИИ ассистентом',
      timestamp: 'сейчас',
      type: 'current',
      messagesCount: messages.length,
      onClick: () => navigate('/chat'),
    })
  }

  // Fallback если совсем нет активности
  if (activities.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center mb-4">
          <ClockIcon className="h-6 w-6 text-gray-400 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Последняя активность
          </h3>
        </div>
        <div className="text-center py-12">
          <SparklesIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h4 className="mt-4 text-sm font-medium text-gray-900 dark:text-white">
            Нет активности
          </h4>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Начните работу с ИИ ассистентом для генерации тестов
          </p>
          <button
            onClick={() => navigate('/chat')}
            className="mt-6 btn-primary"
          >
            <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2" />
            Начать диалог
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <ClockIcon className="h-6 w-6 text-primary-500 mr-2" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Последняя активность
        </h3>
      </div>
      <div className="space-y-4">
        {activities.map((activity) => (
          <button
            key={activity.id}
            onClick={activity.onClick}
            className="w-full group flex items-start space-x-4 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
          >
            <div className="flex-shrink-0 mt-1">
              <div className="h-10 w-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center group-hover:bg-primary-200 dark:group-hover:bg-primary-900/50 transition-colors">
                <ChatBubbleLeftRightIcon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                {activity.description}
              </p>
              <div className="mt-1 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                <span>{activity.timestamp}</span>
                <span>•</span>
                <span>{activity.messagesCount} сообщений</span>
              </div>
            </div>
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </div>
          </button>
        ))}
      </div>
      {chatHistory.length > 5 && (
        <button
          onClick={() => navigate('/history')}
          className="mt-4 w-full text-center text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
        >
          Показать все ({chatHistory.length})
        </button>
      )}
    </div>
  )
}