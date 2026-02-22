import { useMemo } from 'react'
import { ShieldCheck, TestTube, Eye, Bug } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AppLayout } from '@/components/AppLayout'
import { CommandBlock } from '@/components/CommandBlock'
import { StepIndicator } from '@/components/StepIndicator'
import { getSectionIds } from '@/lib/build-state-loader'

export function ValidatePage() {
  const sections = useMemo(() => getSectionIds(), [])

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-stone-900 dark:text-stone-100 mb-2">
            Validate
          </h1>
          <p className="text-stone-600 dark:text-stone-400">
            Run tests and visual validation for each section. Sections that pass are merged to main.
          </p>
        </div>

        {/* What validation does */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-stone-500 dark:text-stone-400" strokeWidth={1.5} />
              Validation Pipeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="bg-stone-50 dark:bg-stone-800/50 rounded-lg p-4">
                <TestTube className="w-5 h-5 text-stone-500 dark:text-stone-400 mb-2" strokeWidth={1.5} />
                <h4 className="font-medium text-stone-900 dark:text-stone-100 text-sm mb-1">Backend Tests</h4>
                <p className="text-xs text-stone-500 dark:text-stone-400">
                  pytest runs API tests for CRUD operations, edge cases, and status codes.
                </p>
              </div>
              <div className="bg-stone-50 dark:bg-stone-800/50 rounded-lg p-4">
                <Bug className="w-5 h-5 text-stone-500 dark:text-stone-400 mb-2" strokeWidth={1.5} />
                <h4 className="font-medium text-stone-900 dark:text-stone-100 text-sm mb-1">Frontend Build</h4>
                <p className="text-xs text-stone-500 dark:text-stone-400">
                  Vite build + ESLint validate compilation and code quality.
                </p>
              </div>
              <div className="bg-stone-50 dark:bg-stone-800/50 rounded-lg p-4">
                <Eye className="w-5 h-5 text-stone-500 dark:text-stone-400 mb-2" strokeWidth={1.5} />
                <h4 className="font-medium text-stone-900 dark:text-stone-100 text-sm mb-1">Visual Check</h4>
                <p className="text-xs text-stone-500 dark:text-stone-400">
                  Playwright screenshots compared against design mockups (if MCP configured).
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Per-section validation */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100">
              Validate by Section
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {sections.length > 0 ? (
              sections.map((sectionId, i) => (
                <StepIndicator
                  key={sectionId}
                  step={i + 1}
                  status="upcoming"
                  isLast={i === sections.length - 1}
                >
                  <div>
                    <h3 className="font-medium text-stone-900 dark:text-stone-100 capitalize mb-2">
                      {sectionId.replace(/-/g, ' ')}
                    </h3>
                    <CommandBlock command={`/build-os/validate ${sectionId}`} />
                  </div>
                </StepIndicator>
              ))
            ) : (
              <p className="text-sm text-stone-500 dark:text-stone-400">
                No sections detected. Load a product plan first.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Resume command */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardContent className="py-4">
            <CommandBlock
              command="/build-os/resume"
              description="If a validation fails, fix the issues and resume from where you left off:"
            />
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
