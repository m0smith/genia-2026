# Running a Genia Change

For every issue:

1. Create branch: `issue-<number>-<short-name>`
2. Run preflight prompt
   - Pre-flight must include a completed PORTABILITY ANALYSIS block (section 3a).
   - All seven portability fields must be answered before the spec phase begins.
   - Incomplete portability analysis is grounds for blocking the spec step.
3. Commit preflight
4. Run spec prompt
5. Commit spec
6. Run design prompt
7. Commit design
8. Run failing-test prompt
9. Commit failing tests
10. Run implementation prompt
11. Commit implementation
12. Run docs prompt
13. Commit docs
14. Run audit prompt
15. Commit audit or audit fixes

Do not merge until audit passes.