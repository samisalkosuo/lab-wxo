# IT Incident Report

**Incident ID:** INC-2025-0715-001  
**Date/Time:** 15.07.2025 02:47 UTC  
**Reported By:** On-Call Engineer — Priya Nair  
**System:** Core Banking Platform — Payment Processing Module  

## Incident Summary

At 02:47 UTC, automated monitoring triggered a P1 alert: the payment processing
service (PayCore v4.2) became completely unresponsive. All transaction processing
has stopped. Affected systems: retail POS integration, mobile banking payment flows,
and corporate wire transfer scheduling.

## Impact Assessment

- **Users affected:** All retail and corporate banking customers — estimated 1.2 million
  active accounts.
- **Revenue impact:** Approximately €85,000 per hour in unprocessed transactions.
- **Duration:** Incident ongoing; 47 minutes unresolved at time of report.
- **SLA breach:** P1 SLA requires resolution within 1 hour; breach threshold reached
  at 03:47 UTC.

## Technical Details

Logs show the database connection pool for `paycore-db-primary` exhausted at 02:44 UTC.
Connection pool size is set to 200; all connections are in WAIT state. Database CPU is
at 98%. No deployment was made in the 6 hours preceding the incident. A batch job
`MONTH_END_RECONCILE` was scheduled at 02:30 UTC — suspected trigger.

## Actions Taken

- On-call DBA engaged at 02:52 UTC.
- Incident bridge open with 6 engineers.
- Considered killing the reconciliation batch job to release DB load.

## Open Items

1. Kill batch job `MONTH_END_RECONCILE` immediately to restore connection pool.
2. Validate transaction state after recovery to ensure no data loss.
3. Conduct post-incident review of batch scheduling policy.

**Reported by:** Priya Nair  
**Incident Date:** 15.07.2025  
