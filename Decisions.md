# Architectural Decisions & Edge Case Audit

## Edge Cases Identified & Handled
1. **Landlines Recorded as Mobile:** Numbers matching `555-2xx` were handled as landlines to prevent dropped SMS attempts.
2. **Channel Fallbacks:** Sequence routes SMS -> Voice -> Email, stopping upon successful delivery or non-recoverable block.
3. **Quiet Hours & Opt-outs:** Hard-enforced inside wrapper classes to restrict invalid sending calls.
4. **Missing Languages:** Defaulted unmapped language preferences to English while tracking metric counts.