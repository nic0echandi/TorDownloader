#!/bin/bash
# Script de instalación rápida de dependencias

set -e

echo "================================"
echo "Instalador - Descargador Tor"
echo "================================"
echo ""

# Verificar Python
echo "1. Verificando Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no instalado"
    echo "   Instala: sudo apt-get install python3 python3-pip"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION encontrado"
echo ""

# Verificar Tor
echo "2. Verificando Tor..."
if ! command -v tor &> /dev/null; then
    echo "⚠ Tor no instalado"
    echo "   Instala: sudo apt-get install tor"
    echo "   Luego inicia: sudo systemctl start tor"
    exit 1
fi
echo "✓ Tor encontrado"
echo ""

# Instalar dependencias Python
echo "3. Instalando dependencias Python..."
pip install -q -r requirements.txt
echo "✓ Dependencias instaladas"
echo ""

# Hacer script ejecutable
echo "4. Configurando permisos..."
chmod +x tor_downloader.py
echo "✓ Script ejecutable"
echo ""

# Crear carpeta de destino
echo "5. Creando carpeta de destino..."
mkdir -p /home/user/Documents/files_descargados/logs
echo "✓ Carpeta creada: /home/user/Documents/files_descargados"
echo ""

# Verificar conexión a Tor
echo "6. Verificando conexión a Tor..."
python3 -c "
import requests
import sys
try:
    session = requests.Session()
    session.proxies.update({'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'})
    response = session.get('http://check.torproject.org', timeout=5)
    if 'Congratulations' in response.text or 'Tor' in response.text:
        print('✓ Conexión a Tor CONFIRMADA')
    else:
        print('⚠ Posible conexión a Tor')
except:
    print('❌ NO conectado a Tor')
    print('   Inicia Tor: sudo systemctl start tor')
    sys.exit(1)
" || exit 1
echo ""

echo "================================"
echo "✓ Instalación completada"
echo "================================"
echo ""
echo "Próximos pasos:"
echo "1. Edita tor_downloader.py si necesitas cambiar:"
echo "   - BASE_URL (URL onion)"
echo "   - DESTINATION_DIR (carpeta de destino)"
echo ""
echo "2. Ejecuta:"
echo "   python3 tor_downloader.py"
echo ""
echo "Más información: cat README.md"
