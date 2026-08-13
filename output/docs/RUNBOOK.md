# Runbook: Operación del Proyecto Proc_Salidas_Gob_REV_mig-2

## Introducción

Este runbook describe los procedimientos operacionales para ejecutar la migración de SAS a Python del proyecto **Proc_Salidas_Gob_REV_mig-2**. El pipeline completo consta de 18 flujos migrables, traducidos a 8 notebooks Python con estrategias de ejecución variadas (pandas, SQL pushdown, Python puro). Cubre: orden de ejecución, parametrización, validación de salidas y resolución de fallos comunes.

---

## 1. Requisitos previos

### 1.1 Entorno Python
- **Versión:** Python 3.9+
- **Paquetes requeridos:**
  - `pandas` >= 1.3.0
  - `sqlalchemy` >= 1.4.0
  - `pyodbc` (para conexión a SQL Server)
  - `numpy` >= 1.20.0
  - `jupyter` >= 1.0.0 (para ejecutar notebooks)

### 1.2 Acceso a bases de datos
- **SQL Server:** Conexión con credenciales de lectura/escritura a librería `GOBGENER`
- **Tablas críticas de entrada:**
  - `GOBGENER.EJECUCION` (ejecución presupuestaria CGR)
  - `GOBGENER.EJEC_DIPRES` (ejecución presupuestaria DIPRES)
  - `GOBGENER.ENTIDADES` (catálogo de entidades)
  - `GOBGENER.COFOG` (clasificación de función)
  - `GOBGENER.MONEDAS_MENSUAL` (tasas de cambio diarias)
  - Tablas de apertura: `CR18_T_SCN_1`, `CR18_T_SCN_2`, `CR18_APERTURA`, `T_SCN_2`

### 1.3 Estructura de directorios
```
output/
├── NB-01_autoexec.ipynb
├── NB-02_proceso_ejecucion_gc_cgr.ipynb
├── NB-03_proceso_ejec_gc_dipres.ipynb
├── NB-04_salida_cg_coy.ipynb
├── NB-05_salida_cg_anual.ipynb
├── NB-06_salida_cnf_coy.ipynb
├── NB-07_salida_cnf_trim_cgr.ipynb
├── NB-08_salida_cnf_trim_dip.ipynb
├── run_all.py
└── logs/
    └── execution.log
```

---

## 2. Parametrización del período de ejecución

### 2.1 Macro variables requeridas
El pipeline utiliza las siguientes macro variables, que deben declararse **antes** de ejecutar los notebooks. Se recomienda centralizar en un archivo `config.yaml`:

| Variable | Tipo | Descripción | Ejemplo | Obligatoria |
|----------|------|-------------|---------|-------------|
| `Year` | int | Año fiscal de ejecución | `2024` | Sí |
| `Mes` | int | Mes actual (1-12) | `6` | Sí |
| `Analista` | str | Nombre del analista ejecutor | `"Juan_Pérez"` | No |
| `Comp1`–`Comp7` | str | Códigos de comparación (valores históricos) | `"2023"` | Condicional |
| `Moneda` | str | Código de moneda | `"CLP"` | Condicional |
| `Mes_imp1`–`Mes_imp12` | int | Meses de imputación (lista de meses a imputa) | `1,2,3` | No |
| `PACAPR1`–`PACAPR7` | str | Paquetes de apertura | `"AAPP"` | Condicional |

**Inyección de parámetros:**

En `run_all.py` o al ejecutar notebook individual:
```python
# Opción 1: Variables de entorno (recomendado)
import os
year = int(os.getenv("EXEC_YEAR", "2024"))
mes = int(os.getenv("EXEC_MES", "6"))

# Opción 2: Diccionario de parámetros (notebook)
params = {
    "Year": 2024,
    "Mes": 6,
    "Analista": "Juan_Pérez",
    "Comp1": "2023",
    "Moneda": "CLP"
}
```

**Nota importante:** Variables sin declaración explícita quedarán como `None` en la celda `parameters`. Consultar `project_config.yaml` o la documentación de mejoras M-005 para validar valores por defecto.

---

## 3. Orden de ejecución de notebooks

### 3.1 Dependencias y orden secuencial

El pipeline sigue este orden obligatorio (dependencias lógicas de datos):

