# Runbook: Operación de Proc_Salidas_Gob_REV_mig

## 1. Alcance y cobertura de esta entrega

Este runbook describe la operación día a día del proyecto **Proc_Salidas_Gob_REV_mig** en su versión actual, que **migra 2 flujos de los 17 totales**:

- **AUTOEXEC**: extracción y agregación de tipos de cambio diarios (monedas)
- **Proceso Ejecución GC CGR**: validación y clasificación de datos de ejecución presupuestaria del gobierno central

**Flujos diferidos** (no incluidos en esta entrega; migración en lotes posteriores):
- Proceso Ejec GC DIPRES
- Salida CG coy
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

## 2. Estructura de salida y artefactos

Los notebooks traducidos se ubican en:

```
output/
├── NB-01_autoexec.ipynb                   (3 nodos, 1 tabla origen, 5 salidas WORK)
└── NB-02_proceso_ejecucion_gc_cgr.ipynb   (31 nodos, múltiples joins, 54 tablas de trabajo)
run_all.py                                  (script de orquestación)
```

Cada notebook:
- Contiene una celda `parameters` al inicio (para inyección de parámetros vía papermill)
- Registra inicio/fin con timestamp
- Genera tablas en WORK (temporales, limpiadas al final de sesión) y GOBGENER (persistentes)
- Valida dependencias entre nodos antes de ejecutar

## 3. Parámetros de ejecución y configuración

### Macro variables requeridas

Los notebooks esperan los siguientes parámetros en la celda `parameters`. **El usuario debe declararlos en `project_config.yaml` o inyectarlos explícitamente:**

| Parámetro | Tipo | Descripción | Valor esperado | Estado |
|-----------|------|-------------|-----------------|--------|
| `Year` | int | Año fiscal de ejecución | 2024, 2023, etc. | **Sin valor ← Declarar** |
| `Mes` | int | Período mensual (1-12) | 1-12 | **Sin valor ← Declarar** |
| `Moneda` | str | Código de moneda | USD, EUR, CLF, UF | **Sin valor ← Declarar** |
| `Comp1` a `Comp7` | str | Códigos de comparadores/entidades especiales | IDs | **Sin valor ← Declarar** |
| `Mes_imp1` a `Mes_imp12` | int | Períodos de imputación mensuales | 1-12 | **Sin valor ← Declarar** |
| `Analista` | str | Identificación del usuario ejecutor | Usuario/email | **Sin valor ← Declarar** |
| `PACAPR1` a `PACAPR7` | str | Partida/Capítulo/Programa/Apertura | Códigos presupuestarios | **Sin valor ← Declarar** |

### Librerías y conexiones de base de datos

| Librería | Tipo | Tablas consumidas | Conexión requerida | Status |
|----------|------|-------------------|--------------------|--------|
| GOBGENER | BD remota | EJECUCION, ENTIDADES, CR18_*, ANALIT_*, EST_EXP_* | `ENTIDAD` alias | ✓ Configurada |
| DCV | BD remota | MONEDAS_MENSUAL | `ENTIDAD` alias | ✓ Configurada |
| WORK | Sesión SAS | Salidas temporales | Local | ✓ Automática |

### Configuración de rutas (hardcodeadas en SAS, pendiente M-001)

Rutas por nodo (conforme a mejora M-001 "Eliminar rutas hardcodeadas"):

- `CodeTask-XzOatjIuMbeLV29h` (AUTOEXEC setup): `/sasdata/BCCH/GEM_DCNI/...`
- `CodeTask-D6fqrxqReNOK5Xch` (MONEDAS_MENSUAL): referencia a libref DCV
- `CodeTask-6FS3khd1yz37XIOH` (Analiticos Var export Excel): `\\FILESERVER\VOLM\GEM\050_DCNI\...`
- Resto de nodos GOBGENER: escritura a BD, sin rutas

**Acción requerida**: Crear `config/paths.yml` centralizado y parametrizar antes de producción (ver Mejora M-009).

## 4. Orden de ejecución y dependencias

### Flujo AUTOEXEC (NB-01)

