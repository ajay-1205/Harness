---
name: sql_review
description: Use when the user shares a SQL query and wants feedback, optimization, or bug-finding.
---

# SQL review skill

Review the query for:
1. Correctness -- does it do what the user likely intends?
2. Performance -- missing indexes implied, unnecessary full scans, N+1 patterns.
3. Style -- readability, explicit column lists over SELECT *.

Respond with a short numbered list of findings, most important first.
Do not rewrite the whole query unless asked.