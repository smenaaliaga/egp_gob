# Runbook: Proc_Salidas_Gob_REV_mig

## Propósito
Este runbook documenta el procedimiento operacional día a día para ejecutar la migración de procesos presupuestarios del Gobierno desde SAS a Python. Cubre orden de ejecución, parámetros requeridos, verificaciones post-ejecución, y resolución de fallos comunes.

---

## 1. Descripción General del Proceso

**Proyecto:** Proc_Salidas_Gob_REV_mig  
**Total de notebooks:** 6 (NB-01 a NB-06)  
**Tipo de ejecución:** Secuencial (dependencias de datos entre flujos)  
**Periodos soportados:** Mensual, trimestral, anual  
**Macro parámetros principales:** `Year`, `Analista`, `Comp1-7`, `Mes`, `Mes_imp1-12`, `Moneda`, `PACAPR1-7`

---

## 2. Orden de Ejecución

### Fase 1: Inicialización (NB-01_autoexec.ipynb)
**Nodos:** 3 (Set Libreria, Monedas_Mensual, Programa)  
**Duración esperada:** 2-5 minutos  
**Datos de entrada:** DCV.MONEDAS_MENSUAL  
**Datos de salida:** WORK.CIERRE_MES, WORK.CIERRE_TRIM, WORK.PROM_MES, WORK.PROM_MES_TODAS, WORK.PROM_TRIM

**Acciones:**
1. Ejecutar NB-01_autoexec.ipynb
2. Verificar que se crean todas las 5 tablas WORK temporales
3. Confirmar que las variables de librería Python están inicializadas

**Parámetros requeridos:**
- Ninguno (fase de setup global)

---

### Fase 2: Validación y Clasificación GC-CGR (NB-02_proceso_ejecucion_gc_cgr.ipynb)
**Nodos:** 31 (validación de entidades, analíticos fijos/variables, TCONS, estructuras de expansión)  
**Duración esperada:** 30-45 minutos  
**Datos de entrada:** GOBGENER.EJECUCION, GOBGENER.ENTIDADES, múltiples tablas WORK (68 datasets)  
**Datos de salida:** 99 datasets entre GOBGENER (nuevas entidades, SCN clasificadas) y WORK (checks y tablas intermedias)

**Acciones:**
1. Ejecutar NB-02_proceso_ejecucion_gc_cgr.ipynb
2. **Detenerse tras paso "5b-Clasif Analiticos Var_mod"** para revisión manual de `CHECK_TRANSVAR.xlsx` exportado a disco
   - Archivo se genera en ruta configurada (ver sección 3.1)
   - Revisar que los códigos SCN propuestos sean válidos
   - Completar manualmente las clasificaciones pendientes (C_SCN vacío)
   - Guardar archivo con cambios
3. Continuar ejecución desde "6a-Check Nvas TCons_mod"
4. **Detenerse tras "6a"** para revisar y completar `CHECK_TCONS.xlsx`
5. Continuar hasta "7a-Check Est_Exp_MM TCons_mod"
6. **Detenerse** para completar `EST_EXP_MM.xlsx` (ponderaciones POND por entidad)
7. Continuar hasta "7b-Check Est_Exp_M TCons_mod"
8. **Detenerse** para completar `EST_EXP_MIXTAS_M.xlsx`
9. Ejecutar resto de nodos (7c-d, 8a-b, 9-11) sin interrupciones adicionales

**Parámetros requeridos:**
- `Year` (tipo: entero, ej: 2025): Año de ejecución presupuestaria a procesar
- `Analista` (tipo: string, ej: "JUAN_LOPEZ"): Responsable de validaciones manuales
- Valores por defecto: si no se proporcionan en celda `parameters`, se asumen `None` → **COMPLETAR ANTES DE EJECUTAR**

