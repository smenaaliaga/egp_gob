# Lineaje de Datos – Proc_Salidas_Gob_REV_mig

## Descripción General

Este documento describe el flujo de datos de la migración SAS→Python del proyecto **Proc_Salidas_Gob_REV_mig**. Mapea las fuentes de datos, transformaciones y salidas por cada Process Flow, indicando el notebook que las contiene y el orden de ejecución.

---

## Flujos Cubiertos en Esta Entrega

Esta entrega cubre **3 Process Flows** traducidos a Python:

1. **AUTOEXEC** → `NB-01_autoexec.ipynb`
2. **Proceso Ejecución GC CGR** → `NB-02_proceso_ejecucion_gc_cgr.ipynb`
3. **Proceso Ejec GC DIPRES** → `NB-03_proceso_ejec_gc_dipres.ipynb`
4. **Salida CG coy** → `NB-04_salida_cg_coy.ipynb`

### Flujos Diferidos (Lotes Posteriores)

Los siguientes flujos se migrarán en lotes posteriores y **no están incluidos** en esta entrega:

- Salida CG Imputa
- Salida CNF trim
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

---

## Notebook 01: AUTOEXEC

**Archivo:** `output/NB-01_autoexec.ipynb`

**Propósito:** Inicialización de ambiente, configuración de librerías y cálculo de indicadores de moneda para períodos mensuales y trimestrales.

### Fuentes de Datos

| Fuente | Librería | Tabla | Descripción |
|--------|----------|-------|-------------|
| Base de datos de cambios | DCV | MONEDAS_MENSUAL | Tipos de cambio mensuales de monedas y UF |

### Transformaciones

| Paso | Nodo SAS | Descripción | Entrada | Salida |
|------|----------|-------------|---------|--------|
| 1 | CodeTask-XzOatjIuMbeLV29h | Set Libreria | — | Configuración de rutas y librerías |
| 2 | CodeTask-D6fqrxqReNOK5Xch | Monedas_Mensual | DCV.MONEDAS_MENSUAL | WORK.CIERRE_MES, WORK.CIERRE_TRIM, WORK.PROM_MES, WORK.PROM_MES_TODAS, WORK.PROM_TRIM |
| 3 | CodeTask-q5ZEbAg5C43nmYfy | Programa | (Dependencias previas) | Configuración final de programa |

### Salidas (WORK)

| Tabla | Descripción | Uso Posterior |
|-------|-------------|--------------|
| WORK.CIERRE_MES | Cierre mensual de tipos de cambio | Cálculos de variación mensual |
| WORK.CIERRE_TRIM | Cierre trimestral de tipos de cambio | Cálculos de variación trimestral |
| WORK.PROM_MES | Promedio mensual de tipos de cambio | Análisis de coyuntura |
| WORK.PROM_MES_TODAS | Promedio mensual de todas las monedas | Consolidación |
| WORK.PROM_TRIM | Promedio trimestral de tipos de cambio | Análisis de variación trimestral |

---

## Notebook 02: Proceso Ejecución GC CGR

**Archivo:** `output/NB-02_proceso_ejecucion_gc_cgr.ipynb`

**Propósito:** Validación y clasificación de ejecución presupuestaria del Gobierno General (CGR), reconciliación de estructuras contables, actualización de matrices de analíticos y gestión de transferencias consolidables.

### Fuentes de Datos

#### Bases de Datos Externas (GOBGENER)

