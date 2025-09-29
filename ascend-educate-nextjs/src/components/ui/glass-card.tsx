import * as React from "react"
import { cn } from "@/lib/utils"
import { cva, type VariantProps } from "class-variance-authority"

const glassCardVariants = cva(
  "glass-card rounded-lg transition-all duration-300",
  {
    variants: {
      variant: {
        default: "hover:shadow-lg",
        interactive: "hover:shadow-glow hover:scale-[1.02] cursor-pointer",
        chat: "chat-message hover:bg-muted/50",
        profile: "avatar-glow",
      },
      size: {
        sm: "p-3",
        default: "p-4",
        lg: "p-6",
        xl: "p-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export interface GlassCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof glassCardVariants> {}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant, size, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(glassCardVariants({ variant, size, className }))}
      {...props}
    />
  ),
)
GlassCard.displayName = "GlassCard"

export { GlassCard, glassCardVariants }