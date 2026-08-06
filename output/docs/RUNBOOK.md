# Runbook: Ejecución Operativa de la Migración Proc_Salidas_Gob_REV

## 1. Descripción General

Este runbook documenta los procedimientos día a día para ejecutar, validar y resolver incidencias de la migración del proyecto **Proc_Salidas_Gob_REV** desde SAS a Python. La entrega cubre **4 flujos migrables** de un total de 16 flujos del proyecto. Los flujos diferidos (13 en esta entrega: AUTOEXEC, Salida CG coy, Salida CG Imputa, Salida CNF trim, Salidas CNF anual y COFOG, Salida_anual para componente especif, Proceso Sit_Patri_MUN, Proceso Ejecución Municipal CGR, Traspasos_info, Salida_CF_GC, Salida_DCNA, Salidas_Cuenta_Produc_AAPP, Salidas_Cuenta_Produc_AAPP_2, Indicadores municipales) se migran en lotes posteriores.

## 2. Entorno y Requisitos Previos

### 2.1 Dependencias de Software
- **Python**: 3.9 o superior
- **Librerías críticas**: pandas, numpy, sqlalchemy, pyodbc (para SQL Server), openpyxl (lectura/escritura Excel)
- **Kernel de notebooks**: JupyterLab o equivalente
- **Gestor de dependencias**: pip (ver `requirements.txt` en el repositorio)

### 2.2 Acceso a Datos
- **Base de datos principal**: SQL Server con schema `GOBGENER` (lectura/escritura)
- **Librefs SAS mapeadas**:
  - `GOBGENER`: tablas centrales de ejecución presupuestaria (lectura/escritura)
  - `WORK`: tablas temporales en sesión (creadas/destruidas durante ejecución)
  - `DCV`: tabla externa `MONEDAS_MENSUAL` (lectura)
- **Archivos compartidos**: rutas UNC para importación/exportación Excel (ver sección 2.3)

### 2.3 Configuración de Rutas
El proyecto utiliza las siguientes rutas (hardcodeadas en los notebooks; resolver vía config-file en lotes posteriores):
- Datos de entrada: `\\FILESERVER\VOLM\GEM\050_DCNI\...` (SAS/Excel)
- Datos SAS legacy: `/sasdata/BCCH/...` (logs, auditoría)
- Output temporal: tablas en memoria WORK (sesión Jupyter)

### 2.4 Parámetros Requeridos
Los siguientes macro variables **DEBEN** inicializarse antes de cada run:
- **Year**: año de análisis (entero, ej: 2024). Sin defecto → **requiere asignación en entrevista B4**.
- **Mes**: mes de análisis (1-12). Sin defecto → **requiere asignación**.
- **Comp1–Comp7**: componentes de agregación presupuestaria (códigos categóricos). Sin defecto → **requiere asignación**.
- **Mes_imp1–Mes_imp12**: impactos mensuales de imputaciones (booleanos). Sin defecto → **requiere asignación**.
- **Moneda**: moneda de análisis (default: CLP). Sin defecto → **requiere asignación**.
- **PACAPR1–PACAPR7**: partidas/capítulos de análisis (códigos). Sin defecto → **requiere asignación**.
- **Analista**: identificador de usuario/analista responsable. Sin defecto → **requiere asignación**.

**NOTA CRÍTICA**: En la primera ejecución de cada lote, estos parámetros deben ser declarados explícitamente en la celda `parameters` del notebook maestro o importados de `project_config.yaml`.

## 3. Estructura de Salida (Notebooks y Artifacts)

### 3.1 Notebooks Generados (Orden Lógico de Ejecución)

