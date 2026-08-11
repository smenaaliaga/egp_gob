# Decisiones de la Migración: Proc_Salidas_Gob_REV_mig-2

## Alcance y Cobertura

Esta migración traduce **18 de 19 flujos** del proyecto `Proc_Salidas_Gob_REV_mig`. La entrega presente cubre los siguientes 4 flujos principales:

1. **AUTOEXEC** (3 nodos) — Inicialización de librerías y procesamiento de monedas mensuales
2. **Proceso Ejecución GC CGR** (31 nodos) — Validación y clasificación de ejecuciones presupuestarias del Gobierno Central desde Contraloría
3. **Proceso Ejec GC DIPRES** (10 nodos) — Validación y clasificación de estructuras analíticas de ejecución DIPRES
4. **Salida CG coy** (14 nodos) — Generación de salidas consolidadas de ejecución de Gobierno Central con imputaciones

### Flujos Diferidos (No Incluidos en Esta Entrega)

Los siguientes **14 flujos** se migrarán en lotes posteriores:

- Salida CG Imputa
- Salida CNF trim
- Salida_CNF_Trim_CGR
- Salida_CNF_Trim_DIP
- Salidas CNF anual y COFOG
- Salida_anual para componente especif_no
- Proceso Sit_Patri_MUN_no
- Proceso Ejecución Municipal CGR_no
- Traspasos_info
- Salida_CF_GC
- Salida_DCNA
- Salidas_Cuenta_Produc_AAPP_no
- Salidas_Cuenta_Produc_AAPP_2_no
- Indicadores municipales

**Justificación del diferimiento:** Los flujos diferidos comparten dependencias complejas con tablas intermedias generadas en lotes anteriores (ej. tablas de Cuentas Nacionales, indicadores agregados) y con entidades del modelo de datos que aún requieren validación de integridad referencial. Su traducción será ejecutada una vez se verifique la completitud de fuentes en la entrega inicial.

---

## Decisiones de Placement y Estrategia

### Notebooks Generados

Se producen **4 notebooks Jupyter** (uno por flujo principal), más un script `run_all.py` de orquestación:

| Flujo | Notebook | Nodos | Estrategia Predominante |
|-------|----------|-------|------------------------|
| AUTOEXEC | `NB-01_autoexec.ipynb` | 3 | Python/Pandas + SQL pushdown |
| Proceso Ejecución GC CGR | `NB-02_proceso_ejecucion_gc_cgr.ipynb` | 31 | SQL pushdown (base de datos) |
| Proceso Ejec GC DIPRES | `NB-03_proceso_ejec_gc_dipres.ipynb` | 10 | SQL pushdown (base de datos) |
| Salida CG coy | `NB-04_salida_cg_coy.ipynb` | 14 | SQL pushdown + Pandas |

### Decisiones de Estrategia por Tipo de Nodo

#### Nodos tipo `OTHER` (Librerías, Programa)
- **Decisión:** Convertir a Python plano (utility).
- **Ubicación:** Notebook `NB-01_autoexec.ipynb`.
- **Rationale:** `LIBNAME`, `%INCLUDE` y declaraciones de programa SAS se mapean a imports de Python, inicialización de conexiones y definición de funciones. No requieren materialización de datos, solo configuración.

#### Nodos tipo `PROC_SQL` (Validación, Clasificación, Redistribución)
- **Decisión:** SQL pushdown a la base de datos GOBGENER cuando sea posible; fallback a Pandas si el SQL incluye extensiones SAS no portables.
- **Ubicación:** Notebooks por flujo (`NB-02`, `NB-03`, `NB-04`).
- **Rationale:** 
  - 90+ nodos son PROC_SQL con lógica de clasificación y validación compleja (múltiples JOINs, CASE WHEN anidados, agregaciones GROUP BY).
  - La base de datos es la fuente de verdad y ejecutar SQL en servidor minimiza transferencia de datos (no bajar tablas completas a memoria).
  - Se usa `temp_table_strategy=session_sql`: las tablas WORK se materializan como `#tmp` en la conexión de sesión, reutilizable entre celdas.

#### Nodos tipo `IMPORT` (Lectura de Archivos)
- **Decisión:** Usar `pandas.read_csv()` o `pandas.read_excel()` según formato.
- **Ubicación:** Nodos de lectura en notebooks respectivos.
- **Rationale:** PROC IMPORT se mapea naturalmente a Pandas I/O; las rutas se parametrizan en celdas de configuración.

