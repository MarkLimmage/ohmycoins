import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_layout/audit')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/_layout/audit"!</div>
}
