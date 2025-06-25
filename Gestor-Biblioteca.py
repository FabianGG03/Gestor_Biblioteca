import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class Libro:
    def __init__(self, id: int, titulo: str, autor: str, stock: int):
        self.id = id
        self.titulo = titulo
        self.autor = autor
        self.stock = stock

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "autor": self.autor,
            "stock": self.stock
        }


class Prestamo:
    def __init__(self, libro_id: int, usuario: str, dias_prestamo: int = 14):
        self.libro_id = libro_id
        self.usuario = usuario
        self.fecha_prestamo = datetime.now().date()
        self.fecha_devolucion = self.fecha_prestamo + timedelta(days=dias_prestamo)
        self.devuelto = False

    def calcular_multa(self) -> float:
        if self.devuelto:
            return 0.0
            
        hoy = datetime.now().date()
        if hoy <= self.fecha_devolucion:
            return 0.0
            
        dias_retraso = (hoy - self.fecha_devolucion).days
        return max(0, dias_retraso) * 0.50


class Notificador:
    @staticmethod
    async def enviar_notificacion(usuario: str, mensaje: str):
        await asyncio.sleep(2)
        print(f"\n📧 Notificación enviada a {usuario}: {mensaje}")


class Biblioteca:
    def __init__(self):
        self.libros: List[Libro] = []
        self.prestamos: List[Prestamo] = []
        self.cargar_datos()

    def cargar_datos(self):
        try:
            with open('biblioteca.json', 'r') as f:
                data = json.load(f)
                
                self.libros = [
                    Libro(l['id'], l['titulo'], l['autor'], l['stock']) 
                    for l in data.get('libros', [])
                ]
            
                self.prestamos = []
                for p in data.get('prestamos', []):
                    prestamo = Prestamo(
                        p['libro_id'], 
                        p['usuario'],
                    )
                    prestamo.fecha_prestamo = datetime.strptime(p['fecha_prestamo'], '%Y-%m-%d').date()
                    prestamo.fecha_devolucion = datetime.strptime(p['fecha_devolucion'], '%Y-%m-%d').date()
                    prestamo.devuelto = p['devuelto']
                    self.prestamos.append(prestamo)
                    
        except FileNotFoundError:
            print("⚠️ No se encontraron datos previos. Iniciando con datos vacíos.")
        except json.JSONDecodeError:
            print("⚠️ Error al leer el archivo de datos. Iniciando con datos vacíos.")

    def guardar_datos(self):
        data = {
            "libros": [libro.to_dict() for libro in self.libros],
            "prestamos": [
                {
                    "libro_id": p.libro_id,
                    "usuario": p.usuario,
                    "fecha_prestamo": p.fecha_prestamo.strftime('%Y-%m-%d'),
                    "fecha_devolucion": p.fecha_devolucion.strftime('%Y-%m-%d'),
                    "devuelto": p.devuelto
                } 
                for p in self.prestamos
            ]
        }
        with open('biblioteca.json', 'w') as f:
            json.dump(data, f, indent=2)

    def agregar_libro(self, libro: Libro):
        if any(l.id == libro.id for l in self.libros):
            print(f"❌ Ya existe un libro con ID {libro.id}")
            return False
            
        self.libros.append(libro)
        self.guardar_datos()
        print(f"✅ Libro '{libro.titulo}' agregado")
        return True

    def buscar_libro(self, criterio: str, valor: str) -> List[Libro]:
        criterio = criterio.lower()
        if criterio not in ["id", "titulo", "autor", "stock"]:
            print(f"❌ Criterio inválido: {criterio}")
            return []
            
        try:
            if criterio in ["id", "stock"]:
                valor = int(valor)
                
            return [l for l in self.libros if getattr(l, criterio) == valor]
        except ValueError:
            print(f"❌ Valor inválido para {criterio}: {valor}")
            return []

    def prestar_libro(self, libro_id: int, usuario: str):
        prestamo_activo = any(
            p for p in self.prestamos 
            if p.libro_id == libro_id 
            and p.usuario == usuario 
            and not p.devuelto
        )
        if prestamo_activo:
            print(f"❌ {usuario} ya tiene prestado este libro")
            return False
            
        libro = next((l for l in self.libros if l.id == libro_id), None)
        if not libro:
            print(f"❌ Libro con ID {libro_id} no encontrado")
            return False
            
        if libro.stock <= 0:
            print(f"❌ No hay existencias de '{libro.titulo}'")
            return False
            
        libro.stock -= 1
        prestamo = Prestamo(libro_id, usuario)
        self.prestamos.append(prestamo)
        self.guardar_datos()

        print(f"✅ Libro '{libro.titulo}' prestado a {usuario}. Devuelve antes del {prestamo.fecha_devolucion}")
        
     
        mensaje = f"¡No olvides devolver '{libro.titulo}' antes del {prestamo.fecha_devolucion}!"
        asyncio.create_task(Notificador.enviar_notificacion(usuario, mensaje))
        return True

    def devolver_libro(self, libro_id: int, usuario: str):
        prestamo = next(
            (p for p in self.prestamos 
             if p.libro_id == libro_id 
             and p.usuario == usuario 
             and not p.devuelto),
            None
        )
        if not prestamo:
            print(f"❌ Préstamo no encontrado para {usuario}")
            return False
            
        libro = next((l for l in self.libros if l.id == libro_id), None)
        if not libro:
            print(f"❌ Libro con ID {libro_id} no encontrado")
            return False
            
        prestamo.devuelto = True
        libro.stock += 1
        self.guardar_datos()
        
        multa = prestamo.calcular_multa()
        if multa > 0:
            print(f"⚠️ Devolución tardía. Multa a pagar: ${multa:.2f}")
        else:
            print(f"✅ Libro '{libro.titulo}' devuelto correctamente")
        return True

    def listar_libros(self):
        if not self.libros:
            print("📚 No hay libros en el catálogo")
            return
            
        print("\n📚 Catálogo de Libros:")
        for libro in self.libros:
            print(f"ID: {libro.id} | Título: {libro.titulo} | Autor: {libro.autor} | Stock: {libro.stock}")

    def listar_prestamos_activos(self):
        activos = [p for p in self.prestamos if not p.devuelto]
        if not activos:
            print("📝 No hay préstamos activos")
            return
            
        print("\n📝 Préstamos Activos:")
        for prestamo in activos:
            libro = next((l for l in self.libros if l.id == prestamo.libro_id), None)
            libro_titulo = libro.titulo if libro else "Libro Desconocido"
            estado = "✅ En plazo" if datetime.now().date() <= prestamo.fecha_devolucion else f"⚠️ Atrasado (Multa: ${prestamo.calcular_multa():.2f})"
            print(f"Usuario: {prestamo.usuario} | Libro: {libro_titulo} | Devuelve: {prestamo.fecha_devolucion} | {estado}")


