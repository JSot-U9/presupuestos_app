# Restructuración de la Estructura Presupuestal

## Cambios Realizados

### 1. Modelo `Presupuesto` ([models/presupuesto.py](models/presupuesto.py))

Se agregaron los siguientes campos para capturar la estructura jerárquica del SIAF:

```python
# --- Estructura presupuestal jerárquica ---
meta: str | None              # Código 0035 (4 dígitos)
programa: str | None          # Código 0066 (4 dígitos)  
producto: str | None          # Código 3000001 (7 dígitos)
actividad_codigo: str | None  # Código 5000276 (7 dígitos)
actividad_descripcion: str | None  # "GESTION DEL PROGRAMA"

# --- Clasificadores funcionales (MEF) ---
funcion: str | None           # Código 22
division_funcional: str | None # Código 048
grupo_funcional: str | None    # Código 0109
```

**Campo deprecado**: `categoria` se mantiene por compatibilidad pero ahora siempre es `NULL`.

### 2. Regex de Parseo ([services/excel_import_service.py](services/excel_import_service.py))

Se mejoró el regex `PROYECTO_LINEA_COMBINADA_RE` para capturar todos los campos:

**Antes**:
```python
PROYECTO_LINEA_COMBINADA_RE = re.compile(
    r"^(\d{4})\s+\d{4}\s+\d+\s+(\d{5,7})\s+(.+?)\s+\d{1,3}\s+\d{1,3}\s+\d{1,4}$"
)
```

**Ahora** (con 8 grupos capturadores):
```python
PROYECTO_LINEA_COMBINADA_RE = re.compile(
    r"^(\d{4})\s+(\d{4})\s+(\d+)\s+(\d{5,7})\s+(.+?)\s+(\d{1,3})\s+(\d{1,3})\s+(\d{1,4})$"
)
# Grupos: (1=meta, 2=programa, 3=producto, 4=actividad_codigo, 5=actividad_descripcion,
#          6=funcion, 7=division_funcional, 8=grupo_funcional)
```

### 3. Lógica de Parseo Jerárquico

Se actualizó el método `_parsear_jerarquia()` para:
- Extraer todos los 8 campos de la línea de proyecto combinada
- Eliminar el procesamiento de `categoria` (ya no relevante)
- Generar diccionarios con todos los campos nuevos

### 4. Persistencia en Base de Datos

Se actualizó la creación de registros `Presupuesto` para mapear todos los campos nuevos:

```python
registro = Presupuesto(
    # ...
    meta=fila["meta"],
    programa=fila["programa"],
    producto=fila["producto"],
    actividad_codigo=fila["actividad_codigo"],
    actividad_descripcion=fila["actividad_descripcion"],
    funcion=fila["funcion"],
    division_funcional=fila["division_funcional"],
    grupo_funcional=fila["grupo_funcional"],
    # ...
)
```

## Estructura de Ejemplo Parseada

**Línea de entrada SIAF**:
```
0035  0066 3000001 5000276 GESTION DEL PROGRAMA 22 048 0109
```

**Se parsea como**:
| Campo | Valor |
|-------|-------|
| `meta` | `0035` |
| `programa` | `0066` |
| `producto` | `3000001` |
| `actividad_codigo` | `5000276` |
| `actividad_descripcion` | `GESTION DEL PROGRAMA` |
| `funcion` | `22` |
| `division_funcional` | `048` |
| `grupo_funcional` | `0109` |

## Instrucciones de Aplicación

### Opción A: Migración Segura (Recomendada)

Si tienes una BD existente con datos que deseas preservar:

```bash
python migracion_estructura_presupuesto.py
```

Esto agregará los nuevos campos como columnas NULL sin afectar datos existentes.

### Opción B: Recrear BD desde Cero

Si tienes una BD de desarrollo/prueba sin datos críticos:

```bash
python migracion_estructura_presupuesto.py --recrear
```

**⚠️ ADVERTENCIA**: Esto borra TODOS los datos. Solo usar en desarrollo.

### Opción C: Manual (SQLite)

Si prefieres ejecutar manualmente:

```sql
ALTER TABLE presupuestos ADD COLUMN producto VARCHAR(20) NULL;
ALTER TABLE presupuestos ADD COLUMN actividad_codigo VARCHAR(20) NULL;
ALTER TABLE presupuestos ADD COLUMN actividad_descripcion VARCHAR(300) NULL;
ALTER TABLE presupuestos ADD COLUMN funcion VARCHAR(10) NULL;
ALTER TABLE presupuestos ADD COLUMN division_funcional VARCHAR(10) NULL;
ALTER TABLE presupuestos ADD COLUMN grupo_funcional VARCHAR(10) NULL;
```

## Retrocompatibilidad

- ✅ Archivos importados con la estructura anterior funcionarán (los nuevos campos serán NULL)
- ✅ El campo `categoria` se mantiene deprecado pero vacío
- ✅ Consultas existentes que filtren por `meta`, `programa`, `rubro` seguirán funcionando

## Verificación

Después de aplicar los cambios, prueba importando un archivo SIAF:

```bash
python main.py
```

Los nuevos campos deben capturarse correctamente en cada importación.
