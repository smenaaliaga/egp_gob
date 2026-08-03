# Linaje de datos – Proc_Salidas_Gob_REV_mig

## Descripción general

Este documento especifica el flujo de datos para cada Process Flow migratable del proyecto Proc_Salidas_Gob_REV_mig. Para cada flujo se detalla:
- **Fuentes de entrada** (datasets y librerías externas)
- **Transformaciones principales** (nodos/notebooks)
- **Salidas producidas** (datasets de trabajo y finales)
- **Ubicación en notebooks** (ruta y referencia de ejecución)

El proyecto comprende **16 flujos migrables** (1 PFD y 15 Containers) con **178 nodos** totales distribuidos en notebooks temáticos. Cada flujo puede depender de salidas de otros.

---

## Flujo 1: AUTOEXEC

**Identificador:** PFD-hy8UZ3ebNxGueabH  
**Notebook:** `NB-01_autoexec.ipynb`  
**Nodos:** 3 (1 PROC_SQL, 2 OTHER)

### Propósito
Extrae y transforma datos de tipos de cambio diarios (divisas y UF) de un repositorio centralizado, generando cuatro tablas agregadas por período mensual y trimestral, y una adicional con promedios de todas las monedas disponibles. Esto alimenta reportes de variabilidad de divisas para análisis de cierre contable y gestión financiera.

### Fuentes de entrada
- **Librería:** `DCV`
- **Tabla:** `DCV.MONEDAS_MENSUAL` — datos de tipos de cambio mensuales por moneda

### Transformaciones
| Nodo | Tipo | Estrategia | Descripción |
|------|------|-----------|-------------|
| `CodeTask-XzOatjIuMbeLV29h` | OTHER | Python | Set Libreria — configuración de paths y librerías |
| `CodeTask-D6fqrxqReNOK5Xch` | PROC_SQL | Pandas | Monedas_Mensual — lectura de `DCV.MONEDAS_MENSUAL`, agregación de promedios por período |
| `CodeTask-q5ZEbAg5C43nmYfy` | OTHER | Python | Programa — lógica de inicialización y validaciones |

### Salidas generadas
- `WORK.CIERRE_MES` — Tipos de cambio agregados a nivel mensual
- `WORK.CIERRE_TRIM` — Tipos de cambio agregados a nivel trimestral
- `WORK.PROM_MES` — Promedios mensuales de monedas
- `WORK.PROM_MES_TODAS` — Promedios mensuales para todas las monedas disponibles
- `WORK.PROM_TRIM` — Promedios trimestrales

### Dependencias
- Ninguna (flujo de inicialización)

### Notas
- Requiere acceso a librería `DCV` con tabla `MONEDAS_MENSUAL`
- Salidas alimentan flujos posteriores de análisis financiero (cierre contable)

---

## Flujo 2: Proceso Ejecución GC CGR

**Identificador:** PFD-wyxachgCf8TVObWz  
**Notebook:** `NB-02_proceso_ejecucion_gc_cgr.ipynb`  
**Nodos:** 31 (20 PROC_SQL, 4 DATA_STEP, 2 IMPORT, 3 QUERY, 2 PROC_OTHER)

### Propósito
Flujo de validación y clasificación de datos de ejecución presupuestaria del gobierno central (Contraloría), que reconcilia cambios en estructuras presupuestarias (entidades, analíticos, transferencias) y enriquece la base con clasificaciones de actividad y función (COFOG).

### Fuentes de entrada

#### De librerías persistentes (GOBGENER)
- `GOBGENER.ANALIT_TCONS` — Clasificación de transferencias consolidables/no consolidables
- `GOBGENER.COFOG` — Clasificación COFOG (función de gasto)
- `GOBGENER.COFOG_T_SCN_2` — COFOG extendido para transferencias
- `GOBGENER.CR18_APERTURA` — Matriz de apertura presupuestaria (actividades/niveles)
- `GOBGENER.CR18_ENTID_DIP` — Mapeo de entidades a DIPRES
- `GOBGENER.CR18_ENTID_DIP_Y` — Mapeo por año
- `GOBGENER.CR18_T_SCN_1` — Clasificaciones de transferencias (tipo 1)
- `GOBGENER.CR18_T_SCN_2` — Clasificaciones de transferencias (tipo 2)
- `GOBGENER.EJECUCION` — Datos de ejecución presupuestaria (principal)
- `GOBGENER.ENTIDADES` — Maestro de entidades del gobierno central
- `GOBGENER.EST_EXP_MGCG` — Estructura de expansión MGCG
- `GOBGENER.EST_EXP_MGG` — Estructura de expansión MGG
- `GOBGENER.EST_EXP_MIXTAS_M` — Estructura de expansión de transacciones mixtas
- `GOBGENER.EST_EXP_MM` — Estructura de expansión MM
- `GOBGENER.EST_MIXTAS_M` — Tipología de transacciones mixtas
- `GOBGENER.EST_MM` — Tipología MM