**Checkpoints de validación:**
- Tras nodo "3b-Clasif Nvas Entidades": verificar que `GOBGENER.ENTIDADES` tiene registros nuevos
- Tras "4b-Clasif Analiticos Predef_mod": revisar `WORK.CHECK_ANALIT_REV` (no debe haber duplicados)
- Tras "6b-Clasif Nvas TCons_mod": confirmar que `GOBGENER.ANALIT_TCONS` aumentó en registros
- Tras "7b": verificar que EST_EXP_MIXTAS_M no tiene ponderaciones duplicadas (suma POND = 1 por clave)

---

### Fase 3: Validación Ejecución GC-DIPRES (NB-03_proceso_ejec_gc_dipres.ipynb)
**Nodos:** 10 (validación anual de DIPRES)  
**Duración esperada:** 10-15 minutos  
**Datos de entrada:** 42 datasets (GOBGENER, WORK de Fase 2)  
**Datos de salida:** 47 datasets (actualización GOBGENER + checks WORK)

**Acciones:**
1. Ejecutar NB-03_proceso_ejec_gc_dipres.ipynb
2. Sin interrupciones (no hay exports Excel en este flujo)
3. Validar al final que `GOBGENER.ENTIDADES` y `GOBGENER.CR18_T_SCN_1/2` no tienen cambios de conteo inesperados

**Parámetros requeridos:**
- `Year` (reutiliza Fase 2): debe ser idéntico al de NB-02

**Checkpoints:**
- Revisar `WORK.CHECK_TCONS_R` y `WORK.CHECK_TCONS_FALT` (deben estar vacíos o con conteos documentados)
- Confirmar que `WORK.TCONS_EST_DEF_M` tiene coherencia (sin valores NULL en POND)

---

### Fase 4: Salida CG Coyuntura (NB-04_salida_cg_coy.ipynb)
**Nodos:** 14 (preparación de indicadores presupuestarios para reportes de coyuntura)  
**Duración esperada:** 20-30 minutos  
**Datos de entrada:** 118 datasets (GOBGENER, WORK consolidados de Fases 2-3)  
**Datos de salida:** 73 datasets WORK (indicadores, ratios, totales por institución)

**Acciones:**
1. Ejecutar NB-04_salida_cg_coy.ipynb
2. Al finalizar, verificar tablas clave:
   - `WORK.RATIOS`: debe tener columnas AÑO, INSTITUCIÓN, INDICADOR_1 a INDICADOR_N
   - `WORK.TOTALES_INST`: consolidado presupuestario por institución
   - No debe haber valores NaN excepto en campos opcionales documentados

**Parámetros requeridos:**
- `Year`: idéntico a Fases 2-3
- `Mes` (tipo: entero 1-12): Mes para análisis de coyuntura (ej: 12 para cierre anual)

**Checkpoints:**
- Verificar que `WORK.TOTALES_INST` tiene al menos N instituciones esperadas (típicamente 40-60 para GC)
- Revisar columnas monetarias en `WORK.RATIOS`: deben estar en millones UF (después de divisor aplicado en M-001)

---

### Fase 5: Salidas Adicionales (NB-05 a NB-06)
**Estado:** Diferidas para lote posterior  
Procesos no incluidos en esta entrega:
- Salida CG Imputa
- Salida CNF trim
- Salidas CNF anual y COFOG
- Salidas especializadas por componente
- Indicadores municipales

Serán traducidos y documentados en siguientes releases.

---

## 3. Configuración de Parámetros

### 3.1 Variables de Ruta (M-001 Aprobada)
Se deben centralizar en archivo `_config.py` en el directorio raíz `/output`:

```python
# _config.py
CONFIG = {
    "excel_export_path": "/output/temp/",  # Ruta donde se guardan .xlsx temporales
    "database_path": {
        "GOBGENER": "postgresql://[host]/gobgener",  # Conectar según env
        "DCV": "postgresql://[host]/dcv"
    },
    "log_path": "/output/logs/",
    "temp_work_path": "/tmp/work_tables/"
}
```

### 3.2 Macro Parámetros Requeridos (M-005 Aprobada)
Crear archivo `_parameters.yaml`:

```yaml
parameters:
  Year: 2025                    # Año ejecución presupuestaria
  Analista: "USUARIO_DEFAULT"   # Responsable de validación manual
  Mes: 12                       # Mes para reportes de coyuntura (1-12)
  Moneda: "UF"                  # Moneda para cálculos (UF/CLP)
  Comp1: 1                      # Pesos para computaciones de indicadores
  Comp2: 0.5
  Comp3: 0.3
  Comp4: 0.2
  Comp5: 0.1
  Comp6: 0.05
  Comp7: 0.025
  Mes_imp1 to Mes_imp12: [1,2,3,4,5,6,7,8,9,10,11,12]  # Meses para imputación
  PACAPR1 to PACAPR7: [valor1, valor2, ...]  # Criterios partida-capítulo-programa
```

**Instrucciones de carga en notebooks:**
- Al inicio de cada notebook, celda `parameters` cargará estos valores:
```python
# Celda 1 de cada notebook
import yaml
with open('../_parameters.yaml') as f:
    params = yaml.safe_load(f)
Year = params['parameters']['Year']
Analista = params['parameters']['Analista']
# ... (resto de parámetros)
```

### 3.3 Validación de Parámetros
Antes de ejecutar Fase 2, verificar:
```python
# Celda de validación (agregar al inicio de NB-02)
assert Year in range(2000, 2100), f"Year inválido: {Year}"
assert isinstance(Analista, str) and len(Analista) > 0, f"Analista vacío: {Analista}"
assert Mes in range(1, 13), f"Mes fuera de rango: {Mes}"
print(f"✓ Parámetros validados: Year={Year}, Analista={Analista}, Mes={Mes}")
```

---

## 4. Verificaciones Post-Ejecución

### Verificación de Integridad de Datos

**Tras completar Fase 2:**
```python
# Validar conteos
from sqlalchemy import inspect

checks = {
    "GOBGENER.ENTIDADES": {"min_rows": 100, "max_rows": 500},
    "GOBGENER.CR18_T_SCN_1": {"min_rows": 500, "max_rows": 5000},
    "GOBGENER.CR18_T_SCN_2": {"min_rows": 500, "max_rows": 5000},
    "GOBGENER.ANALIT_TCONS": {"min_rows": 50, "max_rows": 500}
}

for table, criteria in checks.items():
    count = db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
    assert criteria["min_rows"] <= count <= criteria["max_rows"], \
        f"{table} con {count} rows fuera de rango {criteria}"
    print(f"✓ {table}: {count} rows OK")
```

**Tras completar Fase 3:**
- Validar que `GOBGENER.CR18_ENTID_DIP` y `GOBGENER.CR18_ENTID_DIP_Y` no tengan NULL en columnas clave (C_ANALITICO, C_SCN, C_ITEM)
- Verificar duplicados: `SELECT C_ANALITICO, COUNT(*) FROM GOBGENER.CR18_T_SCN_1 GROUP BY C_ANALITICO HAVING COUNT(*) > 1`
  - Resultado esperado: 0 filas

**Tras completar Fase 4:**
```python
# Validar coherencia de ratios
import pandas as pd
ratios_df = pd.read_sql("SELECT * FROM WORK.RATIOS", db)
assert ratios_df.shape[0] > 0, "WORK.RATIOS vacío"
assert not ratios_df[["AÑO", "INSTITUCIÓN"]].duplicated().any(), \
    "WORK.RATIOS tiene duplicados por AÑO-INSTITUCIÓN"
print(f"✓ WORK.RATIOS: {ratios_df.shape[0]} rows, sin duplicados")
```

---

## 5. Resolución de Fallos Comunes

### Fallo 1: Parámetro `Year` es None tras ejecutar celda `parameters`

**Síntomas:**
- Error: `TypeError: cannot perform reduce with boolean values and integer operands on 'Year' filter`
- O: `Year=None` en salida de celda

**Causa:** Macro parámetro no está declarado en `project_config.yaml` ni en `_parameters.yaml`

**Resolución:**
1. Abrir `_parameters.yaml` (crear si no existe)
2. Agregar entrada:
   ```yaml
   parameters:
     Year: 2025
   ```
