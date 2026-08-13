# Lineaje de Datos

## Estructura General

Este documento describe el flujo de datos desde las fuentes hasta los productos finales para cada Process Flow migrado en el lote actual. El proyecto **Proc_Salidas_Gob_REV_mig-2** incluye **18 flujos migrables** que procesan información presupuestaria y contable del Gobierno General de Chile, alimentando reportes de Cuentas Nacionales, análisis de coyuntura fiscal y validaciones de estructuras analíticas.

La arquitectura sigue un patrón de **enriquecimiento progresivo**: datos brutos de fuentes externas (librerías GOBGENER, DCV) se transforman en WORK (tablas de sesión), se validan y clasifican, y finalmente se consolidan en productos de negocio (tablas GOBGENER de salida y derivados para reporte).

---

## 1. AUTOEXEC

**Notebook:** `NB-01_autoexec.ipynb`

**Propósito:** Inicialización de librerías, configuración global y cálculo de agregaciones de monedas para análisis de variación de divisas.

### Fuentes de Entrada
- **DCV.MONEDAS_MENSUAL** — Tabla externa de tipos de cambio diarios por moneda

### Nodos y Transformaciones
1. **CodeTask-XzOatjIuMbeLV29h** (Set Libreria) — Configuración de librerías y rutas
2. **CodeTask-D6fqrxqReNOK5Xch** (Monedas_Mensual) — Agregación de tipos de cambio diarios → cierre y promedio mensual/trimestral
3. **CodeTask-q5ZEbAg5C43nmYfy** (Programa) — Inicialización de variables y estructuras globales

### Productos de Salida
- **WORK.CIERRE_MES** — Tipo de cambio cierre por mes
- **WORK.CIERRE_TRIM** — Tipo de cambio cierre por trimestre
- **WORK.PROM_MES** — Tipo de cambio promedio por mes
- **WORK.PROM_MES_TODAS** — Promedio de todas las monedas por mes
- **WORK.PROM_TRIM** — Tipo de cambio promedio por trimestre

### Dependencias Externas
- Librería **DCV** (fuente de datos de divisas)
- Librería **GOBGENER** (repositorio de salidas)

---

## 2. Proceso Ejecución GC CGR

**Notebook:** `NB-02_proceso_ejecucion_gc_cgr.ipynb`

**Propósito:** Validación y clasificación de ejecuciones presupuestarias desde datos de Contraloría (CGR), con énfasis en comparación de cambios de entidades, enriquecimiento de matrices analíticas y validación de estructuras consolidables.

### Fuentes de Entrada
- **GOBGENER.EJECUCION** — Ejecución presupuestaria base de CGR
- **GOBGENER.ENTIDADES** — Diccionario de entidades del sector público
- **GOBGENER.COFOG** — Clasificación de funciones de gobierno
- **GOBGENER.CR18_APERTURA**, **GOBGENER.CR18_ENTID_DIP**, **GOBGENER.CR18_ENTID_DIP_Y**, **GOBGENER.CR18_T_SCN_1**, **GOBGENER.CR18_T_SCN_2** — Mapeos de clasificación presupuestaria
- **GOBGENER.EST_EXP_MGCG**, **GOBGENER.EST_EXP_MGG**, **GOBGENER.EST_EXP_MIXTAS_M**, **GOBGENER.EST_EXP_MM** — Estructuras de expansión de muestra
- **GOBGENER.EST_MIXTAS_M**, **GOBGENER.EST_MM** — Ponderadores de muestra
- **GOBGENER.ANALIT_TCONS** — Matriz de analiticos consolidables

### Nodos y Transformaciones
1. **CodeTask-vRkhqURhrfdncIIr** (1-Check Compara PACAPR) — Comparación de cambios en PACAPR (partida/capítulo/articulo)
2. **CodeTask-eSSEltFJH17EEWGl** (2-Check Compara C_ENTIDAD) — Comparación de cambios en códigos de entidad
3. **CodeTask-iE4gTB7hPMNsX4dR** a **CodeTask-R9vRh7beA6yqV7xx** (31 nodos) — Cruce de ejecución con analiticos (fijos y variables), validación de transacciones, detección de cambios de nomenclatura, cálculo de propuestas de clasificación automática, verificación de coherencia COFOG-analítico

