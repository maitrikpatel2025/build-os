import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, Layers, FolderTree, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AppLayout } from '@/components/AppLayout'
import { CommandBlock } from '@/components/CommandBlock'
import { StepIndicator } from '@/components/StepIndicator'
import { getBuildStateFiles, hasOutputProject } from '@/lib/build-state-loader'
import type { StepStatus } from '@/components/StepIndicator'

export function ScaffoldPage() {
  const navigate = useNavigate()

  const hasInit = useMemo(() => getBuildStateFiles().length > 0, [])
  const hasOutput = useMemo(() => hasOutputProject(), [])

  const step1Status: StepStatus = hasOutput ? 'completed' : hasInit ? 'current' : 'upcoming'

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-stone-900 dark:text-stone-100 mb-2">
            Scaffold Project
          </h1>
          <p className="text-stone-600 dark:text-stone-400">
            Generate the full-stack project structure with React frontend, FastAPI backend, and design system configuration.
          </p>
        </div>

        {/* Step 1: Scaffold */}
        <StepIndicator step={1} status={step1Status} isLast={!hasOutput}>
          <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
                <Layers className="w-5 h-5 text-stone-500 dark:text-stone-400" strokeWidth={1.5} />
                {hasOutput ? 'Project Scaffolded' : 'Generate Project Structure'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {hasOutput ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 p-3 bg-lime-50 dark:bg-lime-900/20 rounded-lg border border-lime-200 dark:border-lime-800">
                    <Check className="w-4 h-4 text-lime-600 dark:text-lime-400" strokeWidth={2.5} />
                    <span className="text-sm font-medium text-stone-900 dark:text-stone-100">
                      Project scaffolded successfully
                    </span>
                  </div>

                  {/* Project structure preview */}
                  <div className="bg-stone-50 dark:bg-stone-800/50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-stone-500 dark:text-stone-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                      <FolderTree className="w-4 h-4" strokeWidth={1.5} />
                      Output Structure
                    </h4>
                    <pre className="text-xs font-mono text-stone-600 dark:text-stone-400 leading-relaxed">
{`output/{product}/
├── app/
│   ├── client/          # React + Vite + Tailwind
│   │   ├── src/
│   │   │   ├── shell/   # App shell (nav, layout)
│   │   │   ├── sections/# Per-section pages
│   │   │   └── api/     # API client services
│   │   └── package.json
│   └── server/          # FastAPI + SQLAlchemy
│       ├── server.py    # Entry point
│       ├── routes/      # API routes
│       ├── models/      # Pydantic models
│       └── tests/       # pytest tests
├── scripts/
│   ├── start.sh
│   └── stop.sh
└── README.md`}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {!hasInit && (
                    <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                      <span className="text-sm text-stone-700 dark:text-stone-300">
                        Run <code className="font-mono">/build-os/init</code> first
                      </span>
                    </div>
                  )}
                  <CommandBlock
                    command="/build-os/scaffold"
                    description="Run this command in Claude Code to generate the project:"
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </StepIndicator>

        {/* Next Phase */}
        {hasOutput && (
          <StepIndicator step={2} status="current" isLast>
            <Button
              onClick={() => navigate('/build')}
              className="w-full justify-between h-12"
            >
              <span>Continue to Build</span>
              <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
            </Button>
          </StepIndicator>
        )}
      </div>
    </AppLayout>
  )
}
