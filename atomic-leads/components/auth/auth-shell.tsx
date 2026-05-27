import Link from "next/link"

type AuthShellProps = {
  children: React.ReactNode
  title: string
  description: string
  alternateHref: string
  alternateLabel: string
}

export function AuthShell({
  children,
  title,
  description,
  alternateHref,
  alternateLabel,
}: AuthShellProps) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 p-6">
      <div className="w-full max-w-md space-y-2 text-center">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="flex w-full max-w-md justify-center">{children}</div>
      <p className="text-sm text-muted-foreground">
        <Link href={alternateHref} className="font-medium text-foreground underline-offset-4 hover:underline">
          {alternateLabel}
        </Link>
      </p>
    </div>
  )
}
