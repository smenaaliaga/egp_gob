# Mejoras y Decisiones de Migración — Proc_Salidas_Gob_REV_mig

## Resumen Ejecutivo

En esta migración se evalúan **7 mejoras** identificadas en el análisis de calidad del código SAS original. De ellas, **1 fue aprobada** para aplicar en este lote (M-006: parametrización de macros Year y Comp1-7), **1 fue rechazada** (M-003: refactorización de rutas a variables de configuración), y **5 fueron postergadas** (M-001, M-002, M-004, M-005, M-007) porque sus nodos afectados pertenecen a flujos diferidos que no forman parte de esta entrega.

La estrategia de mejoras sigue el criterio de **diferimiento selectivo**: solo se aplican cambios a los 4 flujos traducidos en este lote (AUTOEXEC, Proceso Ejecución GC CGR, Proceso Ejec GC DIPRES, Salida CG coy). Las demás se re-evalúan cuando entren los flujos pendientes en lotes posteriores.

---

## M-001: Extraer fragmentos SQL duplicados a macros reutilizables

**Categoría:** Mantenibilidad  
**Impacto:** Alto  
**Esfuerzo:** Alto  
**Riesgo:** Medio

### Descripción del problema

Se detectan **19 bloques SQL duplicados** afectando **110+ nodos**. El fragmento más crítico es el cálculo de trimestre:

```sas
CASE WHEN MES IN(1,2,3) THEN 1 
      WHEN MES IN(4,5,6) THEN 2 
      WHEN MES IN(7,8,9) THEN 3 
      ELSE 4 END
```

Este patrón aparece **65 veces** en nodos como `CodeTask-2u1eOTvq3sZo1V34`, `CodeTask-4wxss6QulJ8PK7Pu`, `CodeTask-94I9bgH6Q4ktjiWH`, y otros. Adicionalmente se replican:

- `CREATE TABLE CR18_APERTURA` (19 nodos)
- `DELETE FROM EJECUCION_A_PRELIM` con variantes (16 nodos)
- `UPDATE` con WHERE complejos (4 nodos)

### Justificación

La duplicación introduce riesgo crítico de **inconsistencia**: si la lógica de trimestre cambia o se corrige un bug, requiere actualizar manualmente **65 ubicaciones**, exponiendo el código a:
- Errores por olvido de sitios
- Desincronización entre versiones
- Mayor tiempo de testing y validación

**Beneficios de centralizar:**
- Reducción ~40% de líneas de código duplicado
- Centralización de lógica de negocio
- Facilita auditoría y testing unitario
- Propaga automáticamente correcciones a todos los nodos

### Nodos afectados

19 nodos identificados en flujos diferidos: `CodeTask-2u1eOTvq3sZo1V34`, `CodeTask-4wxss6QulJ8PK7Pu`, `CodeTask-94I9bgH6Q4ktjiWH`, `CodeTask-A3JEhgKfE5syST7K`, `CodeTask-AD4kzP4luBEsTydA`, `CodeTask-KgBtsabMAJrXUjkl`, `CodeTask-PRH1lTSmY7JzJpmI`, `CodeTask-Vob3Cr2FL8rjXBlH`, `CodeTask-W5QOX3IfZ4AXUmE2`, `CodeTask-cjFzgfiIc4f1oaij`, `CodeTask-cpVfXtbY1fhHpykA`, `CodeTask-jd7KWCF4lrlo7kqk`, `CodeTask-kEwO1qvT28cYoAgT`, `CodeTask-r6G37H7LHWkbbRzg`, `CodeTask-rmzRDvtUeZ2SkGKc`, `CodeTask-tPkkXrMn7HpatBGU`, `CodeTask-tli9YgMo32jhmrKW`, `CodeTask-v2XeXrcszN91UcUK`, `CodeTask-wpalwVYAWfwAKJxy`.

### Decisión

**POSTERGADA** — Los nodos afectados residen en flujos que no están incluidos en este lote (están marcados como `flujos_diferidos`). La mejora se re-evalúa y aplica cuando esos flujos entren en traducción en un lote posterior.

---

## M-002: Centralizar constantes de negocio y números mágicos en tabla de parámetros

