import requests
from web_crawler.utils.response import Response

def download(url) -> Response:
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