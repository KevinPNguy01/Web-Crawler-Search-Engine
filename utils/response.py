import pickle

class RawResponse(object):
    def __init__(self, url, content):
        self.url = url
        self.content = content

class Response(object):
    def __init__(self, resp_headers_dict, resp_dict):
        self.url = resp_dict["url"]
        self.status = resp_dict["status"]
        self.error = resp_dict["error"] if "error" in resp_dict else None
        self.headers = resp_headers_dict
        try:
            self.raw_response = (
                pickle.loads(resp_dict["response"])
                if "response" in resp_dict else
                None)
        except TypeError:
            self.raw_response = RawResponse(resp_dict["response"]["url"], resp_dict["response"]["content"])