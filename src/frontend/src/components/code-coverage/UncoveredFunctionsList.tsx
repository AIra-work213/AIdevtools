import React, { useState } from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { UncoveredFunction } from '@/stores/coverageStore';
import { useCoverageStore } from '@/stores/coverageStore';

interface UncoveredFunctionsListProps {
  functions: UncoveredFunction[];
  isGenerating: boolean;
}

const UncoveredFunctionsList: React.FC<UncoveredFunctionsListProps> = ({ functions, isGenerating }) => {
  const { generateTests, getPriorityColor } = useCoverageStore();
  const [selectedFunctions, setSelectedFunctions] = useState<UncoveredFunction[]>([]);
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const filteredFunctions = functions.filter(func =>
    filter === 'all' || func.priority === filter
  );

  const handleSelectFunction = (func: UncoveredFunction) => {
    setSelectedFunctions(prev => {
      const isSelected = prev.some(f => f.name === func.name && f.file_path === func.file_path);
      if (isSelected) {
        return prev.filter(f => !(f.name === func.name && f.file_path === func.file_path));
      } else {
        return [...prev, func];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedFunctions.length === filteredFunctions.length) {
      setSelectedFunctions([]);
    } else {
      setSelectedFunctions(filteredFunctions);
    }
  };

  const handleGenerateTests = async () => {
    if (selectedFunctions.length === 0) {
      alert('Please select at least one function to generate tests for');
      return;
    }
    await generateTests(selectedFunctions);
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'medium':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'low':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      default:
        return null;
    }
  };

  const getComplexityBadge = (complexity: number) => {
    if (complexity >= 5) {
      return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 rounded">Complex</span>;
    } else if (complexity >= 3) {
      return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300 rounded">Moderate</span>;
    }
    return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 rounded">Simple</span>;
  };

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Uncovered Functions ({filteredFunctions.length})
        </h2>

        <div className="flex items-center space-x-4">
          {/* Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as 'all' | 'high' | 'medium' | 'low')}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          >
            <option value="all">All Priorities</option>
            <option value="high">High Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="low">Low Priority</option>
          </select>

          {/* Generate Tests Button */}
          <button
            onClick={handleGenerateTests}
            disabled={selectedFunctions.length === 0 || isGenerating}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            <SparklesIcon className="h-5 w-5 mr-2" />
            {isGenerating ? 'Generating...' : `Generate Tests (${selectedFunctions.length})`}
          </button>
        </div>
      </div>

      {/* Select All Checkbox */}
      <div className="mb-4">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={selectedFunctions.length === filteredFunctions.length && filteredFunctions.length > 0}
            onChange={handleSelectAll}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
            Select all ({selectedFunctions.length} selected)
          </span>
        </label>
      </div>

      {/* Functions List */}
      <div className="space-y-3">
        {filteredFunctions.map((func, index) => (
          <div
            key={`${func.file_path}-${func.name}-${index}`}
            className={`p-4 border rounded-lg transition-all ${
              selectedFunctions.some(f => f.name === func.name && f.file_path === func.file_path)
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700'
            }`}
          >
            <div className="flex items-start space-x-3">
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={selectedFunctions.some(f => f.name === func.name && f.file_path === func.file_path)}
                onChange={() => handleSelectFunction(func)}
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />

              {/* Function Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                    {func.name}
                  </h3>
                  {getPriorityIcon(func.priority)}
                  <span className={`px-2 py-1 text-xs font-medium rounded ${getPriorityColor(func.priority)}`}>
                    {func.priority}
                  </span>
                  {getComplexityBadge(func.complexity)}
                </div>

                <p className="text-xs text-gray-600 dark:text-gray-400 font-mono mb-2">
                  {func.signature}
                </p>

                <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                  <span>
                    File: <span className="font-medium">{func.file_path}</span>
                  </span>
                  <span>
                    Line: <span className="font-medium">{func.line_start}-{func.line_end}</span>
                  </span>
                  <span>
                    Complexity: <span className="font-medium">{func.complexity}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}

        {filteredFunctions.length === 0 && (
          <div className="text-center py-8">
            <CheckCircleIcon className="mx-auto h-12 w-12 text-green-500 mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              {filter === 'all' ? 'All functions are covered by tests!' : `No ${filter} priority functions found`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default UncoveredFunctionsList;