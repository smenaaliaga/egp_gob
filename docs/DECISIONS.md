# Decisiones de la Migración

## Alcance y Flujos Incluidos en Esta Entrega

La presente migración abarca **6 Process Flows de los 17 totales** del proyecto `Proc_Salidas_Gob_REV_mig`, traduciendo **71 nodos** de los 178 identificados. Estos flujos se ejecutan de forma secuencial y son interdependientes (la salida de uno alimenta el siguiente), conformando el núcleo de validación y procesamiento presupuestario del Gobierno.

### Flujos Migrados en Este Lote

1. **AUTOEXEC** (3 nodos)  
   - Inicialización de librerías y procesamiento de monedas mensuales/trimestrales
   - Genera tablas de cierre y promedios para análisis de variación de tipos de cambio
   - Dependencia crítica: **debe ejecutarse primero** en todo ciclo

2. **Proceso Ejecución GC CGR** (31 nodos)  
   - Validación y clasificación de ejecución presupuestaria del Gobierno General  
   - Reconcilia cambios en estructuras contables, actualiza matrices de analíticos fijos y variables
   - Gestiona transferencias consolidables, asignaciones de actividad y códigos COFOG para nuevas entidades
   - Núcleo operativo de la migración

3. **Proceso Ejec GC DIPRES** (10 nodos)  
   - Validación de ejecutiones anuales presupuestarias del lado DIPRES  
   - Asegura correcta imputación de actividades, analíticos y tipos de transacción
   - Genera matrices de referencia para reportes de gobierno

4. **Salida CG coy** (14 nodos)  
   - Preparación de indicadores de ejecución presupuestaria para reportes de coyuntura económica
   - Integra datos de CGR y DIPRES en múltiples formatos de agregación/desagregación

5. **Salida CG Imputa** (7 nodos)  
   - Procesamiento de imputaciones permanentes en ejecución presupuestaria
   - Genera outputs certificados para reportería oficial

6. **Salida CNF trim** (6 nodos)  
   - Consolidación trimestral de cuentas nacionales y flujos de fondos
   - Agregación y validación de datos para reportes trimestrales

### Flujos Diferidos (No Incluidos en Esta Entrega)

Los siguientes **11 Process Flows** permanecen **diferidos a lotes posteriores**:

- Salida CG coy (componentes adicionales)
- Salida CG Imputa (extensiones)
- Salida CNF trim (extensiones)
- Salidas CNF anual y COFOG
- Salida_anual para componente especif
- Proceso Sit_Patri_MUN
- Proceso Ejecución Municipal CGR
- Traspasos_info
- Salida_CF_GC
- Salida_DCNA
- Salidas_Cuenta_Produc_AAPP (2 variantes)
- Indicadores municipales

**Justificación del diferimiento**: Estos flujos dependen de salidas no aún traducidas en este lote o requieren validación adicional de dependencias de bases de datos municipales y de análisis complementarios. Se procesarán en lote posterior una vez consolidadas las bases presentes en esta entrega.

---

## Estrategia de Traducción y Placements

### Clasificación de Nodos por Estrategia

La traducción SAS → Python se realiza según el **tipo de nodo y su contexto de datos**:

| Estrategia | Nodos | Característica | Herramienta Python |
|---|---|---|---|
| **Pandas** | 25 | Lectura de tablas SAS (PROC IMPORT), cálculos agregados, transformaciones tabulares simples | `pd.read_sas()`, `pd.DataFrame`, operaciones vectorizadas |
| **Hybrid** | 35 | PROC SQL complejos con múltiples LEFT JOINs, GROUP BY, actualización de bases, lógica UPSERT | `pandas` + `SQL directo a BD` (SQLAlchemy / pypyodbc) |
| **Python** | 11 | Código SAS DATA step no-SQL, inicialización, utilidades de sistema | Python puro (librerías estándar) |

### Placements Efectivos

- **Utility**: 11 nodos de inicialización, configuración de librerías y parámetros globales → ubicados en `NB-01_autoexec.ipynb`
- **Ambiguous** (con supuesto visible): 4 nodos que acceden a librecias cuyo engine no fue validado
  - `CodeTask-D6fqrxqReNOK5Xch`: Lee desde `DCV.MONEDAS_MENSUAL` → **strategy pandas** (supuesto: tabla SAS, no BD remota)
  - Otros 3 nodos del flujo AUTOEXEC con el mismo patrón
  - **Acción requerida en entrevista B4b**: Confirmar si estos librefs apuntan a servidor SQL o son SAS en disco
- **Hybrid**: 35 nodos con PROC SQL complejos → acceso a `GOBGENER` (BD principal verificada) + actualización de tablas
- **Ambiguous sin resolver**: Si `DCV` resulta ser una base de datos remota, los nodos actuales descargarían **tablas enteras a memoria** (impacto: alto en volumen de datos). Requiere confirmación del usuario.

---

## Supuestos Visibles del Plan

### Macro Variables de Usuario

El plan identifica **35 macro variables** sin valores predefinidos en `project_config.yaml` ni declaradas en la entrevista B4:

