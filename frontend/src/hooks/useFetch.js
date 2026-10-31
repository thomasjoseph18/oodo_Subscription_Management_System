import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../services/api'

/** Loads a GET endpoint. `notBuilt` is true on 404 so a screen can say that
 * its backend has not landed yet instead of showing an error. */
export function useFetch(path, params) {
  const [state, setState] = useState({ data: null, loading: true, error: null, notBuilt: false })
  const key = JSON.stringify(params ?? {})

  const reload = useCallback(() => {
    if (!path) return Promise.resolve()
    setState((current) => ({ ...current, loading: true, error: null }))
    return api
      .get(path, { params: JSON.parse(key) })
      .then(({ data }) => setState({ data, loading: false, error: null, notBuilt: false }))
      .catch((error) =>
        setState({
          data: null,
          loading: false,
          notBuilt: error.response?.status === 404,
          error: errorMessage(error),
        }),
      )
  }, [path, key])

  useEffect(() => {
    reload()
  }, [reload])

  return { ...state, reload }
}
