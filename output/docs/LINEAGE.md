# Linaje de datos — Proc_Salidas_Gob_REV_mig-2

## Descripción general

Este documento detalla el linaje (data lineage) de los **18 flujos migrables** del proyecto Proc_Salidas_Gob_REV_mig-2, mapeando **qué se lee** (fuentes), **qué se produce** (salidas) y **dónde vive cada paso** en los notebooks ejecutables.

La estructura refleja el output strategy de `notebook-flow`: cada Process Flow (PFD) o ProcessFlowContainer genera un notebook independiente (ej. `NB-01_autoexec.ipynb`, `NB-02_proceso_ejecucion_gc_cgr.ipynb`, etc.), dentro del cual las tareas se organizan en celdas lógicamente secuenciadas.

---

## 1. AUTOEXEC (PFD-hy8UZ3ebNxGueabH)

**Notebook**: `output/NB-01_autoexec.ipynb`  
**Nodos**: 3 (1 PROC_SQL, 2 OTHER)  
**Descripción**: Procesa y transforma datos de monedas y tipos de cambio (diarios) en agregaciones mensuales y trimestrales (cierre y promedio) para análisis de variación de divisas en el gobierno general.

### Fuentes de entrada
- `DCV.MONEDAS_MENSUAL` — tabla de tasas de cambio/monedas diarias de la biblioteca DCV

### Tablas/datasets producidos (WORK)
- `WORK.CIERRE_MES` — cierre mensual de tasas
- `WORK.CIERRE_TRIM` — cierre trimestral de tasas
- `WORK.PROM_MES` — promedio mensual
- `WORK.PROM_MES_TODAS` — promedio mensual de todas las monedas
- `WORK.PROM_TRIM` — promedio trimestral

### Celdas (nodal mapping)
1. **Celda 0**: `CodeTask-XzOatjIuMbeLV29h` ("Set Libreria") — Inicialización de bibliotecas y parámetros globales
2. **Celda 1**: `CodeTask-D6fqrxqReNOK5Xch` ("Monedas_Mensual") — PROC SQL que lee DCV.MONEDAS_MENSUAL y produce agregaciones
3. **Celda 2**: `CodeTask-q5ZEbAg5C43nmYfy` ("Programa") — Bloque Python de validación/logging posterior

### Observaciones
- Flujo de **inicialización de sesión**: prepara el WORK con datos de referencia de monedas
- Las salidas se usan downstream en múltiples flujos de salida (ej. `Salida CG coy`)

---

## 2. Proceso Ejecución GC CGR (PFD-wyxachgCf8TVObWz)

**Notebook**: `output/NB-02_proceso_ejecucion_gc_cgr.ipynb`  
**Nodos**: 31 (20 PROC_SQL, 4 DATA_STEP, 3 QUERY, 2 IMPORT, 2 PROC_OTHER)  
**Descripción**: Flujo de validación y clasificación de ejecuciones presupuestarias (GOBGENER) que compara cambios en nomenclatura de entidades, partidas y códigos, luego enriquece la matriz de analíticos fijos y variables con propuestas automáticas de clasificación, finalizando con validaciones de estructuras de transferencias consolidables y actividades COFOG.

### Fuentes de entrada (GOBGENER)
- `GOBGENER.ANALIT_TCONS` — analíticos consolidables
- `GOBGENER.COFOG` — clasificación COFOG
- `GOBGENER.COFOG_T_SCN_2` — mapeo COFOG a SCN
- `GOBGENER.CR18_APERTURA` — apertura CR18
- `GOBGENER.CR18_ENTID_DIP` — entidades DIP CR18
- `GOBGENER.CR18_ENTID_DIP_Y` — entidades DIP CR18 (histórico)
- `GOBGENER.CR18_T_SCN_1` — mapeo CR18 a SCN nivel 1
- `GOBGENER.CR18_T_SCN_2` — mapeo CR18 a SCN nivel 2
- `GOBGENER.EJECUCION` — datos de ejecución presupuestaria de Contraloría
- `GOBGENER.ENTIDADES` — catálogo de entidades
- `GOBGENER.EST_EXP_MGCG` — estructura de expansión (MGCG)
- `GOBGENER.EST_EXP_MGG` — estructura de expansión (MGG)
- `GOBGENER.EST_EXP_MIXTAS_M` — estructura de expansión (mixtas)
- `GOBGENER.EST_EXP_MM` — estructura de expansión (MM)
- `GOBGENER.EST_MIXTAS_M` — estructura mixtas
- `GOBGENER.EST_MM` — estructura MM
- Más 40+ datasets WORK intermediarios (cruce, analítico, checks)

