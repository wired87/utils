import jax.numpy as jnp


# --- Mathematische Kern-Operationen ---
def op_add(x, p): return x + p


def op_sub(x, p): return x - p


def op_mul(x, p): return x * p


def op_div(x, p): return x / (p + 1e-6)


def op_pow(x, p): return jnp.power(x, p)


def op_negate(x, p=None): return -x


# --- JAX / Numpy Funktionen ---
def op_dot(x, p):    return jnp.dot(x, p)


def op_matmul(x, p): return jnp.matmul(x, p)


def op_sum(x, p=None): return jnp.sum(x)


def op_mean(x, p=None): return jnp.mean(x)


def op_exp(x, p=None): return jnp.exp(x)


def op_log(x, p=None): return jnp.log(x + 1e-6)


def op_abs(x, p=None): return jnp.abs(x)


def op_sin(x, p=None): return jnp.sin(x)


def op_cos(x, p=None): return jnp.cos(x)


def op_sqrt(x, p=None): return jnp.sqrt(x)

def op_hermitian_matmul(x, p=None): return x.conj().T

# --- Hilfsfunktionen ---
def op_assign(x, p=None): return x


def plus_single(x, p=None): return x


OPS = {
    # Arithmetik
    '+': op_add,
    '-': op_sub,
    '*': op_mul,
    '/': op_div,
    '**': op_pow,
    '^': op_pow,  # Alias für den Extractor
    'neg': op_negate,
    '+s': plus_single,

    # Lineare Algebra / JNP Spezifisch
    'dot': op_dot,
    'matmul': op_matmul,
    '@': op_matmul,
    'sum': op_sum,
    'mean': op_mean,

    # Mathematische Funktionen
    'exp': op_exp,
    'log': op_log,
    'abs': op_abs,
    'sqrt': op_sqrt,
    'sin': op_sin,
    'cos': op_cos,

    # Zuweisung
    '=': op_assign
}