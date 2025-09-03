from fastapi import FastAPI

from .dependencies import startup_db
from .routers import users


# start fastapi instance
app = FastAPI(lifespan=startup_db)
app.include_router(router=users.router)




