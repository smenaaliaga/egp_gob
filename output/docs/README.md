# README: Migración de Proc_Salidas_Gob_REV a Python

## Qué es esta migración

La migración **Proc_Salidas_Gob_REV_mig** traduce flujos de procesamiento de ejecución presupuestaria de SAS a Python/Jupyter Notebooks. El proyecto original opera en SAS y gestiona datos de ejecución presupuestaria del gobierno central chileno, produciendo tablas de validación, clasificación y reportes de cierre contable para análisis de variabilidad de divisas, cambios estructurales presupuestarios (entidades, analíticos, transferencias) y salidas analíticas de consumo de gobierno.

Esta entrega cubre **2 flujos de un total de 17**, que suman **33 nodos operacionales**:
- **AUTOEXEC**: Extrae y agrega datos de tipos de cambio (3 nodos)
- **Proceso Ejecución GC CGR**: Valida y clasifica ejecución presupuestaria del gobierno central con 31 nodos de validación y enriquecimiento

Los **15 flujos restantes** se migran en lotes posteriores (listados en la sección "Diferidos").

## Qué produce esta entrega

La salida de la migración genera:

1. **Notebooks Jupyter** (`.ipynb`):
   - `NB-01_autoexec.ipynb`: Procesamiento de tasas de cambio mensuales y trimestrales
   - `NB-02_proceso_ejecucion_gc_cgr.ipynb`: Validación y clasificación de ejecución CGR/DIPRES, detección de nuevas entidades, analíticos y cambios estructurales

2. **Script de orquestación** (`run_all.py`):
   - Ejecuta secuencialmente los notebooks del proyecto
   - Parametriza períodos (año, meses, componentes)
   - Maneja dependencias entre flujos
   - Reporta errores y trazabilidad

3. **Tablas de salida** (persistidas en BD o memoria según estrategia):
   - Tablas de trabajo (`WORK.*`): Agregados mensuales/trimestrales, validaciones intermedias, comparativas, checks de consistencia
   - Tablas de negocio (`GOBGENER.*`): Maestros actualizados de entidades, estructuras presupuestarias, clasificaciones COFOG y de actividad
   - Reportes Excel: Propuestas de clasificación de nuevas entidades, analíticos variables y transferencias (destinados a revisión manual)

## Estructura de output

```
output/
├── NB-01_autoexec.ipynb
├── NB-02_proceso_ejecucion_gc_cgr.ipynb
├── run_all.py
├── project_config.yaml              # Configuración centralizada de parámetros
├── logs/
│   ├── NB-01_autoexec_YYYY-MM-DD_HH-MM-SS.log
│   └── NB-02_proceso_ejecucion_gc_cgr_YYYY-MM-DD_HH-MM-SS.log
└── data/
    ├── propostas_entidades_YYYY_MM_DD.xlsx
    ├── propostas_analiticos_var_YYYY_MM_DD.xlsx
    └── propostas_transferencias_YYYY_MM_DD.xlsx
```

## Cómo correr

### Requisitos previos

**Python:**
- Python 3.8+ (3.10+ recomendado)
- Paquetes requeridos:
  ```
  pandas>=1.3.0
  sqlalchemy>=1.4.0
  pyodbc>=4.0.32 (conexión MSSQL)
  openpyxl>=3.8.0 (lectura/escritura Excel)
  jupyter>=1.0.0
  ```

**Base de datos:**
- SQL Server 2016+ (librerías GOBGENER, DCNIDCNA, DCV, GOB)
- Credenciales configuradas en `project_config.yaml` o variables de entorno
- Acceso lectura: GOBGENER, DCV, DCNIDCNA
- Acceso escritura: GOBGENER (actualización de maestros), WORK (tablas temporales)

**Conexión de red:**
- Servidor SQL Server accesible desde máquina de ejecución
- Permisos de lectura de librerías origen
- Permisos de escritura en base TRABAJO y GOBGENER

### Pasos de ejecución

