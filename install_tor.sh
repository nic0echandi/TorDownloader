#!/bin/bash
# Script de instalación de Tor

set -e

echo "================================"
echo "Instalador de Tor"
echo "================================"
echo ""

# Detectar el sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Detectar distribucion
    if [ -f /etc/debian_version ]; then
        echo "📦 Sistema detectado: Debian/Ubuntu"
        echo "Instalando Tor..."
        sudo apt-get update
        sudo apt-get install -y tor
        
    elif [ -f /etc/redhat-release ]; then
        echo "📦 Sistema detectado: Red Hat/CentOS/Fedora"
        echo "Instalando Tor..."
        sudo yum install -y tor
        
    elif [ -f /etc/arch-release ]; then
        echo "📦 Sistema detectado: Arch Linux"
        echo "Instalando Tor..."
        sudo pacman -S tor
        
    else
        echo "❌ Distribución Linux no identificada"
        echo "Por favor instala Tor manualmente: https://www.torproject.org/download/"
        exit 1
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📦 Sistema detectado: macOS"
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew no instalado"
        echo "Instala: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    echo "Instalando Tor..."
    brew install tor

else
    echo "❌ Sistema operativo no soportado"
    exit 1
fi

echo ""
echo "✓ Tor instalado exitosamente"
echo ""

# Iniciar servicio
echo "Iniciando servicio Tor..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start tor
else
    sudo systemctl start tor
    sudo systemctl enable tor  # Autoarrancar al iniciar
fi

echo "✓ Tor iniciado"
echo ""

# Verificar que está escuchando
echo "Verificando conexión..."
sleep 2

if nc -z 127.0.0.1 9050 2>/dev/null; then
    echo "✓ Tor escuchando en puerto 9050"
else
    echo "⚠️  Tor puede no estar listo. Intenta en unos segundos:"
    echo "   telnet 127.0.0.1 9050"
fi

echo ""
echo "================================"
echo "✓ Tor configurado correctamente"
echo "================================"
echo ""
echo "Próximos pasos:"
echo "1. Ejecuta: python3 tor_downloader.py"
echo "2. Ingresa tu URL onion"
echo "3. Elige carpeta de destino"
echo ""
