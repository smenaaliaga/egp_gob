# Mejoras de la Migración

## Introducción

Este documento describe las mejoras identificadas durante el análisis de la traducción del proyecto **Proc_Salidas_Gob_REV_mig** de SAS a Python. Se presentan las mejoras evaluadas, su estado de decisión (aprobada, rechazada o postergada) y la aplicación efectiva en la migración.

La estrategia de mejoras sigue un criterio de impacto vs. esfuerzo: aquellas con impacto alto y esfuerzo medio fueron priorizadas para esta entrega; las de alto esfuerzo se posponen a lotes posteriores cuando sus nodos entren en traducción.

---

## Resumen Ejecutivo

- **Total de mejoras identificadas**: 9
- **Aprobadas e implementadas**: 2 (M-001, M-007)
- **Rechazadas**: 1 (M-009)
- **Postergadas** (deferred_batch): 6 (M-002, M-003, M-004, M-005, M-006, M-008)

Las mejoras aprobadas se aplican a **17 nodos** en flujos de esta entrega (AUTOEXEC, Proceso Ejecución GC CGR, Proceso Ejec GC DIPRES, Salida CG coy). Las postergadas afectan nodos en flujos diferidos y serán revisadas cuando esos flujos entren en traducción.

---

## Mejoras Aprobadas e Implementadas

### M-001: Eliminar rutas hardcodeadas en LIBNAME y OUTFILE

**Estado**: ✅ Aprobado e implementado

**Categoría**: Mantenibilidad

**Descripción**:
Se detectaron 17 nodos con rutas absolutas hardcodeadas en las definiciones de LIBNAME y OUTFILE, incluyendo:
- Rutas UNC: `\\FILESERVER\VOLM\GEM\050_DCNI\...` (CodeTask-1UPaqG3cjfbxeW38)
- Rutas Unix/Linux: `/sasdata/BCCH/GEM_DCNI/...` (CodeTask-XzOatjIuMbeLV29h)

**Nodos afectados**:
CodeTask-1UPaqG3cjfbxeW38, CodeTask-6FS3khd1yz37XIOH, CodeTask-D6fqrxqReNOK5Xch, CodeTask-dzljPfKJnYXDrIyx, CodeTask-ESKX4AdeM3cTnf1w, CodeTask-HBcKDsWhhhzfcrxa, CodeTask-iZLD51MjB1SyOVBJ, CodeTask-Jtvr77EbawEqiCx3, CodeTask-kH5fNiMJvLnwyCUU, CodeTask-QeChUmtaSsJfkhiI, CodeTask-RyLY6iA6j6KidphH, CodeTask-S9YMDIdQqTumexhp, CodeTask-TKijGtt2hNAaRG55, CodeTask-Wil6N97RHUIMSVfs, CodeTask-x5iMg8dNCjGmDI64, CodeTask-XzOatjIuMbeLV29h, CodeTask-YxksHYPWfhCGN8Wj

**Justificación**:
Rutas hardcodeadas impiden portabilidad entre ambientes (DEV, TEST, PROD) y entre sistemas de archivos. Violación de principios de configuración externalizada. Generan fallos silenciosos cuando se cambia servidor o estructura de directorios.

**Impacto**: Alto (portabilidad crítica)  
**Esfuerzo**: Medio (refactorización centralizada)  
**Riesgo**: Medio (cambios aislados sin dependencias cruzadas)

**Aplicación en la migración**:
- Las rutas se externalizan en un archivo de configuración `config/paths.yaml` 
- Los notebooks traducen accesos a librerías y archivos mediante variables de entorno y lectura de config
- En Python se usan `os.path.join()` y variables de entorno (`$PROJECT_ROOT`, `$DATA_DIR`, `$OUTPUT_DIR`)
- Se proporciona plantilla `config/paths_template.yaml` con documentación de rutas esperadas
- Notebooks validan existencia de rutas al inicio (celda de validación)

---

### M-007: Parametrizar y documentar macro variables (Year, Comp1-7, Mes_imp)

**Estado**: ✅ Aprobado e implementado

**Categoría**: Reproducibilidad

