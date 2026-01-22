from fastapi import FastAPI
from fb_outreach.routes import router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="FB Outreach Pipeline API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(router)
