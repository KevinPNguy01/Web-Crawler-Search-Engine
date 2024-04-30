import requests
import cbor
import time

from utils.response import Response

def download(url, config, logger=None) -> Response:
    host, port = config.cache_server
    resp = requests.get(
        f"http://{host}:{port}/",
        params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
        timeout=5
    )
    try:
        if resp and resp.content:
            return Response(cbor.loads(resp.content))
    except (EOFError, ValueError):
        error_message = f"Spacetime Response error {resp} with url {url}."
    except TimeoutError:
        error_message = f"Timeout error with url {url}."
    except Exception as e:
        error_message = f"{type(e).__name__} with url {url}: {e}."
    logger.error(error_message)
    return Response({
        "error": error_message,
        "status": resp.status_code,
        "url": url,
        "response": {"content": b'', "url": url}
    })

def download2(url, config, logger=None) -> Response:
    resp = requests.get(url, timeout=5)
    if resp and resp.content:
        return Response({
            "url": url,
            "status": resp.status_code,
            "error": resp.reason,
            "response": {"content": resp.content, "url": resp.url}
        })
    return Response({
        "url": url,
        "status": 404,
        "error": "Response is None.",
        "response": {"content": b'', "url": url}
    })
        
def download3(url: str, config, logger=None) -> Response:
    url = url.lstrip("https://").lstrip("http://")
    resp = requests.get(
        f"http://localhost:54321/{url}",
        timeout=5
    )
    if resp and resp.content:
        return Response({
            "url": url,
            "status": resp.status_code,
            "error": resp.reason,
            "response": {"content": resp.content, "url": resp.url.replace('localhost:54321/', '')}
        })
    return Response({
        "url": url,
        "status": 404,
        "error": "Response is None.",
        "response": {"content": b'', "url": url}
    })
    
download = download