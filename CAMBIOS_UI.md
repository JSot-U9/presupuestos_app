# Actualización de Vistas de UI - Estructura Presupuestal

## Cambios Realizados

### 1. Vista de Presupuesto Actualizada ([ui/views/presupuesto_view.py](ui/views/presupuesto_view.py))

#### Columnas de la Tabla
**Antes**:
```
Proyecto | Clasificador | Descripción | Meta | PIA | PIM | Certificado | Comprometido | Devengado | Saldo Devengado | % Avance
```

**Ahora**:
```
Proyecto | Meta | Programa | Producto | Actividad | Clasificador | Descripción | Función | PIM | Certificado | Devengado | % Avance
```

#### Filtros Mejorados
Se reemplazaron los filtros antiguos por:
- **Meta** (0035): Código de meta presupuestal
- **Programa** (0066): Código de programa
- **Función** (22): Código funcional MEF
- **Rubro**: Se mantiene como filtro principal

#### Funcionalidad de Detalles
- **Doble clic en fila**: Abre un diálogo con todos los detalles del presupuesto
- Muestra información completa incluyendo:
  - Estructura presupuestal jerárquica
  - Clasificadores funcionales (Función, División Funcional, Grupo Funcional)
  - Datos de actividad/AI/obra
  - Ejecución presupuestal completa

### 2. Diálogo de Detalles ([ui/views/presupuesto_detail_dialog.py](ui/views/presupuesto_detail_dialog.py))

Nuevo widget que muestra todos los campos del presupuesto organizados en secciones:

**PROYECTO**
- Código y nombre del proyecto

**ESTRUCTURA PRESUPUESTAL**
- Rubro (00 RECURSOS ORDINARIOS)
- Meta (0035)
- Programa (0066)
- Producto (3000001)

**ACTIVIDAD / AI / OBRA**
- Código de Actividad (5000276)
- Descripción de Actividad (GESTION DEL PROGRAMA)

**CLASIFICADORES FUNCIONALES (MEF)**
- Función (22)
- División Funcional (048)
- Grupo Funcional (0109)

**CLASIFICADOR DE GASTO**
- Código normalizado (2.3.2.7.11.6)
- Código original (con espacios)
- Descripción

**EJECUCION PRESUPUESTAL**
- Año, Mes
- PIA, PIM, Certificación, Compromiso, Devengado, Saldo, % Avance

**AUDITORIA**
- Fecha de importación
- Archivo de origen

### 3. Controlador Actualizado ([controllers/presupuesto_controller.py](controllers/presupuesto_controller.py))

Se agregaron nuevos métodos para obtener valores únicos:

```python
@staticmethod
def listar_programas(proyecto_id: Optional[int] = None) -> list[str]:
    """Retorna lista de códigos de programa únicos."""

@staticmethod
def listar_funciones(proyecto_id: Optional[int] = None) -> list[str]:
    """Retorna lista de códigos de función únicos."""

@staticmethod
def listar_productos(proyecto_id: Optional[int] = None) -> list[str]:
    """Retorna lista de códigos de producto únicos."""

@staticmethod
def listar_actividades(proyecto_id: Optional[int] = None) -> list[str]:
    """Retorna lista de códigos de actividad únicos."""
```

## Cómo Usar

### Ver Detalles Completos
1. En la vista de **Presupuesto**
2. **Doble clic** en cualquier fila
3. Se abre un diálogo con todos los campos

### Filtrar por Nueva Estructura
1. Use los combos de filtro:
   - **Meta**: Filtrar por código de meta (0035)
   - **Programa**: Filtrar por código de programa (0066)
   - **Función**: Filtrar por código funcional (22, 23, etc.)
   - **Rubro**: Mantiene filtrado por rubro de financiamiento

### Notas
- Los cambios son **retrocompatibles** con datos antiguos
- Campo `categoria` fue reemplazado (deprecado pero mantenido)
- Todos los filtros funcionan de forma independiente
- La tabla se puede desplazar horizontalmente para ver todas las columnas

## Próximas Mejoras Sugeridas

1. **Exportación mejorada**: Incluir nuevos campos en Excel
2. **Búsqueda avanzada**: Filtrar por actividad específica
3. **Gráficos**: Por estructura presupuestal (Meta, Programa, Función)
4. **Análisis**: Comparativa de presupuesto vs. ejecución por estructura
