# -*- coding: utf-8 -*-
"""Edgefolio: la tienda de estrategias de TradingView, una herramienta zlecitool.

routes.py recibe las peticiones y tasks.py lanza lo que corre solo (el reloj del núcleo); catalogue, search,
pricing, orders, downloads, formats, free, mine, proofs, alerts, media y fx hacen el trabajo, sin Flask;
models.py son las tablas (edgefolio_*), en la base de datos común del núcleo.
"""
