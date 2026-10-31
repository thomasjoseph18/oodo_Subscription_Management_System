# Brightloop subscription management: hackathon design

Date: 2026-10-31. Demo deadline: 16:00 IST today. Source requirements: `Subscription_Management_System.pdf`, `design.md`.

## Goal

A working demo of one Brightloop billing month, from sign-up to the finance dashboard. Billing, payments and metrics must be real: no faked payment success or made-up analytics. Every service used must be free.

## Decisions

- Visual style: deliberate Odoo look-alike, following `design.md` tokens, type and components. The hackathon is run by Odoo.
- Brand name in the app: Brightloop, the company in the brief. Doodles and highlights are our own SVGs. Odoo's logo files are not used.
- Staff can view all records and act on any invoice. They can change only assigned customers and subscriptions.
- Scheduled billing auto-confirms invoices. An admin setting turns this off.
- Business rules: INR only; prices exclude tax; discount before tax; tax rounded half-up per line; invoices raised in advance; dates derived from the start date; one invoice equals one discount use; overdue is calculated; minimum password length is 9.
- Renewal: old subscription becomes Renewed, new subscription links through `renewed_from`.
- Quotation is a separate document. An accepted quotation creates a subscription at Confirmed. A subscription created directly moves through Draft and Quotation itself.

## Free stack

| Need | Choice | Fallback |
|---|---|---|
| Runtime | Python 3.12 via uv | Python 3.11 |
| Database | PostgreSQL, installed locally | SQLite for teammates' quick tests only |
| Redis | Upstash free | "Run billing now" calls the same service without Celery |
| Worker | Celery `--pool=solo`, Beat | As above |
| Email | Gmail app password over SMTP | Django console backend, stated in the demo |
| PDF | WeasyPrint, generated on demand | xhtml2pdf if Pango fails on Windows |
| Payments | Razorpay test mode; checkout signature verified on the server | Gateway button disabled; manual payments only |
| Hosting | Local machine | Render free has a cold start and blocks SMTP ports |

## Scope

Build, in order:

1. Foundation: Django, DRF, JWT, roles, Vite, Tailwind tokens, landing and auth pages.
2. Catalogue: products, variants, plans, taxes, discounts, payment terms.
3. Lifecycle: quotation templates, quotations, subscriptions, state machine, event history.
4. Billing: invoice service, duplicate-safe billing run, Beat schedule, invoice PDF and email.
5. Payments: manual recording, partial payments, allocations, Razorpay test checkout, webhook endpoint.
6. Dashboards: admin, staff, customer portal, in-app notifications, basic audit log.
7. Demo: clearly labelled seed data, 5,000-subscription timing check, rehearsal.

Stretch, only after 15:00: assistant with fixed read-only functions (Gemini free key).

Cut for today: forecasting, churn prediction, file storage uploads, proration, Playwright, running Docker. Dockerfiles may be written, but are reported as untested. A cut item is listed as not built, never shown as working.

## Team split

Four people, five commits, merged in order. Each patch needs the one before it.

| Commit | Owner | Brief scenes | Contents |
|---|---|---|---|
| 0 | Lead | All | Frontend, backend skeleton, `common/`, service clients, notifications, audit logs, API contract |
| 1 | Teammate A | New customer signs up; launching a new plan | accounts, customers, products, plans |
| 2 | Teammate B | Quote into subscription; billing day | taxes, quotations, subscriptions, invoices, billing tasks, PDFs |
| 3 | Teammate C | Better price; money comes in | discounts, payments, Razorpay |
| 4 | Lead | Finance lead | analytics, dashboards, assistant, demo data, speed check, final fixes |

Taxes sit in commit 2 because billing needs them. Commit 2 calls a no-op discount hook, and commit 3 replaces it. Each commit includes its own migrations and tests. Teammates use their own git identity, run the tests themselves and commit in real time. Commit dates are not altered.

Until a commit lands, the frontend shows a "not available yet" state for its screens, never mock data.

## Architecture

Modular monolith per the brief: `backend/apps/*` with logic in `services.py`, `frontend/src`, at the repo root. Duplicate billing is blocked by a partial unique constraint on `(subscription, period_start)` excluding cancelled invoices. Billing uses `FOR UPDATE SKIP LOCKED`, and creates the invoice and advances `next_billing_date` in one transaction.

## Tests

pytest for the money paths: billing dates, tax, discounts, duplicate prevention, partial payments, status transitions, webhook signature, customer data isolation. Vitest for login and protected routes. Results are reported as run, including failures.
