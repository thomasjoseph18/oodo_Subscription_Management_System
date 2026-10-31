const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })
const dateFormat = new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })

export const money = (value) => (value === null || value === undefined ? '—' : inr.format(Number(value)))
export const date = (value) => (value ? dateFormat.format(new Date(value)) : '—')
export const label = (value) => (value ? String(value).replaceAll('_', ' ').replace(/^\w/, (c) => c.toUpperCase()) : '—')

/** Password rule from the brief: more than eight characters, upper, lower and special. */
export function passwordProblems(password) {
  const problems = []
  if (password.length <= 8) problems.push('more than 8 characters')
  if (!/[A-Z]/.test(password)) problems.push('an uppercase letter')
  if (!/[a-z]/.test(password)) problems.push('a lowercase letter')
  if (!/[^A-Za-z0-9]/.test(password)) problems.push('a special character')
  return problems
}