**Descripción**:
7 macro variables críticas usadas en 95 nodos del flujo:
- **Year**: año fiscal de ejecución (ej: 2024)
- **Comp1 a Comp7**: 7 comparadores presupuestarios (códigos de comparación)
- **Mes_imp1 a Mes_imp12**: 12 meses de imputación (períodos de correcciones)

Sin inicialización visible ni documentación de valores esperados. Cambios de período requieren edición manual en múltiples nodos.

**Nodos afectados**: 95 nodos distribuidos en múltiples flujos, incluyendo:
CodeTask-19o6EdegIblGxthd, CodeTask-217TBwmLOKn9s1Im, CodeTask-2u1eOTvq3sZo1V34, CodeTask-3GhPnDCy9p2wBP7i, CodeTask-4Vv4xGyymdoAYMNg, ... (y 85 más)

**Justificación**:
Macro variables sin parametrización impiden:
1. **Reproducibilidad**: imposible repetir ejecución con parámetros diferentes sin edición manual
2. **Trazabilidad**: no queda registro de qué valores se usaron en ejecuciones pasadas
3. **Automatización**: bloquea generación de reportes comparativos por período

**Impacto**: Alto (afecta reproducibilidad crítica)  
**Esfuerzo**: Medio (parametrización centralizada)  
**Riesgo**: Medio (cambios no tienen efectos secundarios)

**Aplicación en la migración**:
- Se crea celda `parameters` en **cada notebook** con valores por defecto
- Se proporciona archivo `project_config.yaml` con diccionario de parámetros:
  ```yaml
  run:
    year: 2024
    comparadores: ["COMP1", "COMP2", "COMP3", "COMP4", "COMP5", "COMP6", "COMP7"]
    meses_imputacion: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    periodo_inicio: "2024-01-01"
    periodo_fin: "2024-12-31"
  ```
- Los notebooks leen parámetros en la celda `parameters` (Papermill compatible)
- Se documenta en `runbook` cómo sobrescribir parámetros por ejecución
- Se incluye script `run_all.py` que acepta argumentos CLI para parámetros

---

## Mejoras Rechazadas

### M-009: Crear archivo de configuración centralizado para parámetros de ejecución

**Estado**: ❌ Rechazado

**Categoría**: Reproducibilidad

**Descripción**:
Propuesta de crear archivo de configuración monolítico (.ini, .conf, .sas) que centralice:
- Rutas de librerías (LIBNAME)
- Macro variables (Year, Comp1-7, Mes_imp)
- Valores de filtros (C_CUENTA, C_ANALITICO, C_ENTIDAD)
- Factores de conversión (1000000)
- Parámetros históricos versionados

**Motivo del rechazo**:
Esta mejora fue **rechazada en favor de M-001 y M-007**, que abordan los problemas de forma modular:
- **M-001** resuelve rutas mediante `config/paths.yaml`
- **M-007** parametriza macro variables con `project_config.yaml` + celda `parameters` en notebooks
- Un archivo monolítico de configuración violaría el principio de separación de responsabilidades (rutas ≠ parámetros de ejecución)
- La solución modular permite que cada notebook sea independiente y portable

**Recomendación alternativa**:
Mantener estrategia de configuración distribuida pero documentada:
- `config/paths.yaml` → rutas
- `project_config.yaml` → parámetros de ejecución
- Documentación en `README.md` de cómo ajustar cada archivo

---

## Mejoras Postergadas (Deferred Batch)

Las siguientes 6 mejoras fueron **postergadas** porque sus nodos están en flujos que **no se traducen en esta entrega**. Se reevaluarán cuando esos Process Flows entren en traducción posterior.

### M-002: Refactorizar duplicación masiva de fragmentos SQL

**Estado**: ⏸️ Postergado (deferred_batch)

**Categoría**: Mantenibilidad

**Descripción**:
Se detectaron 19 bloques SQL duplicados con variantes mínimas:
- Fragmento 'CREATE TABLE CR18_APERTURA_PACAPR AS SELECT...' repetido en 19 nodos
- Fragmento DELETE sobre tablas similares repetido en 7 nodos
- Fragmento UPDATE repetido en 5 nodos

**Impacto**: Alto (exponencial de mantenimiento)  
**Esfuerzo**: Alto (refactorización compleja)  
**Riesgo**: Alto (riesgo de introducir inconsistencias)