### Productos de Salida
- **GOBGENER.ANALIT_TCONS** — Matriz validada de analiticos consolidables (reescritura)
- **GOBGENER.COFOG**, **GOBGENER.CR18_*** (tablas de clasificación) — Mapeos actualizados
- **GOBGENER.ENTIDADES** — Diccionario de entidades actualizado
- **GOBGENER.EST_EXP_*** — Estructuras de expansión validadas
- **WORK.ANALIT_*** — Matrices intermedias de analiticos (fijos, variables, por entidad)
- **WORK.CHECK_*** — Tablas de validación (46 variantes: TCONS, ANALIT, COFOG, TRANSVAR, MIXTAS, EST_EXP, etc.)
- **WORK.COMPARA_*** — Comparaciones de cambios (CAPITULO, PARTIDA, PROGRAMA, PACAPR, ENTIDAD)
- **WORK.CRUCE_*** — Cruces de ejecución con analiticos

### Dependencias Externas
- Librería **GOBGENER** (múltiples tablas de referencia y salida)
- Parámetro macro **&Year** (año de procesamiento)

---

## 3. Proceso Ejec GC DIPRES

**Notebook:** `NB-03_proceso_ejec_gc_dipres.ipynb`

**Propósito:** Validación y clasificación paralela de ejecuciones presupuestarias desde datos DIPRES, aplicando la misma lógica de analiticos que CGR pero sobre estructura diferenciada de entidades y niveles de análisis.

### Fuentes de Entrada
- **GOBGENER.EJEC_DIPRES** — Ejecución presupuestaria DIPRES
- **GOBGENER.ENTIDADES** — Diccionario de entidades
- **GOBGENER.CR18_ENTID_DIP_Y**, **GOBGENER.CR18_T_SCN_1**, **GOBGENER.CR18_T_SCN_2** — Mapeos de clasificación específicos para DIPRES
- **GOBGENER.ANALIT_TCONS** — Matriz de analiticos consolidables
- **GOBGENER.EST_EXP_MIXTAS_M**, **GOBGENER.EST_EXP_MM** — Estructuras de expansión
- **WORK.ANALIT_*_D** — Matrices intermedias de CGR (entrada para DIPRES)
- **WORK.CRUCE_*** — Cruces previos de validación

### Nodos y Transformaciones
1. **CodeTask-yXykqUZknliUd6Tv** a **CodeTask-hiQbCN96JdfFBZKx** (10 nodos) — Importación de datos DIPRES, validación de consistencia con diccionarios, clasificación de analiticos, cálculo de propuestas automáticas, validación de transacciones según estructura DIPRES

### Productos de Salida
- **GOBGENER.ANALIT_TCONS**, **GOBGENER.CR18_ENTID_DIP_Y**, **GOBGENER.CR18_T_SCN_*** — Tablas de referencia actualizadas
- **GOBGENER.EST_EXP_MIXTAS_M**, **GOBGENER.EST_EXP_MM** — Estructuras validadas
- **WORK.ANALIT_*_D** — Matrices de analiticos específicas para DIPRES
- **WORK.CHECK_*** — Validaciones DIPRES (18 variantes: TCONS_D, TRANSVAR_DIPRES, ACTIV_ENTID_DIP, etc.)
- **WORK.CRUCE_*** — Cruces de ejecución DIPRES

### Dependencias Externas
- Librería **GOBGENER** (fuente y destino)
- Tablas producidas por *Proceso Ejecución GC CGR*

---

## 4. Salida CG coy

**Notebook:** `NB-04_salida_cg_coy.ipynb`

**Propósito:** Armar la ejecución presupuestaria de Gobierno Central (coyuntura) consolidando CGR y DIPRES, con redistribución de transacciones mixtas, imputación de datos faltantes y apertura institucional.

