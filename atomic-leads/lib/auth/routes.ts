import { createRouteMatcher } from "@clerk/nextjs/server"

export const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/health(.*)",
])

export const isProtectedRoute = createRouteMatcher(["/dashboard(.*)"])