| Librería | Tabla | Descripción | Registros Aprox. |
|----------|-------|-------------|------------------|
| GOBGENER | EJECUCION | Ejecución presupuestaria CGR por PACAPR | ~50k–100k |
| GOBGENER | ENTIDADES | Catálogo maestro de entidades, partidas, capítulos, programas | ~5k–10k |
| GOBGENER | CR18_T_SCN_1 | Matriz de clasificación de analíticos fijos (SCN) | ~2k–5k |
| GOBGENER | CR18_T_SCN_2 | Matriz de clasificación de analíticos variables (transacción SCN) | ~1k–3k |
| GOBGENER | CR18_APERTURA | Aperturas presupuestarias (PACAPR) | ~1k–2k |
| GOBGENER | CR18_ENTID_DIP | Entidades DIPRES para DIP | ~500–1k |
| GOBGENER | CR18_ENTID_DIP_Y | Entidades DIPRES por año | ~500–1k |
| GOBGENER | COFOG | Clasificación COFOG funcional | ~200–500 |
| GOBGENER | COFOG_T_SCN_2 | Mapa COFOG a transacción SCN | ~200–500 |
| GOBGENER | ANALIT_TCONS | Matriz de analíticos con tipo de transacción consolidable (TCONS) | ~500–1k |
| GOBGENER | EST_EXP_MM | Estructura de expansión mensual para TCONS MM | ~100–300 |
| GOBGENER | EST_EXP_MGG | Estructura de expansión GG (multiplos) | ~100–300 |
| GOBGENER | EST_EXP_MGCG | Estructura de expansión GG+CGR | ~100–300 |
| GOBGENER | EST_EXP_MIXTAS_M | Estructura de expansión mixta M (múltiples meses) | ~50–100 |
| GOBGENER | EST_MM | Estructura MM de muestra | ~50–100 |
| GOBGENER | EST_MIXTAS_M | Estructura MIXTAS_M de muestra | ~20–50 |

#### Tablas de Trabajo (WORK)

Generadas en pasos intermedios dentro del mismo flujo o de AUTOEXEC:

- WORK.CIERRE_MES, WORK.CIERRE_TRIM, WORK.PROM_MES (de AUTOEXEC)
- WORK.ANALIT_FIJO_CLAS, WORK.ANALIT_FIJO_CLAS_2, WORK.ANALIT_FIJO_FALTANTE (intermedias)
- WORK.ANALIT_VAR_CLAS, WORK.ANALIT_VAR_CLAS_2, ... WORK.ANALIT_VAR_CLAS_RESTO_F (clasificaciones variables)
- WORK.CRUCE_FIJO, WORK.CRUCE_PROP, WORK.CRUCE_VAR (cruces de validación)
- WORK.CHECK_* (múltiples tablas de verificación: ANALIT_FIJO, ANALIT_VAR, TCONS, COFOG, etc.)
- WORK.NUEVAS_ENTIDADES (entidades no catalogadas del período)
- WORK.EJEC_CGR (ejecución presupuestaria consolidada CGR)

### Transformaciones Principales

| Paso | Nodo SAS | Descripción | Entrada Principal | Salida Principal |
|------|----------|-------------|-------------------|-----------------|
| 1 | CodeTask-vRkhqURhrfdncIIr | Check Compara PACAPR | GOBGENER.EJECUCION, GOBGENER.ENTIDADES | WORK.COMPARA_PACAPR |
| 2 | CodeTask-eSSEltFJH17EEWGl | Check Compara C_ENTIDAD | GOBGENER.EJECUCION, GOBGENER.ENTIDADES | WORK.COMPARA_ENTIDAD |
| 3 | CodeTask-iE4gTB7hPMNsX4dR | Check Nvas Entidades | GOBGENER.EJECUCION, GOBGENER.ENTIDADES | WORK.CHECK_ENTIDADES |
| 4 | CodeTask-19o6EdegIblGxthd | Clasif Nvas Entidades | WORK.CHECK_ENTIDADES | GOBGENER.ENTIDADES (UPDATE), WORK.NUEVAS_ENTIDADES |
| 5 | CodeTask-SR2tNwn9ee5q4ldH | Check Analiticos Predef_mod | GOBGENER.CR18_T_SCN_1 + 8 tablas CRUCE_* | WORK.CRUCE_FIJO_MAX, WORK.CRUCE_FIJO_MAX_2 (propuestas) |
| 6 | CodeTask-imoWjgB9c7XBGB5q | Clasif Analiticos Predef_mod | WORK.CRUCE_FIJO_MAX + verificación | GOBGENER.CR18_T_SCN_1 (UPDATE), WORK.CHECK_ANALIT_REV |
| 7 | CodeTask-6FS3khd1yz37XIOH | Check Analiticos Var_mod | GOBGENER.CR18_T_SCN_2 + 8 CRUCE_PROP/VAR | WORK.CRUCE_VAR_MAX, WORK.CRUCE_VAR_MAX_2, ... (5 niveles) |
| 8 | CodeTask-Jtvr77EbawEqiCx3 | Clasif Analiticos Var_mod | WORK.CRUCE_VAR_MAX (importadas Excel) | GOBGENER.CR18_T_SCN_2 (UPDATE) |
| 9 | CodeTask-x5iMg8dNCjGmDI64 | Check Nvas TCons_mod | GOBGENER.ANALIT_TCONS + CRUCE_* | Exporta a Excel para clasificación manual |
| 10 | CodeTask-ESKX4AdeM3cTnf1w | Clasif Nvas TCons_mod | GOBGENER.ANALIT_TCONS (reimportada Excel) | GOBGENER.ANALIT_TCONS (UPDATE) |
| 11 | CodeTask-Wil6N97RHUIMSVfs | Check Est_Exp_MM TCons_mod | GOBGENER.EST_EXP_MM + ANALIT_TCONS | Exporta a Excel, reimporta, valida |
| 12 | CodeTask-kH5fNiMJvLnwyCUU | Check Est_Exp_M TCons_mod | GOBGENER.EST_EXP_MIXTAS_M | Exporta a Excel, reimporta, valida |
| 13 | CodeTask-1LH51NVFniO8SFVp | Check Est_MM TCons | GOBGENER.EST_MM | WORK.CHECK_EST_MM (verificación solo) |
| 14+ | (Continuación) | Validaciones COFOG, consolidación final | GOBGENER.COFOG + matrices | WORK.EJEC_CGR (salida final) |

