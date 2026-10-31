import axios from 'axios'

let accessToken = null

export function setAccessToken(token) {
  accessToken = token
}

const api = axios.create({ baseURL: '/api', withCredentials: true })

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

let refreshing = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const isAuthCall = original?.url?.startsWith('/auth/')
    if (error.response?.status !== 401 || original?._retried || isAuthCall) throw error
    original._retried = true
    refreshing ??= api.post('/auth/refresh/').finally(() => {
      refreshing = null
    })
    const { data } = await refreshing
    setAccessToken(data.access)
    return api(original)
  },
)

export function errorMessage(error) {
  const payload = error.response?.data?.error
  if (!payload) return 'Something went wrong. Please try again.'
  const fields = Object.entries(payload.details ?? {}).filter(([key]) => key !== 'detail')
  if (fields.length) {
    return fields.map(([key, value]) => `${key.replaceAll('_', ' ')}: ${[value].flat().join(' ')}`).join(' · ')
  }
  return payload.message
}

export async function downloadPdf(path, filename) {
  const { data } = await api.get(path, { responseType: 'blob' })
  const url = URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export default api