| Secuencia | Notebook | Flujos Incluidos | Nodos | Descripción Breve |
|-----------|----------|------------------|-------|-------------------|
| 1 | `NB-01_autoexec.ipynb` | AUTOEXEC (diferido) | 3 | Inicialización de libreras SAS, procesamiento de tipos de cambio (MONEDAS_MENSUAL). **NO ejecutar en este lote.** |
| 2 | `NB-02_proceso_ejecucion_gc_cgr.ipynb` | Proceso Ejecución GC CGR | 31 | Validación y clasificación de datos CGR: nuevas entidades, analíticos fijos/variables, TCONS, estructuras de expansión (MM, MIXTAS_M, MGCG, MGG), COFOG. **EJE CENTRAL.** |
| 3 | `NB-03_proceso_ejec_gc_dipres.ipynb` | Proceso Ejec GC DIPRES | 10 | Validación análoga para ejecución DIPRES: clasificación de analíticos, expansiones, matrices TCONS. |
| 4 | `NB-04_salida_cg_coy.ipynb` | Salida CG coy (diferido) | 14 | Indicadores de coyuntura combinando CGR + DIPRES. **NO ejecutar en este lote.** |
| … | (13 flujos diferidos) | Varios | — | Ejecutarse en lotes posteriores. |

**Ejecución obligatoria en esta entrega**: `NB-02_*` y `NB-03_*`.  
**NO ejecutar**: `NB-01_*`, `NB-04_*`, ni ningún notebook de los 13 flujos diferidos.

### 3.2 Script de Orquestación

- **`run_all.py`**: Ejecuta secuencialmente los notebooks aprobados con papermill.
  - **Invocación**: `python run_all.py --year 2024 --mes 12 --comp1 C1_VALUE ... --analista USUARIO`
  - **Parámetros**: mapea macro variables SAS a parámetros Jupyter.
  - **Logging**: registra inicio/fin de cada notebook, errores, tiempos de ejecución en `logs/run_all.log`.

## 4. Orden de Ejecución y Flujo Operativo

### 4.1 Secuencia Normal (Sin Incidencias)

```
1. Preparación (5–10 min)
   a) Verificar conectividad a BD GOBGENER (SQL Server)
   b) Confirmar que todas las tablas input existen:
      - GOBGENER.EJECUCION, GOBGENER.ENTIDADES
      - GOBGENER.ANALIT_TCONS, GOBGENER.COFOG
      - GOBGENER.CR18_ENTID_DIP, GOBGENER.EST_EXP_MM, etc.
      (ver lineage en `lineage.md`)
   c) Inicializar parámetros: Year, Mes, Comp1–7, Mes_imp1–12, Moneda, PACAPR1–7, Analista

2. Ejecución NB-02_proceso_ejecucion_gc_cgr (30–45 min)
   a) Ejecutar: jupyter nbconvert --to notebook --execute NB-02_*.ipynb \
                --ExecutePreprocessor.timeout=3600
   b) O usar papermill: papermill NB-02_*.ipynb output_nb.ipynb \
                       -p Year 2024 -p Mes 12 -p Comp1 VALUE1 ...
   c) Salidas WORK: COMPARA_PACAPR, NUEVAS_ENTIDADES, ANALIT_FIJO_CLAS, 
      ANALIT_VAR_CLAS, ANALIT_TCONS, EST_EXP_MM, EST_EXP_MGCG, etc. (63+ tablas)
   d) Salidas GOBGENER: tabla se actualizan in-place
      - ENTIDADES (nuevas entidades incorporadas)
      - ANALIT_TCONS, CR18_T_SCN_1, CR18_T_SCN_2 (clasificaciones)
      - COFOG, EST_EXP_MM, EST_EXP_MGCG, EST_EXP_MGG, EST_EXP_MIXTAS_M

3. Validación Post-NB-02 (10–15 min)
   a) Verificar filas INSERT/UPDATE en GOBGENER tables:
      SELECT COUNT(*) FROM GOBGENER.ENTIDADES WHERE YEAR = &Year;
      SELECT COUNT(*) FROM GOBGENER.ANALIT_TCONS WHERE YEAR = &Year;
   b) Revisar archivos Excel exportados (si los hay):
      - CHECK_ANALIT_FIJO_CLAS_2.xlsx (analíticos sin clasificar)
      - CHECK_ANALIT_VAR_CLAS_5.xlsx (propuestas para revisión manual)
      - CHECK_TCONS_FALT.xlsx (TCONS sin estructura)
   c) Si hay filas "REV" (revision pending), contactar a responsable (ver sección 5)

4. Ejecución NB-03_proceso_ejec_gc_dipres (20–30 min)
   a) Depende de salidas de NB-02 (ENTIDADES, ANALIT_FIJO_CLAS, COFOG, etc.)
   b) Ejecutar análogamente: papermill NB-03_*.ipynb ... (mismos parámetros)
   c) Salidas WORK: ANALIT_ENTIDAD_VAR_D, CHECK_ACTIV_ENTID_DIP, etc. (40+ tablas)
   d) Salidas GOBGENER: análogas a NB-02, scope DIPRES

5. Validación Post-NB-03 (10 min)
   a) Verificar integridad de transacciones TCONS+DIPRES:
      SELECT COUNT(*) FROM GOBGENER.CR18_ENTID_DIP_Y WHERE YEAR = &Year;
   b) Cruzar recuentos CGR vs DIPRES (compara_partida, compara_capitulo, etc.)

6. Finalización (2–3 min)
   a) Archivar logs: cp logs/run_all.log logs/run_&Year._&Mes.log
   b) Exportar resumen de ejecución: tablas CHECK_* a CSV para auditoría
   c) Notificar a responsable de cierre
```