#### Nodos con Placement `ambiguous` (sin resolver)
- **Decisión:** Aplicar estrategia `pandas` (default de config).
- **Ubicación:** Ambas celdas afectadas en notebook respectivo.
- **Advertencia:** Si el libref resulta ser una base de datos, la estrategia Pandas bajará la tabla completa a memoria, lo que puede causar overhead. **Acción recomendada:** resolver en entrevista B4b o establecer override de placement. Nodos afectados:
  - `CodeTask-D6fqrxqReNOK5Xch` (Monedas_Mensual) — puede ser `DCV.MONEDAS_MENSUAL` (tabla) o archivo.
  - `CodeTask-cbwaC9NShYE8mV6x`, `CodeTask-oLKJ5g7DvhYHuBME`, `Query-YHeDzXnzld6fOVfj` (están en flujos diferidos; se resuelven en próximo lote).

---

## Supuestos Visibles del Plan

### 1. Macro Variables No Declaradas
El plan identifica 30 macro variables sin valor declarado en `project_config.yaml`:
- `&Year`, `&Mes`, `&Moneda`, `&Analista`
- `&Comp1`–`&Comp7` (6 variables de segmentación comparativa)
- `&PACAPR1`–`&PACAPR7` (7 variables de apertura presupuestaria)
- `&Mes_imp1`–`&Mes_imp12` (12 parámetros de imputación mensuales)

**Decisión:** Todas quedarán como `None` en la celda `parameters` de cada notebook hasta que el usuario las declare en:
- `project_config.yaml` → `run.macro_params`, o
- Entrada interactiva en notebook al ejecutar.

**Impacto:** Crítico. Sin estos parámetros, las celdas SQL que filtren `WHERE ANO = &Year` o `WHERE C_PACAPR IN (&PACAPR1, &PACAPR2, ...)` devolverán conjuntos vacíos o errores. Se debe completar antes de correr.

### 2. Base de Datos GOBGENER — Asunción de Disponibilidad
- **Supuesto:** La BD GOBGENER está disponible y accesible en la sesión Python vía alias registrado (`connection_alias = "GOBGENER"`).
- **Requisito:** Antes de correr notebooks, el usuario debe:
  - Verificar conexión con `pytest-connect.py` o similar.
  - Confirmar permisos de lectura en librerías DCV, DCNI, DCNA.
  - Verificar que la tabla `DCV.MONEDAS_MENSUAL` existe (usada en AUTOEXEC).

### 3. Estrategia de Tablas Temporales: Session SQL
- **Supuesto:** Todas las tablas WORK (temporales) se ejecutan como `#tmp_WORK_XXXX` en la sesión SQL.
- **Implicación:** La sesión de BD debe permanecer abierta durante toda la ejecución del notebook. Si la conexión se cierra entre celdas, las `#tmp` se pierden.
- **Mitigación:** `run_all.py` abre una única sesión compartida y la mantiene durante toda la orquestación.

### 4. Flujos Diferidos No Son Excluidos
- **Clarificación:** El diferimiento es **temporal**, no una exclusión permanente. Los 14 flujos diferidos se migrarán cuando entren sus nodos dependientes en un lote posterior.
- **Razón:** Evitar traducir código con dependencias internas irresueltas, lo que causaría fallos silenciosos.

---

## Decisiones de Entrevista B4b (Placement y Overrides)

### Nodos Resueltos en Entrevista
1. **CodeTask-D6fqrxqReNOK5Xch (Monedas_Mensual)**
   - **Entrevista confirmó:** Libref `DCV.MONEDAS_MENSUAL` es tabla SQL Server.
   - **Estrategia asignada:** `sql_pushdown` (bajada a través de sesión BD).
   - **Notebook:** `NB-01_autoexec.ipynb`.

2. **Nodos DIPRES (CodeTask-23lpner3oIe465S4, CodeTask-6aNX7ji1HAf8Qnl2, etc.)**
   - **Entrevista confirmó:** IMPORT desde archivos Excel externos (rutas hardcodeadas en `\\FILESERVER\VOLM\...`).
   - **Estrategia asignada:** `pandas` (read_excel).
   - **Notebook:** `NB-03_proceso_ejec_gc_dipres.ipynb`.
   - **Nota:** Rutas parametrizadas en celdas de configuración (ver M-002, postponed).

