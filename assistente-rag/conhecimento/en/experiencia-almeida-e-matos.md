---
fonte: site
titulo: Internship at Almeida e Matos
rotulo_fonte: Experience · Almeida e Matos
url: /en/experience/
atualizado: 2026-11-12
---

## Where does Ryan work today?
Since May 2026, Ryan has been a data-focused intern at Almeida e Matos Sociedade de Advogados, a law firm
in Alphaville (Barueri, São Paulo). He works on data engineering in production, with PostgreSQL and
Supabase.

## Incremental replication (CDC)
Ryan built the first version of the incremental replication between the company's transactional and
analytical databases, using PostgreSQL logical replication (CDC), and later extended it to new tables,
with failure recovery and reconciliation of mismatches.

## Incremental loads and faster queries
Ryan replaced a full refresh that hit the timeout with idempotent incremental loads (watermark, upsert
and deduplication), and built an incremental SCD type 2 in the orchestrator's heaviest step. He also
optimizes queries and dashboards with EXPLAIN ANALYZE, covering indexes and autovacuum maintenance.

## Data quality, monitoring and security
Ryan built automated quality checks that actually fail and alert by email (with n8n), and automatic
detection of schema changes (schema drift), with tests. On security, he implemented access control by
department in the database (row-level security) and authorization, with LGPD, Brazil's data protection
law, in mind.

## Integrations and screens
Ryan built the weekly sync of thousands of files and conversations to Google Drive (with pagination,
retries and deduplication), customer identification through the WhatsApp (Meta) API and a workflow
runner in n8n. He also builds screens in React and TypeScript, wired to PL/pgSQL functions and Supabase
Edge Functions.

## What is the biggest challenge Ryan has solved at work?
The challenge Ryan has solved was getting the incremental replication (CDC) running between the main
database and the analytical database (layered, in the medallion model), with an orchestrator that keeps
both always in sync. At first he tried to build it without properly researching the documentation, and
that first approach produced many errors. With his manager's guidance, he rebuilt it the right way and,
together with him, implemented CDC with the orchestrator always connected. They also built a monitoring
screen and WhatsApp alerts, made with n8n, to warn if the replication stops. What he learned: read the
documentation and research before building.

## Has Ryan led a project or people?
Yes, one project: Ryan is leading a billing system, still in progress. It is the first project he has
led; he says he is learning a lot and wants to do even better on the next ones. He has not managed
people yet.

## Billing system (in progress)
Ryan's current challenge is a billing system integrated by API with the company's financial system. The
hard part is the business rules: making something that really works for the finance team. The system
sends automatic reminders on the due date of each installment, receives the payment receipt sent by the
customer and puts it on a screen for the finance team to check and settle. It fits into a task workflow
the company already had.

## Has Ryan worked with people from other areas?
Yes, and it is a part of the job he enjoys. For Ryan, the people who know the workflow are the people in
each area: the sales team knows how to sell and knows what it needs to work better (an automatic
message, an automation, a new field). His role is to understand exactly what they are looking for and
deliver it with the data and tools he has. For example, the sales manager wanted to track disqualified
leads and explained why; Ryan built her a view of that data with filters by period (yesterday, today,
month), by cohort and by who disqualified the most.
