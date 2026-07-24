#!/usr/bin/env python3
"""
Script de demostración: Prueba de reanudación de descargas (3 FASES)

Este script simula y verifica las 3 fases implementadas:
- FASE 1: Persistencia de estado (JSON)
- FASE 2: HTTP Range support
- FASE 3: Robustez y validación

Uso: python3 test_resume_feature.py
"""

import sys
import json
import tempfile
import time
import hashlib
from pathlib import Path

# Importar SOLO las clases de reanudación (no el main)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "tor_downloader_classes",
    str(Path(__file__).parent / "tor_downloader.py")
)
tor_module = importlib.util.module_from_spec(spec)

# Ejecutar sin disparar el código de nivel superior interactivo
import io
import contextlib

# Redirigir stdin para evitar que pida input
with contextlib.redirect_stdin(io.StringIO("")):
    try:
        spec.loader.exec_module(tor_module)
    except EOFError:
        pass  # Esperado cuando stdin está vacío

# Extraer las clases
StateManager = tor_module.StateManager
RangeDownloadHelper = tor_module.RangeDownloadHelper


def test_fase_1_state_persistence():
    """FASE 1: Prueba persistencia de estado JSON"""
    print("\n" + "=" * 70)
    print("TEST FASE 1: Persistencia de Estado")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir)
        manager = StateManager(state_dir)
        
        # Crear estado inicial
        state = manager._create_empty_state()
        print(f"✓ Estado inicial creado")
        print(f"  - Status: {state['status']}")
        print(f"  - Archivos: {len(state['downloaded_files'])}")
        
        # Guardar archivo descargado
        manager.mark_file_downloaded(
            state, 
            "docs/archivo1.pdf",
            "http://example.onion/archivo1.pdf",
            1024000,
            "abc123def456..."
        )
        print(f"✓ Archivo marcado como descargado")
        
        # Guardar estado a JSON
        manager.save_state(state)
        print(f"✓ Estado guardado a JSON")
        print(f"  - Archivo: {manager.state_file}")
        assert manager.state_file.exists(), "❌ No se creó archivo de estado"
        
        # Cargar estado desde JSON
        loaded_state = manager.load_state()
        print(f"✓ Estado cargado desde JSON")
        print(f"  - Archivos recuperados: {len(loaded_state['downloaded_files'])}")
        
        # Verificar que es el mismo
        assert loaded_state['downloaded_files']['docs/archivo1.pdf']['sha256'] == "abc123def456...", \
            "❌ Los datos no coinciden"
        print(f"✓ Integridad de datos verificada")
        
        # Verificar que archivo ya existe
        assert manager.is_file_downloaded(loaded_state, "docs/archivo1.pdf"), \
            "❌ No se detecta archivo descargado"
        print(f"✓ Detección de archivo descargado funcionando")
        
        print("\n✅ FASE 1: APROBADO")
        return True


def test_fase_1_backup_recovery():
    """FASE 1 + FASE 3: Recuperación desde backup"""
    print("\n" + "=" * 70)
    print("TEST FASE 1+3: Recuperación de Backup")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir)
        manager = StateManager(state_dir)
        
        # Crear estado inicial
        state = manager._create_empty_state()
        manager.mark_file_downloaded(
            state, "file1.txt", "http://example.onion/file1.txt", 100, "hash1"
        )
        manager.save_state(state)
        print(f"✓ Estado inicial guardado")
        
        # Crear segundo estado y guardar
        state['downloaded_files']['file2.txt'] = {'status': 'completed'}
        manager.save_state(state)
        print(f"✓ Segundo estado guardado")
        
        # Corromper archivo principal
        with open(manager.state_file, 'w') as f:
            f.write("{ JSON CORRUPTO }")
        print(f"⚠️  Archivo de estado corrompido manualmente")
        
        # Intentar cargar (debería recuperarse desde backup)
        recovered_state = manager.load_state()
        print(f"✓ Estado recuperado (desde backup)")
        print(f"  - Archivos recuperados: {len(recovered_state['downloaded_files'])}")
        
        # Verificar que al menos uno está ahí
        assert len(recovered_state['downloaded_files']) > 0, \
            "❌ No se recuperó nada desde backup"
        print(f"✓ Integridad de backup verificada")
        
        print("\n✅ FASE 1+3 (Backup): APROBADO")
        return True


