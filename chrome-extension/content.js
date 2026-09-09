// EnotecaMolise Smart Content Scraper & Interactive Point & Click Picker V2

let isPickerActive = false;
let currentTargetField = null;
let currentTargetType = 'text'; // 'text', 'image', 'pdf'
let hoverOverlay = null;

function createHighlightOverlay() {
  if (!hoverOverlay) {
    hoverOverlay = document.createElement('div');
    hoverOverlay.id = 'enoteca-picker-highlight';
    hoverOverlay.style.position = 'absolute';
    hoverOverlay.style.pointerEvents = 'none';
    hoverOverlay.style.zIndex = '2147483647';
    hoverOverlay.style.border = '2px dashed #e11d48';
    hoverOverlay.style.backgroundColor = 'rgba(225, 29, 72, 0.15)';
    hoverOverlay.style.borderRadius = '6px';
    hoverOverlay.style.transition = 'all 0.05s ease-out';
    hoverOverlay.style.display = 'none';
    hoverOverlay.style.boxShadow = '0 0 10px rgba(225, 29, 72, 0.4)';

    // Label tag
    const label = document.createElement('span');
    label.id = 'enoteca-picker-label';
    label.style.position = 'absolute';
    label.style.top = '-26px';
    label.style.left = '0';
    label.style.background = '#e11d48';
    label.style.color = '#ffffff';
    label.style.fontSize = '11px';
    label.style.fontWeight = 'bold';
    label.style.padding = '3px 8px';
    label.style.borderRadius = '4px';
    label.style.fontFamily = 'sans-serif';
    label.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    label.style.whiteSpace = 'nowrap';
    label.textContent = '🎯 Clicca per selezionare';
    hoverOverlay.appendChild(label);

    document.body.appendChild(hoverOverlay);
  }
}

function startPickerMode(fieldId, fieldType = 'text') {
  isPickerActive = true;
  currentTargetField = fieldId;
  currentTargetType = fieldType;
  createHighlightOverlay();

  document.addEventListener('mouseover', handleMouseOver, true);
  document.addEventListener('click', handleElementClick, true);
  document.addEventListener('keydown', handleKeyDown, true);
  document.body.style.cursor = 'crosshair';
}

function stopPickerMode() {
  isPickerActive = false;
  currentTargetField = null;
  document.removeEventListener('mouseover', handleMouseOver, true);
  document.removeEventListener('click', handleElementClick, true);
  document.removeEventListener('keydown', handleKeyDown, true);
  document.body.style.cursor = 'default';
  if (hoverOverlay) {
    hoverOverlay.style.display = 'none';
  }
}

function handleKeyDown(e) {
  if (e.key === 'Escape' && isPickerActive) {
    stopPickerMode();
    chrome.runtime.sendMessage({ action: 'PICKER_CANCELLED' });
  }
}

function handleMouseOver(e) {
  if (!isPickerActive || !e.target || e.target === hoverOverlay || hoverOverlay.contains(e.target)) return;

  const rect = e.target.getBoundingClientRect();
  hoverOverlay.style.top = `${rect.top + window.scrollY}px`;
  hoverOverlay.style.left = `${rect.left + window.scrollX}px`;
  hoverOverlay.style.width = `${rect.width}px`;
  hoverOverlay.style.height = `${rect.height}px`;
  hoverOverlay.style.display = 'block';

  const label = document.getElementById('enoteca-picker-label');
  if (label) {
    label.textContent = `🎯 Clicca per inserire in "${currentTargetField}" (Premere ESC per annullare)`;
  }
}