#### Opción 1: Script automatizado (recomendado)

```bash
# 1. Configurar parámetros en project_config.yaml
cd output
nano project_config.yaml
# Editar:
#   - database.host, port, user, password
#   - run.year (ej: 2024)
#   - run.macro_params.Mes (ej: 12 para diciembre)

# 2. Ejecutar
python run_all.py

# 3. Revisar logs
tail -f logs/run_all.log
```

#### Opción 2: Notebooks interactivos (desarrollo/debugging)

```bash
# 1. Iniciar Jupyter
cd output
jupyter notebook

# 2. Abrir NB-01_autoexec.ipynb
# - Ejecutar celda "parameters" (inyecta Year, Mes, Moneda, etc.)
# - Correr celdas en orden (↑↓ secuencial)
# - Inspeccionar outputs intermedios

# 3. Abrir NB-02_proceso_ejecucion_gc_cgr.ipynb
# - Idem NB-01
# - Revisar Excel de propuestas (data/*.xlsx)
# - Completar clasificaciones manuales si aplica
# - Reimportar desde Excel (celda correspondiente)
```

### Parámetros de ejecución

La celda `parameters` en cada notebook acepta:

| Parámetro | Tipo | Ejemplo | Descripción |
|-----------|------|---------|-------------|
| `Year` | int | 2024 | Año fiscal de ejecución |
| `Mes` | int | 12 | Mes (1–12); usado para filtrados |
| `Moneda` | str | "UF" | Divisa reportada (ej: UF, CLP, USD) |
| `Analista` | str | "jperez" | Usuario ejecutante (para auditoría) |
| `Comp1`–`Comp7` | str | "04001000" | Códigos de partida/capítulo comparados (detectar cambios) |
| `Mes_imp1`–`Mes_imp12` | int | 1 | Meses de imputación temporal (1=enero, etc.) |
| `PACAPR1`–`PACAPR7` | str | "01" | Valores PACAPR de referencia histórica |

Los valores pueden pasarse:
- **Directamente en notebook**: Clic en "▶ Run All" o celda `parameters` antes de "Run Below"
- **Desde archivo de config**: `project_config.yaml` (sección `run.macro_params`)
- **Desde línea de comandos** (si se usa papermill/nbconvert):
  ```bash
  papermill NB-01_autoexec.ipynb output_nb.ipynb -p Year 2024 -p Mes 12
  ```

## Diferidos: Qué NO está en esta entrega

Los **15 flujos siguientes** se migran en lotes posteriores y **NO se ejecutan** desde los notebooks de esta entrega:

1. **Proceso Ejec GC DIPRES** (10 nodos)
2. **Salida CG coy** (14 nodos)
3. **Salida CG Imputa** (no especificado)
4. **Salida CNF trim** (no especificado)
5. **Salidas CNF anual y COFOG** (no especificado)
6. **Salida_anual para componente especif** (no especificado)
7. **Proceso Sit_Patri_MUN** (no especificado)
8. **Proceso Ejecución Municipal CGR** (no especificado)
9. **Traspasos_info** (no especificado)
10. **Salida_CF_GC** (no especificado)
11. **Salida_DCNA** (no especificado)
12. **Salidas_Cuenta_Produc_AAPP** (no especificado)
13. **Salidas_Cuenta_Produc_AAPP_2** (no especificado)
14. **Indicadores municipales** (no especificado)
15. (1 flujo adicional no identificado)

**Estos flujos serán entregados en sprints posteriores.** Si alguno es crítico para su negocio inmediato, contacte al equipo de migración.

## Verificaciones tras la ejecución

Tras correr `run_all.py` o completar un notebook, valide:

1. **Logs sin errores críticos**:
   ```bash
   grep -i "error\|exception" logs/NB-0*.log
   ```
   - Advertencias (warnings) son normales; excepciones detienen la ejecución.

