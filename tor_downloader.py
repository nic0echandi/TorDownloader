#!/usr/bin/env python3
"""
Descargador recursivo de archivos desde directorios HTML listables en Tor.
Verifica integridad mediante checksum, reintentos automáticos y logging detallado.
"""

import os
import sys
import logging
import hashlib
import time
import json
import tempfile
import shutil
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# Configuración
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

MAX_RETRIES = 3
TIMEOUT = 30
CHUNK_SIZE = 8192

# Configuración para reanudación de descargas (FASE 2)
MIN_RANGE_SIZE = 1024 * 1024  # 1MB mínimo para usar Range requests
RANGE_TIMEOUT = 10  # Timeout para detectar soporte Range

# Valores por defecto (pueden ser sobrescritos por el usuario)
DEFAULT_DESTINATION_DIR = Path("/home/user/Documents/files_descargados")


def get_user_inputs():
    """Obtener URL base y directorio destino del usuario."""
    print("\n" + "=" * 70)
    print("DESCARGADOR DE ARCHIVOS DESDE TOR")
    print("=" * 70 + "\n")
    
    # Preguntar URL
    while True:
        url_input = input(
            "📍 Ingresa la URL onion base "
            "(ej: http://xxxxx.onion/carpeta/): "
        ).strip()
        
        if not url_input:
            print("❌ La URL no puede estar vacía\n")
            continue
        
        # Validar formato básico
        if not url_input.startswith(("http://", "https://")):
            url_input = "http://" + url_input
        
        if ".onion" not in url_input:
            print("❌ No parece ser una URL onion válida (.onion no encontrado)\n")
            continue
        
        # Asegurar que termina con /
        if not url_input.endswith("/"):
            url_input += "/"
        
        BASE_URL = url_input
        print(f"✓ URL configurada: {BASE_URL}\n")
        break
    
    # Preguntar directorio destino
    while True:
        dest_input = input(
            f"📁 Directorio destino "
            f"[{DEFAULT_DESTINATION_DIR}]: "
        ).strip()
        
        if not dest_input:
            DESTINATION_DIR = DEFAULT_DESTINATION_DIR
        else:
            # Expandir ~ si está presente
            DESTINATION_DIR = Path(dest_input).expanduser()
        
        # Validar que la ruta sea válida
        try:
            # Intentar crear el directorio
            DESTINATION_DIR.mkdir(parents=True, exist_ok=True)
            
            # Verificar permisos de escritura
            test_file = DESTINATION_DIR / ".write_test"
            test_file.touch()
            test_file.unlink()
            
            print(f"✓ Directorio configurado: {DESTINATION_DIR}\n")
            break
        
        except PermissionError:
            print(f"❌ Sin permisos de escritura en: {DESTINATION_DIR}\n")
            continue
        except Exception as e:
            print(f"❌ Error al crear directorio: {e}\n")
            continue
    
    return BASE_URL, DESTINATION_DIR


# Obtener inputs del usuario
BASE_URL, DESTINATION_DIR = get_user_inputs()

