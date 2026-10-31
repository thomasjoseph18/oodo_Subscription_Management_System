import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import DataTable from '../components/DataTable'
import NotBuilt from '../components/NotBuilt'
import { Empty, ErrorState, Highlight, PageHeader, Skeleton, Stat } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useFetch } from '../hooks/useFetch'
import { date, money } from '../utils/format'

function Chart({ title, data, dataKey, kind = 'line', format = money }) {
  const Shape = kind === 'bar' ? BarChart : LineChart
  return (
    <div className="card">
      <h5 className="mb-4">{title}</h5>
      {data.length === 0 ? <p className="py-8 text-center text-sm text-muted">No data in this period.</p> : (
        <ResponsiveContainer width="100%" height={260}>
          <Shape data={data}>
            <CartesianGrid stroke="#e6e9ed" vertical={false} />
            <XAxis dataKey="month" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} width={70} />
            <Tooltip formatter={(value) => format(value)} />
            {kind === 'bar' ? <Bar dataKey={dataKey} fill="#017e84" radius={[4, 4, 0, 0]} /> : <Line dataKey={dataKey} stroke="#714b67" strokeWidth={2} dot={false} />}
          </Shape>
        </ResponsiveContainer>
      )}
    </div>
  )
}

const OVERDUE_COLUMNS = [
  { key: 'number', label: 'Invoice', sortable: false },
  { key: 'customer_name', label: 'Customer', sortable: false },
  { key: 'due_date', label: 'Due', type: 'date', sortable: false },
  { key: 'outstanding', label: 'Outstanding', type: 'money', sortable: false },
]

function useDashboard(params) {
  return useFetch('/dashboard/', params)
}

function Guard({ state, children }) {
  if (state.notBuilt) return <NotBuilt />
  if (state.loading && !state.data) return <Skeleton rows={8} />
  if (state.error) return <ErrorState message={state.error} onRetry={state.reload} />
  return children(state.data)
}

export function AdminDashboard() {
  const [range, setRange] = useState({ from: '', to: '' })
  const state = useDashboard({ from: range.from || undefined, to: range.to || undefined })
  return (
    <>
      <PageHeader title="Dashboard" actions={
        <>
          <input type="date" aria-label="From" className="input w-40" value={range.from} onChange={(event) => setRange({ ...range, from: event.target.value })} />
          <input type="date" aria-label="To" className="input w-40" value={range.to} onChange={(event) => setRange({ ...range, to: event.target.value })} />
        </>
      } />
      <Guard state={state}>{(data) => (
        <>
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Stat title="Customers" value={data.customers} />
            <Stat title="Active subscriptions" value={data.active_subscriptions} />
            <Stat title="All subscriptions" value={data.total_subscriptions} />
            <Stat title="MRR" value={money(data.mrr)} />
            <Stat title="ARR" value={money(data.arr)} />
            <Stat title="Revenue collected" value={money(data.revenue)} />
            <Stat title="Still owed" value={money(data.outstanding)} />
            <Stat title="Overdue invoices" value={data.overdue_count} tone="danger" />
          </div>
          <div className="mb-6 grid gap-4 lg:grid-cols-2">
            <Chart title="Revenue by month" data={data.revenue_trend} dataKey="amount" kind="bar" />
            <Chart title="New subscriptions by month" data={data.subscription_growth} dataKey="count" format={(value) => value} />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="card">
              <h5 className="mb-3">Overdue invoices</h5>
              {data.overdue.length ? <DataTable columns={OVERDUE_COLUMNS} rows={data.overdue} rowLink={(row) => `/app/invoices/${row.id}`} /> : <Empty title="Nothing overdue" />}
            </div>
            <div className="card">
              <h5 className="mb-3">Upcoming renewals</h5>
              {data.upcoming_renewals.length ? (
                <ul className="space-y-2 text-sm">{data.upcoming_renewals.map((row) => <li key={row.id}><Link to={`/app/subscriptions/${row.id}`}>{row.number}</Link> · {row.customer_name} · {date(row.expiry_date)}</li>)}</ul>
              ) : <Empty title="No renewals soon" />}
              <h5 className="mt-6 mb-3">Recent payments</h5>
              <ul className="space-y-2 text-sm">{data.recent_payments.map((row) => <li key={row.id}>{date(row.paid_on)} · {row.customer_name} · {money(row.amount)}</li>)}</ul>
            </div>
          </div>
        </>
      )}</Guard>
    </>
  )
}

export function StaffDashboard() {
  return (
    <>
      <PageHeader title="Dashboard" />
      <Guard state={useDashboard()}>{(data) => (
        <>
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-5">
            <Stat title="Assigned customers" value={data.assigned_customers} />
            <Stat title="Active subscriptions" value={data.active_subscriptions} />
            <Stat title="Pending quotations" value={data.pending_quotations} />
            <Stat title="Pending invoices" value={data.pending_invoices} />
            <Stat title="Overdue" value={data.overdue_count} tone="danger" />
          </div>
          <div className="card">
            <h5 className="mb-3">Overdue invoices</h5>
            {data.overdue.length ? <DataTable columns={OVERDUE_COLUMNS} rows={data.overdue} rowLink={(row) => `/app/invoices/${row.id}`} /> : <Empty title="Nothing overdue" />}
          </div>
        </>
      )}</Guard>
    </>
  )
}

export function DashboardRouter() {
  const { user } = useAuth()
  return user.role === 'admin' ? <AdminDashboard /> : <StaffDashboard />
}

export function CustomerDashboard() {
  const { user } = useAuth()
  return (
    <Guard state={useDashboard()}>{(data) => (
      <>
        <h1 className="display display-3 mb-6">Hello, <Highlight>{user.first_name || 'there'}.</Highlight></h1>
        <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat title="Current plan" value={data.current?.plan_name ?? 'None'} />
          <Stat title="Status" value={data.current?.status ?? '—'} />
          <Stat title="Next billing" value={date(data.current?.next_billing_date)} />
          <Stat title="Outstanding" value={money(data.outstanding)} tone={Number(data.outstanding) > 0 ? 'danger' : undefined} />
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card">
            <h5 className="mb-3">Recent invoices</h5>
            <ul className="space-y-2 text-sm">{data.recent_invoices.map((row) => <li key={row.id}><Link to={`/portal/invoices/${row.id}`}>{row.number}</Link> · {money(row.total)} · {row.payment_state}</li>)}</ul>
          </div>
          <div className="card">
            <h5 className="mb-3">Recent payments</h5>
            <ul className="space-y-2 text-sm">{data.recent_payments.map((row) => <li key={row.id}>{date(row.paid_on)} · {money(row.amount)}</li>)}</ul>
          </div>
        </div>
      </>
    )}</Guard>
  )
}

export function Reports() {
  const state = useFetch('/analytics/')
  return (
    <>
      <PageHeader title="Reports" />
      <Guard state={state}>{(data) => (
        <>
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Stat title="MRR" value={money(data.mrr)} />
            <Stat title="ARR" value={money(data.arr)} />
            <Stat title="Churn rate" value={`${data.churn_rate}%`} />
            <Stat title="Renewal rate" value={`${data.renewal_rate}%`} />
            <Stat title="Average revenue per customer" value={money(data.arpc)} />
            <Stat title="Collection rate" value={`${data.collection_rate}%`} />
            <Stat title="Customer lifetime value" value={money(data.ltv)} />
            <Stat title="Growth this month" value={data.growth} />
          </div>
          <Chart title="Revenue by month" data={data.revenue_trend} dataKey="amount" kind="bar" />
        </>
      )}</Guard>
    </>
  )
}