### Nodos Pendientes de Resolver (Lote 2)
- `CodeTask-cbwaC9NShYE8mV6x`, `CodeTask-oLKJ5g7DvhYHuBME`, `Query-YHeDzXnzld6fOVfj` — en flujos diferidos.

---

## Decisiones Sobre Mejoras (M-001 a M-008)

| ID | Título | Decisión | Acción en Esta Entrega |
|----|----|-------|-----|
| M-001 | Eliminar duplicación masiva SQL | **REJECTED** | No aplica. La deduplicación requiere refactorización completa de 44 nodos; postponed para lote 3 tras validar salidas. |
| M-002 | Centralizar rutas hardcodeadas | **POSTPONED** | Nodos afectados (17 de ellos) están en flujos diferidos. Se reabre cuando entren en próximo lote. |
| M-003 | Extraer números mágicos | **REJECTED** | Conversión compleja; requiere validación del modelo de negocio. Documentado en código inline (comentarios) en esta entrega. |
| M-004 | Refactorizar CASE repetidas | **REJECTED** | Impacto alto en lógica de negocio. Se pospone tras UAT de salidas en lote 1. |
| M-005 | Documentar y versionear macros | **APPROVED** | Aplicado en esta entrega: celda `parameters` en cada notebook con comentarios sobre expected values y rango. |
| M-006 | Eliminar credenciales hardcodeadas | **POSTPONED** | 17 nodos afectados están en flujos diferidos. Implementar con bóveda de secretos en lote 2. |
| M-007 | Validar dependencias de BD | **POSTPONED** | Nodos afectados en flujos diferidos. Audit de esquema en lote 2. |
| M-008 | Suite de validación de datos | **REJECTED** | Lógica de validación integrada en nodos; refactorización requerida tras validar outputs. |

**Mejoras Aplicadas en Esta Entrega:** M-005 (documentación de macros).

---

## Linaje de Datos y Dependencias Críticas

### Flujo 1: AUTOEXEC
```
CodeTask-XzOatjIuMbeLV29h (Set Librera → Python util)
    ↓
CodeTask-D6fqrxqReNOK5Xch (Monedas_Mensual → SQL pushdown)
    → Entrada: DCV.MONEDAS_MENSUAL
    → Salidas: WORK.CIERRE_MES, WORK.CIERRE_TRIM, WORK.PROM_MES, WORK.PROM_MES_TODAS, WORK.PROM_TRIM
    ↓
CodeTask-q5ZEbAg5C43nmYfy (Programa → Python util)
    → Cierre: define macros de programa, inicializa variables globales
```

**Nota:** Las tablas `PROM_MES` se usan en `NB-04_salida_cg_coy.ipynb` (cálculo de ratios). Crítica la ejecución de AUTOEXEC primero.

### Flujo 2: Proceso Ejecución GC CGR
```
31 nodos encadenados → Lectura de 15 librerias GOBGENER → Validación de cambios ENTIDADES
    → Clasificación de analíticos (fijos/variables)
    → Validación de transacciones COFOG
    → Salidas intermedias (WORK.CHECK_*, WORK.COMPARA_*, WORK.CRUCE_*)
    → Tabla final: WORK.EJEC_CGR
```

**Dependencias:** Requiere que AUTOEXEC haya completado. Macro `&Year` es crítica (todos los 31 nodos filtran por año).

### Flujo 3: Proceso Ejec GC DIPRES
```
10 nodos encadenados → IMPORT de archivos Excel (DIPRES, Entidades DIP)
    → Validación de estructura analítica
    → Clasificación SCN
    → Salida: WORK.EJEC_DIP
```

**Dependencias:** Independiente de Flujo 2, pero sus outputs se usan en Flujo 4. Macros `&Mes`, `&Moneda` críticas.

### Flujo 4: Salida CG coy (14 nodos)
```
Entrada: WORK.EJEC_CGR + WORK.EJEC_DIP + WORK.PROM_MES (de AUTOEXEC)
    → Redistribución de transacciones mixtas (M)
    → Imputación de faltantes (DIPRES)
    → Consolidación CGR + DIP
    → Salidas: GOBGENER.IMPUT_GC_DIP, WORK.EJECUCION_CG_CGR, WORK.EJECUCION_CG_DIP, etc.
```

