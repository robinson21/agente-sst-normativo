/**
 * SST Intelligence Dashboard v5.0
 * Con análisis IA (Google Gemini) integrado
 */

// =============================================================================
// Datos fallback para modo local
// =============================================================================
const FALLBACK_MATRIX = [
  {
    "norma": "Ley 16.744",
    "articulo": "Artículo 67",
    "resolucion_osh": "Implementar un Programa de Prevención de Riesgos, contar con Reglamento Interno de Higiene y Seguridad (RIHS) y realizar capacitaciones periódicas.",
    "evidencia": "Reglamento Interno vigente, registros de capacitación (ODI), Programa de Prevención de Riesgos firmado.",
    "estado": "Verificado",
    "link": "https://www.leychile.cl/Navegar?idNorma=28650"
  },
  {
    "norma": "D.S. 594",
    "articulo": "Artículo 3",
    "resolucion_osh": "Realizar operativos de limpieza, control de plagas y asegurar abastecimiento de agua potable y servicios higiénicos suficientes.",
    "evidencia": "Registros de limpieza, certificados de sanitización/desratización, resultados de análisis de agua potable.",
    "estado": "Verificado",
    "link": "https://www.leychile.cl/Navegar?idNorma=167766"
  },
  {
    "norma": "D.S. 40",
    "articulo": "Artículo 21",
    "resolucion_osh": "Elaborar y mantener actualizado el Reglamento Interno de Higiene y Seguridad con la participación del Comité Paritario.",
    "evidencia": "Reglamento Interno actualizado, actas de reuniones CPHS, registro de entrega a trabajadores.",
    "estado": "Verificado",
    "link": "https://www.leychile.cl/Navegar?idNorma=10148"
  },
  {
    "norma": "D.S. 54",
    "articulo": "Artículo 1",
    "resolucion_osh": "Constituir y mantener funcionando el Comité Paritario de Higiene y Seguridad con reuniones mensuales.",
    "evidencia": "Acta de constitución CPHS, actas mensuales, registro de investigaciones de accidentes.",
    "estado": "Verificado",
    "link": "https://www.leychile.cl/Navegar?idNorma=6153"
  },
  {
    "norma": "D.S. 298",
    "articulo": "Completo",
    "resolucion_osh": "Cumplir con normativa de transporte de sustancias peligrosas Clase 3 (líquidos inflamables). Vehículos habilitados, conductores capacitados.",
    "evidencia": "Licencia DGMN, Hojas de Seguridad (HDS), Certificado habilitación vehículo SEREMITT, registro capacitación conductores.",
    "estado": "Verificado",
    "link": "https://www.leychile.cl/Navegar?idNorma=48778"
  }
];

const FALLBACK_SUGGESTIONS = [
  {
    "norma": "D.S. 44 (Actualización SERNAGEOMIN)",
    "articulo": "Varios",
    "descripcion": "Modificaciones al reglamento de seguridad en faenas mineras. Aplica a proveedores de combustible en operaciones mineras.",
    "link": "https://www.leychile.cl/Navegar?idNorma=1234567",
    "status": "analyzed",
    "fuente": "LeyChile (BCN)",
    "ai_analysis": {
      "resumen": "Actualiza requisitos de seguridad para faenas mineras, incluyendo proveedores de combustible y servicios.",
      "aplica_esmax": true,
      "como_aplica": "ESMAX como proveedor de combustible en faenas mineras debe cumplir con requisitos actualizados de seguridad.",
      "acciones_requeridas": [
        "Revisar procedimientos de entrega de combustible en faenas",
        "Actualizar capacitaciones de personal que ingresa a mineras",
        "Verificar cumplimiento de HDS y rotulación de cisternas"
      ],
      "evidencia_necesaria": [
        "Procedimientos actualizados",
        "Registros de capacitación",
        "Checklist de inspección de vehículos"
      ],
      "plazo": "90 días",
      "urgencia": "Media",
      "areas_afectadas": ["SST", "Calidad"],
      "normativa_relacionada": ["D.S. 132", "D.S. 298"]
    }
  }
];

// =============================================================================
// Gemini API Config
// =============================================================================
const GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