### Salidas a Base de Datos (GOBGENER)

| Tabla | Descripción | Modo | Nota |
|-------|-------------|------|------|
| GOBGENER.ENTIDADES | Catálogo maestro (actualizado con nuevas) | UPDATE/INSERT | Anexa nuevas entidades detectadas |
| GOBGENER.CR18_T_SCN_1 | Matriz analíticos fijos SCN (actualizada) | UPDATE | Sincroniza propuestas clasificadas |
| GOBGENER.CR18_T_SCN_2 | Matriz analíticos variables SCN (actualizada) | UPDATE | Sincroniza propuestas clasificadas |
| GOBGENER.ANALIT_TCONS | Matriz TCONS (actualizada) | UPDATE | Sincroniza nuevas transferencias consolidables |
| GOBGENER.EST_EXP_MM, EST_EXP_MGG, EST_EXP_MGCG, EST_EXP_MIXTAS_M | Estructuras de expansión (actualizadas) | UPDATE | Anexan nuevas estructuras validadas |

### Salidas a Trabajo (WORK)

| Tabla | Descripción |
|-------|-------------|
| WORK.EJEC_CGR | Ejecución presupuestaria final consolidada para CGR (feed a flujos posteriores) |
| WORK.CHECK_ANALIT_FIJO, WORK.CHECK_ANALIT_VAR, WORK.CHECK_TCONS_* | Reportes de validación |
| WORK.CRUCE_FIJO_MAX, WORK.CRUCE_VAR_MAX (x5) | Propuestas máximas (candidatos a clasificar) |

---

## Notebook 03: Proceso Ejec GC DIPRES

**Archivo:** `output/NB-03_proceso_ejec_gc_dipres.ipynb`

**Propósito:** Validación y clasificación de ejecutiones presupuestarias anuales de DIPRES, asegurando imputación correcta de actividades, analíticos y tipos de transacción según diccionarios predefinidos.

### Fuentes de Datos

#### Bases de Datos Externas (GOBGENER)

| Librería | Tabla | Descripción |
|----------|-------|-------------|
| GOBGENER | EJEC_DIPRES | Ejecución presupuestaria DIPRES anual | 
| GOBGENER | ENTIDADES | Catálogo maestro de entidades |
| GOBGENER | CR18_T_SCN_1, CR18_T_SCN_2 | Matrices de clasificación SCN |
| GOBGENER | CR18_ENTID_DIP_Y, CR18_T_SCN_* | Entidades y transacciones por año |
| GOBGENER | ANALIT_TCONS | Matriz TCONS |
| GOBGENER | EST_EXP_MM, EST_EXP_MIXTAS_M | Estructuras de expansión |

