# Vídeos · Edgefolio

Cada guía tiene su vídeo, en el canal de YouTube de tuisku: **nunca en el repo** (aquí van su guion y su
enlace; las imágenes, sí, en GitHub). El estándar: `docs/estandar/MARKET.md` §5 del núcleo; cómo se graba,
`docs/estandar/VIDEO.md`.

| Vídeo | Tipo | De qué sale | Guion | Idioma | YouTube | Duración | Estado |
|---|---|---|---|---|---|---|---|
| Cómo se compra en Edgefolio | guía de usuario | `docs/FLUJO_USUARIO.md` | [scripts/user-guide.md](scripts/user-guide.md) | es | | 1:49 | por regrabar (abajo) |
| Cómo se administra Edgefolio | guía de administración | `docs/FLUJO_ADMINISTRADOR.md` | [scripts/admin-guide.md](scripts/admin-guide.md) | es | | 0:56 | grabado, sin voz |
| Edgefolio en un minuto | comercial | `PITCH.md`, `MESSAGES.md` | — | es | | | por escribir |

**La última grabación** (2026-11-25, la rama `claude/ciclo-036` en el commit d920601, con el código de
`_ztool_dev` 5fe0ef4a y el núcleo 0.35.0, en escritorio, 1366 × 768, con Chromium sin ventana): cada guía con
su guion (`.md`), sus subtítulos (`.srt`) y sus frases para la API de voz (`.voz.json`) aquí, en `scripts/`.
Los vídeos mudos (`.mp4` y `.webm`) y una demostración con la voz provisional de Windows y los subtítulos
(`.demo.mp4`) están fuera de git, en `pruebas/2026-11-24_edgefolio_video/video/` de la carpeta de trabajo del
dueño, con los scripts que los graban y los montan (`scripts/servir.py`, `grabar.py` y `montar.py`). Falta la
voz de verdad: el servicio aún no está elegido.

- **La guía de usuario** se graba con la sesión de una cuenta de prueba ya abierta (entrar es del núcleo y no
  sale) y con el PayPal de prueba de la tienda: «Pagar» va directo a Gracias. Con el PayPal de verdad, entre
  los dos sale la página de PayPal: la voz ya dice «paga con PayPal». **Por regrabar** desde el 2026-11-25: en su
  escena U11 (1:11) la fila de confianza aún dice «Factura por correo», y la tienda ya dice «Recibo por correo»
  (`docs/DECISIONES.md`). El guion no cambia: la voz no nombra la factura. Antes de YouTube (la voz de verdad y el
  sí del dueño), se graba otra vez con los mismos scripts.
- **La guía de administración** es el panel del núcleo (`docs/FLUJO_ADMINISTRADOR.md`): sólo lo que le toca a
  la tienda (Métricas, Sistema, Registro, Mensajes de contacto).

Un idioma más es otra fila, con el guion traducido (`scripts/user-guide.en.md`). Si el flujo cambia, su guion
cambia en el mismo cambio y el vídeo pasa a «por regrabar».
