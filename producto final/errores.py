"""Codigos estables de diagnostico para servidor, reles, termocuplas, agua, presiones y conversion de vacio."""
SOLUCIONES = {
    'SHUTDOWN_LOCKED': 'Shutdown en curso: mandos manuales y startup bloqueados. Emergency sigue disponible.',
    'SHUTDOWN_STATE': 'Consulte la etapa. Confirme cierre de gas solo cuando se solicite; no iniciar dos secuencias a la vez. Un fallo de mando requiere paro y revision.',
    'STARTUP_LOCKED': 'Espere que termine el startup y confirme el gas manual. El paro de emergencia sigue disponible.',
    'STARTUP_STATE': 'Consulte el estado del startup. Solo se inicia una vez por ejecucion; confirmar gas solo al final. Un fallo de mando requiere paro y revision, sin reintento automatico.',
    'VAC_TN906_STATE': 'Revisar panel Terranova 906A, salida analogica pin 13, common pin 9 y S0. 0 V indica LO y aproximadamente 3 V OFF/HI; no son presiones confiables. Usar Torr/mTorr. La salida analogica puede no distinguir fallos cerca del extremo superior.',
    'AUTO_TRANSFER': 'Comparar salida real Terranova 906A con su manual: la formula del manual ya esta aplicada. Validar fisicamente unidades y zona de cruce de ambos sensores antes de habilitar seleccion para control. Ver SELECCION_VACIO.md.',
    'AUTO_SENSOR': 'Revisar edad del paquete, errores y rangos de Medium/High. No ajustar gas con paquete repetido, vencido o sensor requerido invalido. Ver SELECCION_VACIO.md.',
    'AUTO_CONFIG': 'Integrar masscontroll.py y definir sensor de control, tolerancia, limites de caudal y significado del flujo deseado antes de habilitar AutoVacio.',
    'AUTO_VALUE': 'Usar lecturas validas y actuales, presion positiva, objetivo entre 0 y 760 Torr (exclusivos) y tolerancia desde cero hasta menos del objetivo. No enviar ajustes con lecturas invalidas.',

    'STOP_LATCHED': 'El paro esta enclavado. Revise el equipo y los errores de apagado antes de reiniciar main.py. No hay rearme desde el navegador.',
    'MFC_INPUT': 'Use una consigna numerica de 0 a 81.9%. La DAQC2 no genera 5 V; no reescalar 81.9% como 100%.',
    'MFC_READ': 'Revise ADCplate 3/S6, pin 2 del Aera, common y alimentacion. Se esperan 0-5 V. Confirmar gas/rango para SCCM.',
    'ROUGH_READ': 'Revise ADCplate address 3 y el cable del Roughing Vacuum Gauge: A en S4, B en S5, con su common.',
    'ROUGH_VALUE': 'La placa devolvio un valor no numerico. Revise comunicacion SPI y ADCplate 3.',
    'ROUGH_RANGE': 'Se esperan 0 a 10 V (0 V = 1e-3 Torr, 10 V = 1000 Torr). Revise alimentacion del sensor, cableado y common de S4/S5.',
    'MFC_DAC': 'Revise DAQC2plate address 4, driver piplates.DAQC2plate y DAC0. No se modifica la salida al arrancar.',
    'MFC_WRITE': 'Consigna incierta: revise DAQC2 4/DAC0 y su cable al pin 6 del Aera. Consulte de nuevo el estado. getDAC no confirma caudal ni posicion mecanica.',
    'VAC_GP270_ZERO': 'La salida es cero: revisar controlador, filamento, autorange y cableado. No mostrar cero Torr ni usar este valor en una grafica logaritmica.',
    'VAC_GP270_STATE': 'Revise el estado del filamento y active autorange en el GP270. El manual indica -10 a -12 V con filamento apagado o rango manual; no es una presion.',
    'VAC_GP270_RANGE': 'Revise salida Pressure del GP270, retorno analogico y S1. Se esperan 0 a -5 V; no invertir el signo ni limitar el valor para ocultar el fallo.',
    'VAC_READ': 'Revise ADCplate address 3, canal S indicado, salida analogica del controlador y referencia de tierra. Verifique que el controlador este alimentado y configurado con la transferencia del modelo indicado. No conectar a entradas I de corriente.',
    'VAC_VALUE': 'Se requiere un voltaje numerico finito de una entrada S de ADCplate address 3. Revise la lectura y el controlador del sensor; no use una entrada I de corriente ni una DAQC2.',
    'VAC_RANGE': 'La formula produjo desbordamiento o un resultado no representable. Revise el voltaje, la escala y que el sensor use la transferencia documentada de su controlador. No sustituya este error por cero Torr.',
    'WATER_TEMP_RANGE': 'Revise transmisor Water, alimentacion y lazo en ADCplate 3/I0. Se esperan 4-20 mA para 0-100 °C; no mostrar la señal fuera de rango como temperatura valida.',
    'WATER_TEMP_VALUE': 'ADCplate devolvio un valor no numerico o no finito para I0. Revise SPI y la alimentacion. No sustituya una respuesta invalida por cero.',

    'WATER_TEMP_READ': 'Revise ADCplate address 3, entrada I0 (indice logico 12), alimentacion y lazo del transmisor. La conversion configurada es (mA - 4) * 6.25 °C.',
    'PRESS_INIT': 'Revise Pi-Plates instalado, SPI, alimentacion y jumpers address 3 de ADCplate. Se reintenta cada 5 segundos. No ejecute Airpsi3.py a la vez que main.py.',
    'PRESS_READ': 'Revise la comunicacion con ADCplate y el canal indicado. Apague antes de modificar cableado; compruebe alimentacion del transmisor y su lazo de corriente.',
    'PRESS_VALUE': 'La placa no devolvio una corriente numerica finita. Revise SPI, libreria y alimentacion; esta respuesta no representa cero PSI.',
    'PRESS_RANGE': 'Compruebe alimentacion, continuidad y polaridad del lazo, que el transmisor sea 4-20 mA y su rango nominal. El PSI mostrado es solo la conversion y no es confiable. Menos de 4 mA se muestra como 0 PSI con aviso.',

    'TEMP_IMPORT': 'No se pudo importar THERMOplate o una dependencia. Revise el modulo indicado en Detalle e instale Pi-Plates en el mismo entorno Python que ejecuta main.py en la Raspberry.',
    'TEMP_ID': 'No se pudo identificar una THERMOplate en el address indicado. Revise alimentacion, SPI y, con el equipo apagado, los jumpers de direccion y el montaje del stack.',
    'TEMP_CONFIG': 'Revise temperaturas.py: canales unicos del 1 al 8, tipo k o j coincidente con cada sonda, address de 0 a 7 y frecuencia 50 o 60 Hz. Si los parametros son correctos, revise el detalle de comunicacion.',
    'TEMP_RANGE': 'La lectura excede el rango de conversion del tipo configurado. Compruebe tipo K/J, polaridad, continuidad y terminales con el equipo apagado. No es una alarma de sobretemperatura del proceso ni confirma que el sensor este roto.',

    'TEMP_INIT': 'Compruebe Pi-Plates instalado, SPI y alimentacion; con el sistema apagado revise jumpers address 2 de THERMOplate. Se reintenta la configuracion cada 5 segundos.',
    'TEMP_READ': 'Revise el canal indicado, apriete de terminales, polaridad +/-, continuidad y tipo de termocupla. Revise SPI si fallan todos los canales. No conecte el sensor a las entradas de ADCplate.',
    'TEMP_VALUE': 'No se muestra el valor recibido. Compruebe sensor abierto, polaridad, tipo K/J y conexion del canal. Los limites usados validan conversion, no seguridad del equipo.',

    'HW_IMPORT': 'Ejecute en la Raspberry con el entorno Python que tiene Pi-Plates y sus dependencias instaladas. Revise el nombre del modulo en Detalle.',
    'HW_INIT': 'Revise el detalle de inicializacion, SPI habilitado, permisos y compatibilidad del controlador GPIO con su Raspberry.',
    'HW_ID': 'Apague antes de revisar el montaje y los jumpers del address indicado. Compruebe alimentacion y SPI; una respuesta inesperada no prueba que la placa este danada.',
    'HW_READ': 'Revise alimentacion y conexion SPI de la placa indicada. Compruebe permisos de /dev/spidev* y cierre otros lectores que interfieran con el bus.',
    'HW_STATE': 'La respuesta no es una mascara valida de 0 a 255. Revise la comunicacion y la version de Pi-Plates; no interprete este valor como OFF.',
    'HW_WRITE': 'El resultado de la orden es incierto. Compruebe el estado real del equipo y la conexion de la placa antes de volver a ordenar. No se reintenta automaticamente.',
    'HW_CONFIRM': 'La orden se envio, pero no pudo confirmarse. Revise el equipo y el estado de la placa antes de repetir; el rele puede haber cambiado.',
    'INPUT': 'Use un equipo definido en manual_control.py y un estado booleano true/false. Recargue el GUI servido por main.py.',
    'HTTP_ORIGIN': 'Abra el GUI desde la direccion que imprime main.py, en el mismo origen que la API.',
    'HTTP_TYPE': 'La solicitud debe usar Content-Type: application/json. Actualice manual_control.js y recargue el GUI.',
    'HTTP_ROUTE': 'Abra / o /vacuum_controller.html en el servidor; revise la ruta solicitada.',
    'GUI_FILE': 'Restaure el archivo indicado en producto final y compruebe que el usuario puede leerlo.',
    'SERVER_BIND': 'Si el puerto esta ocupado, cierre la otra instancia o use python3 main.py --port 8001. Si faltan permisos, use un puerto mayor que 1023.',
    'BROWSER': 'Abra manualmente la URL indicada desde el escritorio de la Raspberry. Por SSH sin sesion grafica no se abrira una ventana local.',
    'INTERNAL': 'Consulte el traceback en la terminal y logs/control.log. Conserve el codigo, la hora y el detalle para depurar; no asuma que la orden fallo sin comprobar el rele.',
}


class ControlError(Exception):
    def __init__(self, code, message, detail='', **context):
        self.code, self.message, self.detail, self.context = code, message, str(detail), context
        super().__init__(self.text())

    def text(self):
        context = ' | '.join(f'{key}={value}' for key, value in self.context.items())
        return (f'[{self.code}] {self.message}' + (f' | {context}' if context else '')
                + (f' | Detalle: {self.detail}' if self.detail else '')
                + f' | Que revisar: {SOLUCIONES[self.code]}')

    def payload(self):
        return {'code': self.code, 'error': self.text(), 'context': self.context}
