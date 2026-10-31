import { useFetch } from '../hooks/useFetch'

/** Editable product lines. Prices are shown by the server after saving, so
 * no money is calculated in the browser. */
export default function LineEditor({ lines, onChange }) {
  const products = useFetch('/products/', { page_size: 100, status: 'active' }).data?.results ?? []
  const variants = useFetch('/variants/', { page_size: 100 }).data?.results ?? []
  const update = (index, patch) => onChange(lines.map((line, position) => (position === index ? { ...line, ...patch } : line)))

  return (
    <div className="mb-4">
      <p className="mb-1 text-sm font-medium text-heading">Product lines</p>
      {lines.map((line, index) => (
        <div key={index} className="mb-2 grid grid-cols-[1fr_1fr_5rem_auto] gap-2">
          <select aria-label="Product" className="input" required value={line.product ?? ''} onChange={(event) => update(index, { product: Number(event.target.value), variant: null })}>
            <option value="">Product…</option>
            {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
          </select>
          <select aria-label="Variant" className="input" value={line.variant ?? ''} onChange={(event) => update(index, { variant: event.target.value ? Number(event.target.value) : null })}>
            <option value="">No variant</option>
            {variants.filter((variant) => variant.product === line.product).map((variant) => <option key={variant.id} value={variant.id}>{variant.name}</option>)}
          </select>
          <input aria-label="Quantity" type="number" min="1" className="input" required value={line.quantity ?? 1} onChange={(event) => update(index, { quantity: Number(event.target.value) })} />
          <button type="button" className="btn btn-light btn-sm" aria-label="Remove line" onClick={() => onChange(lines.filter((_, position) => position !== index))}><i className="fa-solid fa-trash" /></button>
        </div>
      ))}
      <button type="button" className="btn btn-light btn-sm" onClick={() => onChange([...lines, { quantity: 1 }])}>Add a line</button>
    </div>
  )
}
