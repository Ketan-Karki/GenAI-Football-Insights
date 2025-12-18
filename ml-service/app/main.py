from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from dotenv import load_dotenv

from app.predictor_v2 import predictor
print("✅ Using team-agnostic neural network predictor")

# Load environment variables
load_dotenv("../.env")

app = FastAPI(
    title="Football Match Prediction ML Service",
    description="Machine Learning service for predicting football match outcomes",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class PredictionRequest(BaseModel):
    home_team_id: int
    away_team_id: int
    matchday: int = 1
    home_team_name: Optional[str] = None
    away_team_name: Optional[str] = None
    home_team_position: Optional[int] = None
    away_team_position: Optional[int] = None

class TeamStats(BaseModel):
    home_form: float
    away_form: float
    home_goals_avg: float
    away_goals_avg: float
    home_win_rate: float
    away_win_rate: float

class PredictionResponse(BaseModel):
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    predicted_outcome: str
    confidence_score: float
    model_version: str
    model_accuracy: Optional[float] = None
    team_stats: Optional[dict] = None
    insights: Optional[List[str]] = None
    key_features: Optional[dict] = None

@app.get("/")
async def root():
    return {
        "service": "Football Match Prediction ML Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": predictor.model is not None
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_match(request: PredictionRequest):
    """
    Predict match outcome using real team statistics from database
    """
    try:
        # Use the predictor with real team stats and team names for insights
        result = predictor.predict(
            home_team_id=request.home_team_id,
            away_team_id=request.away_team_id,
            matchday=request.matchday,
            home_team_name=request.home_team_name,
            away_team_name=request.away_team_name
        )
        
        return result
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def train_model():
    """
    Trigger model training (admin endpoint)
    """
    # TODO: Implement model training
    return {
        "status": "training_started",
        "message": "Model training initiated - to be implemented"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
