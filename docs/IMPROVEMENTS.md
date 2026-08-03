# Mejoras — Decisiones y Aplicación

## Introducción

Este documento registra las mejoras identificadas durante el análisis del proyecto **Proc_Salidas_Gob_REV_mig**, clasificadas por estado de decisión (aprobada, rechazada, postergada) y su aplicación en la migración de SAS a Python.

---

## Mejoras Aprobadas

### M-001: Consolidar rutas de archivo hardcodeadas en variables parametrizadas

**Categoría:** Mantenibilidad  
**Estado:** ✅ **APROBADA** — Aplicada en la migración

**Descripción:**  
Se detectaron 17 nodos con rutas de archivo hardcodeadas:
- Ejemplo Windows: `\\FILESERVER\VOLM\GEM\050_DCNI\02_CNSI\16_GOBIERNO\...` (CodeTask-1UPaqG3cjfbxeW38)
- Ejemplo Unix: `/sasdata/BCCH/GEM_DCNI/...` (CodeTask-S9YMDIdQqTumexhp)
- Separadores mixtos generan fallos multiplataforma

**Nodos afectados (17):**  
CodeTask-1UPaqG3cjfbxeW38, CodeTask-6FS3khd1yz37XIOH, CodeTask-D6fqrxqReNOK5Xch, CodeTask-dzljPfKJnYXDrIyx, CodeTask-ESKX4AdeM3cTnf1w, CodeTask-HBcKDsWhhhzfcrxa, CodeTask-iZLD51MjB1SyOVBJ, CodeTask-Jtvr77EbawEqiCx3, CodeTask-kH5fNiMJvLnwyCUU, CodeTask-QeChUmtaSsJfkhiI, CodeTask-RyLY6iA6j6KidphH, CodeTask-S9YMDIdQqTumexhp, CodeTask-TKijGtt2hNAaRG55, CodeTask-Wil6N97RHUIMSVfs, CodeTask-x5iMg8dNCjGmDI64, CodeTask-XzOatjIuMbeLV29h, CodeTask-YxksHYPWfhCGN8Wj

**Justificación:**  
Las rutas hardcodeadas generan acoplamiento con infraestructura específica, impidiendo reutilización entre entornos (DEV/PROD/STAGING). Los separadores mixtos causan fallos en ejecución multiplataforma.

**Recomendación:** Centralizar todas las rutas en un archivo de configuración con variables parametrizadas (ej: `config/paths.yaml` o `_paths.py`) que se cargue al inicio de cada notebook.

**Aplicación en la migración:**  
Se ha creado un módulo centralizado `config/file_paths.py` que contiene todas las rutas parametrizadas. Los notebooks importan este módulo y usan constantes como `PATHS['CHECK_ANALITICOS_EXCEL']` en lugar de hardcodear rutas. Los separadores se normalizan automáticamente según el SO mediante `pathlib.Path`.

**Impacto:** Alto | **Esfuerzo:** Alto | **Riesgo:** Medio

---

### M-005: Centralizar macro variables de usuario (Year, Comp1-7) en archivo de configuración

**Categoría:** Reproducibilidad  
**Estado:** ✅ **APROBADA** — Aplicada en la migración

**Descripción:**  
Macro variables sin centralización detectadas:
- **Year**: usada en 95 nodos (ej: CodeTask-19o6EdegIblGxthd, CodeTask-B9diPVJxt3YvUOgq)
- **Comp1–Comp7**: variables de computación parametrizadas en 21 nodos cada una

Estos parámetros se inicializan implícitamente o están hardcodeados en múltiples scripts, generando dependencias ocultas.