function extractImageSrc(el) {
  if (!el) return "";
  
  // Direct img attributes
  let src = el.src || el.currentSrc || el.getAttribute('src') || el.getAttribute('data-src') || el.getAttribute('data-lazy-src') || "";
  
  if (!src && el.getAttribute('srcset')) {
    const parts = el.getAttribute('srcset').split(',');
    if (parts.length > 0) {
      src = parts[0].trim().split(' ')[0];
    }
  }

  // Check background image
  if (!src) {
    const computedStyle = window.getComputedStyle(el);
    const bgImg = computedStyle.backgroundImage || el.style.backgroundImage;
    if (bgImg && bgImg !== 'none') {
      const match = bgImg.match(/url\(['"]?(.*?)['"]?\)/i);
      if (match) src = match[1];
    }
  }

  // Check children or parent elements
  if (!src) {
    const childImg = el.querySelector('img, picture source, [style*="background-image"]');
    if (childImg) return extractImageSrc(childImg);

    const parentImgContainer = el.closest('picture, figure, a, div');
    if (parentImgContainer && parentImgContainer !== el) {
      const parentImg = parentImgContainer.querySelector('img');
      if (parentImg) return extractImageSrc(parentImg);
    }
  }

  if (src && !src.startsWith('http') && !src.startsWith('data:')) {
    try {
      src = new URL(src, window.location.href).href;
    } catch (err) {}
  }

  return src;
}

function handleElementClick(e) {
  if (!isPickerActive || !e.target || e.target === hoverOverlay) return;

  e.preventDefault();
  e.stopPropagation();

  let extractedVal = "";
  const el = e.target;

  if (currentTargetType === 'image') {
    extractedVal = extractImageSrc(el);
  } else if (currentTargetType === 'pdf') {
    extractedVal = el.href || el.getAttribute('href') || "";
    if (!extractedVal) {
      const anchor = el.closest('a');
      if (anchor) extractedVal = anchor.href || anchor.getAttribute('href') || "";
    }
    if (!extractedVal) {
      extractedVal = el.innerText || el.textContent || "";
    }
    if (extractedVal && !extractedVal.startsWith('http') && extractedVal.includes('.pdf')) {
      try {
        extractedVal = new URL(extractedVal, window.location.href).href;
      } catch (err) {}
    }
  } else {
    // Text extraction
    extractedVal = el.innerText || el.textContent || el.value || "";
    extractedVal = extractedVal.replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim();
  }

  // Send value back to sidepanel
  chrome.runtime.sendMessage({
    action: 'ELEMENT_PICKED',
    fieldId: currentTargetField,
    fieldType: currentTargetType,
    value: extractedVal
  });

  stopPickerMode();
}

// Full page auto-scraper logic
function extractWineDataFromPage() {
  const data = {
    name: "",
    category: "VINO_ROSSO",
    denominazione: "DOC",
    vintage_year: null,
    is_riserva: false,
    alcohol_degrees: null,
    description: "",
    photo_url: "",
    technical_sheet_pdf: "",
    serving_temperature: "16-18°C",
    indicative_price: "",
    tasting_notes: { visual: "", olfactory: "", taste: "" },
    grape_varieties: []
  };

  const bodyText = document.body.innerText || "";
  const lowerText = bodyText.toLowerCase();

  // Name
  const ogTitle = document.querySelector('meta[property="og:title"]')?.content;
  const h1Text = document.querySelector('h1')?.innerText?.trim();
  data.name = (ogTitle || h1Text || document.title || "").replace(/[\r\n]+/g, ' ').trim();

  // Description
  const ogDesc = document.querySelector('meta[property="og:description"]')?.content ||
                 document.querySelector('meta[name="description"]')?.content;
  if (ogDesc) {
    data.description = ogDesc.trim();
  } else {
    const p = Array.from(document.querySelectorAll('p')).map(el => el.innerText.trim()).filter(t => t.length > 40);
    if (p.length) data.description = p[0];
  }

  // Image
  const ogImage = document.querySelector('meta[property="og:image"]')?.content;
  if (ogImage) {
    data.photo_url = ogImage.startsWith('http') ? ogImage : new URL(ogImage, window.location.href).href;
  } else {
    const imgs = Array.from(document.querySelectorAll('img')).filter(i => (i.src || '').includes('vino') || (i.alt || '').includes('vino'));
    if (imgs.length) data.photo_url = imgs[0].src;
  }

  // Category
  if (lowerText.includes('spumante') || lowerText.includes('brut')) data.category = 'SPUMANTE';
  else if (lowerText.includes('passito')) data.category = 'PASSITO';
  else if (lowerText.includes('rosato') || lowerText.includes('rosé')) data.category = 'ROSATO';
  else if (lowerText.includes('bianco')) data.category = 'VINO_BIANCO';

  // Denominazione
  if (lowerText.includes('tintilia del molise doc')) data.denominazione = 'Tintilia del Molise DOC';
  else if (lowerText.includes('biferno doc')) data.denominazione = 'Biferno DOC';
  else if (lowerText.includes('igt')) data.denominazione = 'IGT';

  // Riserva & Vintage
  if (lowerText.includes('riserva')) data.is_riserva = true;
  const yMatch = bodyText.match(/\b(20[0-2][0-9])\b/);
  if (yMatch) data.vintage_year = parseInt(yMatch[1], 10);

  // Alcohol
  const alcMatch = bodyText.match(/(\d{2}(?:[.,]\d)?)\s*%\s*(?:vol)?/i);
  if (alcMatch) data.alcohol_degrees = parseFloat(alcMatch[1].replace(',', '.'));

  // PDF
  const pdf = Array.from(document.querySelectorAll('a[href*=".pdf"]')).map(a => a.href)[0];
  if (pdf) data.technical_sheet_pdf = pdf;

  return data;
}

// Runtime Listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'SCRAPE_PAGE') {
    const data = extractWineDataFromPage();
    sendResponse({ status: 'SUCCESS', data });
  } else if (request.action === 'START_PICKER') {
    startPickerMode(request.fieldId, request.fieldType);
    sendResponse({ status: 'PICKER_STARTED' });
  } else if (request.action === 'STOP_PICKER') {
    stopPickerMode();
    sendResponse({ status: 'PICKER_STOPPED' });
  }
  return true;
});