```
CodeTask-XzOatjIuMbeLV29h (Set Libreria)
    ↓ (sin datos, setup)
CodeTask-D6fqrxqReNOK5Xch (Monedas_Mensual)
    ├→ Input: DCV.MONEDAS_MENSUAL (parámetro Year)
    └→ Output: WORK.CIERRE_MES, WORK.CIERRE_TRIM, WORK.PROM_MES, WORK.PROM_MES_TODAS, WORK.PROM_TRIM
    ↓ (dependencia)
CodeTask-q5ZEbAg5C43nmYfy (Programa)
    └→ Utilización de PROM_MES para agregaciones posteriores
```

**Duración estimada**: 2-5 minutos  
**Carga de datos**: ~50K filas de tasas de cambio diarias por período

### Flujo Proceso Ejecución GC CGR (NB-02)

```
FASE 1: Detectar cambios en estructura presupuestaria (Nodos 1-3)
├─ CodeTask-vRkhqURhrfdncIIr (1-Check Compara PACAPR)
│  └→ Compara EJECUCION vs ENTIDADES por Year
├─ CodeTask-eSSEltFJH17EEWGl (2-Check Compara C_ENTIDAD)
│  └→ Detecta cambios en código de partida/capítulo por entidad
└─ CodeTask-iE4gTB7hPMNsX4dR (3a-Check Nvas Entidades)
   └→ Anti-join: entidades nuevas sin histórico

FASE 2: Clasificar analíticos predefinidos (Nodos 4a-b)
├─ CodeTask-SR2tNwn9ee5q4ldH (4a-Check Analiticos Predef)
│  └→ Imputa clasificación de mayor frecuencia histórica
├─ CodeTask-imoWjgB9c7XBGB5q (4b-Clasif Analiticos Predef)
│  └→ Actualiza CR18_T_SCN_1, genera CHECK tables
└─ Validaciones: CHECK_ANALIT_FIJO, CHECK_ANALIT_VAR (sin filas = OK)

FASE 3: Clasificar analíticos variables con revisión manual (Nodos 5a-b)
├─ CodeTask-6FS3khd1yz37XIOH (5a-Check Analiticos Var)
│  ├→ Exporta propuesta a Excel: `/FILESERVER/.../propuesta_ANALITIC_VAR_&Year.xlsx`
│  └→ Pausa: **Usuario debe revisar y clasificar manualmente en Excel**
├─ [INTERVENCIÓN MANUAL] Revisar, validar, completar Excel
└─ CodeTask-Jtvr77EbawEqiCx3 (5b-Clasif Analiticos Var)
   └→ Reimporta desde Excel, limpia y anexa a CR18_T_SCN_2

FASE 4: Clasificar transferencias consolidables (Nodos 6a-b)
├─ CodeTask-x5iMg8dNCjGmDI64 (6a-Check Nvas TCons)
│  ├→ Detecta TC nuevas sin clasificar
│  └→ Exporta a Excel: `/FILESERVER/.../propuesta_TCONS_&Year.xlsx`
├─ [INTERVENCIÓN MANUAL] Revisar clasificación TC (Consolidable/No Consolidable)
└─ CodeTask-ESKX4AdeM3cTnf1w (6b-Clasif Nvas TCons)
   └→ Reimporta, valida y anexa a ANALIT_TCONS

FASE 5: Expandir estructuras analíticas (Nodos 7a-f)
├─ CodeTask-Wil6N97RHUIMSVfs (7a-Check Est_Exp_MM)
│  ├→ Detecta analíticos MM sin estructura
│  └→ Plantilla Excel 12 meses
├─ CodeTask-kH5fNiMJvLnwyCUU (7b-Check Est_Exp_M)
│  ├→ Detecta MIXTAS_M sin expansión
│  └→ Validación de ponderadores (suma=1)
├─ CodeTask-1LH51NVFniO8SFVp (7c-Check Est_MM)
│  └→ Verifica EST_MM integridad
├─ CodeTask-bYsFTxJS2Uy6FqcG (7d-Check Est_M)
│  └→ Verifica EST_EXP_MIXTAS_M integridad
├─ CodeTask-QeChUmtaSsJfkhiI (7e-Check Est_Exp_MGCG)
│  └→ Detecta MGCG sin estructura, propone base item='03'
└─ CodeTask-HBcKDsWhhhzfcrxa (7f-Check Est_Exp_MGG)
   └→ Detecta MGG sin estructura

FASE 6: Clasificación COFOG y Actividades (Nodos 8a-10b)
├─ CodeTask-YSlqeaLYiJMtrUHD (8a-Check Nvas Ent ACTIV)
│  └→ Imputa ACTIVIDAD/NIVEL por reglas PARTIDA/CAPITULO
├─ CodeTask-cccOjpzWIPgShZJi (8b-Clasif ACTIV de Nvas Ent)
│  └→ Actualiza CR18_ENTID_DIP, CR18_ENTID_DIP_Y
├─ CodeTask-EKp3vGrePAlPMEBt (9a-Check Nvas Ent COFOG)
│  └→ Detecta nuevas entidades sin COFOG
├─ CodeTask-Ubk9S5YsiZMvmuUO (9b-Clasif COFOG)
│  └→ Anexa COFOG imputadas
├─ CodeTask-kzhY4l9Rfund2KoE (10a-Check Analit COFOG)
│  └→ Detecta GORE sin clasificación COFOG
└─ CodeTask-nqT31jzfT4UqjYBV (10b-Clasif Analit COFOG)
   └→ Anexa clasificaciones COFOG

FASE 7: Detectar cambios de nomenclatura (Nodos OPC 1a-3b)
├─ CodeTask-kQueAyJNTTEPVdD5 (OPC 1a-Check Name Partida)
│  └→ Fonética SOUNDEX/SPEDIS, cambios de nombre partida
├─ CodeTask-EOvYz3aqoYTNZHG3 (OPC 1b-Clasif Name Partida)
│  └→ Actualiza ENTIDADES con nuevos nombres
├─ CodeTask-1gcQykl9dzmVvPUU (OPC 2a-Check Name Capitulo)
│  └→ Idem capítulo
├─ CodeTask-d8UbUVbjSNJXldiJ (OPC 2b-Clasif Name Capitulo)
│  └→ Actualiza ENTIDADES con nuevos nombres capítulo
├─ CodeTask-vtjUgNIVXI9HJ1gj (OPC 3a-Check Name Programa)
│  └→ Idem programa
└─ CodeTask-R9vRh7beA6yqV7xx (OPC 3b-Clasif Name Programa)
   └→ Actualiza ENTIDADES con nuevos nombres programa
```

