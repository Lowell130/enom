<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[1240px]">
    
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Cantine</h1>
        <p class="text-sm text-ink-soft mt-1.5">Approva le nuove registrazioni, modifica i profili e gestisci le richieste di cancellazione.</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <button v-if="toInvite.length" type="button" class="btn-ghost btn-sm h-11" @click="inviteAllOpen = true">
          <Send class="w-4 h-4" aria-hidden="true" /> Invita le cantine senza accesso ({{ toInvite.length }})
        </button>
        <button @click="showAddModal = true" class="inline-flex items-center space-x-1.5 px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white font-semibold text-sm rounded-xl shadow-xs transition-all">
          <Plus class="w-4 h-4 text-amber-200" />
          <span>Aggiungi Nuova Cantina</span>
        </button>
      </div>
    </div>

    <!-- Filtro per stato -->
    <div role="tablist" aria-label="Filtra per stato" class="flex flex-wrap gap-1.5 mb-4">
      <button v-for="f in statusFilters" :key="f.value" type="button" role="tab" :aria-selected="statusFilter === f.value"
              :class="['pill', statusFilter === f.value && 'pill-active']" @click="setFilter(f.value)">
        {{ f.label }} <span class="ml-1.5 opacity-70">{{ f.count }}</span>
      </button>
    </div>

    <!-- Producers Table -->
    <div class="bg-white rounded-2xl border border-line shadow-xs overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-ink-mute">
        Caricamento cantine in corso...
      </div>
      <p v-else-if="!visibleProducers.length" class="p-10 text-center text-sm text-ink-mute m-0">Nessuna cantina in questo elenco.</p>

      <div v-else-if="visibleProducers.length" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-ink-soft">
          <thead class="bg-stone-50 text-xs uppercase font-bold text-ink-mute border-b border-stone-100">
            <tr>
              <th class="py-4 px-6">Cantina</th>
              <th class="py-4 px-6">Città / Prov.</th>
              <th class="py-4 px-6">Contatti</th>
              <th class="py-4 px-6">Vini a Catalogo</th>
              <th class="py-4 px-6 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100">
            <tr v-for="p in visibleProducers" :key="p.id" :class="['transition-colors', p.status === 'PENDING_APPROVAL' ? 'bg-[#FBF5E8]/60' : 'hover:bg-stone-50/50']">
              
              <!-- Cantina Name & Logo (Clickable Link to Producer Page) -->
              <td class="py-4 px-6 min-w-[240px]">
                <NuxtLink :to="`/produttori/${p.slug}`" target="_blank" class="flex items-center space-x-3.5 group cursor-pointer" title="Clicca per visualizzare la pagina della cantina">
                  <div class="logo-box w-12 h-12 shrink-0 rounded-xl border border-line text-base group-hover:border-wine-300 transition-colors">
                    <SafeImg :src="getLogo(p)" alt="" class="logo-img p-1">{{ initials(p.company_name) }}</SafeImg>
                  </div>
                  <div>
                    <span class="font-sans font-bold text-sm text-ink group-hover:text-wine-800 leading-snug block transition-colors">{{ p.company_name }}</span>
                    <span class="text-xs text-ink-mute font-medium block mt-0.5">slug: {{ p.slug }}</span>
                    <span v-if="p.status && p.status !== 'APPROVED'" :class="['inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide', p.status === 'SUSPENDED' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800']">
                      {{ p.status === 'SUSPENDED' ? 'Sospesa' : 'In attesa di approvazione' }}
                    </span>
                    <span v-if="p.hide_photos" class="inline-block mt-1 mr-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-stone-200 text-ink-soft"
                          title="Le foto dei vini non sono visibili al pubblico">
                      Foto nascoste
                    </span>
                    <span v-if="p.content_consent_at" class="inline-block mt-1 mr-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-bio-50 text-bio-900"
                          :title="`Ha autorizzato la pubblicazione di testi e foto il ${fmtDay(p.content_consent_at)}`">
                      Contenuti autorizzati
                    </span>
                    <span v-if="p.deletion_requested_at" class="inline-block mt-1 ml-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-wine-800 text-white"
                          :title="p.deletion_reason ? `Motivo: ${p.deletion_reason}` : 'Nessun motivo indicato'">
                      Chiede la cancellazione
                    </span>
                  </div>
                </NuxtLink>
              </td>

              <!-- Città / Prov & Coordinate GPS -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span v-if="p.address?.city" class="font-bold text-ink block text-xs">{{ p.address.city }}<template v-if="p.address?.province"> ({{ p.address.province }})</template></span>
                <span v-else class="font-bold text-wine-800 block text-xs">Comune non indicato</span>
                <span v-if="p.address?.geo_coordinates?.lat" class="text-wine-800 font-mono text-[11px] block mt-0.5" title="Coordinate GPS">
                  📍 {{ p.address.geo_coordinates.lat.toFixed(4) }}, {{ p.address.geo_coordinates.lng.toFixed(4) }}
                </span>
                <span v-else class="text-stone-400 font-medium block mt-0.5 text-[11px]">Nessun punto sulla mappa</span>
              </td>

              <!-- Contatti e accesso -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span :class="['inline-flex items-center gap-1 mb-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide', accountBadge(p).cls]" :title="accountBadge(p).title">
                  {{ accountBadge(p).label }}
                </span>
                <span v-if="p.contacts?.email_contact" class="font-medium text-ink-soft block text-xs flex items-center space-x-1">
                  <Mail class="w-3.5 h-3.5 text-stone-400 shrink-0" />
                  <span>{{ p.contacts.email_contact }}</span>
                </span>
                <div class="flex items-center space-x-3 mt-1 text-ink-mute font-medium text-[11px]">
                  <span v-if="p.contacts?.phone" class="inline-flex items-center space-x-1">
                    <Phone class="w-3 h-3 text-stone-400" />
                    <span>{{ p.contacts.phone }}</span>
                  </span>
                  <span v-if="p.contacts?.whatsapp_number" class="inline-flex items-center space-x-1 text-emerald-700 font-semibold">
                    <MessageSquare class="w-3 h-3 text-emerald-600" />
                    <span>WA: {{ p.contacts.whatsapp_number }}</span>
                  </span>
                </div>
              </td>

              <!-- Vini a Catalogo -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span class="px-3 py-1 bg-wine-50 text-wine-900 rounded-full font-bold border border-wine-200/60 inline-flex items-center space-x-1.5">
                  <Wine class="w-3.5 h-3.5 text-wine-800" />
                  <span>{{ wineCount(p.product_count) }}</span>
                </span>
                <span v-if="(p.total_product_count || 0) > (p.product_count || 0)" class="block mt-1 text-[11px] text-ink-mute">
                  {{ p.total_product_count }} inseriti in totale
                </span>
              </td>

              <!-- Azioni (Aligned 2-Row Layout matching Gestione Prodotti) -->
              <td class="py-4 px-6 text-right whitespace-nowrap">
                <div class="flex flex-col items-end space-y-1.5">
                  
                  <!-- Azione rapida sullo stato -->
                  <button v-if="p.status === 'PENDING_APPROVAL'" type="button" class="btn-primary btn-sm h-8 px-3 text-xs" @click="quickStatus(p, 'APPROVED')">
                    <Check class="w-3.5 h-3.5" aria-hidden="true" /> Approva
                  </button>
                  <button v-else-if="p.status === 'SUSPENDED'" type="button" class="btn-outline btn-sm h-8 px-3 text-xs" @click="quickStatus(p, 'APPROVED')">
                    Riattiva
                  </button>
                  <button v-if="(p.account?.status || 'none') !== 'active'" type="button" class="btn-ghost btn-sm h-8 px-3 text-xs" :disabled="inviting === p.id" @click="openInvite(p)">
                    <Send class="w-3.5 h-3.5" aria-hidden="true" /> {{ (p.account?.status || 'none') === 'none' ? 'Invita' : 'Rimanda invito' }}
                  </button>

                  <!-- Row 1: Vedi Pagina & Modifica -->
                  <div class="flex items-center space-x-2">
                    <NuxtLink 
                      :to="`/produttori/${p.slug}`"
                      target="_blank"
                      class="px-3 py-1.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 text-ink-soft rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-line"
                      title="Visualizza Pagina Cantina"
                    >
                      <Eye class="w-3.5 h-3.5 text-wine-800" />
                      <span>Vedi</span>
                    </NuxtLink>

                    <button 
                      @click="openEditModal(p)" 
                      class="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-line"
                    >
                      <Pencil class="w-3.5 h-3.5 text-ink-mute" />
                      <span>Modifica</span>
                    </button>
                  </div>

                  <!-- Row 2: Elimina -->
                  <div class="flex items-center space-x-2">
                    <button 
                      @click="handleDelete(p.id)" 
                      class="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-rose-200/50"
                      title="Elimina definitivo"
                    >
                      <Trash2 class="w-3.5 h-3.5 text-rose-600" />
                      <span>Elimina</span>
                    </button>
                  </div>

                </div>
              </td>

            </tr>
          </tbody>
        </table>
      </div>

    </div>

    <!-- MODAL NUOVA CANTINA -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto border border-stone-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-sans text-xl font-bold text-ink">Aggiungi Nuova Cantina</h3>
          <button @click="showAddModal = false" class="text-stone-400 hover:text-ink-soft p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleAddProducer" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Nome Cantina *</label>
            <input v-model="newProducer.company_name" type="text" required placeholder="es. Cantine del Molise" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Città *</label>
              <input v-model="newProducer.city" type="text" required placeholder="es. Larino" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">CAP</label>
              <input v-model="newProducer.zip_code" type="text" placeholder="86010" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Provincia</label>
              <input v-model="newProducer.province" type="text" placeholder="CB" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Indirizzo (Via/Contrada)</label>
            <input v-model="newProducer.street" type="text" placeholder="Via Matese 10" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
          </div>

          <!-- Coordinate GPS Mappa -->
          <div class="grid grid-cols-2 gap-3 bg-stone-50 p-3 rounded-xl border border-line">
            <div>
              <label class="block text-[11px] font-semibold text-ink-soft mb-1">Latitudine GPS (es. 41,6147818)</label>
              <input v-model="newProducer.lat" type="text" placeholder="41,6147818" class="w-full bg-white border border-stone-200 rounded-lg px-3 py-1.5 text-xs font-mono" />
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-ink-soft mb-1">Longitudine GPS (es. 14,5462307)</label>
              <input v-model="newProducer.lng" type="text" placeholder="14,5462307" class="w-full bg-white border border-stone-200 rounded-lg px-3 py-1.5 text-xs font-mono" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Email Contatto</label>
              <input v-model="newProducer.email_contact" type="email" placeholder="info@cantina.it" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Telefono</label>
              <input v-model="newProducer.phone" type="text" placeholder="+39 0874 12345" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Numero WhatsApp (es. 393331234567)</label>
              <input v-model="newProducer.whatsapp_number" type="text" placeholder="393331234567" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Sito Web Ufficiale</label>
              <input v-model="newProducer.website" type="text" placeholder="https://..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">URL Logo Cantina</label>
            <input v-model="newProducer.logo_url" type="text" placeholder="https://... o carica" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUploadMedia(e, 'logo', 'new')" class="text-xs text-ink-mute" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">URL Foto Copertina Cantina</label>
            <input v-model="newProducer.cover_image_url" type="text" placeholder="https://... o carica" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUploadMedia(e, 'cover', 'new')" class="text-xs text-ink-mute" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Descrizione / Storia</label>
            <textarea v-model="newProducer.description" rows="3" placeholder="Breve descrizione della cantina..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm"></textarea>
          </div>

          <div class="pt-2 flex justify-end space-x-3">
            <button type="button" @click="showAddModal = false" class="px-4 py-2 text-sm text-ink-soft font-semibold">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs">Crea Cantina</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL MODIFICA CANTINA -->
    <div v-if="showEditModal" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-xl w-full p-6 sm:p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto border border-stone-100">
        <div class="flex items-center justify-between mb-4 border-b border-stone-100 pb-3">
          <h3 class="font-sans text-xl font-bold text-ink">Modifica Cantina: {{ editProducer.company_name }}</h3>
          <button @click="showEditModal = false" class="text-stone-400 hover:text-ink-soft p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleUpdateProducer" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Nome Cantina / Azienda *</label>
            <input v-model="editProducer.company_name" type="text" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Stato pubblicazione</label>
            <select v-model="editProducer.status" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm bg-white">
              <option value="APPROVED">Approvata (visibile al pubblico)</option>
              <option value="PENDING_APPROVAL">In attesa di approvazione</option>
              <option value="SUSPENDED">Sospesa</option>
            </select>
          </div>

          <label class="flex items-start gap-2.5 p-3 rounded-xl border border-stone-200 cursor-pointer">
            <input v-model="editProducer.hide_photos" type="checkbox" class="mt-0.5 w-4 h-4 accent-wine-800 shrink-0" />
            <span class="text-sm">
              <span class="font-semibold text-ink block">Nascondi le foto dei vini</span>
              <span class="text-xs text-ink-soft">
                I visitatori vedono la sagoma della bottiglia al posto delle foto. Le foto restano salvate e la cantina continua a vederle.
                <template v-if="editProducer.content_consent_at"> La cantina ha autorizzato testi e foto il {{ fmtDay(editProducer.content_consent_at) }}.</template>
                <template v-else> La cantina non ha ancora autorizzato la pubblicazione (lo fa attivando l'invito).</template>
              </span>
            </span>
          </label>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Città *</label>
              <input v-model="editProducer.city" type="text" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">CAP</label>
              <input v-model="editProducer.zip_code" type="text" placeholder="86010" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Provincia</label>
              <input v-model="editProducer.province" type="text" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Indirizzo (Via/Contrada)</label>
            <input v-model="editProducer.street" type="text" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
          </div>

          <!-- Posizione sulla mappa -->
          <ClientOnly>
            <LocationPicker :lat="editProducer.lat" :lng="editProducer.lng" :town="editProducer.city"
              @update="({ lat, lng }) => { editProducer.lat = lat ?? ''; editProducer.lng = lng ?? '' }" />
          </ClientOnly>
          <div class="grid grid-cols-2 gap-3 bg-stone-50 p-3 rounded-xl border border-line">
            <div>
              <label class="block text-[11px] font-semibold text-ink-soft mb-1">Latitudine GPS (es. 41,6147818)</label>
              <input v-model="editProducer.lat" type="text" placeholder="41,6147818" class="w-full bg-white border border-stone-200 rounded-lg px-3 py-1.5 text-xs font-mono" />
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-ink-soft mb-1">Longitudine GPS (es. 14,5462307)</label>
              <input v-model="editProducer.lng" type="text" placeholder="14,5462307" class="w-full bg-white border border-stone-200 rounded-lg px-3 py-1.5 text-xs font-mono" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Email Contatto</label>
              <input v-model="editProducer.email_contact" type="email" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Telefono</label>
              <input v-model="editProducer.phone" type="text" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">WhatsApp (es. 393331234567)</label>
              <input v-model="editProducer.whatsapp_number" type="text" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-ink-soft mb-1">Sito Web</label>
              <input v-model="editProducer.website" type="text" placeholder="https://..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">URL Logo Cantina</label>
            <input v-model="editProducer.logo_url" type="text" placeholder="https://... o carica" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUploadMedia(e, 'logo', 'edit')" class="text-xs text-ink-mute" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">URL Foto Copertina Cantina</label>
            <input v-model="editProducer.cover_image_url" type="text" placeholder="https://... o carica" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUploadMedia(e, 'cover', 'edit')" class="text-xs text-ink-mute" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Descrizione / Storia Cantina</label>
            <textarea v-model="editProducer.description" rows="4" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm"></textarea>
          </div>

          <div class="pt-4 flex justify-end space-x-3 border-t border-stone-100">
            <button type="button" @click="showEditModal = false" class="px-4 py-2.5 text-sm text-ink-soft font-semibold hover:bg-stone-50 rounded-xl">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs hover:bg-wine-900">Salva Modifiche</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Invito singolo -->
    <div v-if="inviteTarget" class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="invito-titolo" @click.self="inviteTarget = null">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-line flex flex-col gap-4">
        <h3 id="invito-titolo" class="font-sans text-lg font-bold text-ink m-0">Invita {{ inviteTarget.company_name }}</h3>
        <p class="text-sm text-ink-soft m-0">
          Mandiamo un'email con un link personale (valido 14 giorni) per scegliere la password e gestire la pagina della cantina.
          <template v-if="inviteTarget.account?.status && inviteTarget.account.status !== 'none'"> Il link inviato prima non varrà più.</template>
        </p>
        <label class="field-label">Email della cantina
          <input v-model="inviteEmail" type="email" class="input" placeholder="info@cantina.it" />
          <span class="text-[13px] font-normal text-ink-mute">Sarà anche l'email di accesso.</span>
        </label>
        <p v-if="inviteError" role="alert" class="m-0 text-sm font-semibold text-wine-800">{{ inviteError }}</p>
        <div class="flex justify-end gap-3">
          <button type="button" class="btn-ghost btn-sm h-10" @click="inviteTarget = null">Annulla</button>
          <button type="button" class="btn-primary btn-sm h-10" :disabled="!inviteEmail || inviting" @click="sendInvite">
            <Send class="w-4 h-4" aria-hidden="true" /> {{ inviting ? 'Invio…' : 'Manda l\'invito' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Invito a tutte -->
    <div v-if="inviteAllOpen" class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="invito-tutte-titolo" @click.self="inviteAllOpen = false">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-line flex flex-col gap-4">
        <h3 id="invito-tutte-titolo" class="font-sans text-lg font-bold text-ink m-0">Invitare {{ toInvite.length }} {{ toInvite.length === 1 ? 'cantina' : 'cantine' }}?</h3>
        <p class="text-sm text-ink-soft m-0">Ognuna riceve all'email di contatto il link per attivare l'accesso. Le cantine con l'accesso attivo o già invitate non vengono toccate.</p>
        <ul class="list-none m-0 p-0 max-h-[220px] overflow-y-auto text-sm border border-line rounded-xl divide-y divide-stone-100">
          <li v-for="p in toInvite" :key="p.id" class="px-3 py-2 flex justify-between gap-3"><span class="font-semibold text-ink truncate">{{ p.company_name }}</span><span class="text-ink-mute truncate">{{ p.contacts.email_contact }}</span></li>
        </ul>
        <p v-if="withoutEmail.length" class="m-0 text-[13px] text-wine-800">
          Senza email di contatto, quindi non invitate: {{ withoutEmail.map(p => p.company_name).join(', ') }}.
        </p>
        <p v-if="emailMode !== 'smtp'" class="m-0 text-[13px] p-3 rounded-xl bg-[#FBF5E8] border border-[#E8D9B8] text-[#5A4524]">
          Le email non vengono spedite davvero finché non configuri l'invio (SMTP): le trovi in «Email e testi → Posta in uscita».
        </p>
        <div class="flex justify-end gap-3">
          <button type="button" class="btn-ghost btn-sm h-10" @click="inviteAllOpen = false">Annulla</button>
          <button type="button" class="btn-primary btn-sm h-10" :disabled="inviting" @click="sendInviteAll">
            <Send class="w-4 h-4" aria-hidden="true" /> {{ inviting ? 'Invio…' : 'Manda gli inviti' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, Pencil, Eye, Trash2, X, Mail, Phone, MessageSquare, Wine, Check, Send } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'
import LocationPicker from '~/components/LocationPicker.client.vue'

const { fetchWithAuth, mediaBase } = useApi()
const toast = useToast()

const showAddModal = ref(false)
const showEditModal = ref(false)

const { data: producers, pending, refresh } = await useAsyncData('admin_producers_manage', async () => {
  const res = await fetchWithAuth('/producers?include_all=true')
  return res || []
}, { default: () => [] })

const route = useRoute()
const router = useRouter()
const { initials } = useProducer()

// filtro per stato (anche dal link "Rivedi" della panoramica: ?stato=PENDING_APPROVAL)
const statusFilter = ref(String(route.query.stato || 'ALL'))
const setFilter = (value) => {
  statusFilter.value = value
  router.replace({ query: { ...route.query, stato: value === 'ALL' ? undefined : value } })
}
const statusFilters = computed(() => {
  const list = producers.value || []
  return [
    { value: 'ALL', label: 'Tutte', count: list.length },
    { value: 'PENDING_APPROVAL', label: 'In attesa', count: list.filter(p => p.status === 'PENDING_APPROVAL').length },
    { value: 'APPROVED', label: 'Approvate', count: list.filter(p => (p.status || 'APPROVED') === 'APPROVED').length },
    { value: 'SUSPENDED', label: 'Sospese', count: list.filter(p => p.status === 'SUSPENDED').length },
    { value: 'DELETION', label: 'Chiedono la cancellazione', count: list.filter(p => p.deletion_requested_at).length }
  ]
})
// prima le cantine da approvare e quelle che chiedono la cancellazione, poi in ordine alfabetico
const priority = (p) => (p.status === 'PENDING_APPROVAL' ? 0 : p.deletion_requested_at ? 1 : 2)
const visibleProducers = computed(() => {
  const list = (producers.value || []).filter((p) => {
    if (statusFilter.value === 'ALL') return true
    if (statusFilter.value === 'DELETION') return !!p.deletion_requested_at
    return (p.status || 'APPROVED') === statusFilter.value
  })
  return [...list].sort((a, b) => priority(a) - priority(b) || a.company_name.localeCompare(b.company_name, 'it'))
})

const wineCount = (n) => {
  const count = n || 0
  return count === 1 ? '1 vino' : `${count} vini`
}

// accesso delle cantine: inviti via email
const ACCOUNT = {
  none: { label: 'Nessun accesso', cls: 'bg-stone-100 text-ink-mute' },
  invited: { label: 'Invito inviato', cls: 'bg-amber-100 text-amber-800' },
  expired: { label: 'Invito scaduto', cls: 'bg-rose-100 text-rose-800' },
  active: { label: 'Accesso attivo', cls: 'bg-bio-50 text-bio-900' }
}
const fmtDay = (v) => (v ? new Date(String(v).endsWith('Z') ? v : `${v}Z`).toLocaleDateString('it-IT', { day: 'numeric', month: 'long' }) : '')
const accountBadge = (p) => {
  const a = p.account || { status: 'none' }
  const base = ACCOUNT[a.status] || ACCOUNT.none
  const title = a.status === 'invited' ? `Inviato il ${fmtDay(a.invited_at)} a ${a.email}, scade il ${fmtDay(a.expires_at)}`
    : a.status === 'expired' ? `Inviato a ${a.email}: il link è scaduto il ${fmtDay(a.expires_at)}`
    : a.status === 'active' ? `Accede con ${a.email}` : 'La cantina non ha ancora un accesso al sito'
  return { ...base, title }
}
const toInvite = computed(() => (producers.value || []).filter(p => (p.account?.status || 'none') === 'none' && p.contacts?.email_contact))
const withoutEmail = computed(() => (producers.value || []).filter(p => (p.account?.status || 'none') === 'none' && !p.contacts?.email_contact))
const inviteTarget = ref(null)
const inviteEmail = ref('')
const inviteError = ref('')
const inviting = ref(null)
const inviteAllOpen = ref(false)
const { data: emailStatus } = await useAsyncData('email_status_cantine', () => fetchWithAuth('/emails/status').catch(() => null))
const emailMode = computed(() => emailStatus.value?.mode || 'outbox')

const openInvite = (p) => {
  inviteTarget.value = p
  inviteEmail.value = p.account?.email || p.contacts?.email_contact || ''
  inviteError.value = ''
}
const sendInvite = async () => {
  const p = inviteTarget.value
  inviting.value = p.id
  inviteError.value = ''
  try {
    const res = await fetchWithAuth(`/producers/${p.id}/invite`, { method: 'POST', body: { email: inviteEmail.value } })
    toast.success(res.message || 'Invito mandato.')
    inviteTarget.value = null
    await refresh()
  } catch (err) {
    inviteError.value = apiErrorMessage(err, 'Invio non riuscito.')
  } finally {
    inviting.value = null
  }
}
const sendInviteAll = async () => {
  inviting.value = 'all'
  try {
    const res = await fetchWithAuth('/producers/invite-all', { method: 'POST' })
    toast.success(res.message)
    inviteAllOpen.value = false
    await refresh()
  } catch (err) {
    toast.error(apiErrorMessage(err, 'Invio non riuscito.'))
  } finally {
    inviting.value = null
  }
}

const quickStatus = async (p, status) => {
  try {
    await fetchWithAuth(`/producers/${p.id}`, { method: 'PUT', body: { status } })
    toast.success(status === 'APPROVED'
      ? `${p.company_name} è online: abbiamo avvisato la cantina via email.`
      : `${p.company_name} è stata sospesa.`)
    await refresh()
  } catch (err) {
    toast.error(apiErrorMessage(err))
  }
}

const newProducer = reactive({
  company_name: '',
  city: '',
  province: '',
  zip_code: '',
  street: '',
  lat: '',
  lng: '',
  email_contact: '',
  phone: '',
  whatsapp_number: '',
  website: '',
  logo_url: '',
  cover_image_url: '',
  description: ''
})

const editProducer = reactive({
  id: '',
  company_name: '',
  status: 'APPROVED',
  hide_photos: false,
  content_consent_at: null,
  city: '',
  province: '',
  zip_code: '',
  street: '',
  lat: '',
  lng: '',
  email_contact: '',
  phone: '',
  whatsapp_number: '',
  website: '',
  logo_url: '',
  cover_image_url: '',
  description: ''
})

const getLogo = (p) => {
  if (!p.logo_url) return ''
  return p.logo_url.startsWith('http') ? p.logo_url : `${mediaBase}${p.logo_url}`
}

const openEditModal = (p) => {
  const pGeo = p.address?.geo_coordinates || {}
  editProducer.id = p.id
  editProducer.company_name = p.company_name
  editProducer.status = p.status || 'APPROVED'
  editProducer.hide_photos = !!p.hide_photos
  editProducer.content_consent_at = p.content_consent_at || null
  editProducer.city = p.address?.city || ''
  editProducer.province = p.address?.province || ''
  editProducer.zip_code = p.address?.zip_code || ''
  editProducer.street = p.address?.street || ''
  editProducer.lat = pGeo.lat || ''
  editProducer.lng = pGeo.lng || ''
  editProducer.email_contact = p.contacts?.email_contact || ''
  editProducer.phone = p.contacts?.phone || ''
  editProducer.whatsapp_number = p.contacts?.whatsapp_number || ''
  editProducer.website = p.contacts?.website || ''
  editProducer.logo_url = p.logo_url || ''
  editProducer.cover_image_url = p.cover_image_url || ''
  editProducer.description = p.description || ''
  showEditModal.value = true
}

const handleUploadMedia = async (event, type, target = 'edit') => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await fetchWithAuth('/uploads/image', {
      method: 'POST',
      body: formData
    })
    const targetObj = target === 'new' ? newProducer : editProducer
    if (type === 'logo') targetObj.logo_url = res.url
    if (type === 'cover') targetObj.cover_image_url = res.url
    toast.success('Immagine caricata con successo!')
  } catch (err) {
    toast.error('Errore durante l\'upload dell\'immagine.')
  }
}

const parseCoordInput = (val) => {
  if (val === null || val === undefined || val === '') return null
  const num = Number(String(val).replace(',', '.').trim())
  return isNaN(num) ? null : num
}

const handleAddProducer = async () => {
  try {
    const latNum = parseCoordInput(newProducer.lat)
    const lngNum = parseCoordInput(newProducer.lng)
    const geo = (latNum !== null && lngNum !== null) ? { lat: latNum, lng: lngNum } : null
    await fetchWithAuth('/producers', {
      method: 'POST',
      body: {
        company_name: newProducer.company_name,
        description: newProducer.description,
        logo_url: newProducer.logo_url,
        cover_image_url: newProducer.cover_image_url,
        address: { 
          street: newProducer.street, 
          city: newProducer.city, 
          province: newProducer.province,
          zip_code: newProducer.zip_code,
          geo_coordinates: geo
        },
        contacts: { 
          email_contact: newProducer.email_contact, 
          phone: newProducer.phone, 
          whatsapp_number: newProducer.whatsapp_number,
          website: newProducer.website
        }
      }
    })
    showAddModal.value = false
    // Reset form fields
    newProducer.company_name = ''
    newProducer.street = ''
    newProducer.zip_code = ''
    newProducer.lat = ''
    newProducer.lng = ''
    newProducer.email_contact = ''
    newProducer.phone = ''
    newProducer.whatsapp_number = ''
    newProducer.website = ''
    newProducer.logo_url = ''
    newProducer.cover_image_url = ''
    newProducer.description = ''
    toast.success('Cantina creata con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante la creazione della cantina.')
  }
}

const handleUpdateProducer = async () => {
  try {
    const latNum = parseCoordInput(editProducer.lat)
    const lngNum = parseCoordInput(editProducer.lng)
    const geo = (latNum !== null && lngNum !== null) ? { lat: latNum, lng: lngNum } : null
    await fetchWithAuth(`/producers/${editProducer.id}`, {
      method: 'PUT',
      body: {
        company_name: editProducer.company_name,
        status: editProducer.status,
        hide_photos: editProducer.hide_photos,
        description: editProducer.description,
        logo_url: editProducer.logo_url,
        cover_image_url: editProducer.cover_image_url,
        address: {
          street: editProducer.street,
          city: editProducer.city,
          province: editProducer.province,
          zip_code: editProducer.zip_code,
          geo_coordinates: geo
        },
        contacts: {
          email_contact: editProducer.email_contact,
          phone: editProducer.phone,
          whatsapp_number: editProducer.whatsapp_number,
          website: editProducer.website
        }
      }
    })
    toast.success('Cantina aggiornata con successo!')
    showEditModal.value = false
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'aggiornamento della cantina.')
  }
}

const handleDelete = async (id) => {
  if (!confirm('Eliminare questa cantina e TUTTI i suoi vini?')) return
  try {
    await fetchWithAuth(`/producers/${id}`, { method: 'DELETE' })
    toast.success('Cantina eliminata con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'eliminazione.')
  }
}
</script>
