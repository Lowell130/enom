export const useApi = () => {
  const config = useRuntimeConfig()

  const fetchWithAuth = async (endpoint: string, options: any = {}) => {
    const tokenCookie = useCookie('auth_token')
    const token = options.token || tokenCookie.value

    const headers: Record<string, string> = {
      ...(options.headers || {})
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const url = `${config.public.apiBase}${endpoint}`
    
    try {
      return await $fetch(url, {
        ...options,
        headers,
      })
    } catch (err: any) {
      console.error(`API Error on ${endpoint}:`, err)
      throw err
    }
  }

  return {
    fetchWithAuth,
    apiBase: config.public.apiBase,
    mediaBase: config.public.mediaBase
  }
}
