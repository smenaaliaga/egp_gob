# README – Migración Proc_Salidas_Gob_REV_mig-2

## Qué es esta migración

Esta migración traduce un conjunto de **18 Process Flows** del proyecto SAS **Proc_Salidas_Gob_REV_mig-2** a **Jupyter Notebooks con Python**. Los flujos originales procesan información presupuestaria y de ejecución de gasto público del Gobierno General chileno, consolidando datos de fuentes como Contraloría General de la República (CGR), DIPRES y bases de datos de estructura analítica (GOBGENER).

### Alcance de esta entrega

Esta primera entrega incluye la traducción de **18 flujos migratables** de los 19 totales:

- **AUTOEXEC** – Inicialización de librerías y procesamiento de monedas/tipos de cambio
- **Proceso Ejecución GC CGR** – Validación y clasificación de ejecuciones presupuestarias (CGR)
- **Proceso Ejec GC DIPRES** – Validación de estructuras analíticas (DIPRES)
- **Salida CG coy** – Consolidación de ejecución de Gobierno Central de coyuntura (CGR + DIPRES)
- **Salida CG Aper coy** – Ejecución desagregada por apertura institucional (coyuntura)
- **Salida CG Imputa** – Imputaciones y consolidación de transacciones mixtas
- **Salida CNF trim** – Consolidación trimestral de Cuentas Nacionales Financieras
- **Salida_CNF_Trim_CGR** – CNF trimestral con datos CGR
- **Salida_CNF_Trim_DIP** – CNF trimestral con datos DIPRES
- **Salidas CNF anual y COFOG** – Consolidación anual y clasificación COFOG
- **Salida_anual para componente especif_no** – Agregación anual de componentes específicos
- **Proceso Sit_Patri_MUN_no** – Situación patrimonial municipal
- **Proceso Ejecución Municipal CGR_no** – Ejecución municipal (CGR)
- **Traspasos_info** – Procesamiento de traspasos de información
- **Salida_CF_GC** – Cuenta Financiera de Gobierno Central
- **Salida_DCNA** – Salida de Cuentas Nacionales según clasificación DCNA
- **Salidas_Cuenta_Produc_AAPP_no** – Salida de Cuenta de Producción (AAPP)
- **Salidas_Cuenta_Produc_AAPP_2_no** – Salida de Cuenta de Producción (AAPP, segunda parte)

### Flujos diferidos (no incluidos en esta entrega)

El flujo **Indicadores municipales** se traduce en un lote posterior — su traducción depende de validaciones adicionales en tablas municipales y no está incluida en esta versión.

## Qué produce esta migración

### Notebooks Jupyter

Se generan **6 notebooks principales** en la carpeta `output/`:

| Notebook | Flujos | Descripción |
|----------|--------|-------------|
| `NB-01_autoexec.ipynb` | AUTOEXEC | Inicialización: librerías, constantes, lectura y agregación de monedas mensuales en periodos de cierre y promedio |
| `NB-02_proceso_ejecucion_gc_cgr.ipynb` | Proceso Ejecución GC CGR | Validación de cambios nomenclatura, enriquecimiento analítico fijo/variable, validación de estructuras y actividades COFOG |
| `NB-03_proceso_ejec_gc_dipres.ipynb` | Proceso Ejec GC DIPRES | Validación de consistencia analítica DIPRES (entidad, actividad, transferencias) |
| `NB-04_salida_cg_coy.ipynb` | Salida CG coy, Salida CG Aper coy, Salida CG Imputa | Redistribución de transacciones mixtas, consolidación con imputaciones, ejecución total (muestra + expansión) |
| `NB-05_salida_cnf_trim.ipynb` | Salida CNF trim, Salida_CNF_Trim_CGR, Salida_CNF_Trim_DIP | Consolidación trimestral de Cuentas Nacionales Financieras por fuente |
| `NB-06_salidas_adicionales.ipynb` | Salida anual CNF, COFOG, situación patrimonial municipal, ejecución municipal, traspasos, CF_GC, DCNA, Cuenta Producción | Reportes anuales y especializados de análisis coyuntural y estructural |

### Tablas y archivos de salida

Los notebooks generan tablas de trabajo (prefijo `WORK.`) y tablas consolidadas en la librería `GOBGENER`:

- **Salidas consolidadas** (GOBGENER): `IMPUT_GC_DIP`, `IMPUT_GC_DIP_APER`, `EJECUCION_CG`, `EJECUCION_CG_APER`, `EJECUCION_MUNICIPAL`, etc.
- **Tablas de validación** (WORK): `CHECK_*`, `COMPARA_*` — para auditoria y debugging
- **Tablas de trabajo** (WORK): `CRUCE_*`, `EJEC_*`, `RATIOS`, `TOTALES` — intermedias para cálculos

### Script de orquestación

**`run_all.py`** – Ejecuta todos los notebooks en orden, con parámetros inyectados:

```bash
python run_all.py --year 2024 --month 12 --analista "Usuario" --comp1 "COM001" ...
```

## Estructura del proyecto

```
output/
├── NB-01_autoexec.ipynb
├── NB-02_proceso_ejecucion_gc_cgr.ipynb
├── NB-03_proceso_ejec_gc_dipres.ipynb
├── NB-04_salida_cg_coy.ipynb
├── NB-05_salida_cnf_trim.ipynb
├── NB-06_salidas_adicionales.ipynb
├── run_all.py
├── config.yaml          (configuración de rutas, conexiones BD)
└── utilities.py         (funciones compartidas: logaritmo, conexión BD, etc.)
```

