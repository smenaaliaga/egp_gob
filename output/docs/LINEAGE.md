# Lineaje de Datos — Proc_Salidas_Gob_REV_mig

## Flujos y Estructura General

Este documento describe el flujo de datos (lineage) para la migración **Proc_Salidas_Gob_REV_mig**, que consta de **16 flujos migrables de 17 totales**, organizados en **6 notebooks + 1 utilidad** (run_all.py). Los datos circulan a través de **178 nodos** que transforman fuentes externas (BD GOBGENER, DCV) en salidas de análisis presupuestario para gobierno.

La migración abarca cuatro flujos principales de procesamiento (AUTOEXEC, Proceso Ejecución GC CGR, Proceso Ejec GC DIPRES, Salida CG coy) y 12 flujos de salida (análisis, reportes, indicadores). **Flujos diferidos** para lote posterior: AUTOEXEC, Salida CG coy, Salida CG Imputa, Salida CNF trim, Salidas CNF anual y COFOG, Salida_anual para componente especif, Proceso Sit_Patri_MUN, Proceso Ejecución Municipal CGR, Traspasos_info, Salida_CF_GC, Salida_DCNA, Salidas_Cuenta_Produc_AAPP, Salidas_Cuenta_Produc_AAPP_2, Indicadores municipales — **14 flujos no migrados en esta entrega**.

---

## Flujos Migrables en Esta Entrega

### 1. AUTOEXEC → `NB-01_autoexec.ipynb`

**Propósito:** Inicialización de referencias a librerías, carga de tipos de cambio mensuales y cálculo de consolidados mensuales/trimestrales.

| Aspecto | Detalle |
|--------|--------|
| **Nodos** | 3 nodos (CodeTask-XzOatjIuMbeLV29h, CodeTask-D6fqrxqReNOK5Xch, CodeTask-q5ZEbAg5C43nmYfy) |
| **Tipos** | OTHER (2), PROC_SQL (1) |
| **Entrada** | DCV.MONEDAS_MENSUAL (tabla BD: tipos de cambio) |
| **Salida** | WORK.CIERRE_MES, WORK.CIERRE_TRIM, WORK.PROM_MES, WORK.PROM_MES_TODAS, WORK.PROM_TRIM (5 tablas temporales) |
| **Dependencias** | Ninguna (flujo raíz) |
| **Notebook** | NB-01_autoexec.ipynb |
| **Estrategia** | Python (utility para LIBNAME) + pandas (carga y consolidación de promedios) |

**Descripción del flujo:**
- Establece referencias a librerías SAS (GOBGENER, DCV).
- Lee MONEDAS_MENSUAL (divisa, fecha, valor).
- Calcula promedios mensuales (PROM_MES, PROM_MES_TODAS) y trimestrales (PROM_TRIM) por moneda.
- Genera cierres de mes y trimestre para análisis de variación de tipos de cambio.

**Salidas utilizadas por:**
- Proceso Ejecución GC CGR (PROM_MES).
- Salida CG coy (PROM_MES, CIERRE_MES, CIERRE_TRIM).

---

### 2. Proceso Ejecución GC CGR → `NB-02_proceso_ejecucion_gc_cgr.ipynb`

**Propósito:** Validación, clasificación y consolidación de ejecución presupuestaria desde Contraloría General (CGR), detección de cambios organizacionales, imputación de analíticos contables y matrices de estructura.

| Aspecto | Detalle |
|--------|--------|
| **Nodos** | 31 nodos (combinación de PROC_SQL, DATA_STEP, IMPORT, PROC_OTHER, QUERY) |
| **Entrada (BD)** | GOBGENER: ANALIT_TCONS, COFOG, CR18_APERTURA, CR18_ENTID_DIP, CR18_ENTID_DIP_Y, CR18_T_SCN_1, CR18_T_SCN_2, EJECUCION, ENTIDADES, EST_EXP_*, EST_MIXTAS_M, EST_MM, COFOG_T_SCN_2 (20 tablas maestras) |
| **Entrada (WORK)** | ~30 tablas intermedias de control y clasificación |
| **Salida (BD)** | GOBGENER: ANALIT_TCONS, CR18_APERTURA, CR18_ENTID_DIP, CR18_ENTID_DIP_Y, CR18_T_SCN_1, CR18_T_SCN_2, ENTIDADES, EST_EXP_MGCG, EST_EXP_MGG, EST_EXP_MIXTAS_M, EST_EXP_MM (11 tablas actualizadas) |
| **Salida (WORK)** | ~50 tablas de análisis, checks, comparaciones y datos procesados |
| **Dependencias** | AUTOEXEC (PROM_MES) |
| **Notebook** | NB-02_proceso_ejecucion_gc_cgr.ipynb |
| **Estrategia** | SQL pushdown + pandas (para checks de duplicados, consolidación) |