**Razón de postergación**:
Los 19 nodos afectados pertenecen a flujos diferidos (Salida CG Imputa, Salida CNF trim, Salidas CNF anual y COFOG, etc.), que se traducirán en lotes posteriores.

**Recomendación**:
Cuando se traduzcan esos flujos, consolidar fragmentos SQL duplicados en:
- Funciones SQL/Python parametrizadas
- Módulo `lib/sql_templates.py` con plantillas reutilizables

---

### M-003: Extraer expresión CASE de cálculo de trimestre a función/macro

**Estado**: ⏸️ Postergado (deferred_batch)

**Categoría**: Mantenibilidad

**Descripción**:
La expresión CASE WHEN para cálculo de trimestre aparece idéntica en 65 nodos:
```sql
CASE WHEN T1.MES IN(1,2,3) THEN 1 
     WHEN T1.MES IN(4,5,6) THEN 2 
     WHEN T1.MES IN(7,8,9) THEN 3 
     WHEN T1.MES IN(10,11,12) THEN 4 
END AS TRIMESTRE
```

**Impacto**: Alto (lógica de negocio crítica)  
**Esfuerzo**: Medio (extracción a función)  
**Riesgo**: Medio (cambios centralizados)

**Razón de postergación**:
65 nodos afectados están distribuidos en flujos diferidos.

**Recomendación**:
Crear función centralizada `lib.date_utils.mes_to_trimestre(mes: int) -> int` que se reutilice en pandas/SQL.

---

### M-004: Eliminar números mágicos en expresiones SQL

**Estado**: ⏸️ Postergado (deferred_batch)

**Categoría**: Mantenibilidad

**Descripción**:
Se detectaron 10 conjuntos de números mágicos repetidos sin documentación:
- **'1000000'**: conversión de millones (85 nodos)
- **'10201'**, **'5601'**: códigos de entidad/partida (45 nodos cada uno)
- **'04001000'**, **'04002000'**: códigos de estructura (34 nodos)
- **'000'**, **'01000000'**, **'3801'**, **'004'**, **'03000000'**: otros filtros

**Impacto**: Medio (comprensión y auditoría)  
**Esfuerzo**: Medio (extracción a constantes)  
**Riesgo**: Medio (cambios aislados)

**Razón de postergación**:
Nodos afectados en flujos diferidos.

**Recomendación**:
Crear módulo `lib/constants.py` con todas las constantes de negocio documentadas:
```python
# Factores de conversión
CONVERSION_MILLIONS = 1_000_000

# Códigos de entidad
ENTITY_CODE_GOV_CENTRAL = '10201'
ENTITY_CODE_MUNICIPAL = '5601'

# Códigos de cuenta
ACCOUNT_CODE_INCOME = '04001000'
ACCOUNT_CODE_EXPENSE = '04002000'
```

---

### M-005: Implementar validación y testing para fragmentos SQL duplicados

**Estado**: ⏸️ Postergado (deferred_batch)

**Categoría**: Calidad

**Descripción**:
19 fragmentos CREATE TABLE y variantes DELETE/UPDATE duplicados carecen de pruebas unitarias visibles. Inconsistencias potenciales entre versiones.

**Impacto**: Alto (riesgo de corrupción de datos)  
**Esfuerzo**: Alto (suite de testing)  
**Riesgo**: Alto (detecta divergencias peligrosas)

**Razón de postergación**:
Depende de M-002 (refactorización); bloqueada hasta que esos flujos entren en traducción.

**Recomendación**:
Crear suite pytest en `tests/test_sql_deduplication.py` con:
- Fixtures de tablas de prueba
- Validaciones de integridad referencial
- Tests de equivalencia entre variantes SQL

---

### M-006: Normalizar y documentar valores mágicos de clasificación (CASE WHEN ANALITICO)

**Estado**: ⏸️ Postergado (deferred_batch)

**Categoría**: Calidad

**Descripción**:
Clasificaciones hardcodeadas en lógica SQL sin tabla de referencia centralizada:
- **CASE WHEN T2.ANALITICO='M'**: repetida en 23 nodos
- **CASE sobre C_T_AREA** (GM/ED/SL → AAPP/EEPP/SSPP): 6 nodos
- **CASE sobre C_SERVICIO** (1/2/3): 5 nodos

