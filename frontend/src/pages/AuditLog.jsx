import { DataTable } from '../components/DataTable'
import { ActionChip } from '../components/ActionChip'
import { auditApi } from '../api/resources'
import { formatTimestamp } from '../lib/format'

function detail(row) {
  if (row.target_type && row.target_id) return `${row.target_type} ${row.target_id}`
  if (row.target_type) return row.target_type
  const changed = row.changes && Object.keys(row.changes)
  return changed && changed.length ? changed.join(', ') : '—'
}

const columns = [
  {
    key: 'created_at',
    header: 'Timestamp',
    sortKey: 'created_at',
    cellClass: 'mono',
    render: (r) => formatTimestamp(r.created_at),
  },
  { key: 'actor', header: 'Actor', render: (r) => r.actor_email || 'system' },
  { key: 'action', header: 'Action', render: (r) => <ActionChip action={r.action} /> },
  { key: 'detail', header: 'Detail', render: detail },
]

/* The category select writes ?search=, since the Phase 1/2 API filters `action`
   by exact match only; icontains on the action prefix gives the grouping. */
const filters = [
  {
    key: 'search',
    label: 'Action',
    options: [
      { value: '', label: 'All actions' },
      { value: 'auth.', label: 'Auth' },
      { value: 'user.', label: 'User changes' },
      { value: 'role.', label: 'Role changes' },
    ],
  },
]

export function AuditLog() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Audit Log</h1>
          <p className="page-subtitle">Append-only record of every sensitive action</p>
        </div>
      </div>

      <DataTable
        queryKey={['audit-logs']}
        fetcher={(params) => auditApi.list(params)}
        columns={columns}
        filters={filters}
        exportFn={(params) => auditApi.export(params)}
        emptyTitle="No audit entries match your filter"
      />
    </div>
  )
}
