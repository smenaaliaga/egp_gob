# README: Migración Proc_Salidas_Gob_REV

## ¿Qué es esta migración?

Esta es la migración de **SAS a Python** del proyecto `Proc_Salidas_Gob_REV_mig-2`, un sistema de procesamiento de ejecuciones presupuestarias y salidas contables del gobierno central y gobiernos regionales.

El proyecto traduce **18 Process Flows** con un total de **188 nodos SAS** (PROC SQL, PROC IMPORT, DATA STEP y macros) a **Jupyter notebooks en Python**, mantiendo la lógica de negocio intacta y la integración con bases de datos institucionales (GOBGENER).

**Alcance de esta entrega:** Los 4 notebooks generados cubren:
- **NB-01_autoexec.ipynb** – Inicialización de librerías y procesamiento de tasas de cambio
- **NB-02_proceso_ejecucion_gc_cgr.ipynb** – Validación y clasificación de ejecuciones CGR
- **NB-03_proceso_ejec_gc_dipres.ipynb** – Validación y clasificación de ejecuciones DIPRES
- **NB-04_salida_cg_coy.ipynb** – Salidas de coyuntura (consumo de gobierno central)

**Flujos diferidos (lotes posteriores):** 
- Salida CG Imputa
- Salida CNF trim
- Salidas CNF anual y COFOG
- Salida_anual para componente especif_no
- Proceso Sit_Patri_MUN_no
- Proceso Ejecución Municipal CGR_no
- Traspasos_info
- Salida_CF_GC
- Salida_DCNA
- Salidas_Cuenta_Produc_AAPP_no
- Salidas_Cuenta_Produc_AAPP_2_no
- Indicadores municipales

Estos 11 flujos se migran en lotes posteriores; el presente entrega **no** es completa de la arquitectura SAS original.

---

## ¿Qué produce?

Cada notebook genera:

1. **Tablas de trabajo (WORK.*)** – Datasets intermedios en sesión, utilizados como puntos de control y validación
2. **Tablas de salida (GOBGENER.*)** – Tablas persistentes en la base de datos institucional, destinadas a reportes y análisis downstream
3. **Logs de ejecución** – Registro de conteos, validaciones y anomalías detectadas

**Productos principales por notebook:**

| Notebook | Tablas GOBGENER (salidas) | Descripción |
|----------|---------------------------|-------------|
| NB-01_autoexec | — | Datos auxiliares en WORK (tasas de cambio, promedios mensuales, trimestrales) |
| NB-02_proceso_ejecucion_gc_cgr | ANALIT_TCONS, COFOG, CR18_APERTURA, CR18_T_SCN_1/2, ENTIDADES, EST_EXP_* | Clasificación y validación de ejecuciones CGR con estructuras analíticas |
| NB-03_proceso_ejec_gc_dipres | ANALIT_TCONS, CR18_T_SCN_1/2, EST_EXP_MIXTAS_M, EST_EXP_MM | Clasificación de ejecuciones DIPRES con matrices analíticas |
| NB-04_salida_cg_coy | IMPUT_GC_DIP, IMPUT_GC_DIP_APER | Ejecución coyuntural de gobierno central (muestra + expansión), con imputaciones |

---

## Estructura de output

```
output/
├── NB-01_autoexec.ipynb
├── NB-02_proceso_ejecucion_gc_cgr.ipynb
├── NB-03_proceso_ejec_gc_dipres.ipynb
├── NB-04_salida_cg_coy.ipynb
├── run_all.py
├── .env (credenciales y parámetros, **no incluir en control de versiones**)
└── logs/
    └── execution_log_<YYYY-MM-DD_HH:MM:SS>.txt
```

**Archivos clave:**

- **Notebooks (.ipynb):** Contienen celdas de parámetros, conexión a BD, transformaciones SQL/Python y validaciones
- **run_all.py:** Script que ejecuta los 4 notebooks en orden, inyectando parámetros de período y validando dependencias
- **.env:** Variables de entorno (credenciales BD, rutas de archivos, parámetros Year/Mes/Comp*)
- **logs/:** Registro de ejecuciones con conteos de registros y validaciones

---

## Cómo correr

### Requisitos previos

**Python:**
- Python 3.9+
- Dependencias: `pandas`, `sqlalchemy`, `pymssql`, `python-dotenv`, `jupyter`

Instalar con:
```bash
pip install -r requirements.txt
```

**Base de datos:**
- SQL Server con base `GOBGENER` accesible
- Usuario con permisos de lectura en tablas de entrada (EJECUCION, ENTIDADES, etc.)
- Usuario con permisos de escritura en tablas de salida (IMPUT_GC_DIP, IMPUT_GC_DIP_APER, etc.)