**Detalle del flujo de datos:**

**Fase 1 — Detección de cambios organizacionales (nodos 1-3):**
- CodeTask-vRkhqURhrfdncIIr: EJECUCION ⨝ ENTIDADES → WORK.COMPARA_PACAPR (cambios en partida/capítulo/programa por año).
- CodeTask-eSSEltFJH17EEWGl: EJECUCION ⨝ ENTIDADES → WORK.COMPARA_ENTIDAD (cambios en estructura por entidad).
- CodeTask-iE4gTB7hPMNsX4dR: Detección de nuevas entidades sin clasificar (anti-join).

**Fase 2 — Clasificación de nuevas entidades (nodo 3b):**
- CodeTask-19o6EdegIblGxthd: WORK.NUEVAS_ENTIDADES → GOBGENER.ENTIDADES (append FORCE).

**Fase 3a — Analíticos fijos (nodos 4a-4b):**
- CodeTask-SR2tNwn9ee5q4ldH: CR18_T_SCN_1 ⨝ histórico → WORK.ANALIT_FIJO_CLAS (propone clasificaciones por frecuencia, caso cuenta 07-ítem 02 autocompletado).
- CodeTask-imoWjgB9c7XBGB5q: Aplica ANALIT_FIJO_CLAS a CR18_T_SCN_1, marca "REV" pendientes, actualiza GOBGENER.CR18_T_SCN_1, genera checks de duplicados.

**Fase 3b — Analíticos variables (nodos 5a-5b):**
- CodeTask-6FS3khd1yz37XIOH: Detecta analíticos sin clasificación, propone heredando el más frecuente (5 niveles de clave: GORE → resto entidades), exporta a Excel.
- CodeTask-Jtvr77EbawEqiCx3: Importa clasificación desde Excel, normaliza, anexa a GOBGENER (elimina duplicados).

**Fase 4 — Transacciones consolidables (TCONS) (nodos 6a-6b):**
- CodeTask-x5iMg8dNCjGmDI64: Detecta transferencias del año sin clasificación (Consolidable/No Consolidable), exporta a Excel.
- CodeTask-ESKX4AdeM3cTnf1w: Importa clasificación TCONS, normaliza M_MUESTRA, reemplaza en GOBGENER.ANALIT_TCONS.

**Fase 5 — Estructuras de expansión (nodos 7a-7f):**
- CodeTask-Wil6N97RHUIMSVfs: Detecta analíticos MM sin estructura mensual (EST_EXP_MM), propone expansión, valida ponderaciones ∑=1/mes.
- CodeTask-kH5fNiMJvLnwyCUU: Detecta MIXTAS_M sin estructura (EST_EXP_MIXTAS_M), propone expansión, valida y anexa.
- CodeTask-1LH51NVFniO8SFVp: Verifica consistencia: TCONS-MM debe existir en EST_EXP_MM.
- CodeTask-bYsFTxJS2Uy6FqcG: Verifica consistencia: TCONS-MIXTAS_M debe existir en EST_MIXTAS_M.
- CodeTask-QeChUmtaSsJfkhiI: Detecta MGCG sin estructura, propone usando ítem '03' como template, permite revisión en Excel.
- CodeTask-HBcKDsWhhhzfcrxa: Detecta MGG sin estructura, propone y anexa EST_EXP_MGG.