### Fuentes de Entrada
- **GOBGENER.EJECUCION**, **GOBGENER.EJEC_DIPRES** — Ejecuciones base CGR y DIPRES
- **GOBGENER.ENTIDADES** — Diccionario de entidades
- **GOBGENER.ANALIT_TCONS** — Matriz de analiticos consolidables
- **GOBGENER.CR18_APERTURA**, **GOBGENER.CR18_ENTID_DIP_Y**, **GOBGENER.CR18_T_SCN_1**, **GOBGENER.CR18_T_SCN_2** — Mapeos de clasificación
- **GOBGENER.EST_EXP_MIXTAS_M**, **GOBGENER.EST_EXP_MM**, **GOBGENER.EST_MIXTAS_M**, **GOBGENER.EST_MM** — Estructuras de muestra y expansión
- **GOBGENER.T_SCN_2**, **GOBGENER.MOLDE_T_SCN_2** — Plantillas de transacciones SCN
- **GOBGENER.IMPUT_GC_DIP**, **GOBGENER.IMPUT_GC_DIP_APER** — Imputaciones permanentes de DIPRES
- **WORK.PROM_MES**, **WORK.CIERRE_MES** — Agregaciones de tipos de cambio (de AUTOEXEC)
- **WORK.ANALIT_***, **WORK.CRUCE_***, **WORK.CHECK_*** — Matrices validadas de CGR/DIPRES
- **WORK.EJECUCION_***, **WORK.EJEC_***, **WORK.CRUCE_EJEC_*** — Ejecuciones intermedias (múltiples variantes)

### Nodos y Transformaciones
1. **CodeTask-RDZUBeSyggbaTi4d** (1- TCons Mixtas_M_CGR) — Redistribución de transacciones mixtas CGR
2. **CodeTask-99VPAhpFklGwBLLO** (5- TCons Mixtas_M_DIP_MOD) — Redistribución de transacciones mixtas DIPRES
3. **CodeTask-4Vv4xGyymdoAYMNg** (4- Salida EJEC hasta CGR) — Consolidación de ejecución hasta CGR
4. **CodeTask-9HjwuVPWzkAGk1TK** (SALIDA CG_coy CGR y DIP) — Ejecución consolidada coyuntural CGR+DIPRES
5. **CodeTask-8b6bsW9BKVc7jJXj** (Aper_CG_coy hasta CGR) — Apertura institucional por CGR
6. **CodeTask-uhvFDAbzyY6GHgs9** (APER_CG_coy CGR y DIP) — Apertura institucional consolidada
7. **CodeTask-QMEyeoD7jJUN9nQu** (2- IMPUT TC Mixtas_M_DIP) — Imputación de transacciones mixtas faltantes DIPRES
8. **CodeTask-4aWGaC1VmZySxlzM** (3- IMPUT Regulares DIP) — Imputaciones regulares DIPRES por mes
9. **CodeTask-iUHB7DjImHdoG82f** (OPC Agregar IMPUT a permanentes) — Agregación de imputaciones a tabla de permanentes
10. **CodeTask-3GhPnDCy9p2wBP7i** (IMPUT DIP Aper_CG_coy) — Imputación de apertura DIPRES
11. **CodeTask-bMqLfdtsanaslAb2** (OPC Salida CG_coy solo DIP) — Ejecución coyuntural solo DIPRES (variante opcional)
12. **CodeTask-QazYc6dHjnESiTAF** (OPC Aper_CG_coy solo DIP) — Apertura coyuntural solo DIPRES (variante opcional)
13. **CodeTask-IEwZ1IRVGWjGV4HL** (OPC Salida Ent CG_coy DIP) — Ejecución por entidad coyuntural DIPRES
14. **CodeTask-86VdtiWQrF36JEkb** (OPC Aper Ent CG_coy DIP) — Apertura por entidad coyuntural DIPRES

