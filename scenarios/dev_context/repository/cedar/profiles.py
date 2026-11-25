PROFILES = {
    "alpha": {"timeout": (1.75, 23.5), "max_attempts": 4},
    "beta": {"timeout": (4.25, 41.0), "max_attempts": 2},
}
DEFAULT_HEADERS = {"X-Client": "cedar/28", "X-Mode": "stable", "X-Remove": "old"}
DEFAULT_QUERY = {"workspace": "cedar", "page": "old"}
