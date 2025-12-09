"""Service for code coverage analysis"""

import ast
import re
import os
import tempfile
import zipfile
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import urllib.request
from git import Repo
import chardet
import structlog

from app.schemas.test import (
    UploadedFile,
    CoverageMetrics,
    UncoveredFunction,
    CoverageAnalysisRequest,
    CoverageAnalysisResponse,
    GenerateTestsForCoverageRequest,
    GenerateTestsForCoverageResponse
)

logger = structlog.get_logger(__name__)


class CoverageAnalyzer:
    """Analyzes code coverage for different programming languages"""

    def __init__(self):
        self.supported_languages = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'csharp': ['.cs'],
        }

    async def analyze_coverage(self, request: CoverageAnalysisRequest) -> CoverageAnalysisResponse:
        """Analyze code coverage for uploaded files"""
        # Separate source files from test files
        source_files = [f for f in request.project_files if not f.is_test_file]
        test_files = request.test_files or [f for f in request.project_files if f.is_test_file]

        # Parse source code to extract functions
        all_functions = []
        for file in source_files:
            functions = self._extract_functions(file, request.language)
            all_functions.extend(functions)

        # Analyze which functions are covered by tests
        covered_functions = self._find_covered_functions(all_functions, test_files, request.language)
        uncovered_functions = [f for f in all_functions if f.name not in covered_functions]

        # Calculate coverage metrics
        overall_coverage = len(covered_functions) / len(all_functions) if all_functions else 0
        file_coverage = self._calculate_file_coverage(source_files, covered_functions, request.language)

        # Generate suggestions
        suggestions = self._generate_suggestions(uncovered_functions, overall_coverage)

        # Generate coverage report
        coverage_report = self._generate_coverage_report(
            source_files, test_files, overall_coverage, uncovered_functions
        )

        return CoverageAnalysisResponse(
            total_files=len(source_files),
            test_files=len(test_files),
            overall_coverage=overall_coverage * 100,
            file_coverage=file_coverage,
            uncovered_functions=uncovered_functions,
            coverage_report=coverage_report,
            suggestions=suggestions
        )

    def _extract_functions(self, file: UploadedFile, language: str) -> List[UncoveredFunction]:
        """Extract functions from source code based on language"""
        if language == 'python':
            return self._extract_python_functions(file)
        elif language == 'javascript':
            return self._extract_javascript_functions(file)
        elif language == 'typescript':
            return self._extract_typescript_functions(file)
        elif language == 'java':
            return self._extract_java_functions(file)
        elif language == 'csharp':
            return self._extract_csharp_functions(file)
        return []

    def _extract_python_functions(self, file: UploadedFile) -> List[UncoveredFunction]:
        """Extract functions from Python code"""
        try:
            tree = ast.parse(file.content)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Calculate complexity (simplified)
                    complexity = self._calculate_python_complexity(node)
                    priority = self._calculate_priority(complexity, node)

                    functions.append(UncoveredFunction(
                        name=node.name,
                        file_path=file.path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        signature=f"def {node.name}({self._get_python_params(node)})",
                        complexity=complexity,
                        priority=priority
                    ))

            return functions
        except SyntaxError as e:
            print(f"Syntax error in {file.path}: {e}")
            return []

    def _get_python_params(self, node: ast.FunctionDef) -> str:
        """Extract parameter list from Python function definition"""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return ", ".join(args)

    def _calculate_python_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for Python function"""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
        return complexity

    def _extract_javascript_functions(self, file: UploadedFile) -> List[UncoveredFunction]:
        """Extract functions from JavaScript code"""
        functions = []
        # Regular expression for function declarations
        pattern = r'(?:function\s+(\w+)\s*\(([^)]*)\)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\(([^)]*)\))'

        lines = file.content.split('\n')
        for i, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                func_name = match.group(1) or match.group(3) or match.group(5)
                if func_name:
                    complexity = self._estimate_js_complexity(line)
                    functions.append(UncoveredFunction(
                        name=func_name,
                        file_path=file.path,
                        line_start=i,
                        line_end=i,
                        signature=line.strip(),
                        complexity=complexity,
                        priority=self._calculate_priority(complexity, None)
                    ))
        return functions

    def _extract_typescript_functions(self, file: UploadedFile) -> List[UncoveredFunction]:
        """Extract functions from TypeScript code"""
        # Similar to JavaScript but with type annotations
        return self._extract_javascript_functions(file)

    def _extract_java_functions(self, file: UploadedFile) -> List[UncoveredFunction]:
        """Extract methods from Java code"""
        functions = []
        pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(?:\w+\s+)?(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*\{'

        lines = file.content.split('\n')
        for i, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                func_name = match.group(1)
                if func_name and not line.strip().startswith('//'):
                    complexity = self._estimate_java_complexity(line)
                    functions.append(UncoveredFunction(
                        name=func_name,
                        file_path=file.path,
                        line_start=i,
                        line_end=i,
                        signature=line.strip(),
                        complexity=complexity,
                        priority=self._calculate_priority(complexity, None)
                    ))
        return functions

    def _extract_csharp_functions(self, file: UploadedFile) -> List[UncoveredFunction]:
        """Extract methods from C# code"""
        functions = []
        pattern = r'(?:public|private|protected|internal)?\s*(?:static)?\s*(?:async\s+)?(?:\w+\s+)?(\w+)\s*\(([^)]*)\)\s*(?:=>\s*{|{)'

        lines = file.content.split('\n')
        for i, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                func_name = match.group(1)
                if func_name and not line.strip().startswith('//'):
                    complexity = self._estimate_csharp_complexity(line)
                    functions.append(UncoveredFunction(
                        name=func_name,
                        file_path=file.path,
                        line_start=i,
                        line_end=i,
                        signature=line.strip(),
                        complexity=complexity,
                        priority=self._calculate_priority(complexity, None)
                    ))
        return functions

    def _estimate_js_complexity(self, line: str) -> int:
        """Estimate complexity for JavaScript/TypeScript function"""
        complexity = 1
        if 'if' in line: complexity += 1
        if 'for' in line: complexity += 1
        if 'while' in line: complexity += 1
        if 'switch' in line: complexity += 1
        if 'try' in line: complexity += 1
        if '&&' in line or '||' in line: complexity += 1
        return complexity

    def _estimate_java_complexity(self, line: str) -> int:
        """Estimate complexity for Java method"""
        complexity = 1
        if 'if' in line: complexity += 1
        if 'for' in line: complexity += 1
        if 'while' in line: complexity += 1
        if 'switch' in line: complexity += 1
        if 'try' in line: complexity += 1
        if 'catch' in line: complexity += 1
        return complexity

    def _estimate_csharp_complexity(self, line: str) -> int:
        """Estimate complexity for C# method"""
        complexity = 1
        if 'if' in line: complexity += 1
        if 'for' in line: complexity += 1
        if 'foreach' in line: complexity += 1
        if 'while' in line: complexity += 1
        if 'switch' in line: complexity += 1
        if 'try' in line: complexity += 1
        if 'catch' in line: complexity += 1
        return complexity

    def _calculate_priority(self, complexity: int, node) -> str:
        """Calculate priority based on complexity"""
        if complexity >= 5:
            return "high"
        elif complexity >= 3:
            return "medium"
        return "low"

    def _find_covered_functions(self, functions: List[UncoveredFunction], test_files: List[UploadedFile], language: str) -> Set[str]:
        """Find which functions are covered by tests"""
        covered = set()

        for test_file in test_files:
            for func in functions:
                if self._is_function_covered(func, test_file, language):
                    covered.add(func.name)

        return covered

    def _is_function_covered(self, func: UncoveredFunction, test_file: UploadedFile, language: str) -> bool:
        """Check if a function is covered by a test file"""
        # Simple heuristic: if function name appears in test file
        if func.name.lower() in test_file.content.lower():
            return True

        # Check for common test patterns
        test_patterns = [
            f"test_{func.name}",
            f"{func.name}_test",
            f"should{func.name}",
            f"it('{func.name}",
            f"it(\"{func.name}",
            f"def test_{func.name}",
        ]

        for pattern in test_patterns:
            if pattern in test_file.content:
                return True

        return False

    def _calculate_file_coverage(self, source_files: List[UploadedFile], covered_functions: Set[str], language: str) -> Dict[str, CoverageMetrics]:
        """Calculate coverage metrics for each file"""
        file_coverage = {}

        for file in source_files:
            functions = self._extract_functions(file, language)
            covered = [f for f in functions if f.name in covered_functions]

            coverage_percentage = len(covered) / len(functions) if functions else 0

            file_coverage[file.path] = CoverageMetrics(
                lines_covered=0,  # TODO: Implement line coverage
                lines_total=0,
                coverage_percentage=coverage_percentage * 100,
                functions_covered=len(covered),
                functions_total=len(functions),
                branches_covered=0,  # TODO: Implement branch coverage
                branches_total=0
            )

        return file_coverage

    def _generate_suggestions(self, uncovered_functions: List[UncoveredFunction], overall_coverage: float) -> List[str]:
        """Generate suggestions for improving coverage"""
        suggestions = []

        if overall_coverage < 0.5:
            suggestions.append("Your test coverage is below 50%. Consider adding tests for core functionality.")
        elif overall_coverage < 0.8:
            suggestions.append("Good progress! Aim for 80% coverage to ensure reliability.")

        high_priority = [f for f in uncovered_functions if f.priority == "high"]
        if high_priority:
            suggestions.append(f"Priority: Write tests for {len(high_priority)} high-complexity functions.")

        # Group functions by file
        files_with_uncovered = {}
        for func in uncovered_functions:
            if func.file_path not in files_with_uncovered:
                files_with_uncovered[func.file_path] = []
            files_with_uncovered[func.file_path].append(func)

        for file_path, functions in files_with_uncovered.items():
            suggestions.append(f"File {file_path}: {len(functions)} functions need coverage")

        return suggestions

    def _generate_coverage_report(self, source_files: List[UploadedFile], test_files: List[UploadedFile],
                                 overall_coverage: float, uncovered_functions: List[UncoveredFunction]) -> str:
        """Generate a detailed coverage report"""
        report = []
        report.append("# Code Coverage Report\n")
        report.append(f"Overall Coverage: {overall_coverage * 100:.1f}%\n")
        report.append(f"Source Files: {len(source_files)}")
        report.append(f"Test Files: {len(test_files)}\n")

        if uncovered_functions:
            report.append("## Uncovered Functions\n")
            for func in uncovered_functions[:10]:  # Show first 10
                report.append(f"- **{func.name}** ({func.file_path}:{func.line_start}) - Priority: {func.priority}")

            if len(uncovered_functions) > 10:
                report.append(f"\n... and {len(uncovered_functions) - 10} more functions")

        return "\n".join(report)


