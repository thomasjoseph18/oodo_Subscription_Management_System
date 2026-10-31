import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import ResourcePage from './components/ResourcePage'
import { Skeleton } from './components/ui'
import { homeFor, useAuth } from './context/AuthContext'
import { ForgotPassword, Landing, Login, Register, ResetPassword } from './pages/public'
import { resources } from './routes/resources'

const AppLayout = lazy(() => import('./layouts/AppLayout'))
const Home = lazy(() => import('./pages/Home'))
const lazyNamed = (loader, name) => lazy(() => loader().then((module) => ({ default: module[name] })))
const dashboards = () => import('./pages/Dashboards')
const quotations = () => import('./pages/Quotations')
const subscriptions = () => import('./pages/Subscriptions')
const invoices = () => import('./pages/Invoices')
const misc = () => import('./pages/Misc')
const DashboardRouter = lazyNamed(dashboards, 'DashboardRouter')
const CustomerDashboard = lazyNamed(dashboards, 'CustomerDashboard')
const Reports = lazyNamed(dashboards, 'Reports')
const QuotationList = lazyNamed(quotations, 'QuotationList')
const QuotationDetail = lazyNamed(quotations, 'QuotationDetail')
const PortalQuotations = lazyNamed(quotations, 'PortalQuotations')
const SubscriptionList = lazyNamed(subscriptions, 'SubscriptionList')
const SubscriptionDetail = lazyNamed(subscriptions, 'SubscriptionDetail')
const InvoiceList = lazyNamed(invoices, 'InvoiceList')
const InvoiceDetail = lazyNamed(invoices, 'InvoiceDetail')
const PaymentList = lazyNamed(invoices, 'PaymentList')
const Notifications = lazyNamed(misc, 'Notifications')
const Settings = lazyNamed(misc, 'Settings')
const Assistant = lazyNamed(misc, 'Assistant')
const Profile = lazyNamed(misc, 'Profile')

export function RequireRole({ roles }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-8"><Skeleton /></div>
  if (!user) return <Navigate to="/login" replace />
  if (!roles.includes(user.role)) return <Navigate to={homeFor(user)} replace />
  return <Outlet />
}

const TEAM_LINKS = [
  { to: '/app', label: 'Apps', end: true },
  { to: '/app/customers', label: 'Customers' },
  { to: '/app/quotations', label: 'Quotations' },
  { to: '/app/subscriptions', label: 'Subscriptions' },
  { to: '/app/invoices', label: 'Invoices' },
  { to: '/app/payments', label: 'Payments' },
  { to: '/app/dashboard', label: 'Dashboard' },
]
const PORTAL_LINKS = [
  { to: '/portal', label: 'Overview', end: true },
  { to: '/portal/quotations', label: 'Quotations' },
  { to: '/portal/subscriptions', label: 'Subscriptions' },
  { to: '/portal/invoices', label: 'Invoices' },
  { to: '/portal/payments', label: 'Payments' },
  { to: '/portal/profile', label: 'Billing details' },
]
const ADMIN_PAGES = { products: 'products', variants: 'variants', plans: 'plans', 'payment-terms': 'paymentTerms', taxes: 'taxes', discounts: 'discounts', staff: 'staff', 'audit-logs': 'auditLogs' }

export default function App() {
  return (
    <Suspense fallback={<div className="p-8"><Skeleton /></div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />

        <Route element={<RequireRole roles={['admin', 'staff']} />}>
          <Route path="/app" element={<AppLayout home="/app" links={TEAM_LINKS} notificationsPath="/app/notifications" />}>
            <Route index element={<Home />} />
            <Route path="dashboard" element={<DashboardRouter />} />
            <Route path="customers" element={<ResourcePage config={resources.customers} />} />
            <Route path="quotation-templates" element={<ResourcePage config={{ ...resources.quotationTemplates, writeRoles: ['admin', 'staff'] }} />} />
            <Route path="quotations" element={<QuotationList />} />
            <Route path="quotations/:id" element={<QuotationDetail />} />
            <Route path="subscriptions" element={<SubscriptionList />} />
            <Route path="subscriptions/:id" element={<SubscriptionDetail />} />
            <Route path="invoices" element={<InvoiceList />} />
            <Route path="invoices/:id" element={<InvoiceDetail />} />
            <Route path="payments" element={<PaymentList />} />
            <Route path="notifications" element={<Notifications />} />
            <Route element={<RequireRole roles={['admin']} />}>
              {Object.entries(ADMIN_PAGES).map(([path, key]) => <Route key={path} path={path} element={<ResourcePage config={resources[key]} />} />)}
              <Route path="reports" element={<Reports />} />
              <Route path="assistant" element={<Assistant />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Route>
        </Route>

        <Route element={<RequireRole roles={['customer']} />}>
          <Route path="/portal" element={<AppLayout home="/portal" links={PORTAL_LINKS} notificationsPath="/portal/notifications" />}>
            <Route index element={<CustomerDashboard />} />
            <Route path="quotations" element={<PortalQuotations />} />
            <Route path="quotations/:id" element={<QuotationDetail />} />
            <Route path="subscriptions" element={<SubscriptionList portal />} />
            <Route path="subscriptions/:id" element={<SubscriptionDetail portal />} />
            <Route path="invoices" element={<InvoiceList portal />} />
            <Route path="invoices/:id" element={<InvoiceDetail />} />
            <Route path="payments" element={<PaymentList />} />
            <Route path="notifications" element={<Notifications />} />
            <Route path="profile" element={<Profile />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
