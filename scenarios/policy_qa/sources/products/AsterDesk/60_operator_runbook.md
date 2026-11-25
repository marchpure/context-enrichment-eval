# AsterDesk operator handoff and escalation runbook — APPROVED procedure
This runbook explains execution order. Numeric entitlements remain in the product's effective service, export, lifecycle and price sheets. Do not replace those sheets with a summary in a support ticket.

## Support intake
Confirm AsterDesk as the product and use the stable tenant ID. Identify incident time and current subscription. Check for a narrowly scoped approved support exception in the decision transcript. Select coverage and timers from the active service table, then record acknowledgement and owner separately. Acknowledgement alone does not clear a no-owner escalation.

## Export triage
Record selected document set, workspace role, document ACLs, data class, region and approval IDs. Apply shared mandatory gates before interpreting export clocks. If audit is unavailable, deny full export. If one ACL is denied, a workspace-admin role does not override it. If the URL expired, archive retention does not revive it. A fresh URL requires a fresh decision.

## Deletion triage
Block tombstoned content immediately. Inspect the active restore period and an actual legal-hold record. Do not treat an audit event as a content backup. Do not infer a hold from an incident commander escalation. Record source policy and original deletion time so later reviewers can reproduce the decision.

## Commercial triage
Identify the billing meter and unit. A per-1,000 page overage rate is not a flat fee or an export tariff. If Finance has not approved the requested rate, say it is unknown rather than borrowing a nearby product's rate. Preserve the distinction between an approved decision, a proposal and an action item.

## Review checklist
Check product, tenant, incident date, effective version, required permission, clock meaning, and unresolved items. Include source links in the handoff. A reviewer should be able to explain why the decision differs from a visually similar ticket in another product. This procedure itself does not introduce a new SLA, retention period, price, certification or resolution guarantee.
