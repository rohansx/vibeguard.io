package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const (
	version     = "0.2.0"
	defaultAPI  = "https://api.vibeguard.io"
	localAPI    = "http://localhost:8080"
)

type Config struct {
	APIEndpoint string
	APIKey      string
	ConfigPath  string
	Verbose     bool
	Local       bool
}

type ScanResult struct {
	Status          string       `json:"status"`
	FilesScanned    int          `json:"files_scanned"`
	AIDetected      int          `json:"ai_detected"`
	HumanWritten    int          `json:"human_written"`
	MaxAIConfidence float64      `json:"max_ai_confidence"`
	AIPercentage    float64      `json:"ai_percentage"`
	Results         []FileResult `json:"results"`
	Blocked         bool         `json:"blocked"`
	Violations      []Violation  `json:"violations"`
	Warnings        []Warning    `json:"warnings"`
}

type FileResult struct {
	Path         string  `json:"path"`
	AIConfidence float64 `json:"ai_confidence"`
	Status       string  `json:"status"`
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

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(0)
	}

	cmd := os.Args[1]
	args := os.Args[2:]

	switch cmd {
	case "scan":
		cmdScan(args)
	case "analyze":
		cmdAnalyze(args)
	case "init":
		cmdInit(args)
	case "version", "--version", "-v":
		fmt.Printf("vibeguard version %s\n", version)
	case "help", "--help", "-h":
		printUsage()
	default:
		fmt.Printf("Unknown command: %s\n\n", cmd)
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Println(`vibeguard - AI Code Compliance CLI

USAGE:
    vibeguard <command> [options]

COMMANDS:
    scan      Scan files or directories for AI-generated code
    analyze   Analyze a single file
    init      Initialize vibeguard.yaml in current directory
    version   Print version information
    help      Show this help message

SCAN OPTIONS:
    --path, -p <path>     Path to scan (default: current directory)
    --config, -c <file>   Path to vibeguard.yaml config
    --format, -f <fmt>    Output format: text, json, github (default: text)
    --local               Use local Python analyzer (no API)
    --fail-on-block       Exit with code 1 if blocked

EXAMPLES:
    vibeguard scan
    vibeguard scan --path ./src
    vibeguard scan --format json
    vibeguard analyze src/auth/login.ts
    vibeguard init`)
}

func cmdScan(args []string) {
	path := "."
	format := "text"
	local := true // Default to local for now
	failOnBlock := false
	configPath := ""

	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--path", "-p":
			if i+1 < len(args) {
				path = args[i+1]
				i++
			}
		case "--format", "-f":
			if i+1 < len(args) {
				format = args[i+1]
				i++
			}
		case "--config", "-c":
			if i+1 < len(args) {
				configPath = args[i+1]
				i++
			}
		case "--local":
			local = true
		case "--fail-on-block":
			failOnBlock = true
		}
	}

	// Find files to scan
	files, err := findFiles(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error finding files: %v\n", err)
		os.Exit(1)
	}

	if len(files) == 0 {
		fmt.Println("No files found to scan")
		os.Exit(0)
	}

	fmt.Printf("Scanning %d files...\n\n", len(files))

	// Load config if exists
	if configPath == "" {
		configPath = filepath.Join(path, "vibeguard.yaml")
	}

	var result *ScanResult
	if local {
		result, err = scanLocal(files, configPath)
	} else {
		result, err = scanRemote(files, configPath)
	}

	if err != nil {
		fmt.Fprintf(os.Stderr, "Error scanning: %v\n", err)
		os.Exit(1)
	}

	// Output results
	switch format {
	case "json":
		outputJSON(result)
	case "github":
		outputGitHub(result)
	default:
		outputText(result)
	}

	if failOnBlock && result.Blocked {
		os.Exit(1)
	}
}

func cmdAnalyze(args []string) {
	if len(args) == 0 {
		fmt.Println("Usage: vibeguard analyze <file>")
		os.Exit(1)
	}

	filePath := args[0]
	content, err := os.ReadFile(filePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading file: %v\n", err)
		os.Exit(1)
	}

	result, err := analyzeCode(string(content), filePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error analyzing: %v\n", err)
		os.Exit(1)
	}

	conf := result["ai_probability"].(float64) * 100
	status := "human-written"
	statusIcon := "✓"
	if conf > 70 {
		status = "AI-generated"
		statusIcon = "🤖"
	}

	fmt.Printf("%s %s\n", statusIcon, filePath)
	fmt.Printf("   AI Confidence: %.0f%%\n", conf)
	fmt.Printf("   Status: %s\n", status)
}