#### Tablas de Trabajo (WORK)

Generadas en este flujo o heredadas de Proceso Ejecución GC CGR:

- WORK.ANALIT_FIJO_CLAS, WORK.ANALIT_VAR_CLAS* (clasificaciones)
- WORK.CRUCE_FIJO, WORK.CRUCE_PROP, WORK.CRUCE_VAR (cruces)
- WORK.CHECK_* (verificaciones)
- WORK.EJEC_DIP (ejecución DIPRES consolidada)
- WORK.EST_M, WORK.EST_MM (estructuras de muestra)
- WORK.TCONS_EST_DEF_M (matriz TCONS con estructuras definidas)

### Transformaciones

| Paso | Nodo SAS | Descripción | Entrada Principal | Salida Principal |
|------|----------|-------------|-------------------|-----------------|
| 1–10 | CodeTask-yXykqUZknliUd6Tv, ... | Importación DIPRES, validación analíticos, clasificación transacciones | GOBGENER.EJEC_DIPRES, matrices SCN | WORK.EJEC_DIP (consolidada) |

### Salidas

#### A Base de Datos (GOBGENER)

| Tabla | Descripción |
|-------|-------------|
| GOBGENER.ANALIT_TCONS | Actualizada con nuevas clasificaciones |
| GOBGENER.CR18_T_SCN_1, CR18_T_SCN_2 | Matrices SCN actualizadas con reglas DIPRES |
| GOBGENER.EST_EXP_MM, EST_EXP_MIXTAS_M | Estructuras de expansión actualizadas |

#### A Trabajo (WORK)

| Tabla | Descripción |
|-------|-------------|
| WORK.EJEC_DIP | Ejecución DIPRES final consolidada (feed a Salida CG coy) |
| WORK.CHECK_ANALIT_REV, WORK.CHECK_TCONS_* | Reportes de validación |

---

## Notebook 04: Salida CG coy

**Archivo:** `output/NB-04_salida_cg_coy.ipynb`

**Propósito:** Preparación y salida de indicadores de ejecución presupuestaria del gobierno para reportes de coyuntura económica, integrando datos de contabilidad pública (CGR) y presupuesto (DIPRES).

### Fuentes de Datos

#### Bases de Datos Externas (GOBGENER)

| Librería | Tabla | Descripción |
|----------|-------|-------------|
| GOBGENER | EJECUCION, EJEC_DIPRES | Ejecuciones CGR y DIPRES |
| GOBGENER | ENTIDADES | Catálogo de entidades |
| GOBGENER | CR18_APERTURA, CR18_ENTID_DIP, CR18_ENTID_DIP_Y | Aperturas y entidades por año |
| GOBGENER | CR18_T_SCN_1, CR18_T_SCN_2 | Matrices SCN |
| GOBGENER | EST_EXP_MIXTAS_M, EST_MIXTAS_M | Estructuras de expansión mixta |
| GOBGENER | IMPUT_GC_DIP, IMPUT_GC_DIP_APER | Imputaciones consolidadas |
| GOBGENER | MOLDE_T_SCN_2, T_SCN_2 | Moldes de transacción |

#### Tablas de Trabajo (WORK)

Generadas en flujos previos o dentro de este:

- WORK.EJEC_CGR (de Proceso Ejecución GC CGR)
- WORK.EJEC_DIP, WORK.EJEC_DIP_Y (de Proceso Ejec GC DIPRES)
- WORK.PROM_MES (de AUTOEXEC)
- WORK.CR18_APERTURA_PACAPR, WORK.CR18_APERTURA_PACAPR_V (aperturas validadas)
- WORK.EJECUCION_A, EJECUCION_B, EJECUCION_C, EJECUCION_D, EJECUCION_F, EJECUCION_G (desagregaciones por formato)
- WORK.EJECUCION_*_PRELIM, *_PRELIM_DIP, *_PRELIM_DIP_APER, *_PRELIM_DIP_APER_IMP (variantes con imputaciones)
- WORK.EJECUCION_CG, EJECUCION_CG_APER, EJECUCION_CG_DIP, EJECUCION_CG_DIP_APER, EJECUCION_CG_DIP_PREV (consolidaciones)
- WORK.RATIOS, WORK.AUX_RATIOS (indicadores de desempeño)
- WORK.TOTALES, WORK.TOTALES_INST (agregaciones institucionales)
- WORK.EJEC_*_MIXTAS_M, EJEC_MUESTRA_MIXTAS_M (variantes mixtas con muestra)

