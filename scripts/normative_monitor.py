#!/usr/bin/env python3
"""
SST Normative Monitor v3.0 - Con IA Gemini
============================================
Monitoreo real de fuentes oficiales chilenas + Análisis automático con Google Gemini.

Fuentes:
  1. LeyChile (BCN) - API XML pública
  2. Dirección del Trabajo (DT) - Scraping

IA: Google Gemini 2.0 Flash (API gratuita)

Ejecutado diariamente por GitHub Actions.
"""

import os
import sys
import json
import hashlib
import datetime
import time
import logging
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =============================================================================
# Configuración
# =============================================================================
DB_PATH = 'data/matriz_legal_sst.json'
PENDING_PATH = 'data/pending_suggestions.json'
PROCESSED_PATH = 'data/processed_ids.json'

# Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = 'gemini-2.0-flash'
GEMINI_ENDPOINT = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'

# =============================================================================
# Palabras clave AMPLIADAS - Cobertura ESMAX completa
# =============================================================================
SST_KEYWORDS = [
    # --- SST General ---
    'seguridad', 'salud', 'trabajo', 'trabajadores', 'laboral', 'riesgo',
    'prevención', 'accidente', 'enfermedad profesional', 'higiene',
    'comité paritario', 'cphs', 'mutualidad', 'protección', 'siniestro',
    'incapacidad', 'invalidez', 'exposición', 'agente', 'ergonómico',
    'psicosocial', 'acoso', 'violencia', 'emergencia', 'evacuación',
    'extintor', 'epp', 'elemento de protección', 'reglamento interno',
    'fiscalización', 'sanción', 'multa', 'capacitación',
    # --- Normativa SST clave ---
    'ley 16.744', 'ley 16744', 'd.s. 594', 'ds 594', 'd.s. 40', 'ds 40',
    'd.s. 54', 'ds 54', 'd.s. 44', 'ds 44', 'ley karin', 'ley 21.643',
    'suseso', 'seremi', 'isl', 'mutual',
    # --- Energía / Combustibles ---
    'combustible', 'hidrocarburo', 'petróleo', 'gasolina', 'diésel', 'diesel',
    'kerosene', 'gas licuado', 'glp', 'gnl', 'gnc', 'lubricante',
    'estación de servicio', 'expendio', 'almacenamiento de combustible',
    'tanque de combustible', 'surtidor', 'inflamable', 'líquido combustible',
    # --- Plantas de combustible / SEC ---
    'planta de abastecimiento', 'terminal de combustible', 'instalación petrolera',
    'sec', 'superintendencia de electricidad', 'instalación eléctrica',
    'decreto 160', 'ds 160', 'decreto 90', 'reglamento de seguridad para instalaciones',
    'nch 2120', 'almacenamiento sustancias',
    # --- Transporte / Distribución B2C y B2B ---
    'distribución de combustible', 'transporte de carga peligrosa',
    'decreto 298', 'ds 298', 'sustancias peligrosas', 'naciones unidas clase',
    'hoja de seguridad', 'hds', 'sds', 'rombo nfpa', 'camión cisterna',
    'carga peligrosa', 'clase 3', 'mercancía peligrosa', 'adr',
    # --- Minería ---
    'minería', 'faena minera', 'sernageomin', 'reglamento minero',
    'ds 132', 'd.s. 132', 'seguridad minera', 'explotación minera',
    'planta minera', 'chancado', 'relaves', 'polvo en suspensión',
    # --- Puertos / Marítimo ---
    'puerto', 'marítimo', 'directemar', 'instalación portuaria',
    'operación portuaria', 'muelle', 'terminal marítimo', 'código pbip',
    'isps', 'nave', 'embarque', 'desembarque', 'grúa portuaria',
    # --- Seguridad empresarial ---
    'seguridad privada', 'os-10', 'vigilancia', 'plan de emergencia',
    'brigada', 'plan de contingencia', 'simulacro', 'control de acceso',
    'seguridad patrimonial', 'cctv', 'alarma',
    # --- Calidad ---
    'gestión de calidad', 'iso 9001', 'iso 14001', 'iso 45001',
    'norma técnica', 'nch', 'certificación', 'auditoría',
    'sistema de gestión', 'mejora continua', 'no conformidad',
    # --- Medio Ambiente ---
    'medio ambiente', 'evaluación ambiental', 'sea', 'sma',
    'residuo', 'residuo peligroso', 'resp', 'emisión', 'retc',
    'resolución de calificación ambiental', 'rca', 'riles', 'rises',
    'contaminación', 'impacto ambiental', 'huella de carbono',
    'declaración impacto ambiental', 'dia', 'estudio impacto ambiental', 'eia',
]

