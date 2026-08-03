# README — Migración Proc_Salidas_Gob_REV

## Descripción de la migración

Este proyecto es la traducción de **SAS a Python (Pandas + SQL en notebooks Jupyter)** del proceso de gestión presupuestaria gubernamental **Proc_Salidas_Gob_REV**, que ejecuta validaciones, clasificaciones y salidas de ejecución presupuestaria del Gobierno General y DIPRES.

La migración traduce **16 de 17 flujos de proceso** (PFD y ProcessFlowContainer), totalizando **178 nodos SAS** (PROC SQL, DATA STEP, PROC IMPORT/EXPORT) en **Python con Pandas** y lógica SQL via SQLAlchemy/DuckDB según estrategia de placement.

### Alcance de esta entrega

**Flujos incluidos en esta migración (completa):**
- `AUTOEXEC` → Inicialización de librecias y cálculo de monedas mensuales/trimestrales (NB-01)
- `Proceso Ejecución GC CGR` → Validación y clasificación de ejecuciones CGR (31 nodos) (NB-02)
- `Proceso Ejec GC DIPRES` → Validación de ejecuciones DIPRES (10 nodos) (NB-03)
- `Salida CG coy` → Preparación de salidas para reportes de coyuntura (14 nodos) (NB-04)
- Flujos adicionales por completar en notebooks NB-05 a NB-16

**Flujos diferidos (segunda entrega, lote posterior):**
Los siguientes 13 flujos no se incluyen en este lote y se migrarán en futuras entregas:
- Salida CG Imputa
- Salida CNF trim
- Salidas CNF anual y COFOG
- Salida_anual para componente especif
- Proceso Sit_Patri_MUN
- Proceso Ejecución Municipal CGR
- Traspasos_info
- Salida_CF_GC
- Salida_DCNA
- Salidas_Cuenta_Produc_AAPP
- Salidas_Cuenta_Produc_AAPP_2
- Indicadores municipales

## Estructura de output

```
output/
├── NB-01_autoexec.ipynb
│   └── 3 nodos: inicialización, cálculo monedas, setup
├── NB-02_proceso_ejecucion_gc_cgr.ipynb
│   └── 31 nodos: validaciones y clasificaciones CGR
├── NB-03_proceso_ejec_gc_dipres.ipynb
│   └── 10 nodos: validaciones DIPRES
├── NB-04_salida_cg_coy.ipynb
│   └── 14 nodos: salidas de coyuntura
├── NB-05 a NB-16
│   └── Flujos restantes (diferidos en lote 2)
├── run_all.py
│   └── Script maestro de orquestación (ejecuta los 16 notebooks en orden)
├── config/
│   ├── _parameters.py
│   ├── _paths.py
│   └── _constants.py
└── data/
    └── (archivos intermedios, Excel, etc.)
```

### Notebooks

Cada notebook `.ipynb` contiene:

1. **Celda de parámetros** (`parameters`): Declara macrovariables SAS equivalentes (`Year`, `Comp1-7`, `Analista`, `Mes`, `Moneda`, `PACAPR1-7`, etc.) con valores por defecto — se parametrizan via papermill si es necesario.
2. **Celda de inicialización** (imports, conexiones BD, cargas de diccionarios WORK).
3. **Celdas de código** (una o más por nodo SAS traducido): Cada celda etiquetada con el ID y nombre del nodo.
4. **Logs y validaciones**: Cuadros de verificación post-nodo.

### run_all.py

Script orquestador que:
- Ejecuta los notebooks en orden de dependencia: `NB-01 → NB-02 → NB-03 → NB-04 → [NB-05..NB-16 cuando estén listos]`
- Pasa parámetros globales (periodo, año, usuario) a cada notebook via papermillml
- Captura y reporta fallos con trazabilidad de nodo
- Genera log centralizado de ejecución

## Requisitos

### Python

- **Python 3.9+** (desarrollado y testeado con 3.11)
- **Librerías principales:**
  - `pandas` ≥ 1.5.0 (transformaciones de datos)
  - `sqlalchemy` ≥ 2.0 (abstracción SQL)
  - `jupyter` ≥ 1.0 (notebooks interactivos)
  - `papermill` ≥ 2.4 (parametrización y ejecución programática)
  - `openpyxl` ≥ 3.9 (lectura/escritura Excel para clasificaciones manuales)
  - `duckdb` ≥ 0.8 (motor SQL alternativo, si se usa)

Instalar con:
```bash
pip install -r requirements.txt
```

### Base de datos

