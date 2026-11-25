from urllib.parse import urlencode
from .profiles import DEFAULT_HEADERS, DEFAULT_QUERY

def headers(overrides):
    merged = DEFAULT_HEADERS
    merged.update(overrides or {})
    return merged

def query(overrides):
    merged = dict(DEFAULT_QUERY)
    merged.update(overrides or {})
    return urlencode(merged)
