import { useNavigate } from 'react-router-dom'
import {
  SparklesIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  ClockIcon,
  DocumentTextIcon,
  CodeBracketIcon,
} from '@heroicons/react/24/outline'

export function QuickActions() {
  const navigate = useNavigate()

  const actions = [
    {
      title: 'ИИ Ассистент',
      description: 'Генерация тестов с AI',
      icon: SparklesIcon,
      onClick: () => navigate('/chat'),
      color: 'bg-gradient-to-br from-blue-500 to-indigo-600',
    },
    {
      title: 'Анализ покрытия',
      description: 'GitHub/GitLab репозиторий',
      icon: ChartBarIcon,
      onClick: () => navigate('/coverage'),
      color: 'bg-gradient-to-br from-green-500 to-emerald-600',
    },
    {
      title: 'История диалогов',
      description: 'Сохраненные чаты',
      icon: ClockIcon,
      onClick: () => navigate('/history'),
      color: 'bg-gradient-to-br from-purple-500 to-pink-600',
    },
    {
      title: 'Настройки ИИ',
      description: 'Параметры генерации',
      icon: CodeBracketIcon,
      onClick: () => navigate('/settings'),
      color: 'bg-gradient-to-br from-orange-500 to-red-600',
    },
  ]

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <SparklesIcon className="h-6 w-6 text-primary-500 mr-2" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Основные функции
        </h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {actions.map((action) => (
          <button
            key={action.title}
            onClick={action.onClick}
            className="group relative flex flex-col items-start rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-left hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-lg hover:scale-105 transition-all duration-200 overflow-hidden"
          >
            {/* Background gradient on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary-50/50 to-transparent dark:from-primary-900/10 opacity-0 group-hover:opacity-100 transition-opacity" />
            
            <div className="relative z-10 w-full">
              <div className={`${action.color} rounded-lg p-3 w-fit mb-3 shadow-md group-hover:shadow-lg transition-shadow`}>
                <action.icon className="h-6 w-6 text-white" />
              </div>
              <p className="text-base font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                {action.title}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {action.description}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}