**Duración estimada**: 15-45 minutos (sin incluir revisiones manuales Excel)  
**Intervenciones manuales requeridas**: 3 (Analiticos Var, TCONS, Estructuras MM/M/MGCG/MGG)

## 5. Instrucciones de ejecución

### 5.1 Ejecución completa (ambos flujos)

```bash
# Opción A: Via run_all.py (recomendado)
python run_all.py \
  --year 2024 \
  --mes 12 \
  --moneda USD \
  --analista usuario@dominio.cl \
  --comp1 10201 --comp2 5601 --comp3 04001000 \
  --pacapr1 1 --pacapr2 2 --pacapr3 3
```

**Salida esperada**:
```
[2026-08-04 14:32:15] Starting Proc_Salidas_Gob_REV_mig
[2026-08-04 14:32:15] Running NB-01_autoexec.ipynb with Year=2024, Mes=12
[2026-08-04 14:36:42] ✓ NB-01 completed: 5 WORK tables created
[2026-08-04 14:36:43] Running NB-02_proceso_ejecucion_gc_cgr.ipynb with Year=2024
[2026-08-04 14:37:09] ⚠ Fase 3 (Analiticos Var): Pausa. Revisar propuesta_ANALITIC_VAR_2024.xlsx
[2026-08-04 14:37:10] Resume with: python run_all.py --resume --step 5b
...
```

### 5.2 Ejecución por notebook individual

```bash
# NB-01: Tipos de cambio
jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=600 \
  --output=NB-01_autoexec_run.ipynb \
  --ExecutePreprocessor.allow_errors=False \
  output/NB-01_autoexec.ipynb \
  --log-level=INFO

# NB-02: Ejecución GC CGR (fases 1-4)
papermill output/NB-02_proceso_ejecucion_gc_cgr.ipynb \
  output/NB-02_proceso_ejecucion_gc_cgr_2024.ipynb \
  -p Year 2024 \
  -p Mes 12 \
  -p Analista "usuario@dominio.cl" \
  --log-level=INFO
```

### 5.3 Ejecución con intervenciones manuales

**Paso 1**: Ejecutar hasta Fase 3
```bash
python run_all.py --year 2024 --mes 12 --stop-at phase3
```

