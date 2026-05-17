import httpx
import config


def _base_url() -> str:
    return f"http://{config.ANDROID_IP}:{config.ANDROID_PORT}"


async def proxy_get(path: str) -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.get(path)
        r.raise_for_status()
        return r.json()


async def proxy_post(path: str, json: dict | None = None) -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.post(path, json=json)
        r.raise_for_status()
        return r.json()


async def proxy_post_file(path: str, filename: str, data: bytes) -> dict:
    files = {"file": (filename, data, "application/octet-stream")}
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.post(path, files=files)
        r.raise_for_status()
        return r.json()
