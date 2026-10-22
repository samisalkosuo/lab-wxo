// Scenario: Incident Triage. Registers itself on the shared window.SCENARIOS array.
// Order of <script src> tags in presentation.html decides the sidebar number.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "incident-triage",
        name: "Incident Triage Agent",
        label: "Incident Triage",
        description: "Multi-source correlation & governed remediation",
        industry: "Cross-Industry (Cloud & Digital Services)",
        function: "Site Reliability Engineering (SRE) & IT Operations",
        roles: ["Site Reliability Engineer (SRE)", "Incident Commander", "DevOps Engineer", "IT Operations Manager"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Production Incident Triage",
            tag: "Scenario 1 • Overview",
            subtitle: "Autonomous multi-service diagnostics and governed remediation for high-severity production incidents.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">⚡</div>
                <div>
                  <div class="callout-title">The High-Pressure SRE Challenge</div>
                  <div class="callout-text">During production outages, engineers face high cognitive load, alert fatigue, and fragmented observability tools across logs, metrics, and deployment pipelines. Diagnosing root causes under tight SLAs is often slow and error-prone.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Cross-Industry <span style="font-size:12px; color:var(--text-muted);">(Cloud & Digital Services)</span></div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Site Reliability Engineering (SRE) & IT Operations</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">Site Reliability Engineer (SRE)</span>
                    <span class="fit-pill">Incident Commander</span>
                    <span class="fit-pill">DevOps Engineer</span>
                    <span class="fit-pill">IT Operations Manager</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">Alert Storms & Noise</div>
                  </div>
                  <div class="card-body">
                    Multiple microservices fire alerts concurrently. Engineers must separate genuine service regressions from planned maintenance or load tests.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔍</div>
                    <div class="card-title">Fragmented Data</div>
                  </div>
                  <div class="card-body">
                    Evidence is scattered across log aggregators, APM metrics, Git deployment commits, and internal runbook wikis.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">Remediation Risk</div>
                  </div>
                  <div class="card-body">
                    Applying fixes (rollbacks, pool resizes, restarts) carries high risk. Infrastructure modifications require governed human-in-the-loop sign-off.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🎯</div>
                  <div class="card-title">Scenario Objectives</div>
                </div>
                <div class="card-body">
                  <ul>
                    <li><strong>Accelerate MTTR:</strong> Correlate health checks, error logs, saturation metrics, and recent deployments in seconds.</li>
                    <li><strong>Evidence-Based Runbook Guidance:</strong> Match symptoms directly against standard operating procedures with explicit citations.</li>
                    <li><strong>Strict Governance:</strong> Propose remediations through interactive approval forms while completely blocking direct execution permissions from the LLM.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 1 • Agent Paradigm",
            subtitle: "Moving from manual dashboard hopping to intelligent conversational investigation.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Traditional Manual Triage</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Engineer receives vague alert (e.g. "checkout slow").</li>
                      <li>Manually switches between 4+ browser tabs: Grafana, Kibana, GitHub Deployments, Confluence Runbooks.</li>
                      <li>Runs repetitive grep commands and interprets complex stack traces.</li>
                      <li>High risk of pursuing red herrings or applying wrong remediation procedures.</li>
                    </ul>
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">🤖</div>
                    <div class="card-title">Agent-Assisted Triage</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Engineer queries WXO chat with natural language or incident IDs.</li>
                      <li>Agent autonomously queries relevant diagnostic tools based on initial symptoms.</li>
                      <li>Synthesizes findings into concise, evidence-backed root cause explanations.</li>
                      <li>Presents a pre-filled remediation proposal for 1-click human approval.</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-purple">🧠</div>
                  <div class="card-title">Why an Agentic Solution?</div>
                </div>
                <div class="card-body">
                  <div class="grid-3" style="margin-bottom:0;">
                    <div>
                      <strong>Dynamic Investigation Path:</strong> Unlike rigid scripts, the agent adapts its tool calls based on intermediate findings (e.g. querying logs first, then metrics, or skipping unnecessary checks).
                    </div>
                    <div>
                      <strong>Natural Language Synthesis:</strong> Translates raw JSON payloads, N+1 query logs, and latency spikes into clear executive summaries with actionable recommendations.
                    </div>
                    <div>
                      <strong>Unifying Disparate Silos:</strong> Acts as an intelligent orchestration layer across monitoring, logging, CI/CD, and knowledge bases.
                    </div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 1 • Agent Architecture",
            subtitle: "An evidence-based ReAct loop coupled with bounded tools, vectorized knowledge, and a governed flow.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">ReAct Core Loop</div>
                  </div>
                  <div class="card-body">
                    Powered by <code>gpt-oss-120b</code>. Operates on a strict evidence standard: requires at least two corroborating pieces of evidence before asserting root cause.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Runbook Knowledge Base</div>
                  </div>
                  <div class="card-body">
                    Retrieves vetted SRE runbooks via <code>ibm/slate-125m</code> embeddings. Agent cites specific runbook IDs (e.g. <code>RB-DEPLOY-01</code>) in all recommendations.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Approval Flow Gate</div>
                  </div>
                  <div class="card-body">
                    The agent calls <code>request_remediation</code> to trigger a governed flow. The dangerous tool (<code>execute_remediation</code>) is decoupled from the agent entirely.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Specialized Diagnostic Toolset</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">list_open_incidents</span>
                    <span class="tool-chip">get_incident</span>
                    <span class="tool-chip">get_service_health</span>
                    <span class="tool-chip">query_logs</span>
                    <span class="tool-chip">get_metrics</span>
                    <span class="tool-chip">list_recent_deployments</span>
                    <span class="tool-chip">open_ticket</span>
                    <span class="tool-chip">request_remediation</span>
                  </div>
                </div>
              </div>

              <div class="callout-banner" style="margin-top: 20px;">
                <div class="callout-icon">🔍</div>
                <div>
                  <div class="callout-title">Full OpenTelemetry Observability</div>
                  <div class="callout-text">Every reasoning step, tool invocation, token count, and execution latency is captured as an OpenTelemetry trace in watsonx Orchestrate for compliance and auditability.</div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 1 • Enterprise Integration",
            subtitle: "How agent tools translate to production enterprise systems in your technology stack.",
            render: () => `
              <div class="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Agent Capability / Tool</th>
                      <th>Mock Environment</th>
                      <th>Enterprise Real-Life Systems</th>
                      <th>Integration Protocol</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><span class="tool-chip">list_open_incidents</span><br><span class="tool-chip">get_incident</span></td>
                      <td>Static Incident Store (INC-1001–INC-1004)</td>
                      <td><span class="service-tag">PagerDuty, ServiceNow ITSM, OpsGenie, Jira Service Management</span></td>
                      <td>REST API / Webhooks</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">get_service_health</span><br><span class="tool-chip">get_metrics</span></td>
                      <td>Mock In-Memory Metrics (Latency, DB Pool)</td>
                      <td><span class="service-tag">Datadog, Dynatrace, Prometheus / Grafana, Instana, CloudWatch</span></td>
                      <td>OpenAPI / PromQL Query API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">query_logs</span></td>
                      <td>Mock Error & Warning Log Filter</td>
                      <td><span class="service-tag">Splunk, ElasticSearch, OpenSearch, AWS CloudWatch Logs</span></td>
                      <td>Log Search APIs / Lucene Query</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">list_recent_deployments</span></td>
                      <td>Mock Deployment History (DEP-4108)</td>
                      <td><span class="service-tag">GitHub Deployments, ArgoCD, GitLab CI, Harness, Octopus</span></td>
                      <td>GitHub API / Kubernetes API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">incident_triage_runbooks</span></td>
                      <td>Local Markdown Runbooks</td>
                      <td><span class="service-tag">Confluence, Notion, ServiceNow Knowledge Base, Git Docs</span></td>
                      <td>watsonx Vector Store / Milvus</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">execute_remediation</span></td>
                      <td>Mock Rollback & Pool Resize Script</td>
                      <td><span class="service-tag">Argo Rollouts, Kubernetes API, Ansible Automation Platform, Terraform</span></td>
                      <td>Governed WXO Action Flow</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Zero Custom Glue Code Required</div>
                  <div class="callout-text">watsonx Orchestrate natively connects OpenAPI specifications and enterprise pre-built connectors directly to the agent without requiring bespoke integration middle layers.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Benefits of Using the Agent
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 1 • Value Proposition",
            subtitle: "Measurable improvements in operational resilience, speed, and safety.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📉</div>
                    <div class="card-title">Dramatic MTTR Reduction</div>
                  </div>
                  <div class="card-body">
                    Reduces mean time to resolution from 30–45 minutes of manual triage to under 15 seconds of automated data aggregation and correlation.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Cognitive Relief for On-Call</div>
                  </div>
                  <div class="card-body">
                    Eliminates context switching across multiple monitoring dashboards and wikis during 3 AM high-severity outage alerts.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">📋</div>
                    <div class="card-title">Consistent, Auditable Triage</div>
                  </div>
                  <div class="card-body">
                    Standardizes diagnostic rigor across the organization. Every conclusion is backed by explicit citations from approved company runbooks.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Human-Governed Safety Gate</div>
                  </div>
                  <div class="card-body">
                    Guarantees safety by preventing autonomous destructive actions. Remediation tools remain gated behind explicit interactive approval flows.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">
                  While simple static scripts work well for fixed, predictable rules, <strong>Agents excel when inputs vary, log formats evolve, or cross-system hypothesis testing is required</strong> — while providing natural language explanations to the human approver.
                </div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts Board
          {
            title: "Live Demo Prompts",
            tag: "Scenario 1 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <!-- Scene 1 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Vague Opening • Autonomous Discovery</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Hey, checkout is slow. Can you look into it?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Demonstrates agent discovering open incidents and picking INC-1001 without being given the ID.</span>
                  </div>
                </div>

                <!-- Scene 2 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Diagnosis • Bad Deployment Correlation (INC-1001)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Investigate incident INC-1001 on the checkout service. Use your tools to find the root cause. Do NOT call request_remediation - just report your diagnosis and what remediation action you would recommend.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Demonstrates multi-tool evidence collection (latency metric + N+1 query logs + deployment DEP-4108 + RB-DEPLOY-01).</span>
                  </div>
                </div>

                <!-- Scene 3 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Red Herring • Dismissing False Leads (INC-1002)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">Investigate incident INC-1002 on the payments service. There was a recent deployment to notification-service - could that be related? Use your tools to find the root cause. Do NOT call request_remediation - just report your diagnosis and recommended action.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Demonstrates checking user-suggested suspect, dismissing it via runbook rules, and isolating DB pool exhaustion.</span>
                  </div>
                </div>

                <!-- Scene 4 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Approval Flow • Interactive Form (Approve / Reject)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">There is a critical incident on the checkout service, INC-1001. Logs show an N+1 query regression introduced by a recent deployment. Investigate and propose a fix.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Triggers interactive approval form card in WXO UI. Demo 'Approve' in one thread and 'Reject' in a second thread.</span>
                  </div>
                </div>

                <!-- Scene 5 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5</span>
                      <span class="prompt-title">Restraint • Non-Incident & Noise Filtering (INC-1004)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">Investigate incident INC-1004. Use your tools to find the root cause and whether any action is needed.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Demonstrates intelligent restraint: recognizes scheduled load test and correctly recommends NO action.</span>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
