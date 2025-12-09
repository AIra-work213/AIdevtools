import React from 'react';
import { ChartBarIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { CoverageAnalysis } from '@/stores/coverageStore';
import { useCoverageStore } from '@/stores/coverageStore';

interface CoverageVisualizationProps {
  analysis: CoverageAnalysis;
}

const CoverageVisualization: React.FC<CoverageVisualizationProps> = ({ analysis }) => {
  const { getCoverageColor } = useCoverageStore();

  // Calculate statistics
  const averageFileCoverage = Object.values(analysis.file_coverage).reduce(
    (sum, metrics) => sum + metrics.coverage_percentage,
    0
  ) / Object.keys(analysis.file_coverage).length || 0;

  const fullyCoveredFiles = Object.values(analysis.file_coverage).filter(
    metrics => metrics.coverage_percentage === 100
  ).length;

  const partiallyCoveredFiles = Object.values(analysis.file_coverage).filter(
    metrics => metrics.coverage_percentage > 0 && metrics.coverage_percentage < 100
  ).length;

  const uncoveredFiles = Object.values(analysis.file_coverage).filter(
    metrics => metrics.coverage_percentage === 0
  ).length;

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
        Детализация покрытия
      </h2>

      {/* Overall Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Общее покрытие
          </span>
          <span className={`text-sm font-bold ${getCoverageColor(analysis.overall_coverage)}`}>
            {analysis.overall_coverage.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              analysis.overall_coverage >= 80 ? 'bg-green-500' :
              analysis.overall_coverage >= 50 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${analysis.overall_coverage}%` }}
          />
        </div>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <CheckCircleIcon className="mx-auto h-8 w-8 text-green-500 mb-2" />
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {fullyCoveredFiles}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Полностью покрытых файлов
          </div>
        </div>
        <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <ChartBarIcon className="mx-auto h-8 w-8 text-yellow-500 mb-2" />
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {partiallyCoveredFiles}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Частично покрытых файлов
          </div>
        </div>
        <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <XCircleIcon className="mx-auto h-8 w-8 text-red-500 mb-2" />
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {uncoveredFiles}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Непокрытых файлов
          </div>
        </div>
      </div>

      {/* File Coverage List */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Детали покрытия файлов
        </h3>
        <div className="space-y-3">
          {Object.entries(analysis.file_coverage).map(([filePath, metrics]) => (
            <div
              key={filePath}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
            >
              <div className="flex-1 min-w-0 mr-4">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {filePath}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {metrics.functions_covered}/{metrics.functions_total} функций
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-24">
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div
                      className={`h-full rounded-full ${
                        metrics.coverage_percentage >= 80 ? 'bg-green-500' :
                        metrics.coverage_percentage >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${metrics.coverage_percentage}%` }}
                    />
                  </div>
                </div>
                <span className={`text-sm font-medium ${getCoverageColor(metrics.coverage_percentage)} min-w-[3rem] text-right`}>
                  {metrics.coverage_percentage.toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Suggestions */}
      {analysis.suggestions.length > 0 && (
        <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100 mb-3">
            Рекомендации по улучшению
          </h3>
          <ul className="space-y-2">
            {analysis.suggestions.map((suggestion, index) => (
              <li key={index} className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span className="text-blue-800 dark:text-blue-200 text-sm">
                  {suggestion}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CoverageVisualization;