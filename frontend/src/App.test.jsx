import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { passwordProblems } from './utils/format'

const auth = vi.hoisted(() => ({ value: { user: null, loading: false } }))
vi.mock('./context/AuthContext', () => ({
  useAuth: () => auth.value,
  homeFor: (user) => (user?.role === 'customer' ? '/portal' : '/app'),
}))

const { RequireRole } = await import('./App')

function guarded(user) {
  auth.value = { user, loading: false }
  render(
    <MemoryRouter initialEntries={['/secret']}>
      <Routes>
        <Route element={<RequireRole roles={['admin']} />}>
          <Route path="/secret" element={<p>secret page</p>} />
        </Route>
        <Route path="/login" element={<p>login page</p>} />
        <Route path="/portal" element={<p>portal page</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('password rule', () => {
  it('rejects exactly eight characters', () => {
    expect(passwordProblems('Abcdef1!')).toContain('more than 8 characters')
  })
  it('accepts a valid password', () => {
    expect(passwordProblems('Abcdefg1!')).toEqual([])
  })
  it('needs a special character', () => {
    expect(passwordProblems('Abcdefghi')).toContain('a special character')
  })
})

describe('protected routes', () => {
  it('sends signed-out visitors to login', () => {
    guarded(null)
    expect(screen.getByText('login page')).toBeInTheDocument()
  })
  it('sends a customer away from an admin page', () => {
    guarded({ role: 'customer' })
    expect(screen.getByText('portal page')).toBeInTheDocument()
  })
  it('lets the admin in', () => {
    guarded({ role: 'admin' })
    expect(screen.getByText('secret page')).toBeInTheDocument()
  })
})
