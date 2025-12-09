import numpy as np
from typing import Any, Dict, List, Tuple
import structlog

from app.schemas.test import (
    TestCase,
    DuplicateGroup,
    SimilarTestCase
)
from app.core.logging import LoggerMixin

logger = structlog.get_logger(__name__)


class DuplicateService(LoggerMixin):
    """Service for finding duplicate test cases using semantic similarity"""

    def __init__(self):
        # Initialize encoder for semantic similarity
        self.encoder = None  # TODO: Initialize sentence transformer

    async def find_duplicates(
        self,
        test_cases: List[TestCase],
        threshold: float = 0.85
    ) -> List[DuplicateGroup]:
        """
        Find duplicate or similar test cases
        """
        if len(test_cases) < 2:
            return []

        # Extract text representations
        texts = [self._extract_text(test_case) for test_case in test_cases]

        # Generate embeddings
        embeddings = await self._generate_embeddings(texts)

        # Calculate similarity matrix
        similarity_matrix = self._compute_similarity_matrix(embeddings)

        # Find duplicate groups using clustering
        duplicate_groups = self._cluster_duplicates(
            test_cases, similarity_matrix, threshold
        )

        return duplicate_groups

    def build_similarity_matrix(
        self,
        test_cases: List[TestCase]
    ) -> Dict[str, Dict[str, float]]:
        """
        Build similarity matrix for all test pairs
        """
        if len(test_cases) > 100:
            # Too many tests for full matrix
            return {}

        texts = [self._extract_text(tc) for tc in test_cases]
        embeddings = self._generate_embeddings_sync(texts)
        similarity_matrix = self._compute_similarity_matrix(embeddings)

        # Convert to dict format
        matrix_dict = {}
        for i, test1 in enumerate(test_cases):
            matrix_dict[str(test1.id)] = {}
            for j, test2 in enumerate(test_cases):
                if i != j:
                    matrix_dict[str(test1.id)][str(test2.id)] = float(similarity_matrix[i][j])

        return matrix_dict

    def _extract_text(self, test_case: TestCase) -> str:
        """
        Extract text representation from test case for similarity comparison
        """
        # Combine title, description, and steps
        text_parts = [
            test_case.title,
            test_case.description or "",
            " ".join(test_case.steps),
            test_case.expected_result
        ]
        return " ".join(filter(None, text_parts))

    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for texts (async)
        """
        # TODO: Implement async embedding generation
        # For now, return dummy embeddings
        return np.random.rand(len(texts), 384)

    def _generate_embeddings_sync(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for texts (sync)
        """
        # TODO: Implement actual embedding generation
        # For now, return dummy embeddings
        return np.random.rand(len(texts), 384)

    def _compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity matrix
        """
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / norms

        # Compute similarity matrix
        similarity_matrix = np.dot(normalized, normalized.T)
        np.fill_diagonal(similarity_matrix, 0)  # Don't compare with self

        return similarity_matrix

    def _cluster_duplicates(
        self,
        test_cases: List[TestCase],
        similarity_matrix: np.ndarray,
        threshold: float
    ) -> List[DuplicateGroup]:
        """
        Cluster similar test cases into duplicate groups
        """
        n = len(test_cases)
        visited = [False] * n
        groups = []

        for i in range(n):
            if visited[i]:
                continue

            # Find all similar tests
            similar_indices = [i]
            for j in range(i + 1, n):
                if similarity_matrix[i][j] >= threshold:
                    similar_indices.append(j)

            if len(similar_indices) > 1:
                # Mark all as visited
                for idx in similar_indices:
                    visited[idx] = True

                # Create duplicate group
                group = self._create_duplicate_group(
                    test_cases, similar_indices, similarity_matrix
                )
                groups.append(group)

        return groups

    def _create_duplicate_group(
        self,
        test_cases: List[TestCase],
        indices: List[int],
        similarity_matrix: np.ndarray
    ) -> DuplicateGroup:
        """
        Create a duplicate group from indices
        """
        similar_tests = []
        max_similarity = 0.0

        for i, idx in enumerate(indices):
            test_case = test_cases[idx]

            # Find max similarity for this test
            test_similarities = []
            for j, other_idx in enumerate(indices):
                if i != j:
                    sim = similarity_matrix[idx][other_idx]
                    test_similarities.append(sim)
                    max_similarity = max(max_similarity, sim)

            similar_tests.append(SimilarTestCase(
                id=test_case.id or idx,
                title=test_case.title,
                similarity_score=float(np.mean(test_similarities)) if test_similarities else 1.0
            ))

        return DuplicateGroup(
            group_id=f"group_{len(similar_tests)}",
            test_cases=similar_tests,
            similarity_score=float(max_similarity)
        )


# Create singleton instance
duplicate_service = DuplicateService()