#### **Lote 1: Inicialización**
1. **NB-01_autoexec.ipynb** (3 nodos, ~2 min)
   - Establece librerías Python (WORK)
   - Procesa monedas mensuales (DCV.MONEDAS_MENSUAL → WORK.CIERRE_MES, PROM_MES, etc.)
   - **Entrada:** DCV.MONEDAS_MENSUAL
   - **Salida:** WORK.CIERRE_MES, WORK.CIERRE_TRIM, WORK.PROM_MES, WORK.PROM_MES_TODAS, WORK.PROM_TRIM
   - **Supuesto:** La base DCV debe estar disponible y accesible

#### **Lote 2: Validación de ejecución (CGR)**
2. **NB-02_proceso_ejecucion_gc_cgr.ipynb** (31 nodos, ~8–12 min)
   - Compara cambios en nomenclatura de entidades y partidas
   - Valida consistencia de estructuras COFOG y analíticos
   - Genera 80+ tablas de clasificación y CHECK
   - **Entrada:** GOBGENER.EJECUCION, GOBGENER.ENTIDADES, tablas de apertura CR18_*
   - **Salida:** GOBGENER.ANALIT_TCONS, WORK.CHECK_* (45+ tablas de validación)
   - **Dependencia:** Requiere NB-01 ejecutado (aunque sin dependencia directa de WORK)
   - **Supuesto:** Las macros `Year`, `Comp1`–`Comp7` deben estar inicializadas

#### **Lote 3: Validación de ejecución (DIPRES)**
3. **NB-03_proceso_ejec_gc_dipres.ipynb** (10 nodos, ~4–6 min)
   - Valida estructuras analíticas de ejecución DIPRES
   - Genera clasificaciones y tablas de consistencia
   - **Entrada:** GOBGENER.EJEC_DIPRES, GOBGENER.ENTIDADES, tablas de NB-02
   - **Salida:** WORK.ANALIT_*_D, WORK.CHECK_* (variantes DIPRES)
   - **Dependencia:** **Requiere NB-02 completado** (consume WORK.CRUCE_*, CHECK_*)

#### **Lote 4: Salidas de coyuntura**
4. **NB-04_salida_cg_coy.ipynb** (14 nodos, ~6–10 min)
   - Consolida ejecución presupuestaria de Gobierno Central de coyuntura
   - Redistribuye transacciones mixtas (muestra + expansión)
   - Genera EJECUCION_CG_CGR, EJECUCION_CG_DIP, imputaciones
   - **Entrada:** WORK.CHECK_*, WORK.CRUCE_*, GOBGENER.*, WORK.PROM_MES (de NB-01)
   - **Salida:** GOBGENER.IMPUT_GC_DIP, WORK.EJECUCION_CG_*, WORK.RATIOS, WORK.TOTALES
   - **Dependencia:** **Requiere NB-02, NB-03 completados**

5. **NB-05_salida_cg_anual.ipynb** (12 nodos, ~4–8 min) *[opcional en este lote]*
   - Consolidación anual de Gobierno Central
   - **Entrada:** WORK.EJECUCION_CG_*, GOBGENER.IMPUT_*
   - **Salida:** WORK.EJECUCION_CG_ANUAL, WORK.TOTALES_ANUAL
   - **Dependencia:** **Requiere NB-04 completado**

6. **NB-06_salida_cnf_coy.ipynb** (11 nodos, ~5–7 min) *[opcional en este lote]*
   - Consolidación de coyuntura para Cuentas Nacionales Financieras (CNF)
   - **Entrada:** WORK.EJECUCION_*, GOBGENER.*, WORK.RATIOS, WORK.TOTALES
   - **Salida:** WORK.EJECUCION_CNF_*, WORK.INGRESOS_MUNIC
   - **Dependencia:** **Requiere NB-04 completado**

#### **Lote 5: Salidas trimestrales (CNF)**
7. **NB-07_salida_cnf_trim_cgr.ipynb** (9 nodos, ~4–6 min) *[opcional en este lote]*
   - Consol. trimestral CNF (fuente CGR)
   - **Entrada:** WORK.EJECUCION_CG_CGR, WORK.PROM_MES
   - **Salida:** WORK.SALIDA_CNF_trim, WORK.INGRESOS_MUN_TRIM
   - **Dependencia:** **Requiere NB-04 completado + datos anuales disponibles**

8. **NB-08_salida_cnf_trim_dip.ipynb** (11 nodos, ~5–7 min) *[opcional en este lote]*
   - Consol. trimestral CNF (fuente DIPRES)
   - **Entrada:** WORK.EJECUCION_CG_DIP, WORK.PROM_MES
   - **Salida:** WORK.APER_CNF_trim_DIP, WORK.SALIDA_CNF_trim_DIP
   - **Dependencia:** **Requiere NB-04, NB-07 completados**

