<template>
  <div class="py-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <div class="mb-8">
      <NuxtLink to="/dashboard/prodotti" class="text-xs font-semibold text-wine-800 hover:text-wine-900 mb-2 inline-flex items-center gap-1">
        <ArrowLeft class="w-3.5 h-3.5" />
        <span>Torna alla lista prodotti</span>
      </NuxtLink>
      <h1 class="font-sans text-3xl font-bold text-gray-900">
        Modifica Scheda Vino
      </h1>
      <p class="text-xs text-gray-500 mt-1">
        Aggiorna le informazioni della bottiglia, la scheda tecnica dettagliata e la cantina associata.
      </p>
    </div>

    <div v-if="pending" class="p-12 text-center text-sm text-gray-500">
      Caricamento scheda vino...
    </div>

    <form v-else-if="form" @submit.prevent="handleSubmit" class="space-y-8 bg-white rounded-3xl p-8 border border-gray-100 shadow-sm">
      
      <!-- ADMIN PRODUCER ASSIGNMENT SELECTOR -->
      <div v-if="isAdmin" class="bg-amber-50/70 p-5 rounded-2xl border border-amber-200/60">
        <label class="flex items-center gap-1.5 text-xs font-bold text-amber-900 mb-1 uppercase tracking-wider">
          <Shield class="w-4 h-4 text-amber-700" />
          <span>Cantina Associata (Modificabile dall'Admin) *</span>
        </label>
        <select 
          v-model="form.producer_id" 
          required 
          class="w-full border border-amber-300/80 rounded-xl px-4 py-2.5 text-sm font-semibold bg-white focus:ring-2 focus:ring-wine-800 focus:outline-none"
        >
          <option v-for="p in producers" :key="p.id" :value="p.id">
            {{ p.company_name }} ({{ p.address?.city || 'Molise' }})
          </option>
        </select>
      </div>

      <!-- Informazioni Generali -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-wine-100 pb-2">
          Dettagli Generali Bottiglia
        </h3>

        <div class="space-y-5">
          <!-- Row 1: Nome Vino & Tipologia -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div class="sm:col-span-2">
              <label class="block text-xs font-semibold text-gray-700 mb-1">Nome Vino / Etichetta *</label>
              <input 
                v-model="form.name" 
                type="text" 
                required 
                class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Tipologia *</label>
              <select v-model="form.category" required class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none">
                <option value="VINO_ROSSO">Vino Rosso</option>
                <option value="VINO_BIANCO">Vino Bianco</option>
                <option value="ROSATO">Rosato</option>
                <option value="SPUMANTE">Spumante</option>
                <option value="PASSITO">Passito</option>
                <option value="LIQUORE">Liquore / Grappa</option>
              </select>
            </div>
          </div>

          <!-- Row 2: Denominazione, Gradazione, Temperatura, Prezzo -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Denominazione *</label>
              <input 
                v-model="form.denominazione" 
                type="text" 
                required 
                class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Gradazione Alcolica (% Vol)</label>
              <input 
                v-model.number="form.alcohol_degrees" 
                type="number" 
                step="0.1" 
                class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Temperatura di Servizio</label>
              <input 
                v-model="form.serving_temperature" 
                type="text" 
                class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Prezzo Indicativo / Fascia</label>
              <input 
                v-model="form.indicative_price" 
                type="text" 
                class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
              />
            </div>
          </div>

          <!-- Row 3: Annata Vendemmia & Menzione Riserva -->
          <div class="bg-stone-50/70 p-5 rounded-2xl border border-stone-200/60 space-y-3">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <label class="block text-xs font-bold text-stone-800 uppercase tracking-wider">
                Annata Vendemmia & Menzione Riserva
              </label>
              
              <!-- Quick Preset Buttons -->
              <div class="flex flex-wrap items-center gap-1.5">
                <span class="text-[10px] font-semibold text-stone-400 uppercase">Preset:</span>
                <button 
                  type="button"
                  @click="form.is_riserva = false"
                  :class="['px-2.5 py-1 rounded-lg text-xs font-bold transition-all border cursor-pointer', !form.is_riserva && form.vintage_year ? 'bg-wine-800 text-white border-wine-800' : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100']"
                >
                  Annata
                </button>
                <button 
                  type="button"
                  @click="form.is_riserva = true"
                  :class="['px-2.5 py-1 rounded-lg text-xs font-bold transition-all border cursor-pointer', form.is_riserva && form.vintage_year ? 'bg-wine-800 text-white border-wine-800' : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100']"
                >
                  Annata + Riserva
                </button>
                <button 
                  type="button"
                  @click="form.is_riserva = true; form.vintage_year = null"
                  :class="['px-2.5 py-1 rounded-lg text-xs font-bold transition-all border cursor-pointer', form.is_riserva && !form.vintage_year ? 'bg-wine-800 text-white border-wine-800' : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100']"
                >
                  Solo Riserva
                </button>
                <button 
                  type="button"
                  @click="form.is_riserva = false; form.vintage_year = null"
                  :class="['px-2.5 py-1 rounded-lg text-xs font-bold transition-all border cursor-pointer', !form.is_riserva && !form.vintage_year ? 'bg-wine-800 text-white border-wine-800' : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100']"
                >
                  Senza Annata (S.A.)
                </button>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
              <div>
                <label class="block text-[11px] font-semibold text-stone-600 mb-1">Anno Vendemmia (es. 2022 - Opzionale se Riserva)</label>
                <input 
                  v-model.number="form.vintage_year" 
                  type="number" 
                  placeholder="es. 2022" 
                  class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm bg-white focus:ring-2 focus:ring-wine-800 focus:outline-none"
                />
              </div>

              <div class="flex items-center space-x-2 pt-1 sm:pt-5">
                <label class="inline-flex items-center space-x-2.5 cursor-pointer bg-white px-4 py-2.5 rounded-xl border border-stone-200 shadow-2xs hover:border-wine-300 transition-colors w-full">
                  <input 
                    v-model="form.is_riserva" 
                    type="checkbox" 
                    class="w-4 h-4 text-wine-800 rounded border-stone-300 focus:ring-wine-800"
                  />
                  <span class="text-xs font-bold text-stone-800">Menzione "Riserva" in Etichetta</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SCHEDA TECNICA DINAMICA -->
      <div class="bg-stone-50/70 p-6 rounded-2xl border border-stone-200/60">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-4">
          <div class="flex-1">
            <h3 class="font-sans text-lg font-bold text-wine-900">
              Scheda Tecnica Dettagliata (Caratteristiche Extra)
            </h3>
            <p class="text-xs text-stone-500 mt-0.5">I campi principali (Denominazione, Uvaggio, Annata, Gradazione Alcolica, Temperatura e Prezzo) vengono inclusi automaticamente nella Scheda Tecnica del vino. Qui sotto puoi aggiungere caratteristiche aggiuntive (es. Vinificazione, Affinamento, Allergeni, Altitudine).</p>
          </div>

          <button 
            type="button" 
            @click="addCustomAttributeRow()" 
            class="px-4 py-2.5 bg-wine-50 hover:bg-wine-800 text-wine-900 hover:text-white border border-wine-200/80 hover:border-wine-800 rounded-xl text-xs font-bold transition-all shadow-2xs hover:shadow-sm inline-flex items-center justify-center space-x-2 shrink-0 whitespace-nowrap cursor-pointer"
          >
            <Plus class="w-4 h-4" />
            <span>Aggiungi Caratteristica</span>
          </button>
        </div>

        <!-- Custom Attributes List -->
        <div v-if="customAttributes.length" class="space-y-4">
          <div v-for="(attr, idx) in customAttributes" :key="idx" class="p-4 bg-white rounded-2xl border border-stone-200/80 shadow-xs space-y-3">
            
            <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              
              <!-- Attribute Name Selector or Inline Custom Input -->
              <div class="w-full sm:w-2/5">
                <label class="block text-[10px] font-bold text-stone-400 uppercase tracking-wider mb-1">
                  Nome Campo (Seleziona o Crea)
                </label>
                
                <select 
                  v-if="!attr.is_custom_name"
                  v-model="attr.name" 
                  @change="handleAttributeNameChange(attr)"
                  class="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs font-semibold text-stone-800 focus:ring-2 focus:ring-wine-800 focus:outline-none"
                >
                  <option value="" disabled>-- Seleziona o crea campo --</option>
                  <option v-for="m in availableMasterAttributes" :key="m.id" :value="m.name">{{ m.name }}</option>
                  <option value="__NEW__" class="font-bold text-wine-800">➕ + Nuovo Campo Personalizzato...</option>
                </select>

                <div v-else class="flex items-center gap-1.5">
                  <input 
                    v-model="attr.custom_name_input" 
                    type="text" 
                    placeholder="es. Altitudine Vigneto" 
                    class="w-full border border-wine-300 rounded-xl px-3 py-1.5 text-xs font-semibold text-wine-900 bg-wine-50/30 focus:ring-2 focus:ring-wine-800 focus:outline-none"
                  />
                  <button 
                    type="button" 
                    @click="attr.is_custom_name = false; attr.name = ''" 
                    class="p-1 text-stone-400 hover:text-stone-700 text-xs font-bold"
                    title="Annulla inserimento manuale"
                  >
                    ✕
                  </button>
                </div>
              </div>

              <!-- Attribute Value Input with Datalist -->
              <div class="w-full sm:flex-1">
                <label class="block text-[10px] font-bold text-stone-400 uppercase tracking-wider mb-1">
                  Valore Specificato
                  <span v-if="getAttributeHint(attr.name)" class="text-wine-700 font-normal ml-1">({{ getAttributeHint(attr.name) }})</span>
                </label>
                
                <input 
                  v-model="attr.value" 
                  type="text" 
                  :list="'edit-suggestions-' + idx"
                  placeholder="es. 14.5% / Acciaio Inox / Guyot / 75 cl..." 
                  class="w-full border border-gray-200 rounded-xl px-3.5 py-2 text-xs text-stone-800 focus:ring-2 focus:ring-wine-800 focus:outline-none"
                />

                <datalist :id="'edit-suggestions-' + idx">
                  <option v-for="val in getAttributeSuggestions(attr)" :key="val" :value="val" />
                </datalist>
              </div>

              <!-- Delete Row Button -->
              <button 
                type="button" 
                @click="removeCustomAttributeRow(idx)" 
                class="self-end sm:self-center p-2 text-stone-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors mt-2 sm:mt-4"
                title="Rimuovi questa riga"
              >
                <Trash2 class="w-4 h-4" />
              </button>

            </div>

            <!-- Quick Presets / Range Chips -->
            <div v-if="getAttributeSuggestions(attr).length" class="flex flex-wrap items-center gap-1.5 pt-2 border-t border-stone-100">
              <span class="text-[10px] font-semibold text-stone-400 uppercase mr-1">Preset Rapidi:</span>
              <button 
                v-for="preset in getAttributeSuggestions(attr)" 
                :key="preset"
                type="button"
                @click="attr.value = preset"
                :class="[
                  'px-2.5 py-0.5 rounded-full text-[11px] font-medium transition-all border',
                  attr.value === preset 
                    ? 'bg-wine-800 text-white border-wine-800 shadow-xs font-bold' 
                    : 'bg-stone-50 text-stone-700 border-stone-200 hover:bg-wine-50 hover:border-wine-300 hover:text-wine-800'
                ]"
              >
                {{ preset }}
              </button>
            </div>

          </div>
        </div>

        <div v-else class="text-center py-6 text-xs text-stone-400">
          Nessun campo personalizzato ancora aggiunto. Clicca su "Aggiungi Caratteristica" per arricchire la scheda tecnica.
        </div>
      </div>

      <!-- Vitigni & Descrizione -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-wine-100 pb-2">
          Vitigni & Descrizione
        </h3>

        <div class="space-y-4">
          <div class="bg-stone-50/70 p-5 rounded-2xl border border-stone-200/60 space-y-4">
            <div class="flex items-center justify-between">
              <label class="block text-xs font-bold text-stone-800 uppercase tracking-wider">
                Vitigni / Uvaggio (Composizione Ampelografica) *
              </label>
              <span class="text-[11px] text-stone-500 font-medium">Seleziona vitigni e percentuali</span>
            </div>

            <!-- Quick Grape Chips & Percentage Selector -->
            <div class="space-y-3 bg-white p-4 rounded-2xl border border-stone-200/70 shadow-xs">
              
              <div class="flex flex-wrap items-center gap-1.5">
                <span class="text-[10px] font-bold text-stone-400 uppercase mr-1">Aggiungi Vitigno:</span>
                <button 
                  v-for="g in masterGrapes" 
                  :key="g.id"
                  type="button"
                  @click="selectGrapeForBlend(g.name)"
                  class="px-2.5 py-1 rounded-full text-xs font-semibold bg-stone-50 border border-stone-200 text-stone-800 hover:bg-wine-800 hover:text-white hover:border-wine-800 transition-all shadow-2xs"
                >
                  + {{ g.name }}
                </button>
              </div>

              <!-- Selected Grapes List with Percentages -->
              <div v-if="selectedGrapesList.length" class="space-y-2 pt-2 border-t border-stone-100">
                <span class="text-[10px] font-bold text-stone-400 uppercase block mb-1">Composizione Selezionata:</span>
                <div v-for="(gItem, idx) in selectedGrapesList" :key="idx" class="flex flex-wrap items-center gap-2 bg-stone-50 p-2.5 rounded-xl border border-stone-200/60">
                  <span class="font-bold text-xs text-stone-900 w-36 shrink-0">{{ gItem.name }}</span>
                  
                  <span class="text-xs text-stone-400 font-medium">%:</span>
                  <input 
                    v-model="gItem.percentage" 
                    type="text" 
                    placeholder="es. 100% o 80%" 
                    @input="syncGrapesInputFromList()"
                    class="w-24 border border-stone-200 rounded-lg px-2 py-1 text-xs font-bold text-wine-900 bg-white focus:ring-2 focus:ring-wine-800 focus:outline-none"
                  />

                  <!-- Percentage Preset Chips -->
                  <div class="flex flex-wrap items-center gap-1">
                    <button 
                      v-for="pct in ['100%', '80%', '70%', '50%', '30%', '20%', '10%']" 
                      :key="pct"
                      type="button"
                      @click="gItem.percentage = pct; syncGrapesInputFromList()"
                      :class="[
                        'px-2 py-0.5 rounded-md text-[10px] font-semibold transition-all border',
                        gItem.percentage === pct
                          ? 'bg-wine-800 text-white border-wine-800 shadow-2xs'
                          : 'bg-white text-stone-700 border-stone-200 hover:bg-stone-100'
                      ]"
                    >
                      {{ pct }}
                    </button>
                  </div>

                  <button 
                    type="button" 
                    @click="removeSelectedGrape(idx)" 
                    class="p-1 text-stone-400 hover:text-red-600 text-xs ml-auto font-bold"
                    title="Rimuovi vitigno"
                  >
                    ✕
                  </button>
                </div>
              </div>

            </div>

            <!-- Raw Text Input (Result & Editable) -->
            <div>
              <label class="block text-[10px] font-bold text-stone-400 uppercase tracking-wider mb-1">
                Risultato Uvaggio (Modificabile anche a mano):
              </label>
              <input 
                v-model="grapeVarietiesInput" 
                type="text" 
                placeholder="es. Tintilia 100% oppure Montepulciano 80%, Aglianico 20%" 
                class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm bg-white font-semibold text-stone-900 focus:ring-2 focus:ring-wine-800 focus:outline-none"
              />
            </div>

          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Descrizione Vino & Storia</label>
            <textarea 
              v-model="form.description" 
              rows="4" 
              class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Profilo Organolettico -->
      <div v-if="form.tasting_notes">
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-gray-100 pb-2">
          Profilo Organolettico
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Esame Visivo</label>
            <textarea v-model="form.tasting_notes.visual" rows="2" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-wine-800 focus:outline-none"></textarea>
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Esame Olfattivo</label>
            <textarea v-model="form.tasting_notes.olfactory" rows="2" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-wine-800 focus:outline-none"></textarea>
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Esame Gustativo</label>
            <textarea v-model="form.tasting_notes.taste" rows="2" class="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-wine-800 focus:outline-none"></textarea>
          </div>
        </div>
      </div>

      <!-- Abbinamenti Culinari (Smart Interactive Selector & Presets) -->
      <div class="bg-stone-50/70 p-5 rounded-2xl border border-stone-200/60 space-y-4">
        <div class="flex items-center justify-between">
          <label class="block text-xs font-bold text-stone-800 uppercase tracking-wider">
            Abbinamenti Culinari & Gastronomici *
          </label>
          <span class="text-[11px] text-stone-500 font-medium">Seleziona dai preset rapidi o inserisci custom</span>
        </div>

        <!-- Master Pairings Preset Chips -->
        <div v-if="masterPairings && masterPairings.length" class="space-y-3 bg-white p-4 rounded-2xl border border-stone-200/70 shadow-xs">
          <div class="flex flex-wrap items-center gap-1.5">
            <span class="text-[10px] font-bold text-stone-400 uppercase mr-1">Preset Rapidi Abbinamenti:</span>
            <button 
              v-for="p in masterPairings" 
              :key="p.id"
              type="button"
              @click="togglePairingPreset(p.name)"
              :class="[
                'px-2.5 py-1 rounded-full text-xs font-semibold transition-all border shadow-2xs inline-flex items-center space-x-1',
                isPairingSelected(p.name)
                  ? 'bg-wine-800 text-white border-wine-800 font-bold'
                  : 'bg-stone-50 text-stone-800 border-stone-200 hover:bg-wine-50 hover:border-wine-300 hover:text-wine-800'
              ]"
            >
              <span>{{ isPairingSelected(p.name) ? '✓' : '+' }}</span>
              <span>{{ p.name }}</span>
            </button>
          </div>
        </div>

        <!-- Selected Pairings Badges -->
        <div v-if="selectedPairingsList.length" class="flex flex-wrap items-center gap-2 pt-1">
          <span class="text-[10px] font-bold text-stone-400 uppercase mr-1 block w-full">Abbinamenti Selezionati:</span>
          <span 
            v-for="(pairing, pIdx) in selectedPairingsList" 
            :key="pIdx"
            class="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-wine-50 text-wine-900 border border-wine-200/70 rounded-xl text-xs font-bold shadow-2xs"
          >
            <Utensils class="w-3.5 h-3.5 text-wine-800" />
            <span>{{ pairing }}</span>
            <button type="button" @click="removeSelectedPairing(pIdx)" class="text-wine-400 hover:text-wine-900 p-0.5 ml-1 font-bold">✕</button>
          </span>
        </div>

        <!-- Raw Text / Custom Pairing Add Field -->
        <div class="flex gap-2">
          <input 
            v-model="foodPairingsInput" 
            type="text" 
            placeholder="Scrivi un abbinamento custom (es. Risotti ai frutti di mare, Pampa Nella Molisana...)" 
            @keydown.enter.prevent="addCustomPairingFromInput()"
            class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm bg-white font-semibold text-stone-900 focus:ring-2 focus:ring-wine-800 focus:outline-none"
          />
          <button 
            type="button" 
            @click="addCustomPairingFromInput()" 
            class="px-4 py-2.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 border border-stone-200 text-stone-800 font-bold rounded-xl text-xs shrink-0 transition-colors"
          >
            + Aggiungi
          </button>
        </div>
      </div>

      <!-- Upload Foto -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-gray-100 pb-2">
          Immagine Bottiglia & Stato
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">URL Immagine o Carica File</label>
            <input 
              v-model="photoUrlInput" 
              type="text" 
              class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none mb-2"
            />
            <input type="file" accept="image/*" @change="handleFileUpload" class="text-xs text-gray-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Stato Pubblicazione *</label>
            <select v-model="form.status" required class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none">
              <option value="PUBLISHED">Pubblicato (Visibile sul sito)</option>
              <option value="DRAFT">Bozza (Nascosto)</option>
            </select>
          </div>
        </div>
      </div>

      <div v-if="error" class="p-3 bg-red-50 text-red-800 rounded-xl text-xs font-semibold">
        {{ error }}
      </div>

      <!-- Submit -->
      <div class="pt-4 flex justify-end space-x-4">
        <NuxtLink to="/dashboard/prodotti" class="px-6 py-3 border border-gray-200 text-gray-700 font-semibold rounded-xl text-sm hover:bg-gray-50">
          Annulla
        </NuxtLink>
        <button 
          type="submit" 
          :disabled="submitting" 
          class="px-8 py-3 bg-wine-800 hover:bg-wine-900 text-white font-bold rounded-xl text-sm shadow-md transition-all disabled:opacity-50"
        >
          {{ submitting ? 'Salvataggio...' : 'Aggiorna Scheda Vino' }}
        </button>
      </div>

    </form>

  </div>
