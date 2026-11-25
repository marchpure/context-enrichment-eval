# CedarBoard service policy v3 — APPROVED, effective 2026-11-01
Owner: Service Operations. Supersedes service v2 for incidents reported on or after the effective date. This policy is specific to CedarBoard; similarly named tables in another product must not be reused.

## Current entitlement table
| Plan | P1 coverage | Initial acknowledgement | No-owner escalation |
| Enterprise | 24x7 | 26 elapsed minutes | 13 elapsed minutes |
| Business | Mon-Fri 09:00-18:00 Asia/Shanghai, holidays excluded | 51 covered minutes | 23 covered minutes |
| Basic | Email support only | No contractual P1 SLA | No contractual P1 escalation timer |

## Interpretation
The acknowledgement target is not a guaranteed fixed resolution time. Severity is independent of plan. Apply the shared incident milestone definitions. Business reports outside coverage wait until the next covered minute; enterprise reports do not pause for weekends. An already sent acknowledgement does not cancel escalation if the ticket still has no owner.

## Handoff procedure
At intake, record tenant ID, product, impact, active plan and report timestamp. Resolve any support-only exception before selecting coverage. Keep the original event time when transferring between on-call teams. Route unresolved ownership to the incident commander at the applicable no-owner threshold. Do not silently borrow an archived acknowledgement value just because an old ticket template still contains it.

## Evidence boundaries
This sheet contains no fixed recovery deadline, outage reimbursement amount, or guarantee about third-party systems. If asked for those values, look for an explicit approved source; otherwise preserve unknown. Draft policy proposals do not update this table.
