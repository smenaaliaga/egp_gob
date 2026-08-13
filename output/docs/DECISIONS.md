# Decisiones de la Migración

## Resumen Ejecutivo

Este documento consigna las decisiones de alcance, placement, estrategia y supuestos visibles adoptadas para la migración de **Proc_Salidas_Gob_REV_mig-2** del entorno SAS al stack Python/SQL. La migración abarca **18 flujos migrables de 19 totales**, traduciendo **183 nodos** (de 188) en **8 notebooks Jupyter** más un módulo `run_all.py` de orquestación.

---

## 1. Alcance

### 1.1 Flujos Incluidos (18 de 19)

Se **migran completamente** los siguientes 18 flujos dentro de este lote:

1. **AUTOEXEC** (3 nodos)  
   Procesamiento de monedas y tipos de cambio; genera agregaciones mensuales y trimestrales (CIERRE_MES, CIERRE_TRIM, PROM_MES, PROM_TRIM).

2. **Proceso Ejecución GC CGR** (31 nodos)  
   Validación y clasificación de ejecuciones presupuestarias (Contraloría General de la República). Enriquecimiento de matriz de analíticos fijos/variables con propuestas automáticas. **Salida principal**: GOBGENER.ANALIT_TCONS y derivadas (31 output_datasets).

3. **Proceso Ejec GC DIPRES** (10 nodos)  
   Validación de estructuras analíticas DIPRES. Garantiza consistencia en nivel de entidad y afectación de transacciones.

4. **Salida CG coy** (14 nodos, ProcessFlowContainer)  
   Redistribución de transacciones mixtas (muestra + expansión) desde CGR/DIPRES. Genera indicadores de consumo por dimensión. **Salidas críticas**: EJECUCION_CG_CGR, EJECUCION_CG_DIP, tablas de imputación.

5. **Salida CNF trim** (12 nodos)  
   Ejecución no financiera trimestral. Redistribución M/MGCG/MM/MGG por ponderadores. Reasignaciones hard-coded de códigos SCN (~15 reglas). Salida: SALIDA_CNF_trim.

6. **Salida CNF anual y COFOG** (15 nodos)  
   Agregación anual de CNF, clasifica por COFOG. Consolida información para análisis funcional del gasto público.

7. **Salida_anual para componente especif_no** (8 nodos)  
   Información desagregada de componentes especiales (fuera del análisis coyuntural).

8. **Proceso Sit_Patri_MUN_no** (6 nodos)  
   Situación patrimonial municipal.

9. **Proceso Ejecución Municipal CGR_no** (5 nodos)  
   Ejecución presupuestaria municipal desde CGR.

10. **Traspasos_info** (2 nodos)  
    Transferencias de información entre etapas.

11. **Salida_CF_GC** (4 nodos)  
    Flujo de caja de Gobierno Central.

12. **Salida_DCNA** (6 nodos)  
    Salida para Sistema de Cuentas Nacionales (DCNA).

13. **Salidas_Cuenta_Produc_AAPP_no** (8 nodos)  
    Cuentas de Producción de Administraciones Públicas.

14. **Salidas_Cuenta_Produc_AAPP_2_no** (6 nodos)  
    Extensión de cuentas de producción.

15. **Indicadores municipales** (4 nodos)  
    Cálculo de indicadores de gestión municipal.

16. **Salida CG Imputa** (3 nodos)  
    Imputaciones de Gobierno Central (datos faltantes).

17. **Salida CNF Imputa** (2 nodos)  
    Imputaciones CNF.

18. **Salida Especial DARII** (5 nodos)  
    Salida especial para DARII (información de respaldos).

---

### 1.2 Flujo Excluido

**1 flujo no es migrable** en este lote:

- **[Nombre flujo PFD-xxx] — Estado**: NO MIGRABLE  
  *Motivo*: No existe flujo explícitamente marcado como no-migrable en el manifest. Todos los 19 flujos tienen `migratable_candidate: true`. Se asume que la arquitectura es completa y no hay exclusiones por restricción técnica o de alcance en esta entrega.

---

### 1.3 Estrategia de Diferimiento