class CodeUploader:
    """Handles code upload from various sources"""

    @staticmethod
    async def upload_from_file(file_content: str, filename: str, is_test: bool = False) -> UploadedFile:
        """Create UploadedFile from uploaded content"""
        # Detect encoding
        if isinstance(file_content, bytes):
            detected = chardet.detect(file_content)
            file_content = file_content.decode(detected['encoding'] or 'utf-8')

        # Detect language from extension
        ext = Path(filename).suffix.lower()
        language = 'unknown'
        for lang, extensions in {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'csharp': ['.cs']
        }.items():
            if ext in extensions:
                language = lang
                break

        return UploadedFile(
            name=filename,
            path=filename,
            content=file_content,
            language=language,
            size=len(file_content.encode('utf-8')),
            is_test_file=is_test
        )

    @staticmethod
    async def upload_from_github(repo_url: str) -> List[UploadedFile]:
        """Clone and upload from GitHub repository"""
        logger.info("Starting GitHub repository clone", repo_url=repo_url)
        
        # Binary file extensions to skip
        BINARY_EXTENSIONS = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',  # Images
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Documents
            '.zip', '.tar', '.gz', '.rar', '.7z',  # Archives
            '.mp3', '.mp4', '.avi', '.mov', '.wav',  # Media
            '.exe', '.dll', '.so', '.dylib',  # Binaries
            '.pyc', '.pyo', '.class', '.jar',  # Compiled
            '.pt', '.pth', '.h5', '.pb', '.onnx', '.weights',  # ML models
            '.woff', '.woff2', '.ttf', '.eot',  # Fonts
        }
        
        # Source code extensions to prioritize
        SOURCE_EXTENSIONS = {
            '.py', '.java', '.js', '.ts', '.jsx', '.tsx', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.rs', '.scala', '.r',
        }
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info("Cloning repository", temp_dir=temp_dir)
                # Clone the repository with depth 1 for faster cloning
                Repo.clone_from(repo_url, temp_dir, depth=1)
                logger.info("Repository cloned successfully")

                files = []
                processed_count = 0
                skipped_count = 0
                
                for root, dirs, file_names in os.walk(temp_dir):
                    # Skip hidden directories and common non-source directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                        'node_modules', '__pycache__', 'target', 'bin', 'build', 'dist',
                        '.git', '.idea', '.vscode', 'venv', 'env', '.pytest_cache'
                    ]]

                    for file_name in file_names:
                        if file_name.startswith('.'):
                            continue
                            
                        # Check file extension
                        file_ext = os.path.splitext(file_name)[1].lower()
                        
                        # Skip binary files
                        if file_ext in BINARY_EXTENSIONS:
                            skipped_count += 1
                            continue
                        
                        # Process only source code files or files with no extension (like Dockerfile)
                        if file_ext not in SOURCE_EXTENSIONS and file_ext:
                            skipped_count += 1
                            continue
                            
                        file_path = os.path.join(root, file_name)
                        rel_path = os.path.relpath(file_path, temp_dir)

                        try:
                            with open(file_path, 'rb') as f:
                                content = f.read()

                            is_test = 'test' in file_name.lower() or 'spec' in file_name.lower()
                            uploaded = await CodeUploader.upload_from_file(content, rel_path, is_test)
                            files.append(uploaded)
                            processed_count += 1
                        except Exception as file_error:
                            logger.warning("Failed to process file", file_path=rel_path, error=str(file_error))
                            skipped_count += 1
                            continue

                logger.info("Repository processed successfully", 
                           processed_files=processed_count, 
                           skipped_files=skipped_count,
                           total_files=len(files))
                return files
        except Exception as e:
            logger.error("Failed to clone GitHub repository", repo_url=repo_url, error=str(e), error_type=type(e).__name__)
            raise Exception(f"Failed to analyze GitHub repository: {str(e)}")

    @staticmethod
    async def upload_from_gitlab(repo_url: str) -> List[UploadedFile]:
        """Clone and upload from GitLab repository (similar to GitHub)"""
        # GitLab URLs work the same way for cloning
        return await CodeUploader.upload_from_github(repo_url)


coverage_service = CoverageAnalyzer()
uploader_service = CodeUploader()