#!/usr/bin/env python3
"""Ejecuta todos los notebooks en orden topológico.

ADVERTENCIA: los notebooks escriben en SQL Server (ver state/db_connections.yaml).
Ejecutar este script carga datos reales en el servidor configurado. La escritura
es idempotente por periodo (DELETE+INSERT), pero corre con conocimiento del usuario.

Generado por gen_run_all.py — no editar a mano; volver a correr el generador.
"""
import argparse, os, subprocess, sys

NOTEBOOKS = [
    'NB-02_proceso_ejecucion_gc_cgr.ipynb',
    'NB-03_proceso_ejec_gc_dipres.ipynb',
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--notebooks', nargs='*',
                        help='Ejecutar solo estos notebooks (para re-validación parcial)')
    args = parser.parse_args()

    targets = args.notebooks or NOTEBOOKS
    results = {}
    for nb in targets:
        if not os.path.exists(nb):
            print(f'⚠ {nb} no encontrado, saltando')
            results[nb] = 'SKIPPED'
            continue
        print(f'▶ Ejecutando {nb}...')
        rc = subprocess.run(
            ['jupyter', 'nbconvert', '--to', 'notebook', '--execute', nb,
             '--ExecutePreprocessor.timeout=600', '--output', nb],
            capture_output=True, text=True
        )
        if rc.returncode == 0:
            print(f'  ✓ {nb} OK')
            results[nb] = 'PASS'
        else:
            print(f'  ✗ {nb} FALLÓ')
            print(rc.stderr[-500:] if rc.stderr else 'Sin detalle')
            results[nb] = 'FAIL'

    passed = sum(1 for v in results.values() if v == 'PASS')
    failed = sum(1 for v in results.values() if v == 'FAIL')
    print(f'\nResultado: {passed} OK, {failed} fallidos')
    sys.exit(1 if failed > 0 else 0)

if __name__ == '__main__':
    main()
