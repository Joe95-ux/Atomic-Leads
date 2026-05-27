import { SignIn } from "@clerk/nextjs"

import { AuthShell } from "@/components/auth/auth-shell"

export default function SignInPage() {
  return (
    <AuthShell
      title="Welcome back"
      description="Sign in to manage leads, outreach, and scraping jobs."
      alternateHref="/sign-up"
      alternateLabel="Need an account? Sign up"
    >
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
    </AuthShell>
  )
}