### Productos de Salida
- **GOBGENER.IMPUT_GC_DIP**, **GOBGENER.IMPUT_GC_DIP_APER** — Imputaciones permanentes actualizadas
- **WORK.EJECUCION_CG** — Ejecución coyuntural consolidada
- **WORK.EJECUCION_CG_APER** — Apertura coyuntural consolidada
- **WORK.EJECUCION_CG_CGR**, **WORK.EJECUCION_CG_CGR_APER** — Ejecución coyuntural CGR (previo a consolidación)
- **WORK.EJECUCION_CG_DIP**, **WORK.EJECUCION_CG_DIP_APER** — Ejecución coyuntural DIPRES
- **WORK.EJECUCION_A**, **WORK.EJECUCION_B**, **WORK.EJECUCION_C**, **WORK.EJECUCION_D**, **WORK.EJECUCION_F**, **WORK.EJECUCION_G** — Ejecuciones por analítico predefinido (variantes: base, apertura, DIPRES, imputación, etc.)
- **WORK.EJECUCION_CG_DIP_IMPUTACIONES**, **WORK.EJECUCION_CG_DIP_IMPUT_PERM** — Imputaciones de sesión
- **WORK.CRUCE_EJEC_EXP_MIXTAS_M*** — Cruces de ejecución con expansión de mixtas (variantes CGR, DIP, imputación)
- **WORK.EJEC_EXP_MIXTAS_M***, **WORK.EJEC_MUESTRA_MIXTAS_M***, **WORK.EJEC_G_MIXT***, **WORK.EJEC_Z_MIXT*** — Ejecuciones desagregadas por tipo de transacción mixta
- **WORK.CR18_APERTURA_PACAPR***, **WORK.CUENTA_ITEM_07**, **WORK.RATIOS**, **WORK.AUX_RATIOS**, **WORK.TOTALES**, **WORK.TOTALES_INST** — Tablas auxiliares de apertura, ratios y consolidación

### Dependencias Externas
- Librería **GOBGENER** (múltiples tablas de referencia, entrada y salida)
- Flujo **AUTOEXEC** (tipos de cambio y agregaciones mensuales)
- Flujo **Proceso Ejecución GC CGR** (matrices validadas de CGR)
- Flujo **Proceso Ejec GC DIPRES** (matrices validadas de DIPRES)
- Parámetros macro: **&Year**, **&Mes**, **&Moneda**, **&Analista**, **&Mes_imp1**–**&Mes_imp12**, **&Comp1**–**&Comp7**, **&PACAPR1**–**&PACAPR7**

---

## 5. Salida CG Imputa

**Notebook:** `NB-05_salida_cg_imputa.ipynb`

**Propósito:** Refinamiento de ejecución coyuntural CGR+DIPRES incorporando imputaciones sistemáticas por entidades con información agregada y ajustes especiales (transferencias en especie, ingresos operacionales, beca especial carbón).

### Fuentes de Entrada
- **GOBGENER.ANALIT_TCONS**, **GOBGENER.ENTIDADES** — Diccionarios y matrices
- **GOBGENER.IMPUT_GC_DIP**, **GOBGENER.IMPUT_GC_DIP_APER** — Imputaciones permanentes
- **WORK.EJECUCION_CG***, **WORK.EJECUCION_*_PRELIM***, **WORK.EJECUCION_*_APER***, **WORK.EJECUCION_*_DIP***, **WORK.EJECUCION_*_IMP*** — Ejecuciones intermedias de Salida CG coy
- **WORK.RATIOS**, **WORK.TOTALES***, **WORK.EJEC_***, **WORK.CRUCE_***, **WORK.CUENTA_ITEM_07** — Auxiliares de cálculo

### Nodos y Transformaciones
1. (15+ nodos) — Imputación de ingresos operacionales, transferencias en especie de salud (aperturas por ratio), beca especial carbón, y consolidación de ajustes por entidad

### Productos de Salida
- **WORK.EJECUCION_CG_DIP_IMPUTACIONES**, **WORK.EJECUCION_CG_DIP_IMPUT_PERM** — Tabla final de imputaciones integrada
- **WORK.EJECUCION_*_PRELIM_***, **WORK.EJECUCION_*_DIP_AJTESP***, etc. — Ejecuciones con ajustes incorporados

### Dependencias Externas
- Flujo **Salida CG coy** (ejecuciones preliminares)

---

## 6. Salida CNF trim

**Notebook:** `NB-07_salida_cnf_trim_cgr.ipynb`

**Propósito:** Redistribución y consolidación de transacciones de Cuentas Nacionales (CNF) **trimestrales** desde datos CGR, separando el flujo de efectivo en partidas de flujo financiero (MM, MGCG, MGG) y transacciones mixtas (M).

