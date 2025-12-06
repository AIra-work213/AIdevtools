import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  DocumentTextIcon,
  CodeBracketIcon,
  FolderOpenIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

export function QuickActions() {
  const navigate = useNavigate()

  const actions = [
    {
      title: 'Генерация ручных тестов',
      description: 'Из текстовых требований',
      icon: DocumentTextIcon,
      onClick: () => navigate('/chat'),
      color: 'bg-blue-500',
    },
    {
      title: 'Генерация API тестов',
      description: 'Из OpenAPI спецификации',
      icon: CodeBracketIcon,
      onClick: () => navigate('/chat?type=api'),
      color: 'bg-green-500',
    },
    {
      title: 'Валидация кода',
      description: 'Проверка стандартов',
      icon: ChartBarIcon,
      onClick: () => navigate('/chat?action=validate'),
      color: 'bg-yellow-500',
    },
    {
      title: 'Поиск дубликатов',
      description: 'В существующих тестах',
      icon: FolderOpenIcon,
      onClick: () => navigate('/chat?action=duplicates'),
      color: 'bg-purple-500',
    },
  ]

  return (
    <div className="card">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
        Быстрые действия
      </h3>
      <div className="grid grid-cols-2 gap-4">
        {actions.map((action) => (
          <button
            key={action.title}
            onClick={action.onClick}
            className="flex flex-col items-center justify-center rounded-lg border border-gray-200 p-4 text-center hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:hover:border-gray-600 dark:hover:bg-gray-800 transition-colors"
          >
            <div className={`${action.color} rounded-lg p-2`}>
              <action.icon className="h-6 w-6 text-white" />
            </div>
            <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              {action.title}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {action.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  )
}