import { useLocation, useNavigate } from 'react-router-dom'
import { FolderInput, Layers, Hammer, ShieldCheck, Package } from 'lucide-react'
import { getBuildStateFiles, hasOutputProject } from '@/lib/build-state-loader'

export type Phase = 'init' | 'scaffold' | 'build' | 'validate' | 'finalize'

interface PhaseConfig {
  id: Phase
  label: string
  icon: typeof FolderInput
  path: string
}

const phases: PhaseConfig[] = [
  { id: 'init', label: 'Init', icon: FolderInput, path: '/' },
  { id: 'scaffold', label: 'Scaffold', icon: Layers, path: '/scaffold' },
  { id: 'build', label: 'Build', icon: Hammer, path: '/build' },
  { id: 'validate', label: 'Validate', icon: ShieldCheck, path: '/validate' },
  { id: 'finalize', label: 'Finalize', icon: Package, path: '/finalize' },
]

export type PhaseStatus = 'completed' | 'current' | 'upcoming'

export function PhaseNav() {
  const navigate = useNavigate()
  const location = useLocation()

  // Determine current phase from URL
  let currentPhaseId: Phase = 'init'
  if (location.pathname === '/' || location.pathname === '/init') {
    currentPhaseId = 'init'
  } else if (location.pathname === '/scaffold') {
    currentPhaseId = 'scaffold'
  } else if (location.pathname === '/build' || location.pathname.startsWith('/build/')) {
    currentPhaseId = 'build'
  } else if (location.pathname === '/validate' || location.pathname.startsWith('/validate/')) {
    currentPhaseId = 'validate'
  } else if (location.pathname === '/finalize') {
    currentPhaseId = 'finalize'
  }

  // Check completion status
  const hasInit = getBuildStateFiles().length > 0
  const hasScaffold = hasOutputProject()
  const phaseComplete: Record<Phase, boolean> = {
    init: hasInit,
    scaffold: hasScaffold,
    build: false,
    validate: false,
    finalize: false,
  }

  return (
    <nav className="flex items-center justify-center">
      {phases.map((phase, index) => {
        const Icon = phase.icon
        const isFirst = index === 0
        const isComplete = phaseComplete[phase.id]

        let status: PhaseStatus
        if (phase.id === currentPhaseId) {
          status = 'current'
        } else if (isComplete) {
          status = 'completed'
        } else {
          status = 'upcoming'
        }

        return (
          <div key={phase.id} className="flex items-center">
            {!isFirst && (
              <div
                className={`w-4 sm:w-8 lg:w-12 h-px transition-colors duration-200 ${
                  status === 'upcoming'
                    ? 'bg-stone-200 dark:bg-stone-700'
                    : 'bg-stone-400 dark:bg-stone-500'
                }`}
              />
            )}
            <button
              onClick={() => navigate(phase.path)}
              className={`
                group relative flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg transition-all duration-200 whitespace-nowrap
                ${status === 'current'
                  ? 'bg-stone-900 dark:bg-stone-100 text-stone-100 dark:text-stone-900 shadow-sm'
                  : status === 'completed'
                    ? 'bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 hover:bg-stone-200 dark:hover:bg-stone-700'
                    : 'text-stone-400 dark:text-stone-500 hover:text-stone-600 dark:hover:text-stone-400 hover:bg-stone-50 dark:hover:bg-stone-800/50'
                }
              `}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-transform duration-200 group-hover:scale-110 ${
                  status === 'upcoming' ? 'opacity-60' : ''
                }`}
                strokeWidth={1.5}
              />
              <span className={`text-sm font-medium hidden sm:inline ${
                status === 'upcoming' ? 'opacity-60' : ''
              }`}>
                {phase.label}
              </span>
              {isComplete && (
                <span className="absolute -top-1 -left-1 w-4 h-4 rounded-full bg-lime-500 flex items-center justify-center shadow-sm">
                  <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              )}
            </button>
          </div>
        )
      })}
    </nav>
  )
}

export { phases }