### 4.2 Parámetros por Caso de Uso

#### Caso A: Ejecución Mensual Rutinaria (Gobierno Coyuntura)
```
python run_all.py \
  --year 2024 --mes 12 \
  --comp1 COMPONENTE_A --comp2 COMPONENTE_B ... --comp7 COMPONENTE_G \
  --mes_imp1 1 --mes_imp2 1 ... --mes_imp12 0 \
  --moneda CLP --pacapr1 1000 --pacapr2 2000 ... --pacapr7 7000 \
  --analista USUARIO_OPERACION
```
**Tiempo estimado**: 1.5–2 horas (incluye exportación Excel para revisión).

#### Caso B: Reprocessing Histórico (Auditoría)
```
python run_all.py \
  --year 2023 --mes 12 \
  --comp1 ... --analista USUARIO_AUDITORIA
  # Nota: meses_imp pueden variar; consultar acta de cierre del periodo.
```
**Tiempo estimado**: 2–2.5 horas (incluye validaciones estrictas).

#### Caso C: Corrección de Clasificaciones Manual
```
# 1. Editar Excel importado (CHECK_ANALIT_VAR_CLAS_5.xlsx)
# 2. Re-ejecutar NB-02 solo desde la celda de importación:
papermill NB-02_*.ipynb --start-cell "5b-Clasif Analiticos Var_mod" \
  --end-cell "7f-Check Est_Exp_MGG TCons_mod" -p Year 2024 -p Mes 12 ...
# 3. Validar de nuevo.
```

## 5. Validación Post-Ejecución

### 5.1 Checklist de Verificación

- [ ] **Conectividad BD**: SELECT COUNT(*) FROM GOBGENER.ENTIDADES retorna > 0
- [ ] **Tablas WORK creadas**: 63+ tablas temporales en sesión (columna 'output_datasets' del plan)
- [ ] **GOBGENER.ENTIDADES actualizada**: nuevas entidades del año registradas
- [ ] **GOBGENER.ANALIT_TCONS actualizada**: clasificaciones TCONS nuevas > 0
- [ ] **Archivos Excel**: 
  - [ ] Importados (si corresponde): filas revisadas = filas importadas
  - [ ] Exportados (si hay faltantes): archivos creados en output/
  - [ ] Revisión manual completada: nuevas filas clasificadas aprobadas
- [ ] **Logs sin errores críticos**: `grep -i "error\|exception" logs/run_all.log` → vacío
- [ ] **Recuentos cruzados CGR vs DIPRES**:
  - SELECT COUNT(*) FROM GOBGENER.EJECUCION WHERE YEAR = &Year;
  - SELECT COUNT(*) FROM GOBGENER.EJEC_DIPRES WHERE YEAR = &Year;
  - Diferencia esperada: ±5% (variación normal por ajustes)
- [ ] **Duración de ejecución**: 1.5–2.5 horas (reportar si > 3 horas)

### 5.2 Archivos de Salida Esperados (Por Notebook)

