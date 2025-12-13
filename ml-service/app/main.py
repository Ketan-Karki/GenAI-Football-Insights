from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from dotenv import load_dotenv

# Try to use enhanced predictor, fallback to basic if not available
try:
    from app.predictor_enhanced import predictor
    print("✅ Using enhanced ML predictor with player statistics")
except ImportError:
    from app.predictor import predictor
    print("⚠️  Using basic predictor (enhanced version not available)")

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
class MatchFeatures(BaseModel):
    home_team_id: int
    away_team_id: int
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
async def predict_match(features: MatchFeatures):
    """
    Predict match outcome using real team statistics from database
    """
    try:
        # Use the predictor with real team stats
        result = predictor.predict(
            home_team_id=features.home_team_id,
            away_team_id=features.away_team_id,
            matchday=features.home_team_position or 16
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
