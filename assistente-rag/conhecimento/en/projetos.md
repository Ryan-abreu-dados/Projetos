---
fonte: site
titulo: Ryan's projects
rotulo_fonte: Projects
url: /en/projects/
atualizado: 2026-11-12
---

## What projects has Ryan built?
Ryan's public project is incremental replication with CDC in PostgreSQL, available on GitHub. He also
built the Python file organizer at Tel Contact Center, his own portfolio site and this AI assistant
(RAG), still in progress. At work, without internal numbers, he built the CDC replication between the
company's databases, leads the billing system (in progress) and built a view of disqualified leads for
the sales team.

## Incremental replication with CDC in PostgreSQL (public project)
Ryan set up native PostgreSQL logical replication between an online store database and an analytical
database, with synthetic data generated with Faker: 370,708 rows in the initial load, across 4 tables,
and about 85 operations per second in the simulation. Every INSERT, UPDATE and DELETE committed at the
source leaves the transaction log (WAL) and is applied at the target. The project is about what happens
when something goes wrong.

## Results measured in the CDC project
With the target stopped for 30 seconds, the WAL retained at the source grew from 1.77 to 3.39 MB; once
restarted, the target caught up with the source in 0.72 seconds. A dropped replication connection came
back on its own in 2.47 seconds. The measured lag from source to target had a median of 0.3 ms and a p99
of 3.3 ms, with both databases on the same machine.

## md5 reconciliation in the CDC project
Logical replication does not flag a row changed directly at the target: it keeps running without errors
and the data stays wrong. That is why Ryan built a reconciliation that compares both sides in ranges of
10,000 ids, with counts and md5, and only goes row by row in the ranges that differ. In the test, he
changed 3 rows at the target; the replication flagged nothing, and the reconciliation found all 3 and
copied the source value back. The project has 11 tests covering the failures and runs with Docker and
GitHub Actions.

## What Ryan learned from the CDC project
Retained WAL is the cost of a stopped target and, with no limit, it fills the source's disk. At the
target, foreign keys protect nothing that comes from replication. And "green" replication does not mean
correct data: checking the content is a separate job.