#### NB-02_proceso_ejecucion_gc_cgr
- **Tablas WORK** (63+): COMPARA_PACAPR, NUEVAS_ENTIDADES, ANALIT_FIJO_CLAS, CHECK_ANALIT_REV, etc.
- **Tablas GOBGENER** actualizadas: ENTIDADES, ANALIT_TCONS, CR18_T_SCN_1/2, COFOG, EST_EXP_MM, EST_EXP_MGCG, EST_EXP_MGG, EST_EXP_MIXTAS_M
- **Archivos Excel** (si hay faltantes):
  - `CHECK_ANALIT_FIJO_CLAS_2.xlsx` → analíticos fijos sin clasificación
  - `CHECK_ANALIT_VAR_CLAS_5.xlsx` → propuesta clasificación variables (requiere revisión)
  - `CHECK_TCONS_FALT.xlsx` → TCONS sin estructura (requiere definición)
  - `CHECK_EST_EXP_MM.xlsx`, `CHECK_EST_EXP_MGCG.xlsx`, `CHECK_EST_EXP_MGG.xlsx` → expansiones nuevas

#### NB-03_proceso_ejec_gc_dipres
- **Tablas WORK** (40+): ANALIT_ENTIDAD_VAR_D, CHECK_ACTIV_ENTID_DIP, CRUCE_FIJO, CRUCE_VAR, etc.
- **Tablas GOBGENER** actualizadas: CR18_ENTID_DIP_Y, CR18_T_SCN_1/2 (scope DIPRES), EST_EXP_MIXTAS_M, EST_EXP_MM

## 6. Procedimientos de Resolución de Incidencias

### 6.1 Error: "No module named 'pyodbc'"

**Síntoma**: Excepción al conectar a SQL Server.

**Resolución**:
```bash
pip install pyodbc
# Si usa conda:
conda install pyodbc
# En Windows, requiere driver ODBC SQL Server: descargar de Microsoft docs
```

### 6.2 Error: "Table GOBGENER.ENTIDADES not found"

**Síntoma**: Excepción en célula de lectura de datos.

**Resolución**:
1. Verificar conectividad: `sqlcmd -S SERVER_NAME -U USER -P PASS -Q "SELECT COUNT(*) FROM GOBGENER.ENTIDADES"`
2. Si falla, contactar a DBA (sección 7).
3. Si pasa, verificar que el notebook use la conexión correcta:
   ```python
   # En la celda de conexión:
   engine = create_engine('mssql+pyodbc://USER:PASS@SERVER/DATABASE?driver=ODBC+Driver+17+for+SQL+Server')
   ```

### 6.3 Error: "File not found: \\FILESERVER\VOLM\..."

**Síntoma**: Excepción al importar Excel desde ruta UNC.

**Resolución**:
1. Verificar acceso a red: `ping FILESERVER`
2. Si no alcanza, contactar a Network team.
3. Si alcanza, verificar permisos: `ls -la \\FILESERVER\VOLM\...` (o explorador Windows)
4. Si permisos OK, verificar que la ruta en el notebook sea exacta (sin espacios extra, mayúsculas).

### 6.4 Error: "Timeout: execution took > 3600 seconds"

**Síntoma**: Notebook no termina en 1 hora.

**Resolución**:
1. **Aumentar timeout en papermill**:
   ```bash
   papermill NB-02_*.ipynb output.ipynb -p Year 2024 \
     --execute-timeout=7200  # 2 horas
   ```
2. **Identificar cuello de botella**:
   - Revisar logs del notebook: ¿en qué celda se detiene?
   - Si es PROC SQL: verificar que la BD no esté bajo carga alta
   - Si es lectura pandas: tabla muy grande → considerar filtraje pre-ejecución
3. **Contactar a DBA** si sospecha lock en tabla o query lenta.

### 6.5 Error: "PRIMARY KEY constraint violated: Duplicate key in GOBGENER.ANALIT_TCONS"

**Síntoma**: Excepción al INSERT/UPDATE en GOBGENER durante celda de clasificación.

**Resolución**:
1. **Verificar registros duplicados antes de insertar**:
   ```python
   # En notebook:
   df_new = df_new.drop_duplicates(subset=['C_CUENTA', 'C_ITEM', 'YEAR'])
   ```
2. **Si persiste**: ejecutar celda de DELETE primero para limpiar sesión anterior:
   ```sql
   DELETE FROM GOBGENER.ANALIT_TCONS 
   WHERE YEAR = &Year AND C_ASIGNACION = 'TMP_SESSION_ID';
   ```
3. **Contactar a responsable de BD** si el problema es structural (tabla corrupta).

