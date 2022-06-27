def deploy():
    """Run deployment tasks."""
    from app import app, db
    from flask_migrate import upgrade, migrate, init, stamp
    from models import User

    app.app_context().push()
    db.create_all()

    # migrate database to latest revision
    init()
    stamp()
    migrate()
    upgrade()


deploy()
