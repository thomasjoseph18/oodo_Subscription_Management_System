import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import FormFields from '../components/FormFields'
import LineEditor from '../components/LineEditor'
import ListView from '../components/ListView'
import NotBuilt from '../components/NotBuilt'
import { Facts, LinesTable, Timeline, Totals } from '../components/Totals'
import { ConfirmDialog, ErrorState, Modal, PageHeader, Skeleton, StatusBadge } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useAction } from '../hooks/useAction'
import { useFetch } from '../hooks/useFetch'
import { fieldRefs } from '../routes/resources'
import api, { errorMessage } from '../services/api'
import { date, label, money } from '../utils/format'

const COLUMNS = [
  { key: 'number', label: 'Number' },
  { key: 'customer_name', label: 'Customer', sortable: false },
  { key: 'plan_name', label: 'Plan', sortable: false },
  { key: 'next_billing_date', label: 'Next billing', type: 'date' },
  { key: 'expiry_date', label: 'Expires', type: 'date' },
  { key: 'status', label: 'Status', type: 'status' },
]
const STATUSES = ['draft', 'quotation', 'confirmed', 'active', 'paused', 'renewed', 'closed']
const FIELDS = [
  { name: 'customer', label: 'Customer', required: true, ...fieldRefs.customer },
  { name: 'plan', label: 'Plan', required: true, ...fieldRefs.plan },
  { name: 'start_date', label: 'Start date', type: 'date', required: true },
  { name: 'expiry_date', label: 'Expiry date', type: 'date' },
  { name: 'payment_term', label: 'Payment terms', ...fieldRefs.term },
]

export function SubscriptionList({ portal }) {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [form, setForm] = useState(null)

  async function create(event) {
    event.preventDefault()
    try {
      const { data } = await api.post('/subscriptions/', form)
      navigate(`${data.id}`)
    } catch (error) {
      toast(errorMessage(error), 'error')
    }
  }

  return (
    <>
      <PageHeader title="Subscriptions" actions={!portal && <button className="btn btn-primary" onClick={() => setForm({ lines: [] })}>New subscription</button>} />
      <ListView endpoint="/subscriptions/" columns={portal ? COLUMNS.filter((column) => column.key !== 'customer_name') : COLUMNS}
        rowLink={(row) => `${row.id}`} filters={[{ name: 'status', label: 'Status', options: STATUSES }]} emptyTitle="No subscriptions yet" />
      {form && (
        <Modal title="New subscription" onClose={() => setForm(null)}>
          <form onSubmit={create}>
            <FormFields fields={FIELDS} values={form} onChange={(name, value) => setForm({ ...form, [name]: value })} />
            <LineEditor lines={form.lines} onChange={(lines) => setForm({ ...form, lines })} />
            <button className="btn btn-primary">Create subscription</button>
          </form>
        </Modal>
      )}
    </>
  )
}

function ChangePlan({ subscription, onClose, onDone }) {
  const [plan, setPlan] = useState(null)
  const { run, busy } = useAction(onDone)
  return (
    <Modal title="Request a plan change" onClose={onClose}>
      <p className="mb-4 text-sm">The change starts at the next billing date once our team approves it.</p>
      <FormFields fields={[{ name: 'plan', label: 'New plan', ...fieldRefs.plan, params: { status: 'active' } }]} values={{ plan }} onChange={(_, value) => setPlan(value)} />
      <button className="btn btn-primary" disabled={!plan || busy}
        onClick={async () => { if (await run(`/subscriptions/${subscription.id}/plan-change/`, 'Request sent.', { plan })) onClose() }}>Send request</button>
    </Modal>
  )
}

function PlanRequests({ subscriptionId, onDecided }) {
  const { data, reload } = useFetch('/plan-changes/', { subscription: subscriptionId, status: 'pending' })
  const { run, busy } = useAction(async () => { await reload(); await onDecided() })
  const requests = data?.results ?? []
  if (!requests.length) return null
  return (
    <div className="card mb-4">
      <h5 className="mb-3">Plan change requests</h5>
      {requests.map((request) => (
        <div key={request.id} className="flex flex-wrap items-center justify-between gap-2">
          <span>Customer asked for {request.plan_name}</span>
          <span className="flex gap-2">
            <button className="btn btn-light btn-sm" disabled={busy} onClick={() => run(`/plan-changes/${request.id}/reject/`, 'Request rejected.')}>Reject</button>
            <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => run(`/plan-changes/${request.id}/approve/`, 'Plan changed.')}>Approve</button>
          </span>
        </div>
      ))}
    </div>
  )
}

export function SubscriptionDetail({ portal }) {
  const { id } = useParams()
  const { user } = useAuth()
  const { data, loading, error, notBuilt, reload } = useFetch(`/subscriptions/${id}/`)
  const events = useFetch(`/subscriptions/${id}/events/`)
  const refresh = async () => { await reload(); await events.reload() }
  const { run, busy } = useAction(refresh)
  const [closing, setClosing] = useState(false)
  const [changing, setChanging] = useState(false)
  if (notBuilt) return <NotBuilt />
  if (loading && !data) return <Skeleton />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const url = (name) => `/subscriptions/${id}/${name}/`
  const team = user.role !== 'customer'
  const allowed = data.allowed_actions ?? []
  const button = (name, text, primary) => allowed.includes(name) && (
    <button key={name} className={`btn ${primary ? 'btn-primary' : 'btn-light'}`} disabled={busy} onClick={() => run(url(name), `${text} done.`)}>{text}</button>
  )

  return (
    <>
      <PageHeader title={data.number} actions={
        <>
          {team && button('quote', 'Mark as quotation')}
          {team && button('confirm', 'Confirm', true)}
          {team && button('activate', 'Activate', true)}
          {button('pause', 'Pause')}
          {button('resume', 'Resume', true)}
          {button('renew', 'Renew', true)}
          {portal && data.status === 'active' && <button className="btn btn-light" onClick={() => setChanging(true)}>Change plan</button>}
          {allowed.includes('close') && <button className="btn btn-light" onClick={() => setClosing(true)}>Close</button>}
        </>
      } />
      <div className="card mb-4">
        <div className="mb-4"><StatusBadge status={data.status} /></div>
        <Facts items={[
          ['Customer', data.customer_name], ['Plan', data.plan_name], ['Billing', label(data.interval)], ['Payment terms', data.payment_term_name],
          ['Start', date(data.start_date)], ['Expires', date(data.expiry_date)], ['Next billing', date(data.next_billing_date)], ['Per period', money(data.total)],
        ]} />
      </div>
      {team && <PlanRequests subscriptionId={id} onDecided={refresh} />}
      <div className="card mb-4"><h5 className="mb-3">Lines</h5><LinesTable lines={data.lines} /><Totals record={data} /></div>
      <div className="card"><h5 className="mb-3">History</h5><Timeline events={events.data?.results ?? events.data ?? []} /></div>
      {closing && (
        <ConfirmDialog danger title="Close this subscription?" message="Billing stops. This can't be undone." confirmLabel="Close subscription"
          onConfirm={() => { setClosing(false); run(url('close'), 'Subscription closed.') }} onClose={() => setClosing(false)} />
      )}
      {changing && <ChangePlan subscription={data} onClose={() => setChanging(false)} onDone={refresh} />}
    </>
  )
}
