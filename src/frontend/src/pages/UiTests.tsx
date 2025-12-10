import { useState } from 'react'
import { GlobeAltIcon, CodeBracketIcon, CursorArrowRaysIcon } from '@heroicons/react/24/outline'
import { CodeEditor } from '@/components/editor/CodeEditor'
import { toast } from 'react-hot-toast'

interface UiTestResponse {
  code: string
  selectors_found: string[]
  test_scenarios: string[]
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
  const [selectors, setSelectors] = useState<Selector[]>([])
  const [framework, setFramework] = useState<'playwright' | 'selenium' | 'cypress'>('playwright')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<UiTestResponse | null>(null)

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
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Результаты генерации
                </h3>

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
