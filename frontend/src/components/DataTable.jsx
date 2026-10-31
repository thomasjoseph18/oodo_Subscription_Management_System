import { useNavigate } from 'react-router-dom'
import { date, money } from '../utils/format'
import { StatusBadge } from './ui'

function Cell({ column, row }) {
  const value = column.value ? column.value(row) : row[column.key]
  if (column.type === 'money') return money(value)
  if (column.type === 'date') return date(value)
  if (column.type === 'status') return <StatusBadge status={value} />
  if (column.type === 'bool') return value ? 'Yes' : 'No'
  return value ?? '—'
}

export default function DataTable({ columns, rows, ordering, onSort, rowLink, rowActions }) {
  const navigate = useNavigate()
  return (
    <div className="overflow-x-auto rounded-md border border-line">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="bg-subtle text-heading">
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" className="px-4 py-3 font-semibold whitespace-nowrap">
                {column.sortable === false || !onSort ? column.label : (
                  <button className="cursor-pointer font-semibold" onClick={() => onSort(ordering === column.key ? `-${column.key}` : column.key)}>
                    {column.label}{' '}
                    {ordering === column.key && <i className="fa-solid fa-arrow-up text-xs" aria-hidden="true" />}
                    {ordering === `-${column.key}` && <i className="fa-solid fa-arrow-down text-xs" aria-hidden="true" />}
                  </button>
                )}
              </th>
            ))}
            {rowActions && <th scope="col"><span className="sr-only">Actions</span></th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className={`border-t border-line ${rowLink ? 'cursor-pointer hover:bg-surface' : ''}`}
              onClick={rowLink ? () => navigate(rowLink(row)) : undefined}>
              {columns.map((column) => <td key={column.key} className="px-4 py-3"><Cell column={column} row={row} /></td>)}
              {rowActions && <td className="px-4 py-2 text-right whitespace-nowrap" onClick={(event) => event.stopPropagation()}>{rowActions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
