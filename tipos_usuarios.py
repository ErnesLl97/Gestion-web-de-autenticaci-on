from database.connection import db
from database.models import TipoUsuario

def crear_tipos_usuario():
    with db.connection_context():
        tipos = ['admin', 'empleado', 'cliente']
        for tipo in tipos:
            if not TipoUsuario.select().where(TipoUsuario.nombre == tipo).exists():
                TipoUsuario.create(nombre=tipo)
                print(f"✅ Tipo de usuario '{tipo}' creado")

if __name__ == "__main__":
    crear_tipos_usuario()