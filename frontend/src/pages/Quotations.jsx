import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import FormFields from '../components/FormFields'
import LineEditor from '../components/LineEditor'
import ListView from '../components/ListView'
import NotBuilt from '../components/NotBuilt'
import { Facts, LinesTable, Totals } from '../components/Totals'
import { ErrorState, Modal, PageHeader, Skeleton, StatusBadge } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useAction } from '../hooks/useAction'
import { useFetch } from '../hooks/useFetch'
import api, { downloadPdf, errorMessage } from '../services/api'
import { fieldRefs } from '../routes/resources'
import { date } from '../utils/format'

const COLUMNS = [
  { key: 'number', label: 'Number' },
  { key: 'customer_name', label: 'Customer', sortable: false },
  { key: 'plan_name', label: 'Plan', sortable: false },
  { key: 'valid_until', label: 'Valid until', type: 'date' },
  { key: 'total', label: 'Total', type: 'money' },
  { key: 'status', label: 'Status', type: 'status' },
]
const FIELDS = [
  { name: 'customer', label: 'Customer', required: true, ...fieldRefs.customer },
  { name: 'template', label: 'Start from template', type: 'remote', endpoint: '/quotation-templates/', hint: 'Fills in the plan, lines, terms and validity.' },
  { name: 'plan', label: 'Plan', ...fieldRefs.plan, hint: 'Leave empty when using a template.' },
  { name: 'payment_term', label: 'Payment terms', ...fieldRefs.term },
]

export function QuotationList() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [form, setForm] = useState(null)

  async function create(event) {
    event.preventDefault()
    try {
      const { data } = await api.post('/quotations/', form)
      navigate(`${data.id}`)
    } catch (error) {
      toast(errorMessage(error), 'error')
    }
  }

  return (
    <>
      <PageHeader title="Quotations" actions={<button className="btn btn-primary" onClick={() => setForm({ lines: [] })}>New quotation</button>} />
      <ListView endpoint="/quotations/" columns={COLUMNS} rowLink={(row) => `${row.id}`} filters={[{ name: 'status', label: 'Status', options: ['draft', 'sent', 'accepted', 'rejected', 'expired'] }]} emptyTitle="No quotations yet" />
      {form && (
        <Modal title="New quotation" onClose={() => setForm(null)}>
          <form onSubmit={create}>
            <FormFields fields={FIELDS} values={form} onChange={(name, value) => setForm({ ...form, [name]: value })} />
            <LineEditor lines={form.lines} onChange={(lines) => setForm({ ...form, lines })} />
            <button className="btn btn-primary">Create quotation</button>
          </form>
        </Modal>
      )}
    </>
  )
}

export function PortalQuotations() {
  return (
    <>
      <PageHeader title="Quotations" />
      <ListView endpoint="/quotations/" columns={COLUMNS.filter((column) => column.key !== 'customer_name')} rowLink={(row) => `${row.id}`} emptyTitle="No quotations yet" />
    </>
  )
}

export function QuotationDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const team = user.role !== 'customer'
  const navigate = useNavigate()
  const { data, loading, error, notBuilt, reload } = useFetch(`/quotations/${id}/`)
  const { run, busy } = useAction(reload)
  if (notBuilt) return <NotBuilt />
  if (loading && !data) return <Skeleton />
  if (error) return <ErrorState message={error} onRetry={reload} />

  async function convert() {
    const subscription = await run(`/quotations/${id}/convert/`, 'Subscription created.')
    if (subscription) navigate(`/app/subscriptions/${subscription.id}`)
  }

  return (
    <>
      <PageHeader title={data.number} actions={
        <>
          <button className="btn btn-light" onClick={() => downloadPdf(`/quotations/${id}/pdf/`, `${data.number}.pdf`)}>Download PDF</button>
          {team && data.status === 'draft' && <button className="btn btn-primary" disabled={busy} onClick={() => run(`/quotations/${id}/send/`, 'Quotation sent.')}>Send</button>}
          {data.status === 'sent' && <button className="btn btn-light" disabled={busy} onClick={() => run(`/quotations/${id}/reject/`, 'Quotation rejected.')}>Reject</button>}
          {data.status === 'sent' && <button className="btn btn-primary" disabled={busy} onClick={() => run(`/quotations/${id}/accept/`, 'Quotation accepted.')}>Accept</button>}
          {team && data.status === 'accepted' && !data.subscription && <button className="btn btn-primary" disabled={busy} onClick={convert}>Create subscription</button>}
        </>
      } />
      <div className="card mb-4">
        <div className="mb-4"><StatusBadge status={data.status} /></div>
        <Facts items={[['Customer', data.customer_name], ['Plan', data.plan_name], ['Valid until', date(data.valid_until)], ['Payment terms', data.payment_term_name]]} />
      </div>
      <div className="card"><LinesTable lines={data.lines} /><Totals record={data} /></div>
    </>
  )
}
