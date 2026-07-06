from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.routers import papers, books, projects, awards, adoptions, attachments, export, honors, trainings
import os


FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="科研成果管理系统", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(papers.router, prefix="/api/papers", tags=["论文"])
app.include_router(books.router, prefix="/api/books", tags=["专著"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目"])
app.include_router(awards.router, prefix="/api/awards", tags=["奖励"])
app.include_router(adoptions.router, prefix="/api/adoptions", tags=["采纳证明"])
app.include_router(honors.router, prefix="/api/honors", tags=["荣誉称号"])
app.include_router(trainings.router, prefix="/api/trainings", tags=["培训证明"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["附件"])
app.include_router(export.router, prefix="/api/export", tags=["导出"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        if full_path.startswith("api"):
            from fastapi.responses import RedirectResponse
            url = request.url
            return RedirectResponse(url=str(url) + "/", status_code=307)
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