### 6.6 Error: "Excel file has unsupported format or is corrupted"

**Síntoma**: Error al leer CHECK_ANALIT_VAR_CLAS_5.xlsx tras edición manual.

**Resolución**:
1. **Verificar formato**: el archivo debe estar en .xlsx (no .xls).
2. **Regenerar Excel**:
   - Ejecutar NB-02 hasta celda "5a-Check Analiticos Var_mod" nuevamente.
   - Editar el Excel recién generado (más fresco).
3. **Si el usuario editó manualmente**: guardar con "Archivo → Guardar Como → Formato Excel 2007-365 (.xlsx)".

### 6.7 Inconsistencia: "Recuento de filas CGR vs DIPRES difiere en >10%"

**Síntoma**: Validación post-ejecución muestra desigualdad anormal.

**Resolución**:
1. **Verificar que ambos notebooks usaron el mismo Year y Mes**:
   ```python
   # En ambos notebooks, celda 'parameters':
   Year = 2024
   Mes = 12
   ```
2. **Cruzar tablas de validación**:
   ```sql
   SELECT YEAR, COUNT(*) FROM GOBGENER.EJECUCION GROUP BY YEAR;
   SELECT YEAR, COUNT(*) FROM GOBGENER.EJEC_DIPRES GROUP BY YEAR;
   ```
3. **Si la diferencia es esperada** (datos fuente incompletos): documentar en acta y proceder.
4. **Si sospecha error en mapeo**: contactar a analista de validación (sección 7).

### 6.8 Warning: "Placement ambiguous in CodeTask-D6fqrxqReNOK5Xch → strategy pandas"

**Síntoma**: Mensaje en log; ejecución es exitosa pero con riesgo potencial.

**Resolución**:
- **Contexto**: MONEDAS_MENSUAL se descarga entera a memoria. Verificar que la tabla no supere 1 GB en BD.
- **Si es < 100 MB**: ignorar, performance es aceptable.
- **Si es > 1 GB**: reportar a DevOps para optimizar strategy a sql_pushdown en siguiente lote (M-003 rechazada, pero aplicable aquí).

## 7. Contactos y Escaladas

| Rol | Nombre | Contacto | Disponibilidad | Responsabilidades |
|-----|--------|----------|-----------------|-------------------|
| **Responsable de Proceso** | [COMPLETAR] | [COMPLETAR] | L–V 8–18h | Supervisión ejecutiva, parámetros de negocio (Comp1–7, PACAPR1–7), decisiones de revisión manual |
| **Operador de Notebooks** | [COMPLETAR] | [COMPLETAR] | L–V 8–18h, on-call sab | Ejecución diaria, validación de salidas, gestión de incidencias operativas |
| **Analista de Datos** | [COMPLETAR] | [COMPLETAR] | L–V 9–17h | Revisión de clasificaciones Excel, resolución de inconsistencias lógicas, auditoría |
| **DBA / SQL Server Admin** | [COMPLETAR] | [COMPLETAR] | L–V 8–18h, emergencias 24/7 | Connectividad BD, permisos, performance de queries, locks, backups |
| **Network / IT** | [COMPLETAR] | [COMPLETAR] | L–V 8–18h | Acceso a rutas UNC, permisos compartidos, conectividad FILESERVER |
| **Responsable de Migración (DevOps)** | [COMPLETAR] | [COMPLETAR] | L–V 9–17h | Gestión de infraestructura Jupyter, versionado git, CI/CD de notebooks |

**NOTA CRÍTICA**: Las filas en negrita deben completarse en entrevista B4 (decisiones finales) o antes del go-live en producción.

## 8. Parámetros de Configuración por Ambiente

### 8.1 Desarrollo (DEV)
- **BD**: SQL Server DEV (servidor, credenciales en `config_dev.ini`)
- **Timeout**: 3600 segundos (notebooks largos permitidos)
- **Logging**: VERBOSE (incluye debug SQL)
- **Validación Excel**: desactivada (permitir archivos parcialmente editados)

### 8.2 Testing (TEST)
- **BD**: SQL Server TEST (dataset snapshot de PROD del mes anterior)
- **Timeout**: 5400 segundos (1.5x DEV)
- **Logging**: INFO (eventos principales)
- **Validación Excel**: parcial (check formato, no contenido)

