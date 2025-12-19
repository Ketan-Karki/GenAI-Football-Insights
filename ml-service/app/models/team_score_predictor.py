"""
Team-Agnostic Score Prediction Model
Predicts goals for ANY team vs ANY opponent - no home/away bias.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, Tuple, List

class TeamScorePredictor:
    """
    Predicts goals scored by a team given match context.
    Completely team-agnostic - treats all teams equally.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_path = 'models/team_score_predictor.h5'
        self.scaler_path = 'models/score_scaler.pkl'
    
    def build_model(self, n_features: int) -> keras.Model:
        """
        Build neural network for goal prediction.
        Single model predicts goals for ANY team.
        """
        model = keras.Sequential([
            # Input layer
            layers.Dense(
                256, 
                activation='relu', 
                input_shape=(n_features,),
                kernel_regularizer=regularizers.l2(0.001)
            ),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Hidden layers
            layers.Dense(128, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            
            layers.Dense(32, activation='relu'),
            
            # Output layer - predicts goals (0-6 range typically)
            layers.Dense(1, activation='relu')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae', 'mse']
        )
        
        return model
    
    def prepare_training_samples(self, matches_df: pd.DataFrame, 
                                 features_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create training samples where EACH team is treated equally.
        For each match, create TWO samples:
        - Team A attacking Team B
        - Team B attacking Team A
        
        No home/away distinction in the model.
        """
        samples = []
        labels = []
        
        for _, match in matches_df.iterrows():
            # Get features for both teams
            team_a_id = match['team_a_id']
            team_b_id = match['team_b_id']
            match_date = match['match_date']
            
            # Sample 1: Team A perspective
            features_a = self._extract_team_features(
                attacking_team=team_a_id,
                defending_team=team_b_id,
                match_date=match_date,
                is_at_venue=True,  # Team A is at their venue
                features_df=features_df
            )
            label_a = match['team_a_goals']
            
            samples.append(features_a)
            labels.append(label_a)
            
            # Sample 2: Team B perspective (symmetric)
            features_b = self._extract_team_features(
                attacking_team=team_b_id,
                defending_team=team_a_id,
                match_date=match_date,
                is_at_venue=False,  # Team B is away
                features_df=features_df
            )
            label_b = match['team_b_goals']
            
            samples.append(features_b)
            labels.append(label_b)
        
        X = np.array(samples)
        y = np.array(labels)
        
        return X, y
    
    def _extract_team_features(self, attacking_team: int, defending_team: int,
                               match_date: str, is_at_venue: bool,
                               features_df: pd.DataFrame) -> np.ndarray:
        """
        Extract features for a team attacking another team.
        Completely symmetric - no home/away bias.
        """
        # Get team stats from features_df
        att_stats = features_df[features_df['team_id'] == attacking_team].iloc[0]
        def_stats = features_df[features_df['team_id'] == defending_team].iloc[0]
        
        features = {
            # Attacking team's offensive capabilities
            'team_xg_per_game': att_stats.get('xg_per_game', 1.5),
            'team_goals_per_game': att_stats.get('goals_per_game', 1.5),
            'team_shots_per_game': att_stats.get('shots_per_game', 12),
            'team_striker_xg': att_stats.get('top_striker_xg', 0.5),
            'team_playmaker_assists': att_stats.get('playmaker_assists', 3),
            'team_formation_attack': att_stats.get('formation_attack_score', 5),
            'team_pressing_intensity': att_stats.get('pressing_intensity', 5),
            'team_possession_avg': att_stats.get('possession_avg', 50),
            
            # Defending team's defensive capabilities
            'opponent_xg_conceded': def_stats.get('xg_conceded_per_game', 1.5),
            'opponent_goals_conceded': def_stats.get('goals_conceded_per_game', 1.5),
            'opponent_defensive_rating': def_stats.get('defensive_rating', 5),
            'opponent_goalkeeper_save_pct': def_stats.get('goalkeeper_save_pct', 0.7),
            'opponent_tackles_per_game': def_stats.get('tackles_per_game', 15),
            'opponent_formation_defense': def_stats.get('formation_defense_score', 5),
            
            # Match context (venue is just a small feature, not a fundamental split)
            'venue_factor': 1.0 if is_at_venue else 0.85,  # Small boost for home venue
            'rest_days': att_stats.get('rest_days', 3),
            'travel_distance': 0 if is_at_venue else att_stats.get('travel_distance', 200),
            'injury_impact': att_stats.get('injury_impact', 0),
            
            # Team-specific head-to-head
            'h2h_goals_scored_avg': att_stats.get('h2h_goals_vs_opponent', 1.5),
            'h2h_goals_conceded_avg': att_stats.get('h2h_conceded_vs_opponent', 1.5),
            'h2h_win_rate': att_stats.get('h2h_win_rate_vs_opponent', 0.5),
            
            # Recent form and momentum
            'team_form_last_5': att_stats.get('form_last_5', 0.5),
            'team_form_last_10': att_stats.get('form_last_10', 0.5),
            'team_momentum': att_stats.get('momentum', 0),
            'opponent_form_last_5': def_stats.get('form_last_5', 0.5),
            
            # Coach and tactical matchup
            'coach_win_rate': att_stats.get('coach_win_rate', 0.5),
            'tactical_matchup_score': att_stats.get('tactical_matchup', 5),
        }
        
        return np.array(list(features.values()))
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 100, 
              batch_size: int = 32, validation_split: float = 0.2):
        """Train the model on prepared samples"""
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Build model
        self.model = self.build_model(X.shape[1])
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001
            )
        ]
        
        # Train
        history = self.model.fit(
            X_scaled, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def predict_match(self, team_a_features: Dict, team_b_features: Dict,
                     team_a_name: str, team_b_name: str) -> Dict:
        """
        Predict match outcome for Team A vs Team B.
        No home/away - just two teams.
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Extract features for both teams
        features_a = np.array(list(team_a_features.values())).reshape(1, -1)
        features_b = np.array(list(team_b_features.values())).reshape(1, -1)
        
        # Scale features
        features_a_scaled = self.scaler.transform(features_a)
        features_b_scaled = self.scaler.transform(features_b)
        
        # Predict goals for each team
        team_a_goals = self.model.predict(features_a_scaled, verbose=0)[0][0]
        team_b_goals = self.model.predict(features_b_scaled, verbose=0)[0][0]
        
        # Ensure non-negative
        team_a_goals = max(0, team_a_goals)
        team_b_goals = max(0, team_b_goals)
        
        # Determine outcome based on goal difference
        goal_diff = team_a_goals - team_b_goals
        
        # Calculate win probabilities to determine most likely outcome
        if goal_diff > 1.0:
            team_a_prob = min(0.85, 0.5 + (goal_diff * 0.15))
            team_b_prob = max(0.05, 0.5 - (goal_diff * 0.20))
            draw_prob = 1.0 - team_a_prob - team_b_prob
        elif goal_diff < -1.0:
            team_b_prob = min(0.85, 0.5 + (abs(goal_diff) * 0.15))
            team_a_prob = max(0.05, 0.5 - (abs(goal_diff) * 0.20))
            draw_prob = 1.0 - team_a_prob - team_b_prob
        else:
            team_a_prob = 0.5 + (goal_diff * 0.1)
            team_b_prob = 0.5 - (goal_diff * 0.1)
            draw_prob = max(0.2, 1.0 - team_a_prob - team_b_prob)
        
        # Choose winner based on highest probability
        # If probabilities are within 2% of each other, predict Draw
        max_prob = max(team_a_prob, team_b_prob, draw_prob)
        prob_diff_threshold = 0.02
        
        # Check if team_a and team_b are too close (within threshold)
        if abs(team_a_prob - team_b_prob) < prob_diff_threshold and max_prob in (team_a_prob, team_b_prob):
            outcome = "Draw"
            winner = "Draw"
            # When predicting draw due to equal probabilities, boost draw probability
            # Redistribute team_a/team_b probabilities to draw
            draw_prob = 1.0 - (team_a_prob + team_b_prob) * 0.15  # Keep some uncertainty
            team_a_prob = (team_a_prob + team_b_prob) * 0.425
            team_b_prob = (team_a_prob + team_b_prob) * 0.425
            confidence = min(0.95, 0.6 + draw_prob * 0.3)
        elif max_prob == team_a_prob:
            outcome = f"{team_a_name} Win"
            winner = team_a_name
            confidence = self._calculate_confidence(team_a_goals, team_b_goals)
        elif max_prob == team_b_prob:
            outcome = f"{team_b_name} Win"
            winner = team_b_name
            confidence = self._calculate_confidence(team_b_goals, team_a_goals)
        else:
            outcome = "Draw"
            winner = "Draw"
            confidence = 0.5 + (0.5 - abs(goal_diff))
        
        return {
            'predicted_outcome': outcome,
            'predicted_winner': winner,
            'team_a_name': team_a_name,
            'team_b_name': team_b_name,
            'team_a_predicted_goals': round(float(team_a_goals), 1),
            'team_b_predicted_goals': round(float(team_b_goals), 1),
            'confidence_score': round(float(confidence), 2),
            'goal_difference': round(float(goal_diff), 1),
        }
    
    def _calculate_confidence(self, winning_goals: float, losing_goals: float) -> float:
        """Calculate confidence based on predicted goal difference"""
        goal_diff = winning_goals - losing_goals
        # Larger goal difference = higher confidence
        # 1 goal = ~65%, 2 goals = ~80%, 3+ goals = ~90%
        confidence = 0.5 + min(0.45, goal_diff * 0.15)
        return confidence
    
    def save(self):
        """Save model and scaler"""
        os.makedirs('models', exist_ok=True)
        self.model.save(self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        print(f"✅ Model saved to {self.model_path}")
    
    def load(self):
        """Load trained model and scaler"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                # Load with compile=False to avoid Keras version compatibility issues
                self.model = tf.keras.models.load_model(self.model_path, compile=False)
                # Recompile with current Keras version
                self.model.compile(
                    optimizer=keras.optimizers.Adam(learning_rate=0.001),
                    loss='mse',
                    metrics=['mae']
                )
                self.scaler = joblib.load(self.scaler_path)
                print(f"✅ Model loaded from {self.model_path}")
                return True
            except Exception as e:
                print(f"⚠️  Error loading model: {e}")
                return False
        return False
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Evaluate model performance"""
        X_test_scaled = self.scaler.transform(X_test)
        predictions = self.model.predict(X_test_scaled, verbose=0).flatten()
        
        # Calculate metrics
        mae = np.mean(np.abs(predictions - y_test))
        mse = np.mean((predictions - y_test) ** 2)
        rmse = np.sqrt(mse)
        
        # Accuracy within 1 goal
        within_1_goal = np.mean(np.abs(predictions - y_test) <= 1.0)
        
        return {
            'mae': round(float(mae), 3),
            'rmse': round(float(rmse), 3),
            'accuracy_within_1_goal': round(float(within_1_goal), 3)
        }