### Transformaciones Principales

| Paso | Nodo SAS | Descripción | Entrada Principal | Salida Principal |
|------|----------|-------------|-------------------|-----------------|
| 1–14 | CodeTask-RDZUBeSyggbaTi4d, ... CodeTask-86VdtiWQrF36JEkb | Construcción de formatos A–G, aplicación preliminar, imputación DIPRES, ajustes apertura, cálculo ratios | WORK.EJEC_CGR, WORK.EJEC_DIP | WORK.EJECUCION_CG_* (múltiples variantes), WORK.RATIOS, WORK.TOTALES |

### Salidas a Base de Datos (GOBGENER)

| Tabla | Descripción |
|-------|-------------|
| GOBGENER.IMPUT_GC_DIP | Matriz de imputaciones consolidadas |
| GOBGENER.IMPUT_GC_DIP_APER | Matriz de imputaciones por apertura |

### Salidas a Trabajo (WORK) – Tablas de Coyuntura

| Tabla | Descripción | Uso |
|-------|-------------|-----|
| WORK.EJECUCION_CG | Ejecución CG consolidada (feed a informes) |
| WORK.EJECUCION_CG_APER | Ejecución CG por apertura |
| WORK.EJECUCION_CG_CGR | Ejecución CG solo CGR |
| WORK.EJECUCION_CG_DIP | Ejecución CG solo DIPRES |
| WORK.EJECUCION_CG_DIP_PREV | Ejecución CG DIPRES con previsilización |
| WORK.RATIOS | Indicadores de desempeño (tasas, variaciones) |
| WORK.TOTALES | Agregados totales por periodo |
| WORK.TOTALES_INST | Totales por institución |

---

## Dependencias Entre Notebooks

```
NB-01 (AUTOEXEC)
  ↓
  ├─→ NB-02 (Proceso Ejecución GC CGR) ——→ WORK.EJEC_CGR
  │                                         GOBGENER.ENTIDADES (UPDATE)
  │                                         GOBGENER.CR18_T_SCN_1, CR18_T_SCN_2 (UPDATE)
  │                                         GOBGENER.ANALIT_TCONS (UPDATE)
  │
  ├─→ NB-03 (Proceso Ejec GC DIPRES) ——→ WORK.EJEC_DIP
  │      ↑                                 GOBGENER.* (UPDATE, matrices SCN)
  │      └──(lee matrices de NB-02)
  │
  └─→ NB-04 (Salida CG coy) ——→ WORK.EJECUCION_CG_*
         ↑                       WORK.RATIOS, WORK.TOTALES
         └──(lee WORK.EJEC_CGR + WORK.EJEC_DIP + WORK.PROM_MES)
```

---

## Parámetros Macros y Configuración

### Parámetros de Entrada (Sin Centralizar Aún)

Los siguientes parámetros se declaran en las celdas `parameters` de los notebooks pero **carecen de valor declarado en config centralizado** (M-005 pendiente):

| Parámetro | Descripción | Notebooks Afectados |
|-----------|-------------|-------------------|
| `Year` | Año fiscal de procesamiento | NB-02, NB-03, NB-04 |
| `Analista` | Código de analista responsable | NB-02, NB-03 |
| `Comp1` – `Comp7` | Computaciones parametrizadas (ej. códigos de comparación) | NB-02, NB-04 |
| `Mes`, `Mes_imp1`–`Mes_imp12` | Meses y meses de imputación | NB-04 |
| `Moneda` | Moneda de procesamiento (ej. UF, USD) | NB-01 |
| `PACAPR1`–`PACAPR7` | Aperturas presupuestarias parametrizadas | NB-02 |

**Acción:** Centralizar valores en `project_config.yaml` o scripts de inicialización compartidos antes de producción.

---

## Archivos de Datos Intermedios (Excel)

Varios nodos exportan/importan clasificaciones mediante Excel como puente de decisión manual:

