// ===============================================
// SST Intelligence - Cloud Assistant v4.0
// Fallback data para modo local (file://)
// ===============================================

const FALLBACK_MATRIX = [
  {
    "id": "1",
    "norma": "Ley 16.744",
    "articulo": "Artículo 67",
    "descripcion": "Establece que las empresas están obligadas a adoptar y mantener medidas de higiene y seguridad en el trabajo, según las normas que dicte el Servicio Nacional de Salud.",
    "como_resolver": "Implementar un Programa de Prevención de Riesgos, contar con Reglamento Interno de Higiene y Seguridad (RIHS) y realizar capacitaciones periódicas.",
    "evidencia": "Reglamento Interno vigente, registros de capacitación (ODI), Programa de Prevención de Riesgos firmado.",
    "fecha_actualizacion": "2024-05-01",
    "link": "https://www.leychile.cl/Navegar?idNorma=28650#670"
  },
  {
    "id": "2",
    "norma": "D.S. 594",
    "articulo": "Artículo 3",
    "descripcion": "La empresa está obligada a mantener los lugares de trabajo en condiciones sanitarias y ambientales adecuadas para proteger la vida y salud de los trabajadores.",
    "como_resolver": "Realizar operativos de limpieza, control de plagas y asegurar abastecimiento de agua potable y servicios higiénicos suficientes.",
    "evidencia": "Registros de limpieza, certificados de sanitización/desratización, resultados de análisis de agua potable.",
    "fecha_actualizacion": "2024-05-01",
    "link": "https://www.leychile.cl/Navegar?idNorma=167766#30"
  },
  {
    "id": "3",
    "norma": "D.S. 40",
    "articulo": "Artículo 21",
    "descripcion": "Obligación de informar oportuna y convenientemente a todos sus trabajadores acerca de los riesgos que entrañan sus labores (Derecho a Saber).",
    "como_resolver": "Realizar charlas de Inducción de Hombre Nuevo (ODI) al ingreso y ante cambios en procesos o puestos de trabajo.",
    "evidencia": "Documentos ODI firmados por los trabajadores y el representante de la empresa.",
    "fecha_actualizacion": "2024-05-01",
    "link": "https://www.leychile.cl/Navegar?idNorma=10545#210"
  },
  {
    "id": "4",
    "norma": "Ley 21.643 (Ley Karin)",
    "articulo": "Artículos varios",
    "descripcion": "Prevenir, investigar y sancionar el acoso laboral, sexual y la violencia en el trabajo.",
    "como_resolver": "Actualizar el RIHS, implementar un Protocolo de Prevención de Acoso y realizar formación a los mandos medios y trabajadores.",
    "evidencia": "Protocolo de Prevención de Acoso, registros de capacitación sobre la Ley Karin, RIHS actualizado con anexo de denuncias.",
    "fecha_actualizacion": "2024-02-01",
    "link": "https://www.leychile.cl/Navegar?idNorma=1200000"
  },
  {
    "id": "5",
    "norma": "D.S. 54",
    "articulo": "Artículo 1",
    "descripcion": "En toda empresa, faena, sucursal o agencia en que trabajen más de 25 personas, se organizarán Comités Paritarios de Higiene y Seguridad.",
    "como_resolver": "Realizar el proceso de elección de representantes de trabajadores y designación de representantes de la empresa ante el CPHS.",
    "evidencia": "Actas de constitución, acta de elección de trabajadores, actas de reuniones mensuales.",
    "fecha_actualizacion": "2024-05-01",
    "link": "https://www.leychile.cl/Navegar?idNorma=10674"
  },
  {
    "id": "6",
    "norma": "D.S. 594 (Modificado)",
    "articulo": "Artículo 66",
    "descripcion": "Límites permisibles para agentes químicos y físicos en el ambiente de trabajo.",
    "como_resolver": "Realizar mediciones de agentes ambientales mediante laboratorios acreditados y comparar con tablas vigentes.",
    "evidencia": "Informes de mediciones ambientales, certificados de calibración de equipos.",
    "fecha_actualizacion": "2026-04-09",
    "link": "https://www.leychile.cl/Navegar?idNorma=167766#660"
  }
];

const FALLBACK_SUGGESTIONS = [
  {
    "id": "202404092300",
    "norma": "D.S. 44 (Publicación Reciente)",
    "articulo": "Todo el Reglamento",
    "descripcion": "El nuevo Reglamento sobre Gestión Preventiva de los Riesgos Laborales reemplaza definitivamente a los decretos 40 y 54. Requiere la implementación de un SG-SST completo.",
    "link": "https://www.leychile.cl/Navegar?idNorma=1200000",
    "status": "pending_ai"
  }
];

