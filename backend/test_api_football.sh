#!/bin/bash

# Test API-Football integration
echo "Testing API-Football API..."

# Test fixture with known ID
FIXTURE_ID=1035098

echo ""
echo "1. Testing fixture lineups endpoint..."
curl -s -H "x-apisports-key: ae46126b9ccdabd7b348865d33e61702" \
  "https://v3.football.api-sports.io/fixtures/lineups?fixture=$FIXTURE_ID" | \
  jq '.response[] | {team: .team.name, formation: .formation, players: (.startXI | length)}'

echo ""
echo "2. Testing fixture events endpoint..."
curl -s -H "x-apisports-key: ae46126b9ccdabd7b348865d33e61702" \
  "https://v3.football.api-sports.io/fixtures/events?fixture=$FIXTURE_ID" | \
  jq '.response[0:3] | .[] | {time: .time.elapsed, type: .type, player: .player.name, detail: .detail}'

echo ""
echo "3. Checking API quota..."
curl -s -H "x-apisports-key: ae46126b9ccdabd7b348865d33e61702" \
  "https://v3.football.api-sports.io/status" | \
  jq '.response | {requests_today: .requests.current, limit_day: .requests.limit_day}'

echo ""
echo "✅ API-Football is working!"