**Dependencias:** Crítica ejecutar Flujos 1, 2, 3 completos antes.

---

## Validación de Integridad de Entrada

### Base de Datos: Estado No Verificado
Las librerías siguientes están marcadas como `verified_db: false`:
- DCNIDCNA, DCV, DCNI, DCNA, GOBGENER

**Decisión:** En esta entrega, **no se valida esquema** (v. supuesto #2). La validación se postpone a lote 2 (M-007 postponed).

**Acción requerida del usuario antes de correr:**
```
pytest test/test_db_connections.py -v
pytest test/test_schema_gobgener.py -v
```

### Parámetros de Entrada: Validación en Notebook
Cada notebook incluye celda de validación de parámetros:
- Check `&Year` en rango [2010, 2026]
- Check `&Mes` en rango [1, 12]
- Check `&Moneda` en lista permitida (CLP, USD, etc.)
- Check macros `&Comp1`–`&Comp7` contra tabla de referencia

---

## Decisiones sobre Mapping SAS → Python

### SQL Directo (SQL Pushdown)
Todos los `PROC SQL CREATE TABLE` se traducen a:
```python
query = """
SELECT ...
FROM GOBGENER.XXX
WHERE ANO = ?
"""
df = pd.read_sql(query, conn, params=[year_param])
conn.execute(f"CREATE TABLE #tmp_WORK_XXX AS SELECT * FROM (...)")
```

**Excepciones:** Nodos que usan extensiones SAS no portables (ej. `PROC DATASETS`, `DATA step` con lógica condicional compleja) se traducen a Pandas.

### DATA Step → Pandas
Cualquier `DATA step` con lógica record-by-record se mapea a:
```python
df = df.assign(new_col=lambda x: x['col_a'] + x['col_b'])
# o
df['new_col'] = df.apply(lambda row: custom_logic(row), axis=1)
```

### Macros SAS → Parámetros Python
```sas
%LET Year = 2024;
PROC SQL;
    CREATE TABLE XXX AS
    SELECT * FROM GOBGENER.EJECUCION WHERE ANO = &Year;
```

Se traduce a:
```python
params = {'Year': 2024}
query = f"SELECT * FROM GOBGENER.EJECUCION WHERE ANO = {params['Year']}"
```

**Con validación:** La celda `parameters` del notebook valida que `Year` no sea None antes de usarlo.

---

## Plan de Validación de Outputs

### Tabla de Verificación Post-Ejecución

| Notebook | Tabla de Salida | Validación |
|----------|-----------------|-----------|
| NB-01 | WORK.CIERRE_MES | Row count > 0; columnas (ANO, MES, T_CAMBIO_CIERRE, ...) presentes |
| NB-02 | WORK.EJEC_CGR | Row count = input EJECUCION; sin NULLs críticos en (C_ENTIDAD, C_ANALITICO) |
| NB-03 | WORK.EJEC_DIP | Row count > 0; suma(DEVENGADO) = suma(entrada DIPRES) ± 0.01% |
| NB-04 | GOBGENER.IMPUT_GC_DIP | Row count > 0; Columna ANALITICO únicamente en {fijo, variable, diferenciado, mixta} |

### Checks de Integridad
Cada notebook incluye celdas de chequeo:
- `assert len(df_output) > 0`
- `assert not df_output[['C_ENTIDAD', 'C_ANALITICO']].isnull().any()`
- `assert set(df_output['ANALITICO'].unique()).issubset({'fijo', 'variable', 'diferenciado', 'mixta'})`

---

## Notas Finales

1. **Reproducibilidad:** Todas las macro variables deben ser declaradas en `project_config.yaml` o mediante UI del notebook antes de correr. Sin esto, los outputs no serán reproducibles.

2. **Compatibilidad de Versiones:** Se asume Python 3.9+, pandas 1.3+, sqlalchemy 1.4+. Ver `requirements.txt` en directorio de output.

3. **Seguridad:** Credenciales de BD no están en notebooks; se inyectan vía variables de entorno (`DB_USER`, `DB_PASSWORD`). Ver `run_all.py`.

4. **Lotes Posteriores:** La lista de flujos diferidos será revisada tras UAT de esta entrega. Si hay cambios en dependencias, se comunicará al usuario antes de lote 2.