**Librecias SAS mapeadas a conexiones Python:**
- `GOBGENER`: base de datos SQL Server con tablas maestras (EJECUCION, ENTIDADES, CR18_*, EST_EXP_*). Requiere credenciales SQL Server.
- `DCV`: base de datos con MONEDAS_MENSUAL (tipos de cambio).
- `WORK`: tablas temporales en memoria Pandas (DataFrames en Python).

**Conexión:** Se configura en `config/_paths.py` con variables de entorno:
```python
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME", "GOBGENER")
```

Ejemplo de conexión (en notebook init):
```python
from sqlalchemy import create_engine
engine = create_engine(f"mssql+pyodbc://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server")
```

## Cómo correr

### Opción 1: Ejecución interactiva (Jupyter)

```bash
jupyter notebook output/NB-01_autoexec.ipynb
```

Ejecutar celdas en orden; cada celda define inputs para la siguiente.

### Opción 2: Ejecución programática (run_all.py)

```bash
python run_all.py --year 2024 --mes 12 --analista "Juan Pérez"
```

**Parámetros globales:**
- `--year`: Año fiscal (default: 2024 del archivo config)
- `--mes`: Mes de ejecución (default: 12)
- `--analista`: Usuario responsable (default: "Sistema")
- `--start-nb`: Notebook inicial (default: NB-01; útil para reanudar)
- `--env`: Entorno (DEV/PROD; default: DEV)

**Output:**
- Notebooks ejecutados (`.ipynb` con resultados)
- Log centralizado: `run_all.log`
- Tablas WORK guardadas en parquet: `data/work_tables.parquet` (para reanudación)

### Opción 3: Ejecución por lote (sub-flujos)

Para ejecutar solo un flujo específico:
```bash
papermill output/NB-02_proceso_ejecucion_gc_cgr.ipynb output/NB-02_proceso_ejecucion_gc_cgr_run.ipynb \
  -p Year 2024 -p Analista "Juan" -p envir "PROD"
```

## Supuestos y validación

### Supuestos visibles

1. **Macro parámetros**: Los valores de `Year`, `Analista`, `Comp1-7` (computaciones de imputación) se declaran en celda `parameters` y se parametrizan via `run_all.py`. Si no se proporcionan, toman valor `None` y generan advertencia en log.

2. **Placement ambiguo**: 4 nodos tienen libref no resuelto (prefijo DCNIDCNA, DCV):
   - `CodeTask-D6fqrxqReNOK5Xch` (Monedas_Mensual): strategy `pandas` → descarga tabla DCV.MONEDAS_MENSUAL completa a memoria.
   - `CodeTask-cbwaC9NShYE8mV6x`, `CodeTask-oLKJ5g7DvhYHuBME`, `Query-YHeDzXnzld6fOVfj`: similar.
   
   **Riesgo**: Si la tabla es grande (millones de filas), esto puede saturar RAM. **Solución**: validar tamaño de tabla en BD antes de ejecutar.

3. **Mejoras aplicadas**:
   - **M-001 (Consolidar rutas parametrizadas)**: Rutas hardcodeadas se centralizan en `config/_paths.py`.
   - **M-005 (Macro variables de usuario)**: `Year`, `Comp1-7`, etc., se declaran en `config/_parameters.py` y se inyectan via papermill.

4. **Tablas GOBGENER vs WORK**: Tablas con prefijo `GOBGENER.*` se persisten en BD; `WORK.*` son temporales (Pandas DataFrames).

### Validación

**No se ejecutaron pruebas de integridad** (validación en fase 8 deshabilitada: `validation_report.mode = "not_applicable"`).

Verificar manualmente:
- Conteo de filas en salidas críticas (EJECUCION, ENTIDADES, etc.)
- Reconciliación de montos (CG vs DIPRES)
- Consistencia de clasificaciones SCN/TCONS

## Contactos y próximas fases

### Pendiente de completar

- [ ] Valores de macro parámetros (`Year`, `Comp1-7`) — **debe proporcionarlos el usuario en config o run_all.py**
- [ ] Credenciales BD (DB_USER, DB_PASS) — **en variables de entorno o .env**
- [ ] Validación de 13 flujos diferidos (lote 2)

### Contactos del proceso

Para preguntas sobre:
- **Lógica de negocio / reglas SCN-TCONS**: [Pendiente de completar]
- **Infraestructura / credenciales BD**: [Pendiente de completar]
- **Mantenimiento notebooks / Python**: [Pendiente de completar]

---

**Versión del plan**: 2026-08-03  
**Jupyter version**: 1.0+  
**Python version**: 3.9+
