import { z } from "zod"

export const leadFormSchema = z.object({
  fullName: z.string().trim().min(2, "Name must be at least 2 characters."),
  email: z.string().trim().email("Please provide a valid email address."),
  companyName: z.string().trim().max(120).optional(),
})

export type LeadFormValues = z.infer<typeof leadFormSchema>