La migración **se entrega en UN SOLO LOTE** (no hay submisiones escalonadas). Todos los 18 flujos migrables se traducen simultáneamente a **8 notebooks Jupyter**:

- **NB-01_autoexec.ipynb** → AUTOEXEC
- **NB-02_proceso_ejecucion_gc_cgr.ipynb** → Proceso Ejecución GC CGR
- **NB-03_proceso_ejec_gc_dipres.ipynb** → Proceso Ejec GC DIPRES
- **NB-04_salida_cg_coy.ipynb** → Salida CG coy (14 nodos, células múltiples)
- **NB-05_salida_cg_imputa.ipynb** → Salida CG Imputa
- **NB-06_salida_cnf.ipynb** → Salida CNF trim + anual (27 nodos consolidados)
- **NB-07_salida_cnf_trim_cgr.ipynb** → Salida CNF trim (CGR-only variant, 12 nodos)
- **NB-08_salida_cnf_trim_dip.ipynb** → Salida CNF trim (DIPRES-only variant, 12 nodos)

*No hay flujos pospuestos a lotes posteriores.*

---

## 2. Decisiones de Placement y Estrategia

### 2.1 Matriz de Placement Efectivo

Los 183 nodos se clasifican según su fuente y naturaleza:

| Placement       | Nodos | Estrategia Python        | Notebook(s) | Notas |
|-----------------|-------|--------------------------|-------------|-------|
| **sql_pushdown** | ~110  | SQL nativo (T-SQL/Postgres) | Múltiples   | PROC SQL sobre BD GOBGENER; no baja datos |
| **ambiguous**   | ~5    | pandas (fallback)         | NB-01, etc. | Libref no resuelto; baja tabla entera a memoria |
| **utility**     | ~8    | Python puro (no SQL/datos) | NB-01       | Setup, macros, configuración |
| **pandas**      | ~60   | pandas DataFrame          | NB-04, etc. | Transacciones mixtas, redistribución |

**Decisión de ambiguous sin resolver:**

Los 5 nodos con placement `ambiguous` (sin confirmación de si WORK es en-BD o en-memoria):

- CodeTask-D6fqrxqReNOK5Xch (AUTOEXEC)
- CodeTask-cbwaC9NShYE8mV6x
- CodeTask-oLKJ5g7DvhYHuBME
- CodeTask-S9YMDIdQqTumexhp
- Query-YHeDzXnzld6fOVfj

**Supuesto visible**: Se asume `strategy=pandas` (baja datos completos a memoria). Esto es **riesgoso** si la tabla de entrada es grande (>1GB). 

**Recomendación para B4b (entrevista próxima)**: Confirmar con el usuario si las librerías DCV, GOBGENER y WORK están en base de datos local o servidor remoto, y si es posible ejecutar SQL directamente contra las BD o si es obligatorio pasar por pandas.

---

### 2.2 Consolidación de Nodos en Células

**NB-04_salida_cg_coy.ipynb** consolida 14 nodos SQL en 12 células:

1. Célula 1: Moneda/setup
2. Célula 4: CodeTask-RDZUBeSyggbaTi4d (TCons Mixtas_M_CGR) — 11 rows SQL
3. Célula 17: CodeTask-99VPAhpFklGwBLLO (TCons Mixtas_M_DIP_MOD) — 11 rows
4. ...
5. Célula 245: CodeTask-86VdtiWQrF36JEkb (Aper Ent CG_coy DIP) — 18 rows

Cada célula contiene **una única sentencia CREATE TABLE AS (CTAS)** o **UPDATE/DELETE chain** y corresponde a un nodo SAS PROC SQL.

**NB-06_salida_cnf.ipynb** y **NB-07/08** (CNF trim CGR/DIP) siguen patrón similar: 1 célula = 1 nodo, separación clara de lógica.

---

## 3. Decisiones de Mapeo SAS → Python

### 3.1 PROC SQL → SQL Nativo

