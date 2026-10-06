# Conversion Medium y seleccion de sensor para AutoVacio

## Terranova 906A: formula aplicada

Por instruccion del usuario se usa la transferencia del [manual Duniway
Terranova 906A, revision 0817NC, paginas 13–14](https://www.duniway.com/sites/default/files/images/_pg/Terranova906A-Manual.pdf):

`P(mTorr) = 10^(2V)`; al dividir entre 1000, `P(Torr) = 10^(2V - 3)`.
El controlador debe estar configurado en Torr/mTorr. La salida analogica llega
al ADCplate address 3/S0. El manual identifica salida pin 13 y common pin 9
del conector INPUT/OUTPUT. Esta formula reemplaza la anterior de base 972B.

| Voltaje | Torr |
|---|---|
| 0.5 V | 0.01 |
| 1 V | 0.1 |
| 1.5 V | 1 |
| 2 V | 10 |
| 2.5 V | 100 |

`terranova906a_a_torr` valida la entrada y la usa `leer_vacios`. El manual
asocia 0 V a LO y aproximadamente 3 V a OFF/HI. Se rechazan valores <=0 o >=3 V
con VAC_TN906_STATE. Cerca de 3 V puede haber ambiguedad entre presion alta y
estado: este chequeo no garantiza detectar toda desconexion. No se sustituye
un error por cero Torr. High conserva su formula separada.

## Rangos usados y regla de seleccion

Estos son rangos de los instrumentos/ruta de lectura, no una clasificacion universal de vacio.

| Lectura | Rango nominal del instrumento | Rango admitido por el selector |
|---|---|---|
| Medium, Terranova 906A, S0 | 0.0001 a 1000 Torr | 0.001 a 1000 Torr, con lectura sin error de la ruta analogica |
| High, GP270, S1 | 3e-9 a 1.2e-3 Torr, lectura de ionizacion | 3e-9 a 0.001 Torr, limitado por la conversion analogica actual |

Rango GP270: [manual del fabricante, especificaciones seccion 1.2](https://www.idealvac.com/files/manualsII/Granville-Phillips_270_Manual.pdf).
Rango Terranova: manual enlazado arriba, pagina 3; la salida analogica y sus
estados se describen en paginas 13–14. El rango nominal del instrumento no
implica que toda su salida analogica sea utilizable con esta conversion.

### Comportamiento implementado

El limite de cambio es **1 × 10⁻³ Torr** (0.001 Torr). El regreso se decide
con Medium, sin esperar que la conversion de High supere su maximo.

| Condicion, en orden de prioridad | Seleccion |
|---|---|
| Medium valido > 1 × 10⁻³ Torr y <= 1000 Torr | Medium, incluso si High sigue indicando vacio alto, satura o falla |
| No hay Medium valido por encima del limite y High valido entre 3 × 10⁻⁹ y 1 × 10⁻³ Torr | High |
| Medium = 1 × 10⁻³ Torr, pero High no disponible/valido | Medium |
| Ninguna de las anteriores | AUTO_SENSOR; no calcular ajuste de gas |

Ejemplo: al bajar, High = 1 × 10⁻⁴ Torr y Medium = 1 × 10⁻³ Torr seleccionan
High. Al subir, Medium = 2 × 10⁻³ Torr devuelve el control a Medium aunque
High permanezca en 1 × 10⁻³ Torr. Mientras Medium continue sobre el limite,
no se vuelve a High por una lectura baja de este ultimo.

No se exige que ambos valores coincidan. High puede usarse si Medium falta o
marca error, siempre que High sea valido; no se inventa una presion para Medium.
Una lectura Medium con error, no finita, booleana o fuera de rango no fuerza
el regreso. Un fallo de High por si solo tampoco fuerza el regreso: se requiere
Medium valido. Ambos sin lectura util producen error, no una orden de gas.

El cambio es inmediato, sin histeresis ni tres muestras de confirmacion. En
el limite exacto se prefiere High si es valido. Paquetes futuros, repetidos,
fuera de orden o con mas de 3 segundos se rechazan. Las oscilaciones reales
cerca del limite pueden alternar la seleccion; queda comprobarlo fisicamente.
Los umbrales antiguos 0.0005/0.0008 Torr ya no se utilizan.

## Integracion y alcance

`selector_vacio.py` conserva el sensor seleccionado. `accion_con_sensores` en
`autovacio.py` usa su presion para calcular ABRIR_MAS, CERRAR_MAS o MANTENER.
No escribe al DAC ni a los reles. El llamador debe serializar acceso y entregar
paquetes nuevos. El selector no esta conectado a un ciclo actuador en main.py.
AutoVacio permanece deshabilitado por la integracion y parametros pendientes,
no por exigir que ambos sensores coincidan. Startup sigue usando Medium y
termina con regulacion manual. El limite del mass flow sigue en 81.9%.

## Errores y verificacion

- VAC_TN906_STATE: revisar panel, señal analogica, common, S0 y unidades.
- AUTO_SENSOR: paquete o sensor requerido invalido; no producir ajuste de gas.
- Las fallas no envian por si mismas una nueva consigna ni apagan equipos: falta integrar la respuesta del ciclo automatico.

`tests/test_selector_vacio.py` prueba entrada a High sin concordancia con Medium,
extremos, regreso decidido por Medium con High saturado o fallido, permanencia en Medium, paquetes invalidos
y direccion del ajuste. `tests/test_vacio.py` verifica conversion y aislamiento
de fallos. Las pruebas no sustituyen la validacion con los instrumentos.
