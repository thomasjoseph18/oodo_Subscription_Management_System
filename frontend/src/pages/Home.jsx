import { Link } from 'react-router-dom'
import { Highlight } from '../components/ui'
import { useAuth } from '../context/AuthContext'

const TILES = [
  { to: 'dashboard', title: 'Dashboard', icon: 'fa-gauge-high', tone: '#714b67' },
  { to: 'customers', title: 'Customers', icon: 'fa-users', tone: '#017e84' },
  { to: 'products', title: 'Products', icon: 'fa-box', tone: '#fbb130', admin: true },
  { to: 'variants', title: 'Variants', icon: 'fa-tags', tone: '#fc787d', admin: true },
  { to: 'plans', title: 'Plans', icon: 'fa-repeat', tone: '#1bb6f9', admin: true },
  { to: 'quotation-templates', title: 'Templates', icon: 'fa-file-lines', tone: '#00ceb3' },
  { to: 'quotations', title: 'Quotations', icon: 'fa-file-signature', tone: '#62dd8b' },
  { to: 'subscriptions', title: 'Subscriptions', icon: 'fa-rotate', tone: '#714b67' },
  { to: 'invoices', title: 'Invoices', icon: 'fa-file-invoice', tone: '#017e84' },
  { to: 'payments', title: 'Payments', icon: 'fa-money-bill-wave', tone: '#62dd8b' },
  { to: 'taxes', title: 'Taxes', icon: 'fa-landmark', tone: '#fbb130', admin: true },
  { to: 'discounts', title: 'Discounts', icon: 'fa-percent', tone: '#fc787d', admin: true },
  { to: 'reports', title: 'Reports', icon: 'fa-chart-line', tone: '#1bb6f9', admin: true },
  { to: 'assistant', title: 'Assistant', icon: 'fa-wand-magic-sparkles', tone: '#714b67', admin: true },
  { to: 'staff', title: 'Staff', icon: 'fa-user-tie', tone: '#00ceb3', admin: true },
  { to: 'audit-logs', title: 'Audit log', icon: 'fa-clipboard-list', tone: '#6c757d', admin: true },
  { to: 'settings', title: 'Settings', icon: 'fa-gear', tone: '#6c757d', admin: true },
]

export default function Home() {
  const { user } = useAuth()
  const tiles = TILES.filter((tile) => !tile.admin || user.role === 'admin')
  return (
    <div className="mx-auto max-w-4xl py-8">
      <h1 className="display display-3 mb-10 text-center">All your billing on <Highlight>one page.</Highlight></h1>
      <div className="grid grid-cols-3 gap-6 sm:grid-cols-4 lg:grid-cols-6">
        {tiles.map((tile) => (
          <Link key={tile.to} to={tile.to} className="app-tile">
            <span className="flex h-20 w-20 items-center justify-center rounded-md border border-line bg-white"><i className={`fa-solid ${tile.icon} text-3xl`} style={{ color: tile.tone }} aria-hidden="true" /></span>
            <span className="max-w-full truncate text-sm text-heading">{tile.title}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
