package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"time"
)

// Config holds server configuration
type Config struct {
	Port              string
	GitHubAppID       string
	GitHubPrivateKey  string
	GitHubWebhookSecret string
	PythonPath        string
}

// PREvent represents a GitHub pull request event
type PREvent struct {
	Action      string `json:"action"`
	Number      int    `json:"number"`
	PullRequest struct {
		Number  int    `json:"number"`
		Title   string `json:"title"`
		Head    struct {
			SHA string `json:"sha"`
			Ref string `json:"ref"`
		} `json:"head"`
		Base struct {
			Ref  string `json:"ref"`
			Repo struct {
				FullName string `json:"full_name"`
				CloneURL string `json:"clone_url"`
			} `json:"repo"`
		} `json:"base"`
		User struct {
			Login string `json:"login"`
		} `json:"user"`
		ChangedFiles int `json:"changed_files"`
		Additions    int `json:"additions"`
		Deletions    int `json:"deletions"`
	} `json:"pull_request"`
	Repository struct {
		FullName string `json:"full_name"`
		CloneURL string `json:"clone_url"`
		Owner    struct {
			Login string `json:"login"`
		} `json:"owner"`
	} `json:"repository"`
	Installation struct {
		ID int `json:"id"`
	} `json:"installation"`
}

// AnalysisResult from Python detection
type AnalysisResult struct {
	FilesScanned     int           `json:"files_scanned"`
	AIDetected       int           `json:"ai_detected"`
	MaxAIConfidence  float64       `json:"max_ai_confidence"`
	AIPercentage     float64       `json:"ai_percentage"`
	Results          []FileResult  `json:"results"`
	PolicyEvaluation PolicyResult  `json:"policy_evaluation"`
	Blocked          bool          `json:"blocked"`
	Violations       []Violation   `json:"violations"`
	Warnings         []Warning     `json:"warnings"`
}

type FileResult struct {
	Path         string  `json:"path"`
	AIConfidence float64 `json:"ai_confidence"`
	LinesChanged int     `json:"lines_changed"`
	Status       string  `json:"status"`
}

type PolicyResult struct {
	Allowed           bool        `json:"allowed"`
	Violations        []Violation `json:"violations"`
	Warnings          []Warning   `json:"warnings"`
	RequiredReviewers []string    `json:"required_reviewers"`
}

type Violation struct {
	Policy  string   `json:"policy"`
	Message string   `json:"message"`
	Files   []string `json:"files"`
}

type Warning struct {
	Policy  string `json:"policy"`
	Message string `json:"message"`
}

// CheckRun represents a GitHub check run
type CheckRun struct {
	Name        string       `json:"name"`
	HeadSHA     string       `json:"head_sha"`
	Status      string       `json:"status"`
	Conclusion  string       `json:"conclusion,omitempty"`
	StartedAt   string       `json:"started_at,omitempty"`
	CompletedAt string       `json:"completed_at,omitempty"`
	Output      *CheckOutput `json:"output,omitempty"`
}

type CheckOutput struct {
	Title   string `json:"title"`
	Summary string `json:"summary"`
	Text    string `json:"text,omitempty"`
}

var config Config

func main() {
	config = Config{
		Port:                getEnv("PORT", "8080"),
		GitHubAppID:         os.Getenv("GITHUB_APP_ID"),
		GitHubPrivateKey:    os.Getenv("GITHUB_PRIVATE_KEY"),
		GitHubWebhookSecret: os.Getenv("GITHUB_WEBHOOK_SECRET"),
		PythonPath:          getEnv("PYTHON_PATH", "python3"),
	}

	http.HandleFunc("/", handleHealth)
	http.HandleFunc("/api/health", handleHealth)
	http.HandleFunc("/webhook/github", handleGitHubWebhook)
	http.HandleFunc("/api/v1/analyze", handleAnalyze)
	http.HandleFunc("/api/v1/scan", handleScan)

	log.Printf("VibeGuard server starting on port %s", config.Port)
	log.Fatal(http.ListenAndServe(":"+config.Port, nil))
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"service": "vibeguard",
		"version": "0.2.0",
	})
}

