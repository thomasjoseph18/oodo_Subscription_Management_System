import { date, money } from '../utils/format'

export function LinesTable({ lines }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="bg-subtle text-heading">
          <tr>
            {['Product', 'Qty', 'Unit price', 'Discount', 'Tax', 'Amount'].map((title) => <th key={title} scope="col" className="px-3 py-2 font-semibold">{title}</th>)}
          </tr>
        </thead>
        <tbody>
          {lines.map((line) => (
            <tr key={line.id} className="border-t border-line">
              <td className="px-3 py-2">{line.description}</td>
              <td className="px-3 py-2">{line.quantity}</td>
              <td className="px-3 py-2">{money(line.unit_price)}</td>
              <td className="px-3 py-2">{money(line.discount_amount)}</td>
              <td className="px-3 py-2">{money(line.tax_amount)}</td>
              <td className="px-3 py-2">{money(line.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Totals({ record }) {
  const rows = [['Subtotal', record.subtotal], ['Discount', record.discount_total], ['Tax', record.tax_total], ['Total', record.total]]
  return (
    <dl className="ml-auto mt-4 max-w-xs text-sm">
      {rows.map(([name, value]) => (
        <div key={name} className="flex justify-between py-1">
          <dt>{name}</dt>
          <dd className={name === 'Total' ? 'font-semibold text-heading' : ''}>{money(value)}</dd>
        </div>
      ))}
    </dl>
  )
}

export function Facts({ items }) {
  return (
    <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
      {items.map(([name, value]) => (
        <div key={name}>
          <dt className="text-muted">{name}</dt>
          <dd className="font-medium text-heading">{value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  )
}

export function Timeline({ events }) {
  return (
    <ol className="space-y-2 text-sm">
      {events.map((event) => (
        <li key={event.id} className="flex gap-3">
          <span className="text-muted">{date(event.created_at)}</span>
          <span>{event.message}{event.actor_email ? ` (${event.actor_email})` : ''}</span>
        </li>
      ))}
    </ol>
  )
}