#### De WORK (salidas de pasos anteriores en el mismo flujo o de AUTOEXEC)
- 30 datasets intermedios de validación y transformación

### Transformaciones principales

#### Fase 1: Detección de cambios estructurales (Nodos 1-3)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-vRkhqURhrfdncIIr` | Compara PACAPR — detect cambios en códigos/nombres partida/capítulo/programa/entidad vs maestro histórico |
| `CodeTask-eSSEltFJH17EEWGl` | Compara entidades — detect cambios en estructura por entidad |
| `CodeTask-iE4gTB7hPMNsX4dR` | Detecta nuevas entidades sin correspondencia histórica |

**Salidas:** `WORK.COMPARA_PACAPR`, `WORK.COMPARA_ENTIDAD`, `WORK.NUEVAS_ENTIDADES`

#### Fase 2: Clasificación de nuevas entidades (Nodos 3b-4a)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-19o6EdegIblGxthd` | Clasifica nuevas entidades — las agrega al maestro `GOBGENER.ENTIDADES` |
| `CodeTask-SR2tNwn9ee5q4ldH` | Verifica analíticos predefinidos faltantes — busca por clave jerárquica y frecuencia |

**Salidas:** `GOBGENER.ENTIDADES`, `WORK.ANALIT_FIJO_CLAS`, `WORK.ANALIT_FIJO_FALTANTE`

#### Fase 3: Clasificación de analíticos fijos y variables (Nodos 4b-5b)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-imoWjgB9c7XBGB5q` | Actualiza `CR18_T_SCN_1` con clasificaciones fijas validadas |
| `CodeTask-6FS3khd1yz37XIOH` | Clasifica analíticos variables — propone clasificación por KEY_1..KEY_5 |
| `CodeTask-Jtvr77EbawEqiCx3` | Importa y valida propuesta de analíticos variables desde Excel |

**Salidas:** `WORK.ANALIT_VAR_CLAS*`, `WORK.CR18_T_SCN_2`, `GOBGENER.CR18_T_SCN_1`, `GOBGENER.CR18_T_SCN_2`

#### Fase 4: Clasificación de transferencias consolidables (Nodos 6a-6b)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-x5iMg8dNCjGmDI64` | Detecta nuevas transferencias sin clasificar — exporta a Excel |
| `CodeTask-ESKX4AdeM3cTnf1w` | Importa y valida clasificaciones TCONS desde Excel |

**Salidas:** `WORK.CHECK_TCONS*`, `GOBGENER.ANALIT_TCONS`

#### Fase 5: Estructuras de expansión para transacciones (Nodos 7a-7f)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-Wil6N97RHUIMSVfs` | Detecta MM sin estructura — propone plantilla 12 meses, valida suma=1 |
| `CodeTask-kH5fNiMJvLnwyCUU` | Detecta MIXTAS_M sin estructura — expande por entidad, valida pesos |
| `CodeTask-1LH51NVFniO8SFVp` | Verifica TCONS como MM en muestra vs EST_MM |
| `CodeTask-bYsFTxJS2Uy6FqcG` | Verifica TCONS como M en muestra vs EST_EXP_MIXTAS_M |
| `CodeTask-QeChUmtaSsJfkhiI` | Detecta MGCG sin estructura — propone base, valida suma=1 |
| `CodeTask-HBcKDsWhhhzfcrxa` | Detecta MGG sin estructura — propone agregado, valida suma≈1 |

**Salidas:** `WORK.EST_EXP_MM_C`, `WORK.EST_EXP_MIXTAS_M_C`, `GOBGENER.EST_EXP_MGCG`, `GOBGENER.EST_EXP_MGG`

