from app.configuration.routes.routes import Routes
from app.internal.routes import auth, base, invoice, user

__routes__ = Routes(
    routers=(auth.router, base.router, invoice.router, user.router))
