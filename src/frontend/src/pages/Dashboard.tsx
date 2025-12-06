import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import { MetricsCard } from '@/components/ui/MetricsCard'
import { RecentActivity } from '@/components/dashboard/RecentActivity'
import { QuickActions } from '@/components/dashboard/QuickActions'

export function Dashboard() {
  const navigate = useNavigate()

  const metrics = [
    {
      title: 'Сгенерировано тестов',
      value: '147',
      change: '+12',
      changeType: 'increase',
      icon: DocumentTextIcon,
    },
    {
      title: 'Валидаций кода',
      value: '89',
      change: '+5',
      changeType: 'increase',
      icon: CheckCircleIcon,
    },
    {
      title: 'Активных чатов',
      value: '3',
      change: '-1',
      changeType: 'decrease',
      icon: ChatBubbleLeftRightIcon,
    },
    {
      title: 'Сохранено в GitLab',
      value: '52',
      change: '+8',
      changeType: 'increase',
      icon: ClockIcon,
    },
  ]

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Добро пожаловать в TestOps Copilot!
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Интеллектуальный ассистент для автоматизации QA процессов
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <MetricsCard key={metric.title} metric={metric} />
        ))}
      </div>

      {/* Quick Actions and Activity */}
      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <QuickActions />
        <RecentActivity />
      </div>

      {/* CTA */}
      <div className="mt-8 rounded-lg bg-primary-50 p-6 dark:bg-primary-900/20">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-primary-900 dark:text-primary-100">
              Начните генерировать тесты прямо сейчас
            </h3>
            <p className="mt-1 text-sm text-primary-700 dark:text-primary-300">
              Используйте ИИ для создания тестов из текстовых требований или API спецификаций
            </p>
          </div>
          <div className="ml-4">
            <button
              onClick={() => navigate('/chat')}
              className="inline-flex items-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              <ChatBubbleLeftRightIcon className="mr-2 h-4 w-4" />
              Открыть чат
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}