#### Fase 6: Clasificaciones de actividad y función (Nodos 8-10)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-YSlqeaLYiJMtrUHD` | Detecta nuevas entidades sin actividad/nivel — imputa según diccionario PARTIDA/CAPITULO |
| `CodeTask-cccOjpzWIPgShZJi` | Actualiza `CR18_APERTURA` y réplica DIPRES con nuevas entidades |
| `CodeTask-EKp3vGrePAlPMEBt` | Detecta entidades/partidas/capítulos/programas sin COFOG |
| `CodeTask-Ubk9S5YsiZMvmuUO` | Acumula clasificaciones COFOG de nuevas entidades |
| `CodeTask-kzhY4l9Rfund2KoE` | Detecta GORE sin COFOG para cuentas 24/33 |
| `CodeTask-nqT31jzfT4UqjYBV` | Agrega clasificaciones COFOG de nuevas entidades |

**Salidas:** `GOBGENER.CR18_APERTURA`, `GOBGENER.CR18_ENTID_DIP_Y`, `GOBGENER.COFOG`, `GOBGENER.COFOG_T_SCN_2`

#### Fase 7: Detección de cambios de nomenclatura (Nodos OPC1-OPC3)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-kQueAyJNTTEPVdD5` | Detecta partidas cuyo nombre cambió (SOUNDEX/SPEDIS) |
| `CodeTask-EOvYz3aqoYTNZHG3` | Actualiza nombres de partidas en `GOBGENER.ENTIDADES` |
| `CodeTask-1gcQykl9dzmVvPUU` | Detecta capítulos cuyo nombre cambió |
| `CodeTask-d8UbUVbjSNJXldiJ` | Actualiza nombres de capítulos en `GOBGENER.ENTIDADES` |
| `CodeTask-vtjUgNIVXI9HJ1gj` | Detecta programas cuyo nombre cambió |
| `CodeTask-R9vRh7beA6yqV7xx` | Actualiza nombres de programas en `GOBGENER.ENTIDADES` |

**Salidas:** `WORK.COMPARA_PARTIDA*`, `WORK.COMPARA_CAPITULO*`, `WORK.COMPARA_PROGRAMA*`

### Salidas finales (persistentes en GOBGENER)
- `GOBGENER.ANALIT_TCONS` — Actualizado con nuevas transferencias clasificadas
- `GOBGENER.COFOG*` — Clasificaciones COFOG enriquecidas
- `GOBGENER.CR18_APERTURA` — Matriz de apertura actualizada
- `GOBGENER.CR18_ENTID_DIP*` — Mapeos DIPRES actualizados
- `GOBGENER.CR18_T_SCN_1/2` — Clasificaciones de transferencias actualizadas
- `GOBGENER.ENTIDADES` — Maestro de entidades actualizado
- `GOBGENER.EST_EXP_M*` — Estructuras de expansión actualizadas

### Dependencias
- Requiere datos de `GOBGENER.EJECUCION` (ejecutados previamente)
- Depende indirectamente de outputs de AUTOEXEC para parámetros de período
- Alimenta todos los flujos posteriores de generación de salidas

### Parámetros macro
- `&Year` — Año fiscal de procesamiento (sin valor declarado → debe parametrizarse)

### Notas
- Flujo con mayor complejidad: incluye ciclos de validación manual via Excel (exportar/importar)
- Genera 50+ datasets intermedios de validación (CHECK_*)
- Crítico: cualquier cambio en estructuras presupuestarias requiere recorrer este flujo completo

---

## Flujo 3: Proceso Ejec GC DIPRES

**Identificador:** ProcessFlowContainer-FYwV5olig1EcGaWj  
**Notebook:** `NB-03_proceso_ejec_gc_dipres.ipynb`  
**Nodos:** 10 (8 PROC_SQL, 2 IMPORT)

### Propósito
El flujo valida y clasifica actividades, analíticos presupuestarios y transacciones de tesorería de la ejecución presupuestaria DIPRES, imputando automáticamente nuevas entidades y asignaciones según diccionarios de reglas y patrones históricos, con revisión manual de inconsistencias para asegurar consistencia en los datos de gobierno.

### Fuentes de entrada

#### De librerías persistentes (GOBGENER)
- `GOBGENER.ANALIT_TCONS` — Clasificación de transferencias
- `GOBGENER.CR18_ENTID_DIP_Y` — Mapeo DIPRES por año
- `GOBGENER.CR18_T_SCN_1/2` — Clasificaciones de transferencias
- `GOBGENER.EJEC_DIPRES` — Ejecución presupuestaria DIPRES (principal)
- `GOBGENER.ENTIDADES` — Maestro de entidades
- `GOBGENER.EST_EXP_MIXTAS_M` — Estructura de expansión mixtas
- `GOBGENER.EST_EXP_MM` — Estructura de expansión MM