**Paso 2**: Revisar Excel (`propuesta_ANALITIC_VAR_2024.xlsx`)
- Abrir archivo en `/FILESERVER/VOLM/GEM/050_DCNI/.../propuesta_ANALITIC_VAR_2024.xlsx`
- Validar cada fila: `KEY_1` (entidad), `KEY_2` (cuenta), `KEY_3` (item)
- Completar columnas: `N_ANALITICO` (nombre), `C_ANALITICO` (código clasificador)
- Salvar y cerrar

**Paso 3**: Reanudar desde Fase 5
```bash
python run_all.py --year 2024 --mes 12 --resume-from phase5
```

**Paso 4**: Revisar Excel (`propuesta_TCONS_2024.xlsx`)
- Clasificar TC nuevas: columna `TCONS_CLASIFICADA` = 1 (Consolidable) ó 0 (No Consolidable)
- Documentar motivo en `COMENTARIO`

**Paso 5**: Finalizar
```bash
python run_all.py --year 2024 --mes 12 --resume-from phase6
```

## 6. Verificaciones post-ejecución

### 6.1 Validaciones automáticas en cada fase

Tras ejecutar cada fase, revisar **logs y CHECK tables**:

| CHECK Table | Significado | OK = | Acción si falla |
|-------------|-------------|------|-----------------|
| CHECK_ACTIV_ENTID | Nuevas entidades sin actividad | 0 filas | Revisar `CodeTask-YSlqeaLYiJMtrUHD`, validar reglas PARTIDA/CAPITULO |
| CHECK_ANALIT_FIJO | Analíticos predefinidos con inconsistencias | 0 filas | Completar clasificación manual en `CodeTask-6FS3khd1yz37XIOH` |
| CHECK_ANALIT_VAR | Analíticos variables sin clasificar | 0 filas | Importar Excel en `CodeTask-Jtvr77EbawEqiCx3` |
| CHECK_ANALIT_REV | Analíticos pendientes de revisión | 0 filas | Revisar nomenclatura en Fase 7 |
| CHECK_COFOG_ANALIT | Analíticos sin COFOG (GORE) | 0 filas | Clasificar en `CodeTask-kzhY4l9Rfund2KoE` |
| CHECK_COFOG_ENTID | Entidades sin COFOG | 0 filas | Clasificar en `CodeTask-EKp3vGrePAlPMEBt` |
| CHECK_EST_EXP_MM | MM sin estructura | 0 filas | Expandir en `CodeTask-Wil6N97RHUIMSVfs` |
| CHECK_EST_EXP_MIXTAS_M | MIXTAS_M sin estructura por entidad | 0 filas | Expandir en `CodeTask-kH5fNiMJvLnwyCUU` |
| CHECK_EST_MM | MM en muestra sin EST_MM | 0 filas | Validar definición |
| CHECK_EST_EXP_MGCG | MGCG sin estructura | 0 filas | Expandir en `CodeTask-QeChUmtaSsJfkhiI` |
| CHECK_TRANSVAR | Transferencias sin clasificar | 0 filas | Completar `CodeTask-x5iMg8dNCjGmDI64` |
| CHECK_TCONS | TCONS nuevas sin clasificar | 0 filas | Revisar Excel en `CodeTask-ESKX4AdeM3cTnf1w` |

### 6.2 Validaciones de cobertura de datos

Tras completar ambos notebooks, ejecutar:

```sql
-- Conteos esperados (ejemplo Year=2024)
SELECT 'DCV.MONEDAS_MENSUAL' AS tabla, COUNT(*) AS filas FROM DCV.MONEDAS_MENSUAL
UNION ALL
SELECT 'GOBGENER.EJECUCION', COUNT(*) FROM GOBGENER.EJECUCION WHERE &Year = 2024
UNION ALL
SELECT 'GOBGENER.ENTIDADES', COUNT(*) FROM GOBGENER.ENTIDADES
UNION ALL
SELECT 'GOBGENER.CR18_APERTURA', COUNT(*) FROM GOBGENER.CR18_APERTURA
UNION ALL
SELECT 'GOBGENER.ANALIT_TCONS', COUNT(*) FROM GOBGENER.ANALIT_TCONS
UNION ALL
SELECT 'GOBGENER.EST_EXP_MM', COUNT(*) FROM GOBGENER.EST_EXP_MM
UNION ALL
SELECT 'GOBGENER.EST_EXP_MIXTAS_M', COUNT(*) FROM GOBGENER.EST_EXP_MIXTAS_M
UNION ALL
SELECT 'GOBGENER.EST_EXP_MGCG', COUNT(*) FROM GOBGENER.EST_EXP_MGCG
UNION ALL
SELECT 'GOBGENER.EST_EXP_MGG', COUNT(*) FROM GOBGENER.EST_EXP_MGG
UNION ALL
SELECT 'GOBGENER.COFOG', COUNT(*) FROM GOBGENER.COFOG;
```

