from graphviz import Digraph

class Nodo:
    def __init__(self, valor, izquierda=None, derecha=None):
        self.valor = valor
        self.izquierda = izquierda
        self.derecha = self.derecha = derecha
        self.id = id(self)

class State:
    _next_id = 0
    def __init__(self):
        self.id = State._next_id; State._next_id += 1
        self.edges = {}
        self.eps = set()

class Fragment:
    def __init__(self, start, accepts):
        self.start = start
        self.accepts = set(accepts)

def construir_arbol(postfix):
    pila = []
    for token in postfix:
        if token in {'*', '+', '?'}:
            if not pila:
                raise ValueError(f"Falta operando para '{token}'")
            nodo = Nodo(token, izquierda=pila.pop())
            pila.append(nodo)
        elif token in {'.', '|'}:
            if len(pila) < 2:
                raise ValueError(f"Faltan operandos para '{token}'")
            der = pila.pop()
            izq = pila.pop()
            nodo = Nodo(token, izquierda=izq, derecha=der)
            pila.append(nodo)
        else:
            pila.append(Nodo(token))
    if len(pila) != 1:
        raise ValueError("La expresión no está balanceada: sobran nodos")
    return pila[-1]

def dibujar_arbol(raiz, filename):
    dot = Digraph()
    def agregar_nodos(nodo):
        if nodo is None: return
        dot.node(str(nodo.id), nodo.valor)
        if nodo.izquierda:
            dot.edge(str(nodo.id), str(nodo.izquierda.id))
            agregar_nodos(nodo.izquierda)
        if nodo.derecha:
            dot.edge(str(nodo.id), str(nodo.derecha.id))
            agregar_nodos(nodo.derecha)
    agregar_nodos(raiz)
    dot.render(filename, format='png', cleanup=True)

def expandir_clases(expr):
    resultado = ''
    i = 0
    while i < len(expr):
        if expr[i] == '\\':
            if i + 1 < len(expr):
                resultado += expr[i:i+2]
                i += 2
            else:
                raise ValueError("Escape incompleto")
        elif expr[i] == '[':
            i += 1
            contenido = ''
            while i < len(expr) and expr[i] != ']':
                contenido += expr[i]
                i += 1
            if i < len(expr) and contenido:
                resultado += '(' + '|'.join(contenido) + ')'
                i += 1
            else:
                raise ValueError("Clase de caracteres sin cerrar o vacía")
        else:
            resultado += expr[i]
            i += 1
    return resultado

def insertar_concatenaciones(expr):
    if not expr:
        return expr
    resultado = ''
    i = 0
    while i < len(expr) - 1:
        c1 = expr[i]
        c2 = expr[i + 1]
        resultado += c1
        if c1 == '\\':
            i += 1
            resultado += expr[i]
            if i + 1 < len(expr):
                c2 = expr[i + 1]
            else:
                break
        if (
            (c1 in {'*', '+', '?', ')', 'ε'} or c1.isalnum()) and
            (c2 in {'(', 'ε'} or c2.isalnum() or c2 == '\\')
        ):
            resultado += '.'
        i += 1
    resultado += expr[-1]
    return resultado

def expandir_operadores(expr):
    i = 0
    resultado = ''
    while i < len(expr):
        if expr[i] == '\\':
            if i + 1 < len(expr):
                resultado += expr[i:i+2]
                i += 2
            else:
                raise ValueError("Escape incompleto")
        elif expr[i] == '+':
            if resultado and resultado[-1] == ')':
                count = 0
                j = len(resultado) - 1
                while j >= 0:
                    if resultado[j] == ')': count += 1
                    elif resultado[j] == '(':
                        count -= 1
                        if count == 0: break
                    j -= 1
                grupo = resultado[j:]
                resultado = resultado[:j] + '(' + grupo + '.' + grupo + '*)'
            else:
                j = len(resultado) - 1
                while j >= 0 and resultado[j] == '.': j -= 1
                if j < 0: raise ValueError("Operador '+' sin operando previo")
                prev = resultado[j]
                resultado = resultado[:j] + '(' + prev + '.' + prev + '*)'
            i += 1
        elif expr[i] == '?':
            if resultado and resultado[-1] == ')':
                count = 0
                j = len(resultado) - 1
                while j >= 0:
                    if resultado[j] == ')': count += 1
                    elif resultado[j] == '(':
                        count -= 1
                        if count == 0: break
                    j -= 1
                grupo = resultado[j:]
                resultado = resultado[:j] + '(' + grupo + '|ε)'
            else:
                j = len(resultado) - 1
                while j >= 0 and resultado[j] == '.': j -= 1
                if j < 0: raise ValueError("Operador '?' sin operando previo")
                prev = resultado[j]
                resultado = resultado[:j] + '(' + prev + '|ε)'
            i += 1
        else:
            resultado += expr[i]
            i += 1
    return resultado

