import json
from fractions import Fraction
import numpy as np
from utils.logger import LOGGER





def serialize_complex_process(com, restore=False, bytes=True):
    """
    Serialisiert oder deserialisiert ein beliebig verschachteltes Array oder Listenstruktur.
    """
    try:
        data=True
        if restore:
            return deserialize_complex(com)

        if isinstance(com, (complex, np.complexfloating, np.complex128)):
            data = [com.real, com.imag]

        elif isinstance(com, (list, tuple, np.ndarray)) and isinstance(com[0], (list, tuple, np.ndarray)):
            data = [serialize_complex_process(item) for item in com]

        elif isinstance(com, (list, tuple, np.ndarray)) and isinstance(com[0], (complex, np.complexfloating, np.complex128)):
            data = [[item.real, item.imag] for item in com]



            """data = {
                "dtype": str(com.dtype),
                "shape": com.shape
            }
            if bytes is True:
                data.update(
                    {"bytes": base64.b64encode(com.tobytes()).decode("utf-8")}
                )
            else:
                data.update(
                    {"data": com.tolist()}
                )"""
        else:
            raise ValueError(f"Unknown serialize type, {com, type(com)}")
        #print(">>>return data", data)
        return data


    except Exception as e:
        if isinstance(com, dict):
            for k,v in com.items():
                print(f"{k} type:", type(v))
        print("Serialization error", e, com)
    return com



def serialize_complex(com, restore=False, bytes=True):
    #print("Before serialization:", com)
    data = {"serialized_complex": serialize_complex_process(
        com, restore, bytes
    )}
    #print("After serialization:", data)
    return data


def deserialize_complex(bytes_struct, from_json=True, key=None, **args):
    """
    Deserialisiert ein einzelnes oder verschachteltes serialisiertes Array.
    """

    LOGGER.info(f"bytes_struct {bytes_struct}")
    LOGGER.info(f"key {key}")

    # Falls String, erst JSON laden
    if from_json and isinstance(bytes_struct, str):
        bytes_struct = json.loads(bytes_struct)

    elif isinstance(bytes_struct, dict):
        bytes_struct = bytes_struct["serialized_complex"]
    if (
            isinstance(bytes_struct, list)
            and len(bytes_struct) == 2
            and all(isinstance(x, (int, float)) for x in bytes_struct)
    ):
        #print(" len(bytes_struct) == 2 v  bytes_struct", bytes_struct)
        restored = np.complex128(complex(bytes_struct[0] + bytes_struct[1]))

    elif isinstance(bytes_struct, list) and isinstance(bytes_struct[0], list):
        restored = np.array([deserialize_complex(item) for item in bytes_struct])

        """elif isinstance(bytes_struct, list) and isinstance(bytes_struct[0], (int, float)):
            restored = np.complex128(complex(bytes_struct[0], bytes_struct[1]))
        """
    else:
        # Hier Base64 DEKODIEREN
        """b = base64.b64decode(bytes_struct["bytes"])
            #data = bytes_struct["data"]
            array_type = np.dtype(bytes_struct["dtype"])
            array_shape = tuple(bytes_struct["shape"])
            restored_data = np.frombuffer(b, dtype=array_type).reshape(array_shape).copy()
            #restored_data = np.array(data, dtype=array_type).reshape(array_shape)
        """

        restored = bytes_struct
    #print(f"deserialized complex: {restored}")
    return restored

def check_serilisation(data):
    # is data serializable?
    try:
        # yes:
        json.dumps(data)
        return data
    except Exception as e:
        # no -> serialize

        LOGGER.info(f"Serialisation Error: {e}")
        serialized = serialize_complex(data)
        #print(">>serialized", serialized)
        return serialized

def convert_numeric(v):
    try:
        return Fraction(v)
    except Exception as e:
        return v


def check_serialize_dict(data, attr_keys):
    # why attr_keys? -> serialize self.__dict__
    new_dict={}
    for k, v in data.items():
        if k in attr_keys:
            #print("Convert sd key:", k, type(v), v)
            v = check_serilisation(v)
            new_dict[k] = v
    return new_dict