**Archivos de configuración:**
- `.env` en el directorio raíz con:
  ```
  DB_SERVER=<servidor>
  DB_USER=<usuario>
  DB_PASSWORD=<contraseña>
  DB_NAME=GOBGENER
  YEAR=<año fiscal>
  MES=<mes 1-12>
  PACAPR1=<código partida 1>
  # ... PACAPR2-7 (opcional)
  COMP1=<componente 1>
  # ... COMP2-7 (opcional)
  ```

### Ejecución interactiva (recomendada para desarrollo)

1. Abrir **Jupyter Lab** o **VS Code + Jupyter extension:**
   ```bash
   jupyter lab
   ```

2. Ejecutar los notebooks en orden:
   - NB-01_autoexec.ipynb
   - NB-02_proceso_ejecucion_gc_cgr.ipynb
   - NB-03_proceso_ejec_gc_dipres.ipynb
   - NB-04_salida_cg_coy.ipynb

Cada notebook tiene una celda **parameters** al inicio donde se pueden ajustar `Year`, `Mes`, `PACAPR1-7`, `COMP1-7` sin editar código.

### Ejecución automatizada (batch/scheduling)

Ejecutar el script `run_all.py`:

```bash
python run_all.py --year 2024 --mes 12 --pacapr1 3101 --pacapr2 3201 --comp1 GC
```

El script:
- Valida parámetros y conectividad a BD
- Ejecuta los 4 notebooks secuencialmente con `papermill`
- Genera log consolidado en `logs/execution_log_<timestamp>.txt`
- Retorna código de salida 0 (éxito) o 1 (fallo)

---

## Supuestos visibles

1. **Parámetros macro obligatorios:**
   - `Year` – Año fiscal (ej. 2024)
   - `Mes` – Mes de procesamiento (1-12)
   - `PACAPR1-7` – Códigos de partida presupuestaria a procesar (al menos PACAPR1)
   - `Comp1-7` – Componentes de gobierno (al menos Comp1)

   Si no están declarados en `.env`, la celda `parameters` los deja en `None` y la ejecución fallará. Ver **Decisiones** → **Macro variables sin default**.

2. **Libref GOBGENER es SQL Server:**
   - Tablas de entrada están en la BD institucional (no archivos)
   - Tablas de salida (IMPUT_GC_DIP, etc.) se persisten en la misma BD
   - Estrategia de temp tables: `session_sql` (tablas #tmp en la conexión)

3. **Moneda de conversión:** Tasa hardcodeada 1,000,000 para conversión a millones

4. **Período fiscal:** Año civil (enero-diciembre); lógica de trimestre asume mes 1-12

5. **Dependencias entre notebooks:** 
   - NB-01 → NB-02, NB-03 (ambos usan WORK.CIERRE_MES, PROM_MES de autoexec)
   - NB-02 ↔ NB-03 (tablas WORK intermedias compartidas vía BD temporal)
   - NB-04 requiere tablas de NB-02 y NB-03

---

## Cambios respecto a SAS original

1. **Estrategia SQL:** Nodos con `placement: sql_pushdown` mantienen SQL en Python vía `SQLAlchemy + pyodbc`, no todo se convierte a pandas
2. **Librerías removidas:** Macros SAS complejas se simplificaron; verifica `decisions.md` para cambios de lógica
3. **Logging:** Los notebooks usan Python `logging` en lugar de `PROC PRINTTO`
4. **Rendimiento:** Algunos nodos "ambiguous" (CodeTask-D6fqrxqReNOK5Xch, etc.) bajan tablas enteras a pandas en memoria; ver **Decisiones** para alternativas

---

## Próximos pasos

- **Si necesitas desarrollar:** Abre los notebooks en Jupyter, modifica celdas, ejecuta interactivamente
- **Si necesitas producción:** Configura `.env`, ejecuta `run_all.py` desde scheduler (ej. Windows Task Scheduler, Airflow)
- **Si encuentras errores:** Revisa `logs/execution_log_*.txt` y contáctate con el equipo de datos

---

## Contactos y referencias

- **Documentación asociada:**
  - `lineage.md` – Flujo de datos (qué tablas vienen de dónde, qué notebooks las producen)
  - `decisions.md` – Decisiones de alcance, placeholders, supuestos visibles
  - `improvements.md` – Mejoras aprobadas/rechazadas/postergadas
  - `runbook.md` – Operación día a día, verificaciones post-ejecución, troubleshooting

- **Repositorio:** D:\Projects\Migraciones-SAS\Proc_Salidas_Gob_REV (SAS original)
- **EGP generado:** Proc_Salidas_Gob_REV_mig-2.egp (2026-08-11)
- **Plan traducción:** Translation plan aprobado por usuario (2026-08-13)