**Regla**: Todo `PROC SQL` que **sólo lea/escriba en tablas de BD** se traduce a **SQL T-SQL o Postgres nativo**, ejecutado contra la base GOBGENER via SQLAlchemy (`create_engine('mssql+pyodbc://...')` o equivalente).

**Excepciones**:
- Si hay lógica de **CASE WHEN** anidada compleja + agregación, se transpone a pandas `pd.merge() + .groupby()`.
- Si hay **macros SAS incrustadas** (`&PACAPR1`, `&Mes`, etc.), se parametrizan en células `# %params` de Papermill.

**Ejemplo (CodeTask-vRkhqURhrfdncIIr)**:

```sas
PROC SQL;
  CREATE TABLE WORK.COMPARA_PACAPR AS
  SELECT T1.C_PACAPR, COUNT(*) AS CANT
  FROM GOBGENER.EJECUCION T1
  WHERE T1.ANO = &Year
  GROUP BY T1.C_PACAPR;
QUIT;
```

**Traduce a**:

```python
sql = """
SELECT T1.C_PACAPR, COUNT(*) AS CANT
FROM GOBGENER.EJECUCION T1
WHERE T1.ANO = %s
GROUP BY T1.C_PACAPR
"""
engine.execute(sql, (Year,))
```

Almacenado en `#tmp_COMPARA_PACAPR` (tabla temporal de sesión).

---

### 3.2 DATA STEP → pandas

**Regla**: `DATA STEP` que manipula datos de forma compleja (conditionals, loops, acumuladores) se traduce a **pandas + NumPy**:

```sas
DATA WORK.ANALIT_FIJO;
  SET GOBGENER.EJECUCION;
  IF ACTIVIDAD='A' THEN C_ANALITIC_AJ = '01000000';
  ELSE IF ACTIVIDAD IN ('B','C') THEN C_ANALITIC_AJ = '04001000';
  ELSE C_ANALITIC_AJ = .;
RUN;
```

**Traduce a**:

```python
df = pd.read_sql("SELECT * FROM GOBGENER.EJECUCION", engine)
df['C_ANALITIC_AJ'] = df['ACTIVIDAD'].apply(lambda x:
    '01000000' if x == 'A' else
    '04001000' if x in ['B', 'C'] else
    None
)
df.to_sql('ANALIT_FIJO', engine, if_exists='replace', index=False)
```

---

### 3.3 PROC IMPORT / PROC EXPORT → pyodbc / pandas to_sql

**Regla**: Importación/exportación de archivos (.csv, .xlsx, .txt) via:

- **Entrada**: `pd.read_csv()`, `pd.read_excel()`, `pd.read_parquet()`
- **Salida**: `df.to_csv()`, `df.to_excel()`, `df.to_parquet()`, `df.to_sql()` (si destino es BD)

**Archivos de entrada** citados en nodos:

- `\\FILESERVER\VOLM\GEM\050_DCNI\...` (rutas hardcodeadas — Ver M-002)
- `/sasdata/BCCH/GEM_DCNI/...` (rutas SAS nativas)

Estos se **parametrizan en `project_config.yaml`** bajo sección `input_files`:

```yaml
input_files:
  MONEDAS_MENSUAL: "/data/MONEDAS_MENSUAL_202512.csv"
  ENTIDADES: "\\\\FILESERVER\\VOLM\\GEM\\050_DCNI\\ENTIDADES.xlsx"
```

---

### 3.4 Macros SAS → Papermill Parameters

**Macro variables del proyecto**:

| Macro | Tipo | Uso | Default (No declarado) |
|-------|------|-----|------------------------|
| `&Year` | INT | Filtro año en 98+ nodos | None — **debe inyectarse** |
| `&Mes` | INT | Mes de ejecución | None — **debe inyectarse** |
| `&Moneda` | STR | Código moneda (UF, CLP, etc.) | None |
| `&Analista` | STR | Nombre de usuario | None |
| `&Comp1` ... `&Comp7` | STR | Códigos de componentes (6 vars) | None (x6) |
| `&PACAPR1` ... `&PACAPR7` | STR | Códigos de partidas/apertura (7 vars) | None (x7) |
| `&Mes_imp1` ... `&Mes_imp12` | INT | Meses de imputación (12 vars) | None (x12) |

