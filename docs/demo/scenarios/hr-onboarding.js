// Scenario: HR Onboarding. Registers itself on the shared window.SCENARIOS array.
// Sidebar position 4 — fourth <script src> tag in presentation.html.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "hr-onboarding",
        name: "HR Onboarding Agent",
        label: "HR Onboarding",
        description: "Employee provisioning, access governance & department workflows",
        industry: "Cross-Industry (Workforce & People Operations)",
        function: "Human Resources (HR Ops) & IT Identity Provisioning",
        roles: ["HR Operations Coordinator", "IT Access & Identity Admin", "Hiring Manager", "HR Compliance Officer"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Automated HR Onboarding",
            tag: "Scenario 4 • Overview",
            subtitle: "Conversational new-hire provisioning, role-based access governance, and department compliance workflows.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">🚀</div>
                <div>
                  <div class="callout-title">The Onboarding Governance Challenge</div>
                  <div class="callout-text">HR coordinators must onboard diverse new hires across engineering, finance, and other departments. Each hire has different systems allowed, equipment rules, and compliance gates. Traditional manual checklists are slow, error-prone, and lack centralized access governance.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Cross-Industry <span style="font-size:12px; color:var(--text-muted);">(Workforce & People Operations)</span></div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Human Resources (HR Ops) & IT Identity Provisioning</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">HR Operations Coordinator</span>
                    <span class="fit-pill">IT Access & Identity Admin</span>
                    <span class="fit-pill">Hiring Manager</span>
                    <span class="fit-pill">HR Compliance Officer</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">📋</div>
                    <div class="card-title">Incomplete Intake Data</div>
                  </div>
                  <div class="card-body">
                    Hires are frequently registered with missing info like equipment choices. Fixed workflow forms fail or halt when any key data point is absent.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Access Over-Provisioning</div>
                  </div>
                  <div class="card-body">
                    Engineering hires may get ledger access or contractors may get full corporate mailboxes, violating principle of least privilege and policy bounds.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">⚖️</div>
                    <div class="card-title">Compliance Bypass Risk</div>
                  </div>
                  <div class="card-body">
                    Regulated departments like Finance require secondary compliance reviewer approval. Traditional approaches often bypass this check.
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
                    <li><strong>Intelligent Intake:</strong> The agent converses naturally, detects missing fields, and completes the record before proposing access.</li>
                    <li><strong>Rigid Code-Level Enforcement:</strong> Ensures that write operations (<code>hr_provision_access</code>) only run after explicit human approval, with automated department checks.</li>
                    <li><strong>Compliance Gates:</strong> Multi-reviewer sign-off is dynamically triggered for compliance-gated departments (e.g. Finance).</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 4 • Agent Paradigm",
            subtitle: "Moving from manual checklists and unsafe forms to a policy-grounded conversational onboarding assistant.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Traditional Approach</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Coordinators print static paper/wiki checklists with different rules per role.</li>
                      <li>Incomplete forms are returned back and forth, stalling the start date.</li>
                      <li>Permissions are requested directly from IT, leading to over-provisioned access.</li>
                      <li>Approval guidelines are manually cross-checked against long policy documents.</li>
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
                      <li>Agent finds the hire, flags missing fields, and queries coordinates in real-time.</li>
                      <li>Agent correlates the exact system list allowed for the role from local database.</li>
                      <li>Agent checks department rules to trigger standard vs. compliance-gated approvals.</li>
                      <li>Coordinator receives a transparent summary and policy citation prior to starting the flow.</li>
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
                    <div><strong>Flexible Clarification:</strong> Resolves missing variables conversating without crashing fixed backend logic templates.</div>
                    <div><strong>Complex Policy Guidance:</strong> Resolves exceptions like contractor durations or bulk-provision bans in natural language.</div>
                    <div><strong>Seamless Orchestration:</strong> Handles read tools, status checks, and governed flows in a single uniform interface.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 4 • Agent Architecture",
            subtitle: "The architecture splits agent intelligence (read-only tools & policy lookup) from human-governed execution (approval flows).",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">Read-Only Tools</div>
                  </div>
                  <div class="card-body">
                    The agent is equipped with five query tools to safely inspect hires, check role permissions, verify current status, and check compliance rules.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Knowledge Base</div>
                  </div>
                  <div class="card-body">
                    The <code>hr_onboarding_policy</code> knowledge base contains standard onboarding rules, contractor constraints, and compliance sign-off procedures.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Governed Flow Gate</div>
                  </div>
                  <div class="card-body">
                    The write action (<code>hr_provision_access</code>) is hidden behind two flows. Only after human approval are credentials issued.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">Scaffolded Capabilities & Flows</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">hr_list_pending_hires</span>
                    <span class="tool-chip">hr_get_new_hire</span>
                    <span class="tool-chip">hr_get_role_access</span>
                    <span class="tool-chip">hr_get_department_config</span>
                    <span class="tool-chip">hr_check_provisioning_status</span>
                    <span class="tool-chip">hr_request_provisioning</span>
                    <span class="tool-chip">hr_request_compliance_provisioning</span>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 4 • Enterprise Integration",
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
                      <td><span class="tool-chip">hr_get_new_hire</span> / <span class="tool-chip">hr_list_pending_hires</span></td>
                      <td>Fictional Static Employee Database</td>
                      <td><span class="service-tag">Workday, SuccessFactors, Oracle HCM, BambooHR</span></td>
                      <td>REST API (JSON)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_get_role_access</span></td>
                      <td>Fictional Role Access Matrix</td>
                      <td><span class="service-tag">Okta, SailPoint, Microsoft Entra ID (Azure AD), Ping Identity</span></td>
                      <td>OIDC / SCIM / LDAP Directory APIs</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_onboarding_policy</span></td>
                      <td>Local text policy files</td>
                      <td><span class="service-tag">SharePoint, Confluence, ServiceNow Knowledge Base, internal wiki</span></td>
                      <td>watsonx Vector Store (Milvus)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_request_provisioning</span> / <span class="tool-chip">hr_request_compliance_provisioning</span></td>
                      <td>Interactive approval forms and write script</td>
                      <td><span class="service-tag">ServiceNow, Jira Service Management, Salesforce, internal admin panel</span></td>
                      <td>Governed WXO Action Flow / SOAP / REST</td>
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

          // Slide 5: Business & Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 4 • Value Proposition",
            subtitle: "Measurable improvements in operational compliance, data consistency, and speed.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📉</div>
                    <div class="card-title">Rapid Onboarding Time</div>
                  </div>
                  <div class="card-body">
                    Reduces employee provisioning setup from several days of manual scheduling down to under 5 minutes of automated workflows and instant approvals.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Cognitive Relief for HR Coordinators</div>
                  </div>
                  <div class="card-body">
                    Eliminates manual checklist correlation across multiple spreadsheets, departments, and policy pages during the busy onboarding seasons.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">📋</div>
                    <div class="card-title">Guaranteed Compliance</div>
                  </div>
                  <div class="card-body">
                    Guarantees standard or compliance-gated flows based strictly on department settings. No human or LLM can accidentally bypass the compliance reviewer gate.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Governance Enforced in Code</div>
                  </div>
                  <div class="card-body">
                    Protects resources by strictly verifying credentials and rules inside the provisioning script (no admin access, only single hire ID requests).
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">
                  While a simple static script can execute the final provisioning, an <strong>Agent is uniquely suited for intake</strong> — collecting missing variables from coordinators dynamically in natural language, citing policies, and setting up the precise execution payload.
                </div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 4 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <!-- Scene 1 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Standard Employee with Missing Field</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Onboard Alex Kim, Software Engineer, starts 2025-06-09.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Demonstrates agent identifying missing equipment choice in the record, and offering options before proposing access.</span>
                    <button class="script-btn" onclick="showFullScript(1)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <!-- Scene 2 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Contractor Restricted Access</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Set up contractor access for Jordan Lee.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Demonstrates contractor policy lookup, offering guest chat and time-limited VPN access while citing HR-POL-02.</span>
                    <button class="script-btn" onclick="showFullScript(2)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <!-- Scene 3 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Finance compliance gated onboarding</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">Add Sarah Chen to the Finance team.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Demonstrates department configuration triggering the compliance-gated flow with two sequential approval forms (HR Manager & Compliance).</span>
                    <button class="script-btn" onclick="showFullScript(3)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <!-- Scene 4 -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Restraint: Bulk/Admin ban refusal</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">Can you provision admin rights for the whole team?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Demonstrates restraint: the agent declines bulk/admin requests and cites HR-POL-04, keeping the organization secure.</span>
                    <button class="script-btn" onclick="showFullScript(4)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
