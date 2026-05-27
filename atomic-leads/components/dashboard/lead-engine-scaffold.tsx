"use client"

import { useQuery } from "@tanstack/react-query"
import { BellRing, Database, Radio } from "lucide-react"
import { LeadForm } from "@/components/forms/lead-form"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type HealthResponse = {
  status: string
  timestamp: string
}

async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/health")

  if (!response.ok) {
    throw new Error("Failed to reach API")
  }

  return response.json()
}

export function LeadEngineScaffold() {
  const healthQuery = useQuery({
    queryKey: ["api-health"],
    queryFn: fetchHealth,
  })

  return (
    <main className="mx-auto flex min-h-[calc(100svh-65px)] w-full max-w-5xl flex-col gap-6 p-6">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold">Atomic Leads Frontend Scaffold</h1>
        <p className="text-sm text-muted-foreground">
          Query, auth, validation, ORM, and realtime foundations are now wired for
          modular feature work.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Database className="size-4" /> Prisma + PostgreSQL
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Prisma client singleton is ready in `lib/db/prisma.ts`, with PostgreSQL schema
            in `prisma/schema.prisma`.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Radio className="size-4" /> Pusher Channels
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Server and browser helpers are scaffolded under `lib/realtime`.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BellRing className="size-4" /> Pusher Beams
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Push notification bootstrap helper is available at
            `lib/notifications/beams-client.ts`.
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Lead Form Validation (React Hook Form + Zod)</CardTitle>
          </CardHeader>
          <CardContent>
            <LeadForm />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">TanStack Query API Health Check</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {healthQuery.isPending ? <p>Checking API status...</p> : null}
            {healthQuery.isError ? (
              <p className="text-destructive">API unavailable. Check server logs.</p>
            ) : null}
            {healthQuery.data ? (
              <>
                <p>
                  Status: <span className="font-medium">{healthQuery.data.status}</span>
                </p>
                <p className="text-muted-foreground">
                  Last check: {new Date(healthQuery.data.timestamp).toLocaleString()}
                </p>
              </>
            ) : null}
            <Button
              type="button"
              variant="outline"
              onClick={() => healthQuery.refetch()}
              disabled={healthQuery.isFetching}
            >
              Refresh status
            </Button>
          </CardContent>
        </Card>
      </section>
    </main>
  )
}