2. **Tablas de salida pobladas**:
   ```sql
   -- En SQL Server
   SELECT COUNT(*) FROM GOBGENER.ENTIDADES;
   SELECT COUNT(*) FROM WORK.COMPARA_PACAPR;
   SELECT COUNT(*) FROM WORK.CIERRE_MES;
   ```
   - Filas > 0 en tablas principales

3. **Archivos Excel generados**:
   ```bash
   ls -la output/data/*.xlsx
   ```
   - `propostas_*.xlsx` deben existir si hay nuevas clasificaciones

4. **Parámetros registrados**:
   - Inspeccionar celda "parameters" del notebook ejecutado
   - Verificar que Year, Mes, Analista coincidan con la intención

5. **Comparativa vs SAS (primera ejecución)**:
   - Exportar resultados de SAS original a CSV
   - Comparar conteos de filas, sumas de columnas numéricas, valores únicos de claves
   - Diferencias admisibles: redondeos, orden de filas (usar `ORDER BY` para normalizarlas)

## Supuestos y limitaciones

### Supuestos visibles

1. **Placement ambiguo resuelto con pandas**:
   - 4 nodos (CodeTask-D6fqrxqReNOK5Xch, CodeTask-cbwaC9NShYE8mV6x, CodeTask-oLKJ5g7DvhYHuBME, CodeTask-S9YMDIdQqTumexhp) leen tablas de librería desconocida (no especificada como BD ni archivo).
   - **Estrategia adoptada**: `pandas` (descarga tabla entera en memoria).
   - **Riesgo**: Si la tabla es >1GB, puede causar OOM. Resolver con SQL pushdown si se identifica la BD.

2. **Macro variables sin inicialización**:
   - 31 macro variables (&Year, &Analista, &Comp1-7, &Mes_imp1-12, &Mes, &Moneda, &PACAPR1-7) carecen de valor predefinido en SAS.
   - **Estrategia adoptada**: Celdas `parameters` en notebooks dejan el valor como `None` si no se proporciona.
   - **Requisito**: Declarar en `project_config.yaml` → `run.macro_params` o inyectar antes de ejecutar.

3. **3 nodos Query ignorados**:
   - Query-fI94dLNL1vAYjQn4, Query-9hK9UXmLqOXfHIKS, Query-7WLH8bv335ANj5w9 no se traducen (sin información de definición en el EGP).
   - **Impacto**: Bajo si las consultas son opcionales; alto si son críticas. Revisar en decisiones.

### Limitaciones conocidas

1. **Redondeos y tipos de datos**:
   - SAS `NUMERIC` → Python `float64` (diferencias en representación en decimales)
   - Usar `ROUND(..., decimales)` en Python si se requiere exactitud financiera

2. **Macros SAS no replicables**:
   - Funciones SAS complejas (CATX, TRANWRD, SUBSTR, SOUNDEX, SPEDIS) se traducen a pandas/numpy
   - Diferencias semánticas menores en manejo de nulos y strings

3. **Excel interactivo**:
   - Propuestas de clasificación se exportan a Excel (NB-02, paso 5a–5b, 6a–6b, 7a–7f)
   - Requieren revisión manual y reimportación por usuario
   - Automatizar validaciones en futuras versiones

4. **Sin control de concurrencia**:
   - Si dos usuarios ejecutan simultáneamente con los mismos parámetros (Year, Mes), pueden sobrescribir tablas
   - Implementar timestamps o bloqueos en futuras versiones

## Contactos y soporte

Para dudas sobre:
- **Contenido de datos**: Responsable de negocio (no especificado en esta entrega)
- **Estructura de notebooks**: Equipo de migración (documento `decisions` + `runbook`)
- **Parámetros de ejecución**: Ver sección "Parámetros de ejecución" y archivo `project_config.yaml`
- **Cambios en tablas fuente**: Revisar documento `lineage` (qué tablas se leen por flujo)

---

**Versión**: 1.0  
**Fecha de generación**: 2026-08-03  
**Estado**: Entrega parcial (2/17 flujos)