3. Recargar notebook e inyectar parámetro manualmente antes de ejecutar:
   ```python
   Year = 2025  # O el año requerido
   ```
4. Documentar en log quién estableció este valor y cuándo

---

### Fallo 2: Error de conexión a base de datos GOBGENER o DCV

**Síntomas:**
- `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server`
- O: `DatabaseError: No libref found for 'GOBGENER'`

**Causa:** Base de datos no está disponible o ruta es incorrecta (M-006 deferred)

**Resolución:**
1. Verificar configuración de conexión en `_config.py`:
   ```python
   # Probar conexión
   from sqlalchemy import create_engine, inspect
   engine = create_engine("postgresql://user:pass@host:5432/gobgener")
   inspector = inspect(engine)
   tables = inspector.get_table_names()
   print(f"Tablas disponibles: {tables}")
   ```
2. Si no hay conexión:
   - Verificar credenciales en `_config.py` (usuario, contraseña, host, puerto)
   - Confirmar que servidor de base de datos está activo: `ping [host]`
   - Consultar a DBA del proyecto por disponibilidad
3. Si falla en NB-02 o NB-03, no continuar a Fase 4 hasta resolución

**Contacto:** [Pendiente completar — contacto DBA]

---

### Fallo 3: Archivo Excel (.xlsx) generado no se abre o está corrompido

**Síntomas:**
- Error al abrir: `"Excel cannot open the file because the file format or file extension is not valid"`
- O: archivo vacío (0 bytes)

**Causa:** Ruta de exportación no existe, permisos insuficientes, o proceso se interrumpió

**Resolución:**
1. Verificar ruta en `_config.py["excel_export_path"]` existe:
   ```python
   import os
   export_path = "/output/temp/"
   os.makedirs(export_path, exist_ok=True)
   ```
2. Verificar permisos: `ls -l [export_path]` debe tener `w` para usuario Python
3. Si archivo existe pero está vacío:
   - Verificar que tabla intermedia (ej: `WORK.CHECK_TRANSVAR`) tiene datos:
     ```python
     import pandas as pd
     check_df = pd.read_sql("SELECT COUNT(*) FROM WORK.CHECK_TRANSVAR", db)
     print(f"Registros a exportar: {check_df.iloc[0,0]}")
     ```
   - Si conteo = 0, investigar por qué no hay datos (ver "Fallo 4")
4. Re-exportar desde celda correspondiente en notebook

---

### Fallo 4: Tabla WORK intermedia está vacía tras paso anterior

**Síntomas:**
- Error: `ProgrammingError: (psycopg2.ProgrammingError) relation "work.check_transvar" does not exist`
- O: Conteo 0 cuando se espera > 0

**Causa:** 
- Nodo previo no se ejecutó completamente, o fallò silenciosamente
- Datos de entrada (GOBGENER.EJECUCION, etc.) están vacíos para el Year dado

**Resolución:**
1. Verificar que nodo anterior completó sin errores:
   - Revisar salida de celda (debe decir "✓ OK" o similar)
   - Ejecutar: `SELECT COUNT(*) FROM WORK.[tabla_esperada]`
2. Si tabla anterior existe pero está vacía:
   - Verificar datos de entrada: `SELECT COUNT(*) FROM GOBGENER.EJECUCION WHERE YEAR = {Year}`
   - Si vacío: Year no tiene datos, usar Year diferente o cargar datos primero
   - Contactar a DBA por carga de datos
3. Si tabla no existe en absoluto:
   - Ir a celda de ese nodo, revisar código SQL/Python
   - Verificar que CREATE TABLE no fue comentado accidentalmente
   - Ejecutar manualmente esa celda
4. Documentar incident: `[fecha] [usuario] Fallo en nodo X, causa Y, resolución Z`

---

### Fallo 5: Datos en Excel importado no se escriben en BD (paso 5b, 6b, 7a-b)

**Síntomas:**
- Se importa Excel sin errores, pero tabla GOBGENER no cambia
- O: `sqlalchemy.exc.IntegrityError: (psycopg2.IntegrityError) duplicate key value violates unique constraint`