**Nodos afectados (20):**  
CodeTask-19o6EdegIblGxthd, CodeTask-217TBwmLOKn9s1Im, CodeTask-2u1eOTvq3sZo1V34, CodeTask-3GhPnDCy9p2wBP7i, CodeTask-3TTpMTyo2diGXNgR, CodeTask-4Vv4xGyymdoAYMNg, CodeTask-4aWGaC1VmZySxlzM, CodeTask-4g838w5UgiWqIbGy, CodeTask-4wxss6QulJ8PK7Pu, CodeTask-5644937ey7NzmPak, CodeTask-6FS3khd1yz37XIOH, CodeTask-86VdtiWQrF36JEkb, CodeTask-8b6bsW9BKVc7jJXj, CodeTask-94I9bgH6Q4ktjiWH, CodeTask-99VPAhpFklGwBLLO, CodeTask-9HjwuVPWzkAGk1TK, CodeTask-A3JEhgKfE5syST7K, CodeTask-AD4kzP4luBEsTydA, CodeTask-AnOoJdkBHxZcL831, CodeTask-B9diPVJxt3YvUOgq

**Justificación:**  
Sin inicialización centralizada, los valores de macro variables pueden variar según el contexto de ejecución, causando no-determinismo. Esto compromete reproducibilidad y auditoría de cambios.

**Recomendación:** Crear archivo `config/parameters.yaml` o `project_config.py` que declare TODAS las macro variables de entrada (Year, Comp1-7, filtros, periodos) con valores por defecto y documentación clara.

**Aplicación en la migración:**  
Se ha implementado `config/project_config.yaml` que centraliza todos los parámetros globales:
```yaml
run:
  year: 2024
  components: [Comp1, Comp2, ..., Comp7]
  analyst: "Default Analyst"
  periods: [1, 2, ..., 12]
```
Cada notebook carga este archivo mediante una celda de "parámetros" Papermill-compatible. Los valores pueden ser sobrescritos por parámetros CLI en tiempo de ejecución (`run_all.py --year 2025`).

**Impacto:** Alto | **Esfuerzo:** Medio | **Riesgo:** Bajo

---

## Mejoras Postergadas

### M-002: Eliminar duplicación de bloques SQL con tabla de lookup parametrizada

**Categoría:** Calidad  
**Estado:** ⏸️ **POSTERGADA** — *Lote diferido*

**Descripción:**  
Duplicación de bloques SQL detectada:
1. Fragmento `CREATE TABLE CR18_APERTURA_PACAPR` en 19 nodos con JOIN ENTIDADES repetido
2. Variante `DELETE FROM EJECUCION_A_PRELIM_DIP_APER` en 7 nodos
3. Variante `DELETE FROM EJECUCION_A_PRELIM` en 5 nodos
4. `CREATE TABLE EJEC_DIP` en 5 nodos

**Total:** 72 líneas de código duplicado en 45+ nodos

**Nodos afectados (42):**  
CodeTask-2u1eOTvq3sZo1V34, CodeTask-4wxss6QulJ8PK7Pu, CodeTask-94I9bgH6Q4ktjiWH, CodeTask-A3JEhgKfE5syST7K, CodeTask-AD4kzP4luBEsTydA, CodeTask-KgBtsabMAJrXUjkl, CodeTask-PRH1lTSmY7JzJpmI, CodeTask-Vob3Cr2FL8rjXBlH, CodeTask-W5QOX3IfZ4AXUmE2, CodeTask-cjFzgfiIc4f1oaij, CodeTask-cpVfXtbY1fhHpykA, CodeTask-jd7KWCF4lrlo7kqk, CodeTask-kEwO1qvT28cYoAgT, CodeTask-r6G37H7LHWkbbRzg, CodeTask-rmzRDvtUeZ2SkGKc, CodeTask-tPkkXrMn7HpatBGU, CodeTask-tli9YgMo32jhmrKW, CodeTask-v2XeXrcszN91UcUK, CodeTask-wpalwVYAWfwAKJxy, CodeTask-86VdtiWQrF36JEkb, CodeTask-IBn1x34Qkxekgyzd, CodeTask-QazYc6dHjnESiTAF, CodeTask-ZFWBSNwbyPPJmZW3, CodeTask-lLfFqwh2rHhD2IRj, CodeTask-m5Se3FeMZDtIOxcg, CodeTask-uhvFDAbzyY6GHgs9, CodeTask-4Vv4xGyymdoAYMNg, CodeTask-Iyf7PQ2PcCPtQjBv, CodeTask-cC67Jq2LJ4rqaTmz, CodeTask-eZSIe7MX3fTZr9TV, CodeTask-8b6bsW9BKVc7jJXj, CodeTask-eBbsQWPbrDnlFpWd, CodeTask-99VPAhpFklGwBLLO, CodeTask-9HjwuVPWzkAGk1TK, CodeTask-bMqLfdtsanaslAb2, CodeTask-HqGxbifWcl8g9QQH, CodeTask-PfVYfkZipBzGqkdH, CodeTask-RDZUBeSyggbaTi4d, CodeTask-kwUh4TXyxxdvjZsV, CodeTask-z5hLKRPj44xrakAE, CodeTask-IEwZ1IRVGWjGV4HL, CodeTask-e3OMv2r9gQanxJIs

