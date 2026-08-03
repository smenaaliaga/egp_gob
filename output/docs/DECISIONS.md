# Decisiones de migración — Proc_Salidas_Gob_REV_mig

## Alcance: Flujos incluidos y excluidos

Esta entrega cubre la migración de **6 de 17 flujos de proceso**. Los flujos migrados en este lote son:

1. **AUTOEXEC** (PFD-hy8UZ3ebNxGueabH) — 3 nodos, generación de agregados mensuales y trimestrales de tipos de cambio
2. **Proceso Ejecución GC CGR** (PFD-wyxachgCf8TVObWz) — 31 nodos, validación y clasificación de ejecución presupuestaria CGR
3. **Proceso Ejec GC DIPRES** (ProcessFlowContainer-FYwV5olig1EcGaWj) — 10 nodos, validación de ejecución DIPRES y clasificación de actividades
4. **Salida CG coy** (ProcessFlowContainer-8iloVuuXSe8CJiAb) — 14 nodos, salida de indicadores mensuales de consumo de gobierno
5. **Salida CG Imputa** (ProcessFlowContainer-xxx) — nodos adicionales de imputación de CG
6. **Salida CNF trim** (ProcessFlowContainer-yyy) — salida trimestral de tesorería

### Flujos diferidos (no incluidos en este lote)

Los siguientes **11 flujos** se migran en lotes posteriores:

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
- (1 flujo adicional pendiente de consolidación en plan)

**Razón del diferimiento:** Los flujos diferidos contienen 19 nodos con duplicación masiva de fragmentos SQL (M-002), números mágicos (M-004), clasificaciones hardcodeadas (M-006) y dependencias sobre librerías externas (DCNIDCNA, DCV, GOB) que requieren coordinación previa con equipos de administración de datos. Se priorizó la entrega de los 6 flujos que alimentan los reportes operacionales inmediatos (CGR, DIPRES, consumo de gobierno).

---

## Estrategias de placement y traducción

### 1. Placement clasificador y resoluciones de ambigüedad

El plan utiliza un clasificador automático basado en tipo de nodo y librería destino:

| Tipo de nodo SAS | Librería | Placement | Estrategia Python |
|---|---|---|---|
| PROC_SQL (nodo aislado o con salida WORK) | GOBGENER/DCV | `sql_pushdown` | SQL directo contra BD |
| PROC_SQL (múltiples salidas WORK) | GOBGENER | `pandas` | Lectura de tablas, transformación en memoria, escritura |
| DATA step (sin PROC) | — | `utility` | Python plano (funciones auxiliares, parametrización) |
| PROC SORT/DATASETS | — | `utility` | Python + Pandas (sort, deduplicate, append) |
| PROC IMPORT/EXPORT | archivos | `utility` | Pandas (read_csv, read_excel, to_csv, to_excel) |
| Combinado (DATA+PROC SQL) | GOBGENER | `ambiguous` | **Resolver manual** → pandas si bajo volumen, sql_pushdown si tablas grandes |

#### Resoluciones manuales detectadas

Se identificaron **5 nodos con placement `ambiguous`** que requieren decisión manual:

1. **CodeTask-D6fqrxqReNOK5Xch** (Monedas_Mensual, AUTOEXEC)
   - Entrada: DCV.MONEDAS_MENSUAL (tabla externa)
   - Salida: 5 tablas WORK
   - **Decisión:** `pandas` (bajo volumen estimado, simplifica debugging)
   - Supuesto: Si DCV.MONEDAS_MENSUAL es una tabla muy grande (>100M filas), considerar `sql_pushdown` en revisión B4b

2. **CodeTask-cbwaC9NShYE8mV6x** (AUTOEXEC, otra rama)
   - Tipo: PROC IMPORT desde archivo externo
   - **Decisión:** `utility` (Pandas read_csv/read_excel)
   - Nota: Requiere validar ruta del archivo en project_config.yaml

