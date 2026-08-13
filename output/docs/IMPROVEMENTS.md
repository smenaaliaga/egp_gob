# Mejoras — Decisiones y Aplicación

Documento de seguimiento de las mejoras identificadas en la migración de **Proc_Salidas_Gob_REV_mig-2**, especificando decisión (aprobada/rechazada/postergada), justificación y qué se incluyó en esta entrega.

---

## Resumen Ejecutivo

Se identificaron **8 mejoras** durante el análisis de código SAS original. De éstas:
- **3 aprobadas** para inclusión en esta entrega (M-005)
- **4 rechazadas** por conflicto con el alcance actual (M-001, M-003, M-004, M-008)
- **1 postergada** a lote siguiente (M-002, M-006, M-007 — flujos diferidos)

---

## Detalle de Mejoras

### M-001: Eliminar duplicación masiva de fragmentos SQL

| Aspecto | Valor |
|---------|-------|
| **Categoría** | Mantenibilidad |
| **Impacto** | Alto |
| **Esfuerzo** | Alto |
| **Riesgo** | Medio |
| **Nodos afectados** | 44 (18% del corpus total de 188 nodos) |

**Descripción**  
Se detectan 18 bloques de código SQL duplicados en 44 nodos distintos. Ejemplo: fragmento `CREATE TABLE CR18_APERTURA_PACAPR` aparece en 18 nodos (CodeTask-2u1eOTvq3sZo1V34, CodeTask-4wxss6QulJ8PK7Pu, ..., CodeTask-wpalwVYAWfwAKJxy). Similares incluyen DELETE statements repetidos en 6–8 nodos y CREATE UNION statements en 5 nodos. Esta redundancia multiplica puntos de cambio.

