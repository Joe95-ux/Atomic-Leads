"use client"

import * as React from "react"
import { ClerkProvider } from "@clerk/nextjs"
import { dark, shadcn } from "@clerk/themes"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { useTheme } from "next-themes"
import { Toaster } from "sonner"

import { ThemeProvider } from "@/components/theme-provider"
import { TooltipProvider } from "@/components/ui/tooltip"

type AppProvidersProps = {
  children: React.ReactNode
}

function ClerkThemeBridge({ children }: AppProvidersProps) {
  const { resolvedTheme } = useTheme()
  const isDarkTheme = resolvedTheme !== "light"

  return (
    <ClerkProvider appearance={{ baseTheme: isDarkTheme ? dark : shadcn }}>
      {children}
    </ClerkProvider>
  )
}

export function AppProviders({ children }: AppProvidersProps) {
  const [queryClient] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  )

  return (
    <ThemeProvider>
      <ClerkThemeBridge>
        <QueryClientProvider client={queryClient}>
          <TooltipProvider>
            {children}
            <Toaster position="top-right" richColors />
          </TooltipProvider>
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </ClerkThemeBridge>
    </ThemeProvider>
  )
}
