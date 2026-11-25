def position(body):
    if hasattr(body, "tell"):
        return body.tell()
    return None

def read(body):
    return body.read() if hasattr(body, "read") else body

def rewind(body, initial):
    if initial is not None:
        body.seek(0)

def release(body):
    if hasattr(body, "close"):
        body.close()
