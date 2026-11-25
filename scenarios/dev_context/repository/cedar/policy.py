from urllib.parse import urlsplit

def retryable(method, status):
    return status in (429, 503)

def redirect_headers(headers, source, target):
    result = dict(headers)
    if urlsplit(source).hostname != urlsplit(target).hostname:
        result.pop("Authorization", None)
    return result