| Nodo | Archivo | Paso | Contenido |
|------|---------|------|----------|
| CodeTask-6FS3khd1yz37XIOH | `CHECK_CRUCE_VAR_MAX.xlsx` | Exporta | Propuestas de clasificación de analíticos variables (5 niveles) |
| CodeTask-Jtvr77EbawEqiCx3 | `CHECK_CRUCE_VAR_MAX.xlsx` | Importa | Clasificaciones validadas manualmente (aplica a CR18_T_SCN_2) |
| CodeTask-x5iMg8dNCjGmDI64 | `CHECK_TCONS_NUEVAS.xlsx` | Exporta | Nuevas TCONS propuestas |
| CodeTask-ESKX4AdeM3cTnf1w | `CHECK_TCONS_NUEVAS.xlsx` | Importa | TCONS clasificadas manualmente (aplica a ANALIT_TCONS) |
| CodeTask-Wil6N97RHUIMSVfs | `CHECK_EST_EXP_MM_NUEVAS.xlsx` | Exporta/Importa | Ponderaciones (POND) de expansión MM |
| CodeTask-kH5fNiMJvLnwyCUU | `CHECK_EST_EXP_MIXTAS_M_NUEVAS.xlsx` | Exporta/Importa | Clasificación y ponderación mensual de expansión MIXTAS_M |

---

## Mejoras Aplicadas (M-001, M-005)

### M-001: Consolidar Rutas de Archivo (Aprobada)

**Aplicada en:**
- Notebooks hacen referencia a rutas parametrizadas (será implementado en capa de configuración)

**Impacto:** Mejora portabilidad entre entornos.

### M-005: Centralizar Macro Variables de Usuario (Aprobada)

**Aplicada en:**
- Celdas `parameters` de cada notebook declaran variables pero sin valores centralizados

**Pendiente:** Completar `project_config.yaml` con valores por defecto para Year, Analista, Comp1–7.

---

## Notas Operacionales

1. **Manejo de Datos WORK:** Las tablas WORK (temporales de sesión) se regeneran en cada ejecución. Para auditoría, exportar GOBGENER y tablas críticas a CSV/Parquet antes de cerrar sesión.

2. **Ciclo Manual Excel:** Nodos con exportación Excel (pasos 7–8 en NB-02) requieren **intervención manual** antes de continuar. Documentar cambios en log de clasificaciones.

3. **Dependencia de Librerías:**
   - **DCV** (tipos de cambio): Verificar disponibilidad en cada entorno antes de correr NB-01.
   - **GOBGENER**: Librería principal; debe existir y estar accesible con permisos de lectura/escritura para UPDATE.

4. **Orden de Ejecución Estricto:** Ejecutar siempre en orden: NB-01 → NB-02 → NB-03 → NB-04. NB-02 y NB-03 pueden ejecutarse en paralelo si comparten sesión WORK, pero NB-04 requiere salidas de ambas.

5. **Supuestos Pendientes:**
   - Placement `ambiguous` en 5 nodos (CodeTask-D6fqrxqReNOK5Xch, etc.) → resolver en entrevista B4b si son bases de datos o archivos.
   - Macro variables sin valor → asignar en config antes de producción.

---

## Matriz de Dependencias Cruzadas (Referencias Comunes)

| Tabla | Generada en | Consumida en | Frecuencia |
|-------|----------|------------|-----------|
| WORK.CIERRE_MES, WORK.PROM_MES | NB-01 | NB-04 | Cálculo de promedios de coyuntura |
| WORK.EJEC_CGR | NB-02 | NB-04 | Ejecución CGR final |
| WORK.EJEC_DIP | NB-03 | NB-04 | Ejecución DIPRES final |
| GOBGENER.ENTIDADES | NB-02 (UPDATE) | NB-02, NB-03, NB-04 (READ) | Validación de nuevas entidades |
| GOBGENER.CR18_T_SCN_1, CR18_T_SCN_2 | NB-02, NB-03 (UPDATE) | NB-02, NB-03, NB-04 (READ) | Clasificación de analíticos |
| GOBGENER.ANALIT_TCONS | NB-02, NB-03 (UPDATE) | NB-02, NB-03, NB-04 (READ) | Matriz de TCONS |
