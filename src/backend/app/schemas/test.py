from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TestMetadata(BaseModel):
    """Metadata for test generation"""
    feature: Optional[str] = None
    story: Optional[str] = None
    owner: Optional[str] = None
    severity: str = "normal"
    tags: List[str] = []


class ManualTestRequest(BaseModel):
    """Request for manual test generation"""
    requirements: str = Field(..., min_length=3, max_length=10000)
    metadata: Optional[TestMetadata] = None


class TestCase(BaseModel):
    """Individual test case"""
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    steps: List[str]
    expected_result: str
    priority: str = "normal"
    tags: List[str] = []


class ValidationResult(BaseModel):
    """Validation result for generated code"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []


class GeneratedTestResponse(BaseModel):
    """Response for test generation"""
    code: str
    test_cases: List[TestCase]
    validation: ValidationResult
    generation_time: float  # in seconds
    metadata: Optional[TestMetadata] = None


class ManualTestResponse(GeneratedTestResponse):
    """Response for manual test generation (alias of GeneratedTestResponse)."""
    pass


class ApiTestRequest(BaseModel):
    """Request for API test generation"""
    openapi_spec: str = Field(..., min_length=1)
    endpoint_filter: Optional[List[str]] = None
    test_types: List[str] = ["happy_path", "negative"]
    include_validation: bool = True


class ApiTestResponse(BaseModel):
    """Response for API test generation"""
    code: str
    endpoints_covered: List[str]
    test_matrix: Dict[str, List[str]]
    coverage_percentage: float
    validation: ValidationResult


class DuplicateSearchRequest(BaseModel):
    """Request for duplicate search"""
    test_cases: List[TestCase]
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class SimilarTestCase(BaseModel):
    """Similar test case found"""
    id: int
    title: str
    similarity_score: float


class DuplicateGroup(BaseModel):
    """Group of duplicate test cases"""
    group_id: str
    test_cases: List[SimilarTestCase]
    similarity_score: float


class DuplicateSearchResponse(BaseModel):
    """Response for duplicate search"""
    duplicates: List[DuplicateGroup]
    total_tests: int
    duplicates_found: int
    similarity_matrix: Optional[Dict[str, Dict[str, float]]] = None


class ValidationRequest(BaseModel):
    """Request for code validation"""
    code: str = Field(..., min_length=1)
    standards: List[str] = ["allure"]
    strict_mode: bool = False


class ValidationResponse(BaseModel):
    """Response for code validation"""
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    suggestions: List[str]
    metrics: Dict[str, Any]


class GitLabProject(BaseModel):
    """GitLab project representation"""
    id: int
    name: str
    path_with_namespace: str
    web_url: str
    default_branch: str


class CreateMRRequest(BaseModel):
    """Request to create Merge Request"""
    project_id: int
    branch_name: str = Field(..., min_length=1, max_length=255)
    commit_message: str = Field(..., min_length=1, max_length=1000)
    files: Dict[str, str]  # path -> content
    title: Optional[str] = None
    description: Optional[str] = None


class CreateMRResponse(BaseModel):
    """Response for created Merge Request"""
    mr_url: str
    mr_id: int
    web_url: str
    status: str
    merge_status: str


class ChatMessage(BaseModel):
    """Chat message"""
    id: Optional[str] = None
    type: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatHistory(BaseModel):
    """Chat history"""
    messages: List[ChatMessage]
    total_messages: int
    last_updated: datetime


class OptimizationResult(BaseModel):
    """Result of code optimization"""
    original_code: str
    optimized_code: str
    fixes_applied: List[str]
    improvements: List[str]
    metrics_before: Dict[str, Any]
    metrics_after: Dict[str, Any]
    improvement_score: float  # 0-1