# Edgefolio · Flujo de quien administra

- **Qué es:** lo que hace quien administra tuisku con la tienda. Edgefolio **no tiene administración
  propia**: no hay empresas, miembros ni pantallas de administración suyas. Lo de quien administra es el
  **panel del núcleo** (`/zt/admin`), el mismo en todas las herramientas, filtrado por `edgefolio`.
- **De dónde sale:** recorrido en un navegador el 2026-11-25, con el código de `_ztool_dev` (5fe0ef4a, núcleo
  0.35.0), datos nuevos y la cuenta de prueba `admin@pruebas.test` en `ZLECITOOL_ADMINS`. Hasta ese día no
  había ningún documento que lo contara (DOCS.md §2 del núcleo: Edgefolio, «sin él»).
- **Documentos hermanos:** lo de quien compra, `FLUJO_USUARIO.md` (pantallas 1–9); lo que se guarda,
  `DATOS.md`. Las pantallas del panel son del núcleo: no llevan número de `PANTALLAS.md`.
- **Lo que no está en el panel** (A8): publicar un catálogo nuevo, los pedidos y las ventas con PayPal.

**Quién entra.** Una cuenta cuyo correo está en `ZLECITOOL_ADMINS`, con el correo **demostrado** (entrando
una vez con un enlace por correo o restableciendo la contraseña; lo dice el propio panel en «Sistema»). Sin
eso, el panel no se abre.

## A1 · Abrir el panel

| Elemento | Clic → resultado |
|---|---|
| El menú de la cuenta (arriba a la derecha, la inicial y el correo) | Además de lo de todas las cuentas (Mi cuenta, Créditos, Historial de créditos, Contacto, Salir), trae **Métricas** y **Mensajes de contacto** |
| **Métricas** | `/zt/admin`, la primera pestaña del panel |
| **← Volver a la app** | vuelve a la tienda |

Las pestañas del panel: Métricas, Calidad, Tutorial, Sistema, Registro, Mensajes de contacto y Clientes.

## A2 · Métricas

- El periodo (**7 días**, **30 días**, **90 días**) y la herramienta (**Todas las herramientas** o
  **edgefolio**).
- Las tarjetas: cuentas activas (nuevas y en total), operaciones, créditos gastados, ingresos, coste de IA,
  por crédito, margen y mensajes de contacto sin atender; debajo, las operaciones y el coste de IA por día
  (con «Ver como tabla»), los créditos por tipo, los trabajos en segundo plano y las tablas por operación,
  por herramienta, por modelo de IA y de quién gasta más (con «Descargar CSV»).
- **En la tienda sólo dicen algo las cuentas y los mensajes.** Edgefolio no usa créditos ni IA (cobra con
  PayPal, `tool.json` sin `"prices"`), así que sus operaciones, créditos, coste de IA y margen salen a 0; y
  **sus ventas no salen en «Ingresos»**, que cuenta las compras de créditos del núcleo: los pedidos de la
  tienda están en su tabla `edgefolio_order` (`DATOS.md`). Saldrán cuando los pagos pasen al núcleo
  (`ESTADO.md`, «Lo que falta»).

## A3 · Calidad

Las valoraciones de los resultados de la IA, por prompt y versión. En la tienda, siempre vacía: «Todavía no
hay valoraciones en este periodo».

## A4 · Tutorial

El tutorial de bienvenida **del núcleo**: quién lo terminó y en qué paso lo cerró quien se fue. La tienda no
lo usa (su recorrido de bienvenida de tres pasos es el del diseño, `FLUJO_USUARIO.md`, pantalla 1), así que
aquí sale «Nadie ha visto aún el tutorial» para `edgefolio`.

## A5 · Sistema

Lo que más le toca a la tienda:

- **Tareas programadas:** las tres de la tienda (`"schedule"` de `tool.json`), con cuándo tocan, la próxima
  vez y su estado: `fx_update` (los cambios de moneda, los días laborables a las 17:00 de Madrid),
  `send_alerts` (los avisos de las favoritas, cada día a las 09:00) y `purge` (lo que ya no se guarda, a las
  04:00). Sin `ZLECITOOL_PUBLIC_URL`, arriba sale el aviso de que lo de fuera de una petición no puede llevar
  enlaces (los avisos de las favoritas no saldrían).
- **Administradores:** las cuentas de `ZLECITOOL_ADMINS`, con «demostrado» y si tienen segundo factor.
- **Privacidad:** «Borrar mi cuenta» sale; la parte de la tienda (`edgefolio`, su versión del núcleo, si sirve
  la cola y su último latido) y lo que el borrado no alcanza.
- Y lo del núcleo: el segundo factor, el registro de actividad, el gasto en IA del mes, las copias de
  seguridad (con «Hacer una copia ahora»), la caché de PDF, los errores pendientes, los avisos (la tienda no
  tiene) y la app del móvil (la tienda no se instala).

## A6 · Registro

Todo lo apuntado en todas las herramientas (entradas, contraseñas, cuentas borradas, descargas de datos,
pagos del núcleo…), con un filtro **Qué**. Lo de la tienda que sale aquí es lo de las cuentas del núcleo:
sus pedidos y sus descargas van a su log (`tecnico/LOGS.md`), no al registro.

## A7 · Mensajes de contacto y Clientes

- **Mensajes de contacto:** los que llegan por Contacto (el pie y el menú de la cuenta), con el periodo, la
  herramienta y «Sin atender» o «Atendido», y «Descargar CSV».
- **Clientes:** las empresas. Edgefolio es pública y no se vende a empresas: «Aún no hay empresas».

## A8 · Lo que no está en el panel

- **Publicar un catálogo nuevo** del generador: `flask --app app edgefolio import …` en el servidor
  (README, «Publicar un catálogo nuevo», y `catalogue-updates.md`).
- **Los pedidos y las ventas con PayPal**, los enlaces de descarga y las gratis: en la base de datos
  (`edgefolio_*`) y en el log de la tienda. No hay pantalla para verlos; con los pagos en el núcleo, las
  ventas pasarán a «Métricas» e «Ingresos».
- **Las tareas a mano:** `flask --app app edgefolio fx-update`, `send-alerts`, `levels`, `subscribers` y
  `restore-scripts` (README, «Comandos»).