// ===============================================
// App Principal
// ===============================================
document.addEventListener('DOMContentLoaded', () => {
    let officialData = [];
    let suggestionsData = [];
    let isLocalMode = false;

    const normativeBody = document.getElementById('normative-body');
    const suggestionsGrid = document.getElementById('suggestions-grid');
    const searchInput = document.getElementById('search-input');
    const suggestionBadge = document.getElementById('suggestion-badge');
    
    // Tab Switching
    const tabs = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');
        });
    });

    // ===== Carga de datos con fallback =====
    async function loadData() {
        // Intentar cargar desde fetch (funciona en GitHub Pages / servidor local)
        try {
            const offResponse = await fetch('data/matriz_legal_sst.json');
            if (!offResponse.ok) throw new Error(`HTTP ${offResponse.status}`);
            officialData = await offResponse.json();
        } catch (e) {
            console.warn('Fetch de matriz falló, usando datos embebidos:', e.message);
            officialData = FALLBACK_MATRIX;
            isLocalMode = true;
        }

        try {
            const sugResponse = await fetch('data/pending_suggestions.json');
            if (!sugResponse.ok) throw new Error(`HTTP ${sugResponse.status}`);
            suggestionsData = await sugResponse.json();
        } catch (e) {
            console.warn('Fetch de sugerencias falló, usando datos embebidos:', e.message);
            suggestionsData = FALLBACK_SUGGESTIONS;
            isLocalMode = true;
        }

        if (isLocalMode) {
            showLocalBanner();
        }

        renderOfficialTable(officialData);
        renderSuggestions(suggestionsData);
        updateBadge();
    }

    // ===== Banner de modo local =====
    function showLocalBanner() {
        const main = document.querySelector('main');
        const banner = document.createElement('div');
        banner.className = 'local-banner';
        banner.innerHTML = `
            <i class="fas fa-info-circle"></i>
            <span><strong>Modo local:</strong> Mostrando datos embebidos. Para datos en tiempo real, despliega en GitHub Pages o usa <code>python3 -m http.server 8000</code></span>
        `;
        main.insertBefore(banner, main.firstChild);
    }

    // ===== Render Tabla Oficial =====
    function renderOfficialTable(data) {
        normativeBody.innerHTML = '';
        if (data.length === 0) {
            normativeBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 3rem; color: var(--text-muted);">No se encontraron resultados.</td></tr>';
            return;
        }
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="norm-badge">${item.norma}</span></td>
                <td><span class="article-text">${item.articulo}</span></td>
                <td>${item.como_resolver}</td>
                <td>${item.evidencia}</td>
                <td><span class="status-pill verified">Verificado</span></td>
                <td><a href="${item.link}" target="_blank" rel="noopener" class="btn-action" title="Ver norma completa"><i class="fas fa-external-link-alt"></i></a></td>
            `;
            normativeBody.appendChild(row);
        });
    }

    // ===== Render Sugerencias =====
    function renderSuggestions(data) {
        suggestionsGrid.innerHTML = '';
        if (!data || data.length === 0) {
            suggestionsGrid.innerHTML = '<div class="empty-state">No hay hallazgos pendientes de análisis.</div>';
            return;
        }

        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'suggestion-card';
            card.innerHTML = `
                <div class="card-header">
                    <span class="badge-new">NUEVO HALLAZGO</span>
                    <span class="date">${datetimeToDate(item.id)}</span>
                </div>
                <h4>${item.norma}</h4>
                <p class="desc">${item.descripcion}</p>
                <div class="card-footer">
                    <button class="btn-ai" onclick="requestAIAnalysis('${item.id}')">
                        <i class="fas fa-magic"></i> Solicitar Análisis IA
                    </button>
                    <a href="${item.link}" target="_blank" rel="noopener" class="link-secondary">
                        <i class="fas fa-external-link-alt"></i> Ver fuente oficial
                    </a>
                </div>
            `;
            suggestionsGrid.appendChild(card);
        });
    }

    // ===== Utilidades =====
    function datetimeToDate(id) {
        if (!id || id.length < 8) return 'Reciente';
        return `${id.substring(6, 8)}/${id.substring(4, 6)}/${id.substring(0, 4)}`;
    }

    function updateBadge() {
        const count = suggestionsData ? suggestionsData.length : 0;
        suggestionBadge.textContent = count;
        suggestionBadge.style.display = count > 0 ? 'inline-block' : 'none';
    }

    // ===== Exportación a Excel =====
    document.getElementById('btn-export').addEventListener('click', () => {
        if (typeof XLSX === 'undefined') {
            alert('La librería de Excel aún se está cargando. Intenta de nuevo en unos segundos.');
            return;
        }
        const exportData = officialData.map(item => ({
            'Norma': item.norma,
            'Artículo': item.articulo,
            'Descripción': item.descripcion,
            'Cómo Resolver': item.como_resolver,
            'Evidencia': item.evidencia,
            'Fecha Actualización': item.fecha_actualizacion,
            'Link': item.link
        }));
        const ws = XLSX.utils.json_to_sheet(exportData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Matriz Legal SST");
        XLSX.writeFile(wb, `Matriz_SST_Cloud_${new Date().toISOString().split('T')[0]}.xlsx`);
    });

    // ===== Búsqueda con manejo seguro de campos =====
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
            renderOfficialTable(officialData);
            return;
        }
        const filtered = officialData.filter(i =>
            (i.norma || '').toLowerCase().includes(query) ||
            (i.articulo || '').toLowerCase().includes(query) ||
            (i.descripcion || '').toLowerCase().includes(query) ||
            (i.como_resolver || '').toLowerCase().includes(query) ||
            (i.evidencia || '').toLowerCase().includes(query)
        );
        renderOfficialTable(filtered);
    });

    // Iniciar carga
    loadData();
});

// ===== Función global para análisis IA =====
window.requestAIAnalysis = function (id) {
    const modal = document.getElementById('ai-modal');
    modal.classList.add('active');

    setTimeout(() => {
        modal.classList.remove('active');
        alert("Para obtener el análisis experto, copia el nombre del hallazgo en nuestra conversación con Antigravity.\n\nEjemplo: \"Antigravity, analiza el hallazgo D.S. 44\"");
    }, 2500);
};
