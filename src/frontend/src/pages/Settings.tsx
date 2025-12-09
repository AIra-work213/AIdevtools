import { useState } from 'react'
import {
  Cog6ToothIcon,
  MoonIcon,
  SunIcon,
  TrashIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { useSettingsStore, GenerationSettings } from '@/stores/settingsStore'
import { useHistoryStore } from '@/stores/historyStore'
import { useChatStore } from '@/stores/chatStore'
import { toast } from 'react-hot-toast'

export function Settings() {
  const { generationSettings, updateSettings, resetSettings } = useSettingsStore()
  const { chatHistory, clearHistory, exportChat } = useHistoryStore()
  const { clearChat } = useChatStore()
  const [darkMode, setDarkMode] = useState(false)

  const handleExportAllHistory = () => {
    const allData = {
      exportedAt: new Date().toISOString(),
      totalChats: chatHistory.length,
      chats: chatHistory.map(chat => ({
        id: chat.id,
        title: chat.title,
        createdAt: chat.createdAt.toISOString(),
        updatedAt: chat.updatedAt.toISOString(),
        messages: chat.messages.map(msg => ({
          type: msg.type,
          content: msg.content,
          timestamp: msg.timestamp.toISOString(),
          metadata: msg.metadata
        })),
        metadata: chat.metadata
      }))
    }

    const blob = new Blob([JSON.stringify(allData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-history-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast.success('Вся история экспортирована')
  }

  const handleClearAllData = () => {
    if (
      window.confirm(
        'ВНИМАНИЕ: Это действие удалит всю историю диалогов, настройки и текущий чат. Это действие невозможно отменить. Продолжить?'
      )
    ) {
      clearHistory()
      clearChat()
      resetSettings()
      toast.success('Все данные удалены')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
          Настройки
        </h1>
      </div>

      {/* Generation Settings */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Cog6ToothIcon className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">
            Настройки генерации по умолчанию
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Уровень детализации
            </label>
            <select
              className="mt-1 input"
              value={generationSettings.detail_level}
              onChange={(e) => updateSettings({ detail_level: e.target.value })}
            >
              <option value="minimal">Минимальный</option>
              <option value="standard">Стандартный</option>
              <option value="detailed">Детальный</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Температура (креативность)
            </label>
            <div className="mt-1 flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                className="flex-1"
                value={generationSettings.temperature}
                onChange={(e) => updateSettings({ temperature: parseFloat(e.target.value) })}
              />
              <span className="text-sm w-12 text-right">{generationSettings.temperature}</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Максимальное количество токенов
            </label>
            <div className="mt-1 flex items-center gap-2">
              <input
                type="range"
                min="1000"
                max="32000"
                step="1000"
                className="flex-1"
                value={generationSettings.max_tokens}
                onChange={(e) => updateSettings({ max_tokens: parseInt(e.target.value) })}
              />
              <span className="text-sm w-12 text-right">{generationSettings.max_tokens}</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Язык по умолчанию
            </label>
            <select
              className="mt-1 input"
              value={generationSettings.language}
              onChange={(e) => updateSettings({ language: e.target.value })}
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="java">Java</option>
              <option value="csharp">C#</option>
            </select>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              className="form-checkbox"
              checked={generationSettings.use_aaa_pattern}
              onChange={(e) => updateSettings({ use_aaa_pattern: e.target.checked })}
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Использовать AAA паттерн по умолчанию
            </span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              className="form-checkbox"
              checked={generationSettings.include_negative_tests}
              onChange={(e) => updateSettings({ include_negative_tests: e.target.checked })}
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Генерировать негативные тесты по умолчанию
            </span>
          </label>
        </div>
      </div>

      {/* Appearance */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          {darkMode ? <MoonIcon className="h-5 w-5 text-gray-500" /> : <SunIcon className="h-5 w-5 text-gray-500" />}
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">
            Внешний вид
          </h2>
        </div>

        <label className="flex items-center">
          <input
            type="checkbox"
            className="form-checkbox"
            checked={darkMode}
            onChange={(e) => {
              setDarkMode(e.target.checked)
              document.documentElement.classList.toggle('dark', e.target.checked)
            }}
          />
          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
            Темная тема
          </span>
        </label>
      </div>

      {/* Data Management */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <DocumentArrowDownIcon className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">
            Управление данными
          </h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Экспортировать всю историю
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Скачать все диалоги в JSON файл
              </p>
            </div>
            <button
              onClick={handleExportAllHistory}
              disabled={chatHistory.length === 0}
              className="btn-secondary"
            >
              Экспортировать
            </button>
          </div>

          <div className="border-t pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600 dark:text-red-400">
                  Очистить историю
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Удалить все сохраненные диалоги
                </p>
              </div>
              <button
                onClick={() => {
                  if (window.confirm('Удалить всю историю диалогов?')) {
                    clearHistory()
                    toast.success('История очищена')
                  }
                }}
                disabled={chatHistory.length === 0}
                className="btn-secondary text-red-600 border-red-300 hover:bg-red-50 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900/10"
              >
                Очистить
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="card border-red-200 dark:border-red-800">
        <div className="flex items-center gap-2 mb-4">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
          <h2 className="text-lg font-medium text-red-600 dark:text-red-400">
            Опасная зона
          </h2>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              Удалить все данные
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Полностью удалить всю историю, настройки и текущий чат
            </p>
          </div>
          <button
            onClick={handleClearAllData}
            className="btn-primary bg-red-600 hover:bg-red-700 focus:ring-red-500"
          >
            <TrashIcon className="h-4 w-4 mr-2" />
            Удалить всё
          </button>
        </div>
      </div>
    </div>
  )
}