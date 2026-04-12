#!/bin/bash
# =============================================
# Servidor local para desarrollo del Dashboard
# Abre http://localhost:8000 en tu navegador
# =============================================
echo "🚀 Iniciando servidor local SST Intelligence..."
echo "📍 Dashboard disponible en: http://localhost:8000"
echo "   Presiona Ctrl+C para detener."
echo ""
python3 -m http.server 8000
