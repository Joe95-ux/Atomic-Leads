import { SignUp } from "@clerk/nextjs"

import { AuthShell } from "@/components/auth/auth-shell"

export default function SignUpPage() {
  return (
    <AuthShell
      title="Create your account"
      description="Start building your lead engine workspace."
      alternateHref="/sign-in"
      alternateLabel="Already have an account? Sign in"
    >
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
    </AuthShell>
  )
}