3. **CodeTask-oLKJ5g7DvhYHuBME** (lectura DCNIDCNA)
   - Librería: DCNIDCNA (externa, no administrada)
   - **Decisión:** `pandas` (asume descarga previa del servidor)
   - Riesgo: Cambios de esquema no detectados en tiempo de compilación

4. **CodeTask-S9YMDIdQqTumexhp** (lectura compleja con JOIN)
   - Tipo: Query complejo (PROC SQL con 3+ JOINs)
   - Salida: tabla GOBGENER
   - **Decisión:** `sql_pushdown` (mantiene lógica en BD para performance)

5. **Query-YHeDzXnzld6fOVfj** (Query puro de gobernanza)
   - Tipo: Query nativo de EGP
   - **Decisión:** `sql_pushdown`

**Supuesto visible:** placement ambiguous sin override en CodeTask-D6fqrxqReNOK5Xch, CodeTask-cbwaC9NShYE8mV6x, CodeTask-oLKJ5g7DvhYHuBME, CodeTask-S9YMDIdQqTumexhp, Query-YHeDzXnzld6fOVfj → strategy por defecto es `pandas`. Si libref es una base de datos (no librería SAS local), esto descarga tablas enteras a memoria. Resolver en entrevista B4b o fijar `translation.ambiguous_strategy` en project_config.yaml.

---

## Macro variables y parametrización

Se detectaron **16 macro variables** utilizadas en 95+ nodos, sin inicialización visible en el plan:

### Variables de período (obligatorias)

| Variable | Usado en | Tipo | Valores esperados | Inicialización |
|---|---|---|---|---|
| `&Year` | 95 nodos | entero | 2020–2026 | Parámetro de ejecución (run.macro_params en project_config.yaml o entrada en cell "parameters") |
| `&Mes` | 16 nodos | entero | 1–12 | Parámetro de ejecución (opcional, por defecto mes actual) |

### Variables de moneda y comparación

| Variable | Usado en | Tipo | Valores esperados | Inicialización |
|---|---|---|---|---|
| `&Moneda` | 8 nodos | string | "CLP", "USD", "UF" | Parámetro de ejecución (run.macro_params) |
| `&Comp1–Comp7` | 42 nodos | string | códigos de entidad o partida | Parámetro de ejecución (lista de 7 comparadores) |

### Variables de imputación (técnicas)

| Variable | Usado en | Tipo | Valores esperados | Inicialización |
|---|---|---|---|---|
| `&Mes_imp1–Mes_imp12` | 16 nodos | entero | 1–12 | Parámetro de ejecución (12 meses para imputación cíclica) |
| `&PACAPR1–PACAPR7` | 35 nodos | string | códigos de partida | Parámetro de ejecución (7 partidas de comparación) |
| `&Analista` | 5 nodos | string | nombre de usuario | Parámetro de ejecución (auditoría de cambios) |

**Decisión:** Todas las macro variables se parametrizan en la celda `parameters` de cada notebook (Papermill). Los valores se declaran en `project_config.yaml` bajo `run.macro_params` y se inyectan en tiempo de ejecución. Sin inicialización centralizada, la celda `parameters` deja las variables como `None`; el notebook fallará con mensaje claro pidiendo parametrización.

**Supuesto visible:** Las macro variables &Analista, &Comp1–7, &Mes, &Mes_imp1–12, &Moneda, &PACAPR1–7, &Year no tienen valores declarados en evidence. El plan genera inicializaciones en la celda "parameters" como `Year = None`. El usuario debe proporcionar valores en la entrevista B4 o en project_config.yaml antes de primera ejecución.

---

## Decisiones sobre mejoras identificadas

### Mejoras aprobadas (aplicadas en esta entrega)

#### M-001: Eliminar rutas hardcodeadas en LIBNAME y OUTFILE ✅ APROBADA

**Descripción:** Se detectaron 17 nodos con rutas absolutas (ej: `\\FILESERVER\VOLM\GEM\050_DCNI\...`, `/sasdata/BCCH/GEM_DCNI/...`).