#### De WORK (outputs de Proceso Ejecución GC CGR)
- 21 datasets de clasificaciones de analíticos (`ANALIT_*_CLAS*`)
- 8 datasets de checks de validación (`CHECK_*`)
- 5 datasets de cruces entre estructuras (`CRUCE_*`)

### Transformaciones

#### Fase 1: Validación de actividades por entidad (Nodos 1-2)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-yXykqUZknliUd6Tv` | Valida actividades/niveles de nuevas entidades DIPRES |
| `CodeTask-6aNX7ji1HAf8Qnl2` | Complementa CR18_ENTID_DIP_Y con entidades DIPRES del año |

**Salidas:** `WORK.CHECK_ACTIV_ENTID_DIP*`

#### Fase 2: Clasificación de analíticos DIPRES (Nodos 3-5)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-sKKoX2BlU3PiXDXH` | Valida analíticos fijos contra CR18_T_SCN_1 |
| `CodeTask-23lpner3oIe465S4` | Valida analíticos variables contra CR18_T_SCN_2 |
| `CodeTask-iZLD51MjB1SyOVBJ` | Imputa analíticos faltantes por patrón histórico |

**Salidas:** `WORK.ANALIT_*_CLAS_D`, `WORK.CHECK_ANALIT_*`

#### Fase 3: Validación de transferencias DIPRES (Nodos 6-8)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-1UPaqG3cjfbxeW38` | Valida clasificación de transferencias (TCONS) |
| `CodeTask-dzljPfKJnYXDrIyx` | Valida estructuras de expansión (MM/MIXTAS_M) |
| `CodeTask-TKijGtt2hNAaRG55` | Compara totales de ejecución CGR vs DIPRES |

**Salidas:** `WORK.CHECK_TCONS_D`, `WORK.EST_M*`, `WORK.TCONS_EST_DEF_M`

#### Fase 4: Consolidación final (Nodos 9-10)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-kQiRSuJx6sDK7Afw` | Consolida datos DIPRES por mes/partida |
| `CodeTask-hiQbCN96JdfFBZKx` | Genera estadísticas de cobertura y consistencia |

**Salidas:** `WORK.EJEC_DIP*`, `WORK.CHECK_*`

### Salidas finales
- `GOBGENER.ANALIT_TCONS` — Transferencias DIPRES validadas
- `GOBGENER.CR18_ENTID_DIP_Y` — Mapeo DIPRES actualizado
- `GOBGENER.CR18_T_SCN_1/2` — Clasificaciones DIPRES
- `GOBGENER.EST_EXP_MIXTAS_M/MM` — Estructuras validadas
- `WORK.EJEC_DIP` — Ejecución DIPRES consolidada por período

### Dependencias
- **Debe ejecutarse después de:** Proceso Ejecución GC CGR (requiere maestros actualizados en GOBGENER)
- Alimenta: Salida CG coy (consumidor de `WORK.EJEC_DIP`)

### Parámetros macro
- `&Year` — Año fiscal de procesamiento
- `&Comp1-7` — Comparadores (sin valores declarados)

### Notas
- Complementa el flujo CGR con validación paralela desde perspectiva DIPRES
- Reutiliza 70% de las reglas de clasificación del flujo CGR
- Genera 15+ datasets de validación (CHECK_*_DIP)

---

## Flujo 4: Salida CG coy

**Identificador:** ProcessFlowContainer-8iloVuuXSe8CJiAb  
**Notebook:** `NB-04_salida_cg_coy.ipynb`  
**Nodos:** 14 (14 PROC_SQL)

### Propósito
Procesa datos de ejecución presupuestaria (de Contraloría y DIPRES) de transacciones mixtas y regulares para generar indicadores mensuales de consumo de gobierno, desagregados por sectores, actividades, partidas presupuestarias y tipología de transacciones económicas.

### Fuentes de entrada