func cmdInit(args []string) {
	configPath := "vibeguard.yaml"
	if len(args) > 0 {
		configPath = args[0]
	}

	if _, err := os.Stat(configPath); err == nil {
		fmt.Printf("%s already exists\n", configPath)
		os.Exit(1)
	}

	config := `# vibeguard.yaml
version: "1.0"
org: my-org

policies:
  # Block AI code in authentication
  - name: no-ai-in-auth
    description: "AI-generated code not allowed in authentication"
    trigger:
      ai_confidence: "> 70%"
    paths:
      - "src/auth/**"
      - "**/auth*"
      - "**/security/**"
    action: block
    message: "AI-generated code requires security review in auth modules"

  # Require review for high-AI PRs
  - name: high-ai-review
    description: "PRs with >50% AI code need senior review"
    trigger:
      ai_percentage: "> 50%"
      lines_changed: "> 100"
    action: require_reviewers
    reviewers:
      teams: ["senior-engineers"]

  # Warn on quick reviews of AI code
  - name: review-quality
    description: "Flag PRs approved too quickly"
    trigger:
      review_time: "< 2 minutes"
      ai_percentage: "> 30%"
    action: warn
    message: "This PR was approved quickly. Please verify AI-generated sections."
`

	err := os.WriteFile(configPath, []byte(config), 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error writing config: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Created %s\n", configPath)
	fmt.Println("\nEdit this file to customize your AI code policies.")
}

func findFiles(root string) ([]string, error) {
	var files []string

	// File extensions to scan
	extensions := map[string]bool{
		".ts": true, ".tsx": true, ".js": true, ".jsx": true,
		".py": true, ".go": true, ".java": true, ".kt": true,
		".rs": true, ".cpp": true, ".c": true, ".h": true,
		".rb": true, ".php": true, ".swift": true, ".cs": true,
	}

	// Directories to skip
	skipDirs := map[string]bool{
		"node_modules": true, ".git": true, "vendor": true,
		"dist": true, "build": true, "__pycache__": true,
		".next": true, ".nuxt": true, "target": true,
	}

	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}

		if info.IsDir() {
			if skipDirs[info.Name()] {
				return filepath.SkipDir
			}
			return nil
		}

		ext := filepath.Ext(path)
		if extensions[ext] {
			files = append(files, path)
		}

		return nil
	})

	return files, err
}

func scanLocal(files []string, configPath string) (*ScanResult, error) {
	// Read file contents
	var fileData []map[string]string
	for _, f := range files {
		content, err := os.ReadFile(f)
		if err != nil {
			continue
		}
		fileData = append(fileData, map[string]string{
			"path":    f,
			"content": string(content),
		})
	}

	// Read config if exists
	configContent := ""
	if data, err := os.ReadFile(configPath); err == nil {
		configContent = string(data)
	}

	// Build Python script
	reqData := map[string]interface{}{
		"files": fileData,
	}
	if configContent != "" {
		reqData["config"] = configContent
	}
	reqJSON, _ := json.Marshal(reqData)

	script := fmt.Sprintf(`
import sys
sys.path.insert(0, '/root/clawd/vibeguard')
import json

try:
    from detection.stylometry import analyze_code
    from policy.engine import evaluate_commit, EXAMPLE_CONFIG
    
    data = json.loads('''%s''')
    files = data.get('files', [])
    config = data.get('config', EXAMPLE_CONFIG)
    
    results = []
    max_ai = 0
    total_ai_lines = 0
    total_lines = 0
    
    for f in files:
        content = f.get('content', '')
        result = analyze_code(content)
        lines = len(content.split('\n'))
        
        ai_conf = result['ai_probability']
        if ai_conf > max_ai:
            max_ai = ai_conf
        
        if ai_conf > 0.7:
            total_ai_lines += lines
        total_lines += lines
        
        results.append({
            'path': f['path'],
            'ai_confidence': ai_conf,
            'lines_changed': lines,
            'status': 'ai-generated' if ai_conf > 0.7 else 'human-written'
        })
    
    ai_pct = (total_ai_lines / total_lines * 100) if total_lines > 0 else 0
    
    # Evaluate policies
    policy_analysis = {
        'files': results,
        'max_ai_confidence': max_ai,
        'ai_percentage': ai_pct,
        'total_lines_changed': total_lines,
        'security_issues': []
    }
    
    policy_result = evaluate_commit(config, policy_analysis)
    
    output = {
        'status': 'completed',
        'files_scanned': len(results),
        'ai_detected': len([r for r in results if r['status'] == 'ai-generated']),
        'human_written': len([r for r in results if r['status'] == 'human-written']),
        'max_ai_confidence': max_ai,
        'ai_percentage': ai_pct,
        'results': results,
        'blocked': not policy_result['allowed'],
        'violations': policy_result['violations'],
        'warnings': policy_result['warnings']
    }
    
    print(json.dumps(output))
except Exception as e:
    print(json.dumps({'error': str(e)}))
`, strings.ReplaceAll(string(reqJSON), "'", "\\'"))

	cmd := exec.Command("python3", "-c", script)
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("python error: %v", err)
	}

	var result ScanResult
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("parse error: %v", err)
	}

	return &result, nil
}

