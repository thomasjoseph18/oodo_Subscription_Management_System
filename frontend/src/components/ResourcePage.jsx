import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import api, { errorMessage } from '../services/api'
import FormFields from './FormFields'
import ListView from './ListView'
import { ConfirmDialog, Modal, PageHeader } from './ui'

/** Config-driven list and create/edit screen. Backend permissions decide
 * what is allowed; `writeRoles` only hides buttons that would be refused. */
export default function ResourcePage({ config }) {
  const { title, singular, endpoint, columns, fields = [], filters, writeRoles = ['admin'], canDelete, defaults = {}, rowLink } = config
  const { user } = useAuth()
  const { toast } = useToast()
  const [editing, setEditing] = useState(null)
  const [removing, setRemoving] = useState(null)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const canWrite = writeRoles.includes(user?.role) && fields.length > 0

  async function save(event) {
    event.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      if (editing.id) await api.patch(`${endpoint}${editing.id}/`, editing)
      else await api.post(endpoint, editing)
      toast(`${singular} saved.`)
      setEditing(null)
      setRefreshKey((key) => key + 1)
    } catch (error) {
      setErrors(error.response?.data?.error?.details ?? {})
      toast(errorMessage(error), 'error')
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    try {
      await api.delete(`${endpoint}${removing.id}/`)
      toast(`${singular} deleted.`)
      setRefreshKey((key) => key + 1)
    } catch (error) {
      toast(errorMessage(error), 'error')
    }
    setRemoving(null)
  }

  const rowActions = canWrite
    ? (row) => (
        <span className="flex justify-end gap-1">
          <button className="btn btn-light btn-sm" onClick={() => setEditing(row)}>Edit</button>
          {canDelete && <button className="btn btn-light btn-sm" onClick={() => setRemoving(row)}>Delete</button>}
        </span>
      )
    : undefined

  return (
    <>
      <PageHeader title={title} actions={canWrite && <button className="btn btn-primary" onClick={() => setEditing({ ...defaults })}>New {singular.toLowerCase()}</button>} />
      <ListView endpoint={endpoint} columns={columns} filters={filters} rowLink={rowLink} rowActions={rowActions} refreshKey={refreshKey}
        emptyTitle={`No ${title.toLowerCase()} yet`} />
      {editing && (
        <Modal title={editing.id ? `Edit ${singular.toLowerCase()}` : `New ${singular.toLowerCase()}`} onClose={() => setEditing(null)}>
          <form onSubmit={save}>
            <FormFields fields={fields} values={editing} errors={errors} onChange={(name, value) => setEditing({ ...editing, [name]: value })} />
            <div className="mt-2 flex justify-end gap-2">
              <button type="button" className="btn btn-light" onClick={() => setEditing(null)}>Cancel</button>
              <button className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}
      {removing && (
        <ConfirmDialog danger title={`Delete ${singular.toLowerCase()}?`} message="Historic records that use it stay as they are." confirmLabel="Delete" onConfirm={remove} onClose={() => setRemoving(null)} />
      )}
    </>
  )
}
