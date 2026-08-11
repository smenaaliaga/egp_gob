# Runbook: Proc_Salidas_Gob_REV_mig-2

## Resumen Operacional

Este runbook describe el procedimiento día a día para ejecutar la migración de **Proc_Salidas_Gob_REV_mig-2**: un conjunto de 18 flujos SAS traducidos a Python/Jupyter que procesan datos presupuestarios y de ejecución de gasto del Gobierno Central chileno (fuentes CGR y DIPRES).

La entrega **está compuesta por 4 notebooks principales** que cubren los flujos completamente traducidos en este lote:

- **NB-01_autoexec.ipynb**: Procesamiento inicial de monedas y tipos de cambio
- **NB-02_proceso_ejecucion_gc_cgr.ipynb**: Validación y clasificación de ejecuciones (CGR)
- **NB-03_proceso_ejec_gc_dipres.ipynb**: Validación y clasificación de ejecuciones (DIPRES)
- **NB-04_salida_cg_coy.ipynb**: Cálculo y generación de salidas de coyuntura (CGR+DIPRES)

**Pendiente de traducción en lotes posteriores**: 14 flujos diferidos (Salida_CNF_Trim_CGR, Salida_CNF_Trim_DIP, Salidas_CNF_anual_y_COFOG, entre otros).

---

## Requisitos Previos

### Sistema Operativo y Software
- **Python**: 3.9 o superior
- **Jupyter**: 4.0 o superior (Lab o Notebook)
- **Motor de base de datos**: SQL Server con acceso a esquema `GOBGENER`
- **Conexión de red**: Acceso a servidor de BD y a rutas UNC de archivo (si aplica)

### Dependencias Python
Se requieren los siguientes paquetes (incluidos en `requirements.txt`):

```
pyodbc>=4.0.32          # Conexión a SQL Server
pandas>=1.3.0           # Manipulación de datos
numpy>=1.21.0           # Operaciones numéricas
sqlalchemy>=1.4.0       # ORM y builder de SQL
python-dotenv>=0.19.0   # Gestión de variables de entorno
```

### Acceso a Base de Datos
- **Servidor**: (a configurar en `project_config.yaml` o variables de entorno)
- **BD**: GOBGENER
- **Usuario**: Debe tener permisos SELECT sobre tablas de entrada y SELECT+INSERT+UPDATE sobre schema WORK
- **Credenciales**: Se deben proveer mediante variables de entorno (NO en código):
  - `DB_USER`: usuario de base de datos
  - `DB_PASSWORD`: contraseña (no incluirla en repositorio)
  - `DB_SERVER`: nombre/IP del servidor SQL Server

### Parámetros Requeridos
Antes de ejecutar, se deben definir los siguientes parámetros (pueden configurarse en `project_config.yaml` o inyectarse al notebook):

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `Year` | int | Año de procesamiento | 2023 |
| `Mes` | int | Mes de procesamiento (1-12) | 6 |
| `Comp1`–`Comp7` | str | Códigos de componentes analíticos | '04001000' |
| `PACAPR1`–`PACAPR7` | str | Paquetes de aperturas institucionales | 'AAPP' |
| `Moneda` | str | Código de moneda (ej. 'CLP') | 'CLP' |
| `Analista` | str | Nombre del analista ejecutor | 'usuario_sistema' |
| `Mes_imp1`–`Mes_imp12` | int | Meses para imputaciones especiales | 1 a 12 |

**Nota**: Estos parámetros están documentados en la celda `parameters` de cada notebook (Papermill-compatible).

---

## Estructura de Directorios

```
Proc_Salidas_Gob_REV_mig-2/
├── output/
│   ├── NB-01_autoexec.ipynb
│   ├── NB-02_proceso_ejecucion_gc_cgr.ipynb
│   ├── NB-03_proceso_ejec_gc_dipres.ipynb
│   ├── NB-04_salida_cg_coy.ipynb
│   ├── run_all.py                      # Script de orquestación
│   └── project_config.yaml             # Configuración centralizada
├── logs/
│   └── execution_*.log                 # Logs de ejecución
├── data/
│   └── (archivos CSV temporales si aplica)
└── requirements.txt                    # Dependencias Python
```

---

## Orden de Ejecución

**Secuencia lineal recomendada** (cada notebook depende de tablas generadas por el anterior):