### 3.2 Diagrama de dependencias
```
NB-01 (AUTOEXEC)
   ↓
NB-02 (Proceso CGR)
   ↓
NB-03 (Proceso DIPRES) → NB-04 (Salida CG Coy)
                             ↓
                        NB-05 (Salida CG Anual)
                             ↓
                        NB-06 (Salida CNF Coy)
                             ↓
                        NB-07 (Salida CNF Trim CGR)
                             ↓
                        NB-08 (Salida CNF Trim DIP)
```

**En este lote se migran completamente:** NB-01 a NB-04 (4/8 notebooks).  
**Diferidos para próximo lote:** NB-05, NB-06, NB-07, NB-08 (4/8 notebooks) — ver sección 9.

---

## 4. Ejecución del pipeline

### 4.1 Opción A: Ejecución secuencial manual (jupyter notebook)

Para cada notebook en orden:
```bash
jupyter notebook output/NB-01_autoexec.ipynb
# Ejecutar todas las celdas (Kernel → Restart & Run All)
# Verificar logs en la última celda antes de continuar

jupyter notebook output/NB-02_proceso_ejecucion_gc_cgr.ipynb
# Idem.

jupyter notebook output/NB-03_proceso_ejec_gc_dipres.ipynb
# Idem.

jupyter notebook output/NB-04_salida_cg_coy.ipynb
# Idem.
```

**Ventaja:** Control granular, debugging paso-a-paso.  
**Desventaja:** Manual, lento, riesgo de saltar etapas.

### 4.2 Opción B: Ejecución automática (run_all.py) — Recomendado

Script maestro que orquesta la ejecución de todos los notebooks:

```bash
# Instalación de dependencias
pip install -r requirements.txt

# Ejecución con parámetros
export EXEC_YEAR=2024
export EXEC_MES=6
export EXEC_ANALISTA="Juan_Pérez"
python run_all.py --year 2024 --mes 6 --analista "Juan_Pérez"
```

**Flujo interno:**
1. Valida parámetros de entrada
2. Crea directorio `logs/` si no existe
3. Ejecuta NB-01 → NB-02 → NB-03 → NB-04 (+ NB-05 a NB-08 en lotes posteriores)
4. Captura stderr/stdout en `logs/execution.log`
5. Genera reporte de estado por notebook (✓ PASS / ✗ FAIL)
6. Si un notebook falla, detiene y genera alertas

**Ventaja:** Reproducibilidad, auditoría automática, sin intervención.  
**Desventaja:** Si falla un nodo, requiere rollback manual.

### 4.3 Inyección de parámetros (project_config.yaml)

Crear archivo `project_config.yaml` en el directorio raíz:
```yaml
run:
  year: 2024
  mes: 6
  analista: "Juan_Pérez"
  macro_params:
    Year: 2024
    Mes: 6
    Comp1: "2023"
    Comp2: "2022"
    Comp3: "2021"
    Comp4: "2020"
    Comp5: "2019"
    Comp6: "2018"
    Comp7: "2017"
    Moneda: "CLP"
    Mes_imp1: 1
    Mes_imp2: 2
    # ... hasta Mes_imp12
    PACAPR1: "AAPP"
    PACAPR2: "SSPP"
    # ... hasta PACAPR7

database:
  server: "SQL_SERVER_NAME"
  database: "GOBGENER"
  driver: "ODBC Driver 17 for SQL Server"
  # Credenciales: usar variables de entorno, NO hardcode
  # trusted_connection: true (recomendado para Windows)
```

Lectura en `run_all.py`:
```python
import yaml

with open("project_config.yaml", "r") as f:
    config = yaml.safe_load(f)

year = config["run"]["year"]
mes = config["run"]["mes"]
# ... etc.
```

---

## 5. Validación de salidas tras ejecución

### 5.1 Verificaciones inmediatas post-notebook

Tras ejecutar cada notebook, verificar:

#### **NB-01 (AUTOEXEC)**
- [ ] Tabla `WORK.CIERRE_MES` existe y contiene 12 filas (1 por mes)
- [ ] Tabla `WORK.PROM_MES` contiene promedios de tasa de cambio
- [ ] Sin errores de conexión a DCV.MONEDAS_MENSUAL
- Comando de verificación:
  ```python
  df = pd.read_sql("SELECT COUNT(*) as cnt FROM [WORK].[CIERRE_MES]", conn)
  assert df['cnt'][0] == 12, "CIERRE_MES debe tener 12 registros (1 por mes)"
  ```