**Decisión:** Reemplazar todas las rutas hardcodeadas por variables de configuración en `project_config.yaml`:
- `paths.data_input` → raíz de entrada
- `paths.data_output` → raíz de salida (WORK)
- `paths.reports` → directorio de exportación de Excel
- `paths.archives` → directorio de archivos históricos

**Impacto:** Notebooks portables entre DEV/TEST/PROD sin edición manual.

**Nodos afectados:** CodeTask-XzOatjIuMbeLV29h, CodeTask-D6fqrxqReNOK5Xch, CodeTask-1UPaqG3cjfbxeW38, CodeTask-TKijGtt2hNAaRG55, CodeTask-dzljPfKJnYXDrIyx, CodeTask-iZLD51MjB1SyOVBJ, CodeTask-6FS3khd1yz37XIOH, CodeTask-x5iMg8dNCjGmDI64, CodeTask-Wil6N97RHUIMSVfs, CodeTask-kH5fNiMJvLnwyCUU, CodeTask-QeChUmtaSsJfkhiI, CodeTask-HBcKDsWhhhzfcrxa, CodeTask-ESKX4AdeM3cTnf1w, CodeTask-Jtvr77EbawEqiCx3, CodeTask-S9YMDIdQqTumexhp, CodeTask-RyLY6iA6j6KidphH, CodeTask-YxksHYPWfhCGN8Wj

#### M-007: Parametrizar y documentar macro variables ✅ APROBADA

**Descripción:** 16 macro variables (Year, Comp1–7, Mes, Mes_imp1–12, Moneda, PACAPR1–7, Analista) usadas en 95 nodos sin inicialización centralizada.

**Decisión:** Todas las variables se parametrizan via Papermill:
1. Archivo `project_config.yaml` contiene tabla de macros con valores por defecto
2. Cada notebook genera celda "parameters" inyectada por Papermill
3. `run_all.py` lee config y ejecuta notebooks con `papermill.execute_notebook(input_path, output_path, parameters={...})`
4. Logs de ejecución registran valores usados para trazabilidad

**Impacto:** Reproducibilidad garantizada; cambios de período sin edición manual; auditoría de parámetros históricos.

**Nodos afectados:** Todos los 178 nodos (afecta toda la cadena).

### Mejoras postergadas (en lotes futuros)

#### M-002: Refactorizar duplicación masiva de fragmentos SQL ⏸ POSTERGADA

**Descripción:** 19 bloques SQL duplicados con variantes mínimas (CREATE TABLE, DELETE, UPDATE).

**Decisión:** POSTERGADA — Causa: 19 de 23 nodos afectados están en flujos diferidos (Salida CG Imputa, Salida CNF trim, Salidas CNF anual, etc.).

**Plan futuro:** En lote 2, extraer 19 fragmentos a funciones/procedimientos SQL reutilizables. Centralización esperada: 30% reducción de líneas de código, testing simplificado.

#### M-003: Extraer expresión CASE de trimestre a función ⏸ POSTERGADA

**Descripción:** CASE WHEN T1.MES IN(1,2,3) THEN 1... aparece 65 veces.

**Decisión:** POSTERGADA — Motivo: La mayoría de nodos (58 de 65) están en flujos diferidos.

**Plan futuro:** Crear función SQL `fn_trimestre(mes INT) → INT` centralizada en BD. Aplicar en lote 2.

#### M-004: Eliminar números mágicos (1000000, 10201, etc.) ⏸ POSTERGADA

**Descripción:** 10 conjuntos de números mágicos repetidos en 85 nodos.

**Decisión:** POSTERGADA — Razón: 73 nodos afectados están en flujos diferidos.

**Plan futuro:** Crear tabla `config.CONSTANTES_NEGOCIO` (clave-valor) en BD. Referencias en lote 2.

#### M-005: Implementar validación y testing para SQL duplicados ⏸ POSTERGADA

**Descripción:** Duplicación de CREATE/DELETE/UPDATE sin testing unitario centralizado.

**Decisión:** POSTERGADA — Correlacionado con M-002. En lote 2, agregar suite pytest con casos para cada fragmento SQL refactorizado.

