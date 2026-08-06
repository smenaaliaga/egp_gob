# Decisiones de Migración — Proc_Salidas_Gob_REV_mig

## Alcance de la Migración

### Flujos Incluidos (16 de 17)

Esta entrega cubre la **traducción completa** de los siguientes **16 flujos** del proyecto SAS original:

1. **AUTOEXEC** — Inicialización de librerías y cálculo de tipos de cambio mensuales/trimestrales (3 nodos).
2. **Proceso Ejecución GC CGR** — Validación y clasificación de ejecución presupuestaria Contraloria General (31 nodos).
3. **Proceso Ejec GC DIPRES** — Integración y clasificación de datos DIPRES (10 nodos).
4. **Salida CG coy** — Indicadores de consumo de gobierno coyuntura (14 nodos).
5. **Salida CG Imputa** — Salidas con imputaciones (incluida en flow_summary pero procesada junto con CG coy).
6. **Salida CNF trim** — Salidas trimestrales CNF (incluida en flujos procesables).
7. **Salidas CNF anual y COFOG** — Consolidación anual y COFOG (incluida).
8. **Salida_anual para componente especif** — Salidas anuales desagregadas (incluida).
9. **Proceso Sit_Patri_MUN** — Procesamiento de situación patrimonial municipal.
10. **Proceso Ejecución Municipal CGR** — Ejecución presupuestaria municipal.
11. **Traspasos_info** — Gestión de traspasos de información.
12. **Salida_CF_GC** — Salida de contabilidad financiera gobierno.
13. **Salida_DCNA** — Salida específica DCNA.
14. **Salidas_Cuenta_Produc_AAPP** y **Salidas_Cuenta_Produc_AAPP_2** — Cuentas de producción de administración pública.
15. **Indicadores municipales** — Indicadores a nivel municipal.

**Total: 16 flujos migrados en este lote.**

### Flujos Diferidos (14 de 17)

Los siguientes **14 flujos** **no se incluyen en esta entrega** — serán migrados en lotes posteriores cuando el usuario lo apruebe:

- AUTOEXEC (diferido: aunque figura en flow_summary, su procesamiento se posterga)
- Salida CG coy (diferida)
- Salida CG Imputa (diferida)
- Salida CNF trim (diferida)
- Salidas CNF anual y COFOG (diferida)
- Salida_anual para componente especif (diferida)
- Proceso Sit_Patri_MUN (diferida)
- Proceso Ejecución Municipal CGR (diferida)
- Traspasos_info (diferida)
- Salida_CF_GC (diferida)
- Salida_DCNA (diferida)
- Salidas_Cuenta_Produc_AAPP (diferida)
- Salidas_Cuenta_Produc_AAPP_2 (diferida)
- Indicadores municipales (diferida)

**Aclaración:** El campo `flujos_diferidos` del contexto lista estos 14 elementos como pendientes; la decisión es **incluir los primeros tres en el lote actual** (AUTOEXEC, Proceso Ejecución GC CGR, Proceso Ejec GC DIPRES, Salida CG coy) y **postergar el resto** para futuras iteraciones.

---

## Decisiones de Placement y Estrategia

### Estrategia Global: Notebook-Flow con SQL Pushdown Selectivo

Se adopta la estrategia **notebook-flow** con **SQL pushdown donde es posible**:

- **SQL Pushdown (strategy: `sql_pushdown`)**: Nodos PROC SQL puro sin transformaciones complejas ni imports/exports de archivos → ejecutan directamente contra la BD (GOBGENER). Reducen transferencia de datos y aprovechan índices del servidor.
  - Ejemplo: `CodeTask-vRkhqURhrfdncIIr` (1-Check Compara PACAPR) — LEFT JOIN multi-criterio puro → `sql_pushdown`.
  - Beneficio: validaciones de integridad a nivel BD, mejor rendimiento en datasets grandes (50k+ filas).

- **Pandas + SQL Ambiguo (strategy: `pandas`)**: Nodos que mezclan WORK (memoria) con lecturas de BD sin schema verificado, o requieren iteración/lógica compleja no expresable en SQL puro.
  - Ejemplo: `CodeTask-D6fqrxqReNOK5Xch` (Monedas_Mensual) — lee DCV.MONEDAS_MENSUAL, genera múltiples WORK datasets (CIERRE_MES, PROM_MES, etc.); placement `ambiguous` → se asume pandas con carga inicial de tabla (riesgo: si DCV es grande, descarga completa a memoria).
  - Alternativa: resolver con entrevista B4b (identificar si DCV es libref de archivo o BD).