**Justificación**  
El código duplicado es la raíz de inconsistencias y errores de propagación. 44 nodos afectados significa 44 lugares donde un bug o cambio de lógica debe replicarse manualmente, violando el principio DRY (Don't Repeat Yourself). Fragmentos centralizados como funciones o macros reutilizables reducirían LOC, facilitarían auditoría y minimizarían riesgo de desincronización.

**Decisión**  
❌ **RECHAZADA**

**Razón de rechazo**  
El alcance de esta entrega se limita a traducción directa del código SAS existente sin refactorización estructural. Aunque la mejora es técnicamente sólida, su aplicación requeriría reescritura de múltiples notebooks y validación exhaustiva. Se recomienda como iniciativa post-migración para próximos lotes.

**Notas**  
- Revisitar en fase de optimización post-piloto
- Candidatos para extracción: funciones Python `build_cr18_apertura_pacapr()`, `build_union_blocks()`, etc.

---

### M-002: Centralizar y parametrizar rutas hardcodeadas

| Aspecto | Valor |
|---------|-------|
| **Categoría** | Mantenibilidad |
| **Impacto** | Alto |
| **Esfuerzo** | Medio |
| **Riesgo** | Bajo |
| **Nodos afectados** | 21 (flujos diferidos) |

**Descripción**  
21 smells de 'hardcoded_path' en nodos CS-0006, CS-0009, CS-0033, CS-0082, CS-0084, CS-0106, CS-0122, CS-0129, CS-0151, CS-0157, CS-0171, CS-0174, CS-0216, CS-0236, CS-0240, CS-0241, CS-0251, CS-0281, CS-0293, CS-0300, CS-0309. Rutas como `\\FILESERVER\VOLM\GEM\050_DCNI\...` y `/sasdata/BCCH/GEM_DCNI/...` están dispersas en LIBNAME, PROC IMPORT y OUTFILE.

**Justificación**  
Rutas hardcodeadas rompen portabilidad y dificultan migraciones, pruebas en ambientes y cambios de infraestructura. Centralizar en archivo de configuración macro o tabla de parámetros es estándar en SAS empresarial y facilita CI/CD.

**Decisión**  
⏸️ **POSTERGADA**

**Razón de postergación**  
Los nodos afectados pertenecen a flujos diferidos (**AUTOEXEC**, **Proceso Ejecución GC CGR**, **Proceso Ejec GC DIPRES**, y otros en la lista `flujos_diferidos`). Se revisitará cuando esos flujos entren en el siguiente lote de migración.

**Aplicación prevista**  
- Crear archivo `config/data_paths.yaml` centralizado
- Inyectar rutas vía variables de entorno en `run_all.py`
- Validar cambio al integrar flujos diferidos

---

### M-003: Extraer números mágicos a constantes nombradas

| Aspecto | Valor |
|---------|-------|
| **Categoría** | Calidad |
| **Impacto** | Medio |
| **Esfuerzo** | Medio |
| **Riesgo** | Bajo |
| **Nodos afectados** | 30+ (distribuidos en múltiples flujos) |

**Descripción**  
95 instancias de la constante `1000000` (divisor de conversión monetaria) repetida en 20+ nodos. Además, 'magic numbers' como 5601 (55 nodos), 10201 (55 nodos), códigos como '04001000', '04002000', '3801', '004', '01000000' distribuidos sin comentario. Cambio futuro de tasa o códigos administrativos requiere búsqueda manual.

**Justificación**  
Números mágicos sin contexto reducen legibilidad y aumentan riesgo de errores al actualizar valores. Una constante nombrada con documentación facilita auditoría y cambios globales. Ejemplo: `MONETARIO_DIVISOR = 1000000` vs. `/ 1000000` en 95 ubicaciones.

**Decisión**  
❌ **RECHAZADA**

**Razón de rechazo**  
A diferencia de refactorización de SQL, la extracción de constantes en Python es trivial y puede hacerse post-migración sin revalidación. Incluirla ahora alargaría la entrega sin valor inmediato. Se recomienda como tarea técnica en sprint de optimización.

**Notas**  
- Crear módulo `constants.py` post-piloto
- Plantilla: `MONETARIO_DIVISOR`, `COD_ANALÍTICO_*`, `SCN_EXCLUSIÓN_*`, etc.

---

### M-004: Refactorizar expresiones CASE repetidas en función reutilizable

| Aspecto | Valor |
|---------|-------|
| **Categoría** | Calidad |
| **Impacto** | Medio |
| **Esfuerzo** | Medio |
| **Riesgo** | Medio |
| **Nodos afectados** | 75+ |

**Descripción**  
Expresión CASE para cálculo de trimestre (`WHEN T1.MES IN(1,2,3) THEN 1...`) aparece 75 veces en 75 nodos distintos. Expresión CASE para clasificación ANALITICO (`CASE WHEN T2.ANALITICO='M'...`) en 24 nodos. Expresiones CASE para sector (`CASE WHEN T1.C_T_AREA='GM'...`) en 6 nodos. Ninguna centralizada en macro o función.

**Justificación**  
CASE statements duplicados aumentan complejidad ciclomática global y dificultan mantenimiento de lógica de negocio. Convertirlas a funciones Python normalizadas reduce LOC, mejora testabilidad y permite unit tests aislados.

**Decisión**  
❌ **RECHAZADA**

**Razón de rechazo**  
Aunque técnicamente válida, la refactorización de 75 ocurrencias de CASE introduce riesgo de cambio de comportamiento, requiere validación exhaustiva y postergación de entrega. Se incluirá en siguiente lote como mejora de deuda técnica.

**Candidatos para Función Python**  
```python
def trimestre_desde_mes(mes: int) -> int:
    """Retorna trimestre (1-4) dado mes (1-12)."""
    return (mes - 1) // 3 + 1

def clasificar_analitico(analitico: str) -> str:
    """Mapea código de analítico a clasificación consolidada."""
    # {'M': 'MIXTO', 'F': 'FIJO', 'V': 'VARIABLE', ...}
    pass

def sector_desde_area(c_t_area: str) -> str:
    """Retorna sector consolidado desde código administrativo."""
    # {'GM': 'GOBIERNO_MIXTO', 'ED': 'EDUCACIÓN', ...}
    pass
```

---

### M-005: Documentar y versionear dependencias de macro variables

| Aspecto | Valor |
|---------|-------|
| **Categoría** | Reproducibilidad |
| **Impacto** | Alto |
| **Esfuerzo** | Medio |
| **Riesgo** | Medio |
| **Nodos afectados** | 98+ |

**Descripción**  
98 nodos usan macro variable `Year`, 21 nodos usan `Comp1`–`Comp7` (6 variables de configuración), 17 nodos usan `Password_PASSWORD` y `SYSUSERID` sin versionado visible ni documentación de default. Dependencias críticas distribuidas en 98+ nodos sin comentario de origen o valores esperados.

**Justificación**  
Macro variables son parámetros de configuración pero sin versionado explícito. Cambios a futuro (ej. nuevo año fiscal) no pueden auditarse. Documentación de valores default, rango esperado y cómo inyectarlos es requisito de reproducibilidad.

**Decisión**  
✅ **APROBADA**

**Aplicación en esta Entrega**  
1. **Archivo de configuración centralizado**: `project_config.yaml`
   ```yaml
   run:
     macro_params:
       Year: 2024
       Mes: 1
       Comp1: "FISCAL"
       Comp2: null
       Comp3: null
       Comp4: null
       Comp5: null
       Comp6: null
       Comp7: null
       Analista: null
       PACAPR1: null
       PACAPR2: null
       # ... hasta PACAPR7
   ```

2. **Celda de parámetros Papermill estándar** en todos los notebooks:
   ```python
   # parameters
   Year = 2024
   Mes = 1
   Comp1 = "FISCAL"
   # ... resto de variables
   ```

3. **Documentación en README.md**:
   - Descripción de cada macro variable
   - Valores default y rango permitido
   - Cómo inyectar vía CLI o `project_config.yaml`

4. **Supuesto visible** en plan de traducción:
   - Declaración explícita de valores en `project_config.yaml` → `run.macro_params`
   - O entrada en la entrevista B4 (parámetros del usuario)

**Ubicación en Notebooks**  
- Celda 1: Import y setup
- Celda 2: `# parameters` — Papermill injector
- Celda 3: Logging de valores inyectados (auditoría)

**Estado Post-Entrega**  
- ✅ Implementado en todos los **18 notebooks generados**
- ✅ Documentado en `README.md` sección "Ejecución y Parámetros"
- ⚠️ Valores de Comp*, PACAPR*, Mes_imp* requieren definición del usuario en entrevista B4 (actualmente `None`)

---

### M-006: Eliminar credenciales hardcodeadas de código fuente

| Aspecto | Valor |
|---------|-------|
| **Categoría** | Reproducibilidad |
| **Impacto** | Alto |
| **Esfuerzo** | Medio |
| **Riesgo** | Alto |
| **Nodos afectados** | 17 (flujos diferidos) |

**Descripción**  
17 nodos contienen referencias a macro variables `Password_PASSWORD` y `SYSUSEID` que, aunque sean placeholders en el análisis, indican patrón de credenciales en código (CodeTask-1UPaqG3cjfbxeW38, CodeTask-23lpner3oIe465S4, ..., CodeTask-x5iMg8dNCjGmDI64).

**Justificación**  
Credenciales en código violan seguridad (exposure en repos públicos/histórico) y reproducibilidad. Usar variables de entorno o bóveda de secretos es requisito de cualquier pipeline CI/CD.

**Decisión**  
⏸️ **POSTERGADA**

**Razón de postergación**  
Los nodos afectados pertenecen a flujos diferidos. Se revisitará cuando esos flujos entren en el siguiente lote. Patrón de remediación será idéntico a M-002: centralizar en bóveda de secretos (ej. Azure Key Vault, AWS Secrets Manager) o variables de entorno con prefijo `GEM_SECRET_*`.

**Aplicación prevista**  
```python
# En run_all.py o utilities.py
import os
DB_PASSWORD = os.getenv('GEM_SECRET_DB_PASSWORD')
DB_USER = os.getenv('GEM_SECRET_DB_USER')
# Nunca en project_config.yaml ni logs
```

---

### M-007: Validar y documentar dependencias de base de datos no verificadas

| Aspecto | Valor |
|---------|-------|
| **Categoría** | Calidad |
| **Impacto** | Alto |
| **Esfuerzo** | Alto |
| **Riesgo** | Alto |
| **Nodos afectados** | 4 (flujos diferidos) |

**Descripción**  
Múltiples libref (DCNIDCNA, DCV, ...) marcados como `verified_db: false`. No hay confirmación de esquema, permisos de acceso ni compatibilidad de versiones de BD. Tablas como BDATOS_SP, CODIGO_ENTIDAD_SP, EJEC_MUN, MONEDAS_MENSUAL citadas sin validación de integridad referencial.

**Justificación**  
BD no verificadas son fuente principal de fallos en producción. Falta validación de: existencia de tabla, tipos de dato, constraints, permisos. Cambios en BD remota causarían errores runtime sin señal previa.

**Decisión**  
⏸️ **POSTERGADA**

**Razón de postergación**  
Los nodos afectados pertenecen a flujos diferidos. Validación de BD se llevará a cabo cuando se traduzcan (CodeTask-cbwaC9NShYE8mV6x, CodeTask-oLKJ5g7DvhYHuBME, Query-YHeDzXnzld6fOVfj, CodeTask-D6fqrxqReNOK5Xch).

**Aplicación prevista**  
- Script de validación: `validate_db_schema.py`
- Tabla de checksum de esquema: `db_validation_manifest.csv`
- Verificación pre-run en `run_all.py`

---

### M-008: Crear suite de validación de datos de entrada

| Aspecto | Valor |
|---------|-------|
| **Categoría** | Calidad |
| **Impacto** | Alto |
| **Esfuerzo** | Medio |
| **Riesgo** | Medio |
| **Nodos afectados** | 20+ |

**Descripción**  
Código manipula valores de `C_ANALITICO` como strings con códigos fijos ('04001000', '04002000', '01000000', etc.) sin validación visible ni rango permitido. Expresiones CASE implícitamente asumen ciertos valores (T1.MES IN 1-12, T1.C_T_AREA IN {'GM','ED','SL'}, T1.C_SERVICIO IN {1,2,3}). Sin validación previa, valores inválidos propagan silenciosamente a tablas de salida.

**Justificación**  
Datos de entrada no validados son principal causa de garbage-in-garbage-out. Impacto crítico en reportes financieros/presupuestarios donde datos incorrectos pueden invalidar auditoría.

**Decisión**  
❌ **RECHAZADA**

**Razón de rechazo**  
Aunque prioritaria, la creación de suite de validación integral requiere definición de business rules por dominio (ej. qué son valores "válidos" para C_ANALITICO, rango de MES, etc.) que no está en el alcance de esta fase de traducción. Se recomienda como iniciativa separada con participación de usuarios de negocio.

**Candidatos para Validación (Lote Siguiente)**  
- `validadores.py` con funciones como `validar_mes()`, `validar_analitico()`, `validar_cuenta()`, etc.
- Test fixtures en `tests/data_validation_test.py`
- Reporte de anomalías en cada notebook

---

## Resumen de Decisiones

| Mejora | Categoría | Decisión | Razón | Estado |
|--------|-----------|----------|-------|--------|
| M-001 | Mantenibilidad | ❌ Rechazada | Refactorización fuera de alcance | Diferida a optimización post-piloto |
| M-002 | Mantenibilidad | ⏸️ Postergada | Flujos diferidos | Revisitar en lote siguiente |
| M-003 | Calidad | ❌ Rechazada | Trivial en Python, post-migración | Sprint de optimización |
| M-004 | Calidad | ❌ Rechazada | Riesgo de cambio de comportamiento | Lote siguiente |
| M-005 | Reproducibilidad | ✅ Aprobada | Crítica para CI/CD y auditoría | **Implementada en todos los notebooks** |
| M-006 | Reproducibilidad | ⏸️ Postergada | Flujos diferidos | Revisitar en lote siguiente |
| M-007 | Calidad | ⏸️ Postergada | Validación de BD en flujos diferidos | Revisitar en lote siguiente |
| M-008 | Calidad | ❌ Rechazada | Requiere definición de business rules | Iniciativa separada con usuarios |

---

## Impacto en Esta Entrega

### Aplicado ✅
- **M-005**: Todos los 18 notebooks incluyen celda estándar `# parameters` de Papermill
- **Documentación**: README.md describe inyección de macro variables y valores default
- **Configuración**: `project_config.yaml` centraliza definición de parámetros

### No Aplicado (Rechazado o Postergado)
- M-001, M-003, M-004, M-008: Requieren iniciativas separadas post-migración
- M-002, M-006, M-007: Aplicables solo en flujos diferidos (próximo lote)

---

## Próximos Pasos

1. **Después de piloto en prod (mes 1):**
   - Revisar M-001 (extracción de fragmentos SQL duplicados)
   - Crear `constants.py` para M-003
   - Proponer roadmap de refactorización para M-004

2. **Próximo lote de migración:**
   - Reaplicar decisiones M-002, M-006, M-007 a flujos diferidos
   - Realizar validación de BD (M-007)
   - Eliminar credenciales (M-006)

3. **Iniciativa separada (Q siguiente):**
   - Definir esquema de validación de datos (M-008) con analistas de negocio
   - Crear suite de tests de integridad de reportes

---

**Documento generado:** 2026-08-13  
**Versión del plan:** Proc_Salidas_Gob_REV_mig-2 (translation_plan)  
**Aprobación:** Plan de traducción aprobado por usuario; mejoras según decisión del análisis
