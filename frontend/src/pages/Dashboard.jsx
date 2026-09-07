import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../auth/useAuth'
import { ActionChip } from '../components/ActionChip'
import { Skeleton } from '../components/Skeleton'
import { auditApi, rolesApi, usersApi } from '../api/resources'
import { formatTimestamp, roleLabel } from '../lib/format'

function StatCard({ label, value, brand, loading }) {
  return (
    <div className="card stat-card">
      <div className="label">{label}</div>
      <div className={brand ? 'value brand' : 'value'}>
        {loading ? <Skeleton width={64} height={28} /> : value}
      </div>
    </div>
  )
}

function auditSummary(row) {
  const who = row.actor_email || 'system'
  const target = row.target_id ? ` ${row.target_type} ${row.target_id}` : ''
  return `${who} · ${row.action}${target}`
}

export function Dashboard() {
  const { roles, permissions, hasPerm } = useAuth()
  const canAudit = hasPerm('audit.view')

  const totalUsers = useQuery({
    queryKey: ['dash', 'users', 'total'],
    queryFn: () => usersApi.list({ page_size: 1 }),
  })
  const activeUsers = useQuery({
    queryKey: ['dash', 'users', 'active'],
    queryFn: () => usersApi.list({ page_size: 1, is_active: 'true' }),
  })
  const roleCount = useQuery({
    queryKey: ['dash', 'roles'],
    queryFn: () => rolesApi.list({ page_size: 1 }),
  })
  const auditCount = useQuery({
    queryKey: ['dash', 'audit', 'count'],
    queryFn: () => auditApi.list({ page_size: 1 }),
    enabled: canAudit,
  })
  const recent = useQuery({
    queryKey: ['dash', 'audit', 'recent'],
    queryFn: () => auditApi.list({ page_size: 6, ordering: '-created_at' }),
    enabled: canAudit,
  })

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-subtitle">
            Signed in as {roleLabel(roles)} — {permissions.length} permissions
          </p>
        </div>
      </div>

      <div className="stat-grid">
        <StatCard
          label="Total users"
          value={totalUsers.data?.count ?? 0}
          loading={totalUsers.isLoading}
        />
        <StatCard
          label="Active"
          brand
          value={activeUsers.data?.count ?? 0}
          loading={activeUsers.isLoading}
        />
        <StatCard label="Roles" value={roleCount.data?.count ?? 0} loading={roleCount.isLoading} />
        <StatCard
          label="Audit events"
          value={canAudit ? (auditCount.data?.count ?? 0) : '—'}
          loading={canAudit && auditCount.isLoading}
        />
      </div>

      <div className="card activity-card">
        <div className="activity-head">
          <h2>Recent activity</h2>
          {canAudit && <Link to="/audit">View audit log →</Link>}
        </div>

        {!canAudit && (
          <div className="activity-row">
            <span className="summary">Audit log access required to see recent activity.</span>
          </div>
        )}

        {canAudit && recent.isLoading && (
          <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} height={16} />
            ))}
          </div>
        )}

        {canAudit &&
          !recent.isLoading &&
          (recent.data?.results ?? []).map((row) => (
            <div key={row.id} className="activity-row">
              <span className="ts">{formatTimestamp(row.created_at)}</span>
              <ActionChip action={row.action} />
              <span className="summary">{auditSummary(row)}</span>
            </div>
          ))}

        {canAudit && !recent.isLoading && (recent.data?.results ?? []).length === 0 && (
          <div className="activity-row">
            <span className="summary">No activity recorded yet.</span>
          </div>
        )}
      </div>
    </div>
  )
}
