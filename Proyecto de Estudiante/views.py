from abc import ABC, abstractmethod

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido


# =====================================================================
# CLASE BASE (ABSTRACTA)
# =====================================================================
# Los del CRUD llevan el nombre de su entidad (crear_estudiante, crear_materia...)
#
# [CAMBIO - PRÁCTICA CRUDBASE]
# Antes CrudBase solo EXIGÍA métodos (guardar, validar, siguiente eran abstractos).
# Ahora también PRESTA el código que era igual en los 3 controladores:
#   - __init__, guardar(), siguiente() y contar() -> métodos NORMALES (se heredan).
#   - validar() -> sigue ABSTRACTO porque cada entidad valida distinto.
# Regla: código IGUAL en todos = método normal aquí;
#        código DISTINTO pero obligatorio = @abstractmethod.
class CrudBase(ABC):

    # [CAMBIO] __init__ común: antes estaba repetido en los 3 controladores.
    # Cada hijo dice qué ARCHIVO y qué MODELO usa (atributos de clase).
    # POLIMORFISMO: la misma línea crea un Estudiante, una Materia o una
    # Matricula según el controlador que la ejecute (self.MODELO).
    def __init__(self, archivo=None):
        self.gestor = GestorJSON(archivo or self.ARCHIVO)

        # Leemos el JSON y convertimos cada diccionario en un objeto del MODELO
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(self.MODELO.desde_diccionario(datos))

    # [CAMBIO] guardar() pasó de abstracto a normal: era igual en los 3.
    def guardar(self):
        datos = []
        for objeto in self.lista:
            datos.append(objeto.a_diccionario())
        self.gestor.guardar(datos)

    # Sigue ABSTRACTO: cada controlador tiene sus propias reglas de validación.
    @abstractmethod
    def validar(self, datos, id_actual=None):
        pass



    # [CAMBIO] siguiente() pasó de abstracto a normal: era igual en los 3.
    # Se usa 'obj' (nombre genérico) porque sirve para cualquier modelo.
    def siguiente(self):
        mayor = 0
        for obj in self.lista:
            if obj.id > mayor:
                mayor = obj.id
        return mayor + 1

    # [CAMBIO] contar() NUEVO. Primero se probó como @abstractmethod
    # (sin implementarlo sale TypeError al crear el controlador); luego se
    # dejó como método normal porque es igual en los 3. Se usa en el Resumen.
    # 'self' es el controlador real que lo llama, que ya creó su self.lista.
    def contar(self):
        return len(self.lista)

