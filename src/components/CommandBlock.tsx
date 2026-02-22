import { Terminal } from 'lucide-react'

interface CommandBlockProps {
  command: string
  description?: string
}

export function CommandBlock({ command, description }: CommandBlockProps) {
  return (
    <div className="space-y-2">
      {description && (
        <p className="text-stone-600 dark:text-stone-400 text-sm">{description}</p>
      )}
      <div className="bg-stone-100 dark:bg-stone-800 rounded-md px-4 py-3 flex items-center gap-3">
        <Terminal className="w-4 h-4 text-stone-400 dark:text-stone-500 shrink-0" strokeWidth={1.5} />
        <code className="text-sm font-mono text-stone-800 dark:text-stone-200">
          {command}
        </code>
      </div>
    </div>
  )
}