```
1. NB-01_autoexec.ipynb
   ↓ genera: WORK.CIERRE_MES, WORK.CIERRE_TRIM, WORK.PROM_MES, WORK.PROM_TRIM
   
2. NB-02_proceso_ejecucion_gc_cgr.ipynb
   ↓ lee outputs de NB-01; genera: GOBGENER.ANALIT_TCONS, WORK.ANALIT_*
   
3. NB-03_proceso_ejec_gc_dipres.ipynb
   ↓ lee outputs de NB-02; genera: WORK.ANALIT_*_D, WORK.EJEC_DIP
   
4. NB-04_salida_cg_coy.ipynb
   ↓ lee outputs de NB-03; genera: WORK.EJECUCION_CG_*, WORK.RATIOS, salidas finales
```

### Ejecución Manual (Jupyter)

1. Abrir Jupyter Lab/Notebook
2. Navegar a `output/` y abrir `NB-01_autoexec.ipynb`
3. Establecer parámetros en celda `parameters` (primera celda):
   ```python
   # parameters
   Year = 2023
   Mes = 6
   Comp1 = '04001000'
   # ... resto de parámetros
   ```
4. Ejecutar todas las celdas: **Cell → Run All**
5. Verificar logs en consola (última celda imprime resumen)
6. Repetir pasos 2–5 para NB-02, NB-03, NB-04 **en orden**

### Ejecución Automatizada (Papermill + run_all.py)

```bash
cd output/
python run_all.py \
  --year 2023 \
  --mes 6 \
  --comp1 "04001000" \
  --analista "usuario_sistema"
```

El script `run_all.py` orquesta la ejecución secuencial con inyección de parámetros y captura de logs.

---

## Validaciones Post-Ejecución

Tras correr cada notebook, verificar:

### NB-01_autoexec.ipynb
- ✅ Tablas WORK.CIERRE_MES, WORK.CIERRE_TRIM existen y contienen datos
- ✅ Registros en CIERRE_MES ≥ 1 (mínimo un mes cerrado)
- ✅ Columnas: MES, ANO, VALOR, PROMEDIO presentes
- ⚠️ Si error de conexión a BD: verificar credenciales en `.env` y conectividad de red

### NB-02_proceso_ejecucion_gc_cgr.ipynb
- ✅ Tabla GOBGENER.ANALIT_TCONS actualizada (INSERT/UPDATE registrado)
- ✅ Validaciones COMPARA_* generadas: COMPARA_PACAPR, COMPARA_ENTIDAD, COMPARA_CAPITULO
- ✅ Conteo de registros en CHECK_* sin diferencias mayores vs. ejecución anterior
- ⚠️ Si detecta divergencias en COMPARA_*: revisar nodo 2-Check (puede indicar cambio en nomenclatura CGR)

### NB-03_proceso_ejec_gc_dipres.ipynb
- ✅ Tabla WORK.EJEC_DIP contiene datos de ejecución DIPRES del mes
- ✅ Registros analíticos ANALIT_*_D generados (sufijo _D = DIPRES)
- ✅ Validaciones CHECK_ANALIT_REV, CHECK_TCONS_R sin errores críticos
- ⚠️ Si falta DIPRES.EJEC_DIPRES: verificar disponibilidad de datos en BD

### NB-04_salida_cg_coy.ipynb
- ✅ Tabla WORK.EJECUCION_CG_CGR generada con registros de consumo consolidado
- ✅ Tabla WORK.EJECUCION_CG_DIP generada (DIPRES imputado)
- ✅ WORK.RATIOS contiene ratios de transferencias en especie (rango 0–1)
- ✅ Salidas de coyuntura APER_CG_coy completadas
- ✅ Imputaciones permanentes (IMPUT_GC_DIP) aplicadas
- ⚠️ Si RATIOS vacío: revisar disponibilidad de GOBGENER.EST_EXP_MIXTAS_M

---

## Procedimiento ante Fallos Comunes

### Fallo: "Connection refused" o "Login failed"
**Causa**: Credenciales incorrectas o servidor inaccesible
- [ ] Verificar `.env`: `DB_SERVER`, `DB_USER`, `DB_PASSWORD`
- [ ] Probar conectividad: `sqlcmd -S <servidor> -U <usuario> -P <contraseña>`
- [ ] Si error persiste: contactar administrador de BD

