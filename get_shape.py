import numpy as np


def get_modular_shape(item):
    """
    Ermittelt den Shape für komplexe Dicts, Skalare und tief verschachtelte Listen.
    """
    # 1. Prüfe auf Skalar-Endpunkte (Die 'Blätter' des Baums)
    # Ein komplexes Dict ist ein Blatt, genau wie ein Float oder Int.
    is_complex_dict = isinstance(item, dict) and 'real' in item and 'imag' in item
    if is_complex_dict or isinstance(item, (int, float, complex, np.number)):
        return ()

    # 2. Prüfe auf Listen/Arrays (Die 'Äste' des Baums)
    if isinstance(item, (list, tuple, np.ndarray)):
        n = len(item)
        if n == 0:
            return (0,)

        # Rekursion: Wir holen den Shape des Inhalts.
        # WICHTIG: Wir gehen davon aus, dass die Struktur innerhalb eines Items
        # konsistent ist (homogen), wie bei Tensoren/Matrizen üblich.
        inner_shape = get_modular_shape(item[0])
        return (n,) + inner_shape

    # Falls ein leeres Dict oder unbekannter Typ kommt, behandeln wir es als Skalar-Platzhalter
    return ()