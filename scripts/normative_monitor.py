#!/usr/bin/env python3
"""
SST Normative Monitor v2.0
===========================
Monitoreo real de fuentes oficiales chilenas:
  1. LeyChile (BCN) - API XML pública
  2. Dirección del Trabajo (DT) - Scraping de noticias

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

# Palabras clave SST para filtrar normas relevantes
SST_KEYWORDS = [
    'seguridad', 'salud', 'trabajo', 'trabajadores', 'laboral', 'riesgo',
    'prevención', 'accidente', 'enfermedad profesional', 'higiene',
    'comité paritario', 'cphs', 'mutualidad', 'protección', 'siniestro',
    'incapacidad', 'invalidez', 'exposición', 'agente', 'químico', 'físico',
    'ergonómico', 'psicosocial', 'acoso', 'violencia', 'emergencia',
    'evacuación', 'extintor', 'epp', 'elemento de protección',
    'reglamento interno', 'fiscalización', 'sanción', 'multa',
    'ley 16.744', 'ley 16744', 'd.s. 594', 'ds 594', 'd.s. 40', 'ds 40',
    'd.s. 54', 'ds 54', 'd.s. 44', 'ds 44', 'ley karin', 'ley 21.643',
    'suseso', 'seremi', 'isl', 'mutual'
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


def is_sst_relevant(text):
    """Verifica si un texto es relevante para SST."""
    text_lower = normalize_text(text)
    return any(kw in text_lower for kw in SST_KEYWORDS)


def fetch_with_retry(url, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES):
    """Realiza una petición HTTP con reintentos."""
    headers = {
        'User-Agent': 'SST-Monitor/2.0 (Compliance Automation; contacto: asistente-sst)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout, headers=headers, verify=True)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError:
            # Algunos sitios chilenos tienen certificados problemáticos
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
# Monitor 1: LeyChile (BCN) - API XML pública
# =============================================================================
def monitor_leychile():
    """
    Consulta la API XML pública de LeyChile (Biblioteca del Congreso Nacional)
    para las últimas normas publicadas y búsqueda por keywords SST.
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
            logger.error(f"Error parseando XML de últimas normas: {e}")

    # --- Estrategia 2: Búsqueda específica por keywords SST ---
    search_terms = [
        "seguridad+salud+trabajo",
        "riesgo+laboral",
        "accidente+trabajo",
        "prevencion+riesgos",
    ]

    for term in search_terms:
        url_search = f"https://www.leychile.cl/Consulta/obtxml?opt=61&cadena={term}&cantidad=5"
        logger.info(f"Buscando: '{term.replace('+', ' ')}'")

        response = fetch_with_retry(url_search)
        if response:
            try:
                new_findings = parse_leychile_xml(response.text, f"Búsqueda: {term}")
                findings.extend(new_findings)
                logger.info(f"  → {len(new_findings)} resultados para '{term}'")
            except Exception as e:
                logger.error(f"Error parseando búsqueda '{term}': {e}")

        time.sleep(2)  # Respetar el servidor

    # Filtrar solo los relevantes a SST
    sst_findings = []
    for f in findings:
        combined_text = f"{f['norma']} {f.get('descripcion', '')} {f.get('articulo', '')}"
        if is_sst_relevant(combined_text):
            sst_findings.append(f)

    logger.info(f"Total hallazgos SST de LeyChile: {len(sst_findings)}")
    return sst_findings