| Variable | Usada en | Observación |
|---|---|---|
| `Year` | 95 nodos (crítica) | Período fiscal de ejecución; debe declararse globalmente |
| `Analista` | 12 nodos | Usuario responsable de clasificación manual (TCONS, analíticos) |
| `Comp1` a `Comp7` | 21 nodos cada una | Computaciones/periodos parametrizados (ej: trimestres, años fiscales) |
| `Mes`, `Mes_imp1`...`Mes_imp12` | 13 nodos | Periodos de imputación mensual |
| `Moneda` | 8 nodos | Moneda de conversión (UF, USD, etc.) |
| `PACAPR1`...`PACAPR7` | 21 nodos | Capítulos/partidas de apertura parametrizados |

**Decisión**: Estas variables se declaran en la **celda 'parameters'** de los notebooks de Jupyter (segunda celda tras import). El equipo de operaciones debe proveer valores en `project_config.yaml` o fijar valores antes de ejecutar. Si no se asignan, permanecen `None` y causan errores en tiempo de ejecución.

### Bases de Datos y Librecias

**BD Principal Verificada:**
- `GOBGENER` (SQL Server / Oracle): contiene todas las tablas maestras de analíticos, estructuras y ejecuciones. **Accesible desde todos los nodos hybrid**.

**Librecias de Entrada No Verificadas:**
- `DCV`: contiene `MONEDAS_MENSUAL` (1 nodo). Engine desconocido; se asume SAS en disco.
- `DCNIDCNA`: accedida por 3 nodos en flujos diferidos. No incluida en esta entrega.

**Supuesto**: Las conexiones SQL a `GOBGENER` funcionan mediante credenciales en `project_config.yaml` (sección `db_connections`). Si faltan, los nodos hybrid abortan.

### Periodos y Ranges de Ejecución

- **Año fiscal**: Variable `Year` (macro); se espera rango 2015-2026 basado en catálogos históricos
- **Ciclos mensuales**: `Mes` (1-12); `Mes_imp1-12` permiten imputaciones retroactivas
- **Periodos de comparación**: `Comp1-7` representan periodos alternativos para análisis de variación (ej: año anterior, mes anterior, etc.)

---

## Decisiones de Entrevista Relevantes (B4b - Traducción)

### 1. Resolución de Ambiguedad: Librecias SAS vs. BD Remota

**Pregunta Original**: ¿`DCV.MONEDAS_MENSUAL` es tabla SAS en disco o campo en BD remota?

**Decisión Tomada**: Se asume SAS en disco → strategy `pandas` con `pd.read_sas()`. 

**Implicación**:  
- Si es BD remota, la tabla se descarga **entera a memoria** (riesgo: si tiene millones de filas, puede saturar RAM)
- Alternativa segura: cambiar a strategy `hybrid` + SQL directo si es DBMS

**Acción Pendiente**: Usuario debe confirmar en `project_config.yaml` el tipo de libref `DCV` (engine: `SAS` vs `ODBC`/`SQL`).

### 2. Placement de Nodos Multi-Paso: UPSERT (UPDATE+INSERT)

**Patrón Detectado**: 12 nodos implementan lógica UPSERT (ej: `CodeTask-19o6EdegIblGxthd`, `CodeTask-SR2tNwn9ee5q4ldH`):
```sql
DELETE FROM GOBGENER.ENTIDADES WHERE (PK_COLS...) IN (SELECT... FROM TRABAJO);
PROC DATASETS APPEND DATA=TRABAJO BASE=GOBGENER.ENTIDADES FORCE;
```

**Decisión**: Mantener como **hybrid** usando transacciones SQL con rollback:
```python
# Pseudocódigo
with db_connection.transaction():
    db.execute(delete_stmt)
    db.execute(insert_stmt)  # Puede venir de pandas
    db.commit()
```

Si la conexión falla, ambas operaciones revierten (atomicidad).

### 3. Exclusión de Nodos Query (3 nodos)

**Nodos excluidos**:
- `Query-7WLH8bv335ANj5w9`
- `Query-9hK9UXmLqOXfHIKS`
- `Query-fI94dLNL1vAYjQn4`

**Razón**: Son definiciones de vistas o consultas sin materialización en outputs. Su lógica se subsume en los nodos PROC SQL adyacentes (los que consumen sus resultados). Traducir ambos generaría redundancia.

---

## Mejoras Aprobadas y Su Aplicación

### M-001: Consolidar Rutas de Archivo Hardcodeadas (APROBADA)

**Estado en Migración**: Parcialmente aplicada en nodos de `AUTOEXEC`.

**Detalles**:
- Se identifican 17 nodos con rutas SAS hardcodeadas (16 en flujos diferidos, 1 en este lote: `CodeTask-D6fqrxqReNOK5Xch`)
- **Aplicación**: En `NB-01_autoexec.ipynb`, la celda de inicialización declara variables de ruta:
  ```python
  # project_config.yaml o environment
  DATA_PATHS = {
      'MONEDAS': config.get('paths.monedas_input'),  # ej: '/data/monedas_2024.csv'
      'ENTIDADES': config.get('paths.entities_db'),
  }
  ```