**Fase 6 — Validaciones finales y COFOG (nodos 9-10):**
- CodeTask-EKp3vGrePAlPMEBt: Entidades sin actividad COFOG del año.
- CodeTask-Ubk9S5YsiZMvmuUO: Anexa clasificaciones COFOG imputadas.
- CodeTask-kzhY4l9Rfund2KoE: Detección de transacciones cuentas 24/33 en regiones sin COFOG.

**Salidas críticas para siguiente flujo:**
- GOBGENER.ANALIT_TCONS, GOBGENER.CR18_T_SCN_1, GOBGENER.CR18_T_SCN_2, GOBGENER.ENTIDADES (maestros actualizados).
- WORK.ANALIT_FIJO_CLAS, WORK.ANALIT_VAR_CLAS (clasificaciones utilizadas por DIPRES).

---

### 3. Proceso Ejec GC DIPRES → `NB-03_proceso_ejec_gc_dipres.ipynb`

**Propósito:** Validación y clasificación de ejecución presupuestaria DIPRES (Dirección de Presupuestos), aplicando las clasificaciones de CGR e imputando faltantes.

| Aspecto | Detalle |
|--------|--------|
| **Nodos** | 10 nodos (IMPORT, PROC_SQL) |
| **Entrada (BD)** | GOBGENER: ANALIT_TCONS, CR18_ENTID_DIP_Y, CR18_T_SCN_1, CR18_T_SCN_2, EJEC_DIPRES, ENTIDADES, EST_EXP_MIXTAS_M, EST_EXP_MM (8 maestros) |
| **Entrada (WORK — de Proceso CGR)** | WORK.ANALIT_*_CLAS, WORK.ANALIT_*_CLAS_*, WORK.ANALIT_*_FALTANTE*, WORK.CHECK_* (20+ tablas de clasificación y validación) |
| **Salida (BD)** | GOBGENER: ANALIT_TCONS, CR18_ENTID_DIP_Y, CR18_T_SCN_1, CR18_T_SCN_2, EST_EXP_MIXTAS_M, EST_EXP_MM (6 maestros actualizados con variante DIPRES) |
| **Salida (WORK)** | WORK.EJEC_DIP, WORK.TCONS_EST_DEF_M, ~40 tablas de transacciones clasificadas por tipo y dimensión |
| **Dependencias** | Proceso Ejecución GC CGR (maestros actualizados y clasificaciones) |
| **Notebook** | NB-03_proceso_ejec_gc_dipres.ipynb |
| **Estrategia** | SQL pushdown + pandas (joins masivos de clasificación) |

**Detalle del flujo:**
- Lee EJEC_DIPRES (ejecución presupuestaria de DIPRES).
- Clasifica entidades, actividades, analíticos usando las tablas de clasificación generadas por Proceso CGR.
- Imputa actividades y analíticos faltantes aplicando reglas de negocio (búsqueda por clave compuesta con fallback).
- Genera WORK.EJEC_DIP como consolidado de ejecución DIPRES clasificada.
- Produce matrices de estructura de exposición (EST_EXP_*) con variante DIPRES.

**Salidas utilizadas por:**
- Salida CG coy (EJEC_DIP, transacciones clasificadas).

---

### 4. Salida CG coy → `NB-04_salida_cg_coy.ipynb`

**Propósito:** Generación de indicadores de consumo de gobierno (coyuntura) a partir de datos de ejecución presupuestaria (CGR + DIPRES), con redistribución de transacciones mixtas y múltiples salidas agregadas.

