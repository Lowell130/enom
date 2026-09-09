// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2026-09-09',
  devtools: { enabled: false },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1',
      mediaBase: process.env.NUXT_PUBLIC_MEDIA_BASE || 'http://localhost:8000'
    }
  },
  app: {
    head: {
      title: 'EnotecaMolise - I Grandi Vini del Molise',
      meta: [
        { name: 'description', content: 'Il portale ufficiale dei produttori enologici del Molise. Scopri cantine, vini rossi, bianchi, Tintilia del Molise DOC e acquista o contatta i produttori.' }
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap' }
      ]
    }
  }
})
