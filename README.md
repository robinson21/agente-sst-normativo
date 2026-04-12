# 🛡️ Agente SST Normativo - Guía de Configuración

Este repositorio contiene tu **Asistente Experto en SST** automatizado. Sigue estos pasos para activar el monitoreo diario y las notificaciones por correo.

## 🚀 Pasos de Configuración Inicial

### 1. Preparar Cuenta de Correo (Emisor)
Para enviar alertas gratuitas, usaremos una cuenta de Gmail secundaria:
1. Ve a tu cuenta de Google > Seguridad.
2. Activa la **Verificación en 2 pasos**.
3. Busca **Contraseñas de aplicaciones**.
4. Crea una nueva (Nombre: "Asistente SST") y **copia el código de 16 dígitos**.

### 2. Configurar Secretos en GitHub
Para que el asistente trabaje de forma segura en la nube:
1. En este repositorio, ve a **Settings** > **Secrets and variables** > **Actions**.
2. Presiona **New repository secret** y añade estos tres:
   - `SENDER_EMAIL`: Tu correo de Gmail emisor.
   - `SENDER_PASSWORD`: El código de 16 dígitos de la contraseña de aplicación.
   - `RECEIVER_EMAIL`: Tu correo personal donde quieres recibir las alertas.

### 3. Activar el Dashboard (GitHub Pages)
1. Ve a **Settings** > **Pages**.
2. En "Build and deployment" > "Source", selecciona **Deploy from a branch**.
3. Selecciona la rama `main` y la carpeta `/(root)`.
4. En unos minutos, tu dashboard estará en: `https://[tu-usuario].github.io/[nombre-del-repo]/`

## 🤖 Uso del Asistente

- **Diario Oficial**: El asistente revisará cada mañana (5:00 AM Chile) si hay nuevas publicaciones. Si encuentra algo, te enviará un correo.
- **Sugerencias IA**: Los hallazgos aparecerán en la pestaña "Sugerencias IA" del dashboard.
- **Análisis Experto**: Cuando veas una sugerencia, abre nuestra sesión de chat y dime: *"Antigravity, analiza el hallazgo [Nombre de la Norma]"*. Yo generaré el análisis detallado para que lo agregues a tu Matriz Oficial.

---
*Desarrollado con IA para la excelencia en Seguridad y Salud en el Trabajo.*