# =====================================================================
# CONTROLADOR DE ESTUDIANTES
# =====================================================================
class EstudianteController(CrudBase):

    # TUPLA: los campos buscables son fijos y no cambian, por eso tupla y no lista
    # [CAMBIO - SEMESTRE] Agregado a la tupla para poder buscar por semestre.
    CAMPOS_BUSCABLES = ("nombre", "apellido", "email", "carnet", "carrera", "semestre")
    # [CAMBIO] Atributos de clase: le dicen a CrudBase qué modelo crear y qué archivo leer.
    MODELO = Estudiante
    ARCHIVO = "data/estudiantes.json"
    # [CAMBIO] __init__() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def __init__(self, archivo="data/estudiantes.json"):
    #     self.gestor = GestorJSON(archivo)

    #     # Leemos el JSON y convertimos cada diccionario en un objeto Estudiante
    #     self.lista = []
    #     for datos in self.gestor.leer():
    #         self.lista.append(Estudiante.desde_diccionario(datos))

    # [CAMBIO] guardar() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def guardar(self):
    #     datos = []
    #     for estudiante in self.lista:
    #         datos.append(estudiante.a_diccionario())
    #     self.gestor.guardar(datos)

    def carnets_registrados(self, excepto_id=None):
        """CONJUNTO de carnets ya usados: preguntar 'x in conjunto' es instantáneo."""
        return {e.carnet.upper() for e in self.lista if e.id != excepto_id}

    def ids_registrados(self):
        """CONJUNTO de ids: para saber rápido si un estudiante existe."""
        return {e.id for e in self.lista}

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        # Al crear, los cuatro son obligatorios; al actualizar, solo lo que cambia
        if id_actual is None:
            for campo in ("nombre", "apellido", "email", "carnet"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            # CONJUNTO con los emails de los OTROS estudiantes
            usados = {e.email for e in self.lista if e.id != id_actual}
            if email in usados:
                return "Ese email ya está registrado"

        if "carnet" in datos:
            carnet = str(datos["carnet"]).strip().upper()
            if carnet in self.carnets_registrados(id_actual):
                return f"El carnet {carnet} ya está registrado"
        
        # [CAMBIO - SEMESTRE] Paso 4 de 5 (validar). Semestre es OPCIONAL:
        # el menú SIEMPRE manda la clave (aunque vacía), por eso no basta con "if 'semestre' in datos".
        # Se valida solo si escribieron algo: solo dígitos y rango 1 a 8.
        # IMPORTANTE: este bloque va ANTES del return None (lo que va después de un return nunca se ejecuta).
        semestre = str(datos.get("semestre", "")).strip()
        if semestre !="":
            if not semestre.isdigit() or not 1 <= int(semestre) <= 8:
                return "Los semestres deben ser un número entre 1 y 8"

        return None
    
    def obtener_estudiantes(self):
        return self.lista

    def obtener_estudiante(self, id_estudiante):
        for estudiante in self.lista:
            if estudiante.id == id_estudiante:
                return estudiante
        return None

    def buscar_estudiantes(self, termino):
        termino = termino.strip().lower()
        encontrados = []
        if termino == "":
            return encontrados

        for estudiante in self.lista:
            for campo in self.CAMPOS_BUSCABLES:
                if termino in str(getattr(estudiante, campo)).lower():
                    encontrados.append(estudiante)
                    break       # ya coincidió, no revisa más campos
        return encontrados

    # [CAMBIO] siguiente() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def siguiente(self):
    #     mayor = 0
    #     for estudiante in self.lista:
    #         if estudiante.id > mayor:
    #             mayor = estudiante.id
    #     return mayor + 1

    def crear_estudiante(self, datos):
        error = self.validar(datos)
        if error:
            # TUPLA (exito, mensaje): dos valores fijos que siempre van juntos
            return False, error

        # [CAMBIO - SEMESTRE] Se lee como TEXTO limpio (str + strip). Más abajo se convierte a int.
        # Se usa .get() para que no dé KeyError si no viene la clave.
        semestre = str(datos.get("semestre", "")).strip()
        estudiante = Estudiante(self.siguiente(),
                                str(datos["nombre"]).strip().title(),
                                str(datos["apellido"]).strip().title(),
                                str(datos["email"]).strip().lower(),
                                str(datos["carnet"]).strip().upper(),
                                str(datos.get("carrera", "")).strip().title(),
                                # [CAMBIO - SEMESTRE] Si viene vacío queda en 1; si no, se convierte a número.
                                # Se compara con "" (texto vacío), NO con 0 ni con 1, porque semestre aquí es texto.
                                int(semestre) if semestre != "" else 1)
        self.lista.append(estudiante)
        self.guardar()
        return True, f"Estudiante creado: {estudiante.etiqueta()}"

    def actualizar_estudiante(self, id_estudiante, cambios):
        estudiante = self.obtener_estudiante(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        if not cambios:
            return False, "No se indicó ningún cambio"

        # DIFERENCIA de conjuntos: campos que no existen en un estudiante
        # [CAMBIO - SEMESTRE] Permitido al actualizar (si no, daría "Campos no válidos").
        permitidos = {"nombre", "apellido", "email", "carnet", "carrera", "semestre"}
        desconocidos = set(cambios) - permitidos
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        # Se valida ANTES de tocar el objeto: si algo falla, no cambia nada
        error = self.validar(cambios, id_estudiante)
        if error:
            return False, error

        for campo, valor in cambios.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "carrera"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            elif campo == "carnet":
                valor = valor.upper()
            # [CAMBIO - SEMESTRE] Al actualizar también se convierte a int; si no, quedaría "5" (texto) en el JSON.
            elif campo == "semestre":
                valor = int(valor)
            setattr(estudiante, campo, valor)

        self.guardar()
        return True, f"Estudiante {id_estudiante} actualizado"

    def eliminar_estudiante(self, id_estudiante):
        estudiante = self.obtener_estudiante(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"

        self.lista.remove(estudiante)
        self.guardar()
        return True, f"Estudiante {id_estudiante} eliminado"

    # [CAMBIO] contar() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def contar(self):
    #     return len(self.lista)

# =====================================================================
# CONTROLADOR DE MATERIAS
# =====================================================================
class MateriaController(CrudBase):
    # [CAMBIO] Atributos de clase: le dicen a CrudBase qué modelo crear y qué archivo leer.
    MODELO = Materia
    ARCHIVO = "data/materias.json"

    # [CAMBIO] __init__() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def __init__(self, archivo="data/materias.json"):
    #     self.gestor = GestorJSON(archivo)

    #     self.lista = []
    #     for datos in self.gestor.leer():
    #         self.lista.append(Materia.desde_diccionario(datos))

    # [CAMBIO] guardar() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def guardar(self):
    #     datos = []
    #     for materia in self.lista:
    #         datos.append(materia.a_diccionario())
    #     self.gestor.guardar(datos)

    def codigos_registrados(self, excepto_id=None):
        """CONJUNTO de códigos ya usados: preguntar 'x in conjunto' es instantáneo."""
        return {m.codigo.upper() for m in self.lista if m.id != excepto_id}

    def ids_registrados(self):
        """CONJUNTO de ids: para saber rápido si una materia existe."""
        return {m.id for m in self.lista}

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        if id_actual is None:
            for campo in ("nombre", "codigo", "creditos"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "codigo" in datos:
            codigo = str(datos["codigo"]).strip().upper()
            if codigo in self.codigos_registrados(id_actual):
                return f"El código {codigo} ya está registrado"

        if "creditos" in datos:
            creditos = str(datos["creditos"]).strip()
            if not creditos.isdigit() or not 1 <= int(creditos) <= 10:
                return "Los créditos deben ser un número entre 1 y 10"

        cupos = str(datos.get("cupos", "")).strip()
        if cupos != "":
            if not cupos.isdigit() or int(cupos) > Materia.CUPOS_MAXIMOS:
                return f"Los cupos deben estar entre 0 y {Materia.CUPOS_MAXIMOS}"
        return None

    def obtener_materias(self):
        return self.lista

    def obtener_materia(self, id_materia):
        for materia in self.lista:
            if materia.id == id_materia:
                return materia
        return None

    def buscar_materias(self, termino):
        termino = termino.strip().lower()
        encontrados = []
        if termino == "":
            return encontrados

        for materia in self.lista:
            if (termino in materia.nombre.lower()
                    or termino in materia.codigo.lower()):
                encontrados.append(materia)
        return encontrados

    # [CAMBIO] siguiente() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def siguiente(self):
    #     mayor = 0
    #     for materia in self.lista:
    #         if materia.id > mayor:
    #             mayor = materia.id
    #     return mayor + 1

    def crear_materia(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        # Si no escribieron los cupos, empieza en 0
        cupos = str(datos.get("cupos", "")).strip()
        materia = Materia(self.siguiente(),
                          str(datos["nombre"]).strip().title(),
                          str(datos["codigo"]).strip().upper(),
                          int(datos["creditos"]),
                          int(cupos) if cupos != "" else 0)
        self.lista.append(materia)
        self.guardar()
        return True, f"Materia creada: {materia.etiqueta()}"

    def actualizar_materia(self, id_materia, cambios):
        materia = self.obtener_materia(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        if not cambios:
            return False, "No se indicó ningún cambio"

        # DIFERENCIA de conjuntos: campos que no existen en una materia
        desconocidos = set(cambios) - {"nombre", "codigo", "creditos", "cupos"}
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        error = self.validar(cambios, id_materia)
        if error:
            return False, error

        if "nombre" in cambios:
            materia.nombre = str(cambios["nombre"]).strip().title()
        if "codigo" in cambios:
            materia.codigo = str(cambios["codigo"]).strip().upper()
        if "creditos" in cambios:
            materia.creditos = int(cambios["creditos"])
        if "cupos" in cambios:
            materia.cupos = int(cambios["cupos"])

        self.guardar()
        return True, f"Materia {id_materia} actualizada"

    def eliminar_materia(self, id_materia):
        materia = self.obtener_materia(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"

        self.lista.remove(materia)
        self.guardar()
        return True, f"Materia {id_materia} eliminada"

    # --- propio de materias ---
    def materias_sin_cupo(self):
        sin_cupo = []
        for materia in self.lista:
            if materia.cupos == 0:
                sin_cupo.append(materia)
        return sin_cupo

    # [CAMBIO] contar() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def contar(self):
    #     return len(self.lista)

# =====================================================================
# CONTROLADOR DE MATRÍCULAS
# =====================================================================
class MatriculaController(CrudBase):

    # [CAMBIO] Atributos de clase: le dicen a CrudBase qué modelo crear y qué archivo leer.
    MODELO = Matricula
    ARCHIVO = "data/matriculas.json"

    # [CAMBIO] Este controlador SÍ conserva su __init__ porque tiene algo propio
    # (la referencia a los controladores de estudiantes y materias).
    # Con super().__init__() reutiliza la carga del JSON que hace CrudBase.
    def __init__(self, estudiantes, materias):
        super().__init__(archivo=None)
        self.estudiantes= estudiantes
        self.materias=materias
        # La matrícula USA a los otros dos controladores.
        # Hay que pasarle los MISMOS que usa main.py.
        


    # [CAMBIO] guardar() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def guardar(self):
    #     datos = []
    #     for matricula in self.lista:
    #         datos.append(matricula.a_diccionario())
    #     self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        try:
            estudiante_id = int(datos.get("estudiante_id", 0))
            materia_id = int(datos.get("materia_id", 0))
        except (TypeError, ValueError):
            return "estudiante_id y materia_id deben ser números enteros"

        periodo = str(datos.get("periodo", "")).strip()
        if periodo == "":
            return "El campo periodo es obligatorio"

        # CONJUNTO de ids: 'x in conjunto' dice al instante si existe
        if estudiante_id not in self.estudiantes.ids_registrados():
            return f"No existe un estudiante con id {estudiante_id}"
        if materia_id not in self.materias.ids_registrados():
            return f"No existe una materia con id {materia_id}"

        materia = self.materias.obtener_materia(materia_id)
        if not materia.hay_cupo():
            return f"La materia {materia.nombre} no tiene cupos"

        # Se comparan los TRES juntos: mismo estudiante, misma materia y mismo periodo
        for otra in self.lista:
            if (otra.estudiante_id == estudiante_id
                    and otra.materia_id == materia_id
                    and otra.periodo == periodo):
                return "El estudiante ya está matriculado en esa materia y periodo"

        nota = str(datos.get("nota", "")).strip()
        if nota != "" and not Materia.es_nota_valida(nota):
            return "La nota debe ser un número entre 0 y 20"
        return None

    def obtener_matriculas(self):
        return self.lista

    def obtener_matricula(self, id_matricula):
        for matricula in self.lista:
            if matricula.id == id_matricula:
                return matricula
        return None

    # [CAMBIO] siguiente() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def siguiente(self):
    #     mayor = 0
    #     for matricula in self.lista:
    #         if matricula.id > mayor:
    #             mayor = matricula.id
    #     return mayor + 1

    def crear_matricula(self, datos):
        # datos = {"estudiante_id": 1, "materia_id": 2, "periodo": "2026-1"}
        error = self.validar(datos)
        if error:
            return False, error

        nota = str(datos.get("nota", "")).strip()
        materia = self.materias.obtener_materia(int(datos["materia_id"]))
        matricula = Matricula(self.siguiente(),
                              int(datos["estudiante_id"]),
                              materia.id,
                              str(datos["periodo"]).strip(),
                              float(nota) if nota != "" else 0)

        materia.ocupar_cupo()
        self.materias.guardar()          # guarda el cupo nuevo en materias.json
        self.lista.append(matricula)
        self.guardar()                   # guarda la matrícula en matriculas.json
        return True, f"Matrícula {matricula.id} registrada"

    def registrar_nota(self, id_matricula, nota):
        matricula = self.obtener_matricula(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        if not Materia.es_nota_valida(nota):
            return False, "La nota debe ser un número entre 0 y 20"

        matricula.nota = float(nota)
        self.guardar()
        return True, f"Nota registrada: {matricula.nota} · {matricula.estado()}"

    def retirar_matricula(self, id_matricula):
        """Retirar: se borra la matrícula y el cupo vuelve a la materia."""
        matricula = self.obtener_matricula(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"

        materia = self.materias.obtener_materia(matricula.materia_id)
        if materia is not None:
            materia.liberar_cupo()
            self.materias.guardar()

        self.lista.remove(matricula)
        self.guardar()
        return True, f"Matrícula {id_matricula} retirada y cupo liberado"

    # --- propio de matrículas ---
    def certificado(self, id_matricula):
        matricula = self.obtener_matricula(id_matricula)
        if matricula is None:
            return None

        # DICCIONARIO ÍNDICE {id: objeto}: encuentra a cada uno por id al instante
        estudiantes_por_id = {e.id: e for e in self.estudiantes.lista}
        materias_por_id = {m.id: m for m in self.materias.lista}

        estudiante = estudiantes_por_id.get(matricula.estudiante_id)
        materia = materias_por_id.get(matricula.materia_id)

        texto = f"CERTIFICADO #{matricula.id}   periodo: {matricula.periodo}\n"
        if estudiante:
            texto += f"Estudiante: {estudiante.nombre_completo()}   ({estudiante.carnet})\n"
        else:
            texto += "Estudiante: eliminado\n"
        if materia:
            texto += (f"Materia   : {materia.nombre}   ({materia.codigo})"
                      f" · {materia.creditos} créditos\n")
        else:
            texto += "Materia   : eliminada\n"
        texto += "-" * 42 + "\n"
        texto += f"Nota      : {matricula.nota}\n"
        texto += f"Estado    : {matricula.estado()}"
        return texto

    def matriculas_por_estudiante(self):
        """DICCIONARIO de LISTAS {estudiante_id: [matrículas]}: agrupa por estudiante."""
        agrupadas = {}
        for matricula in self.lista:
            # setdefault crea la lista vacía la primera vez que aparece el estudiante
            agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
        return agrupadas

    def promedio_de_estudiante(self, id_estudiante):
        notas = []
        for matricula in self.lista:
            if matricula.estudiante_id == id_estudiante:
                notas.append(matricula.nota)
        if not notas:
            return 0
        return round(sum(notas) / len(notas), 2)

    # [CAMBIO] contar() ahora se hereda de CrudBase. Lo dejo comentado como referencia de la práctica.
    # def contar(self):
    #     return len(self.lista)