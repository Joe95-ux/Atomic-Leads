"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  type LeadFormValues,
  leadFormSchema,
} from "@/lib/validation/lead-form-schema"

const defaultValues: LeadFormValues = {
  fullName: "",
  email: "",
  companyName: "",
}

export function LeadForm() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LeadFormValues>({
    resolver: zodResolver(leadFormSchema),
    defaultValues,
  })

  function onSubmit(values: LeadFormValues) {
    toast.success(`Lead "${values.fullName}" is ready for API submission.`)
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
      <div className="space-y-2">
        <Label htmlFor="fullName">Full name</Label>
        <Input
          id="fullName"
          placeholder="Jane Doe"
          aria-invalid={Boolean(errors.fullName)}
          {...register("fullName")}
        />
        {errors.fullName ? (
          <p className="text-xs text-destructive">{errors.fullName.message}</p>
        ) : null}
      </div>
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="jane@company.com"
          aria-invalid={Boolean(errors.email)}
          {...register("email")}
        />
        {errors.email ? (
          <p className="text-xs text-destructive">{errors.email.message}</p>
        ) : null}
      </div>
      <div className="space-y-2">
        <Label htmlFor="companyName">Company name</Label>
        <Input
          id="companyName"
          placeholder="Acme Inc."
          aria-invalid={Boolean(errors.companyName)}
          {...register("companyName")}
        />
        {errors.companyName ? (
          <p className="text-xs text-destructive">{errors.companyName.message}</p>
        ) : null}
      </div>
      <div className="flex gap-2">
        <Button type="submit">Validate form</Button>
        <Button type="button" variant="outline" onClick={() => reset(defaultValues)}>
          Reset
        </Button>
      </div>
    </form>
  )
}