### Fuentes de Entrada
- **GOBGENER.EJECUCION** — Base CGR
- **GOBGENER.ENTIDADES**, **GOBGENER.COFOG**, **GOBGENER.CR18_APERTURA**, **GOBGENER.CR18_ENTID_DIP**, **GOBGENER.CR18_T_SCN_1**, **GOBGENER.CR18_T_SCN_2** — Clasificadores
- **GOBGENER.EST_EXP_MM**, **GOBGENER.EST_EXP_MGCG**, **GOBGENER.EST_EXP_MGG**, **GOBGENER.EST_EXP_MIXTAS_M** — Estructuras de muestra/expansión
- **GOBGENER.EST_MM**, **GOBGENER.EST_MIXTAS_M** — Ponderadores
- **WORK.PROM_MES** — Promedio mensual (de AUTOEXEC)
- **WORK.EJECUCION_CG_CGR***, **WORK.EJEC_***, **WORK.CRUCE_***, etc. — Ejecuciones intermedias de Salida CG coy / CGR

### Nodos y Transformaciones
1. **CodeTask-H1rH4NREOeKCoiaL** (1- TCons Mixtas_M_CGR) — Redistribución de Mixtas (M) trimestrales
2. **CodeTask-IL8ywtwMvZuRmwf7** (2- TCons MGCG_CGR) — Consolidación de MGCG (flujo financiero GC)
3. **CodeTask-btBRh8OoZtFish5W** (3- TCons MM_CGR) — Consolidación de MM (flujo financiero municipal)
4. **CodeTask-ehSKAJod3YJrNKR2** (4- TCons MGG_CGR) — Consolidación de MGG (flujo financiero GG otros)
5. **CodeTask-9aBaLrUVtLPwcDKx** (SALIDA_CNF_trim) — Consolidación final con reasignaciones de códigos SCN

### Productos de Salida
- **WORK.CRUCE_EJEC_*_MIXTAS_M** — Cruces de transacciones Mixtas (M)
- **WORK.EJEC_*_MIXTAS_M***, **WORK.EJEC_MUESTRA_MIXTAS_M***, **WORK.EJEC_G_MIXT***, **WORK.EJEC_Z_MIXT*** — Ejecuciones de Mixtas por variante
- **WORK.EJECUCION_CNF_TRIM** — Salida consolidada CNF trimestral (reporte final)

### Dependencias Externas
- Flujo **AUTOEXEC** (promedios mensuales)
- Flujo **Salida CG coy** (ejecuciones intermedias CGR)
- Parámetro macro: **&Year**

---

## 7. Salida CNF trim DIPRES

**Notebook:** `NB-08_salida_cnf_trim_dip.ipynb`

**Propósito:** Redistribución y consolidación de transacciones de Cuentas Nacionales **trimestrales** desde datos DIPRES (variante paralela a Salida CNF trim CGR), generando el flujo financiero separado por tipo de transacción.

### Fuentes de Entrada
- **GOBGENER.EJEC_DIPRES** — Base DIPRES
- **GOBGENER.ENTIDADES**, **GOBGENER.CR18_ENTID_DIP_Y**, **GOBGENER.CR18_T_SCN_1**, **GOBGENER.CR18_T_SCN_2** — Clasificadores DIPRES
- **GOBGENER.EST_EXP_MM**, **GOBGENER.EST_EXP_MGCG**, **GOBGENER.EST_EXP_MGG**, **GOBGENER.EST_EXP_MIXTAS_M** — Estructuras de muestra/expansión
- **GOBGENER.EST_MM**, **GOBGENER.EST_MIXTAS_M** — Ponderadores
- **WORK.PROM_MES** — Promedio mensual
- **WORK.EJEC_DIP***, **WORK.EJEC_EXP_MIXTAS_M_DIP***, **WORK.CRUCE_***, etc. — Ejecuciones intermedias DIPRES