#### De librerías persistentes (GOBGENER)
- `GOBGENER.ANALIT_TCONS` — Clasificación de transferencias
- `GOBGENER.CR18_APERTURA` — Matriz de apertura presupuestaria
- `GOBGENER.CR18_ENTID_DIP*` — Mapeos DIPRES
- `GOBGENER.CR18_T_SCN_1/2` — Clasificaciones de transferencias
- `GOBGENER.EJECUCION` — Datos de ejecución CGR
- `GOBGENER.EJEC_DIPRES` — Datos de ejecución DIPRES
- `GOBGENER.ENTIDADES` — Maestro de entidades
- `GOBGENER.EST_EXP_MIXTAS_M*` — Estructuras de expansión mixtas
- `GOBGENER.EST_MIXTAS_M` — Tipología de mixtas
- `GOBGENER.IMPUT_GC_DIP*` — Imputaciones consolidadas CGR-DIPRES
- `GOBGENER.MOLDE_T_SCN_2` — Plantilla de clasificaciones
- `GOBGENER.T_SCN_2` — Transferencias sin consolidar

#### De WORK (outputs de Proceso Ejec GC DIPRES)
- `WORK.EJEC_DIP*` — Ejecución DIPRES consolidada
- 90+ datasets de cruces, ratios y desagregaciones

### Transformaciones

#### Fase 1: Preparación y consolidación por transacción (Nodos 1-5)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-RDZUBeSyggbaTi4d` | Extrae ejecución CGR por mes/partida/entidad/analítico |
| `CodeTask-99VPAhpFklGwBLLO` | Extrae ejecución DIPRES con apertura presupuestaria |
| `CodeTask-4Vv4xGyymdoAYMNg` | Cruce de CGR vs DIPRES por partida/capítulo/programa |
| `CodeTask-9HjwuVPWzkAGk1TK` | Imputación de datos faltantes usando patrones históricos |
| `CodeTask-8b6bsW9BKVc7jJXj` | Normalización de códigos y denominaciones |

**Salidas:** `WORK.EJECUCION_A*`, `WORK.EJECUCION_B*`, `WORK.EJECUCION_C*`, `WORK.EJECUCION_D*`, `WORK.EJECUCION_F*`, `WORK.EJECUCION_G*`

#### Fase 2: Desagregación por tipología de transacción (Nodos 6-10)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-uhvFDAbzyY6GHgs9` | Cruza con EST_EXP_MIXTAS_M para transacciones mixtas |
| `CodeTask-QMEyeoD7jJUN9nQu` | Expande transacciones por mes (12 períodos) |
| `CodeTask-4aWGaC1VmZySxlzM` | Agrega ratios de cobertura (ejecutado vs presupuestado) |
| `CodeTask-iUHB7DjImHdoG82f` | Consolida por sector de actividad |
| `CodeTask-3GhPnDCy9p2wBP7i` | Acumula indicadores mensuales de consumo |

**Salidas:** `WORK.EJEC_MUEST_MIXTAS_M*`, `WORK.EJECUCION_CG*`, `WORK.RATIOS*`

#### Fase 3: Generación de salidas finales (Nodos 11-14)
| Nodo | Descripción |
|------|-------------|
| `CodeTask-bMqLfdtsanaslAb2` | Consolida totales de ejecución por período |
| `CodeTask-QazYc6dHjnESiTAF` | Agrega datos por institución/organismo |
| `CodeTask-IEwZ1IRVGWjGV4HL` | Genera tabla de ratios (ejecutado/presupuestado/comprometido) |
| `CodeTask-86VdtiWQrF36JEkb` | Pivota para formato de salida BI (columnas por mes/trimestre) |

**Salidas:** `WORK.TOTALES`, `WORK.TOTALES_INST`, `WORK.AUX_RATIOS`, `WORK.EJECUCION_CG_DIP_*`

### Salidas finales
- `GOBGENER.IMPUT_GC_DIP` — Matriz consolidada CGR-DIPRES con imputaciones
- `GOBGENER.IMPUT_GC_DIP_APER` — Idem con apertura presupuestaria
- `WORK.EJECUCION_CG_DIP*` — Tablas mensuales de ejecución por mes/período
- `WORK.EJECUCION_CG_CGR*` — Variante solo CGR
- `WORK.TOTALES*` — Totalizaciones por institución y período
- `WORK.RATIOS` — Indicadores de cobertura y desempeño

### Dependencias
- **Requiere:** Outputs de Proceso Ejec GC DIPRES (`WORK.EJEC_DIP*`)
- **Requiere:** Maestros de GOBGENER actualizados (Proceso Ejecución GC CGR)
- Alimenta: Reportes BI y dashboards de seguimiento presupuestario mensual