### Tablas/datasets producidos
**En GOBGENER** (upsert/actualización):
- `GOBGENER.ANALIT_TCONS`, `GOBGENER.COFOG`, `GOBGENER.COFOG_T_SCN_2`
- `GOBGENER.CR18_APERTURA`, `GOBGENER.CR18_ENTID_DIP`, `GOBGENER.CR18_ENTID_DIP_Y`, `GOBGENER.CR18_T_SCN_1`, `GOBGENER.CR18_T_SCN_2`
- `GOBGENER.ENTIDADES`, `GOBGENER.EST_EXP_MGCG`, `GOBGENER.EST_EXP_MGG`, `GOBGENER.EST_EXP_MIXTAS_M`, `GOBGENER.EST_EXP_MM`

**En WORK** (temporales, 80+ tablas):
- Tablas de comparación: `WORK.COMPARA_CAPITULO`, `WORK.COMPARA_ENTIDAD`, `WORK.COMPARA_PACAPR`, `WORK.COMPARA_PARTIDA`, `WORK.COMPARA_PROGRAMA` (y variantes `_1`, `_2`)
- Tablas de analítico: `WORK.ANALIT_FIJO_CLAS`, `WORK.ANALIT_FIJO_CLAS_2`, `WORK.ANALIT_VAR_CLAS`, `WORK.ANALIT_VAR_CLAS_2`–`_5`, `WORK.ANALIT_VAR_CLAS_GORE`, `WORK.ANALIT_VAR_CLAS_RESTO`
- Tablas de cruce: `WORK.CRUCE_FIJO`, `WORK.CRUCE_FIJO_2`, `WORK.CRUCE_FIJO_MAX`, `WORK.CRUCE_FIJO_MAX_2`, `WORK.CRUCE_PROP` (y variantes 2–5), `WORK.CRUCE_VAR` (y variantes)
- Tablas CHECK: `WORK.CHECK_ACTIV_ENTID`, `WORK.CHECK_ANALIT_FIJO`, `WORK.CHECK_ANALIT_REV`, `WORK.CHECK_ANALIT_VAR`, `WORK.CHECK_COFOG_ANALIT`, etc. (30+ checks)
- Otras: `WORK.CR18_APERTURA_PACAPR_BD`, `WORK.EJEC_CGR`, `WORK.ENTID_CGR_YEAR`, `WORK.ENT_N`, `WORK.EST_EXP_M_C`, `WORK.NUEVAS_ENTIDADES`

### Celdas (nodal mapping resumido)
1. **Celda 1**: `CodeTask-vRkhqURhrfdncIIr` — Check Compara PACAPR
2. **Celda 2**: `CodeTask-eSSEltFJH17EEWGl` — Check Compara C_ENTIDAD
3. ... (26 celdas más, secuenciadas por dependencia)
31. **Celda 30**: `CodeTask-R9vRh7beA6yqV7xx` — Query final de consolidación