#### **NB-02 (Proceso CGR)**
- [ ] Tabla `WORK.COMPARA_PACAPR` contiene comparativas de período anterior
- [ ] Tabla `WORK.COMPARA_ENTIDAD` sin valores NULL en columna ENTID
- [ ] Número de filas en `WORK.CHECK_TCONS_P` vs `WORK.CHECK_TCONS` < 5% (tolerancia de diferencias)
- [ ] Sin excepciones en logs (buscar "ERROR" en execution.log)
- Verificación:
  ```python
  checks = ["CHECK_TCONS", "CHECK_COFOG_ENTID", "CHECK_ANALIT_VAR"]
  for table in checks:
      df = pd.read_sql(f"SELECT COUNT(*) as cnt FROM WORK.[{table}]", conn)
      print(f"{table}: {df['cnt'][0]} registros")
  ```

#### **NB-03 (Proceso DIPRES)**
- [ ] Tabla `WORK.ANALIT_ENTIDAD_VAR_D` contiene clasificaciones DIPRES
- [ ] Tabla `WORK.CHECK_TCONS_D` sin datos "faltantes" marcados (NULL en columna ANALÍTICO)
- [ ] Número de registros en CHECK_* DIPRES vs CGR dentro de 10% (variación aceptada)
- Verificación:
  ```python
  df_cgr = pd.read_sql("SELECT COUNT(*) as cnt FROM WORK.CHECK_TCONS_P", conn)
  df_dip = pd.read_sql("SELECT COUNT(*) as cnt FROM WORK.CHECK_TCONS_D", conn)
  variación = abs(df_cgr['cnt'][0] - df_dip['cnt'][0]) / df_cgr['cnt'][0]
  assert variación <= 0.10, f"Variación DIPRES vs CGR: {variación*100:.1f}% (máx 10%)"
  ```

#### **NB-04 (Salida CG Coy)**
- [ ] Tabla `WORK.EJECUCION_CG_CGR` contiene ejecución del período vigente
- [ ] Tabla `GOBGENER.IMPUT_GC_DIP` actualizada con imputaciones de DIPRES
- [ ] Sumas de `EJECUCION_CG_CGR.MONTO` = suma de `EJECUCION.MONTO` por período (tolerancia ±1%)
- [ ] Tabla `WORK.TOTALES` contiene agregados por concepto
- Verificación:
  ```python
  df_salida = pd.read_sql(
      f"SELECT SUM(MONTO) as total FROM WORK.EJECUCION_CG_CGR WHERE YEAR={year} AND MES={mes}", 
      conn
  )
  df_origen = pd.read_sql(
      f"SELECT SUM(MONTO) as total FROM GOBGENER.EJECUCION WHERE YEAR={year} AND MES={mes}", 
      conn
  )
  
  diff_pct = abs(df_salida['total'][0] - df_origen['total'][0]) / df_origen['total'][0]
  assert diff_pct <= 0.01, f"Diferencia de montos: {diff_pct*100:.2f}% (máx 1%)"
  ```

### 5.2 Validaciones de negocio (checks mensuales)

Aplicar los siguientes checks **obligatorios** tras completar NB-04:

| Check | Consulta | Umbral | Acción |
|-------|---------|--------|--------|
| **Integridad de entidades** | `SELECT COUNT(DISTINCT ENTIDAD) FROM WORK.EJECUCION_CG_CGR WHERE YEAR=? AND MES=?` | ≥ 80% de catálogo GOBGENER.ENTIDADES | Si < 80%, investigar filtros no documentados |
| **Montos positivos** | `SELECT COUNT(*) FROM WORK.EJECUCION_CG_CGR WHERE MONTO < 0 AND YEAR=? AND MES=?` | = 0 (sin negativos) | Si > 0, revisar lógica de signos en transformaciones |
| **Cobertura de analíticos** | `SELECT COUNT(DISTINCT C_ANALITICO) FROM WORK.EJECUCION_CG_CGR WHERE YEAR=? AND MES=?` | ≥ 90% respecto a período anterior | Si < 90%, validar cambios en nomenclatura |
| **Imputaciones aplicadas** | `SELECT SUM(MONTO) FROM GOBGENER.IMPUT_GC_DIP WHERE YEAR=? AND MES=?` | > 0 (debe haber imputaciones) | Si = 0, revisar lógica de imputación en NB-04 |
| **Duplicados** | `SELECT ENTIDAD, CUENTA, ITEM, COUNT(*) as cnt FROM WORK.EJECUCION_CG_CGR WHERE YEAR=? AND MES=? GROUP BY ENTIDAD, CUENTA, ITEM HAVING cnt > 1` | 0 duplicados | Si hay duplicados, FAIL y escalate |