### Nodos y Transformaciones
1. **CodeTask-1mziCOFZdgQrmMz1** (OPC TC Mixtas_M_DIP) — Redistribución Mixtas (M) trimestrales DIPRES
2. **CodeTask-dxzerDOUWuhVarVS** (OPC TC MGCG_DIP) — Consolidación MGCG trimestral DIPRES
3. **CodeTask-7eghflcoW5HZefrV** (OPC TC MM_DIP) — Consolidación MM trimestral DIPRES
4. **CodeTask-zzKZG4OLXwmn4BZU** (OPC TC MGG_DIP) — Consolidación MGG trimestral DIPRES
5. **CodeTask-GlckAuW3gYkVggMJ** (OPC APER_CNF_trim solo DIP) — Apertura analítica trimestral DIPRES con reasignaciones

### Productos de Salida
- **WORK.EJEC_EXP_MIXTAS_M_DIP***, **WORK.EJEC_MUESTRA_MIXTAS_M_DIP***, **WORK.EJEC_G_MIXT_DIP***, **WORK.EJEC_Z_MIXT_DIP*** — Ejecuciones de Mixtas DIPRES por variante
- **WORK.APER_CNF_TRIM_DIP** — Salida apertura analítica CNF trimestral DIPRES (reporte final)

### Dependencias Externas
- Flujo **AUTOEXEC** (promedios mensuales)
- Flujo **Proceso Ejec GC DIPRES** (matrices validadas DIPRES)
- Parámetro macro: **&Year**

---

## 8. Salidas CNF Anual

**Notebook:** `NB-09_salidas_cnf_anual_y_cofog.ipynb`

**Propósito:** Agregación anual de transacciones de Cuentas Nacionales desde trimestral, consolidación por clasificaciones COFOG y reasignaciones finales de códigos SCN para reporte anual.

### Fuentes de Entrada
- **GOBGENER.EJECUCION**, **GOBGENER.EJEC_DIPRES** — Bases anuales CGR y DIPRES
- **GOBGENER.ENTIDADES**, **GOBGENER.COFOG**, **GOBGENER.CR18_APERTURA**, **GOBGENER.CR18_T_SCN_1**, **GOBGENER.CR18_T_SCN_2** — Clasificadores
- **GOBGENER.EST_EXP_MM**, **GOBGENER.EST_EXP_MGCG**, **GOBGENER.EST_EXP_MGG**, **GOBGENER.EST_EXP_MIXTAS_M** — Estructuras de muestra
- **GOBGENER.EST_MM**, **GOBGENER.EST_MIXTAS_M** — Ponderadores
- **WORK.PROM_MES** — Promedio mensual
- **WORK.EJECUCION_CNF_TRIM***, **WORK.APER_CNF_TRIM_DIP***, **WORK.EJEC_***, etc. — Tablas trimestrales previas

### Nodos y Transformaciones
1. (8+ nodos) — Agregación anual de transacciones MM, MGCG, MGG, Mixtas (M) desde trimestral, aplicación de clasificación COFOG, reasignaciones de negocio para GC/GG/Municipios

### Productos de Salida
- **WORK.EJECUCION_CNF_ANUAL** — Salida consolidada CNF anual
- **WORK.APER_CNF_ANUAL_DIP** — Apertura analítica anual DIPRES
- **WORK.EJECUCION_COFOG_*** — Desagregaciones por función de gobierno

### Dependencias Externas
- Flujo **Salida CNF trim**, **Salida CNF trim DIPRES** (datos trimestrales)
- Parámetro macro: **&Year**

---

## Tabla Consolidada de Flujos Diferidos (No incluidos en este lote)

La migración actual (lote 1) cubre **18 flujos migrables**. Los siguientes **15 flujos diferidos** se migrarán en lotes posteriores:

