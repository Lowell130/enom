const API_BASE = 'http://localhost:8000/api/v1';

document.addEventListener('DOMContentLoaded', async () => {
  const producerSelect = document.getElementById('producer_id');
  const alertBox = document.getElementById('alert-box');
  const apiStatus = document.getElementById('api-status');
  const wineForm = document.getElementById('wine-form');
  const btnSubmit = document.getElementById('btn-submit');
  const btnRescrape = document.getElementById('btn-rescrape');
  const photoUrlInput = document.getElementById('photo_url');
  const imgPreview = document.getElementById('img-preview');

  // Fields
  const nameInput = document.getElementById('name');
  const categorySelect = document.getElementById('category');
  const denominazioneInput = document.getElementById('denominazione');
  const vintageYearInput = document.getElementById('vintage_year');
  const isRiservaCheckbox = document.getElementById('is_riserva');
  const alcoholDegreesInput = document.getElementById('alcohol_degrees');
  const servingTemperatureInput = document.getElementById('serving_temperature');
  const indicativePriceInput = document.getElementById('indicative_price');
  const grapeVarietiesInput = document.getElementById('grape_varieties');
  const descriptionInput = document.getElementById('description');
  const pdfInput = document.getElementById('technical_sheet_pdf');

  // Preset Buttons
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
    if (photoUrlInput.value) {
      imgPreview.src = photoUrlInput.value;
    }
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

  // 1. Fetch Producers & Grapes List from Backend API
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

      await loadMasterGrapes();
    } catch (err) {
      producerSelect.innerHTML = '<option value="" disabled selected>⚠️ Errore caricamento cantine (Avvia Backend)</option>';
      apiStatus.textContent = 'API Offline';
      apiStatus.style.background = '#fef2f2';
      apiStatus.style.color = '#991b1b';
      showAlert('Assicurati che il backend FastAPI sia attivo su http://localhost:8000', false);
    }
  }

  async function loadMasterGrapes() {
    try {
      const res = await fetch(`${API_BASE}/grapes`);
      if (res.ok) {
        const grapesData = await res.json();
        renderPopupGrapesQuickPills(grapesData);
      }
    } catch (e) {
      console.warn('Error loading grapes in popup:', e);
    }
  }

  function renderPopupGrapesPctPills() {
    const container = document.getElementById('popup-grapes-pct-pills');
    if (!container) return;
    container.innerHTML = '';
    
    const percentages = ['100%', '90%', '85%', '80%', '75%', '70%', '60%', '50%', '40%', '30%', '20%', '15%', '10%', '5%'];
    
    percentages.forEach(pct => {
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'val-pill';
      pill.style.fontWeight = '700';
      pill.style.borderColor = '#fecdd3';
      pill.style.color = '#881337';
      pill.style.background = '#fff1f2';
      pill.textContent = pct;
      
      pill.addEventListener('click', () => {
        applyPercentageToGrapeInput(pct, grapeVarietiesInput);
      });
      container.appendChild(pill);
    });
  }

  function applyPercentageToGrapeInput(pct, inputEl) {
    if (!inputEl) return;
    let val = inputEl.value ? inputEl.value.trim() : '';

    if (!val) {
      inputEl.value = pct;
    } else {
      const items = val.split(',').map(s => s.trim()).filter(Boolean);
      if (items.length > 0) {
        const lastIdx = items.length - 1;
        let lastItem = items[lastIdx];
        
        lastItem = lastItem.replace(/\s*\d{1,3}\s*%?/g, '').trim();
        
        if (lastItem) {
          items[lastIdx] = `${lastItem} ${pct}`;
        } else {
          items[lastIdx] = pct;
        }
        inputEl.value = items.join(', ');
      } else {
        inputEl.value = pct;
      }
    }
    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
    inputEl.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function renderPopupGrapesQuickPills(grapesData) {
    const container = document.getElementById('popup-grapes-quick-pills');
    if (!container || !grapesData) return;
    container.innerHTML = '';
    
    // Filter out combined or legacy multi-grape entries
    const singleGrapesOnly = [];
    grapesData.forEach(g => {
      if (!g || !g.name) return;
      const n = g.name.trim();
      if (n.includes('-') || n.toLowerCase().includes(' in purezza') || n.toLowerCase().includes(' passito') || n.toLowerCase().includes('uve bianche')) {
        return;
      }
      if (!singleGrapesOnly.some(x => x.name.toLowerCase() === n.toLowerCase())) {
        singleGrapesOnly.push(g);
      }
    });

    singleGrapesOnly.forEach(g => {
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'val-pill';
      pill.textContent = `+ ${g.name}`;
      pill.addEventListener('click', () => {
        const current = grapeVarietiesInput.value ? grapeVarietiesInput.value.trim() : '';
        if (!current) {
          grapeVarietiesInput.value = `${g.name} 100%`;
        } else {
          const items = current.split(',').map(s => s.trim()).filter(Boolean);
          const existingGrapeNames = items.map(item => item.replace(/\s*\d{1,3}\s*%/g, '').trim().toLowerCase());
          
          if (!existingGrapeNames.includes(g.name.toLowerCase())) {
            let totalPct = 0;
            items.forEach(item => {
              const match = item.match(/(\d{1,3})\s*%/);
              if (match) totalPct += parseInt(match[1], 10);
            });

            if (items.length === 1 && totalPct === 100) {
              const firstName = items[0].replace(/\s*\d{1,3}\s*%/g, '').trim();
              grapeVarietiesInput.value = `${firstName} 80%, ${g.name} 20%`;
            } else {
              const remPct = Math.max(0, 100 - totalPct);
              const pctStr = remPct > 0 ? ` ${remPct}%` : '';
              grapeVarietiesInput.value = `${current}, ${g.name}${pctStr}`;
            }
          }
        }
        inputEl.dispatchEvent(new Event('input', { bubbles: true }));
        inputEl.dispatchEvent(new Event('change', { bubbles: true }));
      });
      container.appendChild(pill);
    });

    renderPopupGrapesPctPills();
  }

  // 2. Scrape Current Browser Tab
  async function scrapeCurrentTab() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.id) return;

      chrome.tabs.sendMessage(tab.id, { action: 'SCRAPE_PAGE' }, (response) => {
        if (chrome.runtime.lastError || !response || !response.data) {
          // If content script not injected yet, execute it manually
          chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
          }, () => {
            chrome.tabs.sendMessage(tab.id, { action: 'SCRAPE_PAGE' }, (resp) => {
              if (resp && resp.data) fillFormWithScrapedData(resp.data);
            });
          });
          return;
        }
        fillFormWithScrapedData(response.data);
      });
    } catch (e) {
      console.warn('Scraping error:', e);
    }
  }

  function fillFormWithScrapedData(data) {
    if (data.name) nameInput.value = data.name;
    if (data.category) categorySelect.value = data.category;
    if (data.denominazione) denominazioneInput.value = data.denominazione;
    if (data.vintage_year) vintageYearInput.value = data.vintage_year;
    if (data.is_riserva !== undefined) isRiservaCheckbox.checked = data.is_riserva;
    if (data.alcohol_degrees) alcoholDegreesInput.value = data.alcohol_degrees;
    if (data.serving_temperature) servingTemperatureInput.value = data.serving_temperature;
    if (data.indicative_price) indicativePriceInput.value = data.indicative_price;
    if (data.description) descriptionInput.value = data.description;
    if (data.photo_url) {
      photoUrlInput.value = data.photo_url;
      imgPreview.src = data.photo_url;
    }
    if (data.technical_sheet_pdf) pdfInput.value = data.technical_sheet_pdf;
    if (data.grape_varieties && data.grape_varieties.length) {
      grapeVarietiesInput.value = data.grape_varieties.join(', ');
    }

    updatePresetButtons();

    // Auto select producer if title/URL matches
    const pageUrl = window.location.href ? window.location.href.toLowerCase() : "";
    const options = Array.from(producerSelect.options);
    for (const opt of options) {
      if (opt.text && pageUrl.includes(opt.text.toLowerCase().split(' ')[0])) {
        producerSelect.value = opt.value;
        break;
      }
    }
  }

  btnRescrape.addEventListener('click', () => {
    scrapeCurrentTab();
  });

  // 3. Submit Form to Backend API
  wineForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const producerId = producerSelect.value;
    if (!producerId) {
      showAlert('Seleziona una Cantina Produttrice prima di salvare!', false);
      return;
    }

    btnSubmit.disabled = true;
    btnSubmit.textContent = 'Salvando vino nel catalogo...';

    const grapes = grapeVarietiesInput.value ? grapeVarietiesInput.value.split(',').map(s => s.trim()).filter(Boolean) : [];
    const photos = photoUrlInput.value ? [photoUrlInput.value] : [];

    const payload = {
      producer_id: producerId,
      name: nameInput.value.trim(),
      category: categorySelect.value,
      denominazione: denominazioneInput.value.trim(),
      vintage_year: vintageYearInput.value ? parseInt(vintageYearInput.value, 10) : null,
      is_riserva: isRiservaCheckbox.checked,
      alcohol_degrees: alcoholDegreesInput.value ? parseFloat(alcoholDegreesInput.value) : null,
      serving_temperature: servingTemperatureInput.value.trim(),
      indicative_price: indicativePriceInput.value.trim(),
      description: descriptionInput.value.trim(),
      grape_varieties: grapes,
      photos: photos,
      technical_sheet_pdf: pdfInput.value.trim(),
      status: "PUBLISHED"
    };

    try {
      // First get Admin user token from auth API or login directly
      const authRes = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: 'admin@enotecamolise.it',
          password: 'AdminPass2026!'
        })
      });

      if (!authRes.ok) throw new Error('Errore autenticazione Admin');
      const authData = await authRes.json();
      const token = authData.access_token;

      // Submit Product
      const prodRes = await fetch(`${API_BASE}/products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!prodRes.ok) {
        const errData = await prodRes.json();
        throw new Error(errData.detail || 'Errore salvataggio prodotto');
      }

      const createdProduct = await prodRes.json();
      showAlert(`🎉 Vino "${createdProduct.name}" importato con successo in EnotecaMolise!`, true);
    } catch (err) {
      showAlert(`❌ ${err.message}`, false);
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.textContent = '🚀 IMPORTA VINO IN ENOTECAMOLISE';
    }
  });

  // Initial setup
  await loadProducers();
  await scrapeCurrentTab();
});