</template>

<script setup>
import { ArrowLeft, Shield, Plus, Trash2, Utensils } from 'lucide-vue-next'

const route = useRoute()
const productId = route.params.id

const { fetchWithAuth } = useApi()
const { isAdmin } = useAuth()

const submitting = ref(false)
const error = ref('')

const grapeVarietiesInput = ref('')
const foodPairingsInput = ref('')
const photoUrlInput = ref('')

const selectedPairingsList = ref([])

const { data: masterPairings } = await useAsyncData('master_pairings_product_edit', () =>
  fetchWithAuth('/pairings')
)

const isPairingSelected = (name) => {
  return selectedPairingsList.value.some(p => p.toLowerCase() === name.toLowerCase())
}

const togglePairingPreset = (name) => {
  const idx = selectedPairingsList.value.findIndex(p => p.toLowerCase() === name.toLowerCase())
  if (idx >= 0) {
    selectedPairingsList.value.splice(idx, 1)
  } else {
    selectedPairingsList.value.push(name)
  }
  syncFoodPairingsInputFromList()
}

const removeSelectedPairing = (idx) => {
  selectedPairingsList.value.splice(idx, 1)
  syncFoodPairingsInputFromList()
}

const addCustomPairingFromInput = () => {
  if (!foodPairingsInput.value.trim()) return
  const items = foodPairingsInput.value.split(',').map(s => s.trim()).filter(Boolean)
  for (const item of items) {
    if (!isPairingSelected(item)) {
      selectedPairingsList.value.push(item)
    }
  }
  foodPairingsInput.value = ''
  syncFoodPairingsInputFromList()
}

