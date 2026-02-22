import type { ReactNode } from 'react'
import { Check } from 'lucide-react'

export type StepStatus = 'completed' | 'current' | 'upcoming'

interface StepIndicatorProps {
  step: number
  status: StepStatus
  isLast?: boolean
  children: ReactNode
}

export function StepIndicator({ step, status, isLast = false, children }: StepIndicatorProps) {
  return (
    <div className="relative">
      {/* Connector line */}
      {!isLast && (
        <div className="absolute left-[15px] top-[40px] bottom-0 w-px bg-stone-200 dark:bg-stone-700" />
      )}

      <div className="flex gap-4">
        {/* Step number */}
        <div className="shrink-0 relative z-10">
          {status === 'completed' ? (
            <div className="w-8 h-8 rounded-full bg-lime-100 dark:bg-lime-900/30 flex items-center justify-center">
              <Check className="w-4 h-4 text-lime-600 dark:text-lime-400" strokeWidth={2.5} />
            </div>
          ) : status === 'current' ? (
            <div className="w-8 h-8 rounded-full bg-stone-900 dark:bg-stone-100 flex items-center justify-center">
              <span className="text-xs font-bold text-stone-100 dark:text-stone-900">{step}</span>
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-stone-200 dark:bg-stone-700 flex items-center justify-center">
              <span className="text-xs font-medium text-stone-500 dark:text-stone-400">{step}</span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 pb-8">
          {children}
        </div>
      </div>
    </div>
  )
}
