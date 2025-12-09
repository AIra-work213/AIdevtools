import React, { useState } from 'react';
import { ClipboardIcon, CheckIcon, CodeBracketIcon, DownloadIcon } from '@heroicons/react/24/outline';
import { useCoverageStore } from '@/stores/coverageStore';
import Editor from '@monaco-editor/react';

const GeneratedTestsViewer: React.FC = () => {
  const { generatedTests } = useCoverageStore();
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const [copiedTest, setCopiedTest] = useState<string | null>(null);

  const handleCopyTest = async (testName: string, testCode: string) => {
    try {
      await navigator.clipboard.writeText(testCode);
      setCopiedTest(testName);
      setTimeout(() => setCopiedTest(null), 2000);
    } catch (error) {
      console.error('Failed to copy test:', error);
    }
  };

  const handleDownloadTest = (testName: string, testCode: string) => {
    const blob = new Blob([testCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_${testName}.py`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadAllTests = () => {
    Object.entries(generatedTests).forEach(([testName, testCode]) => {
      handleDownloadTest(testName, testCode);
    });
  };

  if (Object.keys(generatedTests).length === 0) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Generated Tests ({Object.keys(generatedTests).length})
        </h2>
        <button
          onClick={handleDownloadAllTests}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex items-center"
        >
          <DownloadIcon className="h-5 w-5 mr-2" />
          Download All
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Test List */}
        <div className="lg:col-span-1 space-y-2">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Test Files
          </h3>
          {Object.entries(generatedTests).map(([testName, testCode]) => (
            <div
              key={testName}
              onClick={() => setSelectedTest(testName)}
              className={`p-3 rounded-lg cursor-pointer transition-colors ${
                selectedTest === testName
                  ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-700'
                  : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CodeBracketIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    test_{testName}.py
                  </span>
                </div>
                <div className="flex space-x-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopyTest(testName, testCode);
                    }}
                    className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                    title="Copy test"
                  >
                    {copiedTest === testName ? (
                      <CheckIcon className="h-4 w-4 text-green-500" />
                    ) : (
                      <ClipboardIcon className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                    )}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownloadTest(testName, testCode);
                    }}
                    className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                    title="Download test"
                  >
                    <DownloadIcon className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Code Editor */}
        <div className="lg:col-span-2">
          {selectedTest ? (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {selectedTest}
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleCopyTest(selectedTest, generatedTests[selectedTest])}
                    className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex items-center"
                  >
                    {copiedTest === selectedTest ? (
                      <>
                        <CheckIcon className="h-4 w-4 mr-1 text-green-500" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <ClipboardIcon className="h-4 w-4 mr-1" />
                        Copy
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => handleDownloadTest(selectedTest, generatedTests[selectedTest])}
                    className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex items-center"
                  >
                    <DownloadIcon className="h-4 w-4 mr-1" />
                    Download
                  </button>
                </div>
              </div>
              <Editor
                height="500px"
                defaultLanguage="python"
                value={generatedTests[selectedTest]}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  roundedSelection: false,
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  readOnly: true,
                }}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-96 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400">
                Select a test file to view its content
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Usage Instructions */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
          How to use these tests:
        </h3>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• Save the test files in your project's test directory</li>
          <li>• Make sure all dependencies are installed</li>
          <li>• Run tests using pytest (e.g., <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">pytest</code>)</li>
          <li>• Review and customize tests as needed for your specific use cases</li>
        </ul>
      </div>
    </div>
  );
};

export default GeneratedTestsViewer;