| Aspecto | Detalle |
|--------|--------|
| **Nodos** | 14 nodos (PROC_SQL) |
| **Entrada (BD)** | GOBGENER: ANALIT_TCONS, CR18_APERTURA, CR18_ENTID_DIP, CR18_ENTID_DIP_Y, CR18_T_SCN_1, CR18_T_SCN_2, EJECUCION, EJEC_DIPRES, ENTIDADES, EST_EXP_MIXTAS_M, EST_MIXTAS_M, IMPUT_GC_DIP, IMPUT_GC_DIP_APER, MOLDE_T_SCN_2, T_SCN_2 (15 maestros) |
| **Entrada (WORK — de CGR y DIPRES)** | WORK.EJEC_DIP, WORK.EJEC_DIP_Y, WORK.EJEC_EXP_MIXTAS_M_DIP, WORK.EJEC_EXP_MIXTAS_M_DIP_IMP, WORK.PROM_MES, WORK.RATIOS, ~110 tablas de transacciones por tipo (EJECUCION_A, EJECUCION_B, ..., EJECUCION_G) |
| **Salida (BD)** | GOBGENER: IMPUT_GC_DIP, IMPUT_GC_DIP_APER (2 maestros de imputaciones) |
| **Salida (WORK)** | WORK.EJECUCION_CG, WORK.EJECUCION_CG_APER, WORK.EJECUCION_CG_CGR, WORK.EJECUCION_CG_DIP (consolid.), WORK.EJECUCION_CG_DIP_IMPUTACIONES, WORK.RATIOS, WORK.TOTALES, WORK.TOTALES_INST (indicadores finales) |
| **Dependencias** | Proceso Ejecución GC CGR, Proceso Ejec GC DIPRES |
| **Notebook** | NB-04_salida_cg_coy.ipynb |
| **Estrategia** | SQL pushdown (agregaciones masivas por dimensión) |

**Detalle del flujo:**
- Consolida ejecuciones CGR y DIPRES a nivel presupuestario completo (A, B, C, D, F, G — clasificación de gasto).
- Distribuye transacciones mixtas (MIXTAS_M) entre tipos de ejecución según estructura de ponderación (EST_EXP_MIXTAS_M).
- Calcula ratios de cobertura y variación respecto a año anterior (WORK.RATIOS, WORK.PROM_MES).
- Genera indicadores agregados por institución (TOTALES_INST) y consolidado nacional (TOTALES).
- Materializa salidas en GOBGENER.IMPUT_GC_DIP y GOBGENER.IMPUT_GC_DIP_APER para exportación a reportes.

**Salidas finales (outputs de esta entrega):**
- WORK.EJECUCION_CG_CGR (ejecución consolidada CGR + imputaciones).
- WORK.EJECUCION_CG_DIP (ejecución consolidada DIPRES + imputaciones).
- WORK.RATIOS (indicadores de variación y cobertura).
- WORK.TOTALES, WORK.TOTALES_INST (agregados para reporting).

---

## Flujos Diferidos (Próximos Lotes)

Los siguientes 14 flujos **no se migran en esta entrega** pero están listados para completitud:

1. **AUTOEXEC** (re-aparece): Diferido por validación pendiente de dependencias laterales.
2. **Salida CG coy**: Diferida (validar orden respecto a Salida CG Imputa).
3. **Salida CG Imputa**: Imputaciones de gobierno consolidado.
4. **Salida CNF trim**: Análisis trimestral de resultados no financieros.
5. **Salidas CNF anual y COFOG**: Consolidado anual y clasificación COFOG.
6. **Salida_anual para componente especif**: Análisis específico por componente.
7. **Proceso Sit_Patri_MUN**: Situación patrimonial municipal.
8. **Proceso Ejecución Municipal CGR**: Ejecución a nivel municipal.
9. **Traspasos_info**: Información de traspasos entre entidades.
10. **Salida_CF_GC**: Análisis de flujo de caja.
11. **Salida_DCNA**: Salida para integración DCNA.
12. **Salidas_Cuenta_Produc_AAPP**: Cuenta de producción sector AAPP.
13. **Salidas_Cuenta_Produc_AAPP_2**: Variante adicional.
14. **Indicadores municipales**: Indicadores agregados por municipio.

Estos flujos **dependen de maestros y clasificaciones** generadas en esta entrega pero requieren validación de orden de ejecución y esquemas de salida.

---

## Tablas Críticas de Lineage

### Maestros (BD GOBGENER)