### Fallo: "Table 'GOBGENER.MONEDAS_MENSUAL' not found"
**Causa**: Tabla de entrada no existe en BD
- [ ] Verificar que GOBGENER contiene tabla MONEDAS_MENSUAL
- [ ] Consultar con equipo de datos si tabla fue renombrada o movida
- [ ] Alternativa: usar tabla histórica si está disponible

### Fallo: "Duplicate key error" en WORK.CIERRE_MES
**Causa**: Tabla WORK persiste de ejecución anterior; el servidor reutiliza sesión SQL
- [ ] Ejecutar en célula previa a NB-01:
  ```python
  import pyodbc
  conn = pyodbc.connect(...).cursor()
  conn.execute("DROP TABLE IF EXISTS WORK.CIERRE_MES")
  conn.commit()
  ```
- [ ] O: cambiar parámetro `temp_table_strategy` a `drop_recreate` en `project_config.yaml`

### Fallo: Registro de auditoría incompleto (COMPARA_* vacías)
**Causa**: Cambio en nomenclatura de entidades no detectado automáticamente
- [ ] Revisar tabla GOBGENER.ENTIDADES: ¿hubo cambios recientes?
- [ ] Ejecutar NB-02 nuevamente para re-auditar
- [ ] Si persiste: contactar al equipo de Analítica (ver sección Contactos)

### Fallo: RATIOS < 0 o RATIOS > 1
**Causa**: Estructura de transacciones mixtas inconsistente
- [ ] Revisar tabla GOBGENER.EST_EXP_MIXTAS_M
- [ ] Verificar que suma de ponderadores = 1 por SCN
- [ ] Ejecutar validación manual:
  ```sql
  SELECT C_SCN, SUM(PONDER) AS suma
  FROM GOBGENER.EST_EXP_MIXTAS_M
  GROUP BY C_SCN
  HAVING SUM(PONDER) <> 1
  ```

### Fallo: "Timeout" en NB-04 (salida_cg_coy)
**Causa**: Volumen de datos alto o consultas SQL complejas
- [ ] Aumentar timeout en conexión (default 30 seg):
  ```python
  conn = pyodbc.connect(..., timeout=300)
  ```
- [ ] Ejecutar durante horario de bajo volumen de BD
- [ ] Contactar administrador de BD para optimizar índices de GOBGENER

---

## Verificación de Integridad de Salidas

### Conteos Esperados (valores indicativos, pueden variar por período)

| Tabla | Conteo Mínimo | Condición |
|-------|---------------|-----------|
| WORK.CIERRE_MES | 1 | Al menos un mes cerrado |
| GOBGENER.ANALIT_TCONS | 100 | Mínimo de registros analíticos consolidados |
| WORK.EJEC_DIP | 50 | Ejecución DIPRES clasificada |
| WORK.EJECUCION_CG_CGR | 200 | Consumo consolidado CGR+DIPRES |
| WORK.RATIOS | 10 | Ponderadores de transacciones mixtas |

### Validación de Correlación
Tras ejecutar NB-04, verificar consistencia:

```python
# En celda nueva del notebook
import pandas as pd
import pyodbc

conn = pyodbc.connect(...)
cg_cgr = pd.read_sql("SELECT SUM(MONTO) FROM WORK.EJECUCION_CG_CGR", conn)
cg_dip = pd.read_sql("SELECT SUM(MONTO) FROM WORK.EJECUCION_CG_DIP", conn)

print(f"CG_CGR total: {cg_cgr.values[0][0]:,.0f}")
print(f"CG_DIP total: {cg_dip.values[0][0]:,.0f}")
print(f"Delta: {abs(cg_cgr.values[0][0] - cg_dip.values[0][0]):,.0f}")

# Delta debe ser < 5% del total CGR
if abs(cg_cgr.values[0][0] - cg_dip.values[0][0]) / cg_cgr.values[0][0] > 0.05:
    print("⚠️ ALERTA: Divergencia > 5% entre CGR y DIPRES")
else:
    print("✅ Validación OK: Consistencia CGR/DIPRES")
```

---

## Horarios de Ejecución Recomendados

