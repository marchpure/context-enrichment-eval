# Portfolio lifecycle invariants — APPROVED
Effective 2026-10-01. Product tables define actual durations; this document defines the meanings of those durations.

## Immediate denial and eventual cleanup
A tombstoned document must be rejected by retrieval immediately. Search-index cleanup is asynchronous; a cleanup service target is not a grace period to continue returning the body. After restoring an eligible trash item, the system must re-evaluate current ACLs before indexing the restored document. A stale search hit must not resurrect deleted content.

## Trash, purge, audit and hold
The trash restore period measures body restorability. Audit retention measures event availability. Audit events cannot reconstruct a purged body. After the product restore period has elapsed, the ordinary restore endpoint cannot restore the body. A legal hold suspends physical purge while active, but does not automatically make a trash item visible to retrieval, and does not grant a user a restore permission.

## Export objects are separate
Download-link validity and archive retention are independent clocks. Link expiry does not prove that the archive has already been removed. An archive still being retained does not make an expired URL valid. Reissuing a link requires a new permission and approval evaluation; never prolong an old URL simply by reading it. Revoking an entitlement does not erase the product audit record.

## Release of legal hold
Releasing a hold lets normal purge eligibility resume; it does not promise a new full restore period. Record which policy and original deletion time are used. A downstream cache must honor the immediate tombstone even before scheduled garbage collection completes. Do not infer a hold from a customer escalation, incident severity or support plan.
