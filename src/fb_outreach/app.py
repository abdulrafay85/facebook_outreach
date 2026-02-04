from fastapi import FastAPI
from fb_outreach.routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FB Outreach Pipeline API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)