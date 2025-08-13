from graphviz import Digraph

class Nodo:
    def __init__(self, valor, izquierda=None, derecha=None):
        self.valor = valor
        self.izquierda = izquierda
        self.derecha = derecha
        self.id = id(self)

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
        if nodo is None:
            return
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
                    if resultado[j] == ')':
                        count += 1
                    elif resultado[j] == '(':
                        count -= 1
                        if count == 0:
                            break
                    j -= 1
                grupo = resultado[j:]
                resultado = resultado[:j] + '(' + grupo + '.' + grupo + '*)'
            else:
                j = len(resultado) - 1
                while j >= 0 and resultado[j] == '.':
                    j -= 1
                prev = resultado[j]
                resultado = resultado[:j] + '(' + prev + '.' + prev + '*)'
            i += 1
        elif expr[i] == '?':
            if resultado and resultado[-1] == ')':
                count = 0
                j = len(resultado) - 1
                while j >= 0:
                    if resultado[j] == ')':
                        count += 1
                    elif resultado[j] == '(':
                        count -= 1
                        if count == 0:
                            break
                    j -= 1
                grupo = resultado[j:]
                resultado = resultado[:j] + '(' + grupo + '|ε)'
            else:
                j = len(resultado) - 1
                while j >= 0 and resultado[j] == '.':
                    j -= 1
                prev = resultado[j]
                resultado = resultado[:j] + '(' + prev + '|ε)'
            i += 1
        else:
            resultado += expr[i]
            i += 1
    return resultado

def shunting_yard(regex):
    salida = []
    pila = []

    precedencia = {
        '*': 3,
        '.': 2,
        '|': 1
    }

    operadores = set(precedencia.keys())
    i = 0
    while i < len(regex):
        c = regex[i]
        if c == ' ':
            i += 1
            continue
        if c == '\\':
            if i + 1 < len(regex):
                salida.append('\\' + regex[i + 1])
                i += 2
            else:
                raise ValueError("Secuencia de escape incompleta")
        elif c.isalnum() or c == 'ε':
            salida.append(c)
            i += 1
        elif c == '(':
            pila.append(c)
            i += 1
        elif c == ')':
            while pila and pila[-1] != '(':
                salida.append(pila.pop())
            if not pila:
                raise ValueError("Falta paréntesis de apertura")
            pila.pop()
            i += 1
        elif c in operadores:
            while (pila and pila[-1] in operadores and
                   precedencia[c] <= precedencia[pila[-1]]):
                salida.append(pila.pop())
            pila.append(c)
            i += 1
        else:
            raise ValueError(f"Carácter no reconocido: '{c}'")
    while pila:
        top = pila.pop()
        if top in {'(', ')'}:
            raise ValueError("Paréntesis desbalanceados.")
        salida.append(top)
    return salida

def procesar_archivo(nombre_archivo):
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()
    for i, linea in enumerate(lineas):
        original = linea.strip()
        if not original:
            continue
        try:
            clase_expandida = expandir_clases(original)
            con_concat = insertar_concatenaciones(clase_expandida)
            expandida = expandir_operadores(con_concat)
            postfijo = shunting_yard(expandida)
            raiz = construir_arbol(postfijo)
            nombre_archivo_salida = f'arbol_expr_{i+1}'
            dibujar_arbol(raiz, nombre_archivo_salida)
            print(f"Expresión [{i+1}]: {original}")
            print(f"Postfijo: {' '.join(postfijo)}")
            print(f"Árbol generado: {nombre_archivo_salida}.png\n")
        except Exception as e:
            print(f"Error en expresión #{i+1}: {e}")

procesar_archivo('problema1/example.txt')