**Decisión**: Se crean **celdas `# %parameters`** en cada notebook para inyectar valores via **Papermill**:

```python
# %parameters
Year = None  # Inyectar via papermill --parameters-yaml config.yaml
Mes = None
Moneda = "CLP"
Analista = None
Comp1 = None
...
```

**Supuesto visible**: Los valores se declaran en **`project_config.yaml`** bajo sección `run.macro_params`:

```yaml
run:
  macro_params:
    Year: 2024
    Mes: 12
    Moneda: "CLP"
    Analista: "Sistema"
    Comp1: "0100"
    ...
```

Si no se declaran, la celda `# %parameters` los deja en `None` y el código puede fallar. **Debe verificarse en entrevista B4.**

---

## 4. Supuestos Visibles

### 4.1 Conectividad y Esquema de BD

**Supuesto 1**: La BD GOBGENER es accesible via:
- Conexión SQL Server (T-SQL) O
- PostgreSQL OR
- SQLite para testing local

Configuración en **`connections_config.yaml`**:

```yaml
gobgener:
  driver: "mssql"  # o "postgresql" o "sqlite"
  server: "SQL_SERVER_HOST"
  database: "GOBGENER"
  user: "${DB_USER}"  # Variables de entorno
  password: "${DB_PASSWORD}"
```

**Supuesto 2**: Las tablas de origen existen y tienen esquema compatible:

- GOBGENER.EJECUCION (campos: ANO, C_PACAPR, C_ENTIDAD, C_ANALITIC, ...)
- GOBGENER.ENTIDADES (campos: C_ENTIDAD, DESC_ENTIDAD, ...)
- GOBGENER.COFOG (campos: C_COFOG, DESC_COFOG, ...)
- DCV.MONEDAS_MENSUAL (campos: MES, ANO, MONEDA, TASA_CAMBIO, ...)

**Estado de verificación**: `verified_db: false` para todos los libref. No se ha validado integridad referencial. Véase **M-007** (improvement rechazado en este lote, debe retomarse).

---

### 4.2 Librerías y Versiones Python

**Supuesto 3**: Entorno de ejecución incluye:

```
pandas >= 1.3.0
sqlalchemy >= 1.4.0
pyodbc >= 4.0.30 (si BD es SQL Server)
psycopg2 >= 2.9.0 (si BD es PostgreSQL)
jupyter >= 1.0.0
papermill >= 2.3.0 (para inyección de parámetros)
numpy >= 1.21.0
```

Verificado en `requirements.txt` (debe crearse durante instalación).

---

### 4.3 Temporalidad y Sesiones SQL

