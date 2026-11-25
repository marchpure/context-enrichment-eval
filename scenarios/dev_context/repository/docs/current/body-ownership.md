# Stream ownership and replay — APPROVED
The caller owns any body stream passed through Client. The transport may read it but must not close it, on success or failure. The same rule holds for every client entry point.
For retryable requests with a seekable stream, each replay starts at the stream position captured before the first attempt, not necessarily byte zero. Rewinding is relative to this request's starting position. The transport's body bytes must be identical on all attempts. These replay rules do not grant permission to retry POST or other unsafe methods.
