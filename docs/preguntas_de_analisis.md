# Preguntas de análisis

Corte de los datos: 01-01-2024. Cada pregunta se responde en la aplicación (`web/index.html`) y aparece en la sección «6. Preguntas de análisis» del reporte PDF. Las cifras de abajo son las que muestra la app con los filtros por defecto (reserva 2P, sin filtros). Al cambiar la reserva (1P/2P/3P), la ubicación o el buscador, las respuestas del reporte se recalculan.

## 1. ¿Dónde se concentran las reservas?
**Dónde se ve:** pestaña *Resumen* («Reservas por ubicación», «Campos más grandes») y pestaña *Gráficas* («Pastel: ¿quién concentra la reserva?» y «Pareto: concentración acumulada»). Filtros: reserva y ubicación.

**Respuesta (2P):** las reservas suman 15,497 MMBPCE. Marino concentra 52.6 % (106 campos), Terrestre 42.7 % (357 campos) y Aguas someras 4.8 % (14 campos). Los 10 campos mayores reúnen 46.8 % y bastan 52 de los 477 campos para llegar a 80 %.

**Con filtro (Marino):** 8,145 MMBPCE; los 10 mayores reúnen 64.9 % y bastan 20 campos para el 80 %. Con 3P, los 10 mayores reúnen 43.4 % y se necesitan 58 campos.

**Cómo leerlo:** la reserva está muy concentrada: pocos campos grandes y muchos pequeños (31 campos tienen 2P = 0).

## 2. ¿Qué tan seguras son las reservas?
**Dónde se ve:** pestaña *Gráficas* («1P vs 2P vs 3P por ubicación») y los hallazgos de *Resumen*. Filtros: ubicación.

**Respuesta:** solo 36.2 % de la reserva 3P está probada (1P 8,359 de 23,089 MMBPCE); el resto es probable (2P − 1P) o posible (3P − 2P) y depende de confirmación. De los 50 campos con 3P ≥ 100 MMBPCE, 7 no tienen nada probado (1,104.9 MMBPCE de 3P) y 16 tienen menos de 10 %. Zama es un caso grande: 36.7 MMBPCE en 1P frente a 707.2 en 3P (≈ 5 %).

**Con filtro (Marino):** 40.9 % probado (1P 4,996 de 12,218 MMBPCE).

**Cómo leerlo:** 3P es un escenario optimista (probabilidad ≥ 10 %), no una cifra segura. La certeza se calcula como 1P / 3P.

## 3. ¿Existe relación entre la superficie de un campo y sus reservas?
**Dónde se ve:** pestaña *Gráficas* («Dispersión: superficie vs reserva», escala logarítmica). Filtros: reserva y ubicación.

**Respuesta (2P):** con 401 campos que tienen superficie y reserva, la correlación en escala logarítmica es 0.46 (moderada): un campo más grande tiende a tener más reserva, pero el tamaño no la determina. La densidad mediana es 0.09 MMBPCE/km² en campos terrestres y 1.37 en marinos.

**Con filtro (Marino):** 95 campos, correlación 0.40. Con 3P: 422 campos, correlación 0.48.

**Limitaciones:** 48 campos no traen superficie y quedan fuera del cálculo. Una correlación moderada no implica causalidad: la densidad depende de la ubicación y del tipo de yacimiento.

## 4. ¿Cuántos pozos hay y cuántos están activos?
**Dónde se ve:** pestaña *Pozos* («Estado de los pozos» y «Campos con más pozos»). Filtros: reserva, ubicación y campo.

**Respuesta:** en los campos con reserva hay 26,613 pozos: 6,771 activos (25 %), 19,826 inactivos y 16 sin dato. El campo con más pozos es TAMAULIPAS CONSTITUCIONES (875). Con el filtro Marino: 2,120 pozos, 634 activos (30 %); el campo con más pozos es AKAL (484).

**Dato global:** el archivo de pozos tiene 34,147 pozos, de los cuales 6,886 están activos (20.2 %). Los 7,534 pozos que no pertenecen a ninguno de los 477 campos con reserva no entran en las respuestas por campo.

**Supuesto de clasificación:** «Activo» agrupa estados como productor, inyector y operando; «Inactivo» agrupa cerrado, taponado, abandonado, suspendido y similares. El resultado depende de esa regla.