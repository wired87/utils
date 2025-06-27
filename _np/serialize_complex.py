def serialize_complex(com, is_quark=False, is_energy=False):
    print("complex before s:", com)
    if is_quark:
        serialized_struct = []
        for i in range(3):
            row = com[i]  # com[i] ist eine 1D-Zeile (Spinor)
            serialized_row = [(z.real, z.imag) for z in row]
            serialized_struct.append(serialized_row)

    elif is_energy is True:
        serialized_struct = []
        for i in range(len(com)):
            row = com[i]  # com[i] ist eine 1D-Zeile (Spinor)
            row_struct = []
            for i in range(len(row)):
                serialized_row = (i.real, i.imag)
                row_struct.append(serialized_row)
            serialized_struct.append(row_struct)
    else:
        serialized_struct = [[(z.real, z.imag) for z in row] for row in com]

    print("serialized_struct", serialized_struct)
    return serialized_struct