const syncFoodPairingsInputFromList = () => {
  foodPairingsInput.value = selectedPairingsList.value.join(', ')
}

const customAttributes = ref([])
const form = ref(null)

const { data: masterAttributes } = await useAsyncData('master_attributes_product_edit', () => 
  fetchWithAuth('/attributes')
)

const availableMasterAttributes = computed(() => {
  if (!masterAttributes.value) return []
  return masterAttributes.value.filter(m => {
    const name = m.name.toLowerCase().trim()
    return !name.includes('gradazione') && !name.includes('grado alcolico') && !name.includes('temperatura') && name !== 'denominazione'
  })
})

const { data: masterGrapes } = await useAsyncData('master_grapes_product_edit', () =>
  fetchWithAuth('/grapes')
)

const { data: producers } = await useAsyncData('admin_producers_edit_product', async () => {
  if (!isAdmin.value) return null
  return await fetchWithAuth('/producers')
})

const selectedGrapesList = ref([])

const selectGrapeForBlend = (grapeName) => {
  const existing = selectedGrapesList.value.find(g => g.name.toLowerCase() === grapeName.toLowerCase())
  if (!existing) {
    const defaultPct = selectedGrapesList.value.length === 0 ? '100%' : ''
    selectedGrapesList.value.push({ name: grapeName, percentage: defaultPct })
  }
  syncGrapesInputFromList()
}

