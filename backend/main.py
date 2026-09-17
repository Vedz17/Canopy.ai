from fastapi import FastAPI

from schemas import (
    EnvironmentalProfile,
    RecommendationRequest,
    RecommendationResponse,
    RetrievalRequest,
    RetrievalResponse,
)
from retrieval_service import retrieve_chunks
from reasoning_service import generate_recommendation


app = FastAPI(
    title="Canopy AI",
    description="AI-powered environmental intelligence system",
    version="0.1.0",
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
