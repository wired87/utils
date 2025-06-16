import random
import string


def generate_id(length=40):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))