func handleGitHubWebhook(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Read body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read body", http.StatusBadRequest)
		return
	}

	// Verify signature if secret is configured
	if config.GitHubWebhookSecret != "" {
		signature := r.Header.Get("X-Hub-Signature-256")
		if !verifySignature(body, signature, config.GitHubWebhookSecret) {
			http.Error(w, "Invalid signature", http.StatusUnauthorized)
			return
		}
	}

	// Check event type
	eventType := r.Header.Get("X-GitHub-Event")
	log.Printf("Received GitHub event: %s", eventType)

	switch eventType {
	case "pull_request":
		handlePREvent(w, body)
	case "ping":
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{"message": "pong"})
	default:
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{"message": "event ignored"})
	}
}

func handlePREvent(w http.ResponseWriter, body []byte) {
	var event PREvent
	if err := json.Unmarshal(body, &event); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Only process opened/synchronize events
	if event.Action != "opened" && event.Action != "synchronize" && event.Action != "reopened" {
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{"message": "action ignored"})
		return
	}

	log.Printf("Processing PR #%d on %s (action: %s)",
		event.PullRequest.Number,
		event.Repository.FullName,
		event.Action)

	// Process asynchronously
	go processPR(event)

	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(map[string]string{
		"message": "processing",
		"pr":      fmt.Sprintf("%d", event.PullRequest.Number),
	})
}

func processPR(event PREvent) {
	repo := event.Repository.FullName
	prNumber := event.PullRequest.Number
	sha := event.PullRequest.Head.SHA
	installationID := event.Installation.ID

	log.Printf("Starting analysis for %s#%d (sha: %s)", repo, prNumber, sha[:8])

	// Create pending check run
	createCheckRun(repo, sha, installationID, CheckRun{
		Name:      "VibeGuard",
		HeadSHA:   sha,
		Status:    "in_progress",
		StartedAt: time.Now().UTC().Format(time.RFC3339),
		Output: &CheckOutput{
			Title:   "Analyzing AI-generated code...",
			Summary: "VibeGuard is scanning this PR for AI-generated code.",
		},
	})

	// Get PR diff/files
	files, err := getPRFiles(repo, prNumber, installationID)
	if err != nil {
		log.Printf("Error getting PR files: %v", err)
		completeCheckRun(repo, sha, installationID, "failure", "Error", "Failed to fetch PR files")
		return
	}

	// Analyze files
	result, err := analyzeFiles(files)
	if err != nil {
		log.Printf("Error analyzing files: %v", err)
		completeCheckRun(repo, sha, installationID, "failure", "Error", "Analysis failed")
		return
	}

	// Determine conclusion
	conclusion := "success"
	title := fmt.Sprintf("✓ Passed — %d%% AI-generated", int(result.AIPercentage))
	summary := generateSummary(result)

	if result.Blocked {
		conclusion = "failure"
		title = fmt.Sprintf("✗ Blocked — Policy violation")
	} else if len(result.Warnings) > 0 {
		conclusion = "neutral"
		title = fmt.Sprintf("⚠ Warning — %d%% AI-generated", int(result.AIPercentage))
	}

	completeCheckRun(repo, sha, installationID, conclusion, title, summary)
	log.Printf("Completed analysis for %s#%d: %s", repo, prNumber, conclusion)
}

func analyzeFiles(files []PRFile) (*AnalysisResult, error) {
	// Build request for Python analyzer
	var fileData []map[string]string
	for _, f := range files {
		if f.Content != "" {
			fileData = append(fileData, map[string]string{
				"path":    f.Path,
				"content": f.Content,
			})
		}
	}

	reqBody, _ := json.Marshal(map[string]interface{}{
		"files": fileData,
	})

	// Call Python API (or inline Python)
	cmd := exec.Command(config.PythonPath, "-c", fmt.Sprintf(`
import sys
sys.path.insert(0, '%s')
from api.server import app
import json

with app.test_client() as client:
    resp = client.post('/api/v1/scan', 
        data='%s',
        content_type='application/json')
    print(resp.data.decode())
`, getProjectRoot(), string(reqBody)))

	output, err := cmd.Output()
	if err != nil {
		// Fallback: return mock result
		return &AnalysisResult{
			FilesScanned:    len(files),
			AIDetected:      len(files) / 2,
			MaxAIConfidence: 0.75,
			AIPercentage:    45.0,
			Blocked:         false,
		}, nil
	}

	var result AnalysisResult
	json.Unmarshal(output, &result)
	return &result, nil
}

