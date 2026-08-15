import { CircleCheckBig, TriangleAlert, Clock } from 'lucide-react'

export const labels = [
  {
    value: 'bug',
    label: 'Bug',
  },
  {
    value: 'feature',
    label: 'Feature',
  },
  {
    value: 'documentation',
    label: 'Documentation',
  },
]

// Severity tiers drive badge color. Every status maps to exactly one tier:
//   critical -> red (destructive)   e.g. expired, denied, failed
//   warning  -> amber (warning)     e.g. expiring soon, needs review
//   good     -> green (success)     e.g. valid, approved, done
//   neutral  -> gray (secondary)    e.g. pending, queued, n/a
export type Severity = 'critical' | 'warning' | 'good' | 'neutral'

export const severityToBadgeVariant: Record<Severity, 'destructive' | 'warning' | 'success' | 'secondary'> = {
  critical: 'destructive',
  warning: 'warning',
  good: 'success',
  neutral: 'secondary',
}

// ClaimPack statuses — must match exactly what the backend poller writes to
// records.status (see README output contract).
export const statuses: {
  label: string
  value: string
  icon: typeof TriangleAlert
  severity: Severity
}[] = [
  { label: 'Valid', value: 'Valid', icon: CircleCheckBig, severity: 'good' as Severity },
  { label: 'Missing', value: 'Missing', icon: TriangleAlert, severity: 'critical' as Severity },
  { label: 'Expired', value: 'Expired', icon: Clock, severity: 'warning' as Severity },
  { label: 'Flagged', value: 'Flagged', icon: TriangleAlert, severity: 'warning' as Severity },
  { label: 'Awaiting Customer', value: 'Awaiting_Customer', icon: Clock, severity: 'warning' as Severity },
  { label: 'Duplicate', value: 'Duplicate', icon: Clock, severity: 'neutral' as Severity },
  { label: 'Unreadable', value: 'Unreadable', icon: Clock, severity: 'warning' as Severity },
]
