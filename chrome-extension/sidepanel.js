const API_BASE = 'http://localhost:8000/api/v1';

let activePickButton = null;
let customAttrCount = 0;
let loadedProducerProducts = [];
let dbMasterAttributes = [];

// -------------------------------------------------------------
// UNIVERSAL TEXT & UNIT NORMALIZATION ENGINE
// -------------------------------------------------------------

function toTitleCase(text) {
  if (!text || typeof text !== 'string') return text;
  text = text.trim();

  // If text is a URL, do NOT perform title case
  if (text.startsWith('http://') || text.startsWith('https://') || text.startsWith('data:') || text.startsWith('blob:')) {
    return text;
  }

  // List of Italian prepositions / articles to keep lowercase if mid-sentence
  const smallWords = new Set(['del', 'della', 'dello', 'degli', 'delle', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'a', 'e', 'o', 'un', 'una', 'uno', 'nel', 'nella', 'nei', 'nelle']);

  // If text looks like a full paragraph (>10 words), use Sentence Case instead of Title Case
  const words = text.split(/\s+/);
  if (words.length > 10) {
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  return words.map((word, index) => {
    // Preserve pure numbers or numbers with dots/commas/units/slashes (e.g. 12.000, 0.75, 150mt, 16-18°, 50/60, q.li)
    if (/^[\d.,°%/:-]+[a-z.]*$/i.test(word) || /^q\.?li$/i.test(word)) {
      const lower = word.toLowerCase();
      if (lower === 'q.li' || lower === 'qli' || lower === 'q.li.') return 'q.li';
      if (lower === 'l' || lower === 'lt' || lower === 'liter') return 'L';
      if (lower === 'cl') return 'cl';
      if (lower === 'ml') return 'ml';
      if (lower === 'ha') return 'ha';
      if (lower === 'mt') return 'mt';
      return word;
    }

    if (/^(DOC|IGT|DOCG|DOP|IGP|PDF|I|II|III|IV|V|VI|VII|VIII|IX|X)$/i.test(word)) {
      return word.toUpperCase();
    }

    const lower = word.toLowerCase();
    if (index > 0 && smallWords.has(lower)) {
      return lower;
    }

    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }).join(' ');
}

function normalizeServingTemperature(val, isExplicitTempField = false) {
  if (!val || typeof val !== 'string') return val;
  val = val.trim();

  const isTemp = /(?:\d{1,2}\s*[-–—/]?\s*\d{1,2}\s*°|\d{1,2}\s*°|°|\bgradi\b)/i.test(val);

  // If it's NOT explicitly a temperature field AND doesn't contain temperature symbols (° or gradi), do NOT touch it!
  if (!isExplicitTempField && !isTemp) {
    return val;
  }

  // Range match e.g. 8-10, 8 - 10, 8-10°, 8-10°C, 16-18°C -> 8-10°
  const rangeMatch = val.match(/(\d{1,2})\s*[-–—]\s*(\d{1,2})/);
  if (rangeMatch) {
    return `${rangeMatch[1]}-${rangeMatch[2]}°`;
  }

  // Single number match e.g. 18, 18°C -> 18°
  const singleMatch = val.match(/(\d{1,2})/);
  if (singleMatch) {
    return `${singleMatch[1]}°`;
  }

  return val;
}

function normalizeUnits(val) {
  if (!val || typeof val !== 'string') return val;
  if (val.startsWith('http://') || val.startsWith('https://')) return val;

  // 1. Quintali / q.li (e.g. 50/60 quintali, 50 quintali, 50 qli, 50 q.li -> 50/60 q.li, 50 q.li)
  val = val.replace(/(\d+(?:[-–—/]\d+)?)\s*(?:quintali|q\.?li|qli)\b/gi, '$1 q.li');

  // 2. Altitude (e.g. 150m, 150 m, 150metri, 150 m.s.l.m. -> 150 mt)
  val = val.replace(/(\d+)\s*(?:m|mt|metri|m\.?s\.?l\.?m\.?)\b/gi, '$1 mt');

  // 3. Format (e.g. 75cl, 750ml, 0.75l -> 75 cl)
  val = val.replace(/\b750\s*ml\b/gi, '75 cl');
  val = val.replace(/\b75\s*cl\b/gi, '75 cl');
  val = val.replace(/\b0[.,]75\s*l\b/gi, '75 cl');
  val = val.replace(/\b1[.,]5\s*l\b/gi, '1.5 L (Magnum)');

  // 4. Alcohol (e.g. 14.5 % vol -> 14.5)
  val = val.replace(/(\d+(?:[.,]\d+)?)\s*%\s*(?:vol)?/gi, '$1');

  // 5. Serving temperature (Format: 8-10° / 16-18°) - ONLY if temperature symbols are present!
  if (/(?:\d{1,2}\s*[-–—/]?\s*\d{1,2}\s*°|\d{1,2}\s*°|°|\bgradi\b)/i.test(val)) {
    val = normalizeServingTemperature(val, false);
  }

  // 6. Price (ONLY when an explicit € or euro currency symbol is present!)
  val = val.replace(/(\d+(?:[.,]\d{2})?)\s*(?:€|euro|eur)\b/gi, '$1€');

  return val;
}

function smartSnapToMasterPreset(attrName, rawVal) {
  if (!rawVal || typeof rawVal !== 'string') return rawVal;
  if (rawVal.startsWith('http://') || rawVal.startsWith('https://')) return rawVal;

  let cleaned = normalizeUnits(rawVal.trim());
  cleaned = toTitleCase(cleaned);

  if (!attrName || !dbMasterAttributes || dbMasterAttributes.length === 0) {
    return cleaned;
  }

  const masterAttr = dbMasterAttributes.find(a => a.name.toLowerCase() === attrName.trim().toLowerCase());

  if (masterAttr && masterAttr.suggested_values && masterAttr.suggested_values.length > 0) {
    const exactMasterPreset = masterAttr.suggested_values.find(v => v.trim().toLowerCase() === rawVal.trim().toLowerCase() || v.trim().toLowerCase() === cleaned.toLowerCase());

    if (exactMasterPreset) {
      return exactMasterPreset;
    }
  }

  return cleaned;
}

function normalizeFieldValue(fieldId, rawValue, attrName = null) {
  if (!rawValue || typeof rawValue !== 'string') return rawValue;
  let val = rawValue.trim();

  // URLs MUST NEVER be title-cased or mutated!
  if (fieldId === 'photo_url' || fieldId === 'technical_sheet_pdf' || val.startsWith('http://') || val.startsWith('https://') || val.startsWith('data:')) {
    return val;
  }

  switch (fieldId) {
    case 'name':
      return toTitleCase(val);

    case 'denominazione':
      const upper = val.toUpperCase().replace(/\./g, '');
      if (upper.includes('DOCG')) return 'DOCG';
      if (upper.includes('DOC')) return 'Tintilia del Molise DOC' === val || 'Biferno DOC' === val ? val : (val.toLowerCase().includes('tintilia') ? 'Tintilia del Molise DOC' : (val.toLowerCase().includes('biferno') ? 'Biferno DOC' : 'DOC'));
      if (upper.includes('IGT')) return 'IGT';
      return toTitleCase(val);

    case 'grape_varieties':
    case 'food_pairings':
      return val.split(',').map(g => {
        let trimmed = g.trim();
        trimmed = trimmed.replace(/(\d+)\s*%/g, '$1%');
        return toTitleCase(trimmed);
      }).join(', ');

    case 'serving_temperature':
      return normalizeServingTemperature(val, true);

    case 'indicative_price':
      val = val.replace(/,/g, '.');
      const numMatch = val.match(/(\d+(?:\.\d+)?)/);
      return numMatch ? `${parseFloat(numMatch[1]).toFixed(2)}€` : val;

    case 'description':
      val = val.replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim();
      return val ? val.charAt(0).toUpperCase() + val.slice(1) : '';

    case 'tasting_visual':
    case 'tasting_olfactory':
    case 'tasting_taste':
      return toTitleCase(val);

    default:
      if (fieldId && fieldId.startsWith('custom-name-')) {
        return toTitleCase(val);
      }
      if (fieldId && fieldId.startsWith('custom-val-')) {
        return smartSnapToMasterPreset(attrName || '', val);
      }
      return toTitleCase(val);
  }
}

// -------------------------------------------------------------
// MAIN EXTENSION SIDE PANEL CONTROLLER
// -------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
  const producerSelect = document.getElementById('producer_id');
  const productTargetSelect = document.getElementById('product_target_select');
  const alertBox = document.getElementById('alert-box');
  const apiStatus = document.getElementById('api-status');
  const wineForm = document.getElementById('wine-form');
  const btnSubmit = document.getElementById('btn-submit');
  const btnAutoScrape = document.getElementById('btn-auto-scrape');
  const btnAddAttr = document.getElementById('btn-add-attr');
  const customAttrsContainer = document.getElementById('custom-attributes-container');
  const quickAttrsContainer = document.getElementById('quick-attrs-container');
  const masterAttrsDatalist = document.getElementById('master-attributes-datalist');

  // Input Fields
  const nameInput = document.getElementById('name');
  const categorySelect = document.getElementById('category');
  const denominazioneInput = document.getElementById('denominazione');
  const vintageYearInput = document.getElementById('vintage_year');
  const isRiservaCheckbox = document.getElementById('is_riserva');
  const alcoholDegreesInput = document.getElementById('alcohol_degrees');
  const servingTemperatureInput = document.getElementById('serving_temperature');
  const indicativePriceInput = document.getElementById('indicative_price');
  const grapeVarietiesInput = document.getElementById('grape_varieties');
  const foodPairingsInput = document.getElementById('food_pairings');
  const descriptionInput = document.getElementById('description');
  const tastingVisualInput = document.getElementById('tasting_visual');
  const tastingOlfactoryInput = document.getElementById('tasting_olfactory');
  const tastingTasteInput = document.getElementById('tasting_taste');
  const photoUrlInput = document.getElementById('photo_url');
  const imgPreview = document.getElementById('img-preview');
  const pdfInput = document.getElementById('technical_sheet_pdf');

  // Presets
  const presetAnnata = document.getElementById('preset-annata');
  const presetRiserva = document.getElementById('preset-riserva');
  const presetSoloRiserva = document.getElementById('preset-solo-riserva');
  const presetSa = document.getElementById('preset-sa');

  function updatePresetButtons() {
    const isRis = isRiservaCheckbox.checked;
    const year = vintageYearInput.value;

    presetAnnata.classList.toggle('active', !isRis && year);
    presetRiserva.classList.toggle('active', isRis && year);
    presetSoloRiserva.classList.toggle('active', isRis && !year);
    presetSa.classList.toggle('active', !isRis && !year);
  }

  presetAnnata.addEventListener('click', () => {
    isRiservaCheckbox.checked = false;
    if (!vintageYearInput.value) vintageYearInput.value = 2022;
    updatePresetButtons();
  });

  presetRiserva.addEventListener('click', () => {
    isRiservaCheckbox.checked = true;
    if (!vintageYearInput.value) vintageYearInput.value = 2022;
    updatePresetButtons();
  });

  presetSoloRiserva.addEventListener('click', () => {
    isRiservaCheckbox.checked = true;
    vintageYearInput.value = '';
    updatePresetButtons();
  });

  presetSa.addEventListener('click', () => {
    isRiservaCheckbox.checked = false;
    vintageYearInput.value = '';
    updatePresetButtons();
  });

  vintageYearInput.addEventListener('input', updatePresetButtons);
  isRiservaCheckbox.addEventListener('change', updatePresetButtons);

  photoUrlInput.addEventListener('input', () => {
    if (photoUrlInput.value) imgPreview.src = photoUrlInput.value;
  });

  function showAlert(message, isSuccess = true, type = null) {
    const toastType = type || (isSuccess ? 'success' : 'error');
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toast-container';
      toastContainer.className = 'toast-container';
      document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast-card toast-${toastType}`;
    
    const icon = document.createElement('span');
    icon.style.fontSize = '14px';
    icon.style.fontWeight = 'bold';
    if (toastType === 'success') icon.textContent = '✓';
    else if (toastType === 'error') icon.textContent = '✕';
    else icon.textContent = 'ℹ';
    
    const text = document.createElement('span');
    text.style.flex = '1';
    text.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(text);
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 5000);
  }

  function clearFormFields() {
    nameInput.value = '';
    categorySelect.value = 'VINO_ROSSO';
    denominazioneInput.value = 'DOC';
    vintageYearInput.value = '';
    isRiservaCheckbox.checked = false;
    alcoholDegreesInput.value = '';
    servingTemperatureInput.value = '16-18°';
    indicativePriceInput.value = '';
    grapeVarietiesInput.value = '';
    if (foodPairingsInput) foodPairingsInput.value = '';
    descriptionInput.value = '';
    tastingVisualInput.value = '';
    tastingOlfactoryInput.value = '';
    tastingTasteInput.value = '';
    photoUrlInput.value = '';
    imgPreview.src = 'https://images.unsplash.com/photo-1586370434639-0fe43b2d32e6?auto=format&fit=crop&w=100&q=80';
    pdfInput.value = '';
    customAttrsContainer.innerHTML = '';
    updatePresetButtons();
  }

  function populateFormWithProduct(prod) {
    clearFormFields();
    if (!prod) return;

    if (prod.name) nameInput.value = normalizeFieldValue('name', prod.name);
    if (prod.category) categorySelect.value = prod.category;
    if (prod.denominazione) denominazioneInput.value = normalizeFieldValue('denominazione', prod.denominazione);
    if (prod.vintage_year) vintageYearInput.value = prod.vintage_year;
    if (prod.is_riserva !== undefined) isRiservaCheckbox.checked = prod.is_riserva;
    if (prod.alcohol_degrees) alcoholDegreesInput.value = prod.alcohol_degrees;
    if (prod.serving_temperature) servingTemperatureInput.value = normalizeFieldValue('serving_temperature', prod.serving_temperature);
    if (prod.indicative_price) indicativePriceInput.value = normalizeFieldValue('indicative_price', prod.indicative_price);
    if (prod.grape_varieties) grapeVarietiesInput.value = normalizeFieldValue('grape_varieties', Array.isArray(prod.grape_varieties) ? prod.grape_varieties.join(', ') : prod.grape_varieties);
    if (prod.food_pairings && foodPairingsInput) foodPairingsInput.value = normalizeFieldValue('food_pairings', Array.isArray(prod.food_pairings) ? prod.food_pairings.join(', ') : prod.food_pairings);
    if (prod.description) descriptionInput.value = normalizeFieldValue('description', prod.description);
    
    if (prod.tasting_notes) {
      if (prod.tasting_notes.visual) tastingVisualInput.value = normalizeFieldValue('tasting_visual', prod.tasting_notes.visual);
      if (prod.tasting_notes.olfactory) tastingOlfactoryInput.value = normalizeFieldValue('tasting_olfactory', prod.tasting_notes.olfactory);
      if (prod.tasting_notes.taste) tastingTasteInput.value = normalizeFieldValue('tasting_taste', prod.tasting_notes.taste);
    }

    if (prod.photos && prod.photos.length > 0) {
      photoUrlInput.value = prod.photos[0];
      imgPreview.src = prod.photos[0];
    }

    if (prod.technical_sheet_pdf) pdfInput.value = prod.technical_sheet_pdf;

    if (prod.custom_attributes && Array.isArray(prod.custom_attributes)) {
      prod.custom_attributes.forEach(attr => {
        addCustomAttributeRow(attr.name, attr.value, false);
      });
    }

    updatePresetButtons();
  }

  // 1. Fetch Master Attributes from Database
  async function loadMasterAttributes() {
    try {
      const res = await fetch(`${API_BASE}/attributes`);
      if (!res.ok) return;
      const attrs = await res.json();

      dbMasterAttributes = attrs.filter(a => 
        a.name !== 'Gradazione Alcolica' && 
        a.name !== 'Temperatura di Servizio'
      );

      // Populate Datalist
      masterAttrsDatalist.innerHTML = '';
      dbMasterAttributes.forEach(attr => {
        const opt = document.createElement('option');
        opt.value = attr.name;
        masterAttrsDatalist.appendChild(opt);
      });

      // Populate Quick Add Buttons for ALL DB Attributes
      quickAttrsContainer.innerHTML = '';
      dbMasterAttributes.forEach(attr => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-quick-attr';
        btn.textContent = `+ ${attr.name}`;
        btn.addEventListener('click', () => {
          addCustomAttributeRow(attr.name, '');
        });
        quickAttrsContainer.appendChild(btn);
      });

      // Populate Grapes Datalist
      try {
        const grapesRes = await fetch(`${API_BASE}/grapes`);
        if (grapesRes.ok) {
          const grapesData = await grapesRes.json();
          const grapesDatalist = document.getElementById('master-grapes-datalist');
          if (grapesDatalist) {
            grapesDatalist.innerHTML = '';
            grapesData.forEach(g => {
              const opt = document.createElement('option');
              opt.value = g.name;
              grapesDatalist.appendChild(opt);
            });
          }
        }
      } catch (e) {
        console.warn('Error loading grapes datalist:', e);
      }

      // Populate Pairings Datalist
      try {
        const pairingsRes = await fetch(`${API_BASE}/pairings`);
        if (pairingsRes.ok) {
          const pairingsData = await pairingsRes.json();
          const pairingsDatalist = document.getElementById('master-pairings-datalist');
          if (pairingsDatalist) {
            pairingsDatalist.innerHTML = '';
            pairingsData.forEach(p => {
              const opt = document.createElement('option');
              opt.value = p.name;
              pairingsDatalist.appendChild(opt);
            });
          }
        }
      } catch (e) {
        console.warn('Error loading pairings datalist:', e);
      }

    } catch (err) {
      console.error('Error fetching master attributes:', err);
    }
  }

  // 2. Fetch Producers & Producer Wines
  async function loadProducers() {
    try {
      const res = await fetch(`${API_BASE}/producers`);
      if (!res.ok) throw new Error('API non raggiungibile');
      const producers = await res.json();
      
      producerSelect.innerHTML = '<option value="" disabled selected>-- Seleziona Cantina Produttrice --</option>';
      producers.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.company_name} (${p.address?.city || 'Molise'})`;
        producerSelect.appendChild(opt);
      });
      apiStatus.textContent = 'API Collegata';
      apiStatus.style.background = '#ecfdf5';
      apiStatus.style.color = '#047857';

      // Load DB Master Attributes
      await loadMasterAttributes();
    } catch (err) {
      producerSelect.innerHTML = '<option value="" disabled selected>⚠️ API Offline (Avvia Backend)</option>';
      apiStatus.textContent = 'API Offline';
      apiStatus.style.background = '#fef2f2';
      apiStatus.style.color = '#991b1b';
      showAlert('Assicurati che il backend FastAPI sia in esecuzione su http://localhost:8000', false);
    }
  }

  async function loadProducerProducts(producerId, selectedProductIdToKeep = 'NEW') {
    productTargetSelect.innerHTML = '<option value="NEW">+ ✨ Crea un Nuovo Vino</option>';
    if (!producerId) return;

    try {
      const res = await fetch(`${API_BASE}/products?producer_id=${producerId}&status=ALL`);
      if (!res.ok) return;
      loadedProducerProducts = await res.json();

      loadedProducerProducts.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        const risTag = p.is_riserva ? ' Riserva' : '';
        const yrTag = p.vintage_year ? ` ${p.vintage_year}` : '';
        opt.textContent = `✏️ Modifica: ${p.name}${yrTag}${risTag}`;
        productTargetSelect.appendChild(opt);
      });

      productTargetSelect.value = selectedProductIdToKeep;
      if (selectedProductIdToKeep !== 'NEW') {
        const targetProd = loadedProducerProducts.find(p => p.id === selectedProductIdToKeep);
        if (targetProd) populateFormWithProduct(targetProd);
      }
    } catch (err) {
      console.error('Error loading producer products:', err);
    }
  }

  producerSelect.addEventListener('change', () => {
    const pId = producerSelect.value;
    loadProducerProducts(pId, 'NEW');
    clearFormFields();
    btnSubmit.textContent = '🚀 IMPORTA NUOVO VINO IN ENOTECAMOLISE';
  });

  productTargetSelect.addEventListener('change', () => {
    const targetVal = productTargetSelect.value;
    if (targetVal === 'NEW') {
      clearFormFields();
      btnSubmit.textContent = '🚀 IMPORTA NUOVO VINO IN ENOTECAMOLISE';
    } else {
      const selectedProd = loadedProducerProducts.find(p => p.id === targetVal);
      if (selectedProd) {
        populateFormWithProduct(selectedProd);
        btnSubmit.textContent = `💾 AGGIORNA VINO ESISTENTE IN ENOTECAMOLISE`;
        showAlert(`Caricata la scheda di "${selectedProd.name}". Puoi ora estrarre o modificare le sue informazioni con i tasti 🎯`, true);
      }
    }
  });

  apiStatus.addEventListener('click', loadProducers);

  // 3. Setup Point & Click Pickers
  function attachPickEvent(buttonEl) {
    buttonEl.addEventListener('click', async () => {
      const fieldId = buttonEl.getAttribute('data-field');
      const fieldType = buttonEl.getAttribute('data-type') || 'text';

      if (activePickButton && activePickButton !== buttonEl) {
        activePickButton.classList.remove('active');
        activePickButton.textContent = activePickButton.getAttribute('data-orig-text') || '🎯 Pick';
      }

      const isDeactivating = buttonEl.classList.contains('active');
      if (isDeactivating) {
        buttonEl.classList.remove('active');
        buttonEl.textContent = buttonEl.getAttribute('data-orig-text') || '🎯 Pick';
        activePickButton = null;
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.id) chrome.tabs.sendMessage(tab.id, { action: 'STOP_PICKER' });
        return;
      }

      buttonEl.setAttribute('data-orig-text', buttonEl.textContent);
      buttonEl.classList.add('active');
      buttonEl.textContent = '🎯 Clicca nel sito...';
      activePickButton = buttonEl;

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.id) return;

      chrome.tabs.sendMessage(tab.id, { action: 'START_PICKER', fieldId, fieldType }, (response) => {
        if (chrome.runtime.lastError) {
          chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
          }, () => {
            chrome.tabs.sendMessage(tab.id, { action: 'START_PICKER', fieldId, fieldType });
          });
        }
      });
    });
  }

  document.querySelectorAll('.btn-pick').forEach(btn => attachPickEvent(btn));

  // Auto-normalize on focusout for text/textarea input fields (EXCLUDING URLs)
  wineForm.addEventListener('focusout', (e) => {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
      const input = e.target;
      if (input.type === 'number' || input.type === 'checkbox' || !input.value) return;
      if (input.id === 'photo_url' || input.id === 'technical_sheet_pdf') return;

      if (input.id && input.id.startsWith('custom-val-')) {
        const row = input.closest('.attr-row');
        const attrName = row ? row.querySelector('.attr-name')?.value : '';
        input.value = normalizeFieldValue(input.id, input.value, attrName);
      } else if (input.id && input.id.startsWith('custom-name-')) {
        input.value = normalizeFieldValue(input.id, input.value);
      } else if (input.id) {
        input.value = normalizeFieldValue(input.id, input.value);
      }
    }
  });

  // Listen for value picked from webpage
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === 'PICKER_CANCELLED') {
      if (activePickButton) {
        activePickButton.classList.remove('active');
        activePickButton.textContent = activePickButton.getAttribute('data-orig-text') || '🎯 Pick';
        activePickButton = null;
      }
      return;
    }

    if (message.action === 'ELEMENT_PICKED') {
      const { fieldId, fieldType, value } = message;
      if (activePickButton) {
        activePickButton.classList.remove('active');
        activePickButton.textContent = activePickButton.getAttribute('data-orig-text') || '🎯 Pick';
        activePickButton = null;
      }

      if (!value) return;

      const input = document.getElementById(fieldId);
      if (input) {
        if (input.type === 'number') {
          const numMatch = value.match(/(\d+(?:[.,]\d+)?)/);
          if (numMatch) input.value = numMatch[1].replace(',', '.');
        } else if (input.type === 'checkbox') {
          input.checked = value.toLowerCase().includes('riserva');
        } else {
          let processedVal = value;
          if (fieldId === 'photo_url' || fieldId === 'technical_sheet_pdf') {
            processedVal = value;
          } else if (fieldId.startsWith('custom-val-')) {
            const row = input.closest('.attr-row');
            const attrName = row ? row.querySelector('.attr-name')?.value : '';
            processedVal = normalizeFieldValue(fieldId, value, attrName);
          } else {
            processedVal = normalizeFieldValue(fieldId, value);
          }
          input.value = processedVal;
        }

        if (fieldId === 'photo_url') {
          imgPreview.src = value;
        }
      }

      updatePresetButtons();
    }
  });

  // 4. Custom Attributes Management
  function addCustomAttributeRow(nameVal = '', valueVal = '', prepend = true) {
    customAttrCount++;
    const nameInputId = `custom-name-${customAttrCount}`;
    const valInputId = `custom-val-${customAttrCount}`;
    const valDatalistId = `custom-val-datalist-${customAttrCount}`;
    const valSuggestionsId = `custom-val-suggestions-${customAttrCount}`;

    const normalizedName = normalizeFieldValue(nameInputId, nameVal);
    const normalizedVal = normalizeFieldValue(valInputId, valueVal, normalizedName);

    const row = document.createElement('div');
    row.className = 'attr-row';
    row.innerHTML = `
      <div class="attr-row-fields">
        <input type="text" id="${nameInputId}" list="master-attributes-datalist" class="attr-name" placeholder="Nome Caratteristica (es. Affinamento)" value="${normalizedName}" style="flex: 1; font-size: 11px; padding: 5px;" />
        <button type="button" class="btn-pick btn-pick-custom" data-field="${nameInputId}" title="Clicca nel sito per inserire il Nome Caratteristica">🎯</button>
      </div>
      <div class="attr-row-fields">
        <input type="text" id="${valInputId}" list="${valDatalistId}" class="attr-value" placeholder="Valore (es. 12 Mesi in Barrique)" value="${normalizedVal}" style="flex: 1; font-size: 11px; padding: 5px;" />
        <button type="button" class="btn-pick btn-pick-custom" data-field="${valInputId}" title="Clicca nel sito per inserire il Valore">🎯</button>
        <button type="button" class="btn-remove-attr" title="Rimuovi riga">✕</button>
      </div>
      <datalist id="${valDatalistId}"></datalist>
      <div class="val-suggestions" id="${valSuggestionsId}"></div>
    `;

    if (prepend) {
      customAttrsContainer.prepend(row);
    } else {
      customAttrsContainer.appendChild(row);
    }
    row.querySelectorAll('.btn-pick-custom').forEach(btn => attachPickEvent(btn));

    const nameInput = row.querySelector(`#${nameInputId}`);
    const valInput = row.querySelector(`#${valInputId}`);
    const valDatalist = row.querySelector(`#${valDatalistId}`);
    const valSuggestionsContainer = row.querySelector(`#${valSuggestionsId}`);

    const syncValueSuggestions = () => {
      const currentName = nameInput.value.trim();
      valDatalist.innerHTML = '';
      valSuggestionsContainer.innerHTML = '';

      if (!currentName || !dbMasterAttributes) return;

      const masterAttr = dbMasterAttributes.find(a => a.name.toLowerCase() === currentName.toLowerCase());
      if (masterAttr && masterAttr.suggested_values && masterAttr.suggested_values.length > 0) {
        masterAttr.suggested_values.forEach(val => {
          // Populate datalist option
          const opt = document.createElement('option');
          opt.value = val;
          valDatalist.appendChild(opt);

          // Populate quick pill button
          const pill = document.createElement('button');
          pill.type = 'button';
          pill.className = 'val-pill';
          pill.textContent = val;
          pill.addEventListener('click', () => {
            valInput.value = val;
            valInput.dispatchEvent(new Event('input', { bubbles: true }));
            valInput.dispatchEvent(new Event('change', { bubbles: true }));
          });
          valSuggestionsContainer.appendChild(pill);
        });
      }
    };

    nameInput.addEventListener('input', syncValueSuggestions);
    nameInput.addEventListener('change', syncValueSuggestions);
    nameInput.addEventListener('focus', syncValueSuggestions);

    // Initial sync
    syncValueSuggestions();

    row.querySelector('.btn-remove-attr').addEventListener('click', () => {
      row.remove();
    });
  }

  btnAddAttr.addEventListener('click', () => {
    addCustomAttributeRow();
  });

  // 5. Auto Scrape
  btnAutoScrape.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) return;

    btnAutoScrape.textContent = '⏳ Estrazione...';
    chrome.tabs.sendMessage(tab.id, { action: 'SCRAPE_PAGE' }, (response) => {
      btnAutoScrape.textContent = '⚡ Auto-Estrai Tutto';
      if (response && response.data) {
        const d = response.data;
        if (d.name) nameInput.value = normalizeFieldValue('name', d.name);
        if (d.category) categorySelect.value = d.category;
        if (d.denominazione) denominazioneInput.value = normalizeFieldValue('denominazione', d.denominazione);
        if (d.vintage_year) vintageYearInput.value = d.vintage_year;
        if (d.is_riserva !== undefined) isRiservaCheckbox.checked = d.is_riserva;
        if (d.alcohol_degrees) alcoholDegreesInput.value = d.alcohol_degrees;
        if (d.description) descriptionInput.value = normalizeFieldValue('description', d.description);
        if (d.photo_url) { photoUrlInput.value = d.photo_url; imgPreview.src = d.photo_url; }
        if (d.technical_sheet_pdf) pdfInput.value = d.technical_sheet_pdf;
        if (d.grape_varieties) grapeVarietiesInput.value = normalizeFieldValue('grape_varieties', Array.isArray(d.grape_varieties) ? d.grape_varieties.join(', ') : d.grape_varieties);
        if (d.food_pairings && foodPairingsInput) foodPairingsInput.value = normalizeFieldValue('food_pairings', Array.isArray(d.food_pairings) ? d.food_pairings.join(', ') : d.food_pairings);
        updatePresetButtons();
        showAlert('Dati estratti e normalizzati con successo! Puoi rifinire qualsiasi campo cliccando sui tasti 🎯', true);
      }
    });
  });

  // 6. Submit Form to Backend API (Create or Update)
  wineForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const producerId = producerSelect.value;
    if (!producerId) {
      showAlert('Seleziona prima la Cantina Produttrice nel box in alto!', false);
      return;
    }

    const targetMode = productTargetSelect.value; // 'NEW' or product_id
    const isUpdate = targetMode !== 'NEW';

    btnSubmit.disabled = true;
    btnSubmit.textContent = isUpdate ? 'Aggiornamento vino in corso...' : 'Creazione vino in corso...';

    const grapesStr = normalizeFieldValue('grape_varieties', grapeVarietiesInput.value);
    const grapes = grapesStr ? grapesStr.split(',').map(s => s.trim()).filter(Boolean) : [];

    const pairingsStr = foodPairingsInput ? normalizeFieldValue('food_pairings', foodPairingsInput.value) : '';
    const pairings = pairingsStr ? pairingsStr.split(',').map(s => s.trim()).filter(Boolean) : [];

    const photos = photoUrlInput.value ? [photoUrlInput.value] : [];

    // Collect & normalize custom attributes
    const customAttrs = [];
    document.querySelectorAll('.attr-row').forEach(row => {
      let name = row.querySelector('.attr-name').value.trim();
      let val = row.querySelector('.attr-value').value.trim();
      if (name && val) {
        name = normalizeFieldValue('custom-name-field', name);
        val = smartSnapToMasterPreset(name, val);
        customAttrs.push({ name, value: val });
      }
    });

    const tastingNotes = {
      visual: normalizeFieldValue('tasting_visual', tastingVisualInput.value),
      olfactory: normalizeFieldValue('tasting_olfactory', tastingOlfactoryInput.value),
      taste: normalizeFieldValue('tasting_taste', tastingTasteInput.value)
    };

    const payload = {
      producer_id: producerId,
      name: normalizeFieldValue('name', nameInput.value),
      category: categorySelect.value,
      denominazione: normalizeFieldValue('denominazione', denominazioneInput.value),
      vintage_year: vintageYearInput.value ? parseInt(vintageYearInput.value, 10) : null,
      is_riserva: isRiservaCheckbox.checked,
      alcohol_degrees: alcoholDegreesInput.value ? parseFloat(alcoholDegreesInput.value) : null,
      serving_temperature: normalizeServingTemperature(servingTemperatureInput.value, true),
      indicative_price: normalizeFieldValue('indicative_price', indicativePriceInput.value),
      description: normalizeFieldValue('description', descriptionInput.value),
      tasting_notes: tastingNotes,
      grape_varieties: grapes,
      food_pairings: pairings,
      photos: photos,
      technical_sheet_pdf: pdfInput.value.trim(),
      custom_attributes: customAttrs,
      status: "PUBLISHED"
    };

    try {
      // Authenticate with JSON body
      const authRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'admin@enotecamolise.it',
          password: 'AdminPass2026!'
        })
      });

      if (!authRes.ok) {
        const errJson = await authRes.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Autenticazione Admin fallita');
      }

      const authData = await authRes.json();
      const token = authData.access_token;

      let prodRes;
      if (isUpdate) {
        // PUT /products/{targetMode}
        prodRes = await fetch(`${API_BASE}/products/${targetMode}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
      } else {
        // POST /products
        prodRes = await fetch(`${API_BASE}/products`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
      }

      if (!prodRes.ok) {
        const errData = await prodRes.json().catch(() => ({}));
        throw new Error(errData.detail || 'Errore durante la trasmissione del vino');
      }

      const savedProduct = await prodRes.json();
      const actionLabel = isUpdate ? 'aggiornato' : 'importato';
      showAlert(`🎉 Vino "${savedProduct.name}" ${actionLabel} con successo in EnotecaMolise!`, true);

      // Refresh master attributes & products list for this producer and select the saved product
      await loadMasterAttributes();
      await loadProducerProducts(producerId, savedProduct.id);
      populateFormWithProduct(savedProduct);
      btnSubmit.textContent = '💾 AGGIORNA VINO ESISTENTE IN ENOTECAMOLISE';

    } catch (err) {
      showAlert(`❌ ${err.message}`, false);
    } finally {
      btnSubmit.disabled = false;
    }
  });

  // Initial Load
  await loadProducers();
});