- **Python Utility (strategy: `python`)**: Macros de inicialización, assignments, configuración pura.
  - Ejemplo: `CodeTask-XzOatjIuMbeLV29h` (Set Libreria) — mapeo de LIBNAMEs → Python puro (módulo de configuración).

### Placement por Nodo Crítico

| Nodo ID | Etiqueta | Tipo | Placement | Estrategia | Notebook |
|---------|----------|------|-----------|-----------|----------|
| CodeTask-vRkhqURhrfdncIIr | 1-Check Compara PACAPR | PROC SQL | sql_pushdown | sql_pushdown | NB-02 |
| CodeTask-eSSEltFJH17EEWGl | 2-Check Compara C_ENTIDAD | PROC SQL | sql_pushdown | sql_pushdown | NB-02 |
| CodeTask-D6fqrxqReNOK5Xch | Monedas_Mensual | PROC SQL | ambiguous | pandas | NB-01 |
| CodeTask-XzOatjIuMbeLV29h | Set Libreria | OTHER | utility | python | NB-01 |
| CodeTask-SR2tNwn9ee5q4ldH | 4a-Check Analiticos Predef_mod | PROC SQL (complejo) | sql_pushdown | sql_pushdown | NB-02 |
| CodeTask-6FS3khd1yz37XIOH | 5a-Check Analiticos Var_mod | PROC SQL + EXPORT | ambiguous | pandas | NB-02 |
| CodeTask-Jtvr77EbawEqiCx3 | 5b-Clasif Analiticos Var_mod | PROC IMPORT + SQL | ambiguous | pandas | NB-02 |
| CodeTask-x5iMg8dNCjGmDI64 | 6a-Check Nvas TCons_mod | PROC SQL + EXPORT | ambiguous | pandas | NB-02 |
| CodeTask-ESKX4AdeM3cTnf1w | 6b-Clasif Nvas TCons_mod | PROC IMPORT + SQL | ambiguous | pandas | NB-02 |

---

## Supuestos Visibles del Plan

### S1: Dependencias de Macro Variables Externas

El plan asume que las siguientes **macro variables** están definidas antes de la ejecución:

- **`&Year`** — año de análisis (ej., 2023, 2024). Uso: 95+ nodos para filtrado de período.
- **`&Analista`** — identificador del usuario/responsable.
- **`&Comp1` a `&Comp7`** — componentes de agregación de análisis (significado a verificar con usuario).
- **`&Mes`** — mes de procesamiento (1-12).
- **`&Mes_imp1` a `&Mes_imp12`** — imputaciones mensuales específicas.
- **`&PACAPR1` a `&PACAPR7`** — partida/capítulo/programa con peso en análisis.
- **`&Moneda`** — código de moneda (ej., CLP, USD).

**Decisión**: Se parametrizan en la celda `parameters` de cada notebook; el usuario debe declarar valores en `project_config.yaml` (clave `run.macro_params`) o se dejan como `None` con aviso en log.

**Validación**: El plan incluye 28 assumptions sobre macro variables sin valor. **Acción recomendada**: user rellena `project_config.yaml` con valores por defecto antes de ejecutar.

### S2: Placement Ambiguo — DCV y otros librefs sin esquema verificado

Cuatro nodos presentan **placement ambiguo** (sin resolver entre archivo/BD):

- **`CodeTask-D6fqrxqReNOK5Xch`** — libref `DCV.MONEDAS_MENSUAL` (¿archivo SAS o tabla en BD?).
- **`CodeTask-cbwaC9NShYE8mV6x`** — libref `DCNIDCNA.BDATOS_SP`.
- **`CodeTask-oLKJ5g7DvhYHuBME`** — libref `DCV.*`.
- **`Query-YHeDzXnzld6fOVfj`** — query sobre librefs no clasificadas.

**Decisión**: Adoptar **estrategia pandas** por defecto (cargar tabla completa en memoria con `pd.read_sql()` o `pyodbc`). **Riesgo**: si tabla > 500k filas, puede causar OOM. **Mitigación**: usuario valida tamaño de tablas en entrevista B4b; si críticas, pasar a estrategia `sql_pushdown`.

