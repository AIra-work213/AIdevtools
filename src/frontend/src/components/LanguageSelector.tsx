import React from 'react';
import { useCoverageStore } from '../stores/coverageStore';

const LanguageSelector: React.FC = () => {
  const {
    selectedLanguage,
    selectedFramework,
    setSelectedLanguage,
    setSelectedFramework,
  } = useCoverageStore();

  const languageFrameworks: Record<string, string[]> = {
    python: ['pytest', 'unittest'],
    javascript: ['jest', 'mocha'],
    typescript: ['jest', 'vitest'],
    java: ['junit', 'testng'],
    csharp: ['nunit', 'xunit'],
  };

  return (
    <>
      <div>
        <label htmlFor="language-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Programming Language
        </label>
        <select
          id="language-select"
          value={selectedLanguage}
          onChange={(e) => {
            setSelectedLanguage(e.target.value);
            // Reset framework when language changes
            setSelectedFramework(languageFrameworks[e.target.value][0]);
          }}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="java">Java</option>
          <option value="csharp">C#</option>
        </select>
      </div>

      <div>
        <label htmlFor="framework-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Test Framework
        </label>
        <select
          id="framework-select"
          value={selectedFramework}
          onChange={(e) => setSelectedFramework(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        >
          {languageFrameworks[selectedLanguage].map((framework) => (
            <option key={framework} value={framework}>
              {framework.charAt(0).toUpperCase() + framework.slice(1)}
            </option>
          ))}
        </select>
      </div>
    </>
  );
};

export default LanguageSelector;