**Categoría:** Mantenibilidad  
**Impacto:** Alto  
**Esfuerzo:** Medio  
**Riesgo:** Bajo

### Descripción del problema

Números mágicos críticos hardcodeados en **85+ nodos** sin documentación:

| Valor | Frecuencia | Ejemplo de nodos | Significado probable |
|-------|-----------|------------------|----------------------|
| `1000000` | 85 nodos | `CodeTask-3GhPnDCy9p2wBP7i`, `CodeTask-4Vv4xGyymdoAYMNg` | Divisor para conversión de unidades (escala) |
| `10201`, `5601` | 45 nodos c/u | Múltiples | IDs de entidades o códigos de negocio |
| `'04001000'`, `'04002000'` | 34 nodos | `CodeTask-IBn1x34Qkxekgyzd` | Códigos de analíticos predefinidos |
| Códigos de entidad (`3801`, `6403`, `19703`, `19701`) | 22, 4, 4, 4 nodos | `CodeTask-A3JEhgKfE5syST7K` | Identificadores de entidades gubernamentales |
| `'000'`, `'03000000'` | 34, 19 nodos | Múltiples | Valores de clasificación o "sin asignar" |

Sin documentación, cada cambio de formato o escala implica búsqueda manual en todo el código.

### Justificación

Números mágicos dificultan:
- **Mantenimiento:** Cambios de escala o clasificaciones requieren búsqueda y reemplazo manual
- **Auditoría:** No es claro por qué se divide entre 1000000 o qué representa '04001000'
- **Testing:** Casos de prueba no documentados; es difícil diseñar validaciones

**Solución propuesta:** Crear tabla `GOBGENER.PARAMETROS_NEGOCIO` con estructura:

```sql
CREATE TABLE GOBGENER.PARAMETROS_NEGOCIO (
  CODIGO           VARCHAR(50),
  DESCRIPCION      VARCHAR(500),
  VALOR_NUMERICO   NUMERIC(18,2),
  VALOR_TEXTO      VARCHAR(100),
  VIGENCIA_DESDE   DATE,
  VIGENCIA_HASTA   DATE,
  RESPONSABLE      VARCHAR(100)
);
```

Ejemplos de registros:
- `(ESCALA_VALORES, Divisor para conversión a millones, 1000000, NULL, 2024-01-01, NULL, Contabilidad)`
- `(ANALITICO_FIJO_MIN, Analítico mínimo fijo clasificado, NULL, '04001000', 2024-01-01, NULL, Validación)`
- `(ENTIDAD_ESPECIAL_GORE, Código de entidad GORE, 3801, NULL, 2024-01-01, NULL, Estructura)`

**Beneficios:**
- Trazabilidad de cambios (auditoría de vigencia)
- Cambios sin modificar SQL
- Reutilización en múltiples nodos
- Diccionario de datos centralizado

### Nodos afectados

14 nodos identificados en flujos diferidos: `CodeTask-3GhPnDCy9p2wBP7i`, `CodeTask-4Vv4xGyymdoAYMNg`, `CodeTask-4aWGaC1VmZySxlzM`, `CodeTask-4g838w5UgiWqIbGy`, `CodeTask-4wxss6QulJ8PK7Pu`, `CodeTask-86VdtiWQrF36JEkb`, `CodeTask-8b6bsW9BKVc7jJXj`, `CodeTask-94I9bgH6Q4ktjiWH`, `CodeTask-99VPAhpFklGwBLLO`, `CodeTask-9HjwuVPWzkAGk1TK`, `CodeTask-A3JEhgKfE5syST7K`, `CodeTask-AD4kzP4luBEsTydA`, `CodeTask-IBn1x34Qkxekgyzd`, `CodeTask-Iyf7PQ2PcCPtQjBv`.

### Decisión

**POSTERGADA** — Los nodos afectados residen en flujos diferidos. Se re-evalúa cuando entren esos flujos.

---

## M-003: Refactorizar rutas de archivo hardcodeadas a variables de configuración

**Categoría:** Mantenibilidad  
**Impacto:** Alto  
**Esfuerzo:** Medio  
**Riesgo:** Medio

### Descripción del problema