### Observaciones
- Flujo de **validación y enriquecimiento de vocabulario**: compara cambios de nomenclatura y propone clasificaciones
- Estrategia: `sql_pushdown` para todos los nodos PROC_SQL (lectura direkt de BD, escritura #tmp de sesión)
- Dependencia de macro: `Year` (año de proceso)
- Salidas feeding flujos downstream: `Proceso Ejec GC DIPRES`, `Salida CG coy`, etc.

---

## 3. Proceso Ejec GC DIPRES (ProcessFlowContainer-FYwV5olig1EcGaWj)

**Notebook**: `output/NB-03_proceso_ejec_gc_dipres.ipynb`  
**Nodos**: 10 (6 PROC_SQL, 4 IMPORT)  
**Descripción**: Proceso de validación y clasificación de estructuras analíticas de ejecución presupuestaria (DIPRES) para asegurar consistencia en actividad, nivel de entidad, y afectación de transacciones según diccionarios institucionales.

### Fuentes de entrada
**De GOBGENER**:
- `GOBGENER.ANALIT_TCONS`, `GOBGENER.CR18_ENTID_DIP_Y`, `GOBGENER.CR18_T_SCN_1`, `GOBGENER.CR18_T_SCN_2`
- `GOBGENER.EJEC_DIPRES` — ejecución presupuestaria del DIPRES
- `GOBGENER.ENTIDADES`, `GOBGENER.EST_EXP_MIXTAS_M`, `GOBGENER.EST_EXP_MM`

**De WORK** (45+ tablas intermediarias del flujo anterior):
- `WORK.ANALIT_ENTIDAD_VAR_D`, `WORK.ANALIT_FIJO_CLAS`, `WORK.ANALIT_FIJO_CLAS_2`, `WORK.ANALIT_FIJO_CLAS_D`, `WORK.ANALIT_FIJO_FALTANTE_D`
- `WORK.ANALIT_VAR_CLAS` (1–5), `WORK.ANALIT_VAR_CLAS_GORE`, `WORK.ANALIT_VAR_CLAS_RESTO`, `WORK.ANALIT_VAR_CLAS_RESTO_F`
- `WORK.CHECK_*_DIP` (variantes específicas DIPRES)
- `WORK.CRUCE_FIJO`, `WORK.CRUCE_FIJO_2`, `WORK.CRUCE_PROP` (2–5), `WORK.CRUCE_VAR` (2–5)
- `WORK.EJEC_DIP`, `WORK.EST_M`, `WORK.EST_MM`, `WORK.TCONS_EST_DEF_M`

### Tablas/datasets producidos
**En GOBGENER** (upsert):
- `GOBGENER.ANALIT_TCONS`, `GOBGENER.CR18_ENTID_DIP_Y`, `GOBGENER.CR18_T_SCN_1`, `GOBGENER.CR18_T_SCN_2`
- `GOBGENER.EST_EXP_MIXTAS_M`, `GOBGENER.EST_EXP_MM`

**En WORK** (variantes con sufijo `_D` o nuevas):
- `WORK.ANALIT_ENTIDAD_VAR_D`, `WORK.ANALIT_FIJO_CLAS`, `WORK.ANALIT_FIJO_CLAS_2`, `WORK.ANALIT_FIJO_CLAS_D`, `WORK.ANALIT_FIJO_FALTANTE_D`
- `WORK.ANALIT_VAR_CLAS` (1–5), `WORK.ANALIT_VAR_CLAS_GORE`, `WORK.ANALIT_VAR_CLAS_RESTO`, `WORK.ANALIT_VAR_CLAS_RESTO_F`
- `WORK.CHECK_*_DIP` (CHECK_ACTIV_ENTID_DIP, CHECK_ACTIV_ENTID_DIP_2, CHECK_ANALIT_REV, etc.)
- `WORK.CRUCE_FIJO` (y variantes), `WORK.CRUCE_PROP` (y variantes), `WORK.CRUCE_VAR` (y variantes `_MAX`)
- `WORK.EJEC_DIP`, `WORK.EST_M`, `WORK.EST_MM`, `WORK.TCONS_EST_DEF_M`

### Celdas (nodal mapping resumido)
1–10: 10 celdas de IMPORT y PROC_SQL, secuenciadas por dependencia de ejecución CGR previa

### Observaciones
- Flujo **paralelo** a `Proceso Ejecución GC CGR` pero enfocado en fuente DIPRES
- Reutiliza tablas de clasificación (CR18, ANALIT) pero produce variantes específicas
- Estrategia: `sql_pushdown` (todas PROC_SQL)
- Parámetro: `Year`

---

## 4. Salida CG coy (ProcessFlowContainer-8iloVuuXSe8CJiAb)

**Notebook**: `output/NB-04_salida_cg_coy.ipynb`  
**Nodos**: 14 (14 PROC_SQL)  
**Descripción**: Este flujo procesa y redistribuye información de transacciones mixtas (muestra y expansión) desde datos de Contraloría y DIPRES, genera indicadores de consumo de gobierno desagregados por diferentes dimensiones, y produce salidas consolidadas para análisis coyuntural con imputaciones de datos faltantes.

### Fuentes de entrada
**De GOBGENER**:
- `GOBGENER.ANALIT_TCONS`, `GOBGENER.CR18_APERTURA`, `GOBGENER.CR18_ENTID_DIP`, `GOBGENER.CR18_ENTID_DIP_Y`
- `GOBGENER.CR18_T_SCN_1`, `GOBGENER.CR18_T_SCN_2`, `GOBGENER.EJECUCION`, `GOBGENER.EJEC_DIPRES`, `GOBGENER.ENTIDADES`
- `GOBGENER.EST_EXP_MIXTAS_M`, `GOBGENER.EST_MIXTAS_M`, `GOBGENER.IMPUT_GC_DIP`, `GOBGENER.IMPUT_GC_DIP_APER`
- `GOBGENER.MOLDE_T_SCN_2`, `GOBGENER.T_SCN_2`

**De WORK** (150+ tablas intermediarias y outputs de flujos anteriores):
- Ratios/auxiliares: `WORK.AUX_RATIOS`, `WORK.PROM_MES`
- Aperturas: `WORK.CR18_APERTURA_PACAPR`, `WORK.CR18_APERTURA_PACAPR_V`
- Cruces de mixtas: `WORK.CRUCE_EJEC_EXP_MIXTAS_M`, `WORK.CRUCE_EJEC_EXP_MIXTAS_M_DIP`, `WORK.CRUCE_EJEC_EXP_MIXTAS_M_DIP_IMP`
- Ejecuciones A–G (múltiples variantes): `WORK.EJECUCION_A`, `WORK.EJECUCION_A_APER`, `WORK.EJECUCION_A_DIP`, `WORK.EJECUCION_A_DIP_APER`, `WORK.EJECUCION_A_DIP_APER_IMP`, `WORK.EJECUCION_A_DIP_IMP`, `WORK.EJECUCION_A_PRELIM` (y subvariantes), `WORK.EJECUCION_B` (y variantes), etc.
- Ejecuciones consolidadas: `WORK.EJECUCION_CG_CGR`, `WORK.EJECUCION_CG_CGR_APER`, `WORK.EJECUCION_CG_CGR_PREV`, `WORK.EJECUCION_CG_DIP`, `WORK.EJECUCION_CG_DIP_APER` (y variantes)
- Ejecuciones de mixtas: `WORK.EJEC_EXP_MIXTAS_M`, `WORK.EJEC_EXP_MIXTAS_M_DIP`, `WORK.EJEC_EXP_MIXTAS_M_DIP_IMP`, `WORK.EJEC_EXP_MIXTAS_M_PRELIM` (y variantes)
- Muestra/expansión: `WORK.EJEC_MIXTAS_M_TOTAL`, `WORK.EJEC_MUESTRA_MIXTAS_M`, `WORK.EJEC_MUESTRA_MIXTAS_M_DIP`, etc.
- Otros: `WORK.CUENTA_ITEM_07`, `WORK.EJEC_DIP`, `WORK.EJEC_DIP_Y`, `WORK.EST_M`, `WORK.EST_MM`, `WORK.RATIOS`, `WORK.TOTALES`, `WORK.TOTALES_INST`

### Tablas/datasets producidos
**En GOBGENER** (upsert):
- `GOBGENER.IMPUT_GC_DIP`, `GOBGENER.IMPUT_GC_DIP_APER`

**En WORK** (consolidadas de coyuntura):
- Consolidadas CGR: `WORK.EJECUCION_CG_CGR`, `WORK.EJECUCION_CG_CGR_APER`, `WORK.EJECUCION_CG_CGR_APER_PREV`, `WORK.EJECUCION_CG_CGR_PREV`
- Consolidadas DIP: `WORK.EJECUCION_CG_DIP`, `WORK.EJECUCION_CG_DIP_APER`, `WORK.EJECUCION_CG_DIP_APER_IMP`, `WORK.EJECUCION_CG_DIP_APER_PREV`, `WORK.EJECUCION_CG_DIP_IMP`, `WORK.EJECUCION_CG_DIP_IMPUTACIONES`, `WORK.EJECUCION_CG_DIP_IMPUT_PERM`, `WORK.EJECUCION_CG_DIP_PREV`
- Por transacción (A–G): `WORK.EJECUCION_C`, `WORK.EJECUCION_D`, `WORK.EJECUCION_F`, `WORK.EJECUCION_G` y variantes con `_APER`, `_DIP`, `_DIP_APER`, `_DIP_APER_IMP`, `_DIP_IMP`
- Mixtas: `WORK.EJEC_EXP_MIXTAS_M`, `WORK.EJEC_EXP_MIXTAS_M_DIP`, `WORK.EJEC_EXP_MIXTAS_M_DIP_IMP`, `WORK.EJEC_EXP_MIXTAS_M_PRELIM` (y variantes)
- Indicadores: `WORK.AUX_RATIOS`, `WORK.RATIOS`
- Otros outputs: `WORK.CR18_APERTURA_PACAPR`, `WORK.CR18_APERTURA_PACAPR_V`, `WORK.CRUCE_EJEC_EXP_MIXTAS_M*`, `WORK.CUENTA_ITEM_07`, `WORK.TOTALES`, `WORK.TOTALES_INST`

### Celdas (nodal mapping resumido)
1. **Celda 4**: `CodeTask-RDZUBeSyggbaTi4d` — TCons Mixtas_M_CGR
2. **Celda 17**: `CodeTask-99VPAhpFklGwBLLO` — TCons Mixtas_M_DIP_MOD
3. ... (12 celdas más)
14. **Celda 245**: `CodeTask-86VdtiWQrF36JEkb` — Aper Ent CG_coy DIP

### Observaciones
- Flujo **más complejo**: integra CGR, DIPRES, imputaciones y cálculo de indicadores
- Estrategia: `sql_pushdown` (todas PROC_SQL)
- Parámetro: `Year`, macro variables de periodos: `Mes`, `Mes_imp1`–`Mes_imp12`
- Reutiliza tablas de `Proceso Ejecución GC CGR` y `Proceso Ejec GC DIPRES`
- Produce salidas finales consolidadas para reportería de coyuntura

---

## 5–18. Flujos adicionales (DIFERIDOS EN LOTE POSTERIOR)

Los siguientes 14 flujos fueron **identificados pero no traducidos en esta entrega** (listed in `flujos_diferidos`):

1. **Salida CG Imputa** — Imputaciones adicionales de GC
2. **Salida CNF trim** — Cuentas Nacionales Trimestrales
3. **Salida_CNF_Trim_CGR** — CNF Trimestral CGR
4. **Salida_CNF_Trim_DIP** — CNF Trimestral DIPRES
5. **Salidas CNF anual y COFOG** — CNF Anual y clasificación COFOG
6. **Salida_anual para componente especif_no** — Salida anual de componentes específicos
7. **Proceso Sit_Patri_MUN_no** — Situación patrimonial municipal (excluido)
8. **Proceso Ejecución Municipal CGR_no** — Ejecución municipal de CGR (excluido)
9. **Traspasos_info** — Traspasos de información
10. **Salida_CF_GC** — Salida de Contabilidad Financiera GC
11. **Salida_DCNA** — Salida de DCNA
12. **Salidas_Cuenta_Produc_AAPP_no** — Cuentas de producción AAPP (excluido)
13. **Salidas_Cuenta_Produc_AAPP_2_no** — Cuentas de producción AAPP alternativo (excluido)
14. **Indicadores municipales** — Indicadores municipales

**Estas serán traducidas en lotes posteriores** conforme al plan de migración iterativo.

---

## Matriz de dependencias (dependencias entre flujos)

```
AUTOEXEC (NB-01)
    ↓
    └─→ Proceso Ejecución GC CGR (NB-02)
            ↓
            └─→ Proceso Ejec GC DIPRES (NB-03)
                    ↓
                    └─→ Salida CG coy (NB-04) ←─── Tablas de monedas (AUTOEXEC)
```

**Observación clave**: Los flujos 2, 3 y 4 tienen dependencia secuencial estricta (cada uno consume outputs del anterior). El AUTOEXEC prepara datos de referencia que alimentan el flujo 4 directamente.

---

## Resumen de volumen de datos

| Aspecto | Conteo |
|---------|---------|
| **Flujos migrables** | 4 (en esta entrega) |
| **Nodos totales** | 58 |
| **Nodos PROC_SQL** | 44 |
| **Tablas GOBGENER (lectura)** | ~50 |
| **Tablas GOBGENER (escritura/upsert)** | ~20 |
| **Tablas WORK (intermediarias + outputs)** | ~250+ |
| **Macro parámetros** | ~35 (Year, Comp1–7, Mes, Mes_imp1–12, Moneda, PACAPR1–7, Analista) |

---

## Convenciones de nomenclatura

- **GOBGENER.\***: Tablas de base de datos persistentes (diccionarios, clasificadores, estructuras)
- **WORK.\***: Tablas temporales de sesión (intermediarias y outputs del pipeline)
- **NB-XX_\***: Notebooks numerados secuencialmente, nombrados por flujo SAS
- **Sufijos**:
  - `_CGR`: Variante de Contraloría
  - `_DIP`: Variante de DIPRES
  - `_APER`: Abierto / desagregado por apertura
  - `_IMP`: Con imputaciones
  - `_PRELIM`: Preliminar (consolidación intermedia)
  - `_MIXTAS_M`: Referido a transacciones mixtas
  - `_MAX`: Máximo / expansión

---

## Observaciones finales

1. **Flujos DIFERIDOS** (14 flujos adicionales) no figuran en este linaje; serán documentados en lotes posteriores.
2. **Estrategia sql_pushdown**: Todos los nodos PROC_SQL usan esta estrategia, minimizando descarga de datos a memoria.
3. **Macro variables críticas**: `Year`, `Comp*`, `Mes*`, `Moneda`, `PACAPR*` — deben ser inyectadas en la celda `parameters` de cada notebook.
4. **Interdependencia fuerte**: Los 4 flujos forman un pipeline lineal; cambios en outputs de upstream afectan downstream.
5. **Volumen de WORK**: ~250+ tablas temporales acumuladas durante ejecución; limpieza de sesión necesaria entre ejecuciones completas.