| Flujo Diferido | Descripción Funcional | Estado |
|---|---|---|
| **Salida_anual para componente especif_no** | Salidas anuales de componentes específicos | Pendiente Lote 2 |
| **Proceso Sit_Patri_MUN_no** | Proceso de situación patrimonial municipal | Pendiente Lote 2 |
| **Proceso Ejecución Municipal CGR_no** | Ejecución de ingresos municipales desde CGR | Pendiente Lote 2 |
| **Traspasos_info** | Gestión de traspasos de información entre sistemas | Pendiente Lote 2 |
| **Salida_CF_GC** | Salida de flujo de caja de Gobierno Central | Pendiente Lote 2 |
| **Salida_DCNA** | Salida hacia base de datos de Cuentas Nacionales | Pendiente Lote 2 |
| **Salidas_Cuenta_Produc_AAPP_no** | Cuentas de producción de AAPP | Pendiente Lote 2 |
| **Salidas_Cuenta_Produc_AAPP_2_no** | Variante 2 de cuentas de producción AAPP | Pendiente Lote 2 |
| **Indicadores municipales** | Cálculo de indicadores desagregados municipales | Pendiente Lote 2 |

---

## Resumen de Dependencias Globales

### Librerías Externas (BD)
- **GOBGENER** — Repositorio central de referencia y salida (73 tablas de entrada, 38 tablas de salida/reescritura)
- **DCV** — Base de datos de tipos de cambio (1 tabla de entrada: MONEDAS_MENSUAL)
- **DCNIDCNA**, **BDATOS_SP**, **CODIGO_ENTIDAD_SP**, **EJEC_MUN** — Fuentes secundarias en flujos diferidos

### Parámetros Macro Críticos
- **&Year** — Año de procesamiento (usado en 98 nodos)
- **&Mes** — Mes de procesamiento (coyuntura)
- **&Mes_imp1**–**&Mes_imp12** — Periodos de imputación (12 meses)
- **&Comp1**–**&Comp7** — Códigos de comparables (validación)
- **&PACAPR1**–**&PACAPR7** — Aperturas de partida/capítulo/articulo (7 variantes)
- **&Moneda** — Moneda de procesamiento
- **&Analista** — Usuario responsable (auditoría)

### Tabla a Tabla (Alcance Completo del Lote 1)

| Tabla Fuente | Tabla Destino | Notebook | Flujo |
|---|---|---|---|
| DCV.MONEDAS_MENSUAL | WORK.CIERRE_MES/TRIM, WORK.PROM_MES/MES_TODAS/TRIM | NB-01 | AUTOEXEC |
| GOBGENER.EJECUCION | WORK.COMPARA_PACAPR, WORK.COMPARA_ENTIDAD, ... (50+ WORK) | NB-02 | Proc. Ejec GC CGR |
| GOBGENER.EJEC_DIPRES | WORK.ANALIT_*_D, WORK.CHECK_*_DIP, ... (35+ WORK) | NB-03 | Proc. Ejec GC DIPRES |
| WORK.CIERRE_MES, WORK.PROM_MES | WORK.EJECUCION_CG*, WORK.CRUCE_EJEC_*, WORK.RATIOS | NB-04 | Salida CG coy |
| WORK.EJECUCION_CG* | WORK.EJECUCION_CNF_TRIM | NB-07 | Salida CNF trim |
| WORK.EJEC_DIP*, WORK.CRUCE_* | WORK.APER_CNF_TRIM_DIP | NB-08 | Salida CNF trim DIP |
| WORK.EJECUCION_CNF_TRIM, WORK.APER_CNF_TRIM_DIP | WORK.EJECUCION_CNF_ANUAL | NB-09 | Salidas CNF Anual |

---

## Notas de Operación

1. **Orden de ejecución recomendado:** AUTOEXEC → Proc. Ejec GC CGR → Proc. Ejec GC DIPRES → Salida CG coy → Salida CG Imputa → Salida CNF trim (CGR) → Salida CNF trim (DIPRES) → Salidas CNF Anual
2. **Tablas WORK son volátiles:** Se reconstruyen en cada corrida; no persisten entre sesiones SAS/Python
3. **Tablas GOBGENER con múltiples reescrituras:** ANALIT_TCONS, CR18_APERTURA, ENTIDADES se actualizan en múltiples flujos; cambios acumulativos requieren validación cruzada
4. **Parámetros año/mes críticos:** Cambios sin sincronización cruzada causarán inconsistencias en consolidación trimestral/anual
5. **Estructura de muestra/expansión compleja:** Uso de ponderadores (POND) y promedios mensuales (PROM_MES) en redistribución de Mixtas; requiere validación de totales al cierre de periodo
