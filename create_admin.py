from werkzeug.security import generate_password_hash
from database.connection import db
from database.models import Usuario, TipoUsuario

def inicializar_sistema():
    with db.connection_context():
        try:
            tipos = ['admin', 'empleado', 'cliente']
            for tipo in tipos:
                TipoUsuario.get_or_create(nombre=tipo)
                print(f"Tipo de usuario '{tipo}' verificado/creado")
            
            tipo_admin = TipoUsuario.get(TipoUsuario.nombre == 'admin')
            
            admin, created = Usuario.get_or_create(
                usuario='admin',
                defaults={
                    'tipousuario_id': tipo_admin.id,
                    'password_hash': generate_password_hash('admin123')
                }
            )
            
            if created:
                print("✅ Usuario admin creado exitosamente")
            else:
                admin.set_password('admin123')
                admin.save()
                print("ℹ️ Usuario admin existente - contraseña actualizada")
            
            print(f"Usuario: {admin.usuario}")
            print(f"Password hash: {admin.password_hash}")
            print(f"Verificación password 'admin123': {admin.check_password('admin123')}")

        except Exception as e:
            print(f"❌ Error crítico: {str(e)}")
            raise

if __name__ == "__main__":
    print("Inicializando sistema...")
    inicializar_sistema()
    print("Proceso completado.")