**17 nodos** contienen rutas absolutas hardcodeadas que imposibilitan migración entre entornos:

- **Rutas UNC (\\FILESERVER\...):**  
  `CodeTask-1UPaqG3cjfbxeW38`, `CodeTask-6FS3khd1yz37XIOH`, `CodeTask-dzljPfKJnYXDrIyx`, `CodeTask-ESKX4AdeM3cTnf1w`, `CodeTask-HBcKDsWhhhzfcrxa`: apuntan a `\\FILESERVER\VOLM\GEM\050_DCNI\...` con archivos Excel de clasificación manual

- **Rutas SAS locales (/sasdata/BCCH):**  
  `CodeTask-D6fqrxqReNOK5Xch`, `CodeTask-S9YMDIdQqTumexhp`, `CodeTask-XzOatjIuMbeLV29h`: apuntan a directorios SAS con datos de tipos de cambio

Ejemplos de nodos afectados en este lote: `CodeTask-D6fqrxqReNOK5Xch` (AUTOEXEC), `CodeTask-XzOatjIuMbeLV29h` (AUTOEXEC).

### Impacto en esta migración

Los notebooks Python/Jupyter resultantes heredarían estas rutas absolutas, impidiendo:
- Portabilidad entre DEV → TEST → PROD
- Deployment en contenedores Docker (rutas no existen en la imagen)
- Ejecución remota o en cloud
- Compatibilidad con diferentes sistemas operativos

### Justificación

Externalizar rutas a un archivo de configuración centralizado (p.ej., `config.ini` o `config.yaml`) con variables como:

```ini
[paths]
PATH_DATA_IN = /sasdata/BCCHI
PATH_FILESERVER = \\FILESERVER\VOLM\GEM\050_DCNI
SASDATA_ROOT = /sasdata/BCCH
PATH_EXCEL_CLASIFICACIONES = ${PATH_FILESERVER}/CLASIFICACIONES
```

Beneficios:
- Facilita cambios de infraestructura sin tocar el código
- Auditoría de migraciones entre entornos
- CI/CD pipeline simplificado
- Portabilidad a cloud/contenedores

### Nodos afectados en este lote

- `CodeTask-D6fqrxqReNOK5Xch` (AUTOEXEC — Monedas_Mensual)
- `CodeTask-XzOatjIuMbeLV29h` (AUTOEXEC — Set Libreria)

Y 15 nodos adicionales en flujos diferidos.

### Decisión

**RECHAZADA con cambio de alcance** — El usuario decidió dejar las rutas explícitas en los notebooks, sin refactorizar a variables externas de configuración. Las rutas se documentarán en comentarios del notebook indicando cómo adaptarlas al entorno local. Razón: simplificar la migración en esta fase y mantener la portabilidad del notebook como artefacto único sin dependencias externas.

**Acción aplicada:** En los notebooks generados (`NB-01_autoexec.ipynb`, `NB-02_proceso_ejecucion_gc_cgr.ipynb`, etc.), las rutas se dejan literales pero se añaden celdas de comentario/markdown indicando dónde cambiarlas.

---

## M-004: Simplificar lógica CASE WHEN replicada y documentar dominio de valores

**Categoría:** Calidad  
**Impacto:** Medio  
**Esfuerzo:** Medio  
**Riesgo:** Bajo

### Descripción del problema

Lógica condicional CASE WHEN duplicada en **71 nodos**:

1. **Cálculo de trimestre** (65 nodos):
   ```sql
   CASE WHEN T1.C_T_AREA='GM' THEN 'AAPP' 
        WHEN T1.C_T_AREA='ED' THEN 'EEPP' 
        WHEN T1.C_T_AREA='SL' THEN 'SSPP' 
        ELSE 'OTRO' END
   ```
   Aparece en: `CodeTask-IpxSz3SSWndt6gw1`, `CodeTask-cjFzgfiIc4f1oaij`, `CodeTask-K6rsz3Du6zil4T7O`, y otros.

2. **Clasificación de área** (6 nodos):
   Variantes del mismo patrón en `CodeTask-ekal3Xobqf5pRWnO`, `CodeTask-oLKJ5g7DvhYHuBME`, `CodeTask-vImIvOrRUwWN5wSg`.

