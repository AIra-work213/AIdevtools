import yaml
import json
from typing import Dict, List, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class OpenAPIParser:
    """Parser for OpenAPI specifications"""

    def __init__(self):
        self.logger = logger.bind(parser="OpenAPIParser")

    async def parse(self, spec: str, format: str = "yaml") -> Dict[str, Any]:
        """
        Parse OpenAPI specification from string
        """
        try:
            if format.lower() == "yaml":
                data = yaml.safe_load(spec)
            elif format.lower() == "json":
                data = json.loads(spec)
            else:
                # Try to auto-detect format
                try:
                    data = yaml.safe_load(spec)
                except:
                    data = json.loads(spec)

            # Normalize to OpenAPI 3.0 format
            normalized = self._normalize_spec(data)

            # Extract endpoints
            endpoints = self._extract_endpoints(normalized)

            self.logger.info(
                "Parsed OpenAPI specification",
                version=normalized.get("openapi", "unknown"),
                endpoints_count=len(endpoints),
                title=normalized.get("info", {}).get("title")
            )

            return {
                "info": normalized.get("info", {}),
                "servers": normalized.get("servers", []),
                "endpoints": endpoints,
                "schemas": self._extract_schemas(normalized)
            }

        except Exception as e:
            self.logger.error("Failed to parse OpenAPI spec", error=str(e))
            raise

    def _normalize_spec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OpenAPI spec to 3.0 format"""
        # Handle Swagger 2.0 conversion
        if "swagger" in data:
            return self._convert_swagger_to_openapi(data)
        return data

    def _convert_swagger_to_openapi(self, swagger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Swagger 2.0 to OpenAPI 3.0"""
        # Basic conversion - can be expanded
        openapi_data = {
            "openapi": "3.0.0",
            "info": swagger_data.get("info", {}),
            "servers": [{"url": swagger_data.get("host", "localhost")}],
            "paths": swagger_data.get("paths", {})
        }

        # Convert schemes
        if "schemes" in swagger_data:
            base_url = "://".join([
                swagger_data.get("schemes", ["http"])[0],
                swagger_data.get("host", "localhost"),
                swagger_data.get("basePath", "")
            ])
            openapi_data["servers"] = [{"url": base_url}]

        return openapi_data

    def _extract_endpoints(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all endpoints from OpenAPI spec"""
        endpoints = []
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "operation_id": operation.get("operationId"),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "tags": operation.get("tags", []),
                        "parameters": self._extract_parameters(operation),
                        "request_body": self._extract_request_body(operation),
                        "responses": operation.get("responses", {}),
                        "security": operation.get("security", [])
                    }

                    # Extract examples
                    if "examples" in operation:
                        endpoint["examples"] = operation["examples"]

                    endpoints.append(endpoint)

        return endpoints

    def _extract_parameters(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract parameters from operation"""
        parameters = []

        # Parameters in operation
        if "parameters" in operation:
            for param in operation["parameters"]:
                parameters.append({
                    "name": param["name"],
                    "in": param["in"],  # path, query, header, cookie
                    "required": param.get("required", False),
                    "type": param.get("type"),
                    "schema": param.get("schema"),
                    "description": param.get("description", "")
                })

        # Parameters from request body schema
        if "requestBody" in operation:
            request_body = operation["requestBody"]
            if "content" in request_body:
                for media_type, media_obj in request_body["content"].items():
                    if "schema" in media_obj:
                        schema = media_obj["schema"]
                        if "properties" in schema:
                            for prop_name, prop_schema in schema["properties"].items():
                                parameters.append({
                                    "name": prop_name,
                                    "in": "body",
                                    "required": prop_name in schema.get("required", []),
                                    "type": prop_schema.get("type"),
                                    "schema": prop_schema,
                                    "description": prop_schema.get("description", "")
                                })

        return parameters

    def _extract_request_body(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract request body from operation"""
        if "requestBody" in operation:
            return operation["requestBody"]
        return None

    def _extract_schemas(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all schemas from spec"""
        schemas = {}

        # OpenAPI 3.0
        if "components" in spec and "schemas" in spec["components"]:
            schemas = spec["components"]["schemas"]
        # Swagger 2.0
        elif "definitions" in spec:
            schemas = spec["definitions"]

        return schemas

    def generate_test_scenarios(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test scenarios for an endpoint"""
        scenarios = []
        method = endpoint["method"]
        parameters = endpoint.get("parameters", [])

        # Happy path scenario
        scenarios.append({
            "name": f"{method} {endpoint['path']} - Success",
            "type": "happy_path",
            "description": f"Successful {method} request to {endpoint['path']}",
            "request_data": self._generate_sample_request(endpoint),
            "expected_status": self._get_success_status(method),
            "expected_response": {"status": "success"}
        })

        # Negative scenarios
        if method in ["POST", "PUT", "PATCH"]:
            # Invalid request body
            scenarios.append({
                "name": f"{method} {endpoint['path']} - Invalid data",
                "type": "negative",
                "description": f"Request with invalid data to {endpoint['path']}",
                "request_data": {"invalid": "data"},
                "expected_status": 400,
                "expected_response": {"error": "Bad Request"}
            })

        # Missing required parameters
        required_params = [p for p in parameters if p.get("required", False)]
        if required_params:
            scenarios.append({
                "name": f"{method} {endpoint['path']} - Missing required params",
                "type": "negative",
                "description": f"Request missing required parameters to {endpoint['path']}",
                "request_data": {},
                "expected_status": 400,
                "expected_response": {"error": "Missing required parameters"}
            })

        # Authentication scenarios
        if endpoint.get("security"):
            scenarios.append({
                "name": f"{method} {endpoint['path']} - Unauthorized",
                "type": "negative",
                "description": f"Request without authentication to {endpoint['path']}",
                "request_data": {},
                "expected_status": 401,
                "expected_response": {"error": "Unauthorized"}
            })

        return scenarios

    def _generate_sample_request(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sample request data for endpoint"""
        request_body = endpoint.get("request_body")
        if not request_body:
            return {}

        # Try to extract sample from examples
        if "content" in request_body:
            for media_type, content in request_body["content"].items():
                if "example" in content:
                    return content["example"]
                if "examples" in content:
                    # Take first example
                    example_key = list(content["examples"].keys())[0]
                    if "value" in content["examples"][example_key]:
                        return content["examples"][example_key]["value"]

        return {"sample": "data"}

    def _get_success_status(self, method: str) -> int:
        """Get expected success status for HTTP method"""
        status_map = {
            "GET": 200,
            "POST": 201,
            "PUT": 200,
            "PATCH": 200,
            "DELETE": 204
        }
        return status_map.get(method, 200)