export const useAuth = () => {
  const { fetchWithAuth } = useApi()
  const tokenCookie = useCookie<string | null>('auth_token', { maxAge: 60 * 60 * 24 * 7 })
  const user = useState<any>('auth_user', () => null)
  const loading = useState<boolean>('auth_loading', () => false)

  const fetchUser = async (customToken?: string) => {
    const activeToken = customToken || tokenCookie.value
    if (!activeToken) {
      user.value = null
      return null
    }
    try {
      loading.value = true
      const userData = await fetchWithAuth('/auth/me', { token: activeToken })
      user.value = userData
      return userData
    } catch (e) {
      tokenCookie.value = null
      user.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  const login = async (credentials: { email: string; password: string }) => {
    const res: any = await fetchWithAuth('/auth/login', {
      method: 'POST',
      body: credentials
    })
    tokenCookie.value = res.access_token
    user.value = res.user
    await fetchUser(res.access_token)
    return res
  }

  const logout = () => {
    tokenCookie.value = null
    user.value = null
    navigateTo('/login')
  }

  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isProducer = computed(() => user.value?.role === 'PRODUCER')
  const isAuthenticated = computed(() => !!user.value)

  return {
    tokenCookie,
    user,
    loading,
    fetchUser,
    login,
    logout,
    isAdmin,
    isProducer,
    isAuthenticated
  }
}
