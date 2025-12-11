import { useState } from 'react'
import { GlobeAltIcon, CodeBracketIcon, CursorArrowRaysIcon, PlayIcon } from '@heroicons/react/24/outline'
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

interface UiTestResponse {
  code: string
  selectors_found: string[]
  test_scenarios: string[]
  setup_instructions: string
  requirements_file: string
  discovered_urls?: string[]  // Adaptive generation
  pages_tested?: number        // Adaptive generation
  validation: {
    is_valid: boolean
    errors: string[]
    warnings: string[]
    suggestions: string[]
  }
}

interface Selector {
  id: string
  type: 'id' | 'class' | 'xpath' | 'css'
  value: string
  description: string
}

export function UiTests() {
  const [inputMethod, setInputMethod] = useState<'html' | 'url'>('html')
  const [htmlContent, setHtmlContent] = useState('')
  const [url, setUrl] = useState('')
  const [sourceCode, setSourceCode] = useState('')
  const [selectors, setSelectors] = useState<Selector[]>([])
  const [framework, setFramework] = useState<'playwright' | 'selenium' | 'cypress'>('playwright')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<UiTestResponse | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)

  const addSelector = () => {
    setSelectors([
      ...selectors,
      {
        id: Date.now().toString(),
        type: 'id',
        value: '',
        description: '',
      },
    ])
  }

  const updateSelector = (id: string, field: keyof Selector, value: string) => {
    setSelectors(
      selectors.map((s) => (s.id === id ? { ...s, [field]: value } : s))
    )
  }

  const removeSelector = (id: string) => {
    setSelectors(selectors.filter((s) => s.id !== id))
  }

  const handleGenerate = async () => {
    if (inputMethod === 'html' && !htmlContent.trim()) {
      toast.error('Введите HTML код')
      return
    }

    if (inputMethod === 'url' && !url.trim()) {
      toast.error('Введите URL')
      return
    }

    setIsGenerating(true)
    setResult(null)

    try {
      const response = await fetch('/api/v1/generate/auto/ui', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_method: inputMethod,
          html_content: inputMethod === 'html' ? htmlContent : null,
          url: inputMethod === 'url' ? url : null,
          selectors: selectors.reduce((acc, s) => {
            if (s.value) {
              acc[s.description || s.value] = s.value
            }
            return acc
          }, {} as Record<string, string>),
          framework,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Ошибка генерации тестов')
      }

      const data = await response.json()
      setResult(data)
      toast.success(`Сгенерировано ${data.test_scenarios.length} тестовых сценариев`)
    } catch (error: any) {
      console.error('UI test generation error:', error)
      toast.error(error.message || 'Произошла ошибка при генерации тестов')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleExecute = async () => {
    if (!result?.code) {
      toast.error('Нет кода для выполнения')
      return
    }

    // Execution inside container поддерживаем только для Python/Selenium
    if (framework !== 'selenium') {
      toast.error('Запуск внутри контейнера доступен только для Selenium (Python). Для Playwright/Cypress скачайте тесты и запустите локально.')
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
          timeout: 60,
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

    const extension = framework === 'playwright' ? 'spec.ts' : framework === 'cypress' ? 'cy.js' : 'py'
    const blob = new Blob([result.code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ui_tests.${extension}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success('Тесты скачаны')
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Генерация UI/E2E тестов
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Автоматическая генерация UI тестов из HTML или веб-страницы
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Источник тестов
            </h3>

            {/* Input Method */}
            <div className="mb-4">
              <div className="flex gap-2">
                <button
                  onClick={() => setInputMethod('html')}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                    inputMethod === 'html'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  <CodeBracketIcon className="inline-block w-5 h-5 mr-2" />
                  HTML
                </button>
                <button
                  onClick={() => setInputMethod('url')}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                    inputMethod === 'url'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  <GlobeAltIcon className="inline-block w-5 h-5 mr-2" />
                  URL
                </button>
              </div>
            </div>

            {/* HTML Input */}
            {inputMethod === 'html' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  HTML код:
                </label>
                <div className="rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" style={{ minHeight: '300px' }}>
                  <CodeEditor
                    value={htmlContent}
                    onChange={setHtmlContent}
                    language="html"
                    height="300px"
                  />
                </div>
              </div>
            )}

            {/* URL Input */}
            {inputMethod === 'url' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  URL страницы:
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            )}

            {/* Framework Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Фреймворк:
              </label>
              <select
                value={framework}
                onChange={(e) => setFramework(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="playwright">Playwright (TypeScript)</option>
                <option value="selenium">Selenium (Python)</option>
                <option value="cypress">Cypress (JavaScript)</option>
              </select>
            </div>

            {/* Selectors */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Селекторы (опционально):
                </label>
                <button
                  onClick={addSelector}
                  className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                >
                  + Добавить
                </button>
              </div>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {selectors.map((selector) => (
                  <div
                    key={selector.id}
                    className="flex gap-2 items-start p-2 bg-gray-50 dark:bg-gray-700/50 rounded"
                  >
                    <select
                      value={selector.type}
                      onChange={(e) =>
                        updateSelector(selector.id, 'type', e.target.value)
                      }
                      className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                    >
                      <option value="id">ID</option>
                      <option value="class">Class</option>
                      <option value="xpath">XPath</option>
                      <option value="css">CSS</option>
                    </select>

                    <input
                      type="text"
                      value={selector.value}
                      onChange={(e) =>
                        updateSelector(selector.id, 'value', e.target.value)
                      }
                      placeholder="Селектор"
                      className="flex-1 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                    />

                    <input
                      type="text"
                      value={selector.description}
                      onChange={(e) =>
                        updateSelector(selector.id, 'description', e.target.value)
                      }
                      placeholder="Описание"
                      className="flex-1 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                    />

                    <button
                      onClick={() => removeSelector(selector.id)}
                      className="text-red-500 hover:text-red-700"
                    >
                      ✕
                    </button>
                  </div>
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
                placeholder="Вставьте код веб-приложения (роутеры, компоненты, логику)..."
                className="w-full h-32 p-3 text-sm font-mono rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-vertical focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                💡 Добавьте код для понимания поведения приложения и генерации точных тестов
              </p>
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="btn-primary w-full"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Генерация...
                </>
              ) : (
                <>
                  <CursorArrowRaysIcon className="h-5 w-5 mr-2" />
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

                {/* Headless Info */}
                {(framework === 'selenium' || framework === 'playwright') && (
                  <div className="mb-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3">
                    <div className="flex items-start gap-2">
                      <svg className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      <div className="text-sm text-blue-800 dark:text-blue-200">
                        <p className="font-medium mb-1">ℹ️ Headless режим</p>
                        <p className="text-xs">
                          Тесты запускаются в headless браузере (без GUI) прямо в контейнере
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                    <div className="text-sm text-purple-600 dark:text-purple-400 mb-1">
                      Селекторы
                    </div>
                    <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                      {result.selectors_found.length}
                    </div>
                  </div>

                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                    <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
                      Сценарии
                    </div>
                    <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                      {result.test_scenarios.length}
                    </div>
                  </div>

                  {result.pages_tested && result.pages_tested > 1 && (
                    <div className="col-span-2 bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                      <div className="text-sm text-green-600 dark:text-green-400 mb-1">
                        🎯 Адаптивная генерация: найдено страниц на сайте
                      </div>
                      <div className="text-2xl font-bold text-green-900 dark:text-green-100 mb-2">
                        {result.pages_tested}
                      </div>
                      {result.discovered_urls && (
                        <div className="text-xs text-green-700 dark:text-green-300 max-h-32 overflow-y-auto">
                          {result.discovered_urls.slice(0, 10).map((url, idx) => (
                            <div key={idx} className="truncate">• {url}</div>
                          ))}
                          {result.discovered_urls.length > 10 && (
                            <div className="mt-1 font-medium">
                              ... и ещё {result.discovered_urls.length - 10} страниц
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Test Scenarios */}
                {result.test_scenarios.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Тестовые сценарии:
                    </h4>
                    <ul className="space-y-1 max-h-40 overflow-y-auto">
                      {result.test_scenarios.map((scenario, idx) => (
                        <li
                          key={idx}
                          className="text-sm text-gray-600 dark:text-gray-400"
                        >
                          {idx + 1}. {scenario}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Validation */}
                {result.validation && !result.validation.is_valid && (
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    {result.validation.errors.length > 0 && (
                      <div className="text-sm text-red-600 dark:text-red-400 mb-2">
                        <div className="font-medium">Ошибки:</div>
                        <ul className="list-disc list-inside">
                          {result.validation.errors.map((error, idx) => (
                            <li key={idx}>{error}</li>
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
                    Сгенерированный код ({framework})
                  </h3>
                  <button onClick={handleDownload} className="btn-secondary text-sm">
                    Скачать
                  </button>
                </div>

                <div className="rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" style={{ minHeight: '500px' }}>
                  <CodeEditor
                    value={result.code}
                    onChange={() => {}}
                    language={framework === 'selenium' ? 'python' : 'typescript'}
                    height="500px"
                    readOnly
                  />
                </div>
              </div>

              {/* Execution Results - Same as ApiTests */}
              {executionResult && (
                <div className="card">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Результаты выполнения
                  </h3>

                  {executionResult.allure_results ? (
                    <div className="space-y-4">
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
                <CursorArrowRaysIcon className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Введите HTML или URL и нажмите "Сгенерировать тесты"
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
