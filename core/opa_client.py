import httpx
from typing import Any, Dict

from core.config import config


async def opa_check(input_data: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{config.opa.URL}/v1/data/authz/allow"
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(url, json={"input": input_data})
        response.raise_for_status()
        return response.json()


