from .profiles import PROFILES
from . import preparation

class Client:
    def __init__(self, transport, lane="alpha"):
        self.transport = transport
        self.lane = lane

    def request(self, method, url, *, headers=None, params=None, timeout=None, body=None, trace=False):
        profile = PROFILES["alpha"]
        prepared = {"headers": preparation.headers(headers), "query": preparation.query(params)}
        return self.transport.send(method, url, prepared=prepared, profile=profile, lane=self.lane, timeout=timeout, body=body, trace=trace)

    def fetch(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def submit(self, url, **kwargs):
        return self.request("POST", url, **kwargs)
