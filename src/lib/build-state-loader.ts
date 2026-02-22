/**
 * Build state loader for the Build OS dashboard.
 *
 * Checks for the existence of key files/directories to determine
 * pipeline phase completion status. Uses Vite's import.meta.glob
 * for static file discovery.
 */

export interface BuildMilestone {
  id: string
  name: string
  section_id: string | null
  status: string
  worktree_path?: string
  backend_port?: number
  frontend_port?: number
}

export interface BuildState {
  build_id: string
  product_name: string
  product_plan_path: string
  tech_stack: {
    frontend: string
    backend: string
    styling: string
    database: string
  }
  milestones: BuildMilestone[]
  design_system: {
    primary: string
    secondary: string
    neutral: string
  }
  entities: string[]
  current_milestone: string | null
  model_set: string
  total_cost: number
  output_path?: string
  created_at?: string
  updated_at?: string
}

/**
 * Check if a product-plan directory has been loaded.
 * Uses Vite's glob to check for the product-overview.md file.
 */
export function hasProductPlan(): boolean {
  const files = import.meta.glob('/product-plan/product-overview.md', { eager: true })
  return Object.keys(files).length > 0
}

/**
 * Get all milestone instruction files from product-plan.
 */
export function getMilestoneFiles(): string[] {
  const files = import.meta.glob('/product-plan/instructions/incremental/*.md', { eager: true })
  return Object.keys(files).sort()
}

/**
 * Get all section IDs from product-plan.
 */
export function getSectionIds(): string[] {
  const files = import.meta.glob('/product-plan/sections/*/README.md', { eager: true })
  return Object.keys(files)
    .map(path => {
      const match = path.match(/\/product-plan\/sections\/([^/]+)\/README\.md$/)
      return match ? match[1] : null
    })
    .filter((id): id is string => id !== null)
    .sort()
}

/**
 * Check if build state files exist.
 */
export function getBuildStateFiles(): string[] {
  const files = import.meta.glob('/agents/*/build_state.json', { eager: true })
  return Object.keys(files)
}

/**
 * Check if output project exists.
 */
export function hasOutputProject(): boolean {
  const files = import.meta.glob('/output/*/README.md', { eager: true })
  return Object.keys(files).length > 0
}

/**
 * Determine phase completion status for the pipeline navigation.
 */
export interface PhaseStatus {
  init: boolean
  scaffold: boolean
  build: boolean
  validate: boolean
  finalize: boolean
}

export function getPhaseStatuses(): PhaseStatus {
  return {
    init: getBuildStateFiles().length > 0,
    scaffold: hasOutputProject(),
    build: false, // Would need to check milestone statuses
    validate: false,
    finalize: false,
  }
}
