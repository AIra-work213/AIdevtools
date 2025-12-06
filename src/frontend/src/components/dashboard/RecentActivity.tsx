import { ClockIcon } from '@heroicons/react/24/outline'

export function RecentActivity() {
  const activities = [
    {
      id: 1,
      description: 'Сгенерированы тесты для модуля авторизации',
      timestamp: '5 минут назад',
      type: 'generation',
    },
    {
      id: 2,
      description: 'Валидация кода: 12 предупреждений исправлено',
      timestamp: '1 час назад',
      type: 'validation',
    },
    {
      id: 3,
      description: 'Создан Merge Request в проект test-automation',
      timestamp: '2 часа назад',
      type: 'gitlab',
    },
    {
      id: 4,
      description: 'Найдено 3 дубликата в тестах',
      timestamp: '3 часа назад',
      type: 'duplicate',
    },
  ]

  return (
    <div className="card">
      <div className="flex items-center">
        <ClockIcon className="h-5 w-5 text-gray-400" />
        <h3 className="ml-2 text-lg font-medium text-gray-900 dark:text-white">
          Последняя активность
        </h3>
      </div>
      <div className="mt-6 flow-root">
        <ul className="-my-5 divide-y divide-gray-200 dark:divide-gray-700">
          {activities.map((activity) => (
            <li key={activity.id} className="py-4">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <div className="h-2 w-2 rounded-full bg-primary-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {activity.description}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {activity.timestamp}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}