func scanRemote(files []string, configPath string) (*ScanResult, error) {
	// Read file contents
	var fileData []map[string]string
	for _, f := range files {
		content, err := os.ReadFile(f)
		if err != nil {
			continue
		}
		fileData = append(fileData, map[string]string{
			"path":    f,
			"content": string(content),
		})
	}

	reqData := map[string]interface{}{
		"files": fileData,
	}
	reqJSON, _ := json.Marshal(reqData)

	resp, err := http.Post(localAPI+"/api/v1/scan", "application/json", bytes.NewBuffer(reqJSON))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)

	var result ScanResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, err
	}

	return &result, nil
}

func analyzeCode(code, filename string) (map[string]interface{}, error) {
	script := fmt.Sprintf(`
import sys
sys.path.insert(0, '/root/clawd/vibeguard')
from detection.stylometry import analyze_code
import json

code = '''%s'''
result = analyze_code(code)
result['filename'] = '%s'
print(json.dumps(result))
`, strings.ReplaceAll(code, "'", "\\'"), filename)

	cmd := exec.Command("python3", "-c", script)
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	json.Unmarshal(output, &result)
	return result, nil
}

func outputText(result *ScanResult) {
	// Header
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("  VibeGuard Analysis\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

	// Summary
	fmt.Printf("  Files scanned:     %d\n", result.FilesScanned)
	fmt.Printf("  AI-generated:      %d\n", result.AIDetected)
	fmt.Printf("  Human-written:     %d\n", result.HumanWritten)
	fmt.Printf("  AI percentage:     %.1f%%\n", result.AIPercentage)
	fmt.Printf("  Max AI confidence: %.0f%%\n\n", result.MaxAIConfidence*100)

	// Violations
	if len(result.Violations) > 0 {
		fmt.Printf("  ❌ POLICY VIOLATIONS\n")
		for _, v := range result.Violations {
			fmt.Printf("     • %s: %s\n", v.Policy, v.Message)
			if len(v.Files) > 0 {
				fmt.Printf("       Files: %s\n", strings.Join(v.Files, ", "))
			}
		}
		fmt.Println()
	}

	// Warnings
	if len(result.Warnings) > 0 {
		fmt.Printf("  ⚠️  WARNINGS\n")
		for _, w := range result.Warnings {
			fmt.Printf("     • %s: %s\n", w.Policy, w.Message)
		}
		fmt.Println()
	}

	// File results
	if len(result.Results) > 0 {
		fmt.Printf("  FILES\n")
		for _, f := range result.Results {
			icon := "✓"
			if f.AIConfidence > 0.7 {
				icon = "🤖"
			}
			fmt.Printf("     %s %-40s %3.0f%%\n", icon, truncate(f.Path, 40), f.AIConfidence*100)
		}
		fmt.Println()
	}

	// Status
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	if result.Blocked {
		fmt.Printf("  ❌ BLOCKED - Policy violations detected\n")
	} else if len(result.Warnings) > 0 {
		fmt.Printf("  ⚠️  PASSED with warnings\n")
	} else {
		fmt.Printf("  ✅ PASSED\n")
	}
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
}

func outputJSON(result *ScanResult) {
	output, _ := json.MarshalIndent(result, "", "  ")
	fmt.Println(string(output))
}

func outputGitHub(result *ScanResult) {
	// GitHub Actions output format
	if result.Blocked {
		fmt.Println("::error::VibeGuard: Policy violations detected")
	}
	for _, v := range result.Violations {
		fmt.Printf("::error file=%s::Policy '%s': %s\n", 
			strings.Join(v.Files, ","), v.Policy, v.Message)
	}
	for _, w := range result.Warnings {
		fmt.Printf("::warning::Policy '%s': %s\n", w.Policy, w.Message)
	}
	
	// Set outputs
	fmt.Printf("::set-output name=blocked::%t\n", result.Blocked)
	fmt.Printf("::set-output name=ai_percentage::%.1f\n", result.AIPercentage)
	fmt.Printf("::set-output name=files_scanned::%d\n", result.FilesScanned)
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return "..." + s[len(s)-max+3:]
}
