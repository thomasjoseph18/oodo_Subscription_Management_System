import { useFetch } from '../hooks/useFetch'
import { label as titleCase } from '../utils/format'
import { Field } from './ui'

function RemoteSelect({ field, value, onChange, id }) {
  const { data } = useFetch(field.endpoint, { page_size: 100, ...field.params })
  const options = data?.results ?? data ?? []
  const text = field.optionLabel ?? ((option) => option.name)
  if (field.multiple) {
    return (
      <select id={id} multiple className="input h-28" value={(value ?? []).map(String)}
        onChange={(event) => onChange([...event.target.selectedOptions].map((option) => Number(option.value)))}>
        {options.map((option) => <option key={option.id} value={option.id}>{text(option)}</option>)}
      </select>
    )
  }
  return (
    <select id={id} className="input" value={value ?? ''} required={field.required}
      onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}>
      <option value="">Select…</option>
      {options.map((option) => <option key={option.id} value={option.id}>{text(option)}</option>)}
    </select>
  )
}

function Control({ field, value, onChange, id }) {
  switch (field.type) {
    case 'remote':
      return <RemoteSelect field={field} value={value} onChange={onChange} id={id} />
    case 'select':
      return (
        <select id={id} className="input" value={value ?? ''} required={field.required} onChange={(event) => onChange(event.target.value)}>
          <option value="">Select…</option>
          {field.options.map((option) => <option key={option} value={option}>{titleCase(option)}</option>)}
        </select>
      )
    case 'textarea':
      return <textarea id={id} className="input" rows={3} value={value ?? ''} onChange={(event) => onChange(event.target.value)} />
    case 'checkbox':
      return <input id={id} type="checkbox" className="h-5 w-5 accent-primary" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
    default:
      return (
        <input id={id} className="input" type={field.type ?? 'text'} step={field.type === 'number' ? '0.01' : undefined}
          min={field.type === 'number' ? '0' : undefined} required={field.required} value={value ?? ''}
          onChange={(event) => onChange(event.target.value === '' ? null : event.target.value)} />
      )
  }
}

export default function FormFields({ fields, values, errors, onChange }) {
  return (
    <div className="grid gap-x-4 md:grid-cols-2">
      {fields.map((field) => {
        const id = `field-${field.name}`
        return (
          <div key={field.name} className={field.type === 'textarea' || field.multiple ? 'md:col-span-2' : ''}>
            <Field id={id} label={field.label} error={errors?.[field.name]?.join?.(' ')} hint={field.hint}>
              <Control id={id} field={field} value={values[field.name]} onChange={(value) => onChange(field.name, value)} />
            </Field>
          </div>
        )
      })}
    </div>
  )
}
