import { create } from 'zustand';
import { toast } from 'react-hot-toast';

interface UploadedFile {
  name: string;
  path: string;
  content: string;
  language: string;
  size: number;
  is_test_file: boolean;
}

interface CoverageMetrics {
  lines_covered: number;
  lines_total: number;
  coverage_percentage: number;
  functions_covered: number;
  functions_total: number;
  branches_covered: number;
  branches_total: number;
}

interface UncoveredFunction {
  name: string;
  file_path: string;
  line_start: number;
  line_end: number;
  signature: string;
  complexity: number;
  priority: 'high' | 'medium' | 'low';
}

interface CoverageAnalysis {
  total_files: number;
  test_files: number;
  overall_coverage: number;
  file_coverage: Record<string, CoverageMetrics>;
  uncovered_functions: UncoveredFunction[];
  coverage_report: string;
  suggestions: string[];
}

interface GeneratedTest {
  [functionName: string]: string;
}

interface CoverageStore {
  // State
  uploadedFiles: UploadedFile[];
  analysis: CoverageAnalysis | null;
  generatedTests: GeneratedTest;
  selectedLanguage: string;
  selectedFramework: string;
  isAnalyzing: boolean;
  isGenerating: boolean;
  uploadMethod: 'file' | 'github' | 'gitlab';
  repoUrl: string;

  // Actions
  setUploadedFiles: (files: UploadedFile[]) => void;
  setAnalysis: (analysis: CoverageAnalysis | null) => void;
  setGeneratedTests: (tests: GeneratedTest) => void;
  setSelectedLanguage: (language: string) => void;
  setSelectedFramework: (framework: string) => void;
  setUploadMethod: (method: 'file' | 'github' | 'gitlab') => void;
  setRepoUrl: (url: string) => void;

  // API Calls
  analyzeCoverage: (files?: File[]) => Promise<void>;
  analyzeFromGithub: (repoUrl: string) => Promise<void>;
  analyzeFromGitlab: (repoUrl: string) => Promise<void>;
  generateTests: (uncoveredFunctions: UncoveredFunction[]) => Promise<void>;
  exportReport: (format: 'json' | 'html') => Promise<void>;

  // Helpers
  clearData: () => void;
  getCoverageColor: (percentage: number) => string;
  getPriorityColor: (priority: string) => string;
}

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

