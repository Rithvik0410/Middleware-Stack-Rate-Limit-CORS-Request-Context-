from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, deque
import uuid
import time

EMAIL = "22f3001101@ds.study.iitm.ac.in"

RATE_LIMIT = 13
WINDOW = 10  # seconds

app = FastAPI()

# Allow HTTPS origins (covers the assigned origin and the browser-based exam page)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# client_id -> timestamps
clients = defaultdict(deque)


@app.middleware("http")
async def middleware(request: Request, call_next):
    # ---------------- Request ID ----------------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # ---------------- Rate Limiting ----------------
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    q = clients[client_id]

    while q and now - q[0] >= WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"X-Request-ID": request_id},
        )

    q.append(now)

    response = await call_next(request)

    # Echo request ID
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    request_id = request.state.request_id

    return JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request_id,
        },
        headers={
            "X-Request-ID": request_id,
        },
    )
