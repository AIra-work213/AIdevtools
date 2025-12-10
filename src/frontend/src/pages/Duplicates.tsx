import { useState } from 'react'
import { MagnifyingGlassIcon, DocumentDuplicateIcon, FolderOpenIcon } from '@heroicons/react/24/outline'
import { CodeEditor } from '@/components/editor/CodeEditor'
import { toast } from 'react-hot-toast'

interface SimilarTestCase {
  title: string
  code: string
  similarity: number
  file?: string
  line?: number
}

interface DuplicateGroup {
  tests: SimilarTestCase[]
  similarity_score: number
}

interface DuplicateSearchResult {
  total_tests: number
  duplicate_groups: DuplicateGroup[]
  duplicates_found: number
}

export function Duplicates() {
  const [code, setCode] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResult, setSearchResult] = useState<DuplicateSearchResult | null>(null)
  const [similarityThreshold, setSimilarityThreshold] = useState(80)

  const handleSearch = async () => {
    if (!code.trim()) {
      toast.error('Введите код тестов для поиска дубликатов')
      return
    }

    setIsSearching(true)
    setSearchResult(null)

    try {
      const response = await fetch('/api/v1/analyze/duplicates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_code: code,
          similarity_threshold: similarityThreshold / 100,
        }),
      })

      if (!response.ok) {
        throw new Error('Ошибка поиска дубликатов')
      }

      const result = await response.json()
      setSearchResult(result)

      if (result.duplicates_found === 0) {
        toast.success('Дубликаты не найдены')
      } else {
        toast.success(`Найдено ${result.duplicates_found} групп дубликатов`)
      }
    } catch (error) {
      console.error('Duplicate search error:', error)
      toast.error('Произошла ошибка при поиске дубликатов')
    } finally {
      setIsSearching(false)
    }
  }

  const handleClear = () => {
    setCode('')
    setSearchResult(null)
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Поиск дубликатов тестов
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Найдите похожие тесты и оптимизируйте тестовое покрытие
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Код тестов
            </h3>

            <div className="mb-4 rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600" style={{ minHeight: '600px' }}>
              <CodeEditor
                value={code}
                onChange={setCode}
                language="python"
                height="600px"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Порог схожести: {similarityThreshold}%
              </label>
              <input
                type="range"
                min="50"
                max="100"
                step="5"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                <span>50% (менее строго)</span>
                <span>100% (очень строго)</span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSearch}
                disabled={isSearching || !code.trim()}
                className="btn-primary flex-1"
              >
                {isSearching ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Поиск...
                  </>
                ) : (
                  <>
                    <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                    Найти дубликаты
                  </>
                )}
              </button>
              <button
                onClick={handleClear}
                disabled={isSearching}
                className="btn-secondary"
              >
                Очистить
              </button>
            </div>
          </div>

          {/* Example */}
          <div className="card bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800">
            <div className="flex items-start gap-3">
              <DocumentDuplicateIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                  Как это работает
                </h4>
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  Алгоритм анализирует структуру тестов, сравнивает их по токенам
                  и находит похожие тесты на основе заданного порога схожести.
                  Дубликаты группируются по степени похожести.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {/* Summary */}
          {searchResult && (
            <div className="card">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {searchResult.total_tests}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Всего тестов</div>
                </div>
                <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                    {searchResult.duplicates_found}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Групп дубликатов</div>
                </div>
                <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {searchResult.total_tests - (searchResult.duplicate_groups.reduce((sum, g) => sum + g.tests.length, 0) || 0)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Уникальных</div>
                </div>
              </div>
            </div>
          )}

          {/* Duplicate Groups */}
          {searchResult && searchResult.duplicate_groups.length > 0 ? (
            <div className="space-y-4">
              {searchResult.duplicate_groups.map((group, groupIndex) => (
                <div key={groupIndex} className="card border-2 border-red-200 dark:border-red-800">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <DocumentDuplicateIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        Группа #{groupIndex + 1}
                      </h3>
                    </div>
                    <span className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 text-sm font-medium rounded-full">
                      {Math.round(group.similarity_score * 100)}% схожесть
                    </span>
                  </div>

                  <div className="space-y-3">
                    {group.tests.map((test, testIndex) => (
                      <div
                        key={testIndex}
                        className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {test.title || `Тест ${testIndex + 1}`}
                          </h4>
                          {test.similarity !== undefined && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {Math.round(test.similarity * 100)}% похож
                            </span>
                          )}
                        </div>
                        {test.file && (
                          <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 mb-2">
                            <FolderOpenIcon className="h-3 w-3" />
                            <span>{test.file}</span>
                            {test.line && <span>:{test.line}</span>}
                          </div>
                        )}
                        <pre className="text-xs bg-white dark:bg-gray-900 p-2 rounded overflow-x-auto">
                          <code className="text-gray-800 dark:text-gray-200">
                            {test.code.split('\n').slice(0, 5).join('\n')}
                            {test.code.split('\n').length > 5 && '\n...'}
                          </code>
                        </pre>
                      </div>
                    ))}
                  </div>

                  <div className="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-xs text-yellow-800 dark:text-yellow-200">
                    💡 Рекомендация: Рассмотрите возможность объединения этих тестов или использования параметризации
                  </div>
                </div>
              ))}
            </div>
          ) : searchResult && searchResult.duplicates_found === 0 ? (
            <div className="card text-center py-12">
              <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mb-4">
                <svg className="h-8 w-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Дубликатов не найдено
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Все тесты уникальны при текущем пороге схожести {similarityThreshold}%
              </p>
            </div>
          ) : (
            <div className="card text-center py-12">
              <MagnifyingGlassIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Готов к поиску
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Введите код тестов и нажмите "Найти дубликаты"
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