### 8.3 Producción (PROD)
- **BD**: SQL Server PROD
- **Timeout**: 7200 segundos (2 horas máximo)
- **Logging**: WARNING (solo errores)
- **Validación Excel**: STRICT (schema + dominio)
- **Backup**: ejecutar antes de cada run → `backup_before_run.sql`

## 9. Cálculo de Parámetros: Macro Variables SAS → Python

Los siguientes parámetros **son macro variables SAS sin valor por defecto**. Deben inicializarse en la entrevista B4 o en archivo de configuración:

### 9.1 Year (Año de Análisis)
- **Tipo**: ENTERO (1900–2100)
- **Origen**: típicamente &SYSDATE (año actual) o especificado en parámetro de ejecución
- **Uso**: filtro WHERE en todas las queries (YEAR = &Year)
- **Ejemplo**: Year = 2024

### 9.2 Mes (Mes de Análisis)
- **Tipo**: ENTERO (1–12)
- **Origen**: típicamente mes actual o posterior para cierres
- **Uso**: filtro MES = &Mes en transacciones, cálculo de trimestre
- **Ejemplo**: Mes = 12 (cierre anual)

### 9.3 Comp1–Comp7 (Componentes de Agregación Presupuestaria)
- **Tipo**: STRING (códigos categóricos de clasificación de gasto)
- **Origen**: tabla de parámetros de negocio GOBGENER (no especificada en EGP)
- **Uso**: GROUP BY y cálculos de agregación en salidas finales
- **Ejemplo**: Comp1 = 'PERSONAL', Comp2 = 'BIENES', ..., Comp7 = 'TRANSFERENCIAS'
- **NOTA CRÍTICA**: sin especificación de dominio válido → **REQUIERE ACTA DE NEGOCIO**

### 9.4 Mes_imp1–Mes_imp12 (Imputaciones Mensuales)
- **Tipo**: BOOLEANO (0=No, 1=Sí)
- **Origen**: decisión mensual sobre qué periodos incluyen imputaciones
- **Uso**: filtro de transacciones "permanentes" vs "transitorias"
- **Ejemplo**: Mes_imp1=1, Mes_imp2=1, ..., Mes_imp12=1 (todos los meses imputados)
- **NOTA**: interconectado con lógica de nodos CodeTask-23lpner3oIe465S4, CodeTask-dzljPfKJnYXDrIyx

### 9.5 Moneda
- **Tipo**: STRING (código de 3 dígitos ISO 4217)
- **Origen**: tabla MONEDAS_MENSUAL (DCV.MONEDAS_MENSUAL)
- **Uso**: conversión de valores en PROC SQL Monedas_Mensual (NB-01, diferido)
- **Ejemplo**: Moneda = 'CLP' (pesos), 'USD' (dólares)

### 9.6 PACAPR1–PACAPR7 (Partidas/Capítulos de Análisis)
- **Tipo**: STRING (códigos de presupuesto; formato: NNN ó NNNN)
- **Origen**: maestro de partidas/capítulos vigentes (tabla no especificada)
- **Uso**: filtro de desglose en salidas finales (no en este lote, pero requerido para NB-04)
- **Ejemplo**: PACAPR1 = '1000' (servicios personales), PACAPR2 = '2000' (bienes), etc.

### 9.7 Analista
- **Tipo**: STRING (código de usuario o nombre)
- **Origen**: variable de ambiente o parámetro de run
- **Uso**: trazabilidad en logs y auditoría (quién ejecutó)
- **Ejemplo**: Analista = 'JPEREZ' ó 'juan.perez@gobierno.cl'

**DECLARACIÓN OBLIGATORIA**: agregar al archivo `project_config.yaml`:
```yaml
run:
  macro_params:
    Year: 2024              # EDIT: año de proceso
    Mes: 12                 # EDIT: mes de proceso
    Comp1: PERSONAL         # EDIT: según matriz de componentes
    Comp2: BIENES           # EDIT: 
    Comp3: SERVICIOS        # EDIT:
    Comp4: TRANSFERENCIAS   # EDIT:
    Comp5: BIENES_INV       # EDIT:
    Comp6: OBRAS_PUBLICAS   # EDIT:
    Comp7: OTROS            # EDIT:
    Mes_imp1: 1             # EDIT: 0 o 1
    Mes_imp2: 1             # EDIT: 0 o 1
    # ... Mes_imp3 a Mes_imp12 ...
    Moneda: CLP             # EDIT: CLP, USD, etc.
    PACAPR1: 1000           # EDIT: códigos de partida/capítulo
    PACAPR2: 2000           # EDIT:
    # ... PACAPR3 a PACAPR7 ...
    Analista: USUARIO       # EDIT: responsable de run
```

