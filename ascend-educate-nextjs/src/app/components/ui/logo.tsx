import { BookOpen } from "lucide-react"
import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  size?: "sm" | "md" | "lg" | "xl"
  showText?: boolean
}

const sizeMap = {
  sm: { icon: "h-6 w-6", text: "text-xl", container: "gap-2" },
  md: { icon: "h-8 w-8", text: "text-2xl", container: "gap-3" },
  lg: { icon: "h-10 w-10", text: "text-3xl", container: "gap-3" },
  xl: { icon: "h-12 w-12", text: "text-4xl", container: "gap-4" },
}

export function Logo({ className, size = "md", showText = true }: LogoProps) {
  const { icon, text, container } = sizeMap[size]
  
  return (
    <div className={cn("flex items-center", container, className)}>
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-primary rounded-lg blur-sm opacity-75" />
        <div className="relative bg-gradient-primary rounded-lg p-2 shadow-glow">
          <BookOpen className={cn(icon, "text-primary-foreground")} />
        </div>
      </div>
      {showText && (
        <span className={cn("font-bold text-foreground", text)}>
          TeachMe
        </span>
      )}
    </div>
  )
}