**Comparar con baseline anterior** para detectar anomalías (ej: caída de >20% en ENTIDADES).

### 6.3 Validación de integridad referencial

```sql
-- Detectar huérfanos: ENTIDADES sin COFOG
SELECT COUNT(DISTINCT C_ENTIDAD) AS ent_sin_cofog
FROM GOBGENER.ENTIDADES e
WHERE NOT EXISTS (
  SELECT 1 FROM GOBGENER.COFOG c 
  WHERE c.C_ENTIDAD = e.C_ENTIDAD AND c.ANO = &Year
);

-- Detectar huérfanos: CR18_APERTURA sin ENTIDADES
SELECT COUNT(DISTINCT C_ENTIDAD) AS apertura_sin_entidad
FROM GOBGENER.CR18_APERTURA ca
WHERE NOT EXISTS (
  SELECT 1 FROM GOBGENER.ENTIDADES e 
  WHERE e.C_ENTIDAD = ca.C_ENTIDAD
);

-- Validar suma de ponderadores en EST_EXP_MM
SELECT C_ANALITICO, SUM(PONDERADOR) AS sum_pond, COUNT(*) AS meses
FROM GOBGENER.EST_EXP_MM
GROUP BY C_ANALITICO
HAVING ABS(SUM(PONDERADOR) - 1.0) > 0.01;
```

Si alguna consulta retorna filas, investigar la fase correspondiente.

## 7. Problemas comunes y soluciones

### 7.1 Error: `Macro variable &Year not defined`

**Síntoma**:
```
ERROR: Macro variable Year is not defined. (or not resolved)
```

**Causa**: Parámetro `Year` no inyectado en celda `parameters`

**Solución**:
1. Editar `project_config.yaml`:
   ```yaml
   run:
     macro_params:
       Year: 2024
       Mes: 12
       Moneda: USD
   ```
2. Ó inyectar vía CLI:
   ```bash
   python run_all.py --year 2024 --mes 12
   ```

### 7.2 Error: `Table GOBGENER.MONEDAS_MENSUAL not found`

**Síntoma**:
```
ERROR: Table or view does not exist: 'DCV.MONEDAS_MENSUAL'
```

**Causa**: Conexión ENTIDAD alias no disponible, ó libref DCV no configurada

**Solución**:
1. Verificar conexión BD:
   ```bash
   sqlplus usuario@ENTIDAD
   SELECT COUNT(*) FROM DCV.MONEDAS_MENSUAL;
   ```
2. Si no conecta, revisar `~/.oracle/.tnsnames.ora` y alias `ENTIDAD`
3. Ó usar variables de entorno:
   ```bash
   export ORACLE_USER=usuario
   export ORACLE_PASSWORD=***
   export ORACLE_SID=ENTIDAD
   python run_all.py --year 2024
   ```

### 7.3 Error: `File not found: propuesta_ANALITIC_VAR_2024.xlsx`

**Síntoma**:
```
ERROR: Cannot open file '\\FILESERVER\VOLM\GEM\050_DCNI\...\propuesta_ANALITIC_VAR_2024.xlsx' (FileNotFoundError)
```

**Causa**: Ruta hardcodeada inaccesible, ó usuario sin permisos

**Solución**:
1. Verificar ruta en Nodo `CodeTask-6FS3khd1yz37XIOH`:
   ```python
   # Buscar en NB-02 celda ~65
   excel_path = "\\\\FILESERVER\\VOLM\\GEM\\050_DCNI\\...\\propuesta_ANALITIC_VAR_&Year.xlsx"
   ```
2. Montar compartida (si es red):
   ```bash
   # Linux
   sudo mount -t cifs -o username=usuario //FILESERVER/VOLM /mnt/fileserver
   
   # Windows (ya debe estar montada)
   NET USE Z: \\FILESERVER\VOLM /PERSISTENT:YES
   ```