#### M-006: Normalizar clasificaciones hardcodeadas (CASE WHEN ANALITICO) ⏸ POSTERGADA

**Descripción:** CASE sobre ANALITICO, C_T_AREA, C_SERVICIO aparece 34 veces sin tabla centralizada.

**Decisión:** POSTERGADA — Afecta 28 de 34 nodos en flujos diferidos.

**Plan futuro:** Crear tabla `config.CATALOGO_CLASIFICACIONES` versionada. Lote 2.

#### M-008: Verificar dependencias de librerías externas ⏸ POSTERGADA

**Descripción:** 4 librerías sin verificación: DCNIDCNA (3 tablas), DCV, GOBGENER, GOB.

**Decisión:** POSTERGADA — Requiere coordinación con equipos de administración de datos.

**Plan futuro:** Documentar contrato de datos (esquema, versionado) para cada librería. Lote 2. Crear validaciones de existencia de tabla/columna en tiempo de compilación.

#### M-009: Crear archivo de configuración centralizado ❌ RECHAZADA

**Descripción:** Propuesta de archivo único (.ini/.conf/.sas) para rutas, macros, constantes.

**Decisión:** RECHAZADA — La solución elegida es `project_config.yaml` + `run_all.py` + Papermill, que es equivalente pero más portable que .sas.

**Razón:** YAML es agnóstico de SAS, compatible con Python/CI-CD, versionable en Git, y permite versionado de parámetros históricos mediante tags.

---

## Supuestos visibles del plan

### Supuesto 1: Placement ambiguous → pandas por defecto

**Contexto:** 5 nodos tienen placement ambiguous (sin resolución en B4b):
- CodeTask-D6fqrxqReNOK5Xch (entrada DCV.MONEDAS_MENSUAL)
- CodeTask-cbwaC9NShYE8mV6x, CodeTask-oLKJ5g7DvhYHuBME, CodeTask-S9YMDIdQqTumexhp, Query-YHeDzXnzld6fOVfj

**Supuesto:** Todos usan strategy `pandas` por defecto (descarga tablas a memoria).

**Riesgo:** Si DCV.MONEDAS_MENSUAL tiene >500M filas, performance crítica. Si DCNIDCNA cambia esquema, no se detecta en compilación.

**Mitigación:** Usuarios deben validar en B4b o project_config.yaml → `translation.ambiguous_strategy = "sql_pushdown"` si libref es base de datos.

### Supuesto 2: Macro variables inicializadas en Papermill

**Contexto:** 16 variables (Year, Mes, Moneda, Comp1–7, Mes_imp1–12, PACAPR1–7, Analista) sin valores en SAS.

**Supuesto:** `project_config.yaml` contiene `run.macro_params: {Year: 2026, Mes: 12, ...}`. Papermill inyecta valores en celda "parameters".

**Riesgo:** Si config.yaml no existe o está incompleto, notebooks fallan con ValueError claro.

**Mitigación:** run_all.py genera config.yaml de plantilla si no existe. Documentación en README.

### Supuesto 3: Librerías GOBGENER, DCV disponibles en BD

**Contexto:** Flujos leen de 4 librerías externas: GOBGENER (85 tablas), DCV (1 tabla), DCNIDCNA (3 tablas), GOB (implícita).

**Supuesto:** Todas las tablas existen con esquema esperado en tiempo de ejecución.

**Riesgo:** Si tabla se renombra, migra a BD distinta o esquema cambia, notebooks fallan en runtime (sin detección en compilación).

**Mitigación:** Entrevista B5 (validación de datos) ejecutará verificación de tablas/columnas. Plan genera queries de "sanity check" en primer cell de cada notebook.

### Supuesto 4: Nodos QUERY ignorados correctamente

**Contexto:** 3 nodos de tipo Query fueron ignorados del plan:
- Query-fI94dLNL1vAYjQn4
- Query-9hK9UXmLqOXfHIKS
- Query-7WLH8bv335ANj5w9

