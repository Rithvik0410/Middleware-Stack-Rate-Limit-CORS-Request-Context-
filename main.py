from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
from collections import defaultdict, deque

EMAIL = "22f3001101@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-e4liei.example.com"

RATE_LIMIT = 13
WINDOW = 10  # seconds

app = FastAPI()

# Also allow the exam page
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
        "*",  # allows the exam page while we manually scope the ACAO header below
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# client_id -> timestamps
clients = defaultdict(deque)


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):
    # --------------------
    # Request ID
    # --------------------
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # --------------------
    # Rate limiting
    # --------------------
    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    q = clients[client]

    while q and now - q[0] > WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"X-Request-ID": request_id},
        )

    q.append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.options("/ping")
def options_ping(request: Request):
    origin = request.headers.get("Origin")

    response = Response(status_code=200)

    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"

    return response


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
