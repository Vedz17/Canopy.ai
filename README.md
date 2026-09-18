# 🌿 Canopy AI

> **AI-powered environmental intelligence for healthier land and ecosystems.**

Canopy AI is an AI-powered environmental decision-support system that combines **scientific knowledge, structured environmental data, Retrieval-Augmented Generation (RAG), and multi-metric reasoning** to turn environmental observations into evidence-backed recommendations.

Instead of looking at soil, climate, land use, and biodiversity independently, Canopy AI reasons about how these environmental factors interact.

---

## ✨ What Canopy AI Does

Canopy AI provides a conversational interface for understanding environmental conditions and exploring potential interventions.

It works across:

- 🌱 **Soil** — pH, organic carbon, moisture
- 🌦️ **Climate** — temperature, rainfall
- 🌾 **Land & Cropping** — land use, crop, cropping pattern
- 🐝 **Biodiversity** — species richness, habitat diversity
- 🏭 **Human Impact** — pollution, deforestation

The system can identify missing information, ask targeted clarification questions, maintain conversation context, retrieve relevant scientific evidence, and generate recommendations grounded in that evidence.

---

## 🧠 Core Idea

Canopy AI connects three layers of environmental intelligence:

```text
┌─────────────────────────────────────┐
│     Structured Environmental Data   │
│                                     │
│       "What is happening?"          │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│       Scientific Knowledge + RAG    │
│                                     │
│       "What does science say?"      │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│       Multi-Metric Reasoning        │
│                                     │
│       "What should we consider?"    │
└─────────────────────────────────────┘
```

---

## 🏗️ Architecture

```text
                         ┌──────────────────┐
                         │    React / Vite  │
                         │      Frontend    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      FastAPI     │
                         │      Backend     │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │   Conversation   │
                         │     Manager      │
                         │                  │
                         │ • Chat History   │
                         │ • Context        │
                         │ • Memory         │
                         │ • Missing Fields │
                         │ • Clarification  │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐       ┌──────────────────┐
          │ Environmental    │       │   RAG Retrieval  │
          │ Profile          │       │                  │
          │                  │       │ PostgreSQL       │
          │ Soil             │       │ + pgvector       │
          │ Climate          │       │                  │
          │ Land             │       │ Scientific       │
          │ Biodiversity     │       │ Knowledge Base   │
          │ Human Impact     │       │                  │
          └────────┬─────────┘       └────────┬─────────┘
                   │                          │
                   └────────────┬─────────────┘
                                ▼
                     ┌─────────────────────┐
                     │ Multi-Metric        │
                     │ Environmental       │
                     │ Reasoning           │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   Cohere Command    │
                     │   Generation Model  │
                     └──────────┬──────────┘
                                │
                                ▼
                     Evidence-backed
                       Recommendation
                                │
                                ▼
                         React / Vite UI
```

---

## 🔬 Scientific Knowledge System

A core component of Canopy AI is its retrievable scientific knowledge layer.

Instead of relying only on the language model's internal knowledge, scientific reports and research documents are processed into searchable vector embeddings.

```text
Scientific PDF / Report
          ↓
    Text Extraction
          ↓
       Cleaning
          ↓
       Chunking
          ↓
   Cohere Embeddings
          ↓
 PostgreSQL + pgvector
          ↓
 Semantic Retrieval
```

The current knowledge base contains:

- **2,481 embedded chunks**
- **6 scientific documents**
- IPCC climate and ecosystem material
- FAO biodiversity resources
- FAO soil carbon resources
- Peer-reviewed research on crop diversification
- Agroforestry and soil-health research

Semantic retrieval uses **Cohere `embed-v4.0`** with vector similarity search.

---

## 💬 Conversational Intelligence

Canopy AI is designed for multi-turn environmental conversations rather than one-shot prompts.

For example:

```text
User:
"My soil seems poor and I grow wheat."

Canopy:
"Do you know the soil organic carbon level?"

User:
"About 0.3%."

Canopy:
"Do you know the rainfall conditions?"

User:
"Rainfall is low."

Canopy:
[Uses the accumulated environmental context
to generate a grounded assessment]
```

The conversation manager maintains:

- Conversation history
- Known environmental facts
- Unknown or declined fields
- Contextual notes
- Environmental profile state

The system avoids silently inventing missing environmental measurements.

---

## 🌍 Multi-Metric Environmental Reasoning

Environmental systems are interconnected.

A change in one part of an ecosystem can influence several others.

For example:

```text
Cropping Pattern
       ↓
Soil Structure / Carbon
       ↓
Water Dynamics
       ↓
Habitat Conditions
       ↓
Biodiversity
```

Canopy AI therefore considers relationships such as:

- Soil ↔ Water
- Land Use ↔ Habitat
- Crop Diversity ↔ Biodiversity
- Management Practices ↔ Soil Carbon
- Environmental Pressure ↔ Ecosystem Resilience

This multi-metric reasoning layer is a key part of the system's environmental intelligence.

---

## 📊 Evidence-Backed Recommendations

When enough environmental context is available, Canopy AI generates recommendations containing:

- **Recommendation** — what could be considered
- **Scientific reasoning** — why the intervention may help
- **Affected metrics** — which environmental dimensions may be influenced
- **Time horizon** — short, medium, or long term
- **Scientific evidence** — retrieved supporting research

The system is designed to distinguish between:

```text
User-provided measurements
        ≠
Dataset estimates
        ≠
Model-generated reasoning
```

This helps prevent unsupported environmental claims from being presented as measured facts.

---

## 🧪 Example Environmental Profile

```json
{
  "soil": {
    "ph": 6.2,
    "organic_carbon": 0.3,
    "moisture": "low"
  },
  "climate": {
    "rainfall": "low",
    "temperature": 31
  },
  "land": {
    "land_use": "agriculture",
    "crop": "wheat",
    "cropping_pattern": "monoculture"
  },
  "biodiversity": {
    "species_richness": "low",
    "habitat_diversity": "low"
  },
  "human_impact": {
    "pollution": "moderate",
    "deforestation": "low"
  }
}
```

The profile can be progressively built through conversation instead of requiring every field upfront.

---

## 🛠️ Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Lucide Icons

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy

### AI

- Cohere `command-a-03-2025`
- Cohere `embed-v4.0`

### Knowledge & Storage

- PostgreSQL
- pgvector
- Scientific reports
- Environmental datasets

### Deployment

- Vercel — Frontend
- Render — Backend
- Render PostgreSQL — Production database

---

## 🔌 API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Backend health check |
| `POST /profile` | Accept an environmental profile |
| `POST /retrieve` | Perform semantic knowledge retrieval |
| `POST /recommend` | Generate an evidence-backed recommendation |
| `POST /chat` | Run the conversational environmental workflow |

---

## 🚀 Running Locally

### Clone the repository

```bash
git clone https://github.com/Vedz17/Canopy.ai.git
cd Canopy.ai
```

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=your_database_url
COHERE_API_KEY=your_cohere_api_key

COHERE_EMBEDDING_MODEL=embed-v4.0
COHERE_EMBEDDING_DIMENSIONS=1024
COHERE_GENERATION_MODEL=command-a-03-2025

ENVIRONMENT=development
```

Start the backend:

```bash
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 📚 Scientific Foundation

The knowledge system incorporates scientific material including:

- **IPCC AR6 WGII** — climate impacts, ecosystems, biodiversity, water, agriculture, adaptation and resilience
- **FAO State of the World's Biodiversity for Food and Agriculture**
- **FAO Global Soil Organic Carbon resources**
- Peer-reviewed meta-analyses covering crop diversification, biodiversity, agroforestry and soil health

The retrieval layer provides relevant evidence to the reasoning process so that recommendations can be connected to documented scientific knowledge.

---

## 🎯 Key Design Principles

### 1. Grounded, not purely generative

Scientific recommendations are supported through retrieval from a dedicated knowledge base.

### 2. Context-aware

Environmental information can be collected progressively through conversation.

### 3. Multi-metric

The system considers interactions between environmental dimensions rather than optimizing one metric in isolation.

### 4. Transparent

Retrieved evidence is surfaced alongside recommendations.

### 5. Conservative with missing data

Unknown environmental measurements are not silently fabricated.

---

## 🎯 Why Canopy AI?

Environmental decisions rarely affect only one variable.

Improving soil can influence water dynamics.

Changing cropping systems can influence biodiversity.

Land-use decisions can alter habitat conditions.

Climate pressures can interact with soil and ecosystem resilience.

**Canopy AI is built to reason across these connections — turning environmental data and scientific knowledge into a single, contextual intelligence layer.**

---

## 👥 Intended Users

Canopy AI is designed as a decision-support system for:

- Environmental scientists
- Researchers
- Sustainable agriculture practitioners
- Land managers
- Ecological assessment workflows

It is intended to support environmental reasoning and exploration, not replace field measurements or expert judgment.

---

## 🔮 Future Scope

Potential extensions include:

- Geospatial environmental context
- Soil and climate dataset integrations
- Satellite-derived land-cover information
- Biodiversity occurrence data
- Spatial environmental risk mapping
- More domain-specific scientific knowledge
- Persistent assessment history
- Advanced environmental scenario modelling

---

## 🌱 Vision

> **From environmental data to ecological understanding.**

Canopy AI aims to make scientific environmental knowledge more accessible, contextual, and actionable — helping people understand not only **what is happening**, but also **why it matters and what evidence suggests next.**

---

## 📄 Project

**Canopy AI**  
AI-powered Environmental Intelligence System

Built for an AI & Environmental Science challenge.
