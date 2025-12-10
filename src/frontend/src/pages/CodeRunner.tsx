import { useState } from 'react'
import { PlayIcon, StopIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'
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

export function CodeRunner() {
  const [sourceCode, setSourceCode] = useState('')
  const [testCode, setTestCode] = useState('')
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [timeout, setTimeout] = useState(10)

  const handleExecute = async () => {
    if (!testCode.trim()) {
      toast.error('Введите код для выполнения')
      return
    }

    setIsExecuting(true)
    setExecutionResult(null)

    try {
      // Auto-detect Allure
      const hasAllure = testCode.includes('@allure') || testCode.includes('import allure')

      const response = await fetch('/api/v1/generate/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: testCode,
          source_code: sourceCode.trim() || null,
          timeout,
          run_with_pytest: hasAllure,
        }),
      })

      if (!response.ok) {
        throw new Error('Ошибка выполнения кода')
      }

      const result = await response.json()
      setExecutionResult(result)

      if (result.can_execute) {
        if (result.allure_results) {
          const { passed, total_tests } = result.allure_results
          toast.success(`✅ Тесты: ${passed}/${total_tests} пройдено (${result.execution_time?.toFixed(2)}с)`)
        } else {
          toast.success(`Код выполнен успешно за ${result.execution_time?.toFixed(2)}с`)
        }
      } else {
        toast.error('Код содержит ошибки')
      }
    } catch (error) {
      console.error('Execution error:', error)
      toast.error('Произошла ошибка при выполнении кода')
    } finally {
      setIsExecuting(false)
    }
  }

  const handleClear = () => {
    setSourceCode('')
    setTestCode('')
    setExecutionResult(null)
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Запуск тестов
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Выполните ваш тестовый код и проверьте результаты
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          {/* Source Code */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Исходный код (опционально)
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Код функций, которые будут тестироваться
            </p>
            <div className="mb-4 rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" style={{ minHeight: '300px' }}>
              <CodeEditor
                value={sourceCode}
                onChange={setSourceCode}
                language="python"
                height="300px"
              />
            </div>
          </div>

          {/* Test Code */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Тестовый код
            </h3>
            <div className="mb-4 rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" style={{ minHeight: '400px' }}>
              <CodeEditor
                value={testCode}
                onChange={setTestCode}
                language="python"
                height="400px"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Таймаут выполнения: {timeout}с
              </label>
              <input
                type="range"
                min="5"
                max="60"
                step="5"
                value={timeout}
                onChange={(e) => setTimeout(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleExecute}
                disabled={isExecuting || !testCode.trim()}
                className="btn-primary flex-1"
              >
                {isExecuting ? (
                  <>
                    <StopIcon className="w-5 h-5 mr-2 animate-spin" />
                    Выполняется...
                  </>
                ) : (
                  <>
                    <PlayIcon className="w-5 h-5 mr-2" />
                    Запустить тесты
                  </>
                )}
              </button>
              <button onClick={handleClear} className="btn-secondary">
                Очистить
              </button>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {executionResult ? (
            <>
              {/* Status */}
              <div className="card">
                <div className="flex items-center gap-3 mb-4">
                  {executionResult.can_execute ? (
                    <CheckCircleIcon className="w-8 h-8 text-green-500" />
                  ) : (
                    <XCircleIcon className="w-8 h-8 text-red-500" />
                  )}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      {executionResult.can_execute ? 'Успешно' : 'Ошибка'}
                    </h3>
                    {executionResult.execution_time !== null && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Время выполнения: {executionResult.execution_time.toFixed(3)}с
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Syntax Errors */}
              {executionResult.syntax_errors.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-medium text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                    <XCircleIcon className="w-5 h-5" />
                    Синтаксические ошибки
                  </h3>
                  <div className="space-y-2">
                    {executionResult.syntax_errors.map((error, index) => (
                      <div
                        key={index}
                        className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
                      >
                        <p className="text-sm text-red-800 dark:text-red-200 font-mono">
                          {error}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Runtime Errors */}
              {executionResult.runtime_errors.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-medium text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                    <XCircleIcon className="w-5 h-5" />
                    Ошибки выполнения
                  </h3>
                  <div className="space-y-2">
                    {executionResult.runtime_errors.map((error, index) => (
                      <div
                        key={index}
                        className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
                      >
                        <pre className="text-sm text-red-800 dark:text-red-200 whitespace-pre-wrap font-mono">
                          {error}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Execution Output */}
              {executionResult.execution_output && (
                <div className="card">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    Вывод программы
                  </h3>
                  <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                    <pre className="whitespace-pre-wrap">{executionResult.execution_output}</pre>
                  </div>
                </div>
              )}

              {/* Allure Report */}
              {executionResult.allure_results && (
                <div className="card">
                  <h3 className="text-lg font-medium text-purple-900 dark:text-purple-300 mb-4 flex items-center gap-2">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Отчет Allure
                  </h3>
                  
                  {/* Summary Stats */}
                  <div className="grid grid-cols-5 gap-3 mb-6">
                    <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Всего</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {executionResult.allure_results.total_tests}
                      </div>
                    </div>
                    <div className="bg-green-100 dark:bg-green-900/30 rounded-lg p-4 text-center">
                      <div className="text-sm text-green-700 dark:text-green-400 mb-1">Пройдено</div>
                      <div className="text-2xl font-bold text-green-800 dark:text-green-300">
                        {executionResult.allure_results.passed}
                      </div>
                    </div>
                    <div className="bg-red-100 dark:bg-red-900/30 rounded-lg p-4 text-center">
                      <div className="text-sm text-red-700 dark:text-red-400 mb-1">Провалено</div>
                      <div className="text-2xl font-bold text-red-800 dark:text-red-300">
                        {executionResult.allure_results.failed}
                      </div>
                    </div>
                    <div className="bg-orange-100 dark:bg-orange-900/30 rounded-lg p-4 text-center">
                      <div className="text-sm text-orange-700 dark:text-orange-400 mb-1">Сломано</div>
                      <div className="text-2xl font-bold text-orange-800 dark:text-orange-300">
                        {executionResult.allure_results.broken}
                      </div>
                    </div>
                    <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Пропущено</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {executionResult.allure_results.skipped}
                      </div>
                    </div>
                  </div>

                  {/* Detailed Test Results */}
                  {executionResult.allure_results.tests.length > 0 && (
                    <div>
                      <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                        Детальные результаты:
                      </h4>
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {executionResult.allure_results.tests.map((test, idx) => (
                          <div
                            key={idx}
                            className={`rounded-lg p-4 border-l-4 ${
                              test.status === 'passed'
                                ? 'bg-green-50 border-green-500 dark:bg-green-900/20 dark:border-green-400'
                                : test.status === 'failed'
                                ? 'bg-red-50 border-red-500 dark:bg-red-900/20 dark:border-red-400'
                                : test.status === 'broken'
                                ? 'bg-orange-50 border-orange-500 dark:bg-orange-900/20 dark:border-orange-400'
                                : 'bg-gray-50 border-gray-500 dark:bg-gray-700 dark:border-gray-400'
                            }`}
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <h5 className="font-semibold text-gray-900 dark:text-white mb-1">
                                  {test.name}
                                </h5>
                                <p className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                                  {test.fullName}
                                </p>
                              </div>
                              <span className={`ml-4 px-3 py-1 rounded-full text-xs font-bold uppercase ${
                                test.status === 'passed' ? 'bg-green-200 text-green-800 dark:bg-green-800 dark:text-green-200' :
                                test.status === 'failed' ? 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200' :
                                test.status === 'broken' ? 'bg-orange-200 text-orange-800 dark:bg-orange-800 dark:text-orange-200' :
                                'bg-gray-200 text-gray-800 dark:bg-gray-600 dark:text-gray-200'
                              }`}>
                                {test.status}
                              </span>
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              ⏱️ Длительность: <span className="font-semibold">{(test.duration / 1000).toFixed(3)}s</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Report Path */}
                  {executionResult.allure_report_path && (
                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm text-blue-800 dark:text-blue-300">
                        <strong>📁 Путь к отчету:</strong>
                        <br />
                        <code className="mt-1 block text-xs">{executionResult.allure_report_path}</code>
                      </p>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="card">
              <div className="text-center py-12">
                <PlayIcon className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Введите код и нажмите "Запустить тесты"
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