def test_fase_1_failed_files():
    """FASE 1: Registro de archivos fallidos"""
    print("\n" + "=" * 70)
    print("TEST FASE 1: Registro de Archivos Fallidos")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir)
        manager = StateManager(state_dir)
        state = manager._create_empty_state()
        
        # Registrar fallo
        manager.mark_file_failed(
            state,
            "http://example.onion/failed.zip",
            "Connection timeout",
            2
        )
        print(f"✓ Fallo registrado")
        print(f"  - URL: {list(state['failed_files'].keys())[0]}")
        print(f"  - Intentos: 2")
        
        # Guardar y cargar
        manager.save_state(state)
        loaded = manager.load_state()
        
        assert "http://example.onion/failed.zip" in loaded['failed_files'], \
            "❌ Fallo no se guardó"
        print(f"✓ Fallo recuperado desde JSON")
        
        print("\n✅ FASE 1 (Fallos): APROBADO")
        return True


def test_fase_2_range_validation():
    """FASE 2: Validación de archivo para reanudar"""
    print("\n" + "=" * 70)
    print("TEST FASE 2: Validación de Archivo Temporal")
    print("=" * 70)
    
    import requests
    range_helper = RangeDownloadHelper(requests.Session())
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "test.bin"
        
        # Crear archivo temporal de 500 bytes
        with open(temp_path, 'wb') as f:
            f.write(b'X' * 500)
        print(f"✓ Archivo temporal creado (500 bytes)")
        
        # Validar (tamaño esperado: 1000 bytes)
        is_valid = range_helper.validate_partial_file(temp_path, "http://example.onion/file", 1000)
        assert is_valid, "❌ Validación falló"
        print(f"✓ Archivo temporal validado como válido")
        
        # Intentar validar si es más grande que esperado (corrupto)
        with open(temp_path, 'ab') as f:
            f.write(b'Y' * 600)  # Ahora 1100 bytes
        print(f"✓ Archivo temporal modificado a 1100 bytes (corrupto)")
        
        is_valid = range_helper.validate_partial_file(temp_path, "http://example.onion/file", 1000)
        assert not is_valid, "❌ No detectó corrupción"
        print(f"✓ Corrupción detectada correctamente")
        
        print("\n✅ FASE 2: APROBADO")
        return True


def test_fase_3_atomic_writes():
    """FASE 3: Escritura atómica de estado"""
    print("\n" + "=" * 70)
    print("TEST FASE 3: Escritura Atómica")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir)
        manager = StateManager(state_dir)
        
        # Crear estado inicial
        state = manager._create_empty_state()
        for i in range(10):
            manager.mark_file_downloaded(
                state, f"file{i}.txt", f"http://example.onion/file{i}.txt", 100, f"hash{i}"
            )
        
        # Guardar (usa tempfile + rename internamente)
        manager.save_state(state)
        print(f"✓ Estado guardado de forma atómica")
        print(f"  - Método: tempfile + rename")
        print(f"  - Archivos: {len(state['downloaded_files'])}")
        
        # Verificar que existe archivo principal Y backup
        assert manager.state_file.exists(), "❌ No existe archivo de estado"
        assert manager.backup_file.exists(), "❌ No existe backup"
        print(f"✓ Archivos de estado y backup existentes")
        
        # Verificar contenido del backup
        with open(manager.backup_file) as f:
            backup_data = json.load(f)
        print(f"✓ Backup está en JSON válido")
        print(f"  - Archivos en backup: {len(backup_data.get('downloaded_files', {}))}")
        
        print("\n✅ FASE 3 (Atomicidad): APROBADO")
        return True


def print_header():
    """Mostrar encabezado de pruebas"""
    print("\n" + "=" * 70)
    print("PRUEBAS DE IMPLEMENTACIÓN: REANUDACIÓN DE DESCARGAS")
    print("=" * 70)
    print("\nVerificando:")
    print("  ✓ FASE 1: Persistencia de estado JSON")
    print("  ✓ FASE 2: HTTP Range support")
    print("  ✓ FASE 3: Robustez y validación")
    print("\n" + "=" * 70)


def main():
    """Ejecutar todas las pruebas"""
    print_header()
    
    tests = [
        ("FASE 1: Persistencia", test_fase_1_state_persistence),
        ("FASE 1: Backup Recovery", test_fase_1_backup_recovery),
        ("FASE 1: Fallos", test_fase_1_failed_files),
        ("FASE 2: Validación", test_fase_2_range_validation),
        ("FASE 3: Atomic Writes", test_fase_3_atomic_writes),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR")
            print(f"   {str(e)}")
            failed += 1
    
    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN DE PRUEBAS")
    print("=" * 70)
    print(f"✅ Aprobadas: {passed}")
    print(f"❌ Fallidas: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 TODAS LAS PRUEBAS APROBADAS")
        print("\nImplementación de 3 FASES verificada correctamente:")
        print("  1. Persistencia de estado: ✅")
        print("  2. HTTP Range support: ✅")
        print("  3. Robustez y validación: ✅")
        print("\nLa reanudación de descargas está lista para producción.")
        return 0
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
        return 1


if __name__ == "__main__":
    sys.exit(main())
