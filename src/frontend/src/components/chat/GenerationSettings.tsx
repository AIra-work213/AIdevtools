import { XMarkIcon } from '@heroicons/react/24/outline'
import { useSettingsStore } from '@/stores/settingsStore'
import { GenerationSettings } from '@/stores/settingsStore'

interface GenerationSettingsModalProps {
  onClose: () => void
}

export function GenerationSettings({ onClose }: GenerationSettingsModalProps) {
  const { generationSettings, updateSettings, resetSettings } = useSettingsStore()

  const handleInputChange = (field: keyof GenerationSettings, value: any) => {
    updateSettings({ [field]: value })
  }

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
              <select
                className="mt-1 input"
                value={generationSettings.test_type}
                onChange={(e) => handleInputChange('test_type', e.target.value)}
              >
                <option value="manual">Ручные тесты</option>
                <option value="api">API тесты</option>
                <option value="ui">UI/E2E тесты</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Уровень детализации
              </label>
              <select
                className="mt-1 input"
                value={generationSettings.detail_level}
                onChange={(e) => handleInputChange('detail_level', e.target.value)}
              >
                <option value="minimal">Минимальный</option>
                <option value="standard">Стандартный</option>
                <option value="detailed">Детальный</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Использовать AAA паттерн
              </label>
              <div className="mt-2">
                <label className="inline-flex items-center">
                  <input
                    type="checkbox"
                    className="form-checkbox"
                    checked={generationSettings.use_aaa_pattern}
                    onChange={(e) => handleInputChange('use_aaa_pattern', e.target.checked)}
                  />
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
                  <input
                    type="checkbox"
                    className="form-checkbox"
                    checked={generationSettings.include_negative_tests}
                    onChange={(e) => handleInputChange('include_negative_tests', e.target.checked)}
                  />
                  <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                    Включать негативные сценарии
                  </span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Temperature (креативность): {generationSettings.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                className="mt-1 w-full"
                value={generationSettings.temperature}
                onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Точный</span>
                <span>Креативный</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Max Tokens: {generationSettings.max_tokens}
              </label>
              <input
                type="range"
                min="1000"
                max="32000"
                step="1000"
                className="mt-1 w-full"
                value={generationSettings.max_tokens}
                onChange={(e) => handleInputChange('max_tokens', parseInt(e.target.value))}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Язык программирования
              </label>
              <select
                className="mt-1 input"
                value={generationSettings.language}
                onChange={(e) => handleInputChange('language', e.target.value)}
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="java">Java</option>
                <option value="csharp">C#</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Фреймворк
              </label>
              <select
                className="mt-1 input"
                value={generationSettings.framework}
                onChange={(e) => handleInputChange('framework', e.target.value)}
                disabled={generationSettings.language !== 'python'}
              >
                {generationSettings.language === 'python' && (
                  <>
                    <option value="pytest">Pytest</option>
                    <option value="unittest">Unittest</option>
                  </>
                )}
                {generationSettings.language === 'javascript' && (
                  <>
                    <option value="jest">Jest</option>
                    <option value="mocha">Mocha</option>
                  </>
                )}
                {generationSettings.language === 'typescript' && (
                  <>
                    <option value="jest">Jest</option>
                    <option value="vitest">Vitest</option>
                  </>
                )}
                {generationSettings.language === 'java' && (
                  <>
                    <option value="junit">JUnit</option>
                    <option value="testng">TestNG</option>
                  </>
                )}
                {generationSettings.language === 'csharp' && (
                  <>
                    <option value="nunit">NUnit</option>
                    <option value="xunit">xUnit</option>
                  </>
                )}
              </select>
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={() => {
                resetSettings()
                onClose()
              }}
              className="btn-secondary"
            >
              Сбросить
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