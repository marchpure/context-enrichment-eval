# Transport contract — APPROVED, revision 5
Client lane selects the matching PROFILES entry at request time. A caller timeout override (scalar or connect/read tuple) is propagated unchanged to every attempt and redirect. None selects the lane default. Do not hardcode either lane's values.
Only GET and HEAD retry 429/503 automatically. Other methods do not retry status failures. A profile max_attempts is the total number of attempts, including the first. Never exceed the profile cap. Status 500 is not retryable. Redirects remain subject to this total cap and credential-isolation rules.