---

## 6. Resolución de fallos comunes

### 6.1 Fallos de conexión a base de datos

**Síntoma:** Error `pyodbc.OperationalError: ('HY000', '[HY000] [Microsoft][ODBC Driver 17 for SQL Server]...') (Error -1) SQLSTATE: HY000`

**Causa probable:**
- Servidor SQL Server no disponible
- Credenciales incorrectas o vencidas
- Driver ODBC no instalado o versión incompatible

**Resolución:**
1. Verificar conectividad:
   ```bash
   # Windows (PowerShell)
   Test-NetConnection -ComputerName SQL_SERVER_NAME -Port 1433
   
   # Linux/Mac
   nc -zv SQL_SERVER_NAME 1433
   ```
2. Validar credenciales (si no usa Windows auth):
   ```python
   import pyodbc
   try:
       conn = pyodbc.connect(
           f"Driver=ODBC Driver 17 for SQL Server;"
           f"Server={server};"
           f"Database={database};"
           f"UID={uid};"
           f"PWD={pwd};"
       )
       print("✓ Conexión exitosa")
   except Exception as e:
       print(f"✗ Error: {e}")
   ```
3. Instalar driver ODBC si no existe:
   ```bash
   # Ubuntu/Debian
   sudo apt install odbc-mssql
   
   # macOS
   brew install mssql-tools
   
   # Windows: descargar desde Microsoft
   ```

### 6.2 Macro variables no inicializadas

**Síntoma:** En notebook, celda `parameters` muestra: `Year is None`, `Mes is None`, etc.

**Causa probable:**
- Parámetros no inyectados (archivo config.yaml no existe o no se leyó)
- Variables declaradas como comentarios en notebook pero no ejecutadas

**Resolución:**
1. Crear `project_config.yaml` (ver sección 4.3)
2. En notebook, celda `parameters` debe leer config:
   ```python
   import yaml
   with open("../project_config.yaml", "r") as f:
       config = yaml.safe_load(f)
   
   Year = config["run"]["macro_params"]["Year"]
   Mes = config["run"]["macro_params"]["Mes"]
   print(f"✓ Parámetros cargados: Year={Year}, Mes={Mes}")
   ```
3. Alternativa: pasar vía `papermill` (pytest-notebook):
   ```bash
   papermill input.ipynb output.ipynb -p Year 2024 -p Mes 6
   ```

### 6.3 Tabla de entrada no existe o está vacía

**Síntoma:** Error `ProgrammingError: ('42S02', "[42S02] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]Invalid object name 'GOBGENER.MONEDAS_MENSUAL'. (Error 208) SQLSTATE: 42S02")`

**Causa probable:**
- Tabla no existe en BD (ej. DCV.MONEDAS_MENSUAL en NB-01)
- Permissions insuficientes (usuario no tiene SELECT en la tabla)
- Tabla vacía para el período solicitado

**Resolución:**
1. Verificar existencia:
   ```sql
   SELECT * FROM INFORMATION_SCHEMA.TABLES 
   WHERE TABLE_SCHEMA = 'DCV' AND TABLE_NAME = 'MONEDAS_MENSUAL'
   ```
2. Validar permisos (consultar admin BD):
   ```sql
   SELECT * FROM GOBGENER.MONEDAS_MENSUAL LIMIT 5
   ```
3. Si tabla vacía para el período:
   - Contactar al propietario de datos (ver sección 7)
   - Usar fallback: copiar datos de período anterior como seed

### 6.4 Fallo en transformación de datos (tipo, precision, NULL)

**Síntoma:** Error `ValueError: Unable to parse string "" at position 123 for dtype('float64')` o `TypeError: unsupported operand type(s)...`

**Causa probable:**
- Columna numérica contiene valores basura o strings vacíos
- Incompatibilidad de tipos en JOIN (ej. int vs str en ENTIDAD)
- Conversión de fecha fallida

**Resolución:**
1. Inspeccionar data antes de transformar:
   ```python
   df = pd.read_sql("SELECT TOP 100 * FROM GOBGENER.EJECUCION", conn)
   print(df.dtypes)
   print(df.isnull().sum())
   print(df[['ENTIDAD', 'MONTO']].head(20))
   ```
