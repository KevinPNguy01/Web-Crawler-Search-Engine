import pickle
from typing import Dict

class RawResponse(object):
    def __init__(self, url: str, content: bytes):
        self.url = url
        self.content = content

class Response(object):
    def __init__(self, resp_dict):
        self.url = resp_dict["url"]
        self.status = resp_dict["status"]
        self.error = resp_dict["error"] if "error" in resp_dict else None
        try:
            self.raw_response: RawResponse = (
                pickle.loads(resp_dict["response"]) if "response" in resp_dict else None
            )
        except TypeError:
            self.raw_response = RawResponse(resp_dict["response"]["url"], resp_dict["response"]["content"])