| Tabla | Fuente | Creada/Actualizada | Consumida Por | Descripción |
|-------|--------|------------------|---------------|-------------|
| ENTIDADES | Entrada + Proceso CGR (nodo 3b) | Proceso CGR | Todos | Catálogo de entidades presupuestarias por año |
| EJECUCION | Entrada CGR | Proceso CGR | Salida CG coy | Ejecución presupuestaria CGR |
| EJEC_DIPRES | Entrada DIPRES | Proceso DIPRES | Proceso DIPRES, Salida CG coy | Ejecucion presupuestaria DIPRES |
| ANALIT_TCONS | Entrada + Proceso CGR (nodo 6b) | Proceso CGR, DIPRES | DIPRES, Salida CG coy | Clasificación de transacciones consolidables |
| CR18_T_SCN_1 | Entrada + Proceso CGR (nodo 4b) | Proceso CGR | DIPRES | Escenarios 1 de clasificación (PACAPR, analíticos fijos) |
| CR18_T_SCN_2 | Entrada + Proceso CGR (nodo 6b) | Proceso CGR | DIPRES | Escenarios 2 de clasificación (TCONS) |
| EST_EXP_MM | Entrada + Proceso CGR (nodo 7a) | Proceso CGR | DIPRES, Salida CG coy | Estructura de expansión mensual para MM |
| EST_EXP_MIXTAS_M | Entrada + Proceso CGR (nodo 7b) | Proceso CGR | DIPRES, Salida CG coy | Estructura de expansión para MIXTAS_M |
| EST_EXP_MGCG, EST_EXP_MGG | Entrada + Proceso CGR (nodos 7e-7f) | Proceso CGR | DIPRES | Estructuras de exposición por tipo (MGCG, MGG) |
| COFOG, COFOG_T_SCN_2 | Entrada + Proceso CGR | Proceso CGR | Externos (clasificación funcional) | Clasificación de actividades por COFOG |
| CR18_ENTID_DIP, CR18_ENTID_DIP_Y | Entrada + Proceso CGR | Proceso CGR | Salida CG coy | Entidades DIPRES y variantes anuales |
| CR18_APERTURA | Entrada + Proceso CGR | Proceso CGR | Salida CG coy | Apertura de presupuesto (nivel de detalle) |
| IMPUT_GC_DIP, IMPUT_GC_DIP_APER | Salida CG coy (nodos) | Salida CG coy | Exports/Reporting | Imputaciones de gobierno consolidado |

### Tablas Temporales (WORK)

| Tabla | Origen | Consumida Por | Descripción |
|-------|--------|---------------|-------------|
| CIERRE_MES, CIERRE_TRIM, PROM_MES*, PROM_TRIM | AUTOEXEC | Proceso CGR, Salida CG coy | Promedios de tipos de cambio |
| COMPARA_PACAPR, COMPARA_ENTIDAD | Proceso CGR (nodos 1-2) | Interno (validación) | Comparativas de cambios organizacionales |
| NUEVAS_ENTIDADES | Proceso CGR (nodo 3a) | Proceso CGR (nodo 3b) | Entidades nuevas detectadas |
| ANALIT_FIJO_CLAS, ANALIT_FIJO_CLAS_2 | Proceso CGR (nodo 4a) | Proceso CGR (nodo 4b), DIPRES | Clasificación propuesta de analíticos fijos |
| ANALIT_VAR_CLAS, ANALIT_VAR_CLAS_2-5 | Proceso CGR (nodo 5a) | Proceso CGR (nodo 5b), DIPRES | Clasificación propuesta de analíticos variables (con claves fallback) |
| ANALIT_FALTANTE, ANALIT_FALTANTE_D | Proceso CGR, DIPRES | Validación de faltantes | Analíticos sin clasificación tras revisión manual |
| CHECK_* (50+) | Proceso CGR, DIPRES | Auditoría y control de calidad | Tablas de control: duplicados, faltantes, inconsistencias |
| EJECUCION_A, EJECUCION_B, ..., EJECUCION_G | Proceso DIPRES | Salida CG coy | Transacciones clasificadas por tipo de gasto (7 categorías) |
| EJEC_DIP, EJEC_DIP_Y | Proceso DIPRES | Salida CG coy | Ejecución DIPRES consolidada y por año |
| EJEC_EXP_MIXTAS_M_DIP, EJEC_EXP_MIXTAS_M_DIP_IMP | Proceso DIPRES, Salida CG coy | Salida CG coy | Transacciones MIXTAS distribuidas e imputadas |
| EJECUCION_CG, EJECUCION_CG_CGR, EJECUCION_CG_DIP | Salida CG coy | Exportación | Consolidados de gobierno CGR/DIPRES |
| RATIOS, TOTALES, TOTALES_INST | Salida CG coy | Exportación/Reporting | Indicadores y agregados finales |

