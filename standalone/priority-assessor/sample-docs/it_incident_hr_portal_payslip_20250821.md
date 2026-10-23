# IT Incident Report

**Incident ID:** INC-2025-0821-017  
**Date/Time:** 21.08.2025 14:13 UTC  
**Reported By:** Service Desk Analyst — Joel Okonkwo  
**System:** Employee HR Self-Service Portal  

## Incident Summary

Three employees in the Finance department have reported that the "View Payslip"
function on the HR self-service portal returns a blank page after clicking the link.
All three are using the Chrome browser on Windows 11. The portal home page and other
functions (leave requests, benefits enrolment) load normally.

## Impact Assessment

- **Users affected:** 3 confirmed; potentially all Finance department users
  (approximately 45 employees) if the issue is role-based.
- **Revenue impact:** None directly; payslip viewing is informational only.
- **Workaround available:** HR can email payslip PDF on request.
- **Duration:** First report received at 13:50 UTC today.

## Technical Details

The HR portal (version 6.4.1) was updated last night at 22:00 UTC. Release notes
for v6.4.1 include a change to the PDF rendering engine for payslips. No other
functions were modified. Server error logs show a `NullPointerException` in
`PayslipRenderer.renderPDF()` when user role = `FINANCE_READ`.

## Actions Taken

- Ticket escalated to Application Support Team at 14:20 UTC.
- Affected users notified of the workaround (HR email request).

## Open Items

1. Application Support to investigate `PayslipRenderer.renderPDF()` for Finance role.
2. If fix is not available within 8 hours, consider rolling back to v6.4.0.

**Reported by:** Joel Okonkwo  
**Incident Date:** 21.08.2025  
