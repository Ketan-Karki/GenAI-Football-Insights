#!/bin/bash
# Monthly retraining script for team-agnostic model
# Runs on 1st of every month at 2 AM

set -e

echo "============================================================"
echo "MONTHLY MODEL RETRAINING - $(date)"
echo "============================================================"

# Navigate to ml-service directory
cd /var/www/football-prediction/ml-service

# Activate virtual environment
source venv/bin/activate

# Set database URL
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/football_db?sslmode=disable"

# Update predictions with actual results
echo "Updating prediction history with actual results..."
python -c "
import psycopg2
import os

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Get all matches that finished in last 30 days
cur.execute('''
    SELECT DISTINCT ph.match_id
    FROM prediction_history ph
    JOIN matches m ON ph.match_id = m.id
    WHERE m.status = 'FINISHED'
      AND m.home_score IS NOT NULL
      AND ph.actual_team_a_goals IS NULL
      AND m.utc_date > CURRENT_DATE - INTERVAL '30 days'
''')

match_ids = [row[0] for row in cur.fetchall()]
print(f'Found {len(match_ids)} matches to update')

# Update each match
from app.handlers.prediction_history import UpdatePredictionWithActual
for match_id in match_ids:
    try:
        UpdatePredictionWithActual(conn, match_id)
        print(f'  ✓ Updated match {match_id}')
    except Exception as e:
        print(f'  ✗ Error updating match {match_id}: {e}')

conn.commit()
conn.close()
print('✅ Prediction history updated')
"

# Retrain model
echo ""
echo "Retraining model with latest data..."
python app/train_team_agnostic.py

# Restart ML service
echo ""
echo "Restarting ML service..."
sudo systemctl restart football-ml

# Check service status
sleep 3
sudo systemctl status football-ml --no-pager | head -n 10

echo ""
echo "============================================================"
echo "✅ MONTHLY RETRAINING COMPLETED - $(date)"
echo "============================================================"

# Log to file
echo "$(date): Monthly retraining completed successfully" >> /var/log/football-ml-retrain.log
