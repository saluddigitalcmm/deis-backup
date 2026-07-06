# DEIS Backup

Este repositorio mantiene un respaldo automático de los archivos de **Atenciones de Urgencia** publicados por el **Departamento de Estadísticas e Información de Salud (DEIS)** del Ministerio de Salud de Chile.

## Objetivo

El propósito de este repositorio es proporcionar una fuente alternativa de descarga para la plataforma **Alertas IRA** cuando el repositorio oficial del DEIS no se encuentre disponible o presente problemas de conectividad desde el servidor donde se ejecuta la plataforma.

## Contenido

El repositorio almacena:

* Los archivos `AtencionesUrgencia<YYYY>.zip` descargados desde el DEIS.
* Un archivo `ultima_actualizacion.txt` con información de la última actualización realizada (fecha, tamaño y hash del archivo).

## Actualización

Los archivos son actualizados automáticamente mediante un script ejecutado desde un equipo con acceso al repositorio oficial del DEIS. El proceso:

1. Descarga el archivo más reciente desde el DEIS.
2. Verifica si el contenido cambió respecto al respaldo anterior.
3. Actualiza el respaldo en este repositorio únicamente cuando existen cambios.
4. Mantiene una copia adicional sincronizada mediante Google Drive como respaldo redundante.

## Uso

Este repositorio está destinado exclusivamente como respaldo para la plataforma **Alertas IRA** y no reemplaza al reposorio oficial del DEIS, el cual continúa siendo la fuente primaria de los datos.

## Fuente oficial

Repositorio DEIS – Atenciones de Urgencia:

https://repositoriodeis.minsal.cl/SistemaAtencionesUrgencia/
