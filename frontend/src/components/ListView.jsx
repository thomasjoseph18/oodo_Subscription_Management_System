import { useEffect, useState } from 'react'
import { useFetch } from '../hooks/useFetch'
import { label } from '../utils/format'
import DataTable from './DataTable'
import NotBuilt from './NotBuilt'
import { Empty, ErrorState, Skeleton } from './ui'

/** Search, filters, sorting and pagination around a DataTable. */
export default function ListView({ endpoint, columns, filters = [], baseParams, rowLink, rowActions, emptyTitle = 'Nothing here yet', refreshKey }) {
  const [search, setSearch] = useState('')
  const [applied, setApplied] = useState('')
  const [filterValues, setFilterValues] = useState({})
  const [ordering, setOrdering] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => {
      setApplied(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  const params = { page, search: applied || undefined, ordering: ordering || undefined, ...baseParams, ...filterValues }
  const { data, loading, error, notBuilt, reload } = useFetch(endpoint, params)

  useEffect(() => {
    if (refreshKey) reload()
  }, [refreshKey, reload])

  if (notBuilt) return <NotBuilt />
  const rows = data?.results ?? []
  const pages = Math.max(1, Math.ceil((data?.count ?? 0) / 20))

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        <input type="search" className="input max-w-xs" placeholder="Search…" aria-label="Search" value={search} onChange={(event) => setSearch(event.target.value)} />
        {filters.map((filter) => (
          <select key={filter.name} className="input max-w-[12rem]" aria-label={filter.label} value={filterValues[filter.name] ?? ''}
            onChange={(event) => {
              setFilterValues({ ...filterValues, [filter.name]: event.target.value || undefined })
              setPage(1)
            }}>
            <option value="">{filter.label}: all</option>
            {filter.options.map((option) => <option key={option} value={option}>{label(option)}</option>)}
          </select>
        ))}
      </div>
      {loading && !data ? <Skeleton /> : error ? <ErrorState message={error} onRetry={reload} /> : rows.length === 0 ? <Empty title={emptyTitle} /> : (
        <>
          <DataTable columns={columns} rows={rows} ordering={ordering} onSort={setOrdering} rowLink={rowLink} rowActions={rowActions} />
          <div className="mt-4 flex items-center justify-between text-sm">
            <span className="text-muted">{data.count} records</span>
            <div className="flex items-center gap-2">
              <button className="btn btn-light btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
              <span>Page {page} of {pages}</span>
              <button className="btn btn-light btn-sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