**Justificación:**  
La duplicación genera riesgo de inconsistencia: un cambio en lógica de negocio debe propagarse manualmente a todos los nodos. Refactorizar creando funciones/procedimientos reutilizables que acepten como argumentos: tabla_origen, tabla_destino, criterios WHERE, join clauses. Reduce líneas de código en ~65% y facilita testing centralizado.

**Razón de postergación:**  
Los nodos afectados por M-002 pertenecen a flujos que **no están incluidos en este lote de migración** (AUTOEXEC, Proceso Ejec GC DIPRES, Salida CG coy, Salida CG Imputa, etc.). La mejora se evaluará cuando dichos flujos entren en un lote posterior.

**Aplicación pendiente:**  
Cuando se migre el siguiente lote, se debe refactorizar usando funciones auxiliares Python (ej: `utils/sql_builders.py` con `build_pacapr_table()`, `delete_preliminary_execution()`) que abstraigan la lógica SQL repetida.

**Impacto:** Alto | **Esfuerzo:** Alto | **Riesgo:** Medio

---

### M-003: Consolidar lógica CASE repetida para trimestre y lookup de categorías

**Categoría:** Calidad  
**Estado:** ⏸️ **POSTERGADA** — *Lote diferido*

**Descripción:**  
Expresión CASE WHEN para trimestre (conversión MES→TRIM) aparece en 65 nodos:
```sas
CASE WHEN T1.MES IN(1,2,3) THEN 1 
      WHEN T1.MES IN(4,5,6) THEN 2 
      WHEN T1.MES IN(7,8,9) THEN 3 
      WHEN T1.MES IN(10,11,12) THEN 4 
      ELSE . END
```

También detectada:
- Expresión CASE WHEN para validación analítico (65 líneas) en 23 nodos
- Expresión CASE para mapping C_T_AREA / C_SERVICIO en 6 nodos

**Nodos afectados (65):**  
La mayoría de nodos en flujos postergados (Salida CG coy, Salida CG Imputa, etc.)

**Justificación:**  
Expresiones CASE repetidas generan deuda técnica: cambios en reglas de negocio (ej: trimestralidad diferente, nuevas categorías de área) requieren buscar/reemplazar manual en 65+ nodos. Crear tablas de lookup (formato/trimestre, categorías de área) y usar JOIN en lugar de CASE. Mejora legibilidad y centraliza lógica de negocio.

**Razón de postergación:**  
Los nodos afectados pertenecen a flujos diferidos que se migrarán en lotes posteriores.

**Aplicación pendiente:**  
Crear tablas de lookup centralizadas (ej: `reference/trimestre_lookup.csv`, `reference/categoria_area_lookup.csv`) y usar `pd.merge()` en lugar de CASE en el código Python equivalente.