const removeSelectedGrape = (idx) => {
  selectedGrapesList.value.splice(idx, 1)
  syncGrapesInputFromList()
}

const syncGrapesInputFromList = () => {
  if (!selectedGrapesList.value.length) return
  const parts = selectedGrapesList.value.map(g => {
    return g.percentage ? `${g.name} ${g.percentage}` : g.name
  })
  grapeVarietiesInput.value = parts.join(', ')
}

const { data: productData, pending } = await useAsyncData(`fetch_product_${productId}`, async () => {
  const prod = await fetchWithAuth(`/products/${productId}`)

  let alc = prod.alcohol_degrees
  let temp = prod.serving_temperature

  if ((alc === null || alc === undefined) && prod.custom_attributes) {
    const alcAttr = prod.custom_attributes.find(a => a.name && (a.name.toLowerCase().includes('gradazione') || a.name.toLowerCase().includes('grado alcolico')))
    if (alcAttr && alcAttr.value) {
      const match = alcAttr.value.match(/(\d+(?:\.\d+)?)/)
      if (match) alc = parseFloat(match[1])
    }
  }
  if (!temp && prod.custom_attributes) {
    const tempAttr = prod.custom_attributes.find(a => a.name && a.name.toLowerCase().includes('temperatura'))
    if (tempAttr && tempAttr.value) {
      temp = tempAttr.value
    }
  }

  form.value = {
    producer_id: prod.producer_id,
    name: prod.name,
    category: prod.category,
    denominazione: prod.denominazione,
    vintage_year: prod.vintage_year,
    is_riserva: prod.is_riserva || false,
    alcohol_degrees: alc,
    description: prod.description,
    tasting_notes: prod.tasting_notes || { visual: '', olfactory: '', taste: '' },
    serving_temperature: temp,
    indicative_price: prod.indicative_price,
    status: prod.status
  }
  grapeVarietiesInput.value = (prod.grape_varieties || []).join(', ')
  if (prod.grape_varieties && prod.grape_varieties.length) {
    selectedGrapesList.value = prod.grape_varieties.map(item => {
      const match = item.match(/^(.*?)\s*(\d+\s*%?)$/)
      if (match) {
        return { name: match[1].trim(), percentage: match[2].trim().endsWith('%') ? match[2].trim() : match[2].trim() + '%' }
      }
      return { name: item.trim(), percentage: '' }
    })
  }
  foodPairingsInput.value = (prod.food_pairings || []).join(', ')
  if (prod.food_pairings && prod.food_pairings.length) {
    selectedPairingsList.value = [...prod.food_pairings]
  }
  photoUrlInput.value = (prod.photos && prod.photos.length) ? prod.photos[0] : ''

  const filteredCustomAttrs = (prod.custom_attributes || []).filter(a => {
    if (!a.name) return false
    const n = a.name.toLowerCase().trim()
    return !n.includes('gradazione') && !n.includes('grado alcolico') && !n.includes('temperatura') && n !== 'denominazione'
  })

  customAttributes.value = filteredCustomAttrs.map(a => ({
    name: a.name,
    value: a.value,
    is_custom_name: false,
    custom_name_input: ''
  }))
  return prod
})