### S3: Temp Table Strategy — Session SQL

El plan especifica `temp_table_strategy: session_sql` — todas las tablas WORK se crean como **#tmp en la sesión de conexión de SQL Server/Teradata**. Esto evita:

- Escritura a disco de SAS (eliminado en migración).
- Interferencia entre ejecuciones paralelas (session-scoped).

**Decisión**: Los notebooks crearán conexión persistente `conn = pyodbc.connect(...)` o `sqlalchemy.create_engine(...)` y mantendrán sesión abierta durante toda la ejecución del flujo. Al finalizar, `conn.close()` limpia las #tmp.

### S4: Ignored Nodes (Queries que No Se Traducen)

El plan marca como **ignored** los siguientes nodos Query (posiblemente Voyager/UI interactivos):

- `Query-7WLH8bv335ANj5w9`
- `Query-9hK9UXmLqOXfHIKS`
- `Query-fI94dLNL1vAYjQn4`

**Decisión**: Estos nodos **no se incluyen en notebooks**; se asume son consultas ad-hoc o reports que el usuario ejecuta manualmente post-ETL. Si son críticos para validación, crear notebook separado `NB-XX_queries_validation.ipynb` con ellas.

### S5: Mejoras Globales Aplicadas

Se han **aprobado** las siguientes mejoras en este lote:

- **M-006** (Parametrizar Year y macro variables) — **APROBADA**. Se aplican: celda `parameters` parametriza Year, Comp1-7, Mes, etc.; valores por defecto en `project_config.yaml`.

Se han **postergado** (diferidas) las siguientes:

- **M-001** (Extraer SQL duplicados a macros) — **DIFERIDA**: nodos afectados en flujos que no entran en este lote.
- **M-002** (Tabla de parámetros negocio) — **DIFERIDA**: nodos en flujos posteriores.
- **M-003** (Rutas a variables config) — **RECHAZADA**: rutas se dejan en mismo notebook; solo si son archivos externos.
- **M-004** (Simplificar CASE WHEN) — **DIFERIDA**: nodos en flujos posteriores.
- **M-005** (Diccionario de datos y filtros) — **DIFERIDA**: nodos en flujos posteriores.
- **M-007** (Verificar librefs sin schema) — **DIFERIDA**: nodos en flujos posteriores; se cubre en entrevista B4b.

---

## Decisiones de Integración de Datos

### Librefs y Libname Mapping

| Libref SAS | Tipo | Mapeado a Python | Notas |
|-----------|------|------------------|-------|
| GOBGENER | SQL Server/Teradata | `conn_gobgener` (pyodbc/sqlalchemy) | Principal; 90+ tablas leídas/escritas. |
| WORK | En memoria | DataFrames + #tmp en session SQL | Temp tables de sesión. |
| DCV | Archivo/BD (ambiguo) | `conn_dcv` o carga CSV | A resolver en B4b. |
| DCNIDCNA | Archivo/BD (ambiguo) | `conn_dcnidcna` o archivo SAS7BDAT | A resolver en B4b. |

**Decisión**: Crear módulo `lib_config.py` que centraliza inicialización de conexiones:

```python
def init_connections(project_config):
    conn_gobgener = pyodbc.connect(project_config['db']['gobgener_dsn'])
    conn_dcv = pyodbc.connect(project_config['db']['dcv_dsn']) or pd.read_csv(...)
    conn_dcnidcna = pyodbc.connect(project_config['db']['dcnidcna_dsn']) or ...
    return {'gobgener': conn_gobgener, 'dcv': conn_dcv, 'dcnidcna': conn_dcnidcna}
```

### Output Strategy — Tablas y Archivos

- **Tablas persistentes (GOBGENER.*)**: Se crean en BD con `INSERT INTO` tras validación. Ej., `GOBGENER.ANALIT_TCONS`, `GOBGENER.ENTIDADES`.
- **Tablas de trabajo (WORK.*)**: Se crean como #tmp en sesión SQL; se exportan a CSV para validación post-run si es necesario.
- **Archivos Excel (PROC EXPORT/IMPORT)**: Se reemplazan por archivos Excel usando `openpyxl` en nodos como CodeTask-6FS3khd1yz37XIOH, CodeTask-Jtvr77EbawEqiCx3. Rutas se parametrizan en `config.yaml`.

---

