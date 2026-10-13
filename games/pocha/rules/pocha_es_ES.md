# Pocha — referencia rápida

*La pocha (también llamada «la podrida») es un juego de cartas tradicional español sin libro de reglas oficial de ninguna editorial, y las reglas varían según la región y la familia. Esta hoja se ajusta a lo que coinciden varias descripciones de reglas y a lo que puntúa la app. Acordar las variantes siguientes antes de empezar. 3–6 jugadores.*

## Objetivo

Antes de cada mano, cada jugador predice exactamente cuántas bazas ganará. Se puntúa acertando **exactamente**, no ganando más bazas. **Gana el total más alto tras la última mano.**

## Baraja y triunfo

- **Baraja española de 40 o 48 cartas.** Orden de las cartas, de mayor a menor: as, 3, rey, caballo, sota, 9, 8, 7, 6, 5, 4, 2. Las cartas no tienen puntos.
- Se reparte una carta cada vez. La siguiente carta se da la vuelta boca arriba y su palo es el **triunfo** (*trump*). Cualquier triunfo gana a cualquier carta de otro palo.
- Con 3 jugadores se suelen quitar los doses. En las manos de 8 cartas pueden participar como máximo 5 jugadores (8 x 5 = 40, toda la baraja de 40 cartas), y hasta 6 si se usa la baraja de 48 cartas.

## Manos

El número de cartas repartidas cambia en cada mano. La app usa 18 manos:

| Manos | Cartas por jugador |
|---|---|
| De la 1 a la 7 | 1, 2, 3, 4, 5, 6, 7 (subiendo) |
| De la 8 a la 11 | 8 cartas, cuatro manos seguidas |
| De la 12 a la 18 | 7, 6, 5, 4, 3, 2, 1 (bajando) |


## Apuestas

- Empezando por el jugador que sale (a la derecha del repartidor) y terminando con el repartidor, cada jugador dice cuántas bazas espera ganar.
- **Restricción del último apostador:** el último jugador en apostar **no** puede elegir un número que haga que la suma de todas las apuestas sea igual al número de bazas de la mano. Por tanto, al menos un jugador debe fallar.

## Juego

- El jugador a la derecha del repartidor sale con cualquier carta.
- Debes **servir el palo** si puedes. Si no puedes, debes jugar un **triunfo** si tienes alguno. Si no tienes ninguno de los dos, juega cualquier carta.
- Las fuentes no coinciden en si también debes **superar** la carta ganadora cuando puedas (una carta más alta del palo de salida, o un triunfo más alto). Acordar esto primero.
- Si se saca un triunfo, todos los que tengan triunfo deben jugar uno.
- Gana la baza el triunfo más alto o, si no lo hay, la carta más alta del palo de salida. El ganador saca la siguiente baza.

## Puntuación

La puntuación habitual publicada es **10 puntos más 5 por baza ganada** por una apuesta exacta, y **-5 por baza de diferencia** (por exceso o por defecto) por un fallo.

**La app puntúa 3 puntos por baza en su lugar:**

| Resultado | Puntos |
|---|---|
| Apuesta exacta | 10 + 3 por baza ganada |
| Apuesta fallida | -3 por baza de diferencia (por exceso o por defecto) |

Ejemplo en la app: apuesta 3 y gana 3 = 19 puntos. Apuesta 3 y gana 1 = -6.

Una apuesta de cero que se cumple puntúa 10 fijos. Consulta la regla de tu mesa si juegas con otro valor.

## Empates y otras variantes

- Si los totales finales empatan, las reglas habituales dicen que se reparten manos extra de una carta hasta romper el empate, o que se prefiera al jugador con menos apuestas fallidas. La app simplemente **comparte la victoria** entre los jugadores empatados.
- Variantes que puedes encontrar y que la app no puntúa: una jugada «Pocha» que vale 100 puntos con 5 o más jugadores, manos con el triunfo elegido por subasta, manos sin triunfo, manos en las que solo ves las cartas de los demás, y multiplicadores de puntuación para ciertos palos de triunfo.
- Las penalizaciones por jugar una carta incorrecta (*renuncio*) suelen acordarse de antemano.

## Consejos para Gamelog

- El tablero cuenta las manos y muestra cuántas cartas repartir. Las cuatro manos de 8 cartas llevan cada una el nombre de un palo, usando los nombres de palo de la baraja elegida (en español: oros, copas, espadas, bastos). Las demás manos se indican como «subiendo» o «bajando».
- Para cada jugador, introduce la apuesta y las bazas ganadas. Las bazas ganadas deben sumar el número de cartas repartidas en esa mano.
- Al introducir las apuestas, la app **bloquea la última apuesta que haría que el total sea igual a las cartas repartidas**, para el jugador que sea el último sin apuesta; por eso introduce las apuestas en orden de juego, con el repartidor al final.
- La puntuación usa los 10 + 3 por baza y -3 por baza de diferencia de la app, no los 5 puntos de la mayoría de reglas escritas.
