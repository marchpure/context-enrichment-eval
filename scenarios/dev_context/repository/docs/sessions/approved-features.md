# Synthetic feature decision session — 2026-11-05
09:00 Proposed tracing on every request in every lane. REJECTED.
09:10 APPROVED: opt-in trace=True emits X-Lane with the current lane name only for alpha. beta does not support this feature, even with trace=True. trace=False emits no transport-generated X-Lane in either lane. Caller headers must not be mutated. This is diagnostic metadata, not an authorization token.
09:20 Proposed automatically sleeping for every Retry-After header on every response. REJECTED.
09:30 APPROVED: when an otherwise retryable 429 response has an integer Retry-After from 0 through 8 inclusive and another attempt is permitted, invoke the injected sleeper with that number before the next attempt. Ignore invalid/out-of-range values, HTTP-date forms, and Retry-After on 503. Do not sleep if the method cannot retry or its attempt cap is already reached. No extra policy was approved for future beta-specific tracing.
