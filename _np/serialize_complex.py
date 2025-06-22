def serialize_complex(com):
    return [[(z.real, z.imag) for z in row] for row in com]
