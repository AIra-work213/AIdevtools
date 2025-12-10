import { useState } from 'react'
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon, LightBulbIcon } from '@heroicons/react/24/outline'
import { CodeEditor } from '@/components/editor/CodeEditor'
import { toast } from 'react-hot-toast'

interface ValidationResult {
  is_valid: boolean
  errors: string[]
  warnings: string[]
  suggestions: string[]
  metrics?: {
    total_lines?: number
    code_lines?: number
    comment_lines?: number
    blank_lines?: number
    functions?: number
    classes?: number
    complexity?: number
  }
}

export function Validate() {
  const [code, setCode] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [strictMode, setStrictMode] = useState(false)

  const handleValidate = async () => {
    if (!code.trim()) {
      toast.error('Введите код для валидации')
      return
    }

    setIsValidating(true)
    setValidationResult(null)

    try {
      const response = await fetch('/api/v1/analyze/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          standards: {
            max_line_length: 120,
            require_docstrings: true,
            require_type_hints: strictMode,
          },
          strict_mode: strictMode,
        }),
      })

      if (!response.ok) {
        throw new Error('Ошибка валидации')
      }

      const result = await response.json()
      setValidationResult(result)

      if (result.is_valid) {
        toast.success('Код валиден! ✅')
      } else {
        toast.error(`Найдено ${result.errors.length} ошибок`)
      }
    } catch (error) {
      console.error('Validation error:', error)
      toast.error('Произошла ошибка при валидации')
    } finally {
      setIsValidating(false)
    }
  }

  const handleClear = () => {
    setCode('')
    setValidationResult(null)
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Валидация кода
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Проверьте ваш код на соответствие стандартам и получите рекомендации по улучшению
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Code Editor */}
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Код для проверки
              </h3>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={strictMode}
                  onChange={(e) => setStrictMode(e.target.checked)}
                  className="form-checkbox rounded text-primary-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Строгий режим
                </span>
              </label>
            </div>

            <div className="mb-4 rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" style={{ minHeight: '600px' }}>
              <CodeEditor
                value={code}
                onChange={setCode}
                language="python"
                height="600px"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleValidate}
                disabled={isValidating || !code.trim()}
                className="btn-primary flex-1"
              >
                {isValidating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Проверка...
                  </>
                ) : (
                  <>
                    <CheckCircleIcon className="h-5 w-5 mr-2" />
                    Проверить код
                  </>
                )}
              </button>
              <button
                onClick={handleClear}
                disabled={isValidating}
                className="btn-secondary"
              >
                Очистить
              </button>
            </div>
          </div>
        </div>

        {/* Validation Results */}
        <div className="space-y-4">
          {/* Overall Status */}
          {validationResult && (
            <div className={`card border-2 ${
              validationResult.is_valid 
                ? 'border-green-500 bg-green-50 dark:bg-green-900/10' 
                : 'border-red-500 bg-red-50 dark:bg-red-900/10'
            }`}>
              <div className="flex items-center gap-3">
                {validationResult.is_valid ? (
                  <>
                    <CheckCircleIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
                    <div>
                      <h3 className="text-lg font-semibold text-green-900 dark:text-green-100">
                        Код валиден
                      </h3>
                      <p className="text-sm text-green-700 dark:text-green-300">
                        Критических проблем не обнаружено
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <XCircleIcon className="h-8 w-8 text-red-600 dark:text-red-400" />
                    <div>
                      <h3 className="text-lg font-semibold text-red-900 dark:text-red-100">
                        Обнаружены ошибки
                      </h3>
                      <p className="text-sm text-red-700 dark:text-red-300">
                        Найдено {validationResult.errors.length} ошибок
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Metrics */}
          {validationResult?.metrics && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Метрики кода
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {validationResult.metrics.total_lines && (
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {validationResult.metrics.total_lines}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Всего строк</div>
                  </div>
                )}
                {validationResult.metrics.functions !== undefined && (
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {validationResult.metrics.functions}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Функций</div>
                  </div>
                )}
                {validationResult.metrics.classes !== undefined && (
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {validationResult.metrics.classes}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Классов</div>
                  </div>
                )}
                {validationResult.metrics.complexity !== undefined && (
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {validationResult.metrics.complexity}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Сложность</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Errors */}
          {validationResult && validationResult.errors.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <XCircleIcon className="h-5 w-5 text-red-600" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Ошибки ({validationResult.errors.length})
                </h3>
              </div>
              <ul className="space-y-2">
                {validationResult.errors.map((error, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg"
                  >
                    <span className="text-red-600 dark:text-red-400 mt-0.5">•</span>
                    <span className="text-sm text-red-800 dark:text-red-200 flex-1">
                      {error}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {validationResult && validationResult.warnings.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Предупреждения ({validationResult.warnings.length})
                </h3>
              </div>
              <ul className="space-y-2">
                {validationResult.warnings.map((warning, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg"
                  >
                    <span className="text-yellow-600 dark:text-yellow-400 mt-0.5">•</span>
                    <span className="text-sm text-yellow-800 dark:text-yellow-200 flex-1">
                      {warning}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggestions */}
          {validationResult && validationResult.suggestions.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <LightBulbIcon className="h-5 w-5 text-blue-600" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Рекомендации ({validationResult.suggestions.length})
                </h3>
              </div>
              <ul className="space-y-2">
                {validationResult.suggestions.map((suggestion, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
                  >
                    <span className="text-blue-600 dark:text-blue-400 mt-0.5">💡</span>
                    <span className="text-sm text-blue-800 dark:text-blue-200 flex-1">
                      {suggestion}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Empty State */}
          {!validationResult && (
            <div className="card text-center py-12">
              <CheckCircleIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Готов к проверке
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Введите код и нажмите "Проверить код" для начала валидации
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
