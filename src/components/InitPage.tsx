import { useMemo } from 'react'
import { Check, AlertTriangle, FolderInput, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AppLayout } from '@/components/AppLayout'
import { CommandBlock } from '@/components/CommandBlock'
import { StepIndicator } from '@/components/StepIndicator'
import { hasProductPlan, getMilestoneFiles, getSectionIds, getBuildStateFiles } from '@/lib/build-state-loader'
import type { StepStatus } from '@/components/StepIndicator'

export function InitPage() {
  const navigate = useNavigate()

  const hasPlan = useMemo(() => hasProductPlan(), [])
  const milestones = useMemo(() => getMilestoneFiles(), [])
  const sections = useMemo(() => getSectionIds(), [])
  const buildStates = useMemo(() => getBuildStateFiles(), [])
  const hasInit = buildStates.length > 0

  const step1Status: StepStatus = hasPlan ? 'completed' : 'current'
  const step2Status: StepStatus = hasInit ? 'completed' : hasPlan ? 'current' : 'upcoming'

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page intro */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-stone-900 dark:text-stone-100 mb-2">
            Initialize Build
          </h1>
          <p className="text-stone-600 dark:text-stone-400">
            Ingest a Design OS <code className="font-mono text-stone-800 dark:text-stone-200">product-plan/</code> folder
            and create the build state that drives the pipeline.
          </p>
        </div>

        {/* Step 1: Product Plan */}
        <StepIndicator step={1} status={step1Status}>
          <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
                <FolderInput className="w-5 h-5 text-stone-500 dark:text-stone-400" strokeWidth={1.5} />
                Load Product Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {hasPlan ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 p-3 bg-lime-50 dark:bg-lime-900/20 rounded-lg border border-lime-200 dark:border-lime-800">
                    <Check className="w-4 h-4 text-lime-600 dark:text-lime-400" strokeWidth={2.5} />
                    <span className="text-sm font-medium text-stone-900 dark:text-stone-100">
                      Product plan detected
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-stone-50 dark:bg-stone-800/50 rounded-lg p-3">
                      <div className="text-2xl font-bold text-stone-900 dark:text-stone-100">{milestones.length}</div>
                      <div className="text-xs text-stone-500 dark:text-stone-400">Milestones</div>
                    </div>
                    <div className="bg-stone-50 dark:bg-stone-800/50 rounded-lg p-3">
                      <div className="text-2xl font-bold text-stone-900 dark:text-stone-100">{sections.length}</div>
                      <div className="text-xs text-stone-500 dark:text-stone-400">Sections</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                    <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" strokeWidth={2} />
                    <span className="text-sm text-stone-700 dark:text-stone-300">
                      No product plan found. Copy your Design OS export first.
                    </span>
                  </div>
                  <CommandBlock
                    command="cp -r /path/to/design-os/product-plan/ ./product-plan/"
                    description="Copy your Design OS export into the Build OS project:"
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </StepIndicator>

        {/* Step 2: Initialize */}
        <StepIndicator step={2} status={step2Status} isLast={!hasInit}>
          <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100">
                {hasInit ? 'Build Initialized' : 'Run Init Command'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {hasInit ? (
                <div className="flex items-center gap-2 p-3 bg-lime-50 dark:bg-lime-900/20 rounded-lg border border-lime-200 dark:border-lime-800">
                  <Check className="w-4 h-4 text-lime-600 dark:text-lime-400" strokeWidth={2.5} />
                  <span className="text-sm font-medium text-stone-900 dark:text-stone-100">
                    Build state created
                  </span>
                </div>
              ) : (
                <CommandBlock
                  command="/build-os/init"
                  description="Run this command in Claude Code to parse the product plan and create the build state:"
                />
              )}
            </CardContent>
          </Card>
        </StepIndicator>

        {/* Next Phase */}
        {hasInit && (
          <StepIndicator step={3} status="current" isLast>
            <Button
              onClick={() => navigate('/scaffold')}
              className="w-full justify-between h-12"
            >
              <span>Continue to Scaffold</span>
              <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
            </Button>
          </StepIndicator>
        )}
      </div>
    </AppLayout>
  )
}
