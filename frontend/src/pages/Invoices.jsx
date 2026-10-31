import { useState } from 'react'
import { useParams } from 'react-router-dom'
import FormFields from '../components/FormFields'
import ListView from '../components/ListView'
import NotBuilt from '../components/NotBuilt'
import { Facts, LinesTable, Totals } from '../components/Totals'
import { ConfirmDialog, ErrorState, Modal, PageHeader, Skeleton, StatusBadge } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useAction } from '../hooks/useAction'
import { useFetch } from '../hooks/useFetch'
import api, { downloadPdf, errorMessage } from '../services/api'
import { date, money } from '../utils/format'

const COLUMNS = [
  { key: 'number', label: 'Number' },
  { key: 'customer_name', label: 'Customer', sortable: false },
  { key: 'invoice_date', label: 'Date', type: 'date' },
  { key: 'due_date', label: 'Due', type: 'date' },
  { key: 'total', label: 'Total', type: 'money' },
  { key: 'outstanding', label: 'Outstanding', type: 'money', sortable: false },
  { key: 'status', label: 'Status', type: 'status' },
  { key: 'payment_state', label: 'Payment', type: 'status', sortable: false },
]
const FILTERS = [
  { name: 'status', label: 'Status', options: ['draft', 'confirmed', 'paid', 'cancelled'] },
  { name: 'payment_state', label: 'Payment', options: ['unpaid', 'partial', 'paid', 'overdue'] },
]
const METHODS = ['cash', 'bank_transfer', 'upi', 'debit_card', 'credit_card']

export function InvoiceList({ portal }) {
  const { toast } = useToast()
  const [refreshKey, setRefreshKey] = useState(0)
  const [running, setRunning] = useState(false)

  async function runBilling() {
    setRunning(true)
    try {
      const { data } = await api.post('/billing-runs/')
      toast(`Billing run finished: ${data.invoices_created} ${data.invoices_created === 1 ? 'invoice' : 'invoices'} created.`)
      setRefreshKey((key) => key + 1)
    } catch (error) {
      toast(errorMessage(error), 'error')
    } finally {
      setRunning(false)
    }
  }

  return (
    <>
      <PageHeader title="Invoices" actions={!portal && <button className="btn btn-primary" disabled={running} onClick={runBilling}>{running ? 'Running…' : 'Run billing now'}</button>} />
      <ListView endpoint="/invoices/" columns={portal ? COLUMNS.filter((column) => column.key !== 'customer_name') : COLUMNS} filters={FILTERS} rowLink={(row) => `${row.id}`} refreshKey={refreshKey} emptyTitle="No invoices yet" />
    </>
  )
}

function RecordPayment({ invoice, onClose, onDone }) {
  const today = new Date().toISOString().slice(0, 10)
  const [form, setForm] = useState({ method: 'bank_transfer', amount: invoice.outstanding, paid_on: today, notes: '' })
  const { run, busy } = useAction(onDone)
  const fields = [
    { name: 'method', label: 'Method', type: 'select', options: METHODS, required: true },
    { name: 'amount', label: 'Amount', type: 'number', required: true },
    { name: 'paid_on', label: 'Date', type: 'date', required: true },
    { name: 'notes', label: 'Note', type: 'textarea' },
  ]
  return (
    <Modal title="Record a payment" onClose={onClose}>
      <form onSubmit={async (event) => {
        event.preventDefault()
        if (await run('/payments/', 'Payment recorded.', { ...form, invoice: invoice.id })) onClose()
      }}>
        <FormFields fields={fields} values={form} onChange={(name, value) => setForm({ ...form, [name]: value })} />
        <button className="btn btn-primary" disabled={busy}>Record payment</button>
      </form>
    </Modal>
  )
}

function loadCheckout() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) return resolve()
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = resolve
    script.onerror = () => reject(new Error('Could not load Razorpay.'))
    document.body.append(script)
  })
}

