import React from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'

interface GenerationSettingsProps {
  onClose: () => void
}

export function GenerationSettings({ onClose }: GenerationSettingsProps) {
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose} />

        <div className="relative w-full max-w-md transform rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>

          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Настройки генерации
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Тип тестов
              </label>
              <select className="mt-1 input">
                <option>Ручные тесты</option>
                <option>API тесты</option>
                <option>UI/E2E тесты</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Уровень детализации
              </label>
              <select className="mt-1 input">
                <option>Минимальный</option>
                <option>Стандартный</option>
                <option>Детальный</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Использовать AAA паттерн
              </label>
              <div className="mt-2">
                <label className="inline-flex items-center">
                  <input type="checkbox" className="form-checkbox" defaultChecked />
                  <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                    Apply (Arrange) - Act - Assert
                  </span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Генерировать негативные тесты
              </label>
              <div className="mt-2">
                <label className="inline-flex items-center">
                  <input type="checkbox" className="form-checkbox" defaultChecked />
                  <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                    Включать негативные сценарии
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button onClick={onClose} className="btn-secondary">
              Отмена
            </button>
            <button onClick={onClose} className="btn-primary">
              Применить
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}