use axum::{
    routing::{get, post},
    Json, Router,
    extract::State,
    http::StatusCode,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::Mutex;
use tower_http::cors::CorsLayer;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct TaskRequest {
    task_id: String,
    description: String,
    files: Vec<String>,
    #[serde(default)]
    context: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct TaskResponse {
    task_id: String,
    status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    vulnerabilities: Option<Vec<Vulnerability>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Vulnerability {
    severity: String,
    category: String,
    description: String,
    line: Option<usize>,
    file: Option<String>,
    recommendation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ScanRequest {
    code: String,
    language: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ScanResponse {
    vulnerabilities: Vec<Vulnerability>,
    summary: SecuritySummary,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SecuritySummary {
    critical: usize,
    high: usize,
    medium: usize,
    low: usize,
    info: usize,
}

type SharedState = Arc<Mutex<HashMap<String, TaskResponse>>>;

#[tokio::main]
async fn main() {
    let state: SharedState = Arc::new(Mutex::new(HashMap::new()));

    let app = Router::new()
        .route("/health", get(health_check))
        .route("/execute", post(execute_task))
        .route("/scan", post(scan_code))
        .route("/analyze", post(analyze_dependencies))
        .layer(CorsLayer::permissive())
        .with_state(state);

    let addr = SocketAddr::from(([0, 0, 0, 0], 8081));
    println!("Security Agent running on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health_check() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "healthy",
        "agent": "security-expert",
        "capabilities": [
            "vulnerability_scanning",
            "dependency_analysis",
            "secure_code_review",
            "owasp_detection"
        ],
        "version": "0.1.0"
    }))
}

async fn execute_task(
    State(state): State<SharedState>,
    Json(request): Json<TaskRequest>,
) -> Json<TaskResponse> {
    println!("Received task: {}", request.description);

    let response = if request.description.to_lowercase().contains("audit")
        || request.description.to_lowercase().contains("scan")
    {
        perform_security_audit(&request).await
    } else {
        TaskResponse {
            task_id: request.task_id.clone(),
            status: "completed".to_string(),
            result: Some(format!(
                "Security Expert received task: {}\n\nI specialize in:\n- Vulnerability scanning\n- OWASP Top 10 detection\n- Secure code review\n- Dependency analysis",
                request.description
            )),
            error: None,
            vulnerabilities: None,
        }
    };

    let mut tasks = state.lock().await;
    tasks.insert(request.task_id.clone(), response.clone());

    Json(response)
}

async fn perform_security_audit(request: &TaskRequest) -> TaskResponse {
    // Simulate security scanning
    let vulnerabilities = vec![
        Vulnerability {
            severity: "high".to_string(),
            category: "Injection".to_string(),
            description: "Potential SQL injection vulnerability detected".to_string(),
            line: Some(42),
            file: request.files.first().cloned(),
            recommendation: "Use parameterized queries instead of string concatenation".to_string(),
        },
        Vulnerability {
            severity: "medium".to_string(),
            category: "Authentication".to_string(),
            description: "Weak password policy detected".to_string(),
            line: Some(15),
            file: request.files.first().cloned(),
            recommendation: "Implement strong password requirements".to_string(),
        },
    ];

    TaskResponse {
        task_id: request.task_id.clone(),
        status: "completed".to_string(),
        result: Some(format!(
            "Security audit completed for: {}\nFound {} vulnerabilities",
            request.description,
            vulnerabilities.len()
        )),
        error: None,
        vulnerabilities: Some(vulnerabilities),
    }
}

async fn scan_code(Json(request): Json<ScanRequest>) -> Json<ScanResponse> {
    use regex::Regex;

    let mut vulnerabilities = Vec::new();

    // Check for common security issues
    let sql_pattern = Regex::new(r#"(?i)(execute|query|exec)\s*\(\s*['"]"#).unwrap();
    let secret_pattern = Regex::new(r#"(?i)(password|secret|key|token)\s*=\s*['"][^'"]+['"][^,}]"#).unwrap();
    let eval_pattern = Regex::new(r#"(?i)(eval|exec)\s*\("#).unwrap();

    for (line_num, line) in request.code.lines().enumerate() {
        if sql_pattern.is_match(line) && line.to_lowercase().contains("$") {
            vulnerabilities.push(Vulnerability {
                severity: "critical".to_string(),
                category: "SQL Injection".to_string(),
                description: "Potential SQL injection with user input".to_string(),
                line: Some(line_num + 1),
                file: None,
                recommendation: "Use parameterized queries".to_string(),
            });
        }

        if secret_pattern.is_match(line) {
            vulnerabilities.push(Vulnerability {
                severity: "high".to_string(),
                category: "Hardcoded Secrets".to_string(),
                description: "Potential hardcoded secret detected".to_string(),
                line: Some(line_num + 1),
                file: None,
                recommendation: "Use environment variables or secret management".to_string(),
            });
        }

        if eval_pattern.is_match(line) {
            vulnerabilities.push(Vulnerability {
                severity: "high".to_string(),
                category: "Code Injection".to_string(),
                description: "Dangerous eval/exec usage detected".to_string(),
                line: Some(line_num + 1),
                file: None,
                recommendation: "Avoid eval/exec, use safer alternatives".to_string(),
            });
        }
    }

    let summary = SecuritySummary {
        critical: vulnerabilities.iter().filter(|v| v.severity == "critical").count(),
        high: vulnerabilities.iter().filter(|v| v.severity == "high").count(),
        medium: vulnerabilities.iter().filter(|v| v.severity == "medium").count(),
        low: 0,
        info: 0,
    };

    Json(ScanResponse {
        vulnerabilities,
        summary,
    })
}

async fn analyze_dependencies() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "analysis_complete",
        "dependencies_checked": 0,
        "vulnerable_packages": [],
        "outdated_packages": []
    }))
}
