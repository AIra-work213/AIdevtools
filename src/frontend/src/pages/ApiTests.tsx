import { useState } from 'react'
import { CodeBracketIcon, DocumentArrowUpIcon, CheckCircleIcon, PlayIcon } from '@heroicons/react/24/outline'
import { CodeEditor } from '@/components/editor/CodeEditor'
import { toast } from 'react-hot-toast'

interface ExecutionResult {
  is_valid: boolean
  can_execute: boolean
  syntax_errors: string[]
  runtime_errors: string[]
  execution_output: string | null
  execution_time: number | null
  allure_report_path: string | null
  allure_results: {
    total_tests: number
    passed: number
    failed: number
    broken: number
    skipped: number
    tests: Array<{
      name: string
      status: string
      duration: number
      fullName: string
    }>
  } | null
}

interface ApiTestResponse {
  code: string
  endpoints_covered: string[]
  test_matrix: Record<string, string[]>
  coverage_percentage: number
  validation: {
    is_valid: boolean
    errors: string[]
    warnings: string[]
    suggestions: string[]
  }
}

export function ApiTests() {
  const [openApiSpec, setOpenApiSpec] = useState('')
  const [sourceCode, setSourceCode] = useState('')
  const [endpointFilter] = useState<string[]>([])
  const [testTypes, setTestTypes] = useState<string[]>(['positive', 'negative', 'boundary'])
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<ApiTestResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        setOpenApiSpec(content)
        toast.success(`Файл ${file.name} загружен`)
      }
      reader.readAsText(file)
    }
  }

  const handleGenerate = async () => {
    if (!openApiSpec.trim()) {
      toast.error('Введите OpenAPI спецификацию')
      return
    }

    setIsGenerating(true)
    setResult(null)

    try {
      // Parse OpenAPI to validate JSON format
      try {
        JSON.parse(openApiSpec)
      } catch {
        // Try YAML parsing (simplified)
        toast.error('Пока поддерживается только JSON формат OpenAPI')
        return
      }

      const response = await fetch('/api/v1/generate/auto/api', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          openapi_spec: openApiSpec,
          endpoint_filter: endpointFilter.length > 0 ? endpointFilter : null,
          test_types: testTypes,
        }),
      })

      if (!response.ok) {
        throw new Error('Ошибка генерации тестов')
      }

      const data = await response.json()
      setResult(data)
      toast.success(`Сгенерировано тестов для ${data.endpoints_covered.length} endpoints`)
    } catch (error) {
      console.error('API test generation error:', error)
      toast.error('Произошла ошибка при генерации тестов')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleExecute = async () => {
    if (!result?.code) {
      toast.error('Нет кода для выполнения')
      return
    }

    setIsExecuting(true)
    setExecutionResult(null)

    try {
      const hasAllure = result.code.includes('@allure') || result.code.includes('import allure')

      const response = await fetch('/api/v1/generate/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: result.code,
          source_code: sourceCode.trim() || null,
          timeout: 30,
          run_with_pytest: hasAllure,
        }),
      })

      if (!response.ok) {
        throw new Error('Ошибка выполнения кода')
      }

      const execResult = await response.json()
      setExecutionResult(execResult)

      if (execResult.can_execute) {
        if (execResult.allure_results) {
          const { passed, total_tests } = execResult.allure_results
          toast.success(`✅ Тесты выполнены: ${passed}/${total_tests} пройдено`)
        } else {
          toast.success(`✅ Код выполнен успешно`)
        }
      } else {
        toast.error('❌ Ошибки выполнения')
      }
    } catch (error) {
      console.error('Execution error:', error)
      toast.error('Произошла ошибка при выполнении кода')
    } finally {
      setIsExecuting(false)
    }
  }

  const handleDownload = () => {
    if (!result?.code) return

    const blob = new Blob([result.code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'api_tests.py'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success('Тесты скачаны')
  }

  const availableTestTypes = [
    { value: 'positive', label: 'Позитивные тесты' },
    { value: 'negative', label: 'Негативные тесты' },
    { value: 'boundary', label: 'Граничные значения' },
    { value: 'security', label: 'Безопасность' },
    { value: 'performance', label: 'Производительность' },
  ]

  const toggleTestType = (type: string) => {
    setTestTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Генерация API тестов
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Автоматическая генерация тестов из OpenAPI спецификации
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              OpenAPI спецификация
            </h3>

            {/* File Upload */}
            <div className="mb-4">
              <label className="block">
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-primary-500 dark:hover:border-primary-400 transition-colors cursor-pointer">
                  <DocumentArrowUpIcon className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500 mb-2" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedFile ? selectedFile.name : 'Загрузите OpenAPI файл (JSON/YAML)'}
                  </p>
                  <input
                    type="file"
                    accept=".json,.yaml,.yml"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>
              </label>
            </div>

            {/* Spec Editor */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Или вставьте спецификацию:
              </label>
              <div className="rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" style={{ minHeight: '300px' }}>
                <CodeEditor
                  value={openApiSpec}
                  onChange={setOpenApiSpec}
                  language="json"
                  height="300px"
                />
              </div>
            </div>

            {/* Test Types Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Типы тестов:
              </label>
              <div className="space-y-2">
                {availableTestTypes.map((type) => (
                  <label key={type.value} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={testTypes.includes(type.value)}
                      onChange={() => toggleTestType(type.value)}
                      className="form-checkbox rounded text-primary-600"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {type.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Source Code Input */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Исходный код (опционально):
              </label>
              <textarea
                value={sourceCode}
                onChange={(e) => setSourceCode(e.target.value)}
                placeholder="Вставьте код API, который будет тестироваться (классы, функции, эндпоинты)..."
                className="w-full h-32 p-3 text-sm font-mono rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-vertical focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                💡 Добавьте FastAPI/Flask роутеры, модели или другой код для улучшения генерации тестов
              </p>
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !openApiSpec.trim()}
              className="btn-primary w-full"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Генерация...
                </>
              ) : (
                <>
                  <CodeBracketIcon className="h-5 w-5 mr-2" />
                  Сгенерировать тесты
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {result ? (
            <>
              {/* Summary */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    Результаты генерации
                  </h3>
                  <button
                    onClick={handleExecute}
                    disabled={isExecuting}
                    className="btn-primary flex items-center gap-2"
                  >
                    {isExecuting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                        Выполнение...
                      </>
                    ) : (
                      <>
                        <PlayIcon className="h-5 w-5" />
                        Запустить тесты
                      </>
                    )}
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                    <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
                      Endpoints
                    </div>
                    <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                      {result.endpoints_covered.length}
                    </div>
                  </div>

                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                    <div className="text-sm text-green-600 dark:text-green-400 mb-1">
                      Покрытие
                    </div>
                    <div className="text-2xl font-bold text-green-900 dark:text-green-100">
                      {result.coverage_percentage.toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* Endpoints List */}
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Покрытые endpoints:
                  </h4>
                  <div className="space-y-1 max-h-40 overflow-y-auto">
                    {result.endpoints_covered.map((endpoint, idx) => (
                      <div
                        key={idx}
                        className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2"
                      >
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                        <code className="text-xs">{endpoint}</code>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Validation Status */}
                {result.validation && (
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <div
                      className={`flex items-center gap-2 ${
                        result.validation.is_valid
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      <CheckCircleIcon className="h-5 w-5" />
                      <span className="font-medium">
                        {result.validation.is_valid ? 'Код валиден' : 'Найдены ошибки'}
                      </span>
                    </div>

                    {result.validation.errors.length > 0 && (
                      <div className="mt-2 text-sm text-red-600 dark:text-red-400">
                        <div className="font-medium mb-1">Ошибки:</div>
                        <ul className="list-disc list-inside">
                          {result.validation.errors.map((error, idx) => (
                            <li key={idx}>{error}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {result.validation.warnings.length > 0 && (
                      <div className="mt-2 text-sm text-yellow-600 dark:text-yellow-400">
                        <div className="font-medium mb-1">Предупреждения:</div>
                        <ul className="list-disc list-inside">
                          {result.validation.warnings.map((warning, idx) => (
                            <li key={idx}>{warning}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Generated Code */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    Сгенерированный код
                  </h3>
                  <button onClick={handleDownload} className="btn-secondary text-sm">
                    Скачать
                  </button>
                </div>

                <div className="rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" style={{ minHeight: '500px' }}>
                  <CodeEditor
                    value={result.code}
                    onChange={() => {}}
                    language="python"
                    height="500px"
                    readOnly
                  />
                </div>
              </div>

              {/* Execution Results */}
              {executionResult && (
                <div className="card">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Результаты выполнения
                  </h3>

                  {executionResult.allure_results ? (
                    <div className="space-y-4">
                      {/* Allure Summary */}
                      <div className="grid grid-cols-5 gap-2">
                        <div className="bg-gray-100 dark:bg-gray-800 rounded p-3 text-center">
                          <div className="text-2xl font-bold">{executionResult.allure_results.total_tests}</div>
                          <div className="text-xs text-gray-600 dark:text-gray-400">Всего</div>
                        </div>
                        <div className="bg-green-100 dark:bg-green-900/30 rounded p-3 text-center">
                          <div className="text-2xl font-bold text-green-600">{executionResult.allure_results.passed}</div>
                          <div className="text-xs text-green-600 dark:text-green-400">Пройдено</div>
                        </div>
                        <div className="bg-red-100 dark:bg-red-900/30 rounded p-3 text-center">
                          <div className="text-2xl font-bold text-red-600">{executionResult.allure_results.failed}</div>
                          <div className="text-xs text-red-600 dark:text-red-400">Провалено</div>
                        </div>
                        <div className="bg-orange-100 dark:bg-orange-900/30 rounded p-3 text-center">
                          <div className="text-2xl font-bold text-orange-600">{executionResult.allure_results.broken}</div>
                          <div className="text-xs text-orange-600 dark:text-orange-400">Сломано</div>
                        </div>
                        <div className="bg-gray-100 dark:bg-gray-800 rounded p-3 text-center">
                          <div className="text-2xl font-bold">{executionResult.allure_results.skipped}</div>
                          <div className="text-xs text-gray-600 dark:text-gray-400">Пропущено</div>
                        </div>
                      </div>

                      {/* Test Details */}
                      <div className="space-y-2">
                        {executionResult.allure_results.tests.map((test, idx) => (
                          <div
                            key={idx}
                            className={`p-3 rounded border ${
                              test.status === 'passed'
                                ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
                                : test.status === 'failed'
                                ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
                                : 'border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="font-medium text-sm">{test.name}</div>
                                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">{test.fullName}</div>
                              </div>
                              <div className="text-right">
                                <span className={`text-xs font-medium ${
                                  test.status === 'passed' ? 'text-green-600' :
                                  test.status === 'failed' ? 'text-red-600' : 'text-orange-600'
                                }`}>
                                  {test.status.toUpperCase()}
                                </span>
                                <div className="text-xs text-gray-500 mt-1">{test.duration}ms</div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div>
                      {executionResult.can_execute ? (
                        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                          <div className="text-green-600 dark:text-green-400 font-medium mb-2">Выполнено успешно</div>
                          {executionResult.execution_output && (
                            <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                              {executionResult.execution_output}
                            </pre>
                          )}
                        </div>
                      ) : (
                        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                          <div className="text-red-600 dark:text-red-400 font-medium mb-2">Ошибка выполнения</div>
                          {executionResult.syntax_errors.length > 0 && (
                            <div className="mb-2">
                              <div className="text-sm font-medium">Синтаксические ошибки:</div>
                              <ul className="text-sm list-disc list-inside">
                                {executionResult.syntax_errors.map((err, idx) => (
                                  <li key={idx}>{err}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {executionResult.runtime_errors.length > 0 && (
                            <div>
                              <div className="text-sm font-medium">Ошибки выполнения:</div>
                              <ul className="text-sm list-disc list-inside">
                                {executionResult.runtime_errors.map((err, idx) => (
                                  <li key={idx}>{err}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="card">
              <div className="text-center py-12">
                <CodeBracketIcon className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Загрузите OpenAPI спецификацию и нажмите "Сгенерировать тесты"
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
