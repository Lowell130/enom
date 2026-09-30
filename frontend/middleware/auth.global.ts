// Protegge le pagine riservate: /dashboard richiede l'accesso,
// alcune sezioni sono riservate all'amministratore.
const ADMIN_ONLY = ['/dashboard/cantine', '/dashboard/attributi', '/dashboard/vitigni', '/dashboard/abbinamenti']

export default defineNuxtRouteMiddleware(async (to) => {
  if (!to.path.startsWith('/dashboard')) return

  const { tokenCookie, user, fetchUser } = useAuth()

  if (!tokenCookie.value) {
    return navigateTo({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (!user.value) {
    await fetchUser()
  }

  if (!user.value) {
    return navigateTo({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (ADMIN_ONLY.some((p) => to.path.startsWith(p)) && user.value.role !== 'ADMIN') {
    return navigateTo('/dashboard')
  }
})
