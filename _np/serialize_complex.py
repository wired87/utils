import numpy as np

def serialize_complex(com, restore=False):
    """
    Serialisiert oder deserialisiert ein beliebig verschachteltes Array oder Listenstruktur.
    """
    if restore:
        return deserialize_complex(com)

    if isinstance(com, list):
        restored = [serialize_complex(item) for item in com]
    else:
        restored =         {
            "bytes": com.tobytes(),
            "dtype": str(com.dtype),
            "shape": com.shape
        }
    print("serialize_complex", restored)
    return restored


def deserialize_complex(bytes_struct):
    """
    Deserialisiert ein einzelnes oder verschachteltes serialisiertes Array.
    """
    if isinstance(bytes_struct, list):
        return [deserialize_complex(item) for item in bytes_struct]
    else:
        b = bytes_struct["bytes"]
        array_type = np.dtype(bytes_struct["dtype"])
        array_shape = bytes_struct["shape"]
        restored = np.frombuffer(b, dtype=array_type).reshape(array_shape)
        print("deserialize_complex",restored)

        return restored
