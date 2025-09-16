'use client'

import * as React from "react"
import { Check, ChevronsUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { BackendRole } from "../lib/backend"
import { useToast } from "@/hooks/use-toast"

interface RoleSwitcherProps {
  roles: BackendRole[]
  activeRole: string
  onRoleSwitch: (role: string, orgId?: string) => Promise<boolean>
  className?: string
}

export function RoleSwitcher({ roles, activeRole, onRoleSwitch, className }: RoleSwitcherProps) {
  const [open, setOpen] = React.useState(false)
  const [switching, setSwitching] = React.useState(false)
  const { toast } = useToast()

  const handleRoleSelect = async (role: BackendRole) => {
    if (role.role === activeRole) {
      setOpen(false)
      return
    }

    setSwitching(true)
    try {
      const success = await onRoleSwitch(role.role, role.org_id)
      if (success) {
        toast({
          title: "Role switched",
          description: `Now active as ${role.role}${role.org_name ? ` in ${role.org_name}` : ''}`,
        })
        setOpen(false)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to switch role. Please try again.",
        variant: "destructive"
      })
    } finally {
      setSwitching(false)
    }
  }

  const getActiveRoleDisplay = () => {
    const active = roles.find(r => r.role === activeRole)
    if (!active) return "Select role"
    
    return (
      <div className="flex items-center gap-2">
        <Badge variant={active.scope === 'global' ? 'default' : 'secondary'}>
          {active.scope}
        </Badge>
        <span>{active.role}</span>
        {active.org_name && (
          <span className="text-muted-foreground">({active.org_name})</span>
        )}
      </div>
    )
  }

  const groupedRoles = roles.reduce((acc, role) => {
    if (!acc[role.scope]) {
      acc[role.scope] = []
    }
    acc[role.scope].push(role)
    return acc
  }, {} as Record<string, BackendRole[]>)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("w-[300px] justify-between", className)}
          disabled={switching}
        >
          {getActiveRoleDisplay()}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[300px] p-0">
        <Command>
          <CommandInput placeholder="Search roles..." />
          <CommandList>
            <CommandEmpty>No roles found.</CommandEmpty>
            {Object.entries(groupedRoles).map(([scope, scopeRoles]) => (
              <CommandGroup key={scope} heading={scope === 'global' ? 'Global Roles' : 'Organization Roles'}>
                {scopeRoles.map((role) => (
                  <CommandItem
                    key={`${role.scope}-${role.role}-${role.org_id || 'global'}`}
                    value={`${role.role} ${role.org_name || ''}`}
                    onSelect={() => handleRoleSelect(role)}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant={role.scope === 'global' ? 'default' : 'secondary'} className="text-xs">
                        {role.scope}
                      </Badge>
                      <span>{role.role}</span>
                      {role.org_name && (
                        <span className="text-muted-foreground text-sm">({role.org_name})</span>
                      )}
                    </div>
                    {role.role === activeRole && (
                      <Check className="h-4 w-4" />
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
