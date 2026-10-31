import { useEffect, useRef } from 'react'
import { label } from '../utils/format'

const STATUS_STYLES = {
  green: 'bg-[#d4edda] text-[#155724]',
  blue: 'bg-[#d1ecf1] text-[#0c5460]',
  amber: 'bg-[#fff3cd] text-[#664d03]',
  red: 'bg-[#f8d7da] text-[#721c24]',
  gray: 'bg-subtle text-body',
}
const STATUS_COLORS = {
  active: 'green', paid: 'green', accepted: 'green', completed: 'green',
  confirmed: 'blue', sent: 'blue', quotation: 'blue', partial: 'blue', renewed: 'blue',
  paused: 'amber', draft: 'amber', unpaid: 'amber', pending: 'amber',
  overdue: 'red', rejected: 'red', expired: 'red', failed: 'red', cancelled: 'red',
}

export function Logo({ className = '' }) {
  return (
    <span className={`font-script text-3xl leading-none font-bold text-primary ${className}`}>
      bright<span className="text-[#8f8f8f]">loop</span>
    </span>
  )
}

export function Highlight({ children, color = '#fbb130' }) {
  return (
    <span className="highlight">
      {children}
      <svg viewBox="0 0 200 20" preserveAspectRatio="none" aria-hidden="true">
        <path d="M2 12 C 40 4, 90 18, 198 7" fill="none" stroke={color} strokeWidth="9" strokeLinecap="round" opacity="0.75" />
      </svg>
    </span>
  )
}

export function StatusBadge({ status }) {
  return <span className={`badge ${STATUS_STYLES[STATUS_COLORS[status] ?? 'gray']}`}>{label(status)}</span>
}

export function Field({ label: text, error, hint, children, id }) {
  return (
    <div className="mb-4">
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-heading">{text}</label>
      {children}
      {hint && <p className="mt-1 text-sm text-muted">{hint}</p>}
      {error && <p className="mt-1 text-sm text-danger" role="alert">{error}</p>}
    </div>
  )
}

export function Modal({ title, onClose, children }) {
  const ref = useRef(null)
  useEffect(() => {
    ref.current?.focus()
    const onKey = (event) => event.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-black/40 p-4">
      <div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title} className="my-8 w-full max-w-2xl rounded-md bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h4 className="text-xl">{title}</h4>
          <button className="cursor-pointer text-muted" onClick={onClose} aria-label="Close"><i className="fa-solid fa-xmark" /></button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function ConfirmDialog({ title, message, confirmLabel = 'Confirm', danger, onConfirm, onClose }) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="mb-6">{message}</p>
      <div className="flex justify-end gap-2">
        <button className="btn btn-light" onClick={onClose}>Keep as is</button>
        <button className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`} onClick={onConfirm}>{confirmLabel}</button>
      </div>
    </Modal>
  )
}

export function Empty({ icon = 'fa-inbox', title, message, action }) {
  return (
    <div className="py-12 text-center">
      <i className={`fa-solid ${icon} mb-3 text-4xl text-[#adb5bd]`} aria-hidden="true" />
      <p className="display display-5 mb-2">{title}</p>
      {message && <p className="text-muted">{message}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="py-12 text-center" role="alert">
      <i className="fa-solid fa-triangle-exclamation mb-3 text-4xl text-danger" aria-hidden="true" />
      <p className="mb-4">{message}</p>
      {onRetry && <button className="btn btn-light" onClick={onRetry}>Try again</button>}
    </div>
  )
}

export function Skeleton({ rows = 5 }) {
  return (
    <div className="animate-pulse space-y-3" aria-label="Loading">
      {Array.from({ length: rows }, (_, index) => <div key={index} className="h-9 rounded-sm bg-subtle" />)}
    </div>
  )
}

export function Stat({ title, value, tone }) {
  return (
    <div className="card">
      <p className="text-sm text-muted">{title}</p>
      <p className={`mt-1 text-2xl font-semibold ${tone === 'danger' ? 'text-danger' : 'text-heading'}`}>{value}</p>
    </div>
  )
}

export function PageHeader({ title, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-3xl">{title}</h1>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}
