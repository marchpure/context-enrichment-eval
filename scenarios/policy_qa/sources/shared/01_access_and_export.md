# Portfolio identity and data-operation gates — APPROVED
Effective 2026-10-01, owner: Security Operations. Applies to every product unless an exception explicitly names the rule it replaces.

## Workspace exports
Full-workspace export requires workspace-admin role, permission on every selected document, and a security approval for that operation. An administrator cannot override a denied document ACL. A security approval alone does not grant an ACL. A support-plan upgrade alone does not grant the workspace-admin role. Own-document exports by members remain bounded by the member's own effective ACLs.

## Audit availability
Full-workspace export fails closed if the audit service is unavailable. Do not issue a download URL and promise to backfill an audit event later. Retrying after service recovery must revalidate current permissions and approval. The exception process cannot bypass a denied document ACL; a tenant exemption must identify the specific gate being relaxed. No portfolio exception in this corpus relaxes the audit gate.

## EU personal data
For EU personal data, full-workspace export additionally needs a DPO approval, even when a security approval exists. Security and DPO approvals serve different purposes and are not substitutes. EU requests containing no personal data do not require this additional DPO approval under this rule. Product-specific retention windows still apply.

## API versus document permissions
An API token proves caller identity and allowed scopes, not entitlement to each selected document. Service accounts follow the same object checks. A successful background job creation is not proof that its eventual download can be authorized. Revalidate tombstones and document ACLs before returning content. Support staff can explain a denial without revealing the content or existence of a document the caller cannot access.