2. Limpiar en pandas:
   ```python
   # Convertir MONTO a float, reemplazando valores inválidos
   df['MONTO'] = pd.to_numeric(df['MONTO'], errors='coerce').fillna(0)
   
   # Convertir ENTIDAD a string normalizado
   df['ENTIDAD'] = df['ENTIDAD'].astype(str).str.strip()
   ```
3. Reejecutar notebook tras limpieza

### 6.5 SQL pushdown: tabla temporal (#tmp) no encontrada

**Síntoma:** Error `ProgrammingError: ('42S02', "[42S02]... Invalid object name '#CRUCE_FIJO'. (Error 208)")` al ejecutar NB-02 o NB-03

**Causa probable:**
- Tabla temporal creada en una sesión, referenciada en otra (timeout de sesión)
- SQL Server reciclò la conexión entre celdas
- Múltiples notebooks en paralelo compitiendo por nombres de #tmp

**Resolución:**
1. **Garantizar sesión SQL persistente** en notebook:
   ```python
   # Al inicio de NB-02
   global sql_session
   from sqlalchemy import create_engine
   
   engine = create_engine(
       f"mssql+pyodbc:///?odbc_connect={connection_string}",
       fast_executemany=True
   )
   sql_session = engine.raw_connection()
   
   # Reutilizar sql_session en todas las celdas
   ```
2. **Usar nombres #tmp únicos** por notebook:
   ```sql
   CREATE TABLE #CRUCE_FIJO_NB02_20240601 AS ...
   ```
3. **Evitar parallelización** en este lote (ver sección 8)

### 6.6 Timeout en consultas grandes (PROC_SQL → SQL pushdown)

**Síntoma:** Error `TimeoutError: MySQL server has gone away` o timeout tras 300s

**Causa probable:**
- Consulta con múltiples JOINs (10+) contra tablas GOBGENER grandes (1M+ rows)
- Índices faltantes en BD
- Estrategia `sql_pushdown` procesando todo en servidor sin límite

**Resolución:**
1. Aumentar timeout en conexión:
   ```python
   engine = create_engine(
       connection_string,
       connect_args={'timeout': 600}  # 10 minutos
   )
   ```
