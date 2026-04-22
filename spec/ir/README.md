# IR Shared Specs

This directory contains executable shared IR semantic-spec cases.

Python is the only executing host today.

Cases in this directory assert portable Core IR lowering shape at the pre-optimization boundary:

- parse
- lower
- normalize portable IR
- compare against shared expected IR

Host-local optimized nodes are outside this contract and must not appear in shared IR expectations.