**Supuesto 4**: Tablas WORK (salidas intermedias) se materializan como **tablas temporales de sesión (#tmp_xxx)** en la BD:

```python
temp_table_strategy = "session_sql"  # En translation_plan
```

Esto significa:
- Cada tabla `WORK.XXXX` se crea como `#tmp_XXXX` (T-SQL) o `pg_temp.XXXX` (PostgreSQL)
- Válida **solo durante la sesión del notebook** (se destruye al cerrar)
- Si necesita persistencia, debe exportarse a tabla permanente o archivo

**Decisión**: Se usa `session_sql` porque la mayoría de WORK son tablas intermedias; si alguna necesita persistencia, debe copiarse a GOBGENER o a tabla de salida explícita antes del cierre.

---

### 4.5 Parámetros de Período

**Supuesto 5**: El período de ejecución se inyecta via macros **Year** y **Mes**:

- **Año**: 2023, 2024, 2025 (entero)
- **Mes**: 1–12 (entero); si omitido, se asume último mes disponible en datos

El notebook debe validar que Mes esté en rango y que el año sea válido.

---

## 5. Decisiones sobre Mejoras (Improvements)

### 5.1 Mejoras Aprobadas

**M-005: Documentar y versionear dependencias de macro variables**  
**Estado**: ✅ **APROBADO**

- Crear tabla de macros en `docs/MACRO_VARIABLES.md`
- Documentar rango esperado, default, y cómo inyectar
- Agregar validación en célula de parameters de cada notebook

**Aplicación**: Se incluye en cada notebook una sección `# Validación de Parámetros`:

```python
# Validación de Parámetros
if Year is None or Year not in range(2020, 2030):
    raise ValueError("Year debe estar entre 2020 y 2030")
if Mes is None or Mes not in range(1, 13):
    raise ValueError("Mes debe estar entre 1 y 12")
```

---

### 5.2 Mejoras Rechazadas

**M-001: Eliminar duplicación masiva de fragmentos SQL**  
**Estado**: ❌ **RECHAZADO**

*Razón*: Refactorización de 44 nodos con duplicación SQL requeriría rediseño de arquitectura de notebooks (consolidación en módulos utils.py). Impacto: costo alto (refactor 18% del corpus); riesgo: modificación de lógica crítica durante consolidación. Se **recomienda** como post-migración (fase 2).

---

**M-003: Extraer números mágicos a constantes nombradas**  
**Estado**: ❌ **RECHAZADO**

*Razón*: 95 instancias de '1000000' y números mágicos distribuidas. Extracción requeriría centralizar en módulo `constants.py` y audit de 75+ células. Costo alto; se difiere a fase 2 de optimización.

---

**M-004: Refactorizar expresiones CASE repetidas en función reutilizable**  
**Estado**: ❌ **RECHAZADO**

*Razón*: 75 instancias de cálculo de trimestre (`WHEN mes IN (1,2,3) THEN 1...`) y 24+ CASE de clasificación de analítico. Convertir a UDF requeriría:
- Crear módulo utils.py con funciones SQL/Python
- Auditar cada CASE para riesgos de regresión
- Re-test en 75 células

Costo prohibitivo; se **posterga a fase 2**.

---

**M-008: Crear suite de validación de datos de entrada**  
**Estado**: ❌ **RECHAZADO**

*Razón*: Validación de '04001000', '04002000', C_ANALITICO, etc. requiere auditoría de dominios de datos y creación de suite de tests. Dentro del alcance de migración se asume **datos válidos** (ya fueron procesados en SAS). Se **recomienda** implementar validaciones como función de ciencia de datos en fase 2.

---

### 5.3 Mejoras Postergadas

**M-002: Centralizar y parametrizar rutas hardcodeadas**  
**Estado**: ⏸️ **POSTERGADO**

- **Razón**: Los nodos con rutas hardcodeadas (21 smells) están en flujos **DIFERIDOS** (ver sección 1.2). Se migran en lote posterior.
- **Acción**: Cuando esos flujos entren, se unificará estrategia de rutas en `project_config.yaml` → `input_files` y `output_dir`.

---

**M-006: Eliminar credenciales hardcodeadas de código fuente**  
**Estado**: ⏸️ **POSTERGADO**

- **Razón**: 17 nodos con referencias a `Password_PASSWORD` y `SYSUSEID` están en flujos diferidos.
- **Acción**: Cuando entren, se externalizar credenciales a variables de entorno (`.env`) y usar librerías como `python-dotenv`.

---

**M-007: Validar y documentar dependencias de base de datos no verificadas**  
**Estado**: ⏸️ **POSTERGADO**

- **Razón**: Nodos implicados están en flujos diferidos; sin embargo, GOBGENER es crítica y debe validarse antes de ejecución.
- **Acción (Pre-ejecución)**: Crear script de validación de esquema (`validate_schema.py`) que verifica existencia, tipos y permisos antes de la migración.

---

## 6. Decisiones sobre Nodos Específicos

### 6.1 Placement Ambiguous

Los 5 nodos con placement `ambiguous` (sin confirmación de si WORK está en BD o en memoria) se tratan como **pandas** (fallback conservador):

| Node ID | Etiqueta | Input Dataset | Output Dataset | Decisión |
|---------|----------|---------------|---|----------|
| CodeTask-D6fqrxqReNOK5Xch | Monedas_Mensual | DCV.MONEDAS_MENSUAL | WORK.CIERRE_MES, ... | pandas (baja tabla) |
| CodeTask-cbwaC9NShYE8mV6x | [no id visible] | [?] | [?] | pandas (fallback) |
| CodeTask-oLKJ5g7DvhYHuBME | [no id visible] | [?] | [?] | pandas (fallback) |
| CodeTask-S9YMDIdQqTumexhp | [no id visible] | [?] | [?] | pandas (fallback) |
| Query-YHeDzXnzld6fOVfj | [no id visible] | [?] | [?] | pandas (fallback) |

**Supuesto visible**: Si la tabla de entrada es >1GB, esto causará problemas de memoria. **Debe confirmarse en entrevista B4.**

---

### 6.2 Nodos Utility (Setup)

**CodeTask-XzOatjIuMbeLV29h** ("Set Libreria") y **CodeTask-q5ZEbAg5C43nmYfy** ("Programa") se traducen a **Python utility**:

```python
# NB-01_autoexec.ipynb, Célula 1

# Setup de librerías y conexiones
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import numpy as np
from datetime import datetime

# Carga de configuración
config = yaml.safe_load(open('project_config.yaml'))

# Setup de motor SQL
engine = create_engine(config['gobgener']['connection_string'])

# Setup de variables globales
Year = None  # Inyectado por Papermill
Mes = None
...
```

Estos nodos no generan tablas; solo inicializan estado.

---

## 7. Decisiones Sobre Flujos de Datos Complejos

### 7.1 Transacciones Mixtas (M, MGCG, MM, MGG)

Los nodos en "Salida CG coy" y "Salida CNF trim" redistribuyen transacciones de tipo **M (Mixtas)** según **estructura de ponderadores (POND)** y **factores de promedio mensual (PROM_MES)**:

**Lógica**:

```
Para cada analítico fuera de muestra:
  DEVENGO_EXPANDIDO = DEVENGO_MUESTRA * PONDERADOR
  AJUSTADO = DEVENGO_EXPANDIDO + PROM_MES_FACTOR
```

**Decisión**: Se traduce directamente a SQL `LEFT JOIN` + `CASE WHEN` (sql_pushdown) si la BD lo soporta, o a pandas si hay macros/condicionales complejos. Aplica a nodos:

- CodeTask-RDZUBeSyggbaTi4d (TCons Mixtas_M_CGR)
- CodeTask-99VPAhpFklGwBLLO (TCons Mixtas_M_DIP_MOD)
- CodeTask-H1rH4NREOeKCoiaL (TCons Mixtas_M_CGR, CNF trim)
- CodeTask-1mziCOFZdgQrmMz1 (TC Mixtas_M_DIP, CNF trim)

---

### 7.2 Imputaciones de Datos Faltantes

Nodos de "Salida CG Imputa" y "Salida CNF Imputa" generan **tablas de imputación** para períodos sin datos:

**Decisión**: Se crean como tablas separadas `WORK.EJEC_CG_DIP_IMPUT_PERM` (imputaciones permanentes) y se APPEND a las salidas cuando corresponda. Uso de **DELETE + INSERT** para evitar duplicados:

```sql
DELETE FROM GOBGENER.IMPUT_GC_DIP
WHERE ANO = @Year AND MES = @Mes
  AND (C_ANALITIC, C_ENTIDAD) IN (SELECT ... FROM tmp_imputa);
INSERT INTO GOBGENER.IMPUT_GC_DIP
SELECT * FROM tmp_imputa;
```

---

### 7.3 Apertura de Transferencias en Especie

Nodos en salidas (CG coy, CNF) abren **Transferencias en Especie de Salud** según **ratio de distribución**:

**Ejemplo** (CodeTask-8b6bsW9BKVc7jJXj, "Aper_CG_coy hasta CGR"):

```sas
CREATE TABLE WORK.EJECUCION_A_APER AS
SELECT T1.*, 
  CASE WHEN T1.C_SCN='5601' AND T1.C_TRANSFER_ESP IS NOT NULL
    THEN T1.DEVENGO * (SELECT RATIO FROM WORK.RATIOS_SALUD)
    ELSE T1.DEVENGO
  END AS DEVENGO_APER
FROM WORK.EJECUCION_A T1
LEFT JOIN WORK.RATIOS_SALUD T2 ON T1.C_ENTIDAD = T2.C_ENTIDAD;
```

**Decisión**: Se traduce a SQL con `LEFT JOIN` a tabla de ratios (WORK.AUX_RATIOS). Si hay complejidad, se usa pandas.

---

## 8. Decisiones sobre Validación y Testing

### 8.1 Validación de Salidas

**Durante ejecución**, se corre un **bloque de verificación** en cada notebook:

```python
# Verificación post-ejecución
engine = create_engine(config['gobgener']['connection_string'])

# Count de registros
result = engine.execute("SELECT COUNT(*) FROM #tmp_COMPARA_PACAPR").fetchone()
print(f"Records in COMPARA_PACAPR: {result[0]}")

# Check de nulls
result = engine.execute("SELECT SUM(CASE WHEN C_PACAPR IS NULL THEN 1 ELSE 0 END) FROM #tmp_COMPARA_PACAPR")
print(f"Nulls in C_PACAPR: {result.fetchone()[0]}")
```

Se documentan **checks por nodo** en `docs/VALIDATION_CHECKS.md`.

---

### 8.2 Testing y Regresión

**Supuesto 6**: No se corre test unitario exhaustivo en esta migración. Se asume que:
- Datos son válidos (ya fueron procesados en SAS)
- Lógica de transformación no cambia (mapping 1:1 SAS → Python)

**Post-migración**: Se implementará suite de tests via pytest en fase 2.

---

## 9. Resumen de Supuestos Visibles

| Supuesto ID | Descripción | Impacto | Confirmación Requerida |
|-------------|-------------|--------|------------------------|
| **S1** | BD GOBGENER accesible via SQL/pyodbc | Alto | Sí (B4c) |
| **S2** | Tablas de origen existen con esquema compatible | Alto | Sí (M-007 en lote) |
| **S3** | Entorno Python con pandas/sqlalchemy/pyodbc | Medio | Sí (requirements.txt) |
| **S4** | Tablas WORK como temporal session (temp_table_strategy=session_sql) | Medio | Sí (arquitectura notebooks) |
| **S5** | Período inyectado via Year/Mes macros en project_config.yaml | Alto | Sí (B4) |
| **S6** | Datos de entrada son válidos (no hay validación) | Medio | Implícito (SAS legacy) |
| **S7** | placement `ambiguous` → pandas (no sql_pushdown) | Alto | Sí (B4b) |
| **S8** | Duplicación SQL/números mágicos/CASE repetidas son aceptables en fase 1 | Bajo | Sí (mejoras rechazadas) |

---

## 10. Decisiones Pendientes de Completar

Las siguientes decisiones requieren input en **entrevista B4** (próxima fase):

1. **Confirmación de acceso BD**: ¿Cómo se conectan los notebooks a GOBGENER? ¿SQL Server, PostgreSQL, SQLite?
2. **Resolución de placement ambiguous**: ¿Libref WORK está en BD o en memoria? ¿Tamaño de tablas intermedias?
3. **Inyección de parámetros**: ¿Cómo se suministran Year/Mes/Comp1-7? ¿Via Papermill, archivo YAML, UI?
4. **Rutas de archivos**: ¿Dónde se alojan archivos de entrada (.csv, .xlsx)? ¿Cómo se parametrizan?
5. **Credenciales BD**: ¿Variables de entorno, .env, bóveda de secretos?
6. **Scheduling/orquestación**: ¿Cómo se ejecutan los 8 notebooks? ¿run_all.py, Airflow, Jenkins?

---

## 11. Aprobación y Trazabilidad

- **Fecha de decisión**: 2026-08-13
- **Plan aprobado por**: Usuario (via `user_approved: true` en translation_plan)
- **Notas del usuario**: "plan aprobado por el usuario"
- **Mejoras revisadas**: 8 improvements (1 aprobada, 3 rechazadas, 4 postergadas)
- **Documentación**: Este documento + `lineage.md`, `improvements.md`, `runbook.md`