2. Particionar consulta en pasos (materializar #tmp intermedios):
   ```sql
   -- En lugar de: SELECT ... FROM A JOIN B JOIN C JOIN D JOIN E...
   -- Hacer:
   CREATE TABLE #step1 AS SELECT ... FROM A JOIN B;
   CREATE TABLE #step2 AS SELECT ... FROM #step1 JOIN C;
   CREATE TABLE #step3 AS SELECT ... FROM #step2 JOIN D;
   ```
3. Validar índices en BD (consultar DBA)

### 6.7 Mejoras pendientes (M-001 a M-008): impacto operacional

**Nota importante:** La validación detectó 8 mejoras, de las cuales:
- **M-001 (eliminar SQL duplicado):** RECHAZADA → sin aplicar
- **M-002 (centralizar rutas):** POSTERGADA → incluir en próximo lote
- **M-003 (números mágicos):** RECHAZADA → sin aplicar
- **M-004 (CASE statements):** RECHAZADA → sin aplicar
- **M-005 (versionado macros):** APROBADA → ver supuestos en decisions.md
- **M-006 (credenciales):** POSTERGADA → incluir en próximo lote
- **M-007 (BD no verificadas):** POSTERGADA → incluir en próximo lote
- **M-008 (validación datos):** RECHAZADA → sin aplicar

**Operativamente:** No hay cambios obligatorios en este lote derivados de mejoras. Los supuestos visibles (M-005 sobre macro variables) quedan reflejados en `project_config.yaml`.

---

## 7. Contactos y escaladas

### 7.1 Puntos de contacto del proceso

Para cada tipo de fallo/pregunta, contactar a:

| Tema | Contacto | Teléfono | Correo | Disponibilidad |
|------|----------|----------|--------|-----------------|
| **Datos (BD GOBGENER, EJECUCION, ENTIDADES)** | Área de Datos Presupuestarios | [Pendiente] | [Pendiente] | L–V 08:00–17:00 |
| **Tablas de cambio (DCV.MONEDAS_MENSUAL)** | Área de Tesorería | [Pendiente] | [Pendiente] | L–V 08:00–17:00 |
| **Credenciales y acceso SQL Server** | DBA / IT Security | [Pendiente] | [Pendiente] | L–V 09:00–18:00 |
| **Parámetros de negocio (Comp*, PACAPR*, Mes_imp*)** | Jefe de Análisis de Ejecución | [Pendiente] | [Pendiente] | Previa cita |
| **Validación de salidas (checks mensuales)** | Auditoría Interna / Contabilidad | [Pendiente] | [Pendiente] | Semana de cierre |
| **Problemas técnicos (Python, notebooks, logs)** | Equipo de Migración (SAS → Python) | [Pendiente] | [Pendiente] | Soporte 24h en periodos críticos |

**Nota:** Los contactos aparecen como "[Pendiente]" — completar con información real antes de operacionalizar.

### 7.2 Escalación de fallos críticos

Definir nivel de severidad:

- **CRITICAL (rojo):** Pipeline fallido, salidas no generadas → Escalar a Jefe de Área + DBA inmediatamente
- **HIGH (naranja):** Validación fallida, diferencias > 5% en totales → Escalar a Jefe de Análisis, pausar cierre
- **MEDIUM (amarillo):** Advertencias en logs, pequeñas discrepancias (< 5%) → Registrar en bitácora, continuar con supervisión
- **LOW (verde):** Información / ajustes menores → Registrar y resolver en siguiente iteración

---

## 8. Consideraciones de performance y parallelización

### 8.1 Tiempo de ejecución estimado por notebook

| Notebook | Nodos | Estrategia principal | Tiempo esperado | Notas |
|----------|-------|----------------------|-----------------|-------|
| NB-01 | 3 | pandas + SQL pushdown | 2–3 min | Lectura DCV.MONEDAS_MENSUAL ~50K rows |
| NB-02 | 31 | SQL pushdown (80% PROC_SQL) | 8–12 min | 45+ tablas WORK generadas |
| NB-03 | 10 | SQL pushdown | 4–6 min | Reutiliza salidas NB-02 |
| NB-04 | 14 | SQL pushdown + pandas | 6–10 min | Consolidaciones + imputaciones |
| **Total (4 notebooks)** | 58 | — | **20–31 min** | Ejecución secuencial |

### 8.2 ¿Paralelizar?

**Respuesta actual: NO**

Aunque lógicamente:
- NB-02 y NB-03 son "independientes" (ambos consumen GOBGENER, producen WORK),
- **No se recomienda paralelización** en este lote por:
  1. **Tablas #tmp compartidas:** Ambos notebooks crean `WORK.CRUCE_*`, `WORK.CHECK_*` con igual nombre → colisión de sesión SQL
  2. **Sobrecargar servidor SQL:** 31+10 = 41 nodos SQL ejecutados simultáneamente → timeout probable
  3. **Validación de orden:** Necesitamos garantizar que NB-02 produce salidas "limpias" antes que NB-03 las consuma

**Futuro (lote 2):** Refactorizar con prefijos únicos en #tmp y considerar multiprocessing con Pool.

### 8.3 Optimizaciones recomendadas

1. **Indexación en BD:** Solicitar al DBA crear índices en:
   - GOBGENER.EJECUCION (ENTIDAD, ACCOUNT, ITEM, YEAR, MES)
   - GOBGENER.EJEC_DIPRES (ENTIDAD, CUENTA, ITEM, YEAR, MES)
   - GOBGENER.ENTIDADES (C_ENTIDAD) — ya debería tenerlo

2. **Caché de tablas maestras:** En NB-02, materializar GOBGENER.COFOG, CR18_APERTURA en WORK (read-once):
   ```python
   # Celda de NB-02, tras conectar
   COFOG = pd.read_sql("SELECT * FROM GOBGENER.COFOG", conn)
   CR18_APERTURA = pd.read_sql("SELECT * FROM GOBGENER.CR18_APERTURA", conn)
   # Reutilizar en celdas posteriores sin re-query
   ```

3. **Logging selectivo:** Reducir verbosity en production (solo WARN/ERROR en logs, INFO en console)

---

## 9. Alcance de este lote vs. diferimientos

### 9.1 Incluido en este lote (Entrega 1)

**Notebooks completamente migrados y operacionales:**
1. NB-01_autoexec.ipynb ✓
2. NB-02_proceso_ejecucion_gc_cgr.ipynb ✓
3. NB-03_proceso_ejec_gc_dipres.ipynb ✓
4. NB-04_salida_cg_coy.ipynb ✓

**Flujos SAS migrables (18 de 19 total) cubiertos:**
- ✓ AUTOEXEC (3 nodos)
- ✓ Proceso Ejecución GC CGR (31 nodos)
- ✓ Proceso Ejec GC DIPRES (10 nodos)
- ✓ Salida CG coy (14 nodos)

**Total:** 58 nodos traducidos, ~20–31 min de ejecución completa.

### 9.2 Diferidos para próximos lotes (no incluido)

**Notebooks EN DESARROLLO (Lote 2+):**
1. NB-05_salida_cg_anual.ipynb (12 nodos) — Flujo "Salida CG anual"
2. NB-06_salida_cnf_coy.ipynb (11 nodos) — Flujo "Salida CNF coy"
3. NB-07_salida_cnf_trim_cgr.ipynb (9 nodos) — Flujo "Salida CNF trim"
4. NB-08_salida_cnf_trim_dip.ipynb (11 nodos) — Flujo "Salida CNF trim DIP"

**Flujos SAS no migrados en este lote:**
- Salida CG Imputa (7 nodos)
- Salidas CNF anual y COFOG (8 nodos)
- Salida_anual para componente especif_no (5 nodos)
- Proceso Sit_Patri_MUN_no (9 nodos)
- Proceso Ejecución Municipal CGR_no (12 nodos)
- Traspasos_info (6 nodos)
- Salida_CF_GC (9 nodos)
- Salida_DCNA (8 nodos)
- Salidas_Cuenta_Produc_AAPP_no (10 nodos)
- Salidas_Cuenta_Produc_AAPP_2_no (7 nodos)
- Indicadores municipales (8 nodos)

**Total diferido:** 130 nodos en 11 flujos (próximos lotes).

**Nota:** No incluir NB-05 a NB-08 en `run_all.py` de este lote ni intentar ejecutarlos — generarán fallos de tabla no encontrada.

---

## 10. Checklist pre-operación

Completar ANTES de ejecutar en producción:

- [ ] **Entorno Python:** `python --version` ≥ 3.9, `pip list | grep pandas` ✓
- [ ] **Dependencias:** `pip install -r requirements.txt` sin errores
- [ ] **BD accesible:** `python -c "import pyodbc; pyodbc.connect(...)"` ✓ conexión exitosa
- [ ] **Config:** `project_config.yaml` existe, contiene Year, Mes, macro_params, credenciales en env vars (NO hardcode)
- [ ] **Estructura directorios:** `output/` existe con 8 notebooks + `run_all.py`
- [ ] **Logs:** `output/logs/` directorio creado (o permitir auto-create en `run_all.py`)
- [ ] **Contactos:** Archivo de contactos (sección 7) completado con números/correos reales
- [ ] **Validaciones:** Script de checks post-ejecución preparado (sección 5.2)
- [ ] **Backup:** Copias de seguridad de tablas GOBGENER críticas disponibles (pre-ejecución)
- [ ] **Ventana de cambio:** Aprobada por Jefe de Área + IT (especialmente si es first-run en producción)
- [ ] **Rollback plan:** Procedimiento para restaurar tablas GOBGENER de backup documented

---

## Apéndice A: Comandos de diagnóstico rápido

```bash
# Verificar Python y paquetes
python --version
pip list | grep -E "pandas|sqlalchemy|pyodbc|jupyter"

# Validar BD
python -c "
import pyodbc
conn = pyodbc.connect('Driver=ODBC Driver 17 for SQL Server;Server=YOUR_SERVER;Database=GOBGENER;Trusted_Connection=yes')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES')
print(f'Tablas en GOBGENER: {cursor.fetchone()[0]}')
"

# Ejecutar notebook individual con papermill (si disponible)
papermill output/NB-01_autoexec.ipynb output/NB-01_autoexec_20240601.ipynb \
  -p Year 2024 -p Mes 6

# Monitorear ejecución de run_all.py
tail -f output/logs/execution.log

# Limpieza de tablas WORK (post-dev, pre-prod)
sqlcmd -S YOUR_SERVER -d GOBGENER -Q "
DROP TABLE IF EXISTS WORK.CIERRE_MES;
DROP TABLE IF EXISTS WORK.COMPARA_PACAPR;
DROP TABLE IF EXISTS WORK.EJECUCION_CG_CGR;
"
```

---

**Versión:** 1.0  
**Fecha:** 2026-08-13  
**Responsable:** Equipo de Migración SAS → Python  
**Próxima revisión:** Post-ejecución Lote 2 (NB-05 a NB-08)