def shunting_yard(regex):
    salida, pila = [], []
    precedencia = {'*': 3, '.': 2, '|': 1}
    operadores = set(precedencia.keys())
    i = 0
    while i < len(regex):
        c = regex[i]
        if c == ' ':
            i += 1; continue
        if c == '\\':
            if i + 1 < len(regex):
                salida.append('\\' + regex[i + 1])
                i += 2
            else:
                raise ValueError("Secuencia de escape incompleta")
        elif c.isalnum() or c == 'ε':
            salida.append(c); i += 1
        elif c == '(':
            pila.append(c); i += 1
        elif c == ')':
            while pila and pila[-1] != '(':
                salida.append(pila.pop())
            if not pila:
                raise ValueError("Falta paréntesis de apertura")
            pila.pop(); i += 1
        elif c in operadores:
            while (pila and pila[-1] in operadores and
                   precedencia[c] <= precedencia[pila[-1]]):
                salida.append(pila.pop())
            pila.append(c); i += 1
        else:
            raise ValueError(f"Carácter no reconocido: '{c}'")
    while pila:
        top = pila.pop()
        if top in {'(', ')'}:
            raise ValueError("Paréntesis desbalanceados.")
        salida.append(top)
    return salida

def _lit(symbol):
    s = State(); f = State()
    if symbol == 'ε':
        s.eps.add(f)
    else:
        s.edges.setdefault(symbol, set()).add(f)
    return Fragment(s, {f})

def _concat(a, b):
    for x in a.accepts:
        x.eps.add(b.start)
    return Fragment(a.start, b.accepts)

def _alt(a, b):
    s = State(); f = State()
    s.eps.update([a.start, b.start])
    for x in a.accepts: x.eps.add(f)
    for x in b.accepts: x.eps.add(f)
    return Fragment(s, {f})

def _star(a):
    s = State(); f = State()
    s.eps.update([a.start, f])
    for x in a.accepts:
        x.eps.update([a.start, f])
    return Fragment(s, {f})

def construir_afn_desde_arbol(nodo: Nodo) -> Fragment:
    if nodo is None:
        return _lit('ε')

    v = nodo.valor
    if nodo.izquierda is None and nodo.derecha is None:
        return _lit(v)

    if v == '.':
        A = construir_afn_desde_arbol(nodo.izquierda)
        B = construir_afn_desde_arbol(nodo.derecha)
        return _concat(A, B)
    elif v == '|':
        A = construir_afn_desde_arbol(nodo.izquierda)
        B = construir_afn_desde_arbol(nodo.derecha)
        return _alt(A, B)
    elif v == '*':
        A = construir_afn_desde_arbol(nodo.izquierda)
        return _star(A)
    else:
        if v == '+':
            A = construir_afn_desde_arbol(nodo.izquierda)
            return _concat(A, _star(A))
        if v == '?':
            A = construir_afn_desde_arbol(nodo.izquierda)
            return _alt(A, _lit('ε'))
        raise ValueError(f"Operador no soportado en árbol: {v}")

def _recolectar_estados(start):
    vistos = set()
    pila = [start]
    while pila:
        s = pila.pop()
        if s in vistos: continue
        vistos.add(s)
        for dests in s.edges.values():
            for d in dests:
                if d not in vistos: pila.append(d)
        for d in s.eps:
            if d not in vistos: pila.append(d)
    return vistos