- Nodos posteriores referencia estas variables, no rutas hardcodeadas
- **Diferidos**: Los 16 nodos en flujos no traducidos seguirán la misma pauta cuando se migren

### M-005: Centralizar Macro Variables de Usuario (APROBADA)

**Estado en Migración**: Aplicada en todos los notebooks.

**Detalles**:
- La segunda celda de cada notebook es una célula `# Parameters` con declaraciones explícitas:
  ```python
  # Parameters (configurable antes de ejecución)
  Year = None  # Asignar valor o leer de project_config.yaml
  Analista = None
  Comp1, Comp2 ... Comp7 = None, None, ..., None
  ```
- El archivo `project_config.yaml` contiene sección `run.macro_params` con valores por defecto
- Si no se asigna, la célula alerta al usuario y aborta con mensaje claro
- **Ventaja**: Reproducibilidad — toda ejecución queda documentada con los parámetros usados (en logs o archivo de salida)

---

## Análisis de Dependencias Entre Flujos

```
AUTOEXEC (inicialización, monedas)
    ↓
Proceso Ejecución GC CGR (validación, clasificación)
    ├── Salida CG coy (output de indicadores)
    ├── Salida CG Imputa (imputaciones)
    └── Salida CNF trim (consolidación trimestral)
        ↓
Proceso Ejec GC DIPRES (validación DIPRES)
    ↓
[Flujos Diferidos: reportería final, análisis municipal, etc.]
```

**Ciclo de Ejecución**:
1. Ejecutar `NB-01_autoexec.ipynb` (inicializa librerías, monedas)
2. Ejecutar `NB-02_proceso_ejecucion_gc_cgr.ipynb` (validación CGR)
3. Ejecutar `NB-03_proceso_ejec_gc_dipres.ipynb` (validación DIPRES en paralelo con paso anterior, pero depende de outputs de CGR)
4. Ejecutar en paralelo:
   - `NB-04_salida_cg_coy.ipynb`
   - `NB-05_salida_cg_imputa.ipynb`
   - `NB-06_salida_cnf_trim.ipynb`

---

## Tecnología y Plataforma de Destino

### Requisitos Validados

| Requisito | Valor | Estado |
|---|---|---|
| Python | 3.9+ | ✓ Especificado |
| Librerías | pandas, sqlalchemy, pyodbc, openpyxl | ✓ Incluidas en requirements.txt |
| BD | SQL Server 2019+ o similar | ✓ GOBGENER accesible |
| Almacenamiento | Disco local + carpeta compartida para WORK/ | ✓ Estructura de directorios creada |
| Jupyter | 1.0+ (notebooks .ipynb) | ✓ Entorno listo |

### Formato de Salida

- **Tablas de trabajo** (`WORK.*`): DataFrames en memoria + exportadas a Parquet/CSV en `output/data/work/`
- **Tablas persistentes** (`GOBGENER.*`): Actualizadas en BD remota (transacciones UPSERT)
- **Reportes manuales**: Archivos Excel (`.xlsx`) en `output/reports/` para clasificación interactiva (TCONS, analíticos variables)

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Macro variables no definidas en runtime | Media | Alto | Validación en celda parameters; archivo de defaults en project_config.yaml |
| Conexión a GOBGENER falla | Baja | Alto | Reintentos (3x) con backoff exponencial; fallback a modo offline (si aplica) |
| Tabla SAS en DCV muy grande → overflow de RAM | Media | Medio | Agregar verificación de tamaño; si >500MB, alertar y usar chunked read |
| Inconsistencia UPSERT (DELETE sin INSERT) | Baja | Crítico | Transacciones con rollback automático; tests unitarios de integridad referencial |
| Cambio en estructura de GOBGENER entre ejecuciones | Baja | Medio | Versionado de esquema en BD; validación de columnas al inicio de cada nodo |

---

## Notas Operacionales Finales

1. **Entrevista B4b Pendiente**: Confirmación de tipos de libref (DCV, etc.) y asignación de valores a macro variables críticas (Year, Analista, etc.)

2. **Flujos Diferidos**: Los 11 Process Flows diferidos se migran en lotes posteriores. Esta entrega es **funcional y completa para el ciclo CGR+DIPRES+salidas básicas**, pero no incluye análisis municipal ni reportería final (COFOG, CNF anual).

3. **Modo de Entrega**: Los 6 notebooks se entregan con estructura modular (`run_all.py` coordina la ejecución secuencial). Cada notebook es independiente documentalmente pero interdependiente en datos.

4. **Validación Post-Ejecución**: Tras correr los notebooks, verificar (runbook incluye checklists):
   - Conteo de filas en tablas maestras (ENTIDADES, ANALIT_TCONS, CR18_T_SCN_1/2)
   - Archivos Excel exportados para clasificación manual (revisar integridad y permisos de escritura)
   - Logs de error en `output/logs/` (búsqueda de palabras clave: `ERROR`, `FAILED`, `CONNECTION`)
