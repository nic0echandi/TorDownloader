# Guía de Instalación de Tor

## 🔧 Instalación Rápida

### Opción 1: Script Automático (Recomendado)
```bash
cd /home/user/Documents/ransome
bash install_tor.sh
```

El script detectará tu sistema e instalará Tor automáticamente.

---

## 📦 Instalación Manual por Sistema

### Debian/Ubuntu
```bash
# Actualizar repositorios
sudo apt-get update

# Instalar Tor
sudo apt-get install -y tor

# Iniciar servicio
sudo systemctl start tor
sudo systemctl enable tor  # Autoarrancar al iniciar

# Verificar
sudo systemctl status tor
```

### Fedora/RHEL/CentOS
```bash
sudo dnf install tor
# o
sudo yum install tor

sudo systemctl start tor
sudo systemctl enable tor
sudo systemctl status tor
```

### Arch Linux
```bash
sudo pacman -S tor

sudo systemctl start tor
sudo systemctl enable tor
sudo systemctl status tor
```

### macOS (con Homebrew)
```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Tor
brew install tor

# Iniciar servicio
brew services start tor

# Verificar
brew services list
```

### Windows
1. Descargar desde: https://www.torproject.org/download/
2. Instalar Tor Browser o Tor independiente
3. Ejecutar Tor localmente (puerto 9050)

---

## ✅ Verificar que Tor Funciona

### Método 1: Ver el estado del servicio
```bash
# Linux
sudo systemctl status tor

# macOS
brew services list
```

### Método 2: Verificar puerto abierto
```bash
# Ver si Tor escucha en puerto 9050
netstat -tuln | grep 9050
# o
lsof -i :9050
```

### Método 3: Conectar al puerto
```bash
telnet 127.0.0.1 9050
# Si ves: Connected to 127.0.0.1, está funcionando
# Presiona Ctrl+] luego quit para salir
```

### Método 4: Verificar con Python
```bash
python3 -c "
import requests
session = requests.Session()
session.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
try:
    response = session.get('http://check.torproject.org', timeout=5)
    if 'Tor' in response.text:
        print('✓ Tor funciona correctamente')
    else:
        print('⚠️  Posible conexión a Tor')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

---

## 🚀 Iniciar la Descarga

Una vez que Tor esté funcionando:

```bash
cd /home/user/Documents/ransome
python3 tor_downloader.py
```

El script debería:
1. Detectar Tor ejecutándose
2. Pedir la URL onion
3. Pedir el directorio destino
4. Comenzar la descarga

---

## ⚠️ Problemas Comunes

### "Command not found: tor"
```bash
# Tor no está instalado o PATH no está actualizado
sudo apt-get install tor  # o tu gestor de paquetes
```

### "Port 9050 is already in use"
Tor ya está ejecutándose:
```bash
# Verifica si está activo
ps aux | grep tor
```

### "Connection refused" cuando se ejecuta el script
```bash
# Reiniciar Tor
sudo systemctl restart tor

# O en macOS
brew services restart tor

# Esperar 5 segundos a que se inicie completamente
sleep 5
python3 tor_downloader.py
```

### "Failed to establish a new connection"
```bash
# Verificar que Tor escucha
sudo netstat -tuln | grep 9050

# Si no aparece nada, Tor no está corriendo:
sudo systemctl start tor
```

### Tor no inicia después de instalar
```bash
# Revisar logs
sudo journalctl -u tor -n 50

# O en macOS
cat ~/Library/Logs/Homebrew/tor.log
```

---

## 🔒 Configuración Adicional (Opcional)

Si necesitas usar un puerto diferente de 9050, edita el archivo de configuración de Tor:

### Linux
```bash
sudo nano /etc/tor/torrc

# Busca o añade:
# SocksPort 9050
# Cambia el puerto si es necesario

sudo systemctl restart tor
```

### macOS
```bash
nano /usr/local/etc/tor/torrc

# Busca o añade:
# SocksPort 9050

brew services restart tor
```

Luego en el script de descarga, cuando pregunte, ingresa el puerto personalizado.

---

## 📊 Monitor de Tor

Para ver estadísticas de Tor en tiempo real:
```bash
# Instalar arm (monitor de Tor)
sudo apt-get install tor-arm
# o
brew install nyx  # macOS

# Ejecutar
arm
# o
nyx
```

---

## ⏹️ Detener Tor

```bash
# Linux
sudo systemctl stop tor

# macOS
brew services stop tor
```

---

**Una vez instalado Tor, ejecuta:**
```bash
python3 tor_downloader.py
```

¿Necesitas ayuda con algo específico?
