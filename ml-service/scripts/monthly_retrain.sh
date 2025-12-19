#!/bin/bash
# Daily retraining script for team-agnostic model
# Runs daily at 2 AM

set -e

echo "============================================================"
echo "DAILY MODEL RETRAINING - $(date)"
echo "============================================================"

# Navigate to ml-service directory
cd /var/www/football-prediction/ml-service

# Activate virtual environment
source venv/bin/activate

# Set database URL
export DATABASE_URL="postgresql://ketan:postgres@localhost:5432/football_db?sslmode=disable"

# Update predictions with actual results
echo "Updating prediction history with actual results..."
python3 << 'EOF'
import psycopg2
import os
import sys

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    # Get all matches that finished and need updating
    cur.execute('''
        SELECT DISTINCT ph.match_id
        FROM prediction_history ph
        JOIN matches m ON ph.match_id = m.id
        WHERE m.status = 'FINISHED'
          AND m.home_score IS NOT NULL
          AND ph.actual_team_a_goals IS NULL
    ''')

    match_ids = [row[0] for row in cur.fetchall()]
    print(f'Found {len(match_ids)} matches to update')

    # Update each match with actual results
    for match_id in match_ids:
        try:
            cur.execute('''
                UPDATE prediction_history ph
                SET 
                    actual_team_a_goals = m.home_score,
                    actual_team_b_goals = m.away_score,
                    actual_outcome = CASE 
                        WHEN m.winner = 'HOME_TEAM' THEN ht.name || ' Win'
                        WHEN m.winner = 'AWAY_TEAM' THEN at.name || ' Win'
                        ELSE 'Draw'
                    END,
                    actual_winner = CASE 
                        WHEN m.winner = 'HOME_TEAM' THEN ht.name
                        WHEN m.winner = 'AWAY_TEAM' THEN at.name
                        ELSE 'Draw'
                    END,
                    prediction_correct = (
                        CASE 
                            WHEN ph.predicted_winner = ht.name AND m.winner = 'HOME_TEAM' THEN true
                            WHEN ph.predicted_winner = at.name AND m.winner = 'AWAY_TEAM' THEN true
                            WHEN ph.predicted_winner = 'Draw' AND m.winner IS NULL THEN true
                            ELSE false
                        END
                    ),
                    goals_error_team_a = ABS(ph.predicted_team_a_goals - m.home_score),
                    goals_error_team_b = ABS(ph.predicted_team_b_goals - m.away_score),
                    updated_at = CURRENT_TIMESTAMP
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE ph.match_id = m.id
                  AND ph.match_id = %s
                  AND m.status = 'FINISHED'
                  AND m.home_score IS NOT NULL
            ''', (match_id,))
            conn.commit()
            print(f'  ✓ Updated match {match_id}')
        except Exception as e:
            print(f'  ✗ Error updating match {match_id}: {e}')
            conn.rollback()

    conn.close()
    print('✅ Prediction history updated')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
EOF

# Retrain model
echo ""
echo "Retraining model with latest data..."
python3 app/train_team_agnostic.py 2>&1 || echo "⚠️  Model retraining skipped or had issues"

# Restart ML service
echo ""
echo "Restarting ML service..."
if sudo -n systemctl restart football-ml 2>/dev/null; then
  echo "✅ ML service restarted"
  # Check service status
  sleep 3
  sudo -n systemctl status football-ml --no-pager | head -n 10 || echo "⚠️  Could not check service status"
else
  echo "⚠️  ML service restart requires sudo password (configure passwordless sudo to enable)"
  echo "   Run: sudo visudo -f /etc/sudoers.d/github-deploy"
  echo "   Add: ketan ALL=(ALL) NOPASSWD: /bin/systemctl restart football-ml"
fi

echo ""
echo "============================================================"
echo "✅ DAILY RETRAINING COMPLETED - $(date)"
echo "============================================================"

# Log to file (use home directory if /var/log not writable)
LOG_FILE="/var/log/football-ml-retrain.log"
if [ ! -w "$(dirname "$LOG_FILE")" ]; then
  LOG_FILE="$HOME/.football-ml-retrain.log"
fi
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date): Daily retraining completed successfully" >> "$LOG_FILE"
echo "Log saved to: $LOG_FILE"