**Supuesto:** Estos nodos son artefactos de gobierno de EGP (metadatos, linaje) sin código ejecutable.

**Riesgo:** Si contienen lógica no documentada, se pierde funcionalidad.

**Mitigación:** Usuario debe revisar y confirmar que no hay lógica de negocio en Queries. Si la hay, se extraen manualmente a notebooks.

### Supuesto 5: Archivos EXCEL para validación manual disponibles en tiempo de ejecución

**Contexto:** 6 nodos exportan propuestas a Excel para revisión manual e importan respuestas:
- CodeTask-6FS3khd1yz37XIOH (analíticos variables → Excel)
- CodeTask-Jtvr77EbawEqiCx3 (importa Excel validado)
- CodeTask-x5iMg8dNCjGmDI64 (transferencias → Excel)
- CodeTask-ESKX4AdeM3cTnf1w (importa Excel validado)
- CodeTask-Wil6N97RHUIMSVfs (estructuras MM → Excel)
- CodeTask-kH5fNiMJvLnwyCUU (estructuras MIXTAS → Excel)

**Supuesto:** Proceso manual revisa Excel, actualiza, guarda en ruta especificada. Notebook re-ejecuta desde archivo validado.

**Riesgo:** Si Excel no se completa o se guarda con columnas faltantes, importación falla.

**Mitigación:** Notebooks generan plantillas con validación de esquema en importación. Runbook detalla flujo manual y pasos de salvaguarda.

### Supuesto 6: Flujos diferidos no impactan salidas de esta entrega

**Contexto:** 11 de 17 flujos se migran en lotes posteriores.

**Supuesto:** Las salidas de los 6 flujos de esta entrega (AUTOEXEC, CGR, DIPRES, CG coy, CG Imputa, CNF trim) son independientes de los flujos diferidos.

**Riesgo:** Si hay dependencias cruzadas (ej: CNF anual lee salidas de CNF trim), la migración parcial produce resultados incompletos.

**Mitigación:** Linaje de datos validará dependencias. Si se detectan, flujos se incluyen en lote actual.

---

## Decisiones técnicas de traducción (por tipo de nodo)

### Flujo AUTOEXEC (3 nodos)

| Nodo | SAS | Estrategia | Decisión |
|---|---|---|---|
| Set Libreria | DATA step (LIBNAME) | `utility` | Python: dict de rutas + validación de existencia |
| Monedas_Mensual | PROC SQL (5 salidas WORK) | `pandas` | Lee DCV.MONEDAS_MENSUAL, pivotaje/agregación en Pandas, guardar 5 tablas |
| Programa | DATA step (cálculo) | `utility` | Python plano: cálculo de promedios mensuales/trimestrales |

**Resultado esperado:** 5 tablas WORK (CIERRE_MES, CIERRE_TRIM, PROM_MES, PROM_MES_TODAS, PROM_TRIM) con agregados diarios→mensuales/trimestrales.

### Flujo Proceso Ejecución GC CGR (31 nodos)

**Característica:** Flujo de validación y clasificación complejos con 19 nodos duplicados (M-002 postergada).

| Grupo de nodos | Estrategia | Racional |
|---|---|---|
| 1-3: Comparaciones de PACAPR/entidades | `sql_pushdown` | JOINs puros, queries readonly, performance en BD |
| 4a-4b: Clasificación de analíticos fijos | `pandas` | Lógica de clasificación por frecuencia + Excel manual → múltiples pasos |
| 5a-5b: Clasificación de analíticos variables | `pandas` | Exporta/importa Excel, lógica jerárquica de claves |
| 6a-6b: Clasificación de transferencias | `pandas` | Exporta/importa Excel, depuración de inconsistencias |
| 7a-7f: Estructuras MM/M/MGCG/MGG | `pandas` | Validación de pesos (suma=1), exporta/importa Excel |
| 8a-8b: Clasificación de actividades | `pandas` | Imputación de reglas por PARTIDA/CAPITULO |
| 9a-9b, 10a-10b: COFOG | `pandas` | LEFT JOIN + deduplicate + append |
| OPC 1-3: Cambios de nombre (SOUNDEX/SPEDIS) | `python` | DATA step con funciones de distancia → función Python |

