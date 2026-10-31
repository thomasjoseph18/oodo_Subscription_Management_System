import { useState } from 'react'
import FormFields from '../components/FormFields'
import ListView from '../components/ListView'
import NotBuilt from '../components/NotBuilt'
import { ErrorState, PageHeader, Skeleton } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { useAction } from '../hooks/useAction'
import { useFetch } from '../hooks/useFetch'
import api, { errorMessage } from '../services/api'

export function Notifications() {
  const [refreshKey, setRefreshKey] = useState(0)
  const { run } = useAction(async () => setRefreshKey((key) => key + 1))
  return (
    <>
      <PageHeader title="Notifications" actions={<button className="btn btn-light" onClick={() => run('/notifications/read-all/', 'All marked as read.')}>Mark all as read</button>} />
      <ListView endpoint="/notifications/" refreshKey={refreshKey} emptyTitle="You're all caught up"
        rowActions={(row) => !row.read_at && <button className="btn btn-light btn-sm" onClick={() => run(`/notifications/${row.id}/read/`, 'Marked as read.')}>Mark read</button>}
        columns={[
          { key: 'created_at', label: 'When', type: 'date' },
          { key: 'title', label: 'Title', sortable: false },
          { key: 'body', label: 'Details', sortable: false },
        ]} />
    </>
  )
}

export function Settings() {
  const { data, loading, error, notBuilt, reload } = useFetch('/settings/')
  const { toast } = useToast()
  if (notBuilt) return <NotBuilt />
  if (loading && !data) return <Skeleton />
  if (error) return <ErrorState message={error} onRetry={reload} />

  async function change(name, value) {
    try {
      await api.patch('/settings/', { [name]: value })
      toast('Setting saved.')
      reload()
    } catch (failure) {
      toast(errorMessage(failure), 'error')
    }
  }

  return (
    <>
      <PageHeader title="Settings" />
      <div className="card max-w-xl">
        <FormFields fields={[{ name: 'auto_confirm_invoices', label: 'Confirm invoices automatically on billing day', type: 'checkbox' }]} values={data} onChange={change} />
      </div>
    </>
  )
}

export function Profile() {
  const { data, loading, error, notBuilt, reload } = useFetch('/customers/me/')
  const [form, setForm] = useState(null)
  const { toast } = useToast()
  if (notBuilt) return <NotBuilt />
  if (loading && !data) return <Skeleton />
  if (error) return <ErrorState message={error} onRetry={reload} />
  const values = form ?? data

  async function save(event) {
    event.preventDefault()
    try {
      await api.patch('/customers/me/', values)
      toast('Billing details saved.')
    } catch (failure) {
      toast(errorMessage(failure), 'error')
    }
  }

  return (
    <>
      <PageHeader title="Billing details" />
      <form className="card max-w-2xl" onSubmit={save}>
        <FormFields values={values} onChange={(name, value) => setForm({ ...values, [name]: value })} fields={[
          { name: 'name', label: 'Name', required: true },
          { name: 'company', label: 'Company' },
          { name: 'phone', label: 'Phone' },
          { name: 'gst_number', label: 'GST number' },
          { name: 'billing_address', label: 'Billing address', type: 'textarea' },
        ]} />
        <button className="btn btn-primary">Save</button>
      </form>
    </>
  )
}

export function Assistant() {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState([])
  const [busy, setBusy] = useState(false)

  async function ask(event) {
    event.preventDefault()
    setBusy(true)
    try {
      const { data } = await api.post('/assistant/query/', { question })
      setHistory([...history, { question, answer: data.answer }])
      setQuestion('')
    } catch (failure) {
      setHistory([...history, { question, answer: failure.response?.status === 404 ? 'The assistant is not available yet.' : errorMessage(failure) }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="Assistant" />
      <div className="card max-w-3xl">
        <p className="mb-4 text-sm text-muted">Answers come only from your Brightloop records. It can read reports but can't change anything.</p>
        <div className="mb-4 space-y-4" aria-live="polite">
          {history.map((item, index) => (
            <div key={index}>
              <p className="font-medium text-heading">{item.question}</p>
              <p className="whitespace-pre-line">{item.answer}</p>
            </div>
          ))}
        </div>
        <form className="flex gap-2" onSubmit={ask}>
          <input className="input" aria-label="Your question" placeholder="How much is still outstanding?" value={question} onChange={(event) => setQuestion(event.target.value)} required />
          <button className="btn btn-primary" disabled={busy}>Ask</button>
        </form>
      </div>
    </>
  )
}
