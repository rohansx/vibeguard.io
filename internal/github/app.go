package github

import (
	"bytes"
	"crypto/rsa"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// App represents a GitHub App
type App struct {
	ID         string
	PrivateKey *rsa.PrivateKey
	httpClient *http.Client
}

// Installation represents a GitHub App installation
type Installation struct {
	ID          int    `json:"id"`
	Account     Account `json:"account"`
	AccessToken string  `json:"-"`
}

type Account struct {
	Login string `json:"login"`
	Type  string `json:"type"`
}

// AccessToken represents an installation access token
type AccessToken struct {
	Token     string    `json:"token"`
	ExpiresAt time.Time `json:"expires_at"`
}

// NewApp creates a new GitHub App client
func NewApp(appID, privateKeyPEM string) (*App, error) {
	block, _ := pem.Decode([]byte(privateKeyPEM))
	if block == nil {
		return nil, fmt.Errorf("failed to parse PEM block")
	}

	key, err := x509.ParsePKCS1PrivateKey(block.Bytes)
	if err != nil {
		// Try PKCS8
		keyInterface, err := x509.ParsePKCS8PrivateKey(block.Bytes)
		if err != nil {
			return nil, fmt.Errorf("failed to parse private key: %v", err)
		}
		var ok bool
		key, ok = keyInterface.(*rsa.PrivateKey)
		if !ok {
			return nil, fmt.Errorf("not an RSA key")
		}
	}

	return &App{
		ID:         appID,
		PrivateKey: key,
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}, nil
}

// GenerateJWT generates a JWT for authenticating as the app
func (a *App) GenerateJWT() (string, error) {
	now := time.Now()
	claims := jwt.MapClaims{
		"iat": now.Unix(),
		"exp": now.Add(10 * time.Minute).Unix(),
		"iss": a.ID,
	}

	token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
	return token.SignedString(a.PrivateKey)
}

// GetInstallationToken gets an access token for an installation
func (a *App) GetInstallationToken(installationID int) (*AccessToken, error) {
	jwt, err := a.GenerateJWT()
	if err != nil {
		return nil, err
	}

	url := fmt.Sprintf("https://api.github.com/app/installations/%d/access_tokens", installationID)
	req, _ := http.NewRequest("POST", url, nil)
	req.Header.Set("Authorization", "Bearer "+jwt)
	req.Header.Set("Accept", "application/vnd.github+json")

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 201 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to get token: %s", body)
	}

	var token AccessToken
	json.NewDecoder(resp.Body).Decode(&token)
	return &token, nil
}

// Client represents an authenticated GitHub client
type Client struct {
	Token      string
	httpClient *http.Client
}

// NewClient creates a new authenticated GitHub client
func NewClient(token string) *Client {
	return &Client{
		Token:      token,
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
}

// CreateCheckRun creates a new check run
func (c *Client) CreateCheckRun(owner, repo string, check CheckRun) (*CheckRunResponse, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/check-runs", owner, repo)
	
	body, _ := json.Marshal(check)
	req, _ := http.NewRequest("POST", url, bytes.NewBuffer(body))
	req.Header.Set("Authorization", "Bearer "+c.Token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 201 {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to create check run: %s", respBody)
	}

	var result CheckRunResponse
	json.NewDecoder(resp.Body).Decode(&result)
	return &result, nil
}

// UpdateCheckRun updates an existing check run
func (c *Client) UpdateCheckRun(owner, repo string, checkRunID int64, check CheckRun) error {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/check-runs/%d", owner, repo, checkRunID)
	
	body, _ := json.Marshal(check)
	req, _ := http.NewRequest("PATCH", url, bytes.NewBuffer(body))
	req.Header.Set("Authorization", "Bearer "+c.Token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to update check run: %s", respBody)
	}

	return nil
}

// GetPRFiles gets the files changed in a pull request
func (c *Client) GetPRFiles(owner, repo string, prNumber int) ([]PRFile, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/pulls/%d/files", owner, repo, prNumber)
	
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", "Bearer "+c.Token)
	req.Header.Set("Accept", "application/vnd.github+json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to get PR files: %s", respBody)
	}

	var files []PRFile
	json.NewDecoder(resp.Body).Decode(&files)
	return files, nil
}

// GetFileContent gets the content of a file
func (c *Client) GetFileContent(owner, repo, path, ref string) (string, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/contents/%s?ref=%s", owner, repo, path, ref)
	
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", "Bearer "+c.Token)
	req.Header.Set("Accept", "application/vnd.github.raw+json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("failed to get file: %d", resp.StatusCode)
	}

	content, _ := io.ReadAll(resp.Body)
	return string(content), nil
}

// CheckRun represents a GitHub check run
type CheckRun struct {
	Name        string       `json:"name"`
	HeadSHA     string       `json:"head_sha"`
	Status      string       `json:"status,omitempty"`
	Conclusion  string       `json:"conclusion,omitempty"`
	StartedAt   string       `json:"started_at,omitempty"`
	CompletedAt string       `json:"completed_at,omitempty"`
	Output      *CheckOutput `json:"output,omitempty"`
}

type CheckOutput struct {
	Title       string        `json:"title"`
	Summary     string        `json:"summary"`
	Text        string        `json:"text,omitempty"`
	Annotations []Annotation  `json:"annotations,omitempty"`
}

type Annotation struct {
	Path            string `json:"path"`
	StartLine       int    `json:"start_line"`
	EndLine         int    `json:"end_line"`
	AnnotationLevel string `json:"annotation_level"` // notice, warning, failure
	Message         string `json:"message"`
	Title           string `json:"title,omitempty"`
}

type CheckRunResponse struct {
	ID int64 `json:"id"`
}

// PRFile represents a file in a pull request
type PRFile struct {
	SHA       string `json:"sha"`
	Filename  string `json:"filename"`
	Status    string `json:"status"`
	Additions int    `json:"additions"`
	Deletions int    `json:"deletions"`
	Changes   int    `json:"changes"`
	RawURL    string `json:"raw_url"`
	Patch     string `json:"patch"`
}