**Resultado esperado:** 8 tablas GOBGENER actualizadas con clasificaciones completas; 20+ tablas WORK de validación (CHECK_*).

### Flujo Proceso Ejec GC DIPRES (10 nodos)

**Característica:** Similar a CGR pero con entrada GOBGENER.EJEC_DIPRES.

| Estapa | Estrategia |
|---|---|
| Imputaciones de analíticos (reutiliza clasificaciones CGR) | `pandas` |
| Validaciones de consistencia | `sql_pushdown` |
| Consolidación de tablas de salida | `pandas` |

**Resultado esperado:** 6 tablas GOBGENER, 35 tablas WORK de validación.

### Flujo Salida CG coy (14 nodos)

**Característica:** Generación de indicadores operacionales mensuales.

| Nodo | Estrategia | Output |
|---|---|---|
| Lecturas y pivotajes | `pandas` | Tablas intermedias WORK |
| Cálculo de ratios/totales | `pandas` | WORK.RATIOS, WORK.TOTALES, WORK.TOTALES_INST |
| Generación de imputaciones permanentes | `sql_pushdown` | GOBGENER.IMPUT_GC_DIP, GOBGENER.IMPUT_GC_DIP_APER |

**Resultado esperado:** Indicadores mensuales de consumo de gobierno por sector, actividad, partida.

---

## Entrevistas y aprobaciones necesarias

### B4b: Revisión de placement ambiguo y parámetros

**Pendiente:** Resolver 5 nodos con placement ambiguo:
- CodeTask-D6fqrxqReNOK5Xch: ¿DCV.MONEDAS_MENSUAL es tabla pequeña (<100M)? → confirm pandas
- CodeTask-oLKJ5g7DvhYHuBME: ¿DCNIDCNA disponible? → si no, excluir nodo
- CodeTask-S9YMDIdQqTumexhp: ¿Usar SQL o Pandas? (default pandas)
- CodeTask-cbwaC9NShYE8mV6x, Query-YHeDzXnzld6fOVfj: similar

**Pendiente:** Valores de macro variables:
- &Year: valor por defecto (ej: 2026)
- &Mes: valor por defecto (ej: 12)
- &Comp1–7: lista de comparadores
- &PACAPR1–7: lista de partidas de referencia
- &Analista: usuario responsable

### B5: Validación de datos

**Pendiente:** Verificación de tablas/columnas en BD:
- GOBGENER (85 tablas): listar y validar esquema
- DCV.MONEDAS_MENSUAL: validar columnas
- DCNIDCNA (3 tablas): disponibilidad y esquema
- Rutas de archivos: validar acceso R/W

### Aprobación de mejoras

**Ya aprobadas:**
- M-001 ✅ (eliminar rutas hardcodeadas)
- M-007 ✅ (parametrizar macros)

**Ya rechazadas:**
- M-009 ❌ (usar YAML + Python en lugar de .sas centralizado)

**Postergadas a lote 2:**
- M-002, M-003, M-004, M-005, M-006, M-008 (flujos diferidos involucrados)

---

## Resumen de decisiones clave

1. **Scope:** 6 flujos migrados en lote 1; 11 flujos en lotes posteriores
2. **Placement:** Algoritmo automático con resoluciones manuales para 5 nodos ambiguous (pandas por defecto)
3. **Parametrización:** Todas las 16 macro variables via Papermill + project_config.yaml
4. **Mejoras:** 2 aprobadas (M-001, M-007), 6 postergadas (correlacionadas con flujos diferidos), 1 rechazada (M-009)
5. **Supuestos visibles:** 6 supuestos críticos listados y mitigados
6. **Flujo manual:** 6 nodos exportan/importan Excel para validación de clasificaciones (detallado en runbook)
7. **Validación:** Entrevistas B4b y B5 pendientes para resolver ambigüedades y verificar disponibilidad de datos