---

## Parámetros de Ejecución (Macros SAS → Parámetros Python)

Los siguientes parámetros se parametrizan en los notebooks (celda `parameters`):

| Parámetro | Tipo | Utilizado Por | Rango/Observación |
|-----------|------|---------------|------------------|
| `Year` | INT | Proceso CGR, DIPRES, Salida CG coy | Año de análisis (ej. 2023); filtro clave |
| `Mes` | INT | Proceso CGR (niveles varios) | Mes específico o agregado (1-12) |
| `Analista` | STR | Proceso CGR (nodos 5a, 6a, 7a-7f) | Nombre de responsable de revisión manual |
| `Comp1-7` | STR | Proceso DIPRES, Salida CG coy | Componentes de agregación de gasto |
| `Mes_imp1-12` | FLOAT | Proceso DIPRES | Factores de imputación por mes |
| `Moneda` | STR | AUTOEXEC | Código de moneda (ej. USD, CLP); filtro de MONEDAS_MENSUAL |
| `PACAPR1-7` | STR | Proceso CGR | Códigos de partida/capítulo/programa a procesar |

**Nota:** Parámetros sin valor declarado en `project_config.yaml` quedan como `None` en la celda `parameters` — el usuario debe completarlos antes de ejecutar o ingresarlos en entrevista B4.

---

## Dependencias Entre Notebooks

```
NB-01_autoexec
    ↓ (PROM_MES, CIERRE_MES, CIERRE_TRIM)
NB-02_proceso_ejecucion_gc_cgr
    ↓ (ANALIT_*_CLAS, ENTIDADES, CR18_T_SCN_1, CR18_T_SCN_2, EST_EXP_*)
NB-03_proceso_ejec_gc_dipres
    ↓ (EJEC_DIP, EJECUCION_A-G, EST_EXP_*)
NB-04_salida_cg_coy
    ↓ (RATIOS, TOTALES, TOTALES_INST, EJECUCION_CG_*)
[Exportación a archivos/BD para reporting]
```

**Ejecutar en orden:** NB-01 → NB-02 → NB-03 → NB-04 (orden secuencial obligatorio).

---

## Puntos de Integración Externa

### Entrada (Fuentes)

- **BD GOBGENER** (SQL Server / Oracle): Maestros, ejecuciones, clasificaciones históricas.
- **BD DCV**: Tipos de cambio mensuales.
- **Archivos Excel** (durante ejecución manual): Clasificaciones propuestas para analíticos variables (nodos 5a, 6a, 7a-7f) — requieren validación y firma de Analista.

### Salida (Consumidores)

- **GOBGENER.IMPUT_GC_DIP, IMPUT_GC_DIP_APER**: Tablas finales persistidas para reportes de coyuntura.
- **WORK.RATIOS, TOTALES, TOTALES_INST**: Salidas para dashboards/análisis posterior.
- **Logs y checksums**: Validación de integridad de transformaciones.

---

## Notas de Validación y Control de Calidad

1. **Librerías SAS → Python:**
   - GOBGENER, DCV, WORK (BD y sesión de notebook).
   - Verificar permisos de acceso y esquema antes de ejecutar.

2. **Excel Bridge (Nodos 5a-7f):**
   - Archivos generados en `output/tmp/` para revisión manual.
   - Usuario debe firmar y volver a ingresar en siguiente nodo.
   - Sin ingreso manual, tablas quedan con estado "PENDIENTE_REVISION".

3. **Supuestos Críticos:**
   - MONEDAS_MENSUAL existe y tiene datos del año de análisis.
   - ENTIDADES maestro incluye todas las combinaciones PACAPR históricas.
   - Clasificaciones de analíticos fijos/variables son acumulativas (no se sobrescriben).
   - Estructura de expansión (EST_EXP_MM, EST_EXP_MIXTAS_M) suma 1.0 por grupo.

4. **Tablas Excluidas (Query nodes ignorados):**
   - Query-7WLH8bv335ANj5w9, Query-9hK9UXmLqOXfHIKS, Query-fI94dLNL1vAYjQn4: No traducidas en esta entrega.