export function InvoiceDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const { toast } = useToast()
  const { data, loading, error, notBuilt, reload } = useFetch(`/invoices/${id}/`)
  const { run, busy } = useAction(reload)
  const [paying, setPaying] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  if (notBuilt) return <NotBuilt />
  if (loading && !data) return <Skeleton />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const team = user.role !== 'customer'
  const payable = data.status === 'confirmed' && Number(data.outstanding) > 0

  async function payOnline() {
    try {
      await loadCheckout()
      const { data: order } = await api.post('/payments/razorpay/order/', { invoice: data.id })
      new window.Razorpay({
        key: order.key, order_id: order.order_id, amount: order.amount, currency: 'INR', name: 'Brightloop', description: data.number,
        theme: { color: '#714b67' },
        handler: async (response) => {
          try {
            await api.post('/payments/razorpay/verify/', response)
            toast('Payment received.')
            reload()
          } catch (failure) {
            toast(errorMessage(failure), 'error')
          }
        },
      }).open()
    } catch (failure) {
      toast(failure.response ? errorMessage(failure) : failure.message, 'error')
    }
  }

  return (
    <>
      <PageHeader title={data.number} actions={
        <>
          <button className="btn btn-light" onClick={() => downloadPdf(`/invoices/${id}/pdf/`, `${data.number}.pdf`)}>Print or download</button>
          {team && data.status === 'draft' && <button className="btn btn-primary" disabled={busy} onClick={() => run(`/invoices/${id}/confirm/`, 'Invoice confirmed.')}>Confirm</button>}
          {team && data.status === 'confirmed' && <button className="btn btn-light" disabled={busy} onClick={() => run(`/invoices/${id}/send/`, 'Invoice sent.')}>Send</button>}
          {team && ['draft', 'confirmed'].includes(data.status) && <button className="btn btn-light" onClick={() => setCancelling(true)}>Cancel</button>}
          {team && data.status === 'cancelled' && <button className="btn btn-primary" disabled={busy} onClick={() => run(`/invoices/${id}/reissue/`, 'New invoice created for this period.')}>Reissue</button>}
          {team && payable && <button className="btn btn-primary" onClick={() => setPaying(true)}>Record payment</button>}
          {!team && payable && <button className="btn btn-primary" onClick={payOnline}>Pay online</button>}
        </>
      } />
      <div className="card mb-4">
        <div className="mb-4 flex gap-2"><StatusBadge status={data.status} /><StatusBadge status={data.payment_state} /></div>
        <Facts items={[
          ['Customer', data.customer_name], ['Subscription', data.subscription_number], ['Invoice date', date(data.invoice_date)], ['Due date', date(data.due_date)],
          ['Billing period', `${date(data.period_start)} to ${date(data.period_end)}`], ['Paid', money(data.amount_paid)], ['Outstanding', money(data.outstanding)],
        ]} />
      </div>
      <div className="card mb-4"><LinesTable lines={data.lines} /><Totals record={data} /></div>
      <div className="card">
        <h5 className="mb-3">Payments</h5>
        {data.payments?.length ? (
          <ul className="space-y-1 text-sm">{data.payments.map((payment) => <li key={payment.id}>{date(payment.paid_on)}: {money(payment.amount)} by {payment.method.replaceAll('_', ' ')} ({payment.reference})</li>)}</ul>
        ) : <p className="text-sm text-muted">No payments yet.</p>}
      </div>
      {paying && <RecordPayment invoice={data} onClose={() => setPaying(false)} onDone={reload} />}
      {cancelling && (
        <ConfirmDialog danger title="Cancel this invoice?" message="Its billing period can be billed again." confirmLabel="Cancel invoice"
          onConfirm={() => { setCancelling(false); run(`/invoices/${id}/cancel/`, 'Invoice cancelled.') }} onClose={() => setCancelling(false)} />
      )}
    </>
  )
}

export function PaymentList() {
  return (
    <>
      <PageHeader title="Payments" />
      <ListView endpoint="/payments/" emptyTitle="No payments yet" filters={[{ name: 'method', label: 'Method', options: [...METHODS, 'online_gateway'] }, { name: 'status', label: 'Status', options: ['completed', 'pending', 'failed'] }]}
        columns={[
          { key: 'reference', label: 'Reference' },
          { key: 'customer_name', label: 'Customer', sortable: false },
          { key: 'invoice_numbers', label: 'Invoices', sortable: false },
          { key: 'method', label: 'Method' },
          { key: 'amount', label: 'Amount', type: 'money' },
          { key: 'paid_on', label: 'Date', type: 'date' },
          { key: 'status', label: 'Status', type: 'status' },
        ]} />
    </>
  )
}