def dibujar_afn(fragment: Fragment, filename, aceptar_ids=None):
    if aceptar_ids is None:
        aceptar_ids = {s.id for s in fragment.accepts}
    dot = Digraph()
    dot.attr(rankdir='LR')

    dot.node('start', shape='point')
    dot.edge('start', str(fragment.start.id), label='')

    estados = _recolectar_estados(fragment.start)

    for s in estados:
        shape = 'doublecircle' if s.id in aceptar_ids else 'circle'
        dot.node(str(s.id), shape=shape, label=f'q{s.id}')

    for s in estados:
        for sym, dests in s.edges.items():
            for d in dests:
                dot.edge(str(s.id), str(d.id), label=_mostrar_simbolo(sym))
        for d in s.eps:
            dot.edge(str(s.id), str(d.id), label='ε')

    dot.render(filename, format='png', cleanup=True)

def _mostrar_simbolo(sym):
    if sym.startswith('\\'):
        m = sym[1:]
        mapa = {'n': '\\n', 't': '\\t', 'r': '\\r', '\\': '\\\\'}
        return mapa.get(m, '\\' + m)
    return sym

def epsilon_cierre(states):
    stack = list(states)
    seen = set(states)
    while stack:
        s = stack.pop()
        for nxt in s.eps:
            if nxt not in seen:
                seen.add(nxt); stack.append(nxt)
    return seen

def mover(states, c):
    out = set()
    for s in states:
        for sym, dests in s.edges.items():
            if _simbolo_coincide(sym, c):
                out.update(dests)
    return out

def _simbolo_coincide(sym, c):
    if sym == c:
        return True
    if sym.startswith('\\'):
        m = sym[1:]
        mapa = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\'}
        return mapa.get(m, None) == c
    return False

def interpretar_cadena_literal(s):
    s = s.strip()
    if s == 'ε':
        return ''
    out = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            nxt = s[i+1]
            mapa = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\'}
            out.append(mapa.get(nxt, nxt))
            i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)

def acepta(fragment: Fragment, w: str) -> bool:
    current = epsilon_cierre({fragment.start})
    for ch in w:
        current = epsilon_cierre(mover(current, ch))
        if not current:
            return False
    return any(st in current for st in fragment.accepts)

def parsear_linea(linea: str):
    linea = linea.strip()
    if not linea:
        return None, None
    if ';' in linea:
        r, w = linea.split(';', 1)
        return r.strip(), w.strip()
    partes = linea.split(None, 1)
    if len(partes) == 1:
        return partes[0], 'ε'
    return partes[0], partes[1]

def procesar_archivo(nombre_archivo):
    with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
        lineas = archivo.readlines()

    for i, linea in enumerate(lineas):
        original = linea.strip()
        if not original:
            continue
        try:
            r, w_raw = parsear_linea(original)
            if r is None:
                continue
            w = interpretar_cadena_literal(w_raw)

            clase_expandida = expandir_clases(r)
            con_concat = insertar_concatenaciones(clase_expandida)
            expandida = expandir_operadores(con_concat)

            postfijo = shunting_yard(expandida)
            raiz = construir_arbol(postfijo)

            nombre_arbol = f'arbol_expr_{i+1}'
            dibujar_arbol(raiz, nombre_arbol)

            State._next_id = 0
            afn = construir_afn_desde_arbol(raiz)

            nombre_afn = f'afn_expr_{i+1}'
            dibujar_afn(afn, nombre_afn)

            ok = acepta(afn, w)

            print(f"Expresión [{i+1}]: {r}")
            print(f"Cadena w: {repr(w)}")
            print(f"Postfijo: {' '.join(postfijo)}")
            print(f"Árbol: {nombre_arbol}.png")
            print(f"AFN : {nombre_afn}.png")
            print("Resultado:", "sí" if ok else "no")
            print()
        except Exception as e:
            print(f"Error en línea #{i+1}: {e}")

procesar_archivo('problema1/example.txt')