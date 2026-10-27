// Scenario: YEL Income Assessment. Registers itself on the shared window.SCENARIOS array.
// Order of <script src> tags in presentation.html decides the sidebar number.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "yel-income-assessment",
        name: "YEL Income Assessment Agent",
        label: "YEL Income Assessment",
        description: "Statutory YEL confirmed work income review & approval",
        industry: "Finnish Statutory Pension Insurance (YEL)",
        function: "YEL Underwriting & Entrepreneur Advisory",
        roles: ["YEL Underwriter (YEL-ratkaisija)", "Entrepreneur Account Specialist", "Insurance Operations Supervisor"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "YEL Confirmed Work Income Review",
            tag: "Scenario 8 • Overview",
            subtitle: "Statutory triennial YEL income assessment with sector benchmarking, social benefit impact analysis, and governed determination.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">📋</div>
                <div>
                  <div class="callout-title">The YEL Income Assessment Challenge</div>
                  <div class="callout-text">The 2023 YEL reform requires Finnish pension providers to review every self-employed person's confirmed work income every three years against sector wage benchmarks. Assessments involve multi-faceted business situations — part-time owners, high-turnover but low-contribution cases, first-time entrepreneurs, and below-threshold freelancers — that a simple lookup cannot resolve. Every formal determination is a legally appealable administrative decision.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Finnish Statutory Pension Insurance <span style="font-size:12px; color:var(--text-muted);">(Työeläke & YEL)</span></div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">YEL Underwriting &amp; Entrepreneur Advisory</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">YEL Underwriter (YEL-ratkaisija)</span>
                    <span class="fit-pill">Entrepreneur Account Specialist</span>
                    <span class="fit-pill">Insurance Operations Supervisor</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">Complex, Contested Cases</div>
                  </div>
                  <div class="card-body">
                    Entrepreneurs present split roles, seasonal fluctuations, holding company structures, and high subcontracting costs. Turnover does not equal work input; each case requires individual analysis.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔍</div>
                    <div class="card-title">Multi-Source Statutory Logic</div>
                  </div>
                  <div class="card-body">
                    The recommendation must apply sector median wages from Statistics Finland / ETK, the EUR 4,000 statutory transition cap, part-time hours adjustments, and the 22% beginner discount — all in the correct sequence.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">Legal Determination Risk</div>
                  </div>
                  <div class="card-body">
                    Every formal determination is a legally appealable administrative decision (valituskelpoinen päätös). Issuing incorrect decisions without underwriter sign-off exposes the provider to TELK appeals and regulatory risk.
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
                    <li><strong>Income Assessment:</strong> Apply sector benchmark, hours ratio, transition cap, and beginner discount to derive a statutory recommendation — with full policy citation.</li>
                    <li><strong>Governed Decision:</strong> Route every formal determination through the yel_issue_decision approval flow so no legally binding record is issued without underwriter sign-off.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 8 • Agent Paradigm",
            subtitle: "From manual benchmark lookups and spreadsheet calculations to a conversational, evidence-driven assessment workflow.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Without the Agent</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Underwriter manually queries ETK wage statistics, applies the cap and hours adjustment in a spreadsheet, and writes a justification from scratch for each case.</li>
                      <li>Entrepreneur disputes require re-reading the YEL Act, searching for the kuuleminen procedure, and re-calculating with adjusted inputs — all in separate tools with no audit trail.</li>
                    </ul>
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">🤖</div>
                    <div class="card-title">With the Agent</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>One conversation: the agent retrieves the entrepreneur profile, fetches the sector benchmark, applies all statutory rules, estimates the social security benefit impact, and surfaces a cited recommendation with step-by-step reasoning.</li>
                      <li>The underwriter reviews the assessment and clicks one button to confirm, adjust, or escalate — all within the same chat thread, with a formal record issued automatically on approval.</li>
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
                    <div><strong>Adaptive reasoning:</strong> Split-role entrepreneurs (e.g. part-time baker + manager) require dynamic hours adjustment, not a fixed formula. The agent asks for evidence and recalculates.</div>
                    <div><strong>Multi-step evidence chain:</strong> Profile → benchmark → cap logic → benefit impact → policy citation — the correct sequence cannot be short-circuited without risking a legally unsound decision.</div>
                    <div><strong>Restraint case:</strong> When revenue is below the EUR 9,010/yr threshold, the agent must identify non-applicability and stop — not attempt an income assessment that would be legally incorrect.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 8 • Agent Architecture",
            subtitle: "ReAct loop with four read-only tools, a YEL policy knowledge base, and a human-governed determination flow.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">ReAct Loop</div>
                  </div>
                  <div class="card-body">The agent uses a ReAct (Reason + Act) loop. Each tool call informs the next step: it does not retrieve all data upfront, but sequences calls based on what it finds — stopping as soon as non-applicability is confirmed.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">YEL Policy Knowledge Base</div>
                  </div>
                  <div class="card-body">Four plain-text policy documents (YEL-POL-01 to YEL-POL-04) covering income definition, the transition cap, social security linkage and the beginner discount, and the kuuleminen / TELK appeals process. The agent is instructed to cite document IDs in every assessment.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Governed Determination Flow</div>
                  </div>
                  <div class="card-body">The write tool (yel_issue_decision_record) is not attached to the agent. It is only reachable through the yel_issue_decision approval flow, which presents the proposal to the underwriter and offers three actions: Confirm, Adjust &amp; Issue, or Escalate to Appeals.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Agent Toolset</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">yel_get_business_profile</span>
                    <span class="tool-chip">yel_get_sector_benchmark</span>
                    <span class="tool-chip">yel_calculate_income_recommendation</span>
                    <span class="tool-chip">yel_estimate_social_benefits</span>
                    <span class="tool-chip">yel_issue_decision</span>
                    <span class="tool-chip">yel_income_policy</span>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 8 • Enterprise Integration",
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
                      <td><span class="tool-chip">yel_get_business_profile</span></td>
                      <td>Static Python dict (businesses.py) — 4 entrepreneur profiles</td>
                      <td><span class="service-tag">Policy Administration System (PAS)</span> <span class="service-tag">CRM</span></td>
                      <td>REST API / SOAP (ISO 20022 pension message standard)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">yel_get_sector_benchmark</span></td>
                      <td>Static Python dict (sector_benchmarks.py) — ETK/Statistics Finland sector medians</td>
                      <td><span class="service-tag">ETK Wage Statistics API</span> <span class="service-tag">Statistics Finland PxWeb API</span></td>
                      <td>REST / JSON (public statistical APIs)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">yel_calculate_income_recommendation</span></td>
                      <td>Deterministic Python logic — hours ratio, cap, beginner discount</td>
                      <td><span class="service-tag">Actuarial Rules Engine</span> <span class="service-tag">Underwriting Platform</span></td>
                      <td>Internal service call / event-driven rules engine</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">yel_estimate_social_benefits</span></td>
                      <td>Illustrative formula Python module (benefit_formulas.py)</td>
                      <td><span class="service-tag">Kela Benefit Calculator API</span> <span class="service-tag">YTK Unemployment API</span></td>
                      <td>REST API (Kela open data / partner APIs)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">yel_issue_decision</span> (flow)</td>
                      <td>Pydantic flow with underwriter approval form</td>
                      <td><span class="service-tag">Document Management System</span> <span class="service-tag">Policy Administration System</span> <span class="service-tag">Postal Dispatch</span></td>
                      <td>Workflow API / BPM (e.g. IBM BPM, Pega)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">yel_income_policy</span> (KB)</td>
                      <td>4 plain-text .txt policy documents (YEL-POL-01 to YEL-POL-04)</td>
                      <td><span class="service-tag">Internal Policy Repository</span> <span class="service-tag">Regulatory Knowledge Base</span></td>
                      <td>Vector search (built-in WXO Knowledge Base)</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Integration Note</div>
                  <div class="callout-text">In production, the business profile and sector benchmark tools would call live APIs from the pension provider's PAS and the ETK statistical data service. The benefit estimation tool could call the Kela partner API for real-time calculations. The mock Python functions are drop-in replacements that can be swapped without changing the agent.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits
          {
            title: "Business &amp; Operational Benefits",
            tag: "Scenario 8 • Value Proposition",
            subtitle: "What the agent makes possible — and where a plain script still works better.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📋</div>
                    <div class="card-title">Consistent Statutory Compliance</div>
                  </div>
                  <div class="card-body">The agent applies the sector benchmark, hours ratio, EUR 4,000 cap, and beginner discount in the correct sequence every time, citing the applicable policy document ID. Cases that should not trigger an assessment (below-threshold revenue) are correctly identified as non-applicable.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Evidence-Based Dispute Handling</div>
                  </div>
                  <div class="card-body">When an entrepreneur disputes a proposal, the agent re-evaluates with adjusted inputs (reported hours, subcontracting costs) and explains why the turnover-based figure was incorrect. This reasoning is captured in the justification passed to the underwriter.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">📊</div>
                    <div class="card-title">Social Security Benefit Visibility</div>
                  </div>
                  <div class="card-body">The agent shows the entrepreneur the direct benefit impact of a YEL income change — daily sickness allowance, parental allowance, unemployment daily rate, and annual pension accrual — alongside the premium change. This context is illustrative; real Kela calculations differ.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Governed Formal Determination</div>
                  </div>
                  <div class="card-body">The write path (issuing a valituskelpoinen päätös) is strictly gated behind the yel_issue_decision approval flow. No legally binding record is created without an underwriter explicitly clicking Confirm, Adjust, or Escalate. The agent cannot bypass this gate.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">A fixed rules engine could apply the statutory formula to straightforward cases (full-time, no dispute). The agent is justified where the input is ambiguous or contested: interpreting an entrepreneur's description of their role, asking clarifying questions about hours, evaluating submitted evidence, and generating a written justification. These steps require natural language understanding, not just arithmetic. The approval flow governance benefit is available to any automated tool — it is not unique to the agent approach.</div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 8 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Transition Cap — IT Consultant</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Conduct a YEL income review for IT consultant ENT-801 (current income EUR 18,000/yr, turnover EUR 95,000/yr). Use your tools to retrieve the profile, sector benchmark, and calculate the recommended income. Do NOT call yel_issue_decision — just report your diagnosis and the proposed new confirmed income with reasoning.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Watch the agent cite YEL-POL-02 for the EUR 4,000 cap. The sector median is EUR 46k — the agent must NOT jump to EUR 46k; it must land at EUR 22k.</span>
                    <button class="script-btn" onclick="showFullScript(1)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Dispute — Bakery Owner</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Artisan bakery owner ENT-802 is contesting a proposed YEL income of EUR 38,000. Retrieve her profile and sector benchmark, then calculate the income recommendation. Do NOT call yel_issue_decision — just report what the correct recommended income should be and why the turnover-based proposal was too high.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The trap: EUR 140k turnover looks large. The agent must separate owner work input (20 h/wk) from revenue and explain why the EUR 38k proposal was too high.</span>
                    <button class="script-btn" onclick="showFullScript(2)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Beginner Discount — Startup Founder</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">New startup founder ENT-803 wants to know their recommended YEL income and whether they qualify for a beginner discount. Retrieve the profile, sector benchmark, and calculate the recommendation. Do NOT call yel_issue_decision — just report the recommended income, whether the beginner discount applies, and what their monthly premium would be.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Watch for the 22% discount applying to the premium only — not reducing the benefit base. The agent should cite YEL-POL-03.</span>
                    <button class="script-btn" onclick="showFullScript(3)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Non-Applicability — Freelancer</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">Side-hustle freelancer ENT-804 has annual revenue of EUR 5,200 and wants to know if YEL insurance is mandatory. Use your tools to check and report whether YEL is required and what options are available.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The restraint case. The agent must confirm non-applicability (below EUR 9,010 threshold) and NOT attempt an income assessment or call the flow. Cite YEL-POL-01.</span>
                    <button class="script-btn" onclick="showFullScript(4)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