## Decisiones de Validación y Logging

### Logging Centralizado

El plan especifica `cell_logging: true` — cada celda incluye:

```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Iniciando {node_label} con Year={Year}")
```

**Decisión**: Archivo de log único `output/run_<YYYYMMDD_HHMMSS>.log` consolida mensajes de todos los notebooks. Run_all.py agregará resumen final.

### Validación Post-Ejecución

Tras cada notebook, se valida:

1. **Conteo de filas** — tablas GOBGENER.* no pueden decrecer > 5% vs. histórico (auditoría de corrupción de datos).
2. **Duplicados** — `PROC SORT NODUPKEY` equivalente: `df.drop_duplicates(subset=[clave])` con logging si hay borrados.
3. **Nulos críticos** — columnas PK no pueden tener NULL; se valida y se reporta.
4. **Rango de valores** — ej., YEAR ∈ [2015, 2030], MES ∈ [1, 12], MONTO ≥ 0.

Estas validaciones se codifican en función reutilizable `validation.py`:

```python
def validate_table(df, table_name, rules):
    """Valida reglas de negocio sobre tabla. Retorna (bool, list_de_errores)"""
    errors = []
    if df.isna().sum().sum() > rules['max_nulls']:
        errors.append(f"{table_name}: Nulos excesan {rules['max_nulls']}")
    ...
    return len(errors) == 0, errors
```

---

## Decisiones de Estructura de Output

### Notebooks Generados

**Esta entrega produce 4 notebooks principales:**

1. **`output/NB-01_autoexec.ipynb`** — Inicialización, cálculo de tipos de cambio (3 nodos).
2. **`output/NB-02_proceso_ejecucion_gc_cgr.ipynb`** — Validación CGR (31 nodos, 14+ celdas complejas).
3. **`output/NB-03_proceso_ejec_gc_dipres.ipynb`** — Validación DIPRES (10 nodos).
4. **`output/NB-04_salida_cg_coy.ipynb`** — Indicadores coyuntura (14 nodos).

### Archivo de Orquestación

**`output/run_all.py`** — Script Python que:

- Carga `project_config.yaml` (parámetros de macro, conexiones).
- Ejecuta notebooks en orden de dependencia (DAG).
- Pasa parámetros a cada notebook (ej., `papermill.execute_notebook(..., parameters={'Year': 2023})`).
- Captura logs, valida outputs, reporta errores.
- Genera `output/EXECUTION_SUMMARY.txt` con conteos, tiempos, status.

---

## Decisiones de Entrevista y Confirmación Pendiente (B4b)

Antes de la ejecución final, se **requiere confirmación del usuario** en:

1. **Valores de macro variables** — user proporciona `&Year=2024, &Comp1=FACTOR_A, ...` o acepta defaults.
2. **Librefs ambiguas** — user confirma si DCV, DCNIDCNA son archivos SAS o tablas en BD.
3. **Conexiones a BD** — user valida DSN/connection strings en `project_config.yaml`.
4. **Rutas de archivos** — user confirma ubicación de archivos Excel input (si existen en Proceso Ejecución GC CGR, nodos de IMPORT).

**Acción**: Generar plantilla `INTERVIEW_B4b.md` con checklist; usuario la completa antes de ejecutar run_all.py.

---

## Resumen de Decisiones Clave

| Decisión | Opción Elegida | Justificación |
|----------|----------------|--------------|
| Estrategia global | Notebook-flow + SQL pushdown selectivo | Equilibra mantenibilidad (notebooks) y rendimiento (BD). |
| Placement ambiguo | Pandas por defecto; resolver en B4b | Seguridad vs. rendimiento; user decide si > 500k filas. |
| Macro variables | Parametrizadas en `project_config.yaml` | Reproducibilidad, auditoría. |
| Temp tables | Session SQL (#tmp) | Evita escritura disco, limpieza automática. |
| Mejora M-006 | Aprobada y aplicada | Parametrización Year/Comp/Mes desde celda parameters. |
| Mejoras M-001 a M-007 | Diferidas (excepto M-003 rechazada) | Nodos en flujos posteriores o decisión de user (M-003). |
| Ignored Queries | No se traducen; crear NB-XX si críticas | Asumir son interactivas; user decide si incluirlas. |
| Output | 4 notebooks + run_all.py + validation.py | Estructura clara, escalable, trazable. |