Falta tabla de lookup centralizada y documentación del dominio (GM→AAPP: ¿qué significa?).

### Justificación

La replicación introduce riesgo de inconsistencia y dificulta:
- **Testing:** No hay especificación única de qué representa cada código
- **Mantenimiento:** Agregar una nueva área requiere actualizar 65 ubicaciones
- **Auditoría:** No se documenta cuándo cambió el mapeo GM→AAPP

**Solución:** Crear tabla `GOBGENER.LOOKUP_T_AREA`:

```sql
CREATE TABLE GOBGENER.LOOKUP_T_AREA (
  C_T_AREA_CODE VARCHAR(10),
  T_AREA_DESC   VARCHAR(100),
  SIGNIFICADO   VARCHAR(500),
  VIGENCIA_DESDE DATE
);
-- Registros:
-- ('GM', 'AAPP', 'Administración Pública', 2024-01-01)
-- ('ED', 'EEPP', 'Empresa Estatal', 2024-01-01)
-- ('SL', 'SSPP', 'Sector Laboral', 2024-01-01)
```

Luego usar LEFT JOIN en lugar de CASE:
```sql
LEFT JOIN GOBGENER.LOOKUP_T_AREA L ON T1.C_T_AREA = L.C_T_AREA_CODE
SELECT ... L.T_AREA_DESC ...
```

**Beneficios:**
- Centralización de mappings
- Fácil agregar nuevas áreas
- Auditoría de cambios
- Testing parametrizado

### Nodos afectados

6 nodos en flujos diferidos: `CodeTask-IpxSz3SSWndt6gw1`, `CodeTask-K6rsz3Du6zil4T7O`, `CodeTask-cjFzgfiIc4f1oaij`, `CodeTask-ekal3Xobqf5pRWnO`, `CodeTask-oLKJ5g7DvhYHuBME`, `CodeTask-vImIvOrRUwWN5wSg`.

### Decisión

**POSTERGADA** — Los nodos afectados residen en flujos diferidos. Se re-evalúa cuando entren esos flujos.

---

## M-005: Crear diccionario de datos y validar filtros hardcodeados en WHERE clauses

**Categoría:** Calidad  
**Impacto:** Alto  
**Esfuerzo:** Medio  
**Riesgo:** Medio

### Descripción del problema

Filtros hardcodeados críticos en DELETE/UPDATE sin documentación ni validación:

| Filtro | Frecuencia | Ejemplo | Justificación (faltante) |
|--------|-----------|---------|--------------------------|
| `C_ENTIDAD=3801, 6403, 19703, 19701` | 22, 4, 4, 4 nodos | `CodeTask-A3JEhgKfE5syST7K` | ¿Por qué se eliminan solo estas entidades? |
| `C_CUENTA='32', '06', '24'` | 7, 10, 10 nodos | `CodeTask-IBn1x34Qkxekgyzd` | ¿Qué cuentas son transacciones consolidables? |
| `C_ITEM='01', '99', '03'` | 3, 7, 7 nodos | `CodeTask-IpxSz3SSWndt6gw1` | ¿Qué ítems NO se consolidan? |
| `C_ASIGNACION='000', '270', '999'` | 3, 7, 7 nodos | `CodeTask-Iyf7PQ2PcCPtQjBv` | ¿Qué significan asignación 000, 999? |
| `C_ANALITICO IN ('04001000','04002000','01000000','03000000')` | 19, 34 nodos | Múltiples | ¿Cuál es el dominio completo de analíticos? |

**Riesgo:** Ausencia de:
- Tabla de control de cambios
- Auditoría de cuándo se aplicó cada filtro
- Justificación del negocio

Ejemplo de error potencial: eliminar accidentalmente la fila con `C_ENTIDAD=3801` sin saber que es GORE (necesario para consolidación).

### Justificación

Crear tabla de auditoría `GOBGENER.AUDITORIA_FILTROS_NEGOCIO`:

