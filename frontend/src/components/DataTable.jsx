import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { IconChevronLeft, IconChevronRight, IconDownload, IconSearch } from './icons'
import { SkeletonRows } from './Skeleton'
import { useToast } from './useToast'
import { errorMessage } from '../lib/apiError'

const DEFAULT_PAGE_SIZE = 25

/* The single shared table for Users and Audit Log (SENTRA_BUILD_SPEC.md §8).
   All view state — search, filters, sort, page — lives in the URL query string,
   so refresh and shared links reproduce the same view. */
export function DataTable({
  queryKey,
  fetcher,
  columns,
  filters = [],
  searchable = false,
  searchPlaceholder = 'Search…',
  exportFn,
  rowActions,
  emptyTitle = 'Nothing here yet',
  emptyAction = null,
}) {
  const toast = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const [exporting, setExporting] = useState(false)

  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10) || 1)
  const pageSize = parseInt(searchParams.get('page_size') || String(DEFAULT_PAGE_SIZE), 10)
  const ordering = searchParams.get('ordering') || ''
  const search = searchParams.get('search') || ''

  const params = { page, page_size: pageSize }
  if (ordering) params.ordering = ordering
  if (search) params.search = search
  for (const f of filters) {
    const v = searchParams.get(f.key)
    if (v) params[f.key] = v
  }

  const query = useQuery({
    queryKey: [...queryKey, params],
    queryFn: () => fetcher(params),
    placeholderData: (prev) => prev,
  })

  const patchParams = (patch, { resetPage = true } = {}) => {
    const next = new URLSearchParams(searchParams)
    for (const [k, v] of Object.entries(patch)) {
      if (v === '' || v == null) next.delete(k)
      else next.set(k, v)
    }
    if (resetPage) next.delete('page')
    setSearchParams(next, { replace: true })
  }

  const toggleSort = (col) => {
    if (!col.sortKey) return
    if (ordering === col.sortKey) patchParams({ ordering: `-${col.sortKey}` })
    else if (ordering === `-${col.sortKey}`) patchParams({ ordering: '' })
    else patchParams({ ordering: col.sortKey })
  }

  const sortIndicator = (col) => {
    if (ordering === col.sortKey) return '▲'
    if (ordering === `-${col.sortKey}`) return '▼'
    return ''
  }

  const runExport = async () => {
    if (!exportFn) return
    setExporting(true)
    try {
      await exportFn(params)
      toast.success('Export downloaded')
    } catch (err) {
      toast.error(errorMessage(err, 'Export failed'))
    } finally {
      setExporting(false)
    }
  }

  const data = query.data
  const rows = data?.results ?? []
  const total = data?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const firstRow = total === 0 ? 0 : (page - 1) * pageSize + 1
  const lastRow = Math.min(page * pageSize, total)
  const colCount = columns.length + (rowActions ? 1 : 0)

  return (
    <div>
      <div className="toolbar">
        {searchable && (
          <div className="search">
            <IconSearch />
            <input
              className="input"
              placeholder={searchPlaceholder}
              defaultValue={search}
              key={search}
              onKeyDown={(e) => {
                if (e.key === 'Enter') patchParams({ search: e.currentTarget.value.trim() })
              }}
              onBlur={(e) => {
                if (e.currentTarget.value.trim() !== search)
                  patchParams({ search: e.currentTarget.value.trim() })
              }}
            />
          </div>
        )}

        {filters.map((f) => (
          <select
            key={f.key}
            className="select"
            value={searchParams.get(f.key) || ''}
            onChange={(e) => patchParams({ [f.key]: e.target.value })}
            aria-label={f.label}
          >
            {f.options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        ))}

        <span className="spacer" />

        {exportFn && (
          <button className="btn btn-secondary" onClick={runExport} disabled={exporting}>
            <IconDownload />
            {exporting ? 'Exporting…' : 'Export to Excel'}
          </button>
        )}
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={col.sortKey ? 'sortable' : undefined}
                    onClick={() => toggleSort(col)}
                  >
                    {col.header}
                    {col.sortKey && <span className="sort-ind">{sortIndicator(col)}</span>}
                  </th>
                ))}
                {rowActions && <th style={{ textAlign: 'right' }}>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {query.isLoading && <SkeletonRows rows={6} cols={colCount} />}

              {!query.isLoading && query.isError && (
                <tr>
                  <td colSpan={colCount}>
                    <div className="empty-state">
                      <h3>Couldn&rsquo;t load data</h3>
                      <p>{errorMessage(query.error)}</p>
                    </div>
                  </td>
                </tr>
              )}

              {!query.isLoading && !query.isError && rows.length === 0 && (
                <tr>
                  <td colSpan={colCount}>
                    <div className="empty-state">
                      <h3>{emptyTitle}</h3>
                      {emptyAction}
                    </div>
                  </td>
                </tr>
              )}

              {!query.isError &&
                rows.map((row) => (
                  <tr key={row.id}>
                    {columns.map((col) => (
                      <td key={col.key} className={col.cellClass}>
                        {col.render ? col.render(row) : row[col.key]}
                      </td>
                    ))}
                    {rowActions && <td className="cell-actions">{rowActions(row)}</td>}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="table-footer">
          <span>{total === 0 ? 'No results' : `Showing ${firstRow}–${lastRow} of ${total}`}</span>
          <span className="hint">server-side · page_size={pageSize}</span>
          <span className="spacer" />
          <div className="pager">
            <button
              className="btn btn-secondary btn-sm"
              disabled={page <= 1}
              onClick={() => patchParams({ page: page - 1 }, { resetPage: false })}
            >
              <IconChevronLeft />
              Prev
            </button>
            <span className="mono" style={{ fontSize: 12 }}>
              Page {page} / {totalPages}
            </span>
            <button
              className="btn btn-secondary btn-sm"
              disabled={page >= totalPages}
              onClick={() => patchParams({ page: page + 1 }, { resetPage: false })}
            >
              Next
              <IconChevronRight />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
