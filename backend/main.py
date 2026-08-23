"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import verify_connectivity, close_driver
from routers import movies, actors, recommendations, graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    ok, msg = verify_connectivity()
    if ok:
        print(f"[OK] {msg}")
    else:
        print(f"[WARN] {msg} -- app will start anyway, endpoints will return 503 until DB is available.")
    yield
    close_driver()
    print("[OK] CognoDB driver closed.")


app = FastAPI(
    title="CineGraph API",
    description="Graph-powered movie recommendation engine backed by CognoDB",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router)
app.include_router(actors.router)
app.include_router(recommendations.router)
app.include_router(graph.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "CineGraph API is running 🎬", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    ok, msg = verify_connectivity()
    return {"status": "ok" if ok else "degraded", "database": msg}
