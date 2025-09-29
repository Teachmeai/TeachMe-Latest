'use client'

import * as React from "react"
import { Mail, Smartphone, Chrome } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { GlassCard } from "@/components/ui/glass-card"
import { Logo } from "@/components/ui/logo"
import { cn } from "@/lib/utils"
import { supabase } from "../../lib/supabase"
import { useToast } from "@/hooks/use-toast"

interface LoginPageProps {
  onLogin: (method: "email" | "google", email?: string) => void
  className?: string
}

export function LoginPage({ onLogin, className }: LoginPageProps) {
  const [email, setEmail] = React.useState("")
  const [loginMethod, setLoginMethod] = React.useState<"email" | "otp" | null>(null)
  const [otpCode, setOtpCode] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(false)
  const [isHydrated, setIsHydrated] = React.useState(false)

  React.useEffect(() => {
    setIsHydrated(true)
  }, [])
  const { toast } = useToast()

  const handleEmailLogin = async () => {
    if (!email.trim()) return
    
    setIsLoading(true)
    try {
      console.log('Sending OTP to:', email)
      
      // Send OTP email
      const { data, error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          shouldCreateUser: true,
          // Don't set emailRedirectTo to force OTP instead of magic link
        }
      })
      
      console.log('OTP response:', { data, error })
      
      if (error) {
        console.error('OTP error:', error)
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive"
        })
      } else {
        setLoginMethod("otp")
        toast({
          title: "Check your email",
          description: `We've sent a 6-digit verification code to ${email}. Please enter it below.`,
        })
      }
    } catch (error) {
      console.error('Unexpected error:', error)
      toast({
        title: "Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleOtpVerification = async () => {
    if (!otpCode.trim()) return
    
    setIsLoading(true)
    try {
      console.log('Verifying OTP:', otpCode, 'for email:', email)
      
      const { data, error } = await supabase.auth.verifyOtp({
        email,
        token: otpCode,
        type: 'email'
      })
      
      console.log('OTP verification response:', { data, error })
      
      if (error) {
        console.error('OTP verification error:', error)
        toast({
          title: "Invalid code",
          description: error.message,
          variant: "destructive"
        })
      } else if (data.session) {
        console.log('OTP verification successful, user signed in')
        console.log('Session data:', data.session)
        toast({
          title: "Success!",
          description: "You have been signed in successfully.",
        })
        // The useAuth hook should handle the state change automatically
      } else if (data.user) {
        console.log('OTP verification successful, user created but no session')
        console.log('User data:', data.user)
        toast({
          title: "Verification successful",
          description: "Please wait while we complete your sign-in...",
        })
        // Try to get the current session
        const { data: sessionData } = await supabase.auth.getSession()
        console.log('Current session after OTP:', sessionData)
        if (sessionData.session) {
          console.log('Session found after OTP verification')
        }
      } else {
        console.log('OTP verification successful but no user or session created')
        toast({
          title: "Verification successful",
          description: "Please try logging in again.",
        })
      }
    } catch (error) {
      console.error('Unexpected OTP verification error:', error)
      toast({
        title: "Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleResendOtp = async () => {
    if (!email.trim()) return
    
    setIsLoading(true)
    try {
      console.log('Resending OTP to:', email)
      
      const { data, error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          shouldCreateUser: true,
        }
      })
      
      console.log('Resend OTP response:', { data, error })
      
      if (error) {
        console.error('Resend OTP error:', error)
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive"
        })
      } else {
        toast({
          title: "Code sent",
          description: `A new 6-digit code has been sent to ${email}.`,
        })
      }
    } catch (error) {
      console.error('Unexpected resend error:', error)
      toast({
        title: "Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    setIsLoading(true)
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
      
      if (error) {
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (!isHydrated) {
    return (
      <div className={cn("min-h-screen flex items-center justify-center p-4 relative bg-gradient-to-br from-background via-background to-muted/30", className)}>
        <div className="relative z-10 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-primary/10 rounded-full mx-auto mb-4 flex items-center justify-center">
              <div className="w-8 h-8 bg-primary/20 rounded animate-pulse" />
            </div>
            <h1 className="text-3xl font-bold mb-2">Loading...</h1>
            <p className="text-muted-foreground">
              Please wait while we prepare your login experience
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("min-h-screen flex items-center justify-center p-4 relative bg-gradient-to-br from-background via-background to-muted/20", className)}>
      {/* Enhanced Background Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(120,119,198,0.05),transparent_50%)]" />
      
      {/* Enhanced Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-primary/8 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 left-1/4 w-80 h-80 bg-accent/8 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-primary/4 rounded-full blur-2xl animate-float" style={{ animationDelay: '2s' }} />
      </div>

      <div className="relative z-10 w-full max-w-lg">
        <div className="text-center mb-10 animate-fade-in">
          <div className="mx-auto mb-8 animate-bounce-in">
            <Logo size="xl" className="justify-center" />
          </div>
          <h1 className="text-4xl font-bold mb-4 text-foreground">
            Welcome Back
          </h1>
          <p className="text-muted-foreground text-lg">
            Sign in to continue your learning journey
          </p>
        </div>

        <GlassCard variant="interactive" size="lg" className="animate-scale-in">
          {loginMethod === "otp" ? (
            // OTP Verification Form
            <div className="space-y-8">
               <div className="text-center">
                 <div className="w-20 h-20 bg-gradient-primary rounded-2xl mx-auto mb-6 flex items-center justify-center shadow-xl animate-bounce-in">
                   <Mail className="h-10 w-10 text-primary-foreground" />
                 </div>
                 <h3 className="text-2xl font-bold mb-4 bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
                   Check Your Email
                 </h3>
                 <p className="text-base text-muted-foreground mb-2">
                   We&apos;ve sent a verification code to <strong className="text-foreground">{email}</strong>
                 </p>
                 <p className="text-sm text-muted-foreground">
                   If you received a magic link instead, click it to sign in directly.
                 </p>
               </div>

              <div className="space-y-6">
                <div className="space-y-3">
                  <Label htmlFor="otp" className="text-base font-semibold">Verification Code</Label>
                  <Input
                    id="otp"
                    type="text"
                    placeholder="Enter 6-digit code"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    className="text-center text-xl tracking-widest glass-card h-14 text-lg font-mono"
                    maxLength={6}
                  />
                </div>

                 <Button
                   onClick={handleOtpVerification}
                   disabled={otpCode.length !== 6 || isLoading}
                   className="w-full glass-button hover-scale text-primary-foreground shadow-lg hover:shadow-xl h-12 text-lg"
                   variant="default"
                 >
                   {isLoading ? "Verifying..." : "Verify & Continue"}
                 </Button>

                 <div className="flex gap-3">
                   <Button
                     onClick={handleResendOtp}
                     disabled={isLoading}
                     variant="outline"
                     className="flex-1 hover-scale h-11"
                   >
                     Resend Code
                   </Button>
                   <Button
                     onClick={() => setLoginMethod(null)}
                     variant="ghost"
                     className="flex-1 hover-scale h-11"
                   >
                     Back to login
                   </Button>
                 </div>
              </div>
            </div>
          ) : (
            // Login Form
            <div className="space-y-8">
              <div className="space-y-6">
                <div className="space-y-3">
                  <Label htmlFor="email" className="text-base font-semibold">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="glass-card border-border h-12 text-base"
                    onKeyPress={(e) => e.key === "Enter" && handleEmailLogin()}
                  />
                </div>

                <Button
                  onClick={handleEmailLogin}
                  disabled={!email.trim() || isLoading}
                  className="w-full glass-button hover-scale text-primary-foreground shadow-lg hover:shadow-xl h-12 text-lg"
                  variant="default"
                >
                  <Mail className="mr-2 h-5 w-5" />
                  {isLoading ? "Sending Code..." : "Send Verification Code"}
                </Button>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border/50" />
                </div>
                <div className="relative flex justify-center text-sm uppercase">
                  <span className="bg-background px-4 text-muted-foreground font-medium">
                    Or continue with
                  </span>
                </div>
              </div>

              <Button
                onClick={handleGoogleLogin}
                disabled={isLoading}
                variant="outline"
                className="w-full hover-scale glass-card h-12 text-base border-border/50 hover:border-primary/50"
              >
                <Chrome className="mr-3 h-5 w-5" />
                {isLoading ? "Connecting..." : "Continue with Google"}
              </Button>
            </div>
          )}
        </GlassCard>

        <div className="text-center mt-8 text-sm text-muted-foreground animate-fade-in">
          By continuing, you agree to our{" "}
          <a href="#" className="text-primary hover:underline font-medium transition-colors duration-200">
            Terms of Service
          </a>{" "}
          and{" "}
          <a href="#" className="text-primary hover:underline font-medium transition-colors duration-200">
            Privacy Policy
          </a>
        </div>
      </div>
    </div>
  )
}