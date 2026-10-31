import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useFetch } from '../hooks/useFetch'
import { Logo } from '../components/ui'

function Bell({ to }) {
  const { data } = useFetch('/notifications/')
  const unread = data?.results?.filter((note) => !note.read_at).length ?? 0
  return (
    <Link to={to} aria-label="Notifications" className="relative text-body">
      <i className="fa-regular fa-bell text-lg" aria-hidden="true" />
      {unread > 0 && <span className="absolute -top-1 -right-1 h-2.5 w-2.5 rounded-full bg-danger" />}
    </Link>
  )
}

export default function AppLayout({ home, links, notificationsPath }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  async function signOut() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <header className="sticky top-0 z-30 border-b border-line bg-white" style={{ transition: 'box-shadow 0.2s ease' }}>
        <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-6 px-4">
          <Link to={home} className="no-underline" aria-label="Home"><Logo /></Link>
          <nav className="hidden flex-1 items-center gap-4 text-sm lg:flex">
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} end={link.end}
                className={({ isActive }) => `font-medium no-underline ${isActive ? 'text-primary' : 'text-body'}`}>{link.label}</NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-4 text-sm">
            <Bell to={notificationsPath} />
            <span className="hidden text-muted md:inline">{user?.email}</span>
            <button className="btn btn-light btn-sm" onClick={signOut}>Sign out</button>
            <button className="cursor-pointer lg:hidden" aria-label="Menu" aria-expanded={open} onClick={() => setOpen(!open)}><i className="fa-solid fa-bars text-lg" /></button>
          </div>
        </div>
        {open && (
          <nav className="flex flex-col gap-2 border-t border-line p-4 text-sm lg:hidden">
            {links.map((link) => <NavLink key={link.to} to={link.to} end={link.end} className="no-underline" onClick={() => setOpen(false)}>{link.label}</NavLink>)}
          </nav>
        )}
      </header>
      <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-8"><Outlet /></main>
    </div>
  )
}