- **Desarrollo/Testing**: Lunes–Viernes, 10:00–12:00 (fuera de picos de reporting)
- **Producción**: Martes–Jueves, 23:00–03:00 (ventana de mantenimiento)
- **Evitar**: Viernes 16:00–lunes 08:00 (fin de semana + reportes de cierre)

---

## Gestión de Logs

### Ubicación
- Logs automáticos guardados en `logs/execution_YYYYMMDD_HHMMSS.log`
- Salida de celdas capturada en archivo de sesión

### Rotación
Mantener máximo 30 logs históricos; ejecutar:
```bash
ls -1t logs/execution_*.log | tail -n +31 | xargs rm
```

### Nivel de Detalle
Por defecto: `INFO` (registra inicio/fin, errores)
Para debugging: cambiar en `project_config.yaml`:
```yaml
logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## Supuestos Visibles

1. **Parámetros inyectados**: `Year`, `Mes`, `Comp*`, `PACAPR*`, `Moneda` deben estar definidos antes de ejecutar NB-02 en adelante. Si no se definen, celdas usan `None` y generan errores de tipo runtime.

2. **Tablas WORK reutilizables**: Tras NB-01, tablas como WORK.CIERRE_MES persisten en sesión SQL. Ejecuciones subsecuentes verifican existencia; si duplica clave, usar `DROP TABLE IF EXISTS` previo.

3. **Estrategia de tablas temporales**: Configurada como `session_sql` (default). Las tablas WORK se crean en la sesión y no se limpian automáticamente entre ejecuciones. Para limpieza automática, cambiar a `drop_recreate` en config.

4. **Macros de período**: Los parámetros `Mes_imp1`–`Mes_imp12` son opcionales. Si se omiten, imputaciones para otros meses se saltan. Consultar con el equipo de Analítica si se necesita imputación de múltiples meses.

5. **Dependencias de libref**: Códigos asumen que libref `GOBGENER` está definida como conexión a esquema GOBGENER del servidor SQL Server. Sin esta, todas las lecturas fallarán.

6. **Validaciones desactivadas**: M-008 (suite de validación de datos de entrada) fue rechazada. Los notebooks NO validan rango de `MES` (debe ser 1–12) ni códigos `C_ANALITICO`. Datos inválidos pueden propagarse sin alerta.

---

## Contactos y Escalación

| Rol | Nombre | Email | Teléfono | Temas |
|-----|--------|-------|----------|-------|
| Administrador de BD | (pendiente) | (pendiente) | (pendiente) | Conexión, permisos, schema GOBGENER |
| Equipo de Analítica | (pendiente) | (pendiente) | (pendiente) | Lógica de imputaciones, nomenclatura, parámetros |
| DevOps / Infraestructura | (pendiente) | (pendiente) | (pendiente) | Errores de red, horarios de mantenimiento, credenciales |
| Propietario del Proceso | (pendiente) | (pendiente) | (pendiente) | Requerimientos, cambios de negocio, aprobación de salidas |

**Nota**: Los contactos arriba marcados como pendientes deben completarse en la entrevista posterior del equipo de migración. Contactar al Project Manager o Administrador de Sistemas.

---

## Próximos Pasos: Flujos Diferidos

Los siguientes **14 flujos están pendientes de traducción en lotes posteriores**:

1. Salida_CNF_Trim_CGR
2. Salida_CNF_Trim_DIP
3. Salidas_CNF_anual_y_COFOG
4. Salida_anual_para_componente_especif_no
5. Proceso_Sit_Patri_MUN_no
6. Proceso_Ejecución_Municipal_CGR_no
7. Traspasos_info
8. Salida_CF_GC
9. Salida_DCNA
10. Salidas_Cuenta_Produc_AAPP_no
11. Salidas_Cuenta_Produc_AAPP_2_no
12. Indicadores_municipales
13. Salida_Cuentas_Consolidadas_Nacional
14. Procesos_Agregados_Finales

Estos se integrarán en nuevos notebooks (NB-05, NB-06, etc.) cuando se apruebe el siguiente lote de traducción.

---

## Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-08-11 | Runbook inicial; 4 notebooks, 18 flujos parciales |

---

**Generado**: 2026-08-11 | **Proyecto**: Proc_Salidas_Gob_REV_mig-2 | **Estrategia de traducción**: notebook-flow (Python/Pandas + SQL Pushdown)