## 10. Auditoría y Trazabilidad

### 10.1 Archivos de Log

- **`logs/run_all.log`**: log maestro de ejecución (inicio/fin, timeouts, errores)
- **`logs/run_&YEAR._&MES.log`**: snapshot de log por período (archivado post-run)
- **Notebook output**: celdas ejecutadas + times; auto-guardadas por papermill

### 10.2 Tablas de Control (CHECK_*)

Los siguientes archivos WORK registran eventos de validación y son críticos para auditoría:

- **CHECK_ACTIV_ENTID**: verificación de entidades con actividad
- **CHECK_ANALIT_FIJO**: control de analíticos fijos clasificados
- **CHECK_ANALIT_REV**: analíticos pendientes de revisión
- **CHECK_TCONS**: validación de transacciones consolidables
- **CHECK_EST_EXP_MM, CHECK_EST_EXP_MGCG, CHECK_EST_EXP_MGG**: estructuras de expansión creadas/validadas

**Exportar a CSV post-run**: 
```python
for table_name in ['CHECK_ACTIV_ENTID', 'CHECK_ANALIT_FIJO', 'CHECK_ANALIT_REV', ...]:
    df = pd.read_sql(f'SELECT * FROM #{table_name}', engine)
    df.to_csv(f'audit/{table_name}_{Year}_{Mes}.csv', index=False)
```

### 10.3 Acta de Ejecución

Completar y archivar tras cada run:

```markdown
## Acta de Ejecución Proc_Salidas_Gob_REV — Lote 1

**Fecha**: [completar]
**Responsable**: [Analista]
**Período**: Año &Year, Mes &Mes
**Parámetros**:
- Comp1–7: [valores]
- Mes_imp1–12: [valores]
- Moneda: [valor]
- PACAPR1–7: [valores]

**Notebooks Ejecutados**:
- [x] NB-02_proceso_ejecucion_gc_cgr (tiempo: XXm)
- [x] NB-03_proceso_ejec_gc_dipres (tiempo: XXm)

**Validaciones**:
- [x] Conectividad BD: OK
- [x] Tablas GOBGENER actualizadas: entidades+XXX filas
- [x] Archivos Excel revisados: [sí/no, descripción]
- [x] Inconsistencias CGR vs DIPRES: [resumen]
- [x] Logs sin errores críticos: OK

**Observaciones**: [libre]

**Firma**: [Operador] — [Responsable] — [Auditoría]
```

## 11. Siguiente Lote: Flujos Diferidos

La siguiente entrega incluirá los 13 flujos diferidos del proyecto:

1. **AUTOEXEC** (NB-01): 3 nodos, inicialización de libreras + MONEDAS_MENSUAL
2. **Salida CG coy** (NB-04): 14 nodos, indicadores de coyuntura (CGR+DIPRES)
3. **Salida CG Imputa**: 16 nodos, imputaciones de gobierno
4. **Salida CNF trim**: 12 nodos, cuenta nacional trimestral
5. **Salidas CNF anual y COFOG**: 18 nodos
6. **Salida_anual para componente especif**: 8 nodos
7. **Proceso Sit_Patri_MUN**: 22 nodos
8. **Proceso Ejecución Municipal CGR**: 15 nodos
9. **Traspasos_info**: 11 nodos
10. **Salida_CF_GC**: 9 nodos
11. **Salida_DCNA**: 13 nodos
12. **Salidas_Cuenta_Produc_AAPP**: 10 nodos (variante 1)
13. **Salidas_Cuenta_Produc_AAPP_2**: 10 nodos (variante 2)
14. **Indicadores municipales**: 14 nodos

**Planificación**: entrega mensual de 2–3 flujos por lote (estimado 4–6 meses para completar 16/16).