const GEMINI_PROMPT = `Eres un experto senior en Seguridad y Salud en el Trabajo (SST), Medio Ambiente, Calidad y cumplimiento regulatorio en Chile. Trabajas para ESMAX Distribución SpA, empresa líder en distribución de combustibles con operaciones en:

- Plantas de almacenamiento y distribución de combustibles
- Estaciones de servicio (venta B2C)
- Venta directa a clientes industriales (B2B)
- Proyectos mineros (suministro de combustible)
- Operaciones portuarias (recepción de combustible)
- Transporte de carga peligrosa (Clase 3 - Líquidos inflamables)

Analiza la siguiente normativa/hallazgo:

📋 NORMA: {norma}
📝 DESCRIPCIÓN: {descripcion}
🔗 FUENTE: {fuente}

Genera un análisis estructurado en formato JSON con esta estructura exacta (responde SOLO el JSON):

{
  "resumen": "Explicación clara de qué dice esta norma en 2-3 oraciones",
  "aplica_esmax": true o false,
  "como_aplica": "Cómo aplica a ESMAX y sus operaciones",
  "acciones_requeridas": ["Acción 1", "Acción 2", "Acción 3"],
  "evidencia_necesaria": ["Documento 1", "Documento 2"],
  "plazo": "Inmediato / 30 días / 90 días / Sin plazo definido",
  "urgencia": "Alta / Media / Baja",
  "areas_afectadas": ["SST", "Medio Ambiente", "Calidad", "Seguridad Empresarial"],
  "normativa_relacionada": ["Ley 16.744", "etc."]
}`;

// =============================================================================
// Gemini API Functions
// =============================================================================
function getApiKey() {
  return localStorage.getItem('gemini_api_key') || '';
}

function setApiKey(key) {
  localStorage.setItem('gemini_api_key', key);
  updateAiStatus();
}

function clearApiKey() {
  localStorage.removeItem('gemini_api_key');
  updateAiStatus();
}

function updateAiStatus() {
  const dot = document.getElementById('ai-dot');
  const text = document.getElementById('ai-status-text');
  const key = getApiKey();

  if (key) {
    dot.className = 'dot online';
    text.textContent = 'IA: Activa';
  } else {
    dot.className = 'dot offline';
    text.textContent = 'IA: Sin configurar';
  }
}