## Cómo correr la migración

### Requisitos

- **Python 3.9+**
- **Paquetes Python**:
  - `pandas` ≥ 1.3
  - `sqlalchemy` ≥ 1.4
  - `pyodbc` ≥ 4.0 (para SQL Server)
  - `jupyter` ≥ 1.0
  - `numpy` ≥ 1.20

- **Base de datos**: SQL Server accesible con las siguientes librerías:
  - `GOBGENER` – Tablas maestras (ENTIDADES, COFOG, diccionarios analíticos)
  - `DCV` – Tabla MONEDAS_MENSUAL (tipos de cambio)

- **Archivos** (según código original):
  - Rutas de lectura/escritura de archivos (CSV, SAS7BDAT) configuradas en `config.yaml`

### Instalación de dependencias

```bash
pip install -r requirements.txt
```

### Ejecución interactiva (notebook por notebook)

1. Abrir `NB-01_autoexec.ipynb` en Jupyter
2. Completar la celda **`parameters`** con los valores del periodo:
   ```python
   Year = 2024
   Mes = 12
   Analista = "Usuario"
   Comp1 = "COM001"
   Comp2 = "COM002"
   # ... (Comp3 a Comp7, Mes_imp1 a Mes_imp12)
   ```
3. Ejecutar todas las celdas (`Ctrl+Shift+Enter` o `Run All`)
4. Repetir para NB-02, NB-03, ... en orden

### Ejecución por lote (script `run_all.py`)

```bash
python run_all.py \
  --year 2024 \
  --month 12 \
  --analista "Usuario" \
  --comp1 "COM001" --comp2 "COM002" --comp3 "COM003" \
  --comp4 "COM004" --comp5 "COM005" --comp6 "COM006" --comp7 "COM007" \
  --mes_imp 1 2 3 4 5 6 7 8 9 10 11 12
```

**Opción `--dry-run`**: Valida parámetros sin ejecutar notebooks.

```bash
python run_all.py --year 2024 --month 12 --dry-run
```

## Parámetros de ejecución

| Parámetro | Tipo | Requerido | Descripción | Ejemplo |
|-----------|------|-----------|-------------|---------|
| `--year` | int | Sí | Año fiscal del proceso | 2024 |
| `--month` | int | Sí | Mes fiscal (1–12) | 12 |
| `--analista` | str | No | Usuario ejecutor (logging) | "Juan Pérez" |
| `--comp1..comp7` | str | No | Códigos de comparador de entidades (máx. 7) | "COM001" |
| `--mes_imp1..mes_imp12` | int | No | Meses a imputar (vacío = sin imputación) | 1 2 3 |
| `--moneda` | str | No | Moneda de reporte (UF/CLP) | "UF" |
| `--pacapr1..pacapr7` | str | No | Paquetes de apertura institucional | "PAC001" |

## Verificaciones tras ejecutar

Después de completar la ejecución, **verificar**:

1. ✓ Todos los notebooks finalizaron sin errores (`[Completed]` en cada celda final)
2. ✓ Tablas en `GOBGENER` se actualizaron:
   - `SELECT COUNT(*) FROM GOBGENER.EJECUCION_CG WHERE AÑO = 2024`
   - Debe retornar > 0
3. ✓ Logs de validación en **últimas celdas** de cada notebook:
   - `CHECK_TCONS_FALT`: verificar faltantes en TCONS
   - `CHECK_ANALIT_REV`: verificar cobertura de analíticos
4. ✓ No hay archivos `.tmp` o `.bak` sin limpiar en `output/`

## Supuestos visibles de la migración

1. **Placement de estrategia**: Nodos con `placement=ambiguous` (4 nodos en AUTOEXEC y flujos diferidos) se traducen con estrategia **pandas** (descargan tablas enteras a memoria). Si una tabla es muy grande (>1 GB), esto puede saturar RAM — resolver en entrevista B4b asignando `placement=sql_pushdown` explícitamente.

2. **Macro variables sin valor**: Los parámetros `Year`, `Mes`, `Analista`, `Comp1`–`Comp7`, `Mes_imp1`–`Mes_imp12`, `Moneda`, `PACAPR1`–`PACAPR7` se dejan como `None` en la celda `parameters` y deben inyectarse al llamar a `run_all.py` o completarse en el notebook manualmente.

3. **Temp tables**: Las tablas `WORK.*` se materializan como `#tmp_*` en sesiones SQL transitorias de la conexión de BD. Al cerrar el notebook, se pierden — comportamiento intencionado para limpiar estado entre ejecuciones.

4. **Credenciales de BD**: Rutas de conexión SQL Server (servidor, BD) se cargan desde `config.yaml`. Credenciales (`uid`, `pwd`) deben inyectarse como variables de entorno (`DB_USER`, `DB_PASS`) — nunca hardcodearlas en el notebook.

5. **Archivos CSV y SAS7BDAT**: Rutas de importación/exportación hardcodeadas en código original se parametrizan en `config.yaml` — actualizar `input_dir` y `output_dir` según el ambiente destino.

## Contactos y soporte

- **Equipo de datos**: [completar contacto]
- **DBA para acceso BD**: [completar contacto]
- **Responsable de proceso**: [completar contacto]

---

**Versión de migración**: 2.0 (Agosto 2026)  
**Generado por**: Migration tool (build_translation_plan.py, doc-writer)  
**Estado**: ✓ Plan aprobado por usuario