**Causa:** 
- Registro ya existe (clave duplicada)
- Validación de datos en Excel falló silenciosamente

**Resolución:**
1. Verificar que Excel tiene validaciones correctas:
   - Columnas esperadas: C_ANALITICO, C_SCN, C_CUP (o según nodo)
   - Sin filas vacías en medio de datos
   - Sin caracteres especiales no permitidos
2. Si ImportError es por duplicados:
   - Revisar lógica de INSERT: debe usar UPSERT (UPDATE si existe, INSERT si no)
   - Código correcto en nodo:
     ```python
     from sqlalchemy.dialects.postgresql import insert
     stmt = insert(table).values(data).on_conflict_do_update(
         index_elements=['C_ANALITICO'],
         set_={"C_SCN": insert(table).excluded.C_SCN}
     )
     db.execute(stmt)
     ```
3. Si validación falla:
   - Revisar columna C_SCN en Excel: valores deben estar en dominio válido
   - Limpiar filas con errores y re-importar
4. Consultar con Analista (parámetro) si hay duda sobre validez de datos

---

### Fallo 6: Parámetro `Analista` no se propaga a checks de verificación

**Síntomas:**
- Columna ANALISTA en CHECK_*.xlsx queda NULL o vacía
- Reportes no rastrean quién revisó qué

**Causa:** Parámetro Analista no está siendo usado en celdas que generan estos checks

**Resolución:**
1. Asegurarse que en celda `parameters` se declara:
   ```python
   Analista = "JUAN_LOPEZ"  # O valor de _parameters.yaml
   ```
2. En cada celda que genera CHECK_*.xlsx, agregar columna:
   ```python
   check_df["ANALISTA_ASIGNADO"] = Analista
   check_df["FECHA_REVISION"] = pd.Timestamp.now()
   ```
3. Re-ejecutar celdas que generan exports

---

## 6. Checklist de Ejecución Completa

Usar antes de cada ciclo de migración:

- [ ] **Pre-ejecución:**
  - [ ] Archivo `_parameters.yaml` existe y contiene Year, Analista, Mes válidos
  - [ ] Archivo `_config.py` apunta a base de datos correcta (DEV/PROD/STAGING)
  - [ ] Conexión a GOBGENER y DCV activa: `python -c "from _config import *; test_db_connection()"`
  - [ ] Directorio `/output/temp/` existe y tiene permisos de escritura
  - [ ] Logs previos archivados (opcional, pero recomendado): `mv /output/logs/*.log /output/logs/archive/`

- [ ] **Fase 1 (NB-01):**
  - [ ] Ejecutar NB-01_autoexec.ipynb
  - [ ] Verificar 5 tablas WORK creadas: CIERRE_MES, CIERRE_TRIM, PROM_MES, PROM_MES_TODAS, PROM_TRIM
  - [ ] Celda final dice "✓ AUTOEXEC Completado"

- [ ] **Fase 2 (NB-02) — Primera pasada:**
  - [ ] Ejecutar hasta nodo "5b-Clasif Analiticos Var_mod"
  - [ ] Archivo CHECK_TRANSVAR.xlsx generado en `/output/temp/`
  - [ ] Abrir Excel, revisar códigos SCN propuestos, completar faltantes
  - [ ] Guardar archivo con cambios
  - [ ] Retomar NB-02, importar Excel
  - [ ] Repetir ciclo para CHECK_TCONS.xlsx, EST_EXP_MM.xlsx, EST_EXP_MIXTAS_M.xlsx
  - [ ] Completar Fase 2 (nodos 9-11)
  - [ ] Verificar `WORK.CHECK_ANALIT_REV`, `WORK.CHECK_TCONS_R`: sin duplicados

- [ ] **Fase 3 (NB-03):**
  - [ ] Ejecutar NB-03_proceso_ejec_gc_dipres.ipynb completa
  - [ ] Verificar `GOBGENER.ENTIDADES` tiene registros nuevos (si procede)
  - [ ] Verificar conteos en `GOBGENER.CR18_T_SCN_1` y `CR18_T_SCN_2`