const handleAttributeNameChange = (attr) => {
  if (attr.name === '__NEW__') {
    attr.is_custom_name = true
    attr.custom_name_input = ''
    attr.name = ''
  } else {
    attr.is_custom_name = false
  }
}

const getAttributeHint = (attrName) => {
  if (!attrName || !masterAttributes.value) return ''
  const m = masterAttributes.value.find(item => item.name === attrName)
  return m?.unit_or_hint || ''
}

const getAttributeSuggestions = (attr) => {
  const name = attr.is_custom_name ? attr.custom_name_input : attr.name
  if (!name) return []
  
  if (name.toLowerCase().includes('gradazione')) {
    return ['10.0%', '10.5%', '11.0%', '11.5%', '12.0%', '12.5%', '13.0%', '13.5%', '14.0%', '14.5%', '15.0%', '15.5%', '16.0%']
  }
  if (name.toLowerCase().includes('temperatura')) {
    return ['6° - 8° C', '8° - 10° C', '10° - 12° C', '12° - 14° C', '14° - 16° C', '16° - 18° C', '18° - 20° C']
  }

  const m = masterAttributes.value?.find(item => item.name === name)
  return m?.suggested_values || []
}

const addCustomAttributeRow = () => {
  customAttributes.value.unshift({ name: '', value: '', is_custom_name: false, custom_name_input: '' })
}

