import { useNavigate } from 'react-router-dom'
import { useMemo } from 'react'
import {
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  ChartBarIcon,
  SparklesIcon,
  CodeBracketIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline'
import { MetricsCard, type Metric } from '@/components/ui/MetricsCard'
import { RecentActivity } from '@/components/dashboard/RecentActivity'
import { QuickActions } from '@/components/dashboard/QuickActions'
import { useHistoryStore } from '@/stores/historyStore'
import { useChatStore } from '@/stores/chatStore'

export function Dashboard() {
  const navigate = useNavigate()
  const { chatHistory } = useHistoryStore()
  const { messages } = useChatStore()

  // Вычисляем реальную статистику
  const stats = useMemo(() => {
    let totalTests = 0
    let totalValidations = 0
    let totalCodeBlocks = 0

    chatHistory.forEach(chat => {
      chat.messages.forEach(msg => {
        if (msg.type === 'assistant' && msg.metadata) {
          if (msg.metadata.testCases) {
            totalTests += Array.isArray(msg.metadata.testCases) 
              ? msg.metadata.testCases.length 
              : 1
          }
          if (msg.metadata.validation) {
            totalValidations++
          }
          if (msg.metadata.code) {
            totalCodeBlocks++
          }
        }
      })
    })

    // Добавляем текущие сообщения
    messages.forEach(msg => {
      if (msg.type === 'assistant' && msg.metadata) {
        if (msg.metadata.testCases) {
          totalTests += Array.isArray(msg.metadata.testCases) 
            ? msg.metadata.testCases.length 
            : 1
        }
        if (msg.metadata.validation) {
          totalValidations++
        }
        if (msg.metadata.code) {
          totalCodeBlocks++
        }
      }
    })

    return {
      totalTests,
      totalValidations,
      totalCodeBlocks,
      activeSessions: messages.length > 0 ? 1 : 0,
      totalChats: chatHistory.length,
    }
  }, [chatHistory, messages])

  const metrics: Metric[] = [
    {
      title: 'Сгенерировано тестов',
      value: stats.totalTests.toString(),
      change: stats.totalTests > 0 ? `+${stats.totalTests}` : '0',
      changeType: 'increase',
      icon: BeakerIcon,
    },
    {
      title: 'Блоков кода',
      value: stats.totalCodeBlocks.toString(),
      change: stats.totalCodeBlocks > 0 ? `${stats.totalCodeBlocks} шт` : 'Пусто',
      changeType: 'increase',
      icon: CodeBracketIcon,
    },
    {
      title: 'Сохранено диалогов',
      value: stats.totalChats.toString(),
      change: stats.activeSessions > 0 ? 'Активная сессия' : 'Нет активных',
      changeType: stats.activeSessions > 0 ? 'increase' : 'neutral',
      icon: ChatBubbleLeftRightIcon,
    },
    {
      title: 'Валидаций кода',
      value: stats.totalValidations.toString(),
      change: stats.totalValidations > 0 ? `${stats.totalValidations} проверок` : 'Нет данных',
      changeType: 'increase',
      icon: CheckCircleIcon,
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

      {/* Feature Highlights CTA */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* AI Chat CTA */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 p-6 shadow-xl">
          <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
          <div className="relative">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-white/20 rounded-lg backdrop-blur">
                <SparklesIcon className="h-6 w-6 text-white" />
              </div>
              <h3 className="ml-3 text-lg font-semibold text-white">
                Генерация тестов с ИИ
              </h3>
            </div>
            <p className="text-sm text-blue-100 mb-4">
              Создавайте pytest тесты из текстовых требований. Поддержка параметризации, fixtures, Allure отчетов.
            </p>
            <button
              onClick={() => navigate('/chat')}
              className="inline-flex items-center rounded-lg bg-white px-4 py-2 text-sm font-medium text-blue-600 shadow-lg hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600 transition-all"
            >
              <ChatBubbleLeftRightIcon className="mr-2 h-4 w-4" />
              Открыть ИИ ассистента
            </button>
          </div>
        </div>

        {/* Coverage CTA */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 p-6 shadow-xl">
          <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
          <div className="relative">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-white/20 rounded-lg backdrop-blur">
                <ChartBarIcon className="h-6 w-6 text-white" />
              </div>
              <h3 className="ml-3 text-lg font-semibold text-white">
                Анализ покрытия кода
              </h3>
            </div>
            <p className="text-sm text-green-100 mb-4">
              Загрузите GitHub/GitLab репозиторий для анализа покрытия и автоматической генерации тестов для непокрытых функций.
            </p>
            <button
              onClick={() => navigate('/coverage')}
              className="inline-flex items-center rounded-lg bg-white px-4 py-2 text-sm font-medium text-green-600 shadow-lg hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-green-600 transition-all"
            >
              <ChartBarIcon className="mr-2 h-4 w-4" />
              Анализировать проект
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}