- [ ] **Fase 4 (NB-04):**
  - [ ] Ejecutar NB-04_salida_cg_coy.ipynb completa
  - [ ] Verificar `WORK.RATIOS`: conteo > 0, sin duplicados
  - [ ] Verificar `WORK.TOTALES_INST`: conteo ≥ 40

- [ ] **Post-ejecución:**
  - [ ] Ejecutar script de validación (ver sección 4)
  - [ ] Revisar logs: `tail -50 /output/logs/migration_[fecha].log`
  - [ ] Documentar en hoja de control: fecha, usuario, Year, estado (OK/FALLOS), observaciones
  - [ ] Archivar archivos temporales Excel: `tar czf /output/archive/temp_[fecha].tar.gz /output/temp/*.xlsx`
  - [ ] Generar reporte de cambios: qué se actualizó en GOBGENER (cuántas entidades nuevas, TCONS, etc.)

---

## 7. Contactos y Escalación

| Rol | Contacto | Disponibilidad | Notas |
|-----|----------|-----------------|-------|
| DBA (Base de Datos) | **[PENDIENTE COMPLETAR]** | Oficina | Resolver fallos de conexión, backup, restauración |
| Analista de Negocio | **[PENDIENTE COMPLETAR]** | Oficina | Validar reglas de clasificación analíticos, TCONS |
| Responsable de Migración (SAS→Python) | **[PENDIENTE COMPLETAR]** | Oficina | Resolver inconsistencias de lógica, mejoras (M-xxx) |
| Soporte Infraestructura | **[PENDIENTE COMPLETAR]** | Oficina | Permisos de servidor, rutas de red |

**Procedimiento de escalación:**
1. Documentar error completo: mensaje, tabla afectada, contexto (nodo, Year, Analista)
2. Intentar resolución local (ver sección 5) por máximo 30 min
3. Si no se resuelve, contactar a Responsable de Migración
4. Si se requiere cambio en datos o acceso a BD, escalar a DBA

---

## 8. Mejoras Aplicadas en Esta Entrega

### M-001: Consolidar rutas de archivo (APROBADA)
**Estado:** Implementada en `_config.py`  
**Verificación:** Confirmar que `_config.py` existe en raíz antes de ejecutar  
**Impacto:** Todas las rutas hardcodeadas en nodos SAS reemplazadas por variables de `_config.py`

### M-005: Centralizar macro variables (APROBADA)
**Estado:** Implementada en `_parameters.yaml`  
**Verificación:** Confirmar que parámetros Year, Analista, Mes, etc. cargan correctamente  
**Impacto:** Reproducibilidad garantizada, auditoría de cambios centralizada

### M-002, M-003, M-004, M-006: (POSTERGADAS)
Serán abordadas en siguientes lotes (NB-05 en adelante) cuando estos nodos se traduzcan.

---

## 9. Registro de Ejecuciones

Mantener tabla de seguimiento:

```
Fecha       | Año | Analista       | Estado | Observaciones                              | Archivo Log
------------|-----|----------------|--------|--------------------------------------------|-----------------------
2025-01-15  | 2025| JUAN_LOPEZ     | OK     | Ciclo completo, 2 ENT nuevas              | migration_20250115.log
2025-01-22  | 2025| MARIA_GONZALEZ | FALLOS | Error en 5b (Excel), reintento en 20min   | migration_20250122.log
```

Guardar en `/output/execution_log.csv` (actualizar después de cada ciclo).

---

## 10. Próximos Pasos (Fuera de Alcance Esta Entrega)

- **Lote 2 (NB-05, NB-06):** Salida CG Imputa, Salidas CNF, indicadores especializados
- **Auditoría:** Validar que Python produce resultados idénticos a SAS en 95%+ de registros
- **Performance:** Medir tiempos de ejecución, optimizar queries lentas
- **Automatización:** Crear script `run_all.py` que ejecute todas las Fases en secuencia con manejo de errores
