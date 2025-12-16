# Team-Aware Prediction Model Architecture

## Overview

This document explains how our ML model predicts **which specific team will win**, not just generic home/away outcomes.

## The Problem We Solved

**Old Approach (Generic Position-Based)**:

- Model predicted: HOME_WIN, DRAW, AWAY_WIN
- Treated all "home teams" the same, all "away teams" the same
- Result: Manchester City at home got similar probability to any home team
- PSG away got low probability just because they're "away team"

**New Approach (Team-Specific)**:

- Model still outputs HOME_WIN/DRAW/AWAY_WIN during training
- BUT includes team identity features (team IDs + quality ratings)
- Model learns: "Team ID 65 (Man City) with quality 85 wins 80% of time"
- Result: PSG away gets high probability because model knows PSG is elite

## How It Works

### 1. Team Identity Features

We added three critical features to make the model team-aware:

```python
features = {
    'home_team_id': 65,           # Manchester City's unique ID
    'away_team_id': 73,           # Burnley's unique ID
    'team_id_diff': -8,           # Interaction feature
    'home_quality_rating': 85.5,  # City's season performance (0-100)
    'away_quality_rating': 42.3,  # Burnley's season performance
    'quality_difference': 43.2,   # Massive gap = City heavily favored
    # ... 25+ more features
}
```

### 2. Training Process

```python
# For each historical match:
X = extract_features(home_team_id, away_team_id, date)
y = actual_outcome  # 0=AWAY_WIN, 1=DRAW, 2=HOME_WIN

# Model learns patterns like:
# "When team_id=65 (City) AND quality_difference > 40 → HOME_WIN 85%"
# "When team_id=567 (PSG) AND quality_rating > 85 → AWAY_WIN 70% even away"

model.fit(X, y)
```

### 3. Prediction Process

```python
# For Manchester City vs Burnley:
features = {
    'home_team_id': 65,
    'away_team_id': 73,
    'home_quality_rating': 85.5,
    'away_quality_rating': 42.3,
    'quality_difference': 43.2,
    # ... other features
}

probabilities = model.predict_proba(features)
# Returns: [0.07, 0.15, 0.78]  # Away 7%, Draw 15%, Home 78%

# We then map to actual team:
if predicted_class == 2:  # HOME_WIN
    winner = "Manchester City"  # Not just "Home Team"
```

## Key Features That Make It Team-Aware

### 1. Team Quality Rating (0-100)

```python
def get_team_quality_rating(team_id):
    # Based on entire season performance
    win_rate = (wins / total_matches) * 100
    goal_performance = 50 + (avg_goals_scored - avg_goals_conceded) * 10
    quality = (win_rate * 0.6) + (goal_performance * 0.4)
    return quality

# Examples:
# Manchester City: 85-90
# PSG: 88
# Real Madrid: 87
# Weak teams: 30-40
```

### 2. Team Identity (IDs)

- Each team has unique external_id from API
- Model learns specific team patterns over time
- Example: Model learns "team_id=65 (City) scores 2.8 goals/game"

### 3. Interaction Features

- `team_id_diff`: Captures team pairing dynamics
- `quality_difference`: Strength gap between teams
- `strength_ratio`: Relative power comparison

## Why This Works Better

**Scenario: PSG (away) vs Sporting (home)**

**Old Model Thinking**:

- "This is home team vs away team"
- "Home teams win 45% of time historically"
- "Predict: HOME_WIN (Sporting)"
- Result: PSG gets 8% ❌

**New Model Thinking**:

- "team_id=567 (PSG) has quality_rating=88"
- "team_id=498 (Sporting) has quality_rating=65"
- "quality_difference = -23 (away team stronger!)"
- "Historical pattern: When quality_diff < -20, away team wins 70%"
- "Predict: AWAY_WIN (PSG)"
- Result: PSG gets 70% ✅

## Response Format

The ML service now returns:

```json
{
  "home_win_probability": 0.3,
  "draw_probability": 0.2,
  "away_win_probability": 0.5,
  "predicted_outcome": "Paris Saint-Germain FC Win", // Team-specific outcome!
  "predicted_winner": "Paris Saint-Germain FC", // Just the team name
  "confidence_score": 0.78,
  "insights": [
    "Paris Saint-Germain FC in better recent form",
    "Paris Saint-Germain FC has stronger attacking threat (2.9 goals/game)",
    "Paris Saint-Germain FC heavily favored to win"
  ]
}
```

## Benefits for Football Fans

1. **Realistic Predictions**: Elite teams get high probabilities even when away
2. **Team-Specific Insights**: "PSG has advantage" not "Away team has advantage"
3. **Data-Driven Analysis**: Based on actual team performance, not position
4. **Confidence Scores**: Shows when model is certain vs uncertain
5. **Educational**: Fans learn which factors matter (quality, form, H2H)

## Technical Implementation

### Feature Engineering (`feature_engineering.py`)

```python
def extract_match_features(home_team_id, away_team_id, date):
    # Calculate team-specific features
    home_quality = get_team_quality_rating(home_team_id, date)
    away_quality = get_team_quality_rating(away_team_id, date)

    features = {
        'home_team_id': home_team_id,
        'away_team_id': away_team_id,
        'home_quality_rating': home_quality,
        'away_quality_rating': away_quality,
        'quality_difference': home_quality - away_quality,
        # ... 25+ more features
    }
    return features
```

### Prediction (`predictor_enhanced.py`)

```python
def predict(home_team_id, away_team_id, home_team_name, away_team_name):
    # Extract features
    X = extract_match_features(home_team_id, away_team_id, date)

    # Get probabilities
    probs = model.predict_proba(X)[0]
    predicted_class = model.predict(X)[0]

    # Generate team-specific outcome
    if predicted_class == 2:  # HOME_WIN
        outcome = f"{home_team_name} Win"
        winner = home_team_name
    elif predicted_class == 0:  # AWAY_WIN
        outcome = f"{away_team_name} Win"
        winner = away_team_name
    else:
        outcome = "Draw"
        winner = "Draw"

    return {
        'predicted_outcome': outcome,  # "Manchester City Win" not "HOME_WIN"
        'predicted_winner': winner,    # "Manchester City" not "Home Team"
        'home_win_probability': probs[2],
        'away_win_probability': probs[0],
        'draw_probability': probs[1]
    }
```

## Model Training

The model is trained on 6000+ historical matches with team IDs:

```python
# Training data includes:
# Match 1: team_65 (City) vs team_73 (Burnley) → HOME_WIN
# Match 2: team_567 (PSG) vs team_498 (Sporting) → AWAY_WIN
# Match 3: team_86 (Madrid) vs team_81 (Barca) → HOME_WIN
# ... 6000+ matches

# Model learns:
# - Team 65 (City) wins 75% at home
# - Team 567 (PSG) wins 65% even away
# - When quality_diff > 40, stronger team wins 85%
```

## For Football Fans

This is **NOT a betting tool**. It's for football fans who want:

- Data-driven match insights
- Understanding of team strengths
- Educational analysis of what factors matter
- Realistic predictions based on performance data

The model shows its confidence score so fans know when predictions are uncertain (evenly matched teams) vs certain (huge quality gap).

---

**Model Version**: v2.0-enhanced-team-aware  
**Accuracy**: ~42% (good for 3-outcome prediction)  
**Training Data**: 6000+ matches across 6 leagues  
**Features**: 31 features including team IDs and quality ratings