# Términos de búsqueda para LeyChile API
SEARCH_TERMS = [
    "seguridad+salud+trabajo",
    "riesgo+laboral",
    "accidente+trabajo",
    "prevencion+riesgos",
    "combustible+seguridad",
    "sustancias+peligrosas",
    "carga+peligrosa+transporte",
    "mineria+seguridad",
    "puerto+maritimo+seguridad",
    "medio+ambiente+residuos",
    "instalacion+electrica+seguridad",
]

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('sst_monitor')

# Timeout y reintentos
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5


# =============================================================================
# Utilidades
# =============================================================================
def load_json(path):
    """Carga un archivo JSON de forma segura."""
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error leyendo {path}: {e}")
    return []


def save_json(path, data):
    """Guarda datos en un archivo JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Datos guardados en {path}")


def generate_finding_id(norma, link):
    """Genera un ID único basado en fecha + hash del contenido."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    content_hash = hashlib.md5(f"{norma}|{link}".encode()).hexdigest()[:8]
    return f"{timestamp}_{content_hash}"


def normalize_text(text):
    """Normaliza texto para comparaciones."""
    if not text:
        return ""
    return text.lower().strip().replace('  ', ' ')


def is_relevant(text):
    """Verifica si un texto es relevante para el monitoreo ESMAX."""
    text_lower = normalize_text(text)
    return any(kw in text_lower for kw in SST_KEYWORDS)


