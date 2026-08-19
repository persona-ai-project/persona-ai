import * as React from "react"
import { cn } from "@/lib/utils"

function Select({
  value,
  onValueChange,
  children,
  className,
  ...props
}: {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
} & Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "value" | "onChange">) {
  return (
    <select
      data-slot="select"
      value={value}
      onChange={(e) => onValueChange?.(e.target.value)}
      className={cn(
        "flex h-9 w-full items-center justify-between gap-2 rounded-lg border border-input bg-transparent px-3 py-2 text-sm transition-colors outline-none placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
}

function SelectTrigger({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <>{children}</>
}

function SelectValue({ placeholder, ...props }: React.HTMLAttributes<HTMLSpanElement> & { placeholder?: string }) {
  return null
}

function SelectContent({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <>{children}</>
}

function SelectItem({
  value,
  children,
  ...props
}: React.OptionHTMLAttributes<HTMLOptionElement> & { value: string }) {
  return (
    <option value={value} {...props}>
      {children}
    </option>
  )
}

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }
