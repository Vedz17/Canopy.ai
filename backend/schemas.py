from pydantic import BaseModel
from typing import Optional


class Soil(BaseModel):
    ph: Optional[float] = None
    organic_carbon: Optional[float] = None
    moisture: Optional[str] = None


class Climate(BaseModel):
    temperature: Optional[float] = None
    rainfall: Optional[str] = None


class Land(BaseModel):
    land_use: Optional[str] = None
    crop: Optional[str] = None
    cropping_pattern: Optional[str] = None


class Biodiversity(BaseModel):
    species_richness: Optional[str] = None
    habitat_diversity: Optional[str] = None


class HumanImpact(BaseModel):
    pollution: Optional[str] = None
    deforestation: Optional[str] = None


class EnvironmentalProfile(BaseModel):
    soil: Soil
    climate: Climate
    land: Land
    biodiversity: Biodiversity
    human_impact: HumanImpact


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5


class RetrievedChunk(BaseModel):
    id: int
    document_id: int
    text: str
    similarity: float


class RetrievalResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]


class RecommendationRequest(BaseModel):
    profile: EnvironmentalProfile
    top_k: int = 5


class Recommendation(BaseModel):
    recommendation: str
    why: str
    affected_metrics: list[str]
    time_horizon: str
    confidence: str
    evidence: list[str]


class RecommendationResponse(BaseModel):
    profile: EnvironmentalProfile
    recommendation: Recommendation
    retrieved_evidence: list[RetrievedChunk]

class ProfileExtraction(BaseModel):
    """
    Partial environmental information extracted from one user message.

    Every field is optional because users are not expected to provide
    a complete environmental profile.
    """
    environmental_relevance: bool = False
    recommendation_requested: bool = False

    soil_ph: Optional[float] = None
    organic_carbon: Optional[float] = None
    soil_moisture: Optional[str] = None

    temperature: Optional[float] = None
    rainfall: Optional[str] = None

    land_use: Optional[str] = None
    crop: Optional[str] = None
    cropping_pattern: Optional[str] = None

    species_richness: Optional[str] = None
    habitat_diversity: Optional[str] = None

    pollution: Optional[str] = None
    deforestation: Optional[str] = None

    unknown_fields: list[str] = []
    context_notes: list[str] = []


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    needs_clarification: bool
    missing_fields: list[str]
    profile: EnvironmentalProfile
    recommendation: Optional[Recommendation] = None
    retrieved_evidence: list[RetrievedChunk] = []