3. Ó cambiar ruta local en `project_config.yaml` (mejora M-009):
   ```yaml
   paths:
     excel_export_dir: "./output/excel_proposals/"
   ```

### 7.4 Error: `Integrity constraint violation: unique key constraint failed`

**Síntoma**:
```
ERROR: ORA-00001: unique constraint GOBGENER.CR18_APERTURA_UK violated
```

**Causa**: Duplicados en CR18_APERTURA durante `CodeTask-19o6EdegIblGxthd` (append de nuevas entidades)

**Solución**:
1. Revisar CHECK table:
   ```sql
   SELECT C_ENTIDAD, COUNT(*) AS cnt
   FROM GOBGENER.CR18_APERTURA
   GROUP BY C_ENTIDAD
   HAVING COUNT(*) > 1;
   ```
2. Eliminar duplicados:
   ```sql
   DELETE FROM GOBGENER.CR18_APERTURA
   WHERE ROWID NOT IN (
     SELECT MIN(ROWID) FROM GOBGENER.CR18_APERTURA
     GROUP BY C_ENTIDAD, C_PARTIDA, C_CAPITULO, C_PROGRAMA, ANO
   );
   COMMIT;
   ```
3. Reintentar fase 2: `python run_all.py --year 2024 --resume-from phase2`

### 7.5 Advertencia: `%SPEDIS returns missing for mismatched strings`

**Síntoma** (en fase 7, OPC):
```
WARNING: SPEDIS algorithm cannot compare strings of different lengths (Partida='3401001' vs '34010')
```

**Causa**: Nodos OPC comparan nombres con diferentes longitudes; SPEDIS falla

**Solución** (no bloqueante):
- Revisar log: `WORK.CHECK_COMPARA_PARTIDA` para falsos positivos
- Si hay >5 advertencias, aumentar threshold en `CodeTask-kQueAyJNTTEPVdD5`:
  ```python
  # Cambiar de 50% a 60% acierto
  SPEDIS_THRESHOLD = 0.60
  ```
- Ejecutar nuevamente fase 7: `python run_all.py --year 2024 --resume-from phase7`

### 7.6 Error: `No rows qualify for aggregation`

**Síntoma** (en fase 5, analíticos variables):
```
WARNING: PROC SQL did not create a table because no rows were selected
```

**Causa**: Periodo `&Mes` sin registros en EJECUCION, ó clasificación ya completa

**Solución**:
- No es error crítico; continuar ejecución
- Verificar si `WORK.CHECK_ANALIT_VAR` está vacía (significa fase 3 ya completa)
- Si hay datos faltantes, revisar parámetro `Mes`: `python run_all.py --year 2024 --mes 6`

## 8. Monitoreo y logging

### 8.1 Activación de logging detallado

```bash
# Via parametro CLI
python run_all.py --year 2024 --log-level DEBUG

# Via variable de entorno
export LOG_LEVEL=DEBUG
export LOG_FILE=logs/proc_salidas_2024.log
python run_all.py --year 2024
```

**Archivo de log**: `logs/proc_salidas_2024-12-04.log`

### 8.2 Métricas de desempeño

Al finalizar cada notebook, se registra:
```
[NB-01] Execution time: 4m 32s
[NB-01] Tables created: 5 (CIERRE_MES, CIERRE_TRIM, PROM_MES, PROM_MES_TODAS, PROM_TRIM)
[NB-01] Rows processed: 52,847
[NB-02] Execution time: 38m 15s (inc. manual reviews)
[NB-02] Manual steps: 3 (Analiticos Var, TCONS, Estructuras)
[NB-02] Rejects (CHECK tables): 17 rows (5x ANALIT_VAR, 8x TCONS, 4x COFOG)
[NB-02] Tables written to GOBGENER: 14 persistent tables
```

## 9. Flujos diferidos: próximas entregas

Los siguientes 15 flujos están **deferred** y se migrarán en lotes posteriores:

1. **Proceso Ejec GC DIPRES** (10 nodos, 47 inputs) → Validación DIPRES
2. **Salida CG coy** (14 nodos, 134 inputs) → Salidas de consumo gubernamental
3. **Salida CG Imputa** (N nodos) → Imputaciones CG
4. **Salida CNF trim** (N nodos) → Consolidación trimestral CNF
5. **Salidas CNF anual y COFOG** (N nodos) → Consolidación anual
6. **Salida_anual para componente especif** (N nodos) → Desgloses anuales
7. **Proceso Sit_Patri_MUN** (N nodos) → Situación patrimonial municipal
8. **Proceso Ejecución Municipal CGR** (N nodos) → Ejecución municipal
9. **Traspasos_info** (N nodos) → Transferencias informativas
10. **Salida_CF_GC** (N nodos) → Consolidación fiscal GC
11. **Salida_DCNA** (N nodos) → Salidas DCNA
12. **Salidas_Cuenta_Produc_AAPP** (N nodos) → Cuentas productivas AAPP
13. **Salidas_Cuenta_Produc_AAPP_2** (N nodos) → Variante cuentas productivas
14. **Indicadores municipales** (N nodos) → KPIs municipales
15. Plus 2 más de la lista de 17 totales

## 10. Contactos y escalamientos

### 10.1 Equipo de soporte

| Rol | Nombre | Email | Teléfono | Disponibilidad |
|-----|--------|-------|----------|-----------------|
| Product Owner | [Contacto pendiente] | [Completar] | [Completar] | **Información incompleta** |
| Data Engineer (migración) | [Contacto pendiente] | [Completar] | [Completar] | **Información incompleta** |
| Analista de BD (GOBGENER) | [Contacto pendiente] | [Completar] | [Completar] | **Información incompleta** |
| Administrador de red (FILESERVER) | [Contacto pendiente] | [Completar] | [Completar] | **Información incompleta** |

**Acción requerida**: Completar matriz de contactos en `project_config.yaml` (Apartado `contacts`)

### 10.2 Procedure ante fallos críticos

1. **SLA**: Notificar en <2h si NB-02 falla en fase 1-2 (cambios estructura presupuestaria)
2. **Escalation**: Si error persiste tras 3 reintentos, contactar Data Engineer
3. **Fallback**: Usar baseline anterior (última ejecución exitosa de `&Year-1`)

### 10.3 Change Control

Cambios a notebooks:
- Mejora M-001 (rutas hardcodeadas): versión v1.1 (APROBADA, pending aplicación)
- Mejora M-007 (parametrización macros): versión v1.1 (APROBADA, pending aplicación)
- Mejoras M-002, M-003, M-004, M-005, M-006, M-008 (otras entregas): POSTERGADAS

Solicitar cambios via: `[data-team-email]/change-requests`

## 11. Apéndice: Supuestos y limitaciones

### 11.1 Supuestos visibles del plan

1. **Placement ambiguous**: 4 nodos con libref sin resolver (CodeTask-D6fqrxqReNOK5Xch, CodeTask-cbwaC9NShYE8mV6x, CodeTask-oLKJ5g7DvhYHuBME, CodeTask-S9YMDIdQqTumexhp, Query-YHeDzXnzld6fOVfj)
   - Strategy actual: `pandas` (baja tabla completa a memoria)
   - Riesgo: Si GOBGENER.EJECUCION > 500M filas, OOM
   - Resolución: Determinar si libref es BD ó archivo en entrevista B4b

2. **Macro variables sin inicialización**: 37 macros sin valor por defecto
   - Declarar en `project_config.yaml` ó inyectar vía CLI

3. **Intervenciones manuales**: 3 pausas en Fase 3, 4, 5
   - Usuario responsable: Analista (parámetro `Analista`)
   - SLA: <24h por revisión

4. **Rutas hardcodeadas**: 17 nodos con rutas absolutas
   - Pending mejora M-001 (v1.1)
   - Bloqueador para portabilidad multi-ambiente

### 11.2 Limitaciones conocidas

1. **Validación de integridad referencial**: No automatizada
   - Mitigación: Revisar CHECK tables post-ejecución (Sección 6)

2. **Traceability de cambios**: Sin audit trail de clasificaciones manuales
   - Mitigación: Guardar versión versionada de cada Excel (propuesta_ANALITIC_VAR_2024_v1.xlsx, v2, etc.)

3. **Reintento automático**: No disponible para fases con pausa manual
   - Mitigación: Usar `--resume-from` explícitamente

4. **Rollback**: No hay punto de recuperación entre fases
   - Mitigación: Mantener backup de tablas GOBGENER pre-ejecución
