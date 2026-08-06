# README: Migración Proc_Salidas_Gob_REV a Python

## ¿Qué es esta migración?

Este proyecto traduce el flujo de procesos SAS **Proc_Salidas_Gob_REV** (Procesos de Salidas del Gobierno) a Python/Jupyter. El sistema calcula indicadores de ejecución presupuestaria consolidada del sector público chileno, procesando datos de la Contraloría General (CGR) y DIPRES, con validaciones, imputaciones y clasificaciones contables que alimentan reportes de coyuntura fiscal y estadísticas financieras.

La migración entrega **16 flujos migrados** de un total de 17 identificados (1 flujo no migratable), organizados en **11 notebooks ejecutables** siguiendo el orden de dependencias. Los nodos traducidos suman **173 tareas** (DATA STEP, PROC SQL, PROC IMPORT, PROC EXPORT) convertidas a código Python/SQL parametrizado.

## Alcance de esta entrega

**Flujos migrados en este lote:**
- AUTOEXEC
- Proceso Ejecución GC CGR (31 nodos)
- Proceso Ejec GC DIPRES (10 nodos)
- Salida CG coy (14 nodos)
- (+ 7 flujos adicionales con 87 nodos más; ver lista completa abajo)

**Flujos diferidos (próximo lote):**
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

Los flujos diferidos **NO están excluidos**: serán traducidos en entregas posteriores siguiendo el mismo estándar.

## Estructura de salida

```
output/
├── NB-01_autoexec.ipynb              # Librerías, monedas mensuales, variables globales
├── NB-02_proceso_ejecucion_gc_cgr.ipynb  # Validación CGR: entidades, analíticos, TCONS, estructuras
├── NB-03_proceso_ejec_gc_dipres.ipynb    # Validación DIPRES (equivalente a CGR, datos DIPRES)
├── NB-04_salida_cg_coy.ipynb         # Indicadores de consumo de gobierno (coyuntura)
├── NB-05_*.ipynb                     # (+ 6 notebooks más para flujos restantes)
├── NB-11_*.ipynb
├── run_all.py                        # Ejecutor maestro (parametrizable, secuencial)
├── config.yaml                       # Parámetros: period, year, macro_params
├── PARAMETROS.py                     # Constantes de negocio (números mágicos, lookups)
└── docs/
    ├── readme.md                     # Este documento
    ├── lineage.md                    # Origen→destino de datos (fuentes, tablas, notebooks)
    ├── decisions.md                  # Decisiones de alcance, placement, supuestos
    ├── improvements.md               # Mejoras aprobadas y su aplicación
    └── runbook.md                    # Operación día a día (cómo correr, verificaciones, fallos)
```

## Cómo correr

### 1. Requisitos previos

**Software:**
- Python 3.9+
- Jupyter (para ejecución interactiva) o papermill (ejecución batch)
- pandas, numpy, sqlalchemy
- pymssql o pyodbc (conexión SQL Server/Sybase ASE donde residan GOBGENER, DCV, etc.)

**Base de datos:**
- Servidor SQL (GOBGENER, DCV librefs mapeadas a bases existentes)
- Tablas de entrada disponibles: `GOBGENER.EJECUCION`, `GOBGENER.EJEC_DIPRES`, `GOBGENER.MONEDAS_MENSUAL`, etc.

**Instalación de dependencias:**
```bash
pip install -r requirements.txt
```

### 2. Configuración

Editar `config.yaml` con:
```yaml
run:
  year: 2023                    # Año de análisis
  month: 12                     # Mes (1-12)
  period: "2023-12"            # Período (YYYY-MM)
  
  # Parámetros macro SAS heredados
  macro_params:
    Year: 2023
    Mes: 12
    Analista: "USUARIO"
    Comp1: "COMP_A"
    Comp2: "COMP_B"
    # ... (Comp3-7, Mes_imp1-12, PACAPR1-7, Moneda, etc.)

database:
  server: "SERVER_PROD"
  database: "GOBGENER"
  user: "${DB_USER}"           # Desde variable de entorno
  password: "${DB_PASSWORD}"   # Desde variable de entorno
  driver: "ODBC Driver 17 for SQL Server"

paths:
  input: "./input"             # Archivos de entrada (Excel, CSV)
  output: "./output"           # Tablas WORK, archivos generados
  temp: "./temp"               # Archivos temporales durante ejecución
  logs: "./logs"               # Logs de ejecución
```

### 3. Ejecución

**Opción A: Ejecución completa (todos los notebooks)**
```bash
python run_all.py --config config.yaml --log-level INFO
```

**Opción B: Ejecución por lote (flujos específicos)**
```bash
python run_all.py --config config.yaml --notebooks NB-01,NB-02,NB-03 --dry-run
```

**Opción C: Ejecución Jupyter interactiva**
```bash
jupyter notebook output/NB-01_autoexec.ipynb
# Ejecutar celdas en orden; los parámetros se leen de config.yaml
```

**Opción D: Ejecución batch con papermill**
```bash
papermill output/NB-01_autoexec.ipynb output/NB-01_autoexec_run_20231201.ipynb \
  -p YEAR 2023 -p MES 12
```

### 4. Validaciones tras ejecución

Tras correr `run_all.py`, verificar:

1. **Logs sin errores críticos:**
   ```bash
   tail -100 logs/run_2023-12-01T14-30-45.log | grep -i "error\|failed"
   ```

2. **Tablas generadas en la BD:**
   ```sql
   -- Desde SQL Server Management Studio
   SELECT COUNT(*) FROM GOBGENER.EJECUCION;
   SELECT COUNT(*) FROM WORK.COMPARA_PACAPR;  -- Si WORK es BD, no tabla en memory
   ```

3. **Conteos de integridad (WORK temporales):**
   - `NB-02` debe generar: 52+ tablas CHECK_* (validaciones)
   - `NB-03` debe generar: 51+ tablas análogas con prefijo _DIP (DIPRES)
   - `NB-04` debe generar: 64+ tablas EJECUCION_* (distintos formatos/agregaciones)

4. **Archivos Excel exportados:**
   ```bash
   ls -lh output/*.xlsx | wc -l  # Debe ser 4+ (propuestas de clasificación)
   ```

## Supuestos y limitaciones

### Supuestos visibles

1. **Macro variables sin valor declarado:** Year, Mes, Comp1-7, Mes_imp1-12, Moneda, Analista, PACAPR1-7.
   - **Acción:** Declarar en `config.yaml` o pasar como argumentos a `run_all.py`.
   - **Si no se declaran:** quedarán como `None` en la celda `parameters` del notebook y causarán errores en filtros/cálculos.

2. **Placement ambiguo en 4 nodos:**
   - `CodeTask-D6fqrxqReNOK5Xch` (Monedas_Mensual): ¿WORK local o base de datos?
   - `CodeTask-cbwaC9NShYE8mV6x`, `CodeTask-oLKJ5g7DvhYHuBME`, `Query-YHeDzXnzld6fOVfj`: idem.
   - **Decisión provisional:** estrategia **pandas** (tabla entera a memoria). **Riesgo:** si la tabla es > 1 GB, falla por memoria.
   - **Resolución:** revisar libref en el sistema SAS original o editar el notebook para usar `sql_pushdown` (consulta directa en BD).

3. **Rutas hardcodeadas conservadas:** Archivos Excel de entrada (`\\FILESERVER\VOLM\...`) permanecen como literals en los notebooks.
   - **Razón:** `M-003` fue rechazada (usuario indicó dejar rutas inline).
   - **Acción manual:** antes de producción, parametrizar en config.yaml.

4. **Flujos diferidos (12 flows, ~80 nodos):** NO incluidos en esta entrega.
   - **Timing:** próxima entrega después de aprobación de este lote.
   - **Impacto:** reportes de CNF, municipales, situación patrimonial quedan para luego.

### Limitaciones de traducción

1. **PROC EXPORT a PC Files Server (OLE DB):** 
   - SAS original: `OUTFILE= \\FILESERVER\... SERVER=OLEDB`.
   - Python: pandas.to_excel() + ruta local → requiere post-procesamiento para sincronizar con UNC.

2. **PROC SORT NODUPKEY con DATA STEP complejo:**
   - SAS: gestión de duplicados durante ordenamiento.
   - Python: `.drop_duplicates()` post-proceso; puede reordenar filas (lógica equivalente, orden diferente).

3. **Variables implícitas (_N_, _ERROR_):**
   - SAS: variables automáticas.
   - Python: agregadas explícitamente donde se detecte (ej: `_N_ = range(1, len(df)+1)`).

4. **LEFT JOIN sobre múltiples criterios con NULLs:**
   - SAS: comportamiento NULL en joins bien definido.
   - Python: pandas.merge() requiere validación adicional de NaN/None si criterios incluyen NULLs.

## Diccionario de archivos generados

| Notebook | Flujo SAS | Entrada | Salida (datos) | Propósito |
|----------|-----------|---------|-----------------|-----------|
| NB-01 | AUTOEXEC | DCV.MONEDAS_MENSUAL | WORK.CIERRE_MES, PROM_TRIM, etc. | Tipos de cambio, variables globales |
| NB-02 | Proceso Ejecución GC CGR | GOBGENER.EJECUCION, .ENTIDADES | WORK.COMPARA_*, .CHECK_*, GOBGENER.ANALIT_TCONS | Validación CGR, clasificación contable |
| NB-03 | Proceso Ejec GC DIPRES | GOBGENER.EJEC_DIPRES, .ENTIDADES | WORK.* (análogas a NB-02) | Equivalente para datos DIPRES |
| NB-04 | Salida CG coy | WORK.EJECUCION_* | WORK.EJECUCION_CG, RATIOS | Indicadores coyuntura fiscal |
| NB-05+ | (Flujos diferidos) | (TBD) | (TBD) | (próximo lote) |

## Contactos y soporte

- **Responsable técnico:** [NOMBRE PENDIENTE]
- **Base de datos (GOBGENER):** [CONTACTO BD]
- **Reportes de error:** Incluir log de `run_all.py` + última celda ejecutada.

## Historial de cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2024-12-XX | Entrega inicial: 11 notebooks, 173 nodos migrados, 16 flujos |

---

**Nota:** Este README se genera automáticamente desde el plan de migración. Para actualizaciones, editar `config.yaml` o revisar `decisions.md` y `runbook.md`.