def mostrar_menu():
    print("\n📚 ** SISTEMA DE BIBLIOTECA **")
    print("1. Agregar libro")
    print("2. Listar todos los libros")
    print("3. Buscar libro")
    print("4. Prestar libro")
    print("5. Devolver libro")
    print("6. Listar préstamos activos")
    print("7. Salir")
    return input("Seleccione una opción: ")

async def main():
    biblioteca = Biblioteca()
    
    while True:
        opcion = mostrar_menu()
        
        if opcion == "1":
            try:
                id = int(input("ID del libro: "))
                titulo = input("Título: ")
                autor = input("Autor: ")
                stock = int(input("Stock inicial: "))
                libro = Libro(id, titulo, autor, stock)
                biblioteca.agregar_libro(libro)
            except ValueError:
                print("❌ Error: ID y Stock deben ser números enteros")
                
        elif opcion == "2":
            biblioteca.listar_libros()
                
        elif opcion == "3":
            print("\n🔍 Buscar por:")
            print("1. ID")
            print("2. Título")
            print("3. Autor")
            print("4. Stock")
            subopcion = input("Seleccione criterio: ")
            
            criterios = {"1": "id", "2": "titulo", "3": "autor", "4": "stock"}
            if subopcion in criterios:
                valor = input(f"Ingrese {criterios[subopcion]}: ")
                libros = biblioteca.buscar_libro(criterios[subopcion], valor)
                if libros:
                    print("\n🔍 Resultados de la búsqueda:")
                    for libro in libros:
                        print(f"ID: {libro.id}, Título: {libro.titulo}, Autor: {libro.autor}, Stock: {libro.stock}")
                else:
                    print("❌ No se encontraron libros")
            else:
                print("❌ Opción inválida")
                
        elif opcion == "4":
            try:
                libro_id = int(input("ID del libro a prestar: "))
                usuario = input("Nombre de usuario: ")
                biblioteca.prestar_libro(libro_id, usuario)
            except ValueError:
                print("❌ Error: ID debe ser un número entero")
                
        elif opcion == "5":
            try:
                libro_id = int(input("ID del libro a devolver: "))
                usuario = input("Nombre de usuario: ")
                biblioteca.devolver_libro(libro_id, usuario)
            except ValueError:
                print("❌ Error: ID debe ser un número entero")
                
        elif opcion == "6":
            biblioteca.listar_prestamos_activos()
                
        elif opcion == "7":
            print("¡Hasta pronto! 👋")
            break
            
        else:
            print("❌ Opción inválida")
        
        
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())