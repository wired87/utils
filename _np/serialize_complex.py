import base64
import json
import numpy as np

def serialize_complex(com, restore=False):
    """
    Serialisiert oder deserialisiert ein beliebig verschachteltes Array oder Listenstruktur.
    """
    if restore:
        return deserialize_complex(com)

    if isinstance(com, list):
        return [serialize_complex(item) for item in com]
    else:
        return {
            "bytes": base64.b64encode(com.tobytes()).decode("utf-8"),
            "dtype": str(com.dtype),
            "shape": com.shape
        }


def deserialize_complex(bytes_struct, from_json=True):
    """
    Deserialisiert ein einzelnes oder verschachteltes serialisiertes Array.
    """
    print("bytes_struct",bytes_struct)
    # Falls String, erst JSON laden
    if from_json and isinstance(bytes_struct, str):
        bytes_struct = json.loads(bytes_struct)

    if isinstance(bytes_struct, list):
        return [deserialize_complex(item) for item in bytes_struct]
    else:
        # Hier Base64 DEKODIEREN
        b = base64.b64decode(bytes_struct["bytes"])
        array_type = np.dtype(bytes_struct["dtype"])
        array_shape = tuple(bytes_struct["shape"])
        restored = np.frombuffer(b, dtype=array_type).reshape(array_shape)
        print("return", restored)
        return restored