**Impacto:** Alto | **Esfuerzo:** Medio | **Riesgo:** Bajo

---

### M-004: Extraer magic numbers en constantes nombradas

**Categoría:** Calidad  
**Estado:** ⏸️ **POSTERGADA** — *Lote diferido*

**Descripción:**  
Magic numbers detectados sin centralización:
- `1000000` (divisor para conversión millones) en 85 nodos
- `10201`, `5601` (códigos de entidad) en 45 nodos cada uno
- `04001000`, `04002000` (códigos analíticos) en 34 nodos
- `000`, `01000000`, `3801`, `004`, `03000000` (identificadores) en 19–34 nodos

**Total:** 250+ ocurrencias en 90+ nodos sin centralización

**Nodos afectados (43):**  
CodeTask-3GhPnDCy9p2wBP7i, CodeTask-4Vv4xGyymdoAYMNg, CodeTask-4aWGaC1VmZySxlzM, CodeTask-4g838w5UgiWqIbGy, CodeTask-4wxss6QulJ8PK7Pu, CodeTask-86VdtiWQrF36JEkb, CodeTask-8b6bsW9BKVc7jJXj, CodeTask-94I9bgH6Q4ktjiWH, CodeTask-99VPAhpFklGwBLLO, CodeTask-9HjwuVPWzkAGk1TK, CodeTask-A3JEhgKfE5syST7K, CodeTask-AD4kzP4luBEsTydA, CodeTask-AxUHu9l3ZXZgyFPH, CodeTask-EPQFhuqPwUQWGIUH, CodeTask-EWymYZfj4F3FkhBN, CodeTask-HgxuQHxkMiglCdNx, CodeTask-HqGxbifWcl8g9QQH, CodeTask-IBn1x34Qkxekgyzd, CodeTask-IEwZ1IRVGWjGV4HL, CodeTask-IpxSz3SSWndt6gw1, CodeTask-Iyf7PQ2PcCPtQjBv, CodeTask-KaANumtn2ITOIPrq, CodeTask-KgBtsabMAJrXUjkl, CodeTask-Kx9bMNvufU53o7se, CodeTask-OxOHS4JkGP66hNEq, CodeTask-PRH1lTSmY7JzJpmI, CodeTask-PfVYfkZipBzGqkdH, CodeTask-QazYc6dHjnESiTAF, CodeTask-RDZUBeSyggbaTi4d, CodeTask-Sz8jEg5IW2MOPNnx, CodeTask-Vob3Cr2FL8rjXBlH, CodeTask-ZFWBSNwbyPPJmZW3, CodeTask-bMqLfdtsanaslAb2, CodeTask-cC67Jq2LJ4rqaTmz, CodeTask-cjFzgfiIc4f1oaij, CodeTask-e3OMv2r9gQanxJIs, CodeTask-eBbsQWPbrDnlFpWd, CodeTask-eZSIe7MX3fTZr9TV, CodeTask-ekal3Xobqf5pRWnO, CodeTask-in1v9zw1LdIGECTd, CodeTask-lLfFqwh2rHhD2IRj, CodeTask-m5Se3FeMZDtIOxcg, CodeTask-tli9YgMo32jhmrKW, CodeTask-uhvFDAbzyY6GHgs9

**Justificación:**  
Magic numbers sin contexto semántico generan confusión y errores en mantenimiento. Si `1000000` representa "CONVERSION_A_MILLONES" o `10201` es "COD_ENTIDAD_DIPRES_DIP", usarlos sin nombre reduce legibilidad y facilita cometer errores. Crear archivo de constantes centralizado mejora auditoría y facilita cambios de reglas de negocio.

**Razón de postergación:**  
Los nodos afectados pertenecen mayormente a flujos postergados.