# Configurar logging
LOG_DIR = DESTINATION_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"descarga_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class StateManager:
    """
    FASE 1: Gestor de persistencia de estado para reanudación de descargas.
    Guarda y carga estado JSON para permitir reanudar descargas interrumpidas.
    """
    
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "download_state.json"
        self.backup_file = self.state_dir / "download_state.backup.json"
    
    def load_state(self) -> Dict:
        """Cargar estado desde archivo JSON. FASE 1."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                logger.info(f"📂 Estado previo cargado: {len(state.get('downloaded_files', {}))} archivos")
                return state
            except Exception as e:
                logger.warning(f"⚠️ Error al cargar estado: {e}")
                # Intentar cargar backup
                if self.backup_file.exists():
                    try:
                        with open(self.backup_file, 'r') as f:
                            state = json.load(f)
                        logger.info("📂 Estado recuperado desde backup")
                        return state
                    except Exception as e2:
                        logger.error(f"❌ No se pudo recuperar backup: {e2}")
        
        return self._create_empty_state()
    
    def _create_empty_state(self) -> Dict:
        """Crear estructura de estado vacía."""
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
            "downloaded_files": {},  # {local_path: {size, sha256, url, status}}
            "failed_files": {},      # {url: {attempts, last_error}}
            "directory_index": {},   # {url: list_of_files}
            "directory_hash": ""     # Hash de estructura para detectar cambios
        }
    
    def save_state(self, state: Dict) -> bool:
        """
        Guardar estado de forma atómica (FASE 3).
        Usa archivo temporal + rename para evitar corrupción.
        """
        try:
            # Crear backup del estado anterior
            if self.state_file.exists():
                shutil.copy2(self.state_file, self.backup_file)
            
            # Escribir a archivo temporal
            with tempfile.NamedTemporaryFile(
                mode='w', 
                dir=self.state_dir, 
                suffix='.tmp', 
                delete=False
            ) as tmp:
                json.dump(state, tmp, indent=2)
                tmp_path = tmp.name
            
            # Rename atómico (FASE 3)
            Path(tmp_path).replace(self.state_file)
            logger.debug(f"💾 Estado guardado: {len(state['downloaded_files'])} archivos")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error al guardar estado: {e}")
            return False
    
    def mark_file_downloaded(self, state: Dict, local_path: str, file_url: str, 
                            size: int, sha256: str) -> None:
        """Marcar archivo como descargado. FASE 1."""
        state['downloaded_files'][local_path] = {
            'size': size,
            'sha256': sha256,
            'url': file_url,
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        }
        # Limpiar de failed si estaba
        state['failed_files'].pop(file_url, None)
    
    def mark_file_failed(self, state: Dict, file_url: str, error: str, attempts: int) -> None:
        """Marcar archivo como fallido. FASE 1."""
        state['failed_files'][file_url] = {
            'attempts': attempts,
            'last_error': error,
            'timestamp': datetime.now().isoformat()
        }
    
    def is_file_downloaded(self, state: Dict, local_path: str) -> bool:
        """Verificar si archivo ya está descargado. FASE 1."""
        return local_path in state['downloaded_files']
    
    def get_downloaded_sha256(self, state: Dict, local_path: str) -> Optional[str]:
        """Obtener SHA256 guardado de archivo. FASE 1."""
        return state['downloaded_files'].get(local_path, {}).get('sha256')
    
    def update_directory_hash(self, state: Dict, directory_hash: str) -> None:
        """Actualizar hash de estructura de directorios. FASE 3."""
        state['directory_hash'] = directory_hash
    
    def has_structure_changed(self, state: Dict, new_hash: str) -> bool:
        """Detectar si estructura de directorios cambió. FASE 3."""
        return state.get('directory_hash') != new_hash


class RangeDownloadHelper:
    """
    FASE 2: Gestor de descargas con soporte HTTP Range.
    Detecta si servidor soporta Range requests y reanuda descargas.
    """
    
    def __init__(self, session: requests.Session):
        self.session = session
        self.range_support_cache = {}  # {url: bool} - Cache de soporte Range
    
    def supports_range_requests(self, file_url: str) -> bool:
        """
        Detectar si servidor soporta HTTP Range requests (FASE 2).
        Retorna True si soporta, False si no.
        """
        if file_url in self.range_support_cache:
            return self.range_support_cache[file_url]
        
        try:
            # Hacer HEAD request con Range para detectar soporte
            response = self.session.head(
                file_url, 
                headers={'Range': 'bytes=0-0'},
                timeout=RANGE_TIMEOUT,
                allow_redirects=False
            )
            
            # Código 206 = Partial Content (soporta Range)
            # Código 200 = OK pero ignora Range (no soporta)
            supports = response.status_code == 206
            self.range_support_cache[file_url] = supports
            
            logger.debug(
                f"Range support para {file_url}: "
                f"{supports} (HTTP {response.status_code})"
            )
            return supports
        
        except Exception as e:
            logger.debug(f"Error detectando Range support: {e}")
            self.range_support_cache[file_url] = False
            return False
    
    def get_remote_size(self, file_url: str) -> Optional[int]:
        """
        Obtener tamaño de archivo remoto. Útil para validar antes de reanudar.
        FASE 2.
        """
        try:
            response = self.session.head(file_url, timeout=RANGE_TIMEOUT)
            if 'content-length' in response.headers:
                return int(response.headers['content-length'])
        except Exception as e:
            logger.debug(f"Error obteniendo tamaño remoto: {e}")
        
        return None
    
    def validate_partial_file(self, temp_path: Path, file_url: str, 
                             expected_size: int) -> bool:
        """
        Validar que archivo temporal es válido para reanudar (FASE 3).
        - Tamaño no mayor a esperado
        - Archivo no corrupto
        """
        if not temp_path.exists():
            return False
        
        try:
            temp_size = temp_path.stat().st_size
            
            # Validación básica: no puede ser mayor que lo esperado
            if temp_size > expected_size:
                logger.warning(
                    f"Archivo temporal corrupto: {temp_size} > {expected_size}"
                )
                return False
            
            # Si está completo, no es temporal
            if temp_size == expected_size:
                logger.debug(f"Archivo temporal ya está completo: {temp_path}")
                return True
            
            # Validación: intentar leer últimos bytes
            try:
                with open(temp_path, 'rb') as f:
                    f.seek(-min(1024, temp_size), 2)  # Leer últimos 1KB
                    f.read()
                return True
            except Exception as e:
                logger.warning(f"Archivo temporal no legible: {e}")
                return False
        
        except Exception as e:
            logger.warning(f"Error validando archivo temporal: {e}")
            return False
    
    def download_with_range(self, file_url: str, temp_path: Path, 
                          session: requests.Session, 
                          offset: int = 0) -> Tuple[bool, int]:
        """
        Descargar archivo con soporte Range (FASE 2).
        
        Retorna: (success, bytes_written)
        """
        try:
            headers = {}
            if offset > 0:
                headers['Range'] = f'bytes={offset}-'
                logger.info(f"Reanudando desde byte {offset}")
            
            response = session.get(
                file_url,
                headers=headers,
                timeout=TIMEOUT,
                stream=True
            )
            
            # Validar respuesta
            if offset > 0 and response.status_code != 206:
                logger.warning(
                    f"Servidor no soporta Range (esperado 206, obtuvo {response.status_code})"
                )
                return False, 0
            elif response.status_code not in [200, 206]:
                logger.error(f"Error HTTP {response.status_code}")
                return False, 0
            
            # Descargar en modo append si hay offset
            file_mode = 'ab' if offset > 0 else 'wb'
            bytes_written = 0
            
            with open(temp_path, file_mode) as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        bytes_written += len(chunk)
            
            return True, bytes_written
        
        except Exception as e:
            logger.error(f"Error descargando con Range: {e}")
            return False, 0


class TorDownloader:
    """Gestor de descargas desde Tor con reintentos, verificación de integridad y reanudación."""
    
    def __init__(self, base_url: str, dest_dir: Path, tor_proxy: Dict):
        self.base_url = base_url.rstrip('/')
        self.dest_dir = dest_dir
        self.tor_proxy = tor_proxy
        self.session = self._create_session()
        
        # FASE 1 y 3: Manager de estado y validación
        self.state_manager = StateManager(self.dest_dir / ".download_state")
        self.state = self.state_manager.load_state()
        
        # FASE 2: Helper para Range requests
        self.range_helper = RangeDownloadHelper(self.session)
        
        # Estadísticas
        self.stats = {
            'total_files': 0,
            'downloaded': 0,
            'failed': 0,
            'resumed': 0,  # Archivos reanudados
            'total_size': 0,
            'errors': []
        }
    
    def _create_session(self) -> requests.Session:
        """Crear sesión con reintentos automáticos."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configurar proxy Tor
        session.proxies.update(self.tor_proxy)
        
        # Header para evitar bloqueos
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        return session
    
    def _format_size(self, bytes_size: int) -> str:
        """Convertir bytes a formato legible (KB, MB, GB)."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f}{unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f}PB"
    
    def _format_progress_bar(self, current: int, total: int, width: int = 30) -> str:
        """Crear barra de progreso visual."""
        if total == 0:
            return "[" + "=" * width + "]  0%"
        
        percent = current / total
        filled = int(width * percent)
        bar = "=" * filled + "-" * (width - filled)
        percentage = f"{percent * 100:.1f}%"
        
        return f"[{bar}] {percentage:>5}"
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calcular SHA256 de un archivo."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _get_files_from_directory(self, url: str) -> Tuple[List[str], List[str]]:
        """
        Obtener lista de archivos y carpetas de un directorio HTML listable.
        Retorna (archivos, carpetas)
        """
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            files = []
            directories = []
            
            for link in soup.find_all('a', href=True):
                href = link.get('href').strip()
                text = link.get_text().strip()
                
                # Ignorar enlaces especiales
                if href in ['..', '/', '.']:
                    continue
                
                # Ignorar texto vacío
                if not text or text in ['[ICO]', '[PARENTDIR]']:
                    continue
                
                # Detectar carpetas (terminan en /)
                if href.endswith('/'):
                    directories.append(href)
                else:
                    files.append(href)
            
            return files, directories
        
        except requests.RequestException as e:
            logger.error(f"Error al acceder a {url}: {e}")
            self.stats['errors'].append(f"Acceso a directorio: {url} - {e}")
            return [], []
    
    def _download_file(self, file_url: str, dest_path: Path) -> bool:
        """
        Descargar archivo con soporte para reanudación (FASES 1, 2, 3).
        - FASE 1: Detecta archivos ya descargados
        - FASE 2: Usa HTTP Range si servidor lo soporta
        - FASE 3: Valida integridad y recupera de corrupción
        """
        # FASE 1: Verificar si ya está descargado
        local_path_str = str(dest_path.relative_to(self.dest_dir))
        if self.state_manager.is_file_downloaded(self.state, local_path_str):
            if dest_path.exists():
                logger.info(f"⏭️  Saltando (ya descargado): {dest_path.name}")
                self.stats['downloaded'] += 1
                return True
            else:
                logger.info(f"🔄 Archivo registrado pero no existe, descargando: {dest_path.name}")
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = dest_path.with_suffix(dest_path.suffix + '.tmp')
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # FASE 2: Detectar soporte Range y obtener tamaño remoto
                remote_size = self.range_helper.get_remote_size(file_url)
                supports_range = False
                offset = 0
                
                if remote_size and remote_size > MIN_RANGE_SIZE:
                    supports_range = self.range_helper.supports_range_requests(file_url)
                
                # FASE 3: Validar archivo temporal si existe
                if temp_path.exists() and supports_range and remote_size:
                    is_valid = self.range_helper.validate_partial_file(
                        temp_path, file_url, remote_size
                    )
                    if is_valid:
                        offset = temp_path.stat().st_size
                        logger.info(
                            f"📥 Reanudando: {dest_path.name} "
                            f"({self._format_size(offset)}/{self._format_size(remote_size)})"
                        )
                        self.stats['resumed'] += 1
                    else:
                        logger.warning(f"Archivo temporal corrupto, reiniciando: {dest_path.name}")
                        temp_path.unlink(missing_ok=True)
                        offset = 0
                
                logger.info(f"Descargando: {file_url}")
                
                # Descargar con Range si es posible
                if supports_range and offset > 0:
                    success, bytes_written = self.range_helper.download_with_range(
                        file_url, temp_path, self.session, offset
                    )
                    if success:
                        file_size = temp_path.stat().st_size
                    else:
                        # Fallback: descargar completo si Range falla
                        temp_path.unlink(missing_ok=True)
                        raise Exception("Range download failed, falling back to full download")
                else:
                    # Descarga normal sin Range
                    response = self.session.get(file_url, timeout=TIMEOUT, stream=True)
                    response.raise_for_status()
                    
                    total_size = 0
                    if 'content-length' in response.headers:
                        total_size = int(response.headers['content-length'])
                    
                    file_size = 0
                    start_time = time.time()
                    last_log_size = 0
                    
                    with open(temp_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            if chunk:
                                f.write(chunk)
                                file_size += len(chunk)
                                
                                elapsed = time.time() - start_time
                                if elapsed > 0:
                                    speed = file_size / elapsed
                                    downloaded = self._format_size(file_size)
                                    speed_str = self._format_size(speed)
                                    should_update = (file_size - last_log_size) >= (100 * 1024)
                                    
                                    if total_size > 0:
                                        remaining = total_size - file_size
                                        eta = remaining / speed if speed > 0 else 0
                                        progress_bar = self._format_progress_bar(file_size, total_size)
                                        total = self._format_size(total_size)
                                        
                                        if should_update or file_size >= total_size:
                                            progress_text = (
                                                f"{progress_bar} {downloaded}/{total} "
                                                f"({speed_str}/s) ETA: {int(eta)}s"
                                            )
                                            print(f"\r{progress_text}", end='', flush=True)
                                            last_log_size = file_size
                                    else:
                                        if should_update:
                                            progress_text = f"[====>] {downloaded} ({speed_str}/s)"
                                            print(f"\r{progress_text}", end='', flush=True)
                                            last_log_size = file_size
                    
                    if last_log_size > 0:
                        print()
                    
                    if total_size > 0 and file_size != total_size:
                        raise ValueError(
                            f"Tamaño incorrecto: esperado {total_size}, obtenido {file_size}"
                        )
                
                # Validación final y renombre
                temp_path.rename(dest_path)
                
                elapsed = time.time() - start_time
                sha256 = self._calculate_sha256(dest_path)
                
                # FASE 1: Guardar estado de archivo descargado
                self.state_manager.mark_file_downloaded(
                    self.state, local_path_str, file_url, file_size, sha256
                )
                self.state_manager.save_state(self.state)
                
                self.stats['downloaded'] += 1
                self.stats['total_size'] += file_size
                
                logger.info(
                    f"✓ {dest_path.name} ({self._format_size(file_size)}) "
                    f"en {elapsed:.1f}s ({self._format_size(file_size/elapsed)}/s) "
                    f"SHA256: {sha256[:16]}..."
                )
                
                return True
            
            except Exception as e:
                logger.warning(
                    f"Intento {attempt}/{MAX_RETRIES} fallido para {file_url}: {e}"
                )
                if attempt == MAX_RETRIES:
                    logger.error(f"✗ Falló después de {MAX_RETRIES} intentos: {file_url}")
                    self.stats['failed'] += 1
                    
                    # FASE 1: Guardar en registro de fallidos
                    self.state_manager.mark_file_failed(self.state, file_url, str(e), attempt)
                    self.state_manager.save_state(self.state)
                    
                    self.stats['errors'].append(f"{file_url} - {str(e)}")
                    temp_path.unlink(missing_ok=True)
                    return False
                
                # No eliminar .tmp en fallos intermedios si Range estaba activo
                # Esto permite reanudar en siguiente intento
                if not (supports_range and temp_path.exists()):
                    temp_path.unlink(missing_ok=True)
                
                time.sleep(2 ** attempt)
        
        return False
    
    def _crawl_directory(self, dir_url: str, local_path: Path) -> None:
        """Explorar recursivamente un directorio."""
        logger.info(f"Explorando: {dir_url}")
        
        files, directories = self._get_files_from_directory(dir_url)
        
        # Descargar archivos
        for file_name in files:
            self.stats['total_files'] += 1
            file_url = urljoin(dir_url, file_name)
            file_dest = local_path / file_name
            self._download_file(file_url, file_dest)
        
        # Explorar subdirectorios recursivamente
        for dir_name in directories:
            subdir_url = urljoin(dir_url, dir_name)
            subdir_path = local_path / dir_name.rstrip('/')
            self._crawl_directory(subdir_url, subdir_path)
    
    def start_download(self) -> None:
        """Iniciar descarga completa."""
        logger.info("=" * 70)
        logger.info(f"INICIANDO DESCARGA DESDE TOR")
        logger.info(f"URL: {self.base_url}")
        logger.info(f"Destino: {self.dest_dir}")
        logger.info(f"Proxy: {self.tor_proxy.get('http', 'N/A')}")
        logger.info("=" * 70)
        
        self.dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Mostrar resumen del estado previo si hay
        if self.state.get('downloaded_files'):
            logger.info(f"📂 Reanudando: {len(self.state['downloaded_files'])} archivos previos")
        
        start_time = time.time()
        self._crawl_directory(self.base_url + '/', self.dest_dir)
        elapsed_time = time.time() - start_time
        
        # Guardar estado final
        self.state['status'] = 'completed' if self.stats['failed'] == 0 else 'partial'
        self.state_manager.save_state(self.state)
        
        self._print_summary(elapsed_time)
    
    def _print_summary(self, elapsed_time: float) -> None:
        """Mostrar resumen de descarga con estadísticas de reanudación."""
        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN DE DESCARGA")
        logger.info("=" * 70)
        logger.info(f"Total de archivos encontrados: {self.stats['total_files']}")
        logger.info(f"Archivos descargados exitosamente: {self.stats['downloaded']}")
        logger.info(f"Archivos reanudados (Range): {self.stats['resumed']}")  # FASE 2
        logger.info(f"Archivos fallidos: {self.stats['failed']}")
        logger.info(f"Tamaño total descargado: {self._format_size(self.stats['total_size'])}")
        logger.info(f"Tiempo total: {self._format_time(elapsed_time)}")
        logger.info(f"Velocidad promedio: {self._format_speed(self.stats['total_size'], elapsed_time)}")
        
        # FASE 1 y 3: Información de persistencia
        logger.info(f"\n📊 ESTADÍSTICAS DE PERSISTENCIA:")
        logger.info(f"  Archivos en caché: {len(self.state.get('downloaded_files', {}))}")
        logger.info(f"  Archivos fallidos registrados: {len(self.state.get('failed_files', {}))}")
        logger.info(f"  Estado guardado: {self.state.get('status', 'unknown')}")
        
        if self.stats['errors']:
            logger.info("\nERRORES ENCONTRADOS:")
            for error in self.stats['errors']:
                logger.info(f"  - {error}")
        
        logger.info(f"\n💾 Archivo de log: {LOG_FILE}")
        logger.info(f"📂 Estado persistente: {self.state_manager.state_dir}")
        logger.info("=" * 70 + "\n")
    
    @staticmethod
    def _format_size(bytes_size: int) -> str:
        """Formato legible para tamaño de archivo."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} PB"
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Formato legible para tiempo."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m"
        else:
            return f"{seconds / 3600:.1f}h"
    
    @staticmethod
    def _format_speed(bytes_size: int, seconds: float) -> str:
        """Formato legible para velocidad de descarga."""
        if seconds == 0:
            return "N/A"
        speed = bytes_size / seconds
        return TorDownloader._format_size(int(speed)) + "/s"


