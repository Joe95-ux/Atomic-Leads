import { AuthHeader } from "@/components/layout/auth-header"

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AuthHeader />
      {children}
    </>
  )
}
