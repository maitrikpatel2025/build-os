import { createBrowserRouter } from 'react-router-dom'
import { InitPage } from '@/components/InitPage'
import { ScaffoldPage } from '@/components/ScaffoldPage'
import { BuildPage } from '@/components/BuildPage'
import { ValidatePage } from '@/components/ValidatePage'
import { FinalizePage } from '@/components/FinalizePage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <InitPage />,
  },
  {
    path: '/scaffold',
    element: <ScaffoldPage />,
  },
  {
    path: '/build',
    element: <BuildPage />,
  },
  {
    path: '/validate',
    element: <ValidatePage />,
  },
  {
    path: '/finalize',
    element: <FinalizePage />,
  },
])
