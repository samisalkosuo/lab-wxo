// Scenario: Cloud FinOps. Registers itself on the shared window.SCENARIOS array.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "cloud-finops",
        name: "Cloud FinOps Agent",
        label: "Cloud FinOps",
        description: "Spend anomaly investigation, rightsizing recommendations, and governed resource reclamation",
        industry: "Cross-Industry (Public & Hybrid Cloud Infrastructure)",
        function: "Cloud FinOps & Infrastructure Cost Governance",
        roles: ["FinOps Practitioner / Analyst", "Cloud Solutions Architect", "Engineering Budget Owner", "IT Infrastructure Lead"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Cloud FinOps & Cost Optimization",
            tag: "Scenario 5 • Overview",
            subtitle: "Cloud costs are opaque, vague complaints drive multi-step investigations, and resource changes need human approval before anything is touched.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">💰</div>
                <div>
                  <div class="callout-title">The Problem</div>
                  <div class="callout-text">A bill jumps 30% and no one knows why. Idle resources accumulate unnoticed. A billing error looks like real usage. Acting on any of these without investigation wastes money or breaks something.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Cross-Industry <span style="font-size:12px; color:var(--text-muted);">(Public & Hybrid Cloud Infrastructure)</span></div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Cloud FinOps & Infrastructure Cost Governance</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">FinOps Practitioner / Analyst</span>
                    <span class="fit-pill">Cloud Solutions Architect</span>
                    <span class="fit-pill">Engineering Budget Owner</span>
                    <span class="fit-pill">IT Infrastructure Lead</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">📈</div>
                    <div class="card-title">Unexplained Spend Spikes</div>
                  </div>
                  <div class="card-body">A vague "our bill jumped" report has multiple possible causes: zombie resources, traffic spikes, billing errors, or misconfigurations. Each requires a different response.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🕵️</div>
                    <div class="card-title">Red Herrings and Edge Cases</div>
                  </div>
                  <div class="card-body">A VM with near-zero CPU looks idle — but it runs a Saturday batch job. A billing line shows 1 000 GPU hours — but telemetry records zero usage. Investigation must check all angles.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">Governance Before Action</div>
                  </div>
                  <div class="card-body">Reclaiming or resizing a resource without approval can break a pipeline or cause an outage. Cost-owner sign-off must happen before any infrastructure change.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🎯</div>
                  <div class="card-title">Scenario Objectives</div>
                </div>
                <div class="card-body">
                  <ul>
                    <li><strong>Investigate:</strong> Show progressive multi-step investigation from a vague cost complaint to a specific root cause, using five read-only tools and a policy knowledge base.</li>
                    <li><strong>Govern:</strong> Show two approval flows — one for reclamation, one for rightsizing — where the write tools are never attached to the agent and only fire after cost-owner approval.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 5 • Agent Paradigm",
            subtitle: "A fixed script cannot handle a vague complaint whose investigation path depends on what each tool call returns.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Traditional Approach</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>A FinOps analyst manually queries cost dashboards across services and accounts, then cross-references utilisation telemetry and billing reports — a slow, error-prone process.</li>
                      <li>Policy documents live in a separate wiki. The analyst must look them up, check thresholds, and decide whether to escalate or act — relying on memory and discipline.</li>
                    </ul>
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">🤖</div>
                    <div class="card-title">Agent-Assisted Approach</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>The agent receives a vague complaint, selects which tool to call next based on what the previous call returned, and cites the policy document ID that justifies its recommendation.</li>
                      <li>Write actions — reclaiming or resizing a resource — are gated behind an approval flow. The agent cannot execute them directly; it can only propose.</li>
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
                    <div><strong>Vague input:</strong> "Our bill jumped 30%" has no ticket ID or service name. The agent must start broad and narrow down.</div>
                    <div><strong>Branching path:</strong> a Compute spike leads to zombie VMs; a GPU spike leads to a billing error. The path cannot be drawn in advance.</div>
                    <div><strong>Deterministic gate:</strong> the approval step is a flow, not a prompt rule. It runs the same regardless of what the model says.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 5 • Agent Architecture",
            subtitle: "Five read-only investigative tools, a policy knowledge base, and two governed write flows — the write tools are never given to the agent directly.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">Progressive Investigation</div>
                  </div>
                  <div class="card-body">The agent starts with a spend summary, identifies the biggest mover, drills into the spike explanation, and then verifies each candidate resource's utilisation over a 30-day window (not just 7 days) before drawing a conclusion.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Policy Knowledge Base</div>
                  </div>
                  <div class="card-body">Four plain-text policy documents (CF-POL-01 through CF-POL-04) define idle thresholds, zombie classification, rightsizing criteria, and billing-error escalation. The agent retrieves the relevant document and cites its ID.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Governed Write Flows</div>
                  </div>
                  <div class="card-body">Two separate approval flows: <code>cf_approve_reclaim</code> for reclamation and <code>cf_approve_resize</code> for rightsizing. Each shows a form to the cost owner. <code>cf_reclaim_resource</code> and <code>cf_resize_resource</code> are not attached to the agent.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Tools Attached to the Agent</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">cf_get_spend_summary</span>
                    <span class="tool-chip">cf_list_idle_resources</span>
                    <span class="tool-chip">cf_get_resource_utilization</span>
                    <span class="tool-chip">cf_explain_cost_spike</span>
                    <span class="tool-chip">cf_get_billing_lines</span>
                    <span class="tool-chip">cf_approve_reclaim</span>
                    <span class="tool-chip">cf_approve_resize</span>
                    <span class="tool-chip">cloud_finops_policy</span>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 5 • Enterprise Integration",
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
                      <td><span class="tool-chip">cf_get_spend_summary</span> <span class="tool-chip">cf_explain_cost_spike</span></td>
                      <td>Static Python dicts — per-service spend and root-cause records</td>
                      <td><span class="service-tag">AWS Cost Explorer</span> <span class="service-tag">Azure Cost Management</span> <span class="service-tag">GCP Billing API</span></td>
                      <td>REST API / cloud SDK</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">cf_list_idle_resources</span> <span class="tool-chip">cf_get_resource_utilization</span></td>
                      <td>Static Python dicts — resource inventory and 30-day utilisation records</td>
                      <td><span class="service-tag">CloudWatch Metrics</span> <span class="service-tag">Azure Monitor</span> <span class="service-tag">Datadog</span> <span class="service-tag">Dynatrace</span></td>
                      <td>Metrics API / observability SDK</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">cf_get_billing_lines</span></td>
                      <td>Static billing line items with discrepancy flags</td>
                      <td><span class="service-tag">AWS Billing Console</span> <span class="service-tag">Azure Invoices API</span> <span class="service-tag">Internal finance ERP</span></td>
                      <td>REST API / finance system connector</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">cloud_finops_policy</span></td>
                      <td>Four .txt policy documents (CF-POL-01 through CF-POL-04)</td>
                      <td><span class="service-tag">Confluence</span> <span class="service-tag">SharePoint</span> <span class="service-tag">Internal policy repo</span></td>
                      <td>Built-in KB (vector search)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">cf_approve_reclaim</span> <span class="tool-chip">cf_approve_resize</span></td>
                      <td>Approval flow — form rendered in the WXO chat UI</td>
                      <td><span class="service-tag">ServiceNow Change Management</span> <span class="service-tag">Jira Service Management</span> <span class="service-tag">Custom ITSM</span></td>
                      <td>WXO flow (human-in-the-loop)</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Same Agent, Real Systems</div>
                  <div class="callout-text">Replace the mock Python functions with real API calls to your cloud provider's cost and metrics APIs. The agent instructions, policy KB, and approval flows stay the same.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 5 • Value Proposition",
            subtitle: "What this pattern enables — and where a script or fixed flow remains the better choice.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">🔍</div>
                    <div class="card-title">Root-Cause Investigation from Vague Input</div>
                  </div>
                  <div class="card-body">A plain "our bill jumped" complaint triggers a structured investigation: spend summary → service breakdown → spike explanation → per-resource utilisation check. The path adapts to what each tool returns, not a fixed script.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">📋</div>
                    <div class="card-title">Policy Grounding with Citations</div>
                  </div>
                  <div class="card-body">The agent retrieves the relevant policy document (CF-POL-01 through CF-POL-04) and cites its ID in every recommendation. Thresholds and procedures live in the KB, not hardcoded in the agent instructions.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">🛡️</div>
                    <div class="card-title">Governed Write Actions</div>
                  </div>
                  <div class="card-body">Reclamation and rightsizing are gated behind separate approval flows. The write tools are not attached to the agent. Approve runs the tool; Reject runs nothing. The governance is code, not a prompt instruction.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🚫</div>
                    <div class="card-title">Restraint on Billing Errors</div>
                  </div>
                  <div class="card-body">When a billing line item has a data discrepancy (reported vs. actual usage), the agent flags it and escalates to finance — it does not act. CF-POL-04 defines this restraint; the agent cites it.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">A script is faster, cheaper, and deterministic when the investigation path is fixed and inputs are well-formed. An agent adds value when the input is vague, the next step depends on the previous result, and policy documents change often. The approval gate works identically either way — it is a flow, not agent reasoning. In the smoke run, all four prompts completed with the expected tool sequences and CF-004 produced the correct restraint response. Approval form clicks (Approve/Reject) have not yet been browser-verified.</div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 5 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Vague Bill Spike</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Our cloud bill jumped 30% this month. Can you investigate why?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Vague input — no service or resource named. Watch the agent call cf_get_spend_summary first, then drill into Compute (VMs).</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Idle Resource Scan</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Are there any idle resources in account acct-001 we can reclaim?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Watch for the red herring: vm-batch-weekend-01 looks idle on a 7-day window but has a Saturday batch job visible in the 30-day data.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Reclamation Approval</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">Reclaim the zombie VM vm-zombie-01 in account acct-001. It has been running with no workload since 2025-04-10.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Run twice — once to show Approve (mock reclaim executes), once to show Reject (nothing happens). Use a fresh conversation for each path.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Rightsizing Approval</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">The database cluster db-cluster-prod-01 looks over-provisioned. Can you check and recommend a rightsizing?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The saving figure in the tool result says "illustrative" — point that out. The agent should also mention the change-control window from CF-POL-03.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5</span>
                      <span class="prompt-title">Billing Error Restraint</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">The billing report shows we used 1 000 GPU hours this month. Can you verify that?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The right answer is to do nothing and escalate. Telemetry shows 0 GPU hours consumed. The agent should cite CF-POL-04 and not call any write tool.</span>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
