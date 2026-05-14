from app import create_app, db
from app.models import Role
app = create_app()
with app.app_context():
    print([r.name for r in Role.query.all()])
