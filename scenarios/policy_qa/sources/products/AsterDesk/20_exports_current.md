# AsterDesk export lifecycle policy — APPROVED, effective 2026-11-01
This document owns the export object clocks. Shared portfolio access-and-export policy owns authorization and audit guards. Both must be satisfied; this document does not replace the shared gate checklist.

## Current clocks
Download URL validity is 28 elapsed hours after issuance. Export archives are retained for 5 elapsed days after creation. The clocks are independent. An expired URL cannot be used merely because the archive remains in storage. Reissue requires fresh authorization and approval; the old URL is not revived.

## Full-workspace export
Workspace-admin role, ACL permission on every selected document, and security approval are all required. EU personal data additionally requires DPO approval. The audit service must be available. A support-plan exception does not bypass any of these conditions. If one document is denied, do not claim that an all-workspace export is authorized; a differently scoped operation requires a new explicit request.

## Operational failure handling
On audit outage, do not issue the full-export link. Preserve a denial reason without storing the selected document bodies in the incident ticket. When the service recovers, revalidate ACLs, tombstones and approvals. Record issuance time for the new URL and creation time for the archive separately. Retries must not reset archive retention by pretending an old archive is new.

## Unsupported promises
This sheet does not set a bulk-export tariff, reimburse an incident or guarantee exact job completion time. Draft requests for longer links are not approved clocks. For deletion and legal holds, use the product lifecycle sheet and shared invariants.
