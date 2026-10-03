"""Mass flow reservado: solo consigna cero simulada para Emergency."""
class MassControl:
    def set_percent(self, percent):
        if percent != 0: raise ValueError('Mass flow no habilitado')
        return {'command_percent':0,'simulation':True}

