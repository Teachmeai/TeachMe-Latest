import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-semibold ring-offset-background transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 relative overflow-hidden",
  {
    variants: {
      variant: {
        default: "bg-gradient-primary text-primary-foreground shadow-lg hover:shadow-xl hover:scale-105 active:scale-95",
        destructive: "bg-destructive text-destructive-foreground shadow-lg hover:shadow-xl hover:bg-destructive/90 hover:scale-105 active:scale-95",
        outline: "border-2 border-border bg-background hover:bg-primary/10 hover:text-primary hover:border-primary/50 shadow-sm hover:shadow-md hover:scale-105 active:scale-95",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:shadow-md hover:bg-secondary/80 hover:scale-105 active:scale-95",
        ghost: "hover:bg-primary/10 hover:text-primary hover:scale-105 active:scale-95",
        link: "text-primary underline-offset-4 hover:underline hover:text-primary/80",
        glass: "glass-button text-primary-foreground shadow-lg hover:shadow-xl hover:scale-105 active:scale-95",
        gradient: "bg-gradient-accent text-primary-foreground shadow-lg hover:shadow-xl hover:scale-105 active:scale-95",
        hero: "bg-gradient-primary text-primary-foreground shadow-xl hover:shadow-2xl hover:scale-110 active:scale-105 animate-pulse-glow",
        premium: "bg-gradient-to-r from-primary via-accent to-primary text-primary-foreground shadow-xl hover:shadow-2xl hover:scale-110 active:scale-105 relative overflow-hidden",
        subtle: "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground shadow-sm hover:shadow-md hover:scale-105 active:scale-95",
        success: "bg-success text-success-foreground shadow-lg hover:shadow-xl hover:bg-success/90 hover:scale-105 active:scale-95",
        warning: "bg-warning text-warning-foreground shadow-lg hover:shadow-xl hover:bg-warning/90 hover:scale-105 active:scale-95",
      },
      size: {
        xs: "h-7 px-2 text-xs rounded-md",
        sm: "h-8 px-3 text-sm rounded-md",
        default: "h-10 px-4 py-2",
        lg: "h-11 px-6 text-base rounded-lg",
        xl: "h-12 px-8 text-lg rounded-xl",
        icon: "h-10 w-10",
        "icon-sm": "h-8 w-8",
        "icon-lg": "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
