# BorealDocs deletion and retention v3 — APPROVED, effective 2026-11-01
The following durations are specific to this product. They do not inherit numeric defaults from another product with the same feature names.

## Operative durations
Trash restore period: 16 elapsed days. Audit-event retention: 140 elapsed days. Search-index deletion service target: 6 elapsed minutes. Tombstoned bodies are denied immediately by retrieval, even before that index target has elapsed.

## Restore decision
After the ordinary restore period expires, an audit event cannot reconstruct the document body. Active legal hold suspends physical purge, but never grants a read permission or automatically makes tombstoned content retrievable. On hold release, use the original deletion time to resume purge eligibility. Do not promise a fresh full restore period.

## Operational procedure
Check tombstone, original deletion time, applicable hold, caller ACL and policy version separately. A stale search-index hit is not an authorization. When restoration is allowed, re-evaluate the current ACL before the item can be returned. Record restore or denial as an audit event; an audit event is metadata about an operation, not a backup of its body.

## Export distinction
Export-link expiry and archive retention are defined in the export policy and are not the trash restore period. A retained exported archive does not automatically restore a deleted source document. A customer's request for incident escalation does not by itself create a legal hold. Archived lifecycle guidance must not override these active durations.
