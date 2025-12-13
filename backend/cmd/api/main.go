package main

import (
	"context"
	"database/sql"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/yourusername/football-prediction/internal/handlers"
	"github.com/yourusername/football-prediction/internal/service"
)

func main() {
	// Load environment variables from project root
	if err := godotenv.Load("../.env"); err != nil {
		log.Warn().Msg("No .env file found, using environment variables")
	}

	// Setup logger
	setupLogger()

	// Connect to database
	db, err := connectDB()
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to connect to database")
	}
	defer db.Close()

	// Get Football API key
	apiKey := os.Getenv("FOOTBALL_API_KEY")
	if apiKey == "" {
		log.Warn().Msg("FOOTBALL_API_KEY not set - API calls will fail")
	}

	// Setup Gin router
	router := setupRouter(db, apiKey)

	// Start server
	startServer(router)
}

func setupLogger() {
	logLevel := os.Getenv("LOG_LEVEL")
	if logLevel == "" {
		logLevel = "info"
	}

	level, err := zerolog.ParseLevel(logLevel)
	if err != nil {
		level = zerolog.InfoLevel
	}

	zerolog.SetGlobalLevel(level)
	log.Logger = zerolog.New(zerolog.ConsoleWriter{Out: os.Stdout, TimeFormat: time.RFC3339}).With().Timestamp().Logger()
}

func connectDB() (*sql.DB, error) {
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		return nil, fmt.Errorf("DATABASE_URL environment variable not set")
	}

	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	// Set connection pool settings
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	log.Info().Msg("Successfully connected to database")
	return db, nil
}

func setupRouter(db *sql.DB, apiKey string) *gin.Engine {
	// Set Gin mode
	if os.Getenv("API_ENV") == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.Default()

	// Middleware
	router.Use(corsMiddleware())
	router.Use(rateLimitMiddleware())

	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"timestamp": time.Now().Unix(),
		})
	})

	// Initialize services and handlers
	footballService := service.NewFootballService(apiKey, db)
	footballHandler := handlers.NewFootballHandler(footballService)

	// API v1 routes
	v1 := router.Group("/api/v1")
	{
		v1.GET("/competitions", footballHandler.GetCompetitions)
		v1.GET("/matches", footballHandler.GetMatches)
		v1.GET("/matches/:id", footballHandler.GetMatch)
		v1.GET("/standings/:competition", footballHandler.GetStandings)
		v1.GET("/predictions/:matchId", footballHandler.GetPrediction)
	}

	return router
}

func startServer(router *gin.Engine) {
	port := os.Getenv("API_PORT")
	if port == "" {
		port = "8080"
	}

	host := os.Getenv("API_HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	addr := fmt.Sprintf("%s:%s", host, port)

	srv := &http.Server{
		Addr:           addr,
		Handler:        router,
		ReadTimeout:    10 * time.Second,
		WriteTimeout:   10 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	// Start server in goroutine
	go func() {
		log.Info().Str("address", addr).Msg("Starting API server")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("Failed to start server")
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info().Msg("Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal().Err(err).Msg("Server forced to shutdown")
	}

	log.Info().Msg("Server exited")
}

// Middleware
func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	}
}

func rateLimitMiddleware() gin.HandlerFunc {
	// TODO: Implement proper rate limiting
	return func(c *gin.Context) {
		c.Next()
	}
}