### Parámetros macro
- `&Year` — Año fiscal de procesamiento
- `&Mes*` — Meses a incluir (12 variables Mes_imp1..Mes_imp12, sin valores declarados)
- `&Moneda` — Moneda de presentación (sin valor declarado)

### Notas
- Genera 50+ datasets intermedios de desagregaciones y ratios
- Salida crítica para BI: sirve base para dashboards de seguimiento presupuestario
- Conversión de moneda (factor 1000000 para presentar en millones)
- Dependencia fuerte con WORK.PROM_MES (de AUTOEXEC) para ajustes de divisas

---

## Flujos diferidos (lote posterior)

Los siguientes 15 Process Flows están **pendientes de migración** en lotes posteriores:

1. **Proceso Sit_Patri_MUN** — Situación patrimonial municipal
2. **Proceso Ejecución Municipal CGR** — Ejecución municipal consolidada
3. **Salida CG Imputa** — Generación de imputaciones de ejecución
4. **Salida CNF trim** — Salida trimestral consolidada
5. **Salidas CNF anual y COFOG** — Consolidado anual con funciones
6. **Salida_anual para componente especif** — Especializaciones anuales
7. **Traspasos_info** — Procesamiento de transferencias de información
8. **Salida_CF_GC** — Salida contable-financiera gobierno central
9. **Salida_DCNA** — Exportación a DCNA (sistema externo)
10. **Salidas_Cuenta_Produc_AAPP** — Cuenta de producción de administraciones públicas
11. **Salidas_Cuenta_Produc_AAPP_2** — Variante 2 de cuenta de producción
12. **Indicadores municipales** — Métricas de desempeño municipal

Estos flujos no se incluyen en esta entrega pero utilizan outputs de los cuatro flujos migrables documentados arriba.

---

## Resumen de dependencias entre flujos

```
AUTOEXEC
  ├─→ Proceso Ejecución GC CGR ✓ (este lote)
        ├─→ Proceso Ejec GC DIPRES ✓ (este lote)
        │     └─→ Salida CG coy ✓ (este lote)
        │           └─→ [Flujos posteriores]
        └─→ Salida CG coy ✓ (este lote)
              └─→ [Flujos posteriores]

[Otros 12 flujos diferidos]
```

---

## Tabla de librerías y conexiones

| Alias | Descripción | Tablas utilizadas | Acceso |
|-------|-------------|-------------------|--------|
| `DCV` | Datos centrales de cambio/moneda | MONEDAS_MENSUAL | R (lectura) |
| `GOBGENER` | Gobernanza genera — maestros persistentes | 40+ tablas de catálogos y configuración | R/W |
| `WORK` | Área de trabajo (sesión SAS→memoria Python) | 150+ datasets transitorios | R/W |

---

## Convenciones de nomenclatura

### Prefijos de datasets
- **GOBGENER.*** — Maestros y tablas de configuración persistentes
- **WORK.*** — Datasets transitorios (sesión, no persistentes en este plan)
- **DCV.*** — Datos de monedas y divisas (lectura especializada)

### Sufijos comunes
- `_CLAS` — Clasificación aplicada / completada
- `_CLAS_2`, `_CLAS_3`, etc. — Versiones iterativas de clasificación
- `_D` — Variante DIPRES
- `_CGR` — Variante Contraloría
- `_P` — Preliminary (preliminar)
- `_FALT` / `_FALTANTE` — Filas sin clasificar/incompletas
- `_R` — Revisado / reconciliado
- `_PRELIM` — Preliminar
- `_APER` — Con apertura presupuestaria

---

## Matriz de trazabilidad: entrada → salida

| Flujo | Entrada principal | Transformación crítica | Salida principal | Consumidor |
|-------|-------------------|------------------------|------------------|-----------|
| AUTOEXEC | `DCV.MONEDAS_MENSUAL` | Agregación por período | `WORK.PROM_MES*` | Salida CG coy |
| Proceso Ejecución GC CGR | `GOBGENER.EJECUCION` | Reconciliación de estructuras | `GOBGENER.ENTIDADES*` | Proceso Ejec GC DIPRES |
| Proceso Ejec GC DIPRES | `GOBGENER.EJEC_DIPRES` | Validación paralela DIPRES | `WORK.EJEC_DIP` | Salida CG coy |
| Salida CG coy | `WORK.EJEC_DIP` + `GOBGENER.EJECUCION` | Desagregación y ratios | `WORK.TOTALES` | BI / Dashboards |
