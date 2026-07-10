# Sistema de Gestión de Ejecución Presupuestal — v1

Aplicación de escritorio (PySide6 + SQLAlchemy) para registrar, consultar
e importar la ejecución presupuestal de proyectos de inversión pública,
a partir de reportes SIAF con celdas combinadas.

## Estado de la v1 (mínimamente funcional)

Cubierto:
- Login con roles (ADMIN / EDITOR / VISUALIZADOR) y usuario `admin` inicial.
- Dashboard: proyectos, PIM, certificado, comprometido, devengado, saldo,
  % de ejecución, y gráfico PIM vs Devengado por proyecto.
- Proyectos: CRUD completo con búsqueda.
- Presupuesto: consulta con filtro por proyecto/texto, exportación a Excel.
- **Catálogo de clasificadores (MEF)**: se importa desde Configuración
  (archivo con columnas ANIO, CLASIFICADOR, DESCRIPCION,
  DESCRIPCION_DETALLADA) y es la fuente de verdad para validar y
  completar la descripción de cada partida presupuestal. El cruce usa un
  código normalizado (espacios del reporte SIAF convertidos a puntos,
  p.ej. `"2.3. 1  1. 1  1"` → `"2.3.1.1.1.1"`) para no confundir códigos
  distintos que a simple vista se ven parecidos.
- **Importar Excel**: motor de limpieza para reportes SIAF con celdas
  combinadas (columnas/filas fantasma), corre en hilo aparte con barra
  de progreso — es el refactor directo de `pruebas_presupuesto.py`. Cada
  clasificador importado se cruza automáticamente contra el catálogo.
  **Los proyectos/actividades del archivo se detectan y crean
  automáticamente** (no hay que tipear código de proyecto a mano);
  soporta los dos formatos de exportación SIAF observados ("por
  Proyecto" y "por Programa") de forma consistente entre sí.
- Reportes: exportación a Excel (presupuesto y proyectos) y PDF (resumen
  de ejecución) con `reportlab`.
- Auditoría básica (login, crear/editar/eliminar) y manejo de excepciones
  en toda operación de BD/archivo.

Pendiente para v2 (fuera del alcance mínimo, documentado en el código
como TODO): permisos granulares por módulo, copias de seguridad
automáticas, módulo de Ejecución mensual con UI propia (el modelo ya
existe: `models/ejecucion.py`), tema oscuro.

## Instalación

```bash
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Si vas a usar **PostgreSQL** en vez del SQLite por defecto:

```bash
export DATABASE_URL="postgresql+psycopg2://usuario:password@localhost:5432/presupuesto_db"
```

## Ejecución

```bash
python main.py
```

Usuario inicial: `admin` / `admin123` (creado automáticamente la primera
vez que arranca la app; cámbialo desde Configuración en producción).

## Formato de Excel esperado para importar

Reportes tipo SIAF ("RESUMEN DEL MARCO PRESUPUESTAL Y LA EJECUCIÓN DEL
GASTO") con columnas PIA / PIM / Certificación / Compromiso / Devengado /
Saldos / % Avance, generados con celdas combinadas (una columna de Excel
"fantasma" a cada lado de cada columna de datos). El importador:

1. Elimina filas/columnas totalmente vacías.
2. Detecta columnas fantasma (baja densidad de datos) y fusiona su
   contenido con la columna de datos más cercana.
3. Elimina bloques de cabecera repetidos dentro del archivo.
4. **Detecta automáticamente cada proyecto/actividad** del reporte
   (línea `"0035  0066 3000001 5000276 GESTION DEL PROGRAMA 22 048 0109"`
   en el formato "por Proyecto", o las líneas separadas equivalentes en
   el formato "por Programa") y crea el `Proyecto` correspondiente si no
   existe — usando siempre el código de actividad de 5-7 dígitos (el más
   específico y estable), no el número de secuencia interno del archivo.
5. Parsea la jerarquía Rubro → Meta → Categoría → Clasificador dentro de
   cada proyecto detectado.
6. Normaliza cada código de clasificador (reemplaza espacios por puntos y
   colapsa duplicados: `"2.3. 1  1. 1  1"` → `"2.3.1.1.1.1"`) y lo cruza
   contra el catálogo oficial cargado en Configuración. Si lo encuentra,
   usa la descripción canónica del catálogo; si no, conserva la
   descripción tal cual venía en el reporte y lo reporta como advertencia
   al final de la importación.

Si el archivo no trae ningún proyecto reconocible (formato atípico), el
formulario de importación permite indicar un código/nombre de "respaldo"
que se usa solo en ese caso.

**Importante**: importa primero el catálogo de clasificadores (Configuración
→ "Importar catálogo de clasificadores") antes de importar reportes de
presupuesto, para que el cruce funcione desde la primera importación.

## Estructura del proyecto

```
main.py                 Punto de entrada
config.py                Configuración (BD, constantes)
database/                 Conexión SQLAlchemy (engine, sesión, init_db)
models/                    Usuario, Proyecto, Presupuesto, Ejecucion, Auditoria
services/                  Lógica de negocio (auth, proyecto, presupuesto,
                           importación/exportación Excel, dashboard)
controllers/               Capa fina entre UI y services (maneja sesiones de BD)
reports/                   Generación de PDF (reportlab)
ui/                        Login, ventana principal, vistas por módulo
utils/                     Validadores, logger, hashing de contraseñas
```

## Notas técnicas

- Contraseñas: PBKDF2-HMAC-SHA256 (stdlib), no texto plano.
- La UI nunca ejecuta consultas directamente: siempre pasa por
  `controllers/`, que abren/cierran la sesión de BD y hacen `expunge()`
  de los objetos para que la UI pueda usarlos sin errores de sesión
  cerrada (`DetachedInstanceError`).
- La importación de Excel corre en un `QThread` separado para no
  congelar la interfaz con archivos grandes.