export const useCoverageStore = create<CoverageStore>((set, get) => ({
  // Initial state
  uploadedFiles: [],
  analysis: null,
  generatedTests: {},
  selectedLanguage: 'python',
  selectedFramework: 'pytest',
  isAnalyzing: false,
  isGenerating: false,
  uploadMethod: 'file',
  repoUrl: '',

  // Actions
  setUploadedFiles: (files) => set({ uploadedFiles: files }),
  setAnalysis: (analysis) => set({ analysis }),
  setGeneratedTests: (tests) => set({ generatedTests: tests }),
  setSelectedLanguage: (language) => set({ selectedLanguage: language }),
  setSelectedFramework: (framework) => set({ selectedFramework: framework }),
  setUploadMethod: (method) => set({ uploadMethod: method }),
  setRepoUrl: (url) => set({ repoUrl: url }),

  // API Calls
  analyzeCoverage: async (files?: File[]) => {
    set({ isAnalyzing: true });
    try {
      const { selectedLanguage, selectedFramework } = get();

      if (!files || files.length === 0) {
        toast.error('Please select files to analyze');
        return;
      }

      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });
      formData.append('language', selectedLanguage);
      formData.append('framework', selectedFramework);
      formData.append('include_suggestions', 'true');

      const response = await fetch(`${API_BASE}/coverage/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to analyze coverage');
      }

      const analysis: CoverageAnalysis = await response.json();
      set({ analysis });

      toast.success(`Analysis complete! Overall coverage: ${analysis.overall_coverage.toFixed(1)}%`);
    } catch (error) {
      console.error('Error analyzing coverage:', error);
      toast.error('Failed to analyze coverage');
    } finally {
      set({ isAnalyzing: false });
    }
  },

  analyzeFromGithub: async (repoUrl: string) => {
    set({ isAnalyzing: true, repoUrl });
    try {
      const { selectedLanguage, selectedFramework } = get();

      const formData = new FormData();
      formData.append('repo_url', repoUrl);
      formData.append('language', selectedLanguage);
      formData.append('framework', selectedFramework);

      // Create AbortController with 10 minute timeout for large repos
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000);

      const response = await fetch(`${API_BASE}/coverage/upload/github`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error('Failed to analyze GitHub repository');
      }

      const analysis: CoverageAnalysis = await response.json();
      set({ analysis });

      toast.success(`GitHub analysis complete! Overall coverage: ${analysis.overall_coverage.toFixed(1)}%`);
    } catch (error) {
      console.error('Error analyzing GitHub repo:', error);
      if (error instanceof Error && error.name === 'AbortError') {
        toast.error('Request timeout - repository is too large. Please try a smaller repository.');
      } else {
        toast.error('Failed to analyze GitHub repository');
      }
    } finally {
      set({ isAnalyzing: false });
    }
  },

  analyzeFromGitlab: async (repoUrl: string) => {
    set({ isAnalyzing: true, repoUrl });
    try {
      const { selectedLanguage, selectedFramework } = get();

      const formData = new FormData();
      formData.append('repo_url', repoUrl);
      formData.append('language', selectedLanguage);
      formData.append('framework', selectedFramework);

      const response = await fetch(`${API_BASE}/coverage/upload/gitlab`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to analyze GitLab repository');
      }

      const analysis: CoverageAnalysis = await response.json();
      set({ analysis });

      toast.success(`GitLab analysis complete! Overall coverage: ${analysis.overall_coverage.toFixed(1)}%`);
    } catch (error) {
      console.error('Error analyzing GitLab repo:', error);
      toast.error('Failed to analyze GitLab repository');
    } finally {
      set({ isAnalyzing: false });
    }
  },

  generateTests: async (uncoveredFunctions: UncoveredFunction[]) => {
    set({ isGenerating: true });
    try {
      const response = await fetch(`${API_BASE}/coverage/generate-tests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          uncovered_functions: uncoveredFunctions,
          project_context: 'Generate comprehensive unit tests',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate tests');
      }

      const result = await response.json();
      set({ generatedTests: result.generated_tests });

      toast.success(`Generated ${Object.keys(result.generated_tests).length} test(s)! Coverage improvement: ${result.coverage_improvement.toFixed(1)}%`);
    } catch (error) {
      console.error('Error generating tests:', error);
      toast.error('Failed to generate tests');
    } finally {
      set({ isGenerating: false });
    }
  },

  exportReport: async (format: 'json' | 'html') => {
    try {
      const { analysis, selectedLanguage, selectedFramework } = get();

      if (!analysis) {
        toast.error('No analysis to export');
        return;
      }

      const formData = new FormData();
      formData.append('format', format);
      formData.append('request', JSON.stringify({
        project_files: [],
        language: selectedLanguage,
        framework: selectedFramework,
      }));

      const response = await fetch(`${API_BASE}/coverage/export`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to export report');
      }

      if (format === 'json') {
        const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'coverage_report.json';
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === 'html') {
        const htmlContent = await response.text();
        const blob = new Blob([htmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'coverage_report.html';
        a.click();
        URL.revokeObjectURL(url);
      }

      toast.success(`Report exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Error exporting report:', error);
      toast.error('Failed to export report');
    }
  },

  // Helpers
  clearData: () => set({
    uploadedFiles: [],
    analysis: null,
    generatedTests: {},
    repoUrl: '',
  }),

  getCoverageColor: (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 50) return 'text-yellow-600';
    return 'text-red-600';
  },

  getPriorityColor: (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  },
}));