import { useCallback, useState } from 'react'
import { useToast } from '../context/ToastContext'
import api, { errorMessage } from '../services/api'

/** Posts to an action endpoint, shows a toast and reloads the record. */
export function useAction(reload) {
  const { toast } = useToast()
  const [busy, setBusy] = useState(false)

  const run = useCallback(
    async (path, success, body) => {
      setBusy(true)
      try {
        const { data } = await api.post(path, body)
        toast(success)
        await reload?.()
        return data
      } catch (error) {
        toast(errorMessage(error), 'error')
        return null
      } finally {
        setBusy(false)
      }
    },
    [reload, toast],
  )

  return { run, busy }
}
