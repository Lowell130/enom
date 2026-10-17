// ID di Google Analytics 4 impostato dall'amministratore (vuoto = statistiche spente).
// Lo carica il plugin analytics.client.ts; banner e pagine lo leggono per adattare i testi.
export const useAnalyticsId = () => useState<string>('ga_measurement_id', () => '')
