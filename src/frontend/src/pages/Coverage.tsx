import React, { useState, useRef } from 'react';
import { CloudArrowUpIcon, CodeBracketIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import { useCoverageStore } from '@/stores/coverageStore';
import LanguageSelector from '@/components/LanguageSelector';
import CoverageVisualization from '@/components/code-coverage/CoverageVisualization';
import UncoveredFunctionsList from '@/components/code-coverage/UncoveredFunctionsList';
import GeneratedTestsViewer from '@/components/code-coverage/GeneratedTestsViewer';

const Coverage: React.FC = () => {
  const {
    uploadMethod,
    repoUrl,
    analysis,
    isAnalyzing,
    isGenerating,
    selectedLanguage,
    selectedFramework,
    setUploadMethod,
    setRepoUrl,
    analyzeFromGithub,
    analyzeFromGitlab,
    exportReport,
  } = useCoverageStore();

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(Array.from(event.target.files));
    }
  };

  const handleAnalyze = async () => {
    if (uploadMethod === 'file' && selectedFiles.length > 0) {
      await useCoverageStore.getState().analyzeCoverage(selectedFiles);
    } else if (uploadMethod === 'github' && repoUrl) {
      await analyzeFromGithub(repoUrl);
    } else if (uploadMethod === 'gitlab' && repoUrl) {
      await analyzeFromGitlab(repoUrl);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Анализ покрытия кода
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Анализируйте покрытие кода и генерируйте недостающие тесты
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Загрузите ваш код
        </h2>

        {/* Upload Method Selector */}
        <div className="flex space-x-4 mb-6">
          <button
            onClick={() => setUploadMethod('file')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              uploadMethod === 'file'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <CloudArrowUpIcon className="inline-block w-5 h-5 mr-2" />
            Файлы
          </button>
          <button
            onClick={() => setUploadMethod('github')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              uploadMethod === 'github'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <CodeBracketIcon className="inline-block w-5 h-5 mr-2" />
            GitHub
          </button>
          <button
            onClick={() => setUploadMethod('gitlab')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              uploadMethod === 'gitlab'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <CodeBracketIcon className="inline-block w-5 h-5 mr-2" />
            GitLab
          </button>
        </div>

        {/* Upload Content */}
        {uploadMethod === 'file' && (
          <div>
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
              <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <label htmlFor="file-upload" className="cursor-pointer">
                <span className="text-gray-900 dark:text-white font-medium">
                  Нажмите для загрузки файлов
                </span>
                <span className="text-gray-500 dark:text-gray-400">
                  {' '}или перетащите их сюда
                </span>
                <input
                  ref={fileInputRef}
                  id="file-upload"
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileSelect}
                  accept=".py,.js,.jsx,.ts,.tsx,.java,.cs"
                />
              </label>
              <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">
                Файлы Python, JavaScript, TypeScript, Java, C#
              </p>
              {selectedFiles.length > 0 && (
                <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                  Выбрано файлов: {selectedFiles.length}
                </div>
              )}
            </div>
          </div>
        )}

        {(uploadMethod === 'github' || uploadMethod === 'gitlab') && (
          <div>
            <label htmlFor="repo-url" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              URL репозитория
            </label>
            <input
              type="text"
              id="repo-url"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder={`https://github.com/username/repository`}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>
        )}

        {/* Language and Framework Selection */}
        <div className="grid grid-cols-2 gap-4 mt-6">
          <LanguageSelector />
        </div>

        {/* Analyze Button */}
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing || (uploadMethod === 'file' && selectedFiles.length === 0) || ((uploadMethod === 'github' || uploadMethod === 'gitlab') && !repoUrl)}
          className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isAnalyzing ? 'Анализ...' : 'Анализировать покрытие'}
        </button>
      </div>

      {/* Results Section */}
      {analysis && (
        <div className="space-y-8">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Общее покрытие</h3>
              <p className={`text-3xl font-bold ${useCoverageStore.getState().getCoverageColor(analysis.overall_coverage)}`}>
                {analysis.overall_coverage.toFixed(1)}%
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Проанализировано файлов</h3>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {analysis.total_files}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {analysis.test_files} тестовых файлов
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Непокрытых функций</h3>
              <p className="text-3xl font-bold text-red-600">
                {analysis.uncovered_functions.length}
              </p>
            </div>
          </div>

          {/* Coverage Visualization */}
          <CoverageVisualization analysis={analysis} />

          {/* Export Button */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={() => exportReport('json')}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              <DocumentArrowDownIcon className="inline-block w-5 h-5 mr-2" />
              Экспорт JSON
            </button>
            <button
              onClick={() => exportReport('html')}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              <DocumentArrowDownIcon className="inline-block w-5 h-5 mr-2" />
              Экспорт HTML
            </button>
          </div>

          {/* Uncovered Functions List */}
          <UncoveredFunctionsList
            functions={analysis.uncovered_functions}
            isGenerating={isGenerating}
          />

          {/* Generated Tests Viewer */}
          <GeneratedTestsViewer />
        </div>
      )}
    </div>
  );
};

export default Coverage;