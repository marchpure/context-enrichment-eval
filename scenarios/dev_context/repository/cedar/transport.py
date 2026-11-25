from . import policy, body as bodies

class Transport:
    def __init__(self, adapter, sleeper=lambda seconds: None):
        self.adapter = adapter
        self.sleeper = sleeper

    def send(self, method, url, *, prepared, profile, lane, timeout=None, body=None, trace=False):
        headers = dict(prepared["headers"])
        initial = bodies.position(body)
        try:
            for attempt in range(3):
                if attempt:
                    bodies.rewind(body, initial)
                response = self.adapter.request(method, url, headers=dict(headers), query=prepared["query"], timeout=profile["timeout"], body=bodies.read(body))
                if response.status in (301, 302, 307, 308) and response.location:
                    headers = policy.redirect_headers(headers, url, response.location)
                    url = response.location
                    continue
                if policy.retryable(method, response.status) and attempt < 2:
                    continue
                return response
            return response
        finally:
            bodies.release(body)
