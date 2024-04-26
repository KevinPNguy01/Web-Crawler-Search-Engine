import requests
import cbor
import time

from utils.response import Response

def download(url, config, logger=None) -> Response:
    host, port = config.cache_server
    try:
        resp = requests.get(
            f"http://{host}:{port}/",
            params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
            timeout=5
        )
        if resp and resp.content:
            return Response(resp.headers, cbor.loads(resp.content))
    except (EOFError, ValueError):
        logger.error(f"Spacetime Response error {resp} with url {url}.")
        return Response({}, {
            "error": f"Spacetime Response error {resp} with url {url}.",
            "status": resp.status_code,
            "url": url})
    except TimeoutError:
        logger.error(f"Timeout error with url {url}.")
        return Response({}, {
            "error": f"Timeout error with url {url}.",
            "status": 408,
            "url": url})

def download2(url, config, logger=None) -> Response:
    try:
        resp = requests.get(url, timeout=5)
        if resp and resp.content:
            return Response(resp.headers, {
                "url": url,
                "status": resp.status_code,
                "error": resp.reason,
                "response": {"content": resp.content, "url": resp.url}
            })
    except (EOFError, ValueError):
        logger.error(f"Spacetime Response error {resp} with url {url}.")
        return Response({}, {
            "error": f"Spacetime Response error {resp} with url {url}.",
            "status": resp.status_code,
            "url": resp.url})
    except TimeoutError:
        logger.error(f"Timeout error with url {url}.")
        return Response({}, {
            "error": f"Timeout error with url {url}.",
            "status": 408,
            "url": resp.url})
        
def download3(url: str, config, logger=None) -> Response:
    try:
        url = url.lstrip("https://").lstrip("http://")
        try:
            resp = requests.get(
                f"http://localhost:54321/{url}",
                timeout=5
            )
        except:
            resp = requests.get(
                    f"http://localhost:54321/{url}.html",
                    timeout=5
                )
        if resp and resp.content:
            return Response(resp.headers, {
                "url": url.replace('localhost:54321/', ''),
                "status": resp.status_code,
                "error": resp.reason,
                "response": {"content": resp.content, "url": resp.url.replace('localhost:54321/', '')}
            })
    except (EOFError, ValueError):
        logger.error(f"Spacetime Response error {resp} with url {url.replace('localhost:54321/', '')}.")
        return Response({}, {
            "error": f"Spacetime Response error {resp} with url {url.replace('localhost:54321/', '')}.",
            "status": resp.status_code,
            "url": resp.url.replace('localhost:54321/', '')})
    except TimeoutError:
        logger.error(f"Timeout error with url {url.replace('localhost:54321/', '')}.")
        return Response({}, {
            "error": f"Timeout error with url {url.replace('localhost:54321/', '')}.",
            "status": 408,
            "url": resp.url.replace('localhost:54321/', '')})
    
download = download3