// Riduce nel browser le immagini troppo grandi prima di inviarle al server:
// un logo di 8000 px occupa centinaia di MB quando il server lo decomprime e
// Cloud Run può esaurire la memoria (errore 503). Il server le porta comunque a
// 2400 px, quindi ridurle qui non perde qualità e rende il caricamento più veloce.
// Se il browser non riesce a leggere il file (formati rari) si invia l'originale.

const MAX_SIDE = 2400
const MAX_BYTES_UNTOUCHED = 1.5 * 1024 * 1024

const loadBitmap = async (file: File): Promise<ImageBitmap | HTMLImageElement> => {
  if ('createImageBitmap' in window) {
    try {
      // rispetta l'orientamento delle foto scattate col telefono
      return await createImageBitmap(file, { imageOrientation: 'from-image' } as any)
    } catch { /* si prova con <img> */ }
  }
  const url = URL.createObjectURL(file)
  try {
    const img = new Image()
    img.decoding = 'async'
    img.src = url
    await img.decode()
    return img
  } finally {
    URL.revokeObjectURL(url)
  }
}

export const shrinkImage = async (file: File): Promise<File> => {
  if (!import.meta.client || !file?.type?.startsWith('image/') || /svg|gif/i.test(file.type)) return file
  let source: ImageBitmap | HTMLImageElement
  try {
    source = await loadBitmap(file)
  } catch {
    return file
  }
  const w = 'naturalWidth' in source ? source.naturalWidth : source.width
  const h = 'naturalHeight' in source ? source.naturalHeight : source.height
  const scale = Math.min(1, MAX_SIDE / Math.max(w, h))
  if (scale === 1 && file.size <= MAX_BYTES_UNTOUCHED) {
    if ('close' in source) source.close()
    return file
  }
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(w * scale))
  canvas.height = Math.max(1, Math.round(h * scale))
  const ctx = canvas.getContext('2d')
  if (!ctx) return file
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(source as CanvasImageSource, 0, 0, canvas.width, canvas.height)
  if ('close' in source) source.close()

  // WebP tiene la trasparenza dei loghi; dove non è supportato il browser restituisce PNG
  const blob: Blob | null = await new Promise(resolve => canvas.toBlob(resolve, 'image/webp', 0.9))
  if (!blob) return file
  const ext = blob.type === 'image/webp' ? 'webp' : blob.type === 'image/jpeg' ? 'jpg' : 'png'
  const name = (file.name || 'immagine').replace(/\.[^.]+$/, '') + '.' + ext
  // se per assurdo il risultato pesa di più e l'originale non era enorme, si tiene l'originale
  if (blob.size >= file.size && scale === 1) return file
  return new File([blob], name, { type: blob.type })
}