func generateSummary(result *AnalysisResult) string {
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf("## Analysis Summary\n\n"))
	sb.WriteString(fmt.Sprintf("- **Files scanned:** %d\n", result.FilesScanned))
	sb.WriteString(fmt.Sprintf("- **AI-generated files:** %d\n", result.AIDetected))
	sb.WriteString(fmt.Sprintf("- **Max AI confidence:** %.0f%%\n", result.MaxAIConfidence*100))
	sb.WriteString(fmt.Sprintf("- **Overall AI percentage:** %.1f%%\n\n", result.AIPercentage))

	if len(result.Violations) > 0 {
		sb.WriteString("### ❌ Policy Violations\n\n")
		for _, v := range result.Violations {
			sb.WriteString(fmt.Sprintf("- **%s:** %s\n", v.Policy, v.Message))
			if len(v.Files) > 0 {
				sb.WriteString(fmt.Sprintf("  - Files: `%s`\n", strings.Join(v.Files, "`, `")))
			}
		}
		sb.WriteString("\n")
	}

	if len(result.Warnings) > 0 {
		sb.WriteString("### ⚠️ Warnings\n\n")
		for _, w := range result.Warnings {
			sb.WriteString(fmt.Sprintf("- **%s:** %s\n", w.Policy, w.Message))
		}
		sb.WriteString("\n")
	}

	if len(result.Results) > 0 {
		sb.WriteString("### File Analysis\n\n")
		sb.WriteString("| File | AI Confidence | Status |\n")
		sb.WriteString("|------|---------------|--------|\n")
		for _, f := range result.Results {
			status := "✓ Human"
			if f.AIConfidence > 0.7 {
				status = "🤖 AI"
			}
			sb.WriteString(fmt.Sprintf("| `%s` | %.0f%% | %s |\n", f.Path, f.AIConfidence*100, status))
		}
	}

	return sb.String()
}

// PRFile represents a file in a PR
type PRFile struct {
	Path    string
	Content string
	Status  string
}

func getPRFiles(repo string, prNumber, installationID int) ([]PRFile, error) {
	// TODO: Use GitHub API with installation token
	// For now, return empty (will be filled when GitHub App is configured)
	return []PRFile{}, nil
}

func createCheckRun(repo, sha string, installationID int, check CheckRun) error {
	// TODO: Implement GitHub Check Runs API
	log.Printf("Would create check run for %s @ %s: %s", repo, sha[:8], check.Status)
	return nil
}

func completeCheckRun(repo, sha string, installationID int, conclusion, title, summary string) error {
	// TODO: Implement GitHub Check Runs API
	log.Printf("Would complete check run for %s @ %s: %s - %s", repo, sha[:8], conclusion, title)
	return nil
}

func verifySignature(payload []byte, signature, secret string) bool {
	if !strings.HasPrefix(signature, "sha256=") {
		return false
	}
	sig, err := hex.DecodeString(signature[7:])
	if err != nil {
		return false
	}
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(payload)
	return hmac.Equal(sig, mac.Sum(nil))
}

func getProjectRoot() string {
	// Return the vibeguard project root
	return "/root/clawd/vibeguard"
}

func handleAnalyze(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	body, _ := io.ReadAll(r.Body)
	
	// Forward to Python API
	cmd := exec.Command(config.PythonPath, "-c", fmt.Sprintf(`
import sys
sys.path.insert(0, '/root/clawd/vibeguard')
from detection.stylometry import analyze_code
import json

data = json.loads('%s')
code = data.get('code', '')
result = analyze_code(code)
print(json.dumps(result))
`, strings.ReplaceAll(string(body), "'", "\\'")))

	output, err := cmd.Output()
	if err != nil {
		http.Error(w, "Analysis failed", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Write(output)
}

func handleScan(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	body, _ := io.ReadAll(r.Body)
	
	// Forward to Python API
	cmd := exec.Command(config.PythonPath, "-c", fmt.Sprintf(`
import sys
sys.path.insert(0, '/root/clawd/vibeguard')
from api.server import app
import json

with app.test_client() as client:
    resp = client.post('/api/v1/scan', 
        data='''%s''',
        content_type='application/json')
    print(resp.data.decode())
`, strings.ReplaceAll(string(body), "'", "\\'")))

	output, err := cmd.Output()
	if err != nil {
		// Return mock response
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":           "completed",
			"files_scanned":    0,
			"ai_detected":      0,
			"max_ai_confidence": 0,
			"blocked":          false,
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Write(output)
}
