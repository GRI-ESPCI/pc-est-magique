from app import create_app, db
from app.models import Role, Permission, PermissionType, PermissionScope
app = create_app()
with app.app_context():
    admin_role = db.session.scalar(db.select(Role).filter_by(name="Admin"))
    if not admin_role:
        print("Admin role not found.")
    else:
        # Create permission
        perm = Permission.get_or_create(PermissionType.all, PermissionScope.calendar)
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
            db.session.commit()
            print(f"Granted calendar permissions to '{admin_role.name}' role.")
        else:
            print(f"'{admin_role.name}' role already has calendar permissions.")
