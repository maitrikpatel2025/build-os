import { useMemo } from 'react'
import { Check, Package, FolderTree, Play } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AppLayout } from '@/components/AppLayout'
import { CommandBlock } from '@/components/CommandBlock'
import { hasOutputProject } from '@/lib/build-state-loader'

export function FinalizePage() {
  const hasOutput = useMemo(() => hasOutputProject(), [])

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-stone-900 dark:text-stone-100 mb-2">
            Finalize
          </h1>
          <p className="text-stone-600 dark:text-stone-400">
            Final review, cleanup, and prepare the built application for deployment.
          </p>
        </div>

        {/* Finalize command */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
              <Package className="w-5 h-5 text-stone-500 dark:text-stone-400" strokeWidth={1.5} />
              Finalize Build
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <CommandBlock
              command="/build-os/finalize"
              description="Run this to clean up worktrees, run full test suite, and generate final documentation:"
            />
          </CardContent>
        </Card>

        {/* What finalize does */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
              <FolderTree className="w-5 h-5 text-stone-500 dark:text-stone-400" strokeWidth={1.5} />
              What Finalize Does
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              <CheckItem label="Clean up all remaining worktrees" />
              <CheckItem label="Run full backend test suite (all sections)" />
              <CheckItem label="Run frontend build validation" />
              <CheckItem label="Run lint checks (ruff + eslint)" />
              <CheckItem label="Generate project README with setup instructions" />
              <CheckItem label="Report build summary with cost tracking" />
            </div>
          </CardContent>
        </Card>

        {/* Start the app */}
        {hasOutput && (
          <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
                <Play className="w-5 h-5 text-lime-600 dark:text-lime-400" strokeWidth={1.5} />
                Start Your Application
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2 p-3 bg-lime-50 dark:bg-lime-900/20 rounded-lg border border-lime-200 dark:border-lime-800">
                <Check className="w-4 h-4 text-lime-600 dark:text-lime-400" strokeWidth={2.5} />
                <span className="text-sm font-medium text-stone-900 dark:text-stone-100">
                  Output project detected
                </span>
              </div>

              <div className="space-y-3">
                <CommandBlock
                  command="cd output/{product-name} && ./scripts/start.sh"
                  description="Start both frontend and backend:"
                />
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-stone-50 dark:bg-stone-800/50 rounded-lg p-3 text-center">
                    <div className="text-sm font-mono text-stone-700 dark:text-stone-300">Frontend</div>
                    <div className="text-xs text-stone-500 dark:text-stone-400">http://localhost:3000</div>
                  </div>
                  <div className="bg-stone-50 dark:bg-stone-800/50 rounded-lg p-3 text-center">
                    <div className="text-sm font-mono text-stone-700 dark:text-stone-300">Backend</div>
                    <div className="text-xs text-stone-500 dark:text-stone-400">http://localhost:8000</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* SDK orchestration */}
        <Card className="border-stone-200 dark:border-stone-700 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-stone-900 dark:text-stone-100">
              SDK Orchestration (Advanced)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-stone-600 dark:text-stone-400">
              For fully automated builds, use the SDK orchestration scripts directly:
            </p>
            <CommandBlock command="uv run python adws/adw_workflows/build_all.py --build-id <id>" />
            <div className="grid sm:grid-cols-2 gap-3 mt-2">
              <div className="bg-stone-50 dark:bg-stone-800/50 rounded-md p-3">
                <code className="text-[11px] font-mono text-stone-600 dark:text-stone-400">build_all.py</code>
                <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">Full pipeline</p>
              </div>
              <div className="bg-stone-50 dark:bg-stone-800/50 rounded-md p-3">
                <code className="text-[11px] font-mono text-stone-600 dark:text-stone-400">build_milestone.py</code>
                <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">Single milestone</p>
              </div>
              <div className="bg-stone-50 dark:bg-stone-800/50 rounded-md p-3">
                <code className="text-[11px] font-mono text-stone-600 dark:text-stone-400">build_section_only.py</code>
                <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">Frontend only</p>
              </div>
              <div className="bg-stone-50 dark:bg-stone-800/50 rounded-md p-3">
                <code className="text-[11px] font-mono text-stone-600 dark:text-stone-400">build_and_validate.py</code>
                <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">Build + validate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}

function CheckItem({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 py-1">
      <div className="w-4 h-4 rounded border-2 border-stone-300 dark:border-stone-600" />
      <span className="text-sm text-stone-700 dark:text-stone-300">{label}</span>
    </div>
  )
}
