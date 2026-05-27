# Atomic Leads Frontend

Frontend scaffold for the Atomic Leads dashboard and client-facing workflow.

## Included stack

- Next.js App Router + TypeScript
- Clerk authentication (`proxy.ts`, `/sign-in`, `/sign-up`, protected `/dashboard`)
- TanStack Query provider and devtools
- React Hook Form + Zod schema-based form validation
- Prisma ORM configured for PostgreSQL (local Docker + production)
- Pusher Channels and Beams setup helpers

## Environment variables

Copy `.env.example` to `.env` and set values:

```bash
cp .env.example .env
```

## Database (PostgreSQL)

Start local Postgres:

```bash
npm run db:up
npm run prisma:migrate
npm run prisma:generate
```

`DATABASE_URL` in `.env` should match `docker-compose.yml` for local dev. In production, point it at your hosted PostgreSQL instance (same connection string format).

## Useful scripts

```bash
npm run dev
npm run lint
npm run typecheck
npm run db:up
npm run prisma:migrate
npm run prisma:generate
npm run prisma:push
npm run prisma:studio
```

## Project structure

- `app/(auth)` sign-in and sign-up routes
- `app/(main)` authenticated app shell and pages
- `lib/auth` route matchers for Clerk middleware
- `components/providers` app-level providers (theme, Clerk, query)
- `components/forms` form components (React Hook Form + Zod)
- `lib/validation` shared Zod schemas
- `lib/db` Prisma client singleton
- `lib/realtime` Pusher Channels helpers
- `lib/notifications` Pusher Beams bootstrap
