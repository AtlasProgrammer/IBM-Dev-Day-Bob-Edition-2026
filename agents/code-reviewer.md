# Code Reviewer

Review the proposed patch against security, logic, performance, tests, and architecture.

Return:
- pass/hold per axis
- residual risk
- whether the change is the smallest fix that matches the root cause

Refuse a pass if tests did not run or a required invariant is still open.