Sin versionado de reglas de negocio.

**Impacto**: Medio (auditoría y gobernanza)  
**Esfuerzo**: Medio (extracción a tablas de referencia)  
**Riesgo**: Medio (cambios centralizados)

**Razón de postergación**:
Nodos en flujos diferidos.

**Recomendación**:
Crear tablas de referencia en BD:
- `GOBGENER.ANALITICO_MAPPING` (tipos de analíticos)
- `GOBGENER.AREA_CLASSIFICATION` (C_T_AREA → clasificación)
- `GOBGENER.SERVICE_TYPE_MAPPING` (C_SERVICIO → tipo de servicio)

E implementar como lookups DataFrame en Python.

---

### M-008: Verificar y documentar dependencias de librerías externas

**Estado**: ⏸️ Postergado (deferred_batch)

**Categoría**: Reproducibilidad

**Descripción**:
4 librerías/esquemas sin verificación de estructura:
- **DCNIDCNA**: 3 tablas (BDATOS_SP, CODIGO_ENTIDAD_SP, EJEC_MUN) en 3 nodos
- **DCV**: MONEDAS_MENSUAL en 1 nodo
- **GOBGENER** y **GOB**: esquemas ampliamente usados

Sin validación de existencia ni contrato de datos (columnas, tipos).

**Impacto**: Alto (fallos silenciosos)  
**Esfuerzo**: Medio (validación en tiempo de compilación)  
**Riesgo**: Alto (detección tardía de cambios de esquema)

**Razón de postergación**:
Nodos afectados en flujos diferidos.

**Recomendación**:
Crear módulo `lib/data_contracts.py` con:
- Esquemas esperados (columnas, tipos, restricciones)
- Función de validación contra BD real
- Verificación ejecutada al inicio de cada notebook

---

## Impacto de Mejoras Aprobadas en la Migración

### En el Código Traducido

| Aspecto | Antes (SAS) | Después (Python/Notebooks) |
|---------|------------|---------------------------|
| **Rutas hardcodeadas** | ✗ 17 nodos con rutas brutas | ✅ Todas externalizadas en `config/paths.yaml` |
| **Parámetros de ejecución** | ✗ Macro variables sin valor inicial | ✅ Celda `parameters` en cada notebook + `project_config.yaml` |
| **Portabilidad** | ✗ Falla si cambia servidor o directorios | ✅ Portable entre ambientes sin edición de código |
| **Reproducibilidad** | ✗ Imposible cambiar Year/Comp sin edición manual | ✅ CLI flags + Papermill compatible |

### En Operación

- **run_all.py** acepta argumentos de línea de comandos para todos los parámetros
- **Runbook** documenta cómo variar parámetros por ejecución
- Archivo **project_config.yaml** permite cambios sin tocar notebooks
- Archivo **config/paths.yaml** facilita migración a nuevos servidores

---

## Recomendaciones para Lotes Posteriores

Cuando los flujos diferidos entren en traducción:

1. **Retomar M-002, M-003, M-004**: Consolidar duplicación SQL mediante funciones parametrizadas
2. **Implementar M-005**: Suite de testing unitario para fragmentos SQL críticos
3. **Ejecutar M-006**: Refactorizar clasificaciones a tablas de referencia versionadas
4. **Aplicar M-008**: Validación de contratos de datos en tiempo de compilación

Prioridad: **M-002 y M-003** (impacto alto en mantenibilidad) > M-005 (asegura calidad) > M-004, M-006, M-008 (mejoras secundarias).

---

## Conclusión

Las 2 mejoras aprobadas (M-001, M-007) resuelven **críticas de portabilidad y reproducibilidad** en esta entrega. Afectan **17 nodos** de flujos traducidos y **95 nodos** en total del proyecto.

Las 6 mejoras postergadas se abordarán cuando sus nodos entren en traducción posterior, priorizando las de mayor impacto (refactorización de SQL duplicado, testing).

La mejora rechazada (M-009) fue descartada en favor de una estrategia modular más flexible que separa configuración de rutas y parámetros.

Todos los documentos producidos (README, lineage, decisions, runbook) reflejan la aplicación de estas mejoras en el código traducido.