const removeCustomAttributeRow = (index) => {
  customAttributes.value.splice(index, 1)
}

const toast = useToast()

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await fetchWithAuth('/uploads/image', {
      method: 'POST',
      body: formData
    })
    photoUrlInput.value = res.url
    toast.success('Immagine caricata con successo!')
  } catch (err) {
    toast.error('Errore durante l\'upload dell\'immagine.')
  }
}

const handleSubmit = async () => {
  submitting.value = true
  error.value = ''

  // Process inline custom attribute names
  for (const attr of customAttributes.value) {
    if (attr.is_custom_name && attr.custom_name_input.trim()) {
      const newName = attr.custom_name_input.trim()
      attr.name = newName
      try {
        await fetchWithAuth('/attributes', {
          method: 'POST',
          body: { name: newName, unit_or_hint: '', suggested_values: attr.value ? [attr.value] : [] }
        })
      } catch (e) {
        console.warn('Auto-create master attribute error:', e)
      }
    }
  }

  const grapes = grapeVarietiesInput.value ? grapeVarietiesInput.value.split(',').map(s => s.trim()).filter(Boolean) : []
  const pairings = foodPairingsInput.value ? foodPairingsInput.value.split(',').map(s => s.trim()).filter(Boolean) : []
  const photos = photoUrlInput.value ? [photoUrlInput.value] : []
  const validCustomAttrs = customAttributes.value
    .filter(a => a.name && a.value)
    .filter(a => {
      const n = a.name.toLowerCase().trim()
      return !n.includes('gradazione') && !n.includes('grado alcolico') && !n.includes('temperatura') && n !== 'denominazione'
    })
    .map(a => ({ name: a.name, value: a.value }))

  const cleanVintageYear = (form.value.vintage_year !== '' && form.value.vintage_year !== null && form.value.vintage_year !== undefined)
    ? (isNaN(Number(form.value.vintage_year)) ? null : Number(form.value.vintage_year))
    : null

  const cleanAlcoholDegrees = (form.value.alcohol_degrees !== '' && form.value.alcohol_degrees !== null && form.value.alcohol_degrees !== undefined)
    ? (isNaN(Number(form.value.alcohol_degrees)) ? null : Number(form.value.alcohol_degrees))
    : null

  try {
    await fetchWithAuth(`/products/${productId}`, {
      method: 'PUT',
      body: {
        ...form.value,
        vintage_year: cleanVintageYear,
        alcohol_degrees: cleanAlcoholDegrees,
        grape_varieties: grapes,
        food_pairings: pairings,
        photos: photos,
        custom_attributes: validCustomAttrs
      }
    })
    toast.success('Scheda vino aggiornata con successo!')
    navigateTo('/dashboard/prodotti')
  } catch (err) {
    error.value = 'Errore durante l\'aggiornamento della scheda vino.'
    toast.error('Errore durante l\'aggiornamento della scheda vino.')
  } finally {
    submitting.value = false
  }
}
</script>
