# 📥 Descargador de Archivos desde Tor

Script Python completamente automatizado para descargar recursivamente archivos desde un directorio HTML listable en Tor, con verificación de integridad (SHA256), reintentos automáticos y logging detallado.

---

## 📋 Tabla de Contenidos

1. [¿Qué es esto?](#qué-es-esto)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Instalación Paso a Paso](#instalación-paso-a-paso)
4. [Configuración](#configuración)
5. [Cómo Usar](#cómo-usar)
6. [Características](#características)
7. [Compatibilidad por Plataforma](#compatibilidad-por-plataforma)
8. [Solución de Problemas](#solución-de-problemas)
9. [Seguridad](#seguridad)

---

## ¿Qué es esto?

Un script Python que descarga automáticamente todos los archivos de un sitio `.onion` (Tor) de forma recursiva, verificando que cada archivo es íntegro mediante checksums SHA256. Perfecto para descargar grandes colecciones de archivos de forma segura y confiable.

**Ventajas:**
- ✅ Descarga automática y recursiva
- ✅ Verificación SHA256 de cada archivo
- ✅ Reintentos automáticos si fallan
- ✅ Logging completo de todo el proceso
- ✅ Interfaz interactiva y amigable
- ✅ Funciona a través de Tor

---

## 📋 Requisitos del Sistema

### ⚠️ **Importante: Este proyecto NO incluye Tor**

El script es **solo un cliente Python** que se conecta a Tor. Debes tener **Tor instalado y ejecutándose** en tu computadora para que funcione.

**En todas las plataformas (Linux, macOS, Windows):**
- ✅ Tor debe estar instalado y corriendo en puerto `9050`
- ✅ El script se conecta a través de ese puerto
- ✅ No hay Tor incluido en este proyecto

### 1. Python 3.8 o superior
- **Linux/macOS**: Generalmente ya instalado
- **Windows**: Descargar desde https://www.python.org

Verificar instalación:
```bash
python3 --version
```

Debe mostrar algo como `Python 3.8.10` o superior.

### 2. Tor instalado y ejecutándose
Te mostraremos cómo instalarlo en la siguiente sección.

**El script verifica automáticamente que Tor está corriendo antes de empezar a descargar.**

### 3. Herramientas de desarrollo (solo en Linux)
```bash
# Debian/Ubuntu
sudo apt-get install python3-dev build-essential

# Fedora/CentOS
sudo dnf install python3-devel gcc

# Arch
sudo pacman -S base-devel
```

---

## 🚀 Instalación Paso a Paso

### PASO 1: Instalar Tor

#### En Linux (Debian/Ubuntu)

```bash
# Actualizar lista de paquetes
sudo apt-get update

# Instalar Tor
sudo apt-get install tor

# Iniciar el servicio Tor
sudo systemctl start tor

# Verificar que está ejecutándose
sudo systemctl status tor
```

Deberías ver algo como:
```
● tor.service - Anonymizing overlay network for TCP
   Loaded: loaded (/lib/systemd/system/tor.service)
   Active: active (running)
```

Presiona `q` para salir.

#### En Linux (Fedora/CentOS/RHEL)

```bash
sudo dnf install tor
sudo systemctl start tor
sudo systemctl status tor
```

#### En macOS

```bash
# Con Homebrew (si no tienes Homebrew, instálalo desde https://brew.sh)
brew install tor
brew services start tor

# Verificar
brew services list | grep tor
```

#### En Windows

**Opción A: Usar Tor Browser (Más fácil - Recomendado)**

1. Descargar desde https://www.torproject.org/download/
2. Ejecutar el instalador y seguir los pasos
3. Abrir Tor Browser
4. Ir a Settings → Connection → verificar que SOCKS5 proxy está en `127.0.0.1:9050`
5. Dejar Tor Browser abierto mientras descargas

**Opción B: Instalar Tor Standalone**

1. Descargar desde https://www.torproject.org/download/#windows
2. Extraer el archivo ZIP
3. Abrir terminal en esa carpeta y ejecutar `tor.exe`
4. Debería aparecer un mensaje: `Bootstrapped 100% (done): Done`
5. Dejar ejecutándose en la terminal mientras descargas

**Verificar que Tor está escuchando:**

En PowerShell o cmd:
```powershell
netstat -an | findstr 9050
```

Deberías ver algo como:
```
TCP    127.0.0.1:9050    0.0.0.0:0    LISTENING
```

---

### PASO 2: Crear Carpeta del Proyecto

Abre la terminal/cmd y ejecuta:

```bash
# En Windows
cd C:\Users\TuUsuario\Documents
mkdir ransome
cd ransome

# En Linux/macOS
mkdir -p ~/Documents/ransome
cd ~/Documents/ransome
```

---

### PASO 3: Crear Entorno Virtual de Python

El entorno virtual es una "burbuja" de Python aislada donde instalamos las dependencias del proyecto sin afectar el resto del sistema.

#### En Linux/macOS

```bash
# Crear el entorno virtual
python3 -m venv .venv

# Activarlo
source .venv/bin/activate
```

Cuando esté activo, verás algo como:
```
(.venv) usuario@computadora ~/Documents/ransome $
```

#### En Windows (PowerShell)

```bash
# Crear el entorno virtual
python -m venv .venv

# Activarlo
.venv\Scripts\Activate.ps1
```

Si recibís un error de permisos, ejecuta primero:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### En Windows (cmd.exe)

```cmd
# Crear el entorno virtual
python -m venv .venv

# Activarlo
.venv\Scripts\activate.bat
```

---

### PASO 4: Instalar Dependencias

Con el entorno virtual activado (recuerda, debe verse `(.venv)` en la terminal):

```bash
# Actualizar pip (gestor de paquetes Python)
pip install --upgrade pip

# Instalar las dependencias necesarias
pip install PySocks requests beautifulsoup4 urllib3
```

**¿Qué hace cada paquete?**
- **PySocks**: Soporte para conexión SOCKS (protocolo que usa Tor)
- **requests**: Librería para hacer peticiones HTTP
- **beautifulsoup4**: Analizar HTML para encontrar enlaces
- **urllib3**: Gestión de conexiones HTTP/HTTPS

El proceso debería terminar con:
```
Successfully installed PySocks-1.x.x requests-2.x.x beautifulsoup4-4.x.x urllib3-2.x.x
```

---

### PASO 5: Verificar Instalación

Prueba que todo está instalado correctamente:

```bash
# Verificar Python
python --version

# Verificar Tor está ejecutándose
netstat -tuln | grep 9050
```

Si ves algo como:
```
tcp 0 0 127.0.0.1:9050 0.0.0.0:* LISTEN
```

¡Excelente! Todo está listo.

---

## ⚙️ Configuración

### Método 1: Configuración Interactiva (Recomendado)

Simplemente ejecuta el script y te pedirá los datos:

```bash
python tor_downloader.py
```

El script te preguntará:
1. **URL del sitio Tor** (ej: `http://xxxxx.onion/carpeta/`)
2. **Carpeta donde guardar** (por defecto: `~/files_descargados/`)

### Método 2: Configuración Manual

Si necesitas cambiar más parámetros, edita `tor_downloader.py`:

```python
# Abre con tu editor favorito (nano, vim, VSCode, etc)
# Busca estas líneas y modifica:

BASE_URL = "http://tu-sitio.onion/carpeta/"  # Tu URL
DESTINATION_DIR = Path("/ruta/local")        # Donde guardar
MAX_RETRIES = 3                              # Reintentos (1-5)
TIMEOUT = 30                                 # Segundos por archivo
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}
```

**Explicación de cada parámetro:**

| Parámetro | Significado | Ejemplo |
|-----------|-------------|---------|
| `BASE_URL` | URL del sitio Tor a descargar | `http://pifk3xu3v....onion/files/` |
| `DESTINATION_DIR` | Carpeta local donde guardar | `/home/usuario/Descargas` |
| `MAX_RETRIES` | Cuántas veces reintentar un archivo fallido | `3` (1-5 recomendado) |
| `TIMEOUT` | Segundos máximos por conexión | `30` (aumenta si la red es lenta) |

---

## 📖 Cómo Usar

### Uso Básico

```bash
# Asegúrate que el entorno virtual esté activo
# Debe verse (.venv) en la terminal

python tor_downloader.py
```

El script te pedirá:
```
======================================================================
DESCARGADOR DE ARCHIVOS DESDE TOR
======================================================================

📍 Ingresa la URL onion base (ej: http://xxxxx.onion/carpeta/): 
```

Pega tu URL y presiona Enter.

### Ver Progreso en Tiempo Real

En otra terminal (con el entorno virtual activado):

```bash
tail -f ~/files_descargados/logs/descarga_*.log
```

Verás algo como:
```
2026-07-23 12:54:01 - INFO - ✓ archivo1.pdf (2.3 MB) SHA256: a1b2c3d4...
2026-07-23 12:54:03 - INFO - Descargando: archivo2.zip
2026-07-23 12:54:10 - INFO - ✓ archivo2.zip (15.4 MB) SHA256: e5f6g7h8...
```

### Pausar y Reanudar

```bash
# Ver procesos Python en ejecución
ps aux | grep tor_downloader

# Detener (reemplaza PID con el número mostrado)
kill PID

# Reanudar: ejecuta de nuevo, el script detectará archivos ya descargados
python tor_downloader.py
```

### Ejecutar en Background (Descargas Largas)

En Linux/macOS:
```bash
nohup python tor_downloader.py > descarga.log 2>&1 &
echo $! > downloader.pid  # Guardar ID del proceso
```

Para verificar:
```bash
tail -f descarga.log
```

Para detener después:
```bash
kill $(cat downloader.pid)
```

---

## ✨ Características

| Característica | Descripción |
|---|---|
| **Recursivo** | Descarga todos los archivos y subcarpetas automáticamente |
| **Reintentos** | Si falla una descarga, reinenta hasta 3 veces |
| **Verificación** | Calcula SHA256 de cada archivo para garantizar integridad |
| **Estructura** | Mantiene la jerarquía de carpetas original |
| **Logging** | Guarda log detallado en `carpeta_destino/logs/` |
| **Resumen** | Al terminar muestra estadísticas (total descargado, tiempo, velocidad) |
| **Manejo de Errores** | No se detiene si un archivo falla, continúa con los demás |
| **Tor Integration** | Conexión automática a través de proxy SOCKS5 |

---

## 📊 Salida del Script

### Ejemplo de Ejecución

```
======================================================================
DESCARGADOR DE ARCHIVOS DESDE TOR
======================================================================

📍 Ingresa la URL onion base: http://ejemplo.onion/carpeta/
✓ URL configurada: http://ejemplo.onion/carpeta/

📁 Directorio destino [/home/user/files_descargados]: 
✓ Directorio configurado: /home/user/files_descargados

Verificando conexión a Tor en puerto 9050...
✓ Conexión a Tor verificada

Listo para descargar

======================================================================
INICIANDO DESCARGA DESDE TOR
======================================================================

Explorando: http://ejemplo.onion/carpeta/
✓ archivo1.pdf (2.3 MB) SHA256: c75ee...
✓ archivo2.docx (1.1 MB) SHA256: 03b5f...
✓ carpeta/archivo3.zip (45.6 MB) SHA256: 8912...
```

### Resumen Final

```
======================================================================
RESUMEN DE DESCARGA
======================================================================
Total de archivos encontrados: 247
Archivos descargados exitosamente: 245
Archivos fallidos: 2
Tamaño total descargado: 2.45 GB
Tiempo total: 12 minutos 23 segundos
Velocidad promedio: 3.31 MB/s

Errores encontrados:
  - Acceso a directorio: http://ejemplo.onion/error/ - Timeout

Archivo de log: /home/user/files_descargados/logs/descarga_20260723_125010.log
======================================================================
```

---

## 🔧 Solución de Problemas

### ❌ Error: "Tor no está ejecutándose"

**Síntoma:**
```
ERROR - Error al acceder: Failed to establish a new connection
```

**Solución:**

En Linux:
```bash
sudo systemctl start tor
sudo systemctl status tor  # Verificar que está activo
```

En macOS:
```bash
brew services start tor
brew services list | grep tor
```

En Windows:
- Abre "Tor Browser" (debería tener Tor en background)
- O ejecuta el servicio de Tor directamente

---

### ❌ Error: "ModuleNotFoundError: No module named 'socks'"

**Síntoma:**
```
ModuleNotFoundError: No module named 'socks'
```

**Solución:**

```bash
# Asegúrate que el entorno virtual esté activo
source .venv/bin/activate  # Linux/macOS
# o
.venv\Scripts\activate     # Windows

# Instala PySocks
pip install PySocks
```

---

### ❌ Error: "Connection refused" o "Cannot assign requested address"

**Síntoma:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solución:**

1. Verifica que Tor esté ejecutándose:
   ```bash
   netstat -tuln | grep 9050  # Linux/macOS
   netstat -ano | findstr :9050  # Windows
   ```

2. Si ves LISTEN en puerto 9050, está bien. Si no:
   ```bash
   sudo systemctl start tor  # Linux
   brew services start tor   # macOS
   ```

3. Espera 5-10 segundos y reinicia el script

---

### ❌ Error: "Timeout" o "Remote disconnected"

**Síntoma:**
```
WARNING - Retrying... after connection broken
```

**Solución:**

Esto es normal en Tor, el script reintentar automáticamente. Pero si persiste:

```bash
# Aumentar timeout en tor_downloader.py
TIMEOUT = 60  # Cambiar de 30 a 60
```

O aumentar reintentos:
```bash
MAX_RETRIES = 5  # Cambiar de 3 a 5
```

---

### ❌ "Permission denied" en Linux

**Síntoma:**
```
PermissionError: [Errno 13] Permission denied
```

**Solución:**

```bash
# Cambiar permisos de la carpeta de destino
chmod 755 /ruta/a/carpeta

# O crear carpeta nueva con permisos correctos
mkdir -p ~/files_descargados
chmod 755 ~/files_descargados
```

---

### ❌ Descarga muy lenta

**Posibles causas:**
1. **Conexión lenta a Tor**: Normal, Tor es más lento (500KB-2MB/s típicamente)
2. **Servidor lento**: El sitio onion puede estar saturado
3. **Red congestionada**: Muchos usuarios en Tor

**Soluciones:**
```bash
# Aumentar timeout
TIMEOUT = 60

# Ejecutar en background y dejar ejecutándose
nohup python tor_downloader.py &

# Monitorear progreso
tail -f ~/files_descargados/logs/descarga_*.log
```

---

### ❌ "URL no válida" o ".onion no encontrado"

**Síntoma:**
```
❌ No parece ser una URL onion válida
```

**Solución:**

Verifica que la URL:
1. Empiece con `http://` o `https://`
2. Contenga `.onion`
3. Termine con `/`

Ejemplos correctos:
```
http://ejemplo.onion/
http://ejemplo.onion/carpeta/
https://ejemplo.onion/files/
```

Ejemplos incorrectos:
```
ejemplo.onion/carpeta      # Falta http://
http://ejemplo.com/        # No es .onion
http://ejemplo.onion       # Falta / al final
```

---

## 🔒 Seguridad

### ¿Cómo funciona?

1. **Todo a través de Tor**: Las descargas nunca ven tu IP real
2. **Verificación de integridad**: SHA256 verifica que no fue modificado
3. **Logs locales**: Solo tu computadora tiene registro del proceso
4. **Archivos temporales**: Se eliminan automáticamente

### Buenas Prácticas

✅ Descarga solo desde sitios de confianza
✅ Verifica los checksums SHA256 de los archivos
✅ Mantén Tor actualizado
✅ No uses la misma conexión para actividades no-anónimas
✅ Lee los logs regularmente para detectar problemas

### ⚠️ No es 100% anónimo si:
- Abres los archivos descargados mientras otros servicios están conectados
- Usas la misma conexión sin Tor para otras cosas
- El archivo tiene identificadores únicos internos

---

## �️ Compatibilidad por Plataforma

### Windows
```
✅ Requisitos:
   - Python 3.8+ (descargar desde python.org)
   - Tor Browser O Tor Standalone (desde torproject.org)
   - El script se conecta al puerto 9050
   
⚙️ Pasos:
   1. Instalar Python
   2. Descargar e instalar Tor Browser o Tor Standalone
   3. ABRIR Tor Browser (o ejecutar tor.exe si es standalone)
   4. Seguir pasos de instalación (PASO 2-5)
   5. Ejecutar: python tor_downloader.py
   
✅ Verificación:
   En PowerShell: netstat -an | findstr 9050
   Debe mostrar: TCP 127.0.0.1:9050 ... LISTENING
```

### Linux (Debian/Ubuntu/Fedora/Arch)
```
✅ Requisitos:
   - Python 3.8+
   - Tor (instalable vía apt/dnf/pacman)
   
⚙️ Pasos:
   1. Instalar Tor: sudo apt-get install tor
   2. Iniciar: sudo systemctl start tor
   3. Seguir pasos de instalación (PASO 2-5)
   4. Ejecutar: python tor_downloader.py
   
✅ Verificación:
   netstat -tuln | grep 9050
   Debe mostrar: tcp ... 127.0.0.1:9050 ... LISTEN
```

### macOS
```
✅ Requisitos:
   - Python 3.8+
   - Tor (instalable vía Homebrew o dmg)
   
⚙️ Pasos:
   1. Instalar Tor: brew install tor
   2. Iniciar: brew services start tor
   3. Seguir pasos de instalación (PASO 2-5)
   4. Ejecutar: python tor_downloader.py
   
✅ Verificación:
   netstat -an | grep 9050
   Debe mostrar: tcp4 ... 127.0.0.1.9050 ... LISTEN
```

---

## �📝 Limitaciones Conocidas

| Limitación | Detalles |
|---|---|
| **HTML listable** | Solo funciona si el servidor muestra directorios. No con descargas directas |
| **Velocidad Tor** | Típicamente 500KB-2MB/s, mucho más lento que internet normal |
| **Autenticación** | No soporta usuario/contraseña HTTP |
| **Certificados SSL** | Si el sitio usa HTTPS auto-firmado, puede fallar |
| **Tamaño máximo** | Teóricamente ilimitado, pero limitado por RAM/disco disponible |

---

## 📞 Soporte y Contribuciones

Si encuentras problemas:

1. Revisa la sección "Solución de Problemas"
2. Verifica los logs en `carpeta_destino/logs/`
3. Asegúrate que Tor está ejecutándose

---

## ⚖️ Licencia y Nota Legal

**Este script es una herramienta educativa.** Úsalo responsablemente y dentro del marco legal de tu jurisdicción.

⚠️ El usuario es responsable del contenido descargado y su legalidad.

---

## 🎯 Siguientes Pasos

1. ✅ Instalaste Python
2. ✅ Instalaste Tor
3. ✅ Creaste el entorno virtual
4. ✅ Instalaste dependencias
5. **→ Ahora**: Ejecuta `python tor_downloader.py`

¡Listo para descargar! 🚀

---

**Última actualización**: 2026-07-23  
**Versión**: 1.0  
**Compatible con**: Python 3.8+, Linux, macOS, Windows
