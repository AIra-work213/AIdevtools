import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import structlog
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)


class CloudEvolutionClient:
    """Client for Cloud.ru Evolution Foundation Model API"""

    def __init__(self, api_key: str, base_url: str = "https://foundation-models.api.cloud.ru/v1"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = "Qwen/Qwen3-Coder-480B-A35B-Instruct"
        self.logger = logger.bind(service="CloudEvolutionClient")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000,
        temperature: float = 0.3,
        stream: bool = False,
        **kwargs
    ) -> str | AsyncGenerator:
        """
        Send chat completion request to Cloud.ru Evolution API
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "presence_penalty": 0,
                "top_p": 0.95,
                **kwargs
            }

            self.logger.info(
                "Sending chat completion request",
                model=self.model,
                messages_count=len(messages),
                max_tokens=max_tokens,
                temperature=temperature
            )

            if stream:
                return self._stream_response(params)
            else:
                response = await self.client.chat.completions.create(**params)
                content = response.choices[0].message.content
                self.logger.info("Received chat completion response", tokens=len(content or ""))
                return content or ""

        except Exception as e:
            self.logger.error("Chat completion request failed", error=str(e))
            raise

    async def _stream_response(self, params: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream response from the API"""
        stream = await self.client.chat.completions.create(**params, stream=True)

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get text embedding for semantic search
        Note: This might require a different model or endpoint
        """
        # TODO: Implement actual embedding from Cloud.ru or use alternative
        # For now, we'll use a mock implementation
        import hashlib
        hash_object = hashlib.md5(text.encode())
        hex_dig = hash_object.hexdigest()

        # Convert hash to a simple embedding vector (384 dimensions like sentence-transformers)
        embedding = []
        for i in range(0, len(hex_dig), 2):
            byte_val = int(hex_dig[i:i+2], 16)
            normalized = (byte_val - 128) / 128.0  # Normalize to [-1, 1]
            embedding.extend([normalized] * 6)  # Repeat to get 384 dims

        return embedding[:384]

    async def analyze_code(
        self,
        code: str,
        analysis_type: str = "validation"
    ) -> Dict[str, Any]:
        """
        Analyze Python code for various purposes
        """
        system_prompt = """
        You are an expert Python code analyzer specializing in test automation.
        Analyze the provided code and return a detailed analysis.
        """

        user_prompt = f"""
        Analyze the following Python test code:

        ```python
        {code}
        ```

        Provide analysis for:
        1. Code quality and structure
        2. Adherence to testing standards
        3. Potential issues or improvements
        4. Best practices compliance

        Return your analysis in JSON format.
        """

        try:
            response = await self.chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], temperature=0.1)

            # TODO: Parse JSON response
            return {
                "analysis": response,
                "score": 0.9,  # Mock score
                "issues": [],
                "suggestions": []
            }

        except Exception as e:
            self.logger.error("Code analysis failed", error=str(e))
            raise

    async def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured response following given schema
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add schema guidance to user prompt
        schema_guided_prompt = f"""
        CRITICAL: Your response MUST follow this exact JSON schema:
        ```json
        {schema}
        ```

        Your entire response should be valid JSON that conforms to this schema.
        Do not include any text outside the JSON structure.

        User Request:
        {prompt}

        Provide your response:
        """

        messages.append({"role": "user", "content": schema_guided_prompt})

        try:
            response = await self.chat_completion(
                messages=messages,
                temperature=0.3
            )

            # Parse JSON from response
            import json
            try:
                # Extract JSON from response (in case there's extra text)
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_content = response[start:end]
                    return json.loads(json_content)
                else:
                    self.logger.warning("No JSON found in schema-guided response")
                    return {"error": "No valid JSON found", "raw_response": response}
            except json.JSONDecodeError as e:
                self.logger.error("Failed to parse JSON response", error=str(e))
                return {"error": "Invalid JSON", "raw_response": response}

        except Exception as e:
            self.logger.error("Schema-guided generation failed", error=str(e))
            raise