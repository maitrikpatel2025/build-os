import { useMemo } from 'react'
import { Hammer, Check, Circle, Minus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AppLayout } from '@/components/AppLayout'
import { CommandBlock } from '@/components/CommandBlock'
import { getMilestoneFiles } from '@/lib/build-state-loader'

interface MilestoneDisplay {
  id: string
  name: string
  isShell: boolean
  order: number
}

const statusIcons: Record<string, { icon: typeof Check; className: string }> = {
  complete: { icon: Check, className: 'text-lime-600 dark:text-lime-400 bg-lime-100 dark:bg-lime-900/30' },
  tested: { icon: Check, className: 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30' },
  wired: { icon: Minus, className: 'text-violet-600 dark:text-violet-400 bg-violet-100 dark:bg-violet-900/30' },
  backend_done: { icon: Minus, className: 'text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30' },
  frontend_done: { icon: Minus, className: 'text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30' },
  in_progress: { icon: Circle, className: 'text-stone-600 dark:text-stone-400 bg-stone-200 dark:bg-stone-700' },
  pending: { icon: Circle, className: 'text-stone-400 dark:text-stone-500 bg-stone-100 dark:bg-stone-800' },
}

export function BuildPage() {
  const milestoneFiles = useMemo(() => getMilestoneFiles(), [])

  // Parse milestone files into display objects
  const milestones: MilestoneDisplay[] = useMemo(() => {
    return milestoneFiles.map(path => {
      const match = path.match(/(\d+)-([^.]+)\.md$/)
      if (!match) return null
      const order = parseInt(match[1])
      const slug = match[2]
      return {
        id: `${match[1]}-${slug}`,
        name: slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        isShell: slug === 'shell',
        order,
      }
    }).filter((m): m is MilestoneDisplay => m !== null)
  }, [milestoneFiles])

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-stone-900 dark:text-stone-100 mb-2">
            Build
          </h1>
          <p className="text-stone-600 dark:text-stone-400">
            Build each milestone incrementally — shell first, then each section through the full pipeline.
          </p>
        </div>

        {/* One-shot option */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
              <Hammer className="w-5 h-5 text-stone-500 dark:text-stone-400" strokeWidth={1.5} />
              Build All (One-Shot)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CommandBlock
              command="/build-os/build-all"
              description="Run the entire pipeline automatically — shell through all sections to finalization:"
            />
          </CardContent>
        </Card>

        {/* Milestone-by-milestone */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100">
              Incremental (Step-by-Step)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ul className="divide-y divide-stone-200 dark:divide-stone-700">
              {milestones.map((milestone) => (
                <li key={milestone.id} className="px-6 py-4">
                  <div className="flex items-start gap-4">
                    {/* Status */}
                    <div className="shrink-0 mt-0.5">
                      <div className="w-6 h-6 rounded-full bg-stone-200 dark:bg-stone-700 flex items-center justify-center">
                        <span className="text-xs font-medium text-stone-600 dark:text-stone-400">
                          {milestone.order}
                        </span>
                      </div>
                    </div>

                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-stone-900 dark:text-stone-100">
                        {milestone.name}
                      </h3>

                      {milestone.isShell ? (
                        /* Shell milestone — single command */
                        <div className="mt-3">
                          <CommandBlock command="/build-os/build-shell" />
                        </div>
                      ) : (
                        /* Section milestone — 4-step pipeline */
                        <div className="mt-3 space-y-2">
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            <PipelineStep
                              label="Frontend"
                              command={`/build-os/build-section ${milestone.id.replace(/^\d+-/, '')}`}
                              status="pending"
                            />
                            <PipelineStep
                              label="API"
                              command={`/build-os/build-api ${milestone.id.replace(/^\d+-/, '')}`}
                              status="pending"
                            />
                            <PipelineStep
                              label="Wire Data"
                              command={`/build-os/wire-data ${milestone.id.replace(/^\d+-/, '')}`}
                              status="pending"
                            />
                            <PipelineStep
                              label="Validate"
                              command={`/build-os/validate ${milestone.id.replace(/^\d+-/, '')}`}
                              status="pending"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Status check */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardContent className="py-4">
            <CommandBlock
              command="/build-os/status"
              description="Check current build progress at any time:"
            />
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}

interface PipelineStepProps {
  label: string
  command: string
  status: string
}

function PipelineStep({ label, command, status }: PipelineStepProps) {
  const config = statusIcons[status] || statusIcons.pending
  const Icon = config.icon

  return (
    <div className="bg-stone-50 dark:bg-stone-800/50 rounded-md p-3">
      <div className="flex items-center gap-2 mb-1.5">
        <div className={`w-4 h-4 rounded-full flex items-center justify-center ${config.className}`}>
          <Icon className="w-2.5 h-2.5" strokeWidth={2.5} />
        </div>
        <span className="text-xs font-medium text-stone-700 dark:text-stone-300">{label}</span>
      </div>
      <code className="text-[11px] font-mono text-stone-500 dark:text-stone-400 break-all">
        {command}
      </code>
    </div>
  )
}
