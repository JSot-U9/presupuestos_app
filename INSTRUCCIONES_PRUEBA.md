# 📋 Instrucciones para Probar con Tu Archivo XLS

## ✅ Migracion Completada

Los nuevos campos se agregaron exitosamente a la BD:
- ✓ producto
- ✓ actividad_codigo
- ✓ actividad_descripcion
- ✓ funcion
- ✓ division_funcional
- ✓ grupo_funcional

## 🔄 Siguientes Pasos

### Opción A: Copiar tu archivo adjunto manualmente

El archivo **reporte20260710095852.xls** que adjuntaste debe copiarse a la carpeta `data/`:

```bash
# En Windows (PowerShell)
Copy-Item "C:\ruta\a\reporte20260710095852.xls" -Destination "data\reporte20260710095852.xls"

# Luego ejecutar:
py prueba_importacion.py data/reporte20260710095852.xls
```

### Opción B: Descargar el archivo desde tu navegador

1. Descarga el archivo adjunto a tu equipo
2. Cópialo a la carpeta: `c:\Users\PC 178\Documents\GitHub\presupuestos_app\data\`
3. Ejecuta:
```bash
py prueba_importacion.py data/reporte20260710095852.xls
```

## 📊 Qué Se Validará

El script de prueba verificará:

```
✓ Migración de estructura presupuestal
✓ Lectura y limpieza del archivo
✓ Parseo de estructura jerárquica
✓ Captura de campos nuevos:
  - meta (0035)
  - programa (0066)
  - producto (3000001)
  - actividad_codigo (5000276)
  - actividad_descripcion (GESTION DEL PROGRAMA)
  - funcion (22)
  - division_funcional (048)
  - grupo_funcional (0109)
✓ Inserción en base de datos
✓ Muestra de registros importados
```

## 📝 Notas

- El archivo existente (rptMetaPresupuestal.xls) es de META presupuestal, no un reporte SIAF
- Tu archivo adjunto (reporte20260710095852.xls) debe ser un reporte SIAF con los campos que especificaste
- Asegúrate que el archivo tenga la estructura esperada:
  - Líneas de proyecto con formato: `0035  0066 3000001 5000276 GESTION DEL PROGRAMA 22 048 0109`
  - Filas de clasificador iniciando con `2.`