async function analyzeWithGemini(finding) {
  const apiKey = getApiKey();
  if (!apiKey) {
    alert('⚠️ Configura tu API Key de Gemini en la pestaña "Configuración" para usar el análisis IA.');
    return null;
  }

  const prompt = GEMINI_PROMPT
    .replace('{norma}', finding.norma || 'N/D')
    .replace('{descripcion}', finding.descripcion || finding.resolucion_osh || 'N/D')
    .replace('{fuente}', finding.fuente || finding.link || 'N/D');

  const payload = {
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: {
      temperature: 0.3,
      maxOutputTokens: 2048,
      responseMimeType: "application/json"
    }
  };

  try {
    const response = await fetch(`${GEMINI_ENDPOINT}?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`HTTP ${response.status}: ${err}`);
    }

    const data = await response.json();
    let text = data.candidates[0].content.parts[0].text.trim();

    if (text.startsWith('```json')) text = text.slice(7);
    if (text.startsWith('```')) text = text.slice(3);
    if (text.endsWith('```')) text = text.slice(0, -3);

    return JSON.parse(text.trim());
  } catch (err) {
    console.error('Error Gemini:', err);
    alert(`Error al conectar con Gemini: ${err.message}`);
    return null;
  }
}

async function testApiKey() {
  const apiKey = document.getElementById('api-key-input').value.trim() || getApiKey();
  const statusEl = document.getElementById('key-status');

  if (!apiKey) {
    statusEl.innerHTML = '<span class="status-error">❌ Ingresa una API key primero.</span>';
    return;
  }

  statusEl.innerHTML = '<span class="status-testing"><i class="fas fa-spinner fa-spin"></i> Probando conexión...</span>';

  try {
    const response = await fetch(`${GEMINI_ENDPOINT}?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: 'Responde solo: OK' }] }],
        generationConfig: { maxOutputTokens: 10 }
      })
    });

    if (response.ok) {
      statusEl.innerHTML = '<span class="status-success">✅ ¡Conexión exitosa! API Key válida.</span>';
    } else {
      const err = await response.text();
      statusEl.innerHTML = `<span class="status-error">❌ Error: ${response.status}. Verifica tu API key.</span>`;
    }
  } catch (err) {
    statusEl.innerHTML = `<span class="status-error">❌ Error de conexión: ${err.message}</span>`;
  }
}

// =============================================================================
// Data Loading
// =============================================================================
let matrixData = [];
let suggestionsData = [];

async function loadData() {
  const isLocal = window.location.protocol === 'file:';

  if (isLocal) {
    showLocalBanner();
    matrixData = FALLBACK_MATRIX;
    suggestionsData = FALLBACK_SUGGESTIONS;
  } else {
    try {
      const [matRes, sugRes] = await Promise.all([
        fetch('data/matriz_legal_sst.json'),
        fetch('data/pending_suggestions.json')
      ]);
      matrixData = await matRes.json();
      suggestionsData = await sugRes.json();
    } catch (err) {
      console.warn('Error loading data, using fallback:', err);
      showLocalBanner();
      matrixData = FALLBACK_MATRIX;
      suggestionsData = FALLBACK_SUGGESTIONS;
    }
  }

  renderMatrix(matrixData);
  renderSuggestions(suggestionsData);

  const badge = document.getElementById('suggestion-badge');
  badge.textContent = suggestionsData.length;
  badge.style.display = suggestionsData.length > 0 ? 'inline-flex' : 'none';
}

function showLocalBanner() {
  const banner = document.createElement('div');
  banner.className = 'local-mode-banner';
  banner.innerHTML = '<i class="fas fa-info-circle"></i> <strong>Modo local:</strong> Mostrando datos embebidos. Para datos en tiempo real, despliega en GitHub Pages o usa <code>python3 -m http.server 8000</code>';
  document.querySelector('.controls').prepend(banner);
}

// =============================================================================
// Render Matrix Table
// =============================================================================
function renderMatrix(data) {
  const tbody = document.getElementById('normative-body');
  tbody.innerHTML = '';

  data.forEach(item => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><span class="norm-badge">${item.norma}</span></td>
      <td><span class="article-text">${item.articulo}</span></td>
      <td>${item.resolucion_osh}</td>
      <td>${item.evidencia}</td>
      <td><span class="status-badge status-${item.estado?.toLowerCase().replace(' ', '-')}">${item.estado}</span></td>
      <td><a href="${item.link}" target="_blank" class="link-secondary"><i class="fas fa-external-link-alt"></i></a></td>
    `;
    tbody.appendChild(row);
  });
}

// =============================================================================
// Render Suggestions with AI Analysis
// =============================================================================
function renderSuggestions(data) {
  const grid = document.getElementById('suggestions-grid');
  grid.innerHTML = '';

  if (!data || data.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-check-circle"></i>
        <h4>Sin hallazgos pendientes</h4>
        <p>El monitor no ha detectado normativa nueva. La próxima ejecución es a las 5:00 AM.</p>
      </div>`;
    return;
  }

  data.forEach((item, idx) => {
    const ai = item.ai_analysis;
    const hasAi = ai && ai.resumen;
    const urgencyClass = hasAi ? `urgency-${(ai.urgencia || 'baja').toLowerCase()}` : 'urgency-pending';
    const urgencyLabel = hasAi ? ai.urgencia : 'Pendiente IA';
    const appliesToEsmax = hasAi && ai.aplica_esmax;

    const card = document.createElement('div');
    card.className = 'suggestion-card';
    card.innerHTML = `
      <div class="card-header">
        <div class="card-badges">
          <span class="urgency-badge ${urgencyClass}">${urgencyLabel}</span>
          ${appliesToEsmax ? '<span class="esmax-badge">Aplica ESMAX</span>' : ''}
          ${hasAi ? '<span class="ai-badge"><i class="fas fa-brain"></i> Analizado</span>' : '<span class="ai-badge pending"><i class="fas fa-clock"></i> Sin analizar</span>'}
        </div>
        <span class="card-source">${item.fuente || 'Desconocida'}</span>
      </div>
      <h4 class="card-title">${item.norma}</h4>
      <p class="card-description">${item.descripcion || ''}</p>

      ${hasAi ? `
        <div class="ai-summary">
          <div class="ai-summary-header">
            <i class="fas fa-robot"></i> Resumen IA
          </div>
          <p>${ai.resumen}</p>
          ${ai.como_aplica ? `<p class="ai-applies"><strong>Impacto ESMAX:</strong> ${ai.como_aplica}</p>` : ''}
        </div>

        ${ai.acciones_requeridas && ai.acciones_requeridas.length ? `
          <div class="ai-actions">
            <strong><i class="fas fa-tasks"></i> Acciones requeridas:</strong>
            <ul>${ai.acciones_requeridas.map(a => `<li>${a}</li>`).join('')}</ul>
          </div>
        ` : ''}

        <div class="ai-meta">
          ${ai.plazo ? `<span class="meta-item"><i class="fas fa-calendar"></i> ${ai.plazo}</span>` : ''}
          ${ai.areas_afectadas ? `<span class="meta-item"><i class="fas fa-building"></i> ${ai.areas_afectadas.join(', ')}</span>` : ''}
        </div>
      ` : ''}

      <div class="card-actions">
        <a href="${item.link}" target="_blank" class="btn btn-sm">
          <i class="fas fa-external-link-alt"></i> Ver norma
        </a>
        <button class="btn btn-sm btn-ai" onclick="analyzeItem(${idx})">
          <i class="fas fa-brain"></i> ${hasAi ? 'Re-analizar' : 'Analizar con IA'}
        </button>
        ${hasAi ? `<button class="btn btn-sm btn-detail" onclick="showFullAnalysis(${idx})">
          <i class="fas fa-eye"></i> Ver detalle
        </button>` : ''}
      </div>
    `;
    grid.appendChild(card);
  });
}

// =============================================================================
// IA Analysis Actions
// =============================================================================
async function analyzeItem(idx) {
  const item = suggestionsData[idx];
  if (!item) return;

  // Show processing modal
  const modal = document.getElementById('ai-modal');
  modal.classList.add('active');

  const analysis = await analyzeWithGemini(item);

  modal.classList.remove('active');

  if (analysis) {
    suggestionsData[idx].ai_analysis = analysis;
    suggestionsData[idx].status = 'analyzed';
    renderSuggestions(suggestionsData);
    showFullAnalysis(idx);
  }
}

function showFullAnalysis(idx) {
  const item = suggestionsData[idx];
  const ai = item?.ai_analysis;
  if (!ai) return;

  const modal = document.getElementById('analysis-modal');
  const result = document.getElementById('analysis-result');

  const urgencyClass = `urgency-${(ai.urgencia || 'baja').toLowerCase()}`;

  result.innerHTML = `
    <div class="analysis-header-info">
      <h4>${item.norma}</h4>
      <div class="analysis-badges">
        <span class="urgency-badge ${urgencyClass}">${ai.urgencia || 'N/D'}</span>
        ${ai.aplica_esmax ? '<span class="esmax-badge">✅ Aplica a ESMAX</span>' : '<span class="no-esmax-badge">❌ No aplica directamente</span>'}
      </div>
    </div>

    <div class="analysis-section">
      <h5><i class="fas fa-file-alt"></i> Resumen</h5>
      <p>${ai.resumen}</p>
    </div>

    ${ai.como_aplica ? `
    <div class="analysis-section">
      <h5><i class="fas fa-industry"></i> Impacto en ESMAX</h5>
      <p>${ai.como_aplica}</p>
    </div>` : ''}

    ${ai.acciones_requeridas?.length ? `
    <div class="analysis-section">
      <h5><i class="fas fa-tasks"></i> Acciones Requeridas</h5>
      <ul>${ai.acciones_requeridas.map(a => `<li>${a}</li>`).join('')}</ul>
    </div>` : ''}

    ${ai.evidencia_necesaria?.length ? `
    <div class="analysis-section">
      <h5><i class="fas fa-folder-open"></i> Evidencia Necesaria</h5>
      <ul>${ai.evidencia_necesaria.map(e => `<li>${e}</li>`).join('')}</ul>
    </div>` : ''}

    <div class="analysis-footer">
      <div class="analysis-meta-grid">
        <div class="meta-block">
          <span class="meta-label">Plazo</span>
          <span class="meta-value">${ai.plazo || 'N/D'}</span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Áreas afectadas</span>
          <span class="meta-value">${(ai.areas_afectadas || []).join(', ') || 'N/D'}</span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Normativa relacionada</span>
          <span class="meta-value">${(ai.normativa_relacionada || []).join(', ') || 'N/D'}</span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Modelo IA</span>
          <span class="meta-value">${ai.model || 'Gemini 2.0 Flash'}</span>
        </div>
      </div>
    </div>
  `;

  modal.classList.add('active');
}

function closeAnalysisModal() {
  document.getElementById('analysis-modal').classList.remove('active');
}

// =============================================================================
// Tab Navigation
// =============================================================================
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const tabId = btn.dataset.tab + '-tab';
      document.getElementById(tabId).classList.add('active');
    });
  });
}

// =============================================================================
// Search Filter
// =============================================================================
function setupSearch() {
  const input = document.getElementById('search-input');
  input.addEventListener('input', () => {
    const query = input.value.toLowerCase();
    const filteredMat = matrixData.filter(item =>
      Object.values(item).some(val =>
        typeof val === 'string' && val.toLowerCase().includes(query)
      )
    );
    renderMatrix(filteredMat);

    const filteredSug = suggestionsData.filter(item => {
      const searchable = `${item.norma} ${item.descripcion || ''} ${item.ai_analysis?.resumen || ''}`;
      return searchable.toLowerCase().includes(query);
    });
    renderSuggestions(filteredSug);
  });
}

// =============================================================================
// Export
// =============================================================================
function setupExport() {
  document.getElementById('btn-export').addEventListener('click', () => {
    if (typeof XLSX === 'undefined') {
      alert('Librería de Excel no disponible');
      return;
    }
    const wb = XLSX.utils.book_new();
    const ws1 = XLSX.utils.json_to_sheet(matrixData);
    XLSX.utils.book_append_sheet(wb, ws1, 'Matriz Legal');

    const sugFlat = suggestionsData.map(s => ({
      norma: s.norma,
      descripcion: s.descripcion,
      fuente: s.fuente,
      link: s.link,
      urgencia: s.ai_analysis?.urgencia || 'Pendiente',
      aplica_esmax: s.ai_analysis?.aplica_esmax ? 'Sí' : 'Pendiente',
      resumen_ia: s.ai_analysis?.resumen || 'Sin análisis',
      acciones: (s.ai_analysis?.acciones_requeridas || []).join(' | ')
    }));
    const ws2 = XLSX.utils.json_to_sheet(sugFlat);
    XLSX.utils.book_append_sheet(wb, ws2, 'Sugerencias IA');

    XLSX.writeFile(wb, `SST_ESMAX_${new Date().toISOString().slice(0, 10)}.xlsx`);
  });
}

// =============================================================================
// Settings
// =============================================================================
function setupSettings() {
  document.getElementById('btn-save-key').addEventListener('click', () => {
    const key = document.getElementById('api-key-input').value.trim();
    if (key) {
      setApiKey(key);
      document.getElementById('key-status').innerHTML = '<span class="status-success">✅ API Key guardada correctamente.</span>';
      document.getElementById('api-key-input').value = '';
    }
  });

  document.getElementById('btn-test-key').addEventListener('click', testApiKey);

  document.getElementById('btn-clear-key').addEventListener('click', () => {
    clearApiKey();
    document.getElementById('key-status').innerHTML = '<span class="status-error">🗑️ API Key eliminada.</span>';
  });

  // Pre-fill if key exists
  if (getApiKey()) {
    document.getElementById('api-key-input').placeholder = '•••••••• (key guardada)';
  }
}

// =============================================================================
// Modal close on background click
// =============================================================================
function setupModals() {
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });
}

// =============================================================================
// Init
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupSearch();
  setupExport();
  setupSettings();
  setupModals();
  updateAiStatus();
  loadData();
});