def fetch_with_retry(url, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES):
    """Realiza una petición HTTP con reintentos."""
    headers = {
        'User-Agent': 'SST-Monitor/3.0 (ESMAX Compliance; contacto: asistente-sst)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout, headers=headers, verify=True)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError:
            logger.warning(f"Error SSL en {url}, intentando sin verificación...")
            try:
                response = requests.get(url, timeout=timeout, headers=headers, verify=False)
                response.raise_for_status()
                return response
            except Exception as e:
                logger.warning(f"Intento {attempt}/{max_retries} falló para {url}: {e}")
        except Exception as e:
            logger.warning(f"Intento {attempt}/{max_retries} falló para {url}: {e}")

        if attempt < max_retries:
            time.sleep(RETRY_DELAY)

    logger.error(f"Todos los intentos fallaron para {url}")
    return None


# =============================================================================
# Análisis con Google Gemini
# =============================================================================
GEMINI_PROMPT_TEMPLATE = """Eres un experto senior en Seguridad y Salud en el Trabajo (SST), Medio Ambiente, Calidad y cumplimiento regulatorio en Chile. Trabajas para ESMAX Distribución SpA, empresa líder en distribución de combustibles con operaciones en:

- Plantas de almacenamiento y distribución de combustibles
- Estaciones de servicio (venta B2C)
- Venta directa a clientes industriales (B2B)  
- Proyectos mineros (suministro de combustible)
- Operaciones portuarias (recepción de combustible)
- Transporte de carga peligrosa (Clase 3 - Líquidos inflamables)

Analiza la siguiente normativa/hallazgo detectado por el monitor automático:

📋 NORMA: {norma}
📝 DESCRIPCIÓN: {descripcion}
🔗 FUENTE: {fuente}

Genera un análisis estructurado en formato JSON con la siguiente estructura exacta (responde SOLO el JSON, sin markdown ni texto adicional):

{{
  "resumen": "Explicación clara y simple de qué dice esta norma en 2-3 oraciones",
  "aplica_esmax": true/false,
  "como_aplica": "Explicación de cómo aplica específicamente a ESMAX y sus operaciones",
  "acciones_requeridas": [
    "Acción concreta 1",
    "Acción concreta 2",
    "Acción concreta 3"
  ],
  "evidencia_necesaria": [
    "Documento/registro 1",
    "Documento/registro 2"
  ],
  "plazo": "Inmediato / 30 días / 90 días / Sin plazo definido",
  "urgencia": "Alta / Media / Baja",
  "areas_afectadas": ["SST", "Medio Ambiente", "Calidad", "Seguridad Empresarial"],
  "normativa_relacionada": ["Ley 16.744", "D.S. 594", "etc."]
}}"""


def analyze_with_gemini(finding):
    """
    Envía un hallazgo a Google Gemini para análisis experto.
    Retorna el análisis como diccionario o None si falla.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY no configurada. Saltando análisis IA.")
        return None

    prompt = GEMINI_PROMPT_TEMPLATE.format(
        norma=finding.get('norma', 'N/D'),
        descripcion=finding.get('descripcion', 'N/D'),
        fuente=finding.get('fuente', finding.get('link', 'N/D'))
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json"
        }
    }

    headers = {
        'Content-Type': 'application/json',
    }

    url = f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}"

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Extraer texto de la respuesta de Gemini
        text = data['candidates'][0]['content']['parts'][0]['text']

        # Limpiar posible markdown wrapping
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()

        # Parsear JSON
        analysis = json.loads(text)
        analysis['analyzed_at'] = datetime.datetime.now().isoformat()
        analysis['model'] = GEMINI_MODEL

        logger.info(f"  ✅ Análisis IA completado - Urgencia: {analysis.get('urgencia', 'N/D')}")
        return analysis

    except requests.exceptions.HTTPError as e:
        logger.error(f"  ❌ Error HTTP Gemini: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"     Detalle: {e.response.text[:300]}")
    except json.JSONDecodeError as e:
        logger.error(f"  ❌ Error parseando respuesta Gemini: {e}")
        logger.error(f"     Texto recibido: {text[:300] if 'text' in dir() else 'N/A'}")
    except KeyError as e:
        logger.error(f"  ❌ Estructura inesperada de respuesta Gemini: {e}")
    except Exception as e:
        logger.error(f"  ❌ Error inesperado con Gemini: {e}")

    return None


# =============================================================================
# Monitor 1: LeyChile (BCN) - API XML pública
# =============================================================================
def monitor_leychile():
    """
    Consulta la API XML pública de LeyChile para normas relevantes.
    """
    logger.info("=" * 60)
    logger.info("Escaneando LeyChile (BCN) - API XML...")
    findings = []

    # --- Estrategia 1: Últimas normas publicadas ---
    url_ultimas = "https://www.leychile.cl/Consulta/obtxml?opt=3&cantidad=15"
    logger.info(f"Consultando últimas 15 normas: {url_ultimas}")

    response = fetch_with_retry(url_ultimas)
    if response:
        try:
            new_findings = parse_leychile_xml(response.text, "Últimas publicadas")
            findings.extend(new_findings)
            logger.info(f"  → {len(new_findings)} normas obtenidas de 'últimas publicadas'")
        except Exception as e:
            logger.error(f"Error parseando XML: {e}")

    # --- Estrategia 2: Búsqueda por keywords ---
    for term in SEARCH_TERMS:
        url_search = f"https://www.leychile.cl/Consulta/obtxml?opt=61&cadena={term}&cantidad=5"
        logger.info(f"Buscando: '{term.replace('+', ' ')}'")

        response = fetch_with_retry(url_search)
        if response:
            try:
                new_findings = parse_leychile_xml(response.text, f"Búsqueda: {term}")
                findings.extend(new_findings)
                logger.info(f"  → {len(new_findings)} resultados")
            except Exception as e:
                logger.error(f"Error parseando búsqueda '{term}': {e}")

        time.sleep(1.5)

    # Filtrar solo los relevantes
    relevant = [f for f in findings if is_relevant(
        f"{f['norma']} {f.get('descripcion', '')} {f.get('articulo', '')}"
    )]

    logger.info(f"Total hallazgos relevantes de LeyChile: {len(relevant)}")
    return relevant


def parse_leychile_xml(xml_text, source_label):
    """Parsea la respuesta XML de la API de LeyChile."""
    findings = []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"XML inválido ({source_label}): {e}")
        return findings

    for norma_elem in root.iter():
        titulo = None
        id_norma = None
        fecha = None
        url_norma = None
        tipo_norma = None

        if norma_elem.tag in ('norma', 'Norma', 'ley', 'Ley', 'resultado', 'Resultado'):
            for child in norma_elem:
                tag_lower = child.tag.lower()
                text = (child.text or '').strip()

                if tag_lower in ('titulo', 'nombre', 'glosa', 'titulonorma'):
                    titulo = text
                elif tag_lower in ('idnorma', 'id', 'numero'):
                    id_norma = text
                elif tag_lower in ('fecha', 'fechapublicacion', 'fechapromulgacion'):
                    fecha = text
                elif tag_lower in ('tiponorma', 'tipo'):
                    tipo_norma = text
                elif tag_lower in ('url', 'link', 'urlnorma'):
                    url_norma = text

            if titulo or id_norma:
                norma_name = titulo or f"Norma ID {id_norma}"
                if tipo_norma:
                    norma_name = f"{tipo_norma} - {norma_name}"

                link = url_norma or (f"https://www.leychile.cl/Navegar?idNorma={id_norma}" if id_norma else "https://www.leychile.cl")

                findings.append({
                    "id": generate_finding_id(norma_name, link),
                    "norma": norma_name[:200],
                    "articulo": "Ver norma completa",
                    "descripcion": f"Publicación detectada en LeyChile ({source_label}). Fecha: {fecha or 'N/D'}.",
                    "link": link,
                    "status": "pending_ai",
                    "fuente": "LeyChile (BCN)",
                    "fecha_deteccion": datetime.datetime.now().isoformat()
                })

    return findings


# =============================================================================
# Monitor 2: Dirección del Trabajo (DT)
# =============================================================================
def monitor_dt():
    """Escanea noticias y dictámenes de la DT."""
    logger.info("=" * 60)
    logger.info("Escaneando Dirección del Trabajo (DT)...")
    findings = []

    urls_dt = [
        "https://www.dt.gob.cl/legislacion/1624/w3-propertyvalue-22040.html",
        "https://www.dt.gob.cl/legislacion/1624/w3-channel.html",
    ]

    for url in urls_dt:
        logger.info(f"Consultando: {url}")
        response = fetch_with_retry(url)

        if response:
            try:
                response.encoding = response.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

                links = soup.find_all('a', href=True)
                for link in links:
                    text = link.get_text(strip=True)
                    href = link['href']

                    if len(text) < 15:
                        continue

                    if is_relevant(text):
                        if href.startswith('/'):
                            href = f"https://www.dt.gob.cl{href}"
                        elif not href.startswith('http'):
                            continue

                        findings.append({
                            "id": generate_finding_id(text, href),
                            "norma": text[:200],
                            "articulo": "Ver documento completo",
                            "descripcion": "Publicación detectada en la Dirección del Trabajo.",
                            "link": href,
                            "status": "pending_ai",
                            "fuente": "Dirección del Trabajo (DT)",
                            "fecha_deteccion": datetime.datetime.now().isoformat()
                        })
            except Exception as e:
                logger.error(f"Error procesando DT ({url}): {e}")

        time.sleep(2)

    seen_links = set()
    unique = []
    for f in findings:
        if f['link'] not in seen_links:
            seen_links.add(f['link'])
            unique.append(f)

    logger.info(f"Total hallazgos de DT: {len(unique)}")
    return unique


# =============================================================================
# Deduplicación Multi-criterio
# =============================================================================
def is_duplicate(finding, existing_items, processed_ids):
    """Verifica si un hallazgo ya existe."""
    f_link = normalize_text(finding.get('link', ''))
    f_norma = normalize_text(finding.get('norma', ''))
    f_hash = hashlib.md5(f"{f_norma}|{f_link}".encode()).hexdigest()

    if f_hash in processed_ids:
        return True

    for item in existing_items:
        item_link = normalize_text(item.get('link', ''))
        item_norma = normalize_text(item.get('norma', ''))

        if f_link and item_link and f_link == item_link:
            return True
        if f_norma and item_norma:
            if f_norma in item_norma or item_norma in f_norma:
                return True

    return False


# =============================================================================
# Notificación por Email (con resumen IA)
# =============================================================================
def send_alert_email(new_items):
    """Envía un correo con resumen de hallazgos y análisis IA."""
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    receiver_email = os.getenv('RECEIVER_EMAIL')

    if not all([sender_email, sender_password, receiver_email]):
        logger.warning("Faltan variables de entorno para correo. Saltando.")
        return

    msg = MIMEMultipart()
    msg['From'] = f"Asistente SST ESMAX <{sender_email}>"
    msg['To'] = receiver_email
    msg['Subject'] = f"🔔 Alerta SST ESMAX: {len(new_items)} Nuevos Hallazgos"

    body = "=" * 60 + "\n"
    body += "🛡️ ASISTENTE SST ESMAX - REPORTE DIARIO\n"
    body += f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    body += "=" * 60 + "\n\n"

    for i, item in enumerate(new_items, 1):
        body += f"📌 HALLAZGO #{i}\n"
        body += f"   Norma: {item['norma']}\n"
        body += f"   Fuente: {item.get('fuente', 'Desconocida')}\n"
        body += f"   Link: {item['link']}\n"

        # Si tiene análisis IA, incluirlo
        ai = item.get('ai_analysis')
        if ai:
            body += f"\n   🧠 ANÁLISIS IA:\n"
            body += f"   Urgencia: {'🔴' if ai.get('urgencia') == 'Alta' else '🟡' if ai.get('urgencia') == 'Media' else '🟢'} {ai.get('urgencia', 'N/D')}\n"
            body += f"   Aplica a ESMAX: {'✅ SÍ' if ai.get('aplica_esmax') else '❌ NO'}\n"
            body += f"   Resumen: {ai.get('resumen', 'N/D')}\n"

            acciones = ai.get('acciones_requeridas', [])
            if acciones:
                body += f"   Acciones:\n"
                for a in acciones[:3]:
                    body += f"     → {a}\n"

            body += f"   Plazo: {ai.get('plazo', 'N/D')}\n"
            body += f"   Áreas: {', '.join(ai.get('areas_afectadas', []))}\n"

        body += "\n" + "-" * 40 + "\n\n"

    body += "\n📊 Dashboard: https://robinson21.github.io/agente-sst-normativo/\n"
    body += "\n--\nAsistente SST ESMAX v3.0 con IA Gemini\n"

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logger.info("✅ Correo enviado exitosamente.")
    except Exception as e:
        logger.error(f"Error al enviar correo: {e}")


# =============================================================================
# Función Principal
# =============================================================================
def main():
    logger.info("🚀 Iniciando SST Normative Monitor v3.0 (con IA Gemini)")
    logger.info(f"Hora: {datetime.datetime.now().isoformat()}")
    logger.info(f"Gemini API: {'✅ Configurada' if GEMINI_API_KEY else '⚠️ No configurada'}")
    logger.info("=" * 60)

    # Cargar datos existentes
    pending = load_json(PENDING_PATH)
    official = load_json(DB_PATH)
    processed_ids = load_json(PROCESSED_PATH)

    all_existing = pending + official

    # Ejecutar monitores
    all_findings = []

    try:
        all_findings.extend(monitor_leychile())
    except Exception as e:
        logger.error(f"Error en monitor LeyChile: {e}")

    try:
        all_findings.extend(monitor_dt())
    except Exception as e:
        logger.error(f"Error en monitor DT: {e}")

    logger.info("=" * 60)
    logger.info(f"Total hallazgos brutos: {len(all_findings)}")

    # Filtrar duplicados
    new_items = []
    for finding in all_findings:
        if not is_duplicate(finding, all_existing, processed_ids):
            new_items.append(finding)
            f_link = normalize_text(finding.get('link', ''))
            f_norma = normalize_text(finding.get('norma', ''))
            f_hash = hashlib.md5(f"{f_norma}|{f_link}".encode()).hexdigest()
            processed_ids.append(f_hash)

    logger.info(f"Hallazgos nuevos (post-dedup): {len(new_items)}")

    # ========================================
    # Análisis con Gemini IA
    # ========================================
    if new_items and GEMINI_API_KEY:
        logger.info("=" * 60)
        logger.info("🧠 Iniciando análisis con Google Gemini...")
        analyzed_count = 0

        for i, item in enumerate(new_items):
            logger.info(f"  Analizando [{i+1}/{len(new_items)}]: {item['norma'][:60]}...")

            analysis = analyze_with_gemini(item)
            if analysis:
                item['ai_analysis'] = analysis
                item['status'] = 'analyzed'
                analyzed_count += 1
            else:
                item['ai_analysis'] = None
                item['status'] = 'pending_ai'

            # Rate limiting: esperar entre llamadas
            if i < len(new_items) - 1:
                time.sleep(4)

        logger.info(f"✅ Análisis completado: {analyzed_count}/{len(new_items)} hallazgos analizados")

    if new_items:
        pending.extend(new_items)
        save_json(PENDING_PATH, pending)

        processed_ids = processed_ids[-500:]
        save_json(PROCESSED_PATH, processed_ids)

        send_alert_email(new_items)

        logger.info(f"✅ {len(new_items)} nuevos hallazgos procesados.")
        for item in new_items:
            urgencia = ''
            if item.get('ai_analysis'):
                urgencia = f" [Urgencia: {item['ai_analysis'].get('urgencia', 'N/D')}]"
            logger.info(f"   → {item['norma'][:70]}...{urgencia}")
    else:
        processed_ids = processed_ids[-500:]
        save_json(PROCESSED_PATH, processed_ids)
        logger.info("✅ Sin hallazgos nuevos.")

    logger.info("=" * 60)
    logger.info("Monitor finalizado.")


if __name__ == "__main__":
    main()