def verify_tor_connection(tor_proxy: Dict, port: int = 9050) -> bool:
    """Verificar conexión a Tor. Retorna True si está conectado."""
    logger.info(f"Verificando conexión a Tor en puerto {port}...")
    
    if not tor_proxy:
        # Si no hay proxy, asumir que está bien
        return True
    
    # Intentar con múltiples sitios (fallback)
    test_urls = [
        'http://check.torproject.org',
        'http://www.torproject.org',
        'http://ipv4.icanhazip.com',  # Simple IP check
    ]
    
    for url in test_urls:
        try:
            session = requests.Session()
            session.proxies.update(tor_proxy)
            response = session.get(url, timeout=10)
            
            # Si cualquiera de estos sitios responde, consideramos que Tor funciona
            if response.status_code == 200:
                logger.info(f"✓ Conexión a Tor verificada ({url})")
                return True
        except Exception as e:
            logger.debug(f"Intento con {url} falló: {e}")
            continue
    
    # Si ninguno funcionó, intentar una conexión directa al puerto SOCKS
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            logger.info(f"✓ Puerto {port} está abierto y escuchando (asumiendo Tor funciona)")
            return True
    except Exception as e:
        logger.debug(f"Error al verificar puerto: {e}")
    
    return False


def ask_tor_options():
    """Preguntar opciones de Tor si no está disponible."""
    global TOR_PROXY
    
    print("\n" + "=" * 70)
    print("⚠️  PROBLEMA CON LA CONEXIÓN A TOR")
    print("=" * 70 + "\n")
    
    print("Opciones disponibles:")
    print("1. Instalar Tor (ver instrucciones)")
    print("2. Especificar puerto Tor diferente")
    print("3. Continuar SIN Tor (⚠️  no recomendado, menos seguro)")
    print("0. Cancelar\n")
    
    choice = input("Selecciona una opción (0-3): ").strip()
    
    if choice == "1":
        print("\n📖 INSTRUCCIONES DE INSTALACIÓN:")
        print("\n▶ Ubuntu/Debian:")
        print("  sudo apt-get update")
        print("  sudo apt-get install -y tor")
        print("  sudo systemctl start tor")
        print("\n▶ Fedora/RHEL:")
        print("  sudo dnf install -y tor")
        print("  sudo systemctl start tor")
        print("\n▶ Arch:")
        print("  sudo pacman -S tor")
        print("  sudo systemctl start tor")
        print("\n▶ macOS:")
        print("  brew install tor")
        print("  brew services start tor")
        print("\nO ejecuta: bash /home/user/Documents/ransome/install_tor.sh\n")
        return False
    
    elif choice == "2":
        port_input = input("\n¿Qué puerto usa tu Tor? (default 9050): ").strip()
        if port_input and port_input.isdigit():
            port = int(port_input)
            TOR_PROXY = {
                'http': f'socks5://127.0.0.1:{port}',
                'https': f'socks5://127.0.0.1:{port}'
            }
            print(f"\n✓ Puerto actualizado a {port}")
            
            if verify_tor_connection(TOR_PROXY, port):
                print("✓ Conexión verificada\n")
                return True
            else:
                print("❌ No se puede conectar al puerto especificado\n")
                return False
        else:
            print("❌ Puerto inválido\n")
            return False
    
    elif choice == "3":
        print("\n" + "=" * 70)
        print("⚠️  ADVERTENCIA DE SEGURIDAD")
        print("=" * 70)
        print("\nSi continúas sin Tor:")
        print("  • Tu dirección IP será visible")
        print("  • No habrá privacidad de navegación")
        print("  • El contenido descargado no estará cifrado")
        print("\nUSO SOLO PARA TESTING O ARCHIVOS PÚBLICOS\n")
        print("=" * 70 + "\n")
        
        response = input("¿Continuar sin Tor? [s/n]: ").strip().lower()
        if response in ['s', 'si', 'yes', 'y']:
            print("\n⚠️  Continuando SIN Tor\n")
            # Usar un proxy vacío (sin Tor)
            TOR_PROXY = {}
            return True
        else:
            print("Cancelado\n")
            return False
    
    else:
        print("Cancelado\n")
        return False


def main():
    """Función principal."""
    global TOR_PROXY
    
    try:
        # Verificar conexión a Tor
        if not verify_tor_connection(TOR_PROXY):
            if not ask_tor_options():
                logger.error("No se puede continuar sin Tor")
                sys.exit(1)
        
        print("\n" + "=" * 70)
        print("✓ Listo para descargar")
        print("=" * 70 + "\n")
        
        # Iniciar descarga
        downloader = TorDownloader(BASE_URL, DESTINATION_DIR, TOR_PROXY)
        downloader.start_download()
        
        # Retornar código de éxito/fallo
        if downloader.stats['failed'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\n⚠ Descarga cancelada por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