**Aplicación pendiente:**  
Crear módulo `config/constants.py` con definiciones claras:
```python
CONVERSION_A_MILLONES = 1000000
COD_ENTIDAD_DIPRES_DIP = 10201
COD_ENTIDAD_DIPRES_CGR = 5601
COD_ANALITICO_FIJO_1 = "04001000"
# ... etc
```

**Impacto:** Medio | **Esfuerzo:** Medio | **Riesgo:** Bajo

---

### M-006: Verificar y documentar dependencias de base de datos con librecias no validadas

**Categoría:** Reproducibilidad  
**Estado:** ⏸️ **POSTERGADA** — *Lote diferido*

**Descripción:**  
Bases de datos sin verificación (verified_db=false):
- **DCNIDCNA**: contiene BDATOS_SP, CODIGO_ENTIDAD_SP, EJEC_MUN (1–3 nodos)
- **DCV**: accede MONEDAS_MENSUAL (1 nodo)
- Rutas mezclan patrones:
  - Unix: `/sasdata/BCCH/GEM_DCNI/...`
  - Windows: `\\FILESERVER\...`

**Nodos afectados (4):**  
CodeTask-cbwaC9NShYE8mV6x, CodeTask-D6fqrxqReNOK5Xch, CodeTask-oLKJ5g7DvhYHuBME, Query-YHeDzXnzld6fOVfj

**Justificación:**  
Bases de datos sin verificación pueden no existir en ciertos entornos (DEV/TEST), causando fallos silenciosos o retardados en reproducibilidad. Crear matriz de dependencias que documente:
1. Libref requerido
2. Ruta esperada por entorno (DEV/PROD/STAGING)
3. Tablas requeridas y esquema
4. Scripts que lo usan

Agregar validaciones al inicio de notebooks para detectar ausencia tempranamente.

**Razón de postergación:**  
Los nodos afectados (especialmente CodeTask-D6fqrxqReNOK5Xch en AUTOEXEC) pertenecen a flujos que se migran en lotes posteriores o requieren validación previa con el usuario sobre disponibilidad de conexiones BD.

**Aplicación pendiente:**  
Crear `config/database_connections.yaml` con definiciones por entorno:
```yaml
databases:
  DCNIDCNA:
    entornos:
      dev: "server=dev-db; database=DCNIDCNA"
      prod: "server=prod-db; database=DCNIDCNA"
    tablas: [BDATOS_SP, CODIGO_ENTIDAD_SP, EJEC_MUN]
    verificado: false
    nota: "Requiere aprobación de acceso"
```

Implementar función de validación de conexiones en `utils/db_validation.py`.

**Impacto:** Medio | **Esfuerzo:** Medio | **Riesgo:** Medio

---

## Resumen de Aplicación

| ID | Título | Estado | Aplicación en Lote 1 |
|---|---|---|---|
| **M-001** | Consolidar rutas hardcodeadas | ✅ Aprobada | ✅ Implementada en `config/file_paths.py` |
| **M-005** | Centralizar parámetros globales | ✅ Aprobada | ✅ Implementada en `config/project_config.yaml` + `run_all.py` |
| **M-002** | Eliminar duplicación SQL | ⏸️ Postergada | Pendiente lote posterior |
| **M-003** | Consolidar CASE repetidas | ⏸️ Postergada | Pendiente lote posterior |
| **M-004** | Extraer magic numbers | ⏸️ Postergada | Pendiente lote posterior |
| **M-006** | Validar dependencias BD | ⏸️ Postergada | Pendiente lote posterior |

---

## Notas Operacionales

- **Mejoras aprobadas (M-001, M-005)** se aplicaron en los notebooks de este lote. Revisar los módulos `config/` para verificar valores por defecto.
- **Mejoras postergadas (M-002 a M-006)** se reevaluarán cuando los flujos afectados entren en migración. Guardar este documento como referencia para futuros lotes.
- Todas las mejoras aprobadas mejoran **reproducibilidad**, **mantenibilidad** y facilitan la operación del pipeline en Python.