```sql
CREATE TABLE GOBGENER.AUDITORIA_FILTROS_NEGOCIO (
  NODE_ID              VARCHAR(100),
  FILTRO_CRITERIO      VARCHAR(500),
  JUSTIFICACION        VARCHAR(2000),
  RESPONSABLE          VARCHAR(100),
  FECHA_VIGENCIA       DATE,
  FECHA_ULTIMA_MOD     DATETIME,
  ESTADO               VARCHAR(20),  -- ACTIVO, SUPRIMIDO, PENDIENTE_REVISION
  CAMBIO_JUSTIFICACION VARCHAR(2000)
);
```

Beneficios:
- **Gobernanza:** Todas las reglas de filtrado deben estar justificadas
- **Auditoría regulatoria:** Crítico en sector financiero/público
- **Trazabilidad:** Quién cambió qué filtro y cuándo
- **Prevención:** Evita corrupción de datos accidental

### Nodos afectados

15 nodos en flujos diferidos: `CodeTask-3GhPnDCy9p2wBP7i`, `CodeTask-4Vv4xGyymdoAYMNg`, `CodeTask-4aWGaC1VmZySxlzM`, `CodeTask-86VdtiWQrF36JEkb`, `CodeTask-8b6bsW9BKVc7jJXj`, `CodeTask-9HjwuVPWzkAGk1TK`, `CodeTask-A3JEhgKfE5syST7K`, `CodeTask-IBn1x34Qkxekgyzd`, `CodeTask-IpxSz3SSWndt6gw1`, `CodeTask-Iyf7PQ2PcCPtQjBv`, `CodeTask-KgBtsabMAJrXUjkl`, `CodeTask-PRH1lTSmY7JzJpmI`, `CodeTask-QazYc6dHjnESiTAF`, `CodeTask-Vob3Cr2FL8rjXBlH`, `CodeTask-ZFWBSNwbyPPJmZW3`.

### Decisión

**POSTERGADA** — Los nodos afectados residen en flujos diferidos. Se re-evalúa cuando entren esos flujos.

---

## M-006: Parametrizar variable macro Year y macro variables Comp1-7, Mes_imp5/12 con versionado

**Categoría:** Reproducibilidad  
**Impacto:** Alto  
**Esfuerzo:** Medio  
**Riesgo:** Bajo

### Descripción del problema

**95+ nodos** utilizan macro variables sin parámetro externo ni versionado:

- **Year:** utilizado en 95+ nodos sin definición centralizada. ¿Dónde se asigna `&YEAR=2024`? ¿Se puede ejecutar el código para 2023, 2022?
- **Comp1–Comp7:** 21 nodos usan componentes de agregación presupuestaria (`&COMP1`, `&COMP2`, etc.). Sin definición visible, es imposible saber qué representan.
- **Mes_imp5 a Mes_imp12:** 16 nodos usan impactos mensuales. ¿Son montos? ¿Porcentajes?
- **Analista, Moneda, PACAPR1–PACAPR7:** Otros 11+ macro variables sin documentación.

**Impacto en reproducibilidad:**
- No es posible regenerar reportes de años anteriores (auditoría fallida)
- Ejecutar el código requiere conocimiento tácito ("necesitas saber que &Year debe ser 2024")
- Imposibilidad de testing parametrizado
- Imposibilidad de versionar "qué parámetros se usaron para el informe de agosto 2024"

### Justificación

Crear archivo centralizado `MACROS_CONFIG.sas` o tabla `GOBGENER.PARAMETROS_EJECUCION`:

**Opción 1: Archivo SAS (mejor para SAS):**
```sas
%LET YEAR_ANALYSIS=2024;
%LET COMP1=COMP_PRESUPUESTAL_1;
%LET COMP2=COMP_PRESUPUESTAL_2;
... etc
```

**Opción 2: Tabla SQL (mejor para Python, auditoría):**
```sql
CREATE TABLE GOBGENER.PARAMETROS_EJECUCION (
  PARAMETRO_ID VARCHAR(50),
  VALOR_TEXTO  VARCHAR(500),
  VALOR_FECHA  DATE,
  PERIODO      VARCHAR(10),  -- AAAA-MM
  RESPONSABLE  VARCHAR(100),
  FECHA_VIGENCIA DATE
);
-- Registros:
-- ('YEAR_ANALYSIS', '2024', NULL, '2024-01', 'Contabilidad', 2024-01-01)
-- ('COMP1', 'PRESUPUESTAL_1', NULL, '2024-01', 'Contabilidad', 2024-01-01)
-- ('MONEDA', 'CLP', NULL, '2024-01', 'Contabilidad', 2024-01-01)
```

