package repository

import (
	"database/sql"
	"fmt"

	"github.com/yourusername/football-prediction/pkg/football"
)

type CompetitionRepository struct {
	db *sql.DB
}

func NewCompetitionRepository(db *sql.DB) *CompetitionRepository {
	return &CompetitionRepository{db: db}
}

func (r *CompetitionRepository) Create(comp *football.Competition) error {
	query := `
		INSERT INTO competitions (external_id, name, code, area_name, current_season_start_date, current_season_end_date)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (external_id) DO UPDATE
		SET name = EXCLUDED.name,
		    code = EXCLUDED.code,
		    area_name = EXCLUDED.area_name,
		    current_season_start_date = EXCLUDED.current_season_start_date,
		    current_season_end_date = EXCLUDED.current_season_end_date,
		    updated_at = CURRENT_TIMESTAMP
		RETURNING id
	`

	var startDate, endDate *string
	if comp.CurrentSeason != nil {
		startDate = &comp.CurrentSeason.StartDate
		endDate = &comp.CurrentSeason.EndDate
	}

	var id int
	err := r.db.QueryRow(query, comp.ID, comp.Name, comp.Code, comp.Area.Name, startDate, endDate).Scan(&id)
	if err != nil {
		return fmt.Errorf("failed to create competition: %w", err)
	}

	return nil
}

func (r *CompetitionRepository) GetByCode(code string) (*football.Competition, error) {
	query := `
		SELECT id, external_id, name, code, area_name, current_season_start_date, current_season_end_date
		FROM competitions
		WHERE code = $1
	`

	var comp football.Competition
	var startDate, endDate sql.NullString

	err := r.db.QueryRow(query, code).Scan(
		&comp.ID,
		&comp.ID,
		&comp.Name,
		&comp.Code,
		&comp.Area.Name,
		&startDate,
		&endDate,
	)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get competition: %w", err)
	}

	if comp.CurrentSeason == nil {
		comp.CurrentSeason = &football.Season{}
	}
	if startDate.Valid {
		comp.CurrentSeason.StartDate = startDate.String
	}
	if endDate.Valid {
		comp.CurrentSeason.EndDate = endDate.String
	}

	return &comp, nil
}

func (r *CompetitionRepository) List() ([]*football.Competition, error) {
	query := `
		SELECT id, external_id, name, code, area_name, current_season_start_date, current_season_end_date
		FROM competitions
		ORDER BY name
	`

	rows, err := r.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to list competitions: %w", err)
	}
	defer rows.Close()

	var competitions []*football.Competition
	for rows.Next() {
		var comp football.Competition
		var startDate, endDate sql.NullString

		err := rows.Scan(
			&comp.ID,
			&comp.ID,
			&comp.Name,
			&comp.Code,
			&comp.Area.Name,
			&startDate,
			&endDate,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan competition: %w", err)
		}

		if comp.CurrentSeason == nil {
			comp.CurrentSeason = &football.Season{}
		}
		if startDate.Valid {
			comp.CurrentSeason.StartDate = startDate.String
		}
		if endDate.Valid {
			comp.CurrentSeason.EndDate = endDate.String
		}

		competitions = append(competitions, &comp)
	}

	return competitions, nil
}