def parse_leychile_xml(xml_text, source_label):
    """Parsea la respuesta XML de la API de LeyChile."""
    findings = []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"XML inválido de LeyChile ({source_label}): {e}")
        return findings

    # La API de LeyChile devuelve normas en diferentes estructuras XML
    # Buscar elementos de norma (pueden ser <norma>, <ley>, o similar)
    for norma_elem in root.iter():
        # Extraer campos comunes de la API de LeyChile
        titulo = None
        id_norma = None
        fecha = None
        url_norma = None
        tipo_norma = None

        # Buscar en atributos y sub-elementos
        if norma_elem.tag in ('norma', 'Norma', 'ley', 'Ley', 'resultado', 'Resultado'):
            for child in norma_elem:
                tag_lower = child.tag.lower()
                text = (child.text or '').strip()

                if tag_lower in ('titulo', 'nombre', 'glosa', 'tituloNorma'.lower()):
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

                link = url_norma or f"https://www.leychile.cl/Navegar?idNorma={id_norma}" if id_norma else "https://www.leychile.cl"

                findings.append({
                    "id": generate_finding_id(norma_name, link),
                    "norma": norma_name[:200],  # Limitar longitud
                    "articulo": "Ver norma completa",
                    "descripcion": f"Nueva publicación detectada en LeyChile ({source_label}). Fecha: {fecha or 'N/D'}.",
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
    """
    Escanea noticias y dictámenes recientes de la Dirección del Trabajo.
    """
    logger.info("=" * 60)
    logger.info("Escaneando Dirección del Trabajo (DT)...")
    findings = []

    # Página principal y noticias de la DT (pueden cambiar; el monitor maneja errores)
    urls_dt = [
        "https://www.dt.gob.cl/legislacion/1624/w3-propertyvalue-22040.html",  # Dictámenes
        "https://www.dt.gob.cl/legislacion/1624/w3-channel.html",  # Legislación general
    ]

    for url in urls_dt:
        logger.info(f"Consultando: {url}")
        response = fetch_with_retry(url)

        if response:
            try:
                response.encoding = response.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

                # Buscar enlaces que contengan contenido SST relevante
                links = soup.find_all('a', href=True)
                for link in links:
                    text = link.get_text(strip=True)
                    href = link['href']

                    if len(text) < 15:
                        continue

                    if is_sst_relevant(text):
                        # Construir URL completa si es relativa
                        if href.startswith('/'):
                            href = f"https://www.dt.gob.cl{href}"
                        elif not href.startswith('http'):
                            continue

                        findings.append({
                            "id": generate_finding_id(text, href),
                            "norma": text[:200],
                            "articulo": "Ver documento completo",
                            "descripcion": f"Publicación detectada en la Dirección del Trabajo.",
                            "link": href,
                            "status": "pending_ai",
                            "fuente": "Dirección del Trabajo (DT)",
                            "fecha_deteccion": datetime.datetime.now().isoformat()
                        })

            except Exception as e:
                logger.error(f"Error procesando DT ({url}): {e}")

        time.sleep(2)  # Respetar el servidor

    # Eliminar duplicados internos por link
    seen_links = set()
    unique_findings = []
    for f in findings:
        if f['link'] not in seen_links:
            seen_links.add(f['link'])
            unique_findings.append(f)

    logger.info(f"Total hallazgos SST de DT: {len(unique_findings)}")
    return unique_findings


# =============================================================================
# Deduplicación Multi-criterio
# =============================================================================
def is_duplicate(finding, existing_items, processed_ids):
    """
    Verifica si un hallazgo ya existe usando múltiples criterios:
    1. Link exacto
    2. Nombre de norma normalizado
    3. Hash de contenido en IDs procesados
    """
    f_link = normalize_text(finding.get('link', ''))
    f_norma = normalize_text(finding.get('norma', ''))
    f_hash = hashlib.md5(f"{f_norma}|{f_link}".encode()).hexdigest()

    # Verificar contra IDs procesados anteriormente
    if f_hash in processed_ids:
        return True

    for item in existing_items:
        item_link = normalize_text(item.get('link', ''))
        item_norma = normalize_text(item.get('norma', ''))

        # Criterio 1: Link exacto
        if f_link and item_link and f_link == item_link:
            return True

        # Criterio 2: Nombre de norma muy similar (>80% coincidencia)
        if f_norma and item_norma:
            # Coincidencia simple por inclusión
            if f_norma in item_norma or item_norma in f_norma:
                return True

    return False


# =============================================================================
# Notificación por Email
# =============================================================================
def send_alert_email(new_items):
    """Envía un correo de notificación usando GitHub Secrets."""
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    receiver_email = os.getenv('RECEIVER_EMAIL')

    if not all([sender_email, sender_password, receiver_email]):
        logger.warning("Faltan variables de entorno para envío de correo. Saltando notificación.")
        return

    msg = MIMEMultipart()
    msg['From'] = f"Asistente SST <{sender_email}>"
    msg['To'] = receiver_email
    msg['Subject'] = f"🔔 Alerta SST: {len(new_items)} Nuevos Hallazgos Detectados"

    body = "El Asistente SST ha detectado nuevas publicaciones que requieren tu revisión:\n\n"
    body += f"Fecha del escaneo: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    body += "=" * 60 + "\n\n"

    for i, item in enumerate(new_items, 1):
        body += f"📌 Hallazgo #{i}\n"
        body += f"   Norma: {item['norma']}\n"
        body += f"   Fuente: {item.get('fuente', 'Desconocida')}\n"
        body += f"   Descripción: {item['descripcion']}\n"
        body += f"   Link: {item['link']}\n"
        body += "-" * 40 + "\n\n"

    body += "\n📋 Próximos pasos:\n"
    body += "1. Revisa los hallazgos en tu Dashboard SST\n"
    body += "2. Para cada hallazgo, inicia una conversación con Antigravity:\n"
    body += '   → "Antigravity, analiza el hallazgo [Nombre de la Norma]"\n'
    body += "3. Revisa el análisis experto y decide si incorporarlo a tu Matriz Oficial\n"

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logger.info("✅ Correo de alerta enviado exitosamente.")
    except Exception as e:
        logger.error(f"Error al enviar el correo: {e}")


# =============================================================================
# Función Principal
# =============================================================================
def main():
    logger.info("🚀 Iniciando SST Normative Monitor v2.0")
    logger.info(f"Hora de ejecución: {datetime.datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Cargar datos existentes
    pending = load_json(PENDING_PATH)
    official = load_json(DB_PATH)
    processed_ids = load_json(PROCESSED_PATH)

    # Combinar todos los items existentes para deduplicación
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

    # Filtrar duplicados con multi-criterio
    new_items = []
    for finding in all_findings:
        if not is_duplicate(finding, all_existing, processed_ids):
            new_items.append(finding)
            # Agregar hash a procesados
            f_link = normalize_text(finding.get('link', ''))
            f_norma = normalize_text(finding.get('norma', ''))
            f_hash = hashlib.md5(f"{f_norma}|{f_link}".encode()).hexdigest()
            processed_ids.append(f_hash)

    logger.info(f"Hallazgos nuevos (post-dedup): {len(new_items)}")

    if new_items:
        # Agregar a sugerencias pendientes
        pending.extend(new_items)
        save_json(PENDING_PATH, pending)

        # Guardar IDs procesados (mantener últimos 500 para no crecer indefinidamente)
        processed_ids = processed_ids[-500:]
        save_json(PROCESSED_PATH, processed_ids)

        # Enviar notificación por correo
        send_alert_email(new_items)

        logger.info(f"✅ Se encontraron {len(new_items)} nuevos hallazgos.")
        for item in new_items:
            logger.info(f"   → {item['norma'][:80]}...")
    else:
        # Guardar IDs procesados de todas formas
        processed_ids = processed_ids[-500:]
        save_json(PROCESSED_PATH, processed_ids)
        logger.info("✅ Escaneo finalizado. No hay hallazgos nuevos desde el último escaneo.")

    logger.info("=" * 60)
    logger.info("Monitor finalizado.")


if __name__ == "__main__":
    main()
