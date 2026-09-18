from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    EnvironmentalProfile,
    RecommendationRequest,
    RecommendationResponse,
    RetrievalRequest,
    RetrievalResponse,
    ChatRequest,
    ChatResponse,
)
from retrieval_service import retrieve_chunks
from reasoning_service import generate_recommendation
from conversation_service import get_or_create_session
from conversation_manager import (
    build_environmental_profile,
    process_message,
)

app = FastAPI(
    title="Canopy AI",
    description="AI-powered environmental intelligence system",
    version="0.1.0",
)

# Enable CORS for the React/Vite dev server and production clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://canopyai-theta.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Canopy AI backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/profile")
def create_profile(profile: EnvironmentalProfile):
    return {
        "message": "Environmental profile received",
        "profile": profile,
    }


@app.post(
    "/retrieve",
    response_model=RetrievalResponse,
)
def retrieve_knowledge(request: RetrievalRequest):
    results = retrieve_chunks(
        query=request.query,
        top_k=request.top_k,
    )

    return {
        "query": request.query,
        "results": results,
    }


@app.post(
    "/recommend",
    response_model=RecommendationResponse,
)
def recommend(request: RecommendationRequest):
    recommendation, retrieved_evidence = generate_recommendation(
        profile=request.profile,
        top_k=request.top_k,
    )

    return {
        "profile": request.profile,
        "recommendation": recommendation,
        "retrieved_evidence": retrieved_evidence,
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):
    state = get_or_create_session(
        request.session_id
    )

    result = process_message(
        state=state,
        message=request.message,
    )

    profile = build_environmental_profile(
        state
    )

    recommendation = None
    retrieved_evidence = []

    # Only execute RAG + Gemini when the conversation manager explicitly allows reasoning
    if result.get("can_reason", False):
        recommendation, retrieved_evidence = generate_recommendation(
            profile=profile,
            top_k=5,
        )

    return {
        "session_id": request.session_id,
        "response": result["response"],
        "needs_clarification": result["needs_clarification"],
        "missing_fields": result["missing_fields"],
        "profile": profile,
        "recommendation": recommendation,
        "retrieved_evidence": retrieved_evidence,
    }   