**Beneficios:**
- Auditoría: "Qué parámetros se usaron para el informe X"
- Reproducibilidad: Ejecutar para 2023, 2022, 2024 sin cambiar código
- Testing parametrizado: Casos de prueba con diferentes valores
- Versionado en Git: Cambios de parámetros trackeables
- Cambios sin tocar el código: Deploy simple

### Nodos afectados en este lote

Todos los nodos de los 4 flujos traducidos dependen indirectamente de Year y otros parámetros:
- **AUTOEXEC:** `CodeTask-XzOatjIuMbeLV29h`, `CodeTask-D6fqrxqReNOK5Xch`, `CodeTask-q5ZEbAg5C43nmYfy`
- **Proceso Ejecución GC CGR:** Nodos que usan Year en filtros (ej. `CodeTask-vRkhqURhrfdncIIr`)
- **Proceso Ejec GC DIPRES:** Similar
- **Salida CG coy:** Similar

Adicionalmente, nodos en flujos diferidos: `CodeTask-19o6EdegIblGxthd`, `CodeTask-217TBwmLOKn9s1Im`, `CodeTask-2u1eOTvq3sZo1V34`, `CodeTask-3GhPnDCy9p2wBP7i`, `CodeTask-3TTpMTyo2diGXNgR`, `CodeTask-4Vv4xGyymdoAYMNg`, `CodeTask-4aWGaC1VmZySxlzM`, `CodeTask-4g838w5UgiWqIbGy`, `CodeTask-4wxss6QulJ8PK7Pu`, `CodeTask-5644937ey7NzmPak`, `CodeTask-6FS3khd1yz37XIOH`, etc.

### Decisión

**APROBADA Y APLICADA A ESTE LOTE**

Se implementa parametrización de Year y variables de componentes/impactos en los notebooks Python de esta entrega:

1. **En NB-01_autoexec.ipynb:**
   - Celda de parámetros Jupyter parametrizada con `Year=2024` (default)
   - Posibilidad de pasar `--Year 2023` al ejecutar con Papermill

2. **En todos los notebooks (NB-02, NB-03, NB-04):**
   - Celda `# Parameters` estándar de Jupyter que declara:
     ```python
     Year = 2024  # Parámetro: año de análisis
     Comp1 = None  # Parámetro: componente 1 (completar en config o al ejecutar)
     Comp2 = None
     ...
     ```
   - Comentarios explícitos indicando dónde completar los valores o cómo obtenerlos de tabla GOBGENER.PARAMETROS_EJECUCION

3. **En run_all.py:**
   - Script que lee `config.yaml` o tabla de BD y pasa parámetros a cada notebook vía Papermill

4. **Versionado:**
   - Archivo `PARAMETROS_EJECUCION_2024.yaml` con valores por período
   - Histórico en Git para auditoría

**Artefactos generados:**
- `notebooks/NB-01_autoexec.ipynb` con celda parameters
- `notebooks/NB-02_proceso_ejecucion_gc_cgr.ipynb` con celda parameters
- `notebooks/NB-03_proceso_ejec_gc_dipres.ipynb` con celda parameters
- `notebooks/NB-04_salida_cg_coy.ipynb` con celda parameters
- `run_all.py` con lógica de parametrización
- `config_sample.yaml` como plantilla

---

## M-007: Verificar y documentar dependencias de base de datos (librefs) sin verified_db

**Categoría:** Reproducibilidad  
**Impacto:** Alto  
**Esfuerzo:** Bajo  
**Riesgo:** Bajo

### Descripción del problema

**4 librefs** detectados sin verificación de esquema en nodos del análisis:

| Libref | Tablas | Nodos | Estado |
|--------|--------|-------|--------|
| DCNIDCNA | BDATOS_SP, CODIGO_ENTIDAD_SP, EJEC_MUN | 3 nodos en flujos diferidos | No verificado |
| DCV | MONEDAS_MENSUAL | `CodeTask-D6fqrxqReNOK5Xch` (AUTOEXEC, este lote) | No verificado |
| GOBGENER | Múltiples (99 tablas) | Todos los flujos | Verificado (asumido) |
| Otros 2 librefs omitidos en resumen | — | — | — |

