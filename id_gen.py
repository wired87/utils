import random
import string


def generate_id(length=20):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length)).lower()