**Riesgo:** Los nodos afectados producen datos críticos sin validar:
- Existencia de tablas
- Esquema (¿columnas?) 
- Permisos de acceso
- Disponibilidad en DEV/TEST/PROD

Ejemplo: Si `DCV.MONEDAS_MENSUAL` no existe en el ambiente de ejecución, el notebook `NB-01_autoexec` fallará silenciosamente o con error críptico.

### Justificación

Crear script de validación `validate_db_connections.py`:

```python
import pandas as pd
from sqlalchemy import inspect

# Verificar que libref DCV existe y contiene MONEDAS_MENSUAL
engine = get_connection('DCV')
inspector = inspect(engine)
tables = inspector.get_table_names()

assert 'MONEDAS_MENSUAL' in tables, \
    f"Tabla MONEDAS_MENSUAL no encontrada en DCV. Tablas disponibles: {tables}"

# Verificar esquema
columns = inspector.get_columns('MONEDAS_MENSUAL')
assert 'MES' in [c['name'] for c in columns], \
    "Columna MES no encontrada en MONEDAS_MENSUAL"
```

**Beneficios:**
- Fail-fast: Detecta problemas antes de ejecutar ETL
- Documentación: Esquema esperado explícito
- Portabilidad: Valida que el ambiente esté correctamente configurado
- CI/CD: Test automatizado en cada deployment

### Nodos afectados en este lote

- `CodeTask-D6fqrxqReNOK5Xch` (AUTOEXEC — utiliza DCV.MONEDAS_MENSUAL)

Nodos en flujos diferidos:
- `CodeTask-cbwaC9NShYE8mV6x`, `CodeTask-oLKJ5g7DvhYHuBME`, `Query-YHeDzXnzld6fOVfj`

### Decisión

**POSTERGADA** — Los nodos críticos afectados (DCNIDCNA) están en flujos diferidos. Sin embargo, para este lote:

**En NB-01_autoexec.ipynb (que usa DCV.MONEDAS_MENSUAL):**
- Se añade celda de validación inicial:
  ```python
  # Verificar conexión a DCV y existencia de MONEDAS_MENSUAL
  try:
      df_test = pd.read_sql("SELECT COUNT(*) FROM DCV.MONEDAS_MENSUAL", engine)
      print(f"✓ DCV.MONEDAS_MENSUAL accesible ({df_test.iloc[0,0]} registros)")
  except Exception as e:
      raise RuntimeError(f"✗ No se pudo acceder a DCV.MONEDAS_MENSUAL: {e}")
  ```

- Documentación en el README indicando las dependencias de BD requeridas

---

## Resumen de aplicaciones en esta entrega

| Mejora | Estado | Aplicación | Artefacto |
|--------|--------|-----------|-----------|
| M-001 | Postergada | — | — |
| M-002 | Postergada | — | — |
| M-003 | Rechazada | Rutas explícitas en notebooks con comentarios | NB-*.ipynb |
| M-004 | Postergada | — | — |
| M-005 | Postergada | — | — |
| M-006 | Aprobada | Parametrización con celdas Jupyter + run_all.py | run_all.py, config_sample.yaml, NB-*.ipynb |
| M-007 | Postergada (parcial) | Validación de DCV en NB-01 | NB-01_autoexec.ipynb |

---

## Plan de acción para lotes posteriores

Cuando entren los flujos diferidos, se re-evalúan M-001, M-002, M-004, M-005, M-007 y se aplican según aprobación del usuario. Se recomienda:

1. Prioridad alta: **M-005** (auditoría de filtros) — crítico para gobernanza
2. Prioridad alta: **M-002** (constantes de negocio) — facilita mantenimiento
3. Prioridad media: **M-001** (eliminar duplicación SQL) — mejora legibilidad
4. Prioridad media: **M-007** (validar librefs) — mejora reproducibilidad
5. Prioridad baja: **M-004** (lookups CASE WHEN) — cosmético
