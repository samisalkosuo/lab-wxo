// Scenario: Partial Early Old-Age Pension Advisor. Registers itself on the shared window.SCENARIOS array.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "pension-ove-advisor",
        name: "Partial Early Old-Age Pension Advisor Agent",
        label: "Partial Early Old-Age Pension Advisor",
        description: "Advises members on taking 25% or 50% partial early old-age pension (OVE) in Finland, calculating actuarial reductions, simulating ongoing work accrual, and filing official applications.",
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Partial Early Old-Age Pension Advisor (OVE)",
            tag: "Scenario 7 • Overview",
            subtitle: "Finnish statutory retirement rules (TyEL/JuEL) require cohort-specific age verifications, permanent 0.4%/mo penalty calculations, and continuing employment accrual simulations.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">🏛️</div>
                <div>
                  <div class="callout-title">The Challenge</div>
                  <div class="callout-text">Members approaching retirement want flexible work-pension combinations, but navigating birth cohort minimum ages, permanent actuarial reductions (varhennusvähennys), and tax trade-offs without expert guidance leads to poor financial decisions or rejected applications.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Finnish Statutory Pension Insurance <span style="font-size:12px; color:var(--text-muted);">(TyEL, JuEL, YEL - e.g. Varma, Ilmarinen, Elo, Veritas, Keva)</span></div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Pension Customer Advisory, Actuarial Calculations & Claims Processing</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">Pension Advisory Specialist</span>
                    <span class="fit-pill">Customer Service Representative</span>
                    <span class="fit-pill">Actuarial Case Handler</span>
                    <span class="fit-pill">Pension Operations Lead</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">📊</div>
                    <div class="card-title">Multi-Variable Rules</div>
                  </div>
                  <div class="card-body">Statutory OVE age thresholds shift by birth cohort (1958–1967+). Calculations require factoring 25%/50% draw portions, permanent 0.4%/mo reductions, and life expectancy coefficients (elinaikakerroin).</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">💼</div>
                    <div class="card-title">Working Beside Pension</div>
                  </div>
                  <div class="card-body">Unlike full retirement, OVE has no salary limits. Work continues to accrue new pension at 1.5%/year. Members need dynamic simulations comparing net income and future final pensions.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🛡️</div>
                    <div class="card-title">Governance & Irreversibility</div>
                  </div>
                  <div class="card-body">Once an OVE election is granted and paid, it cannot be revoked. Benefit conflicts (active disability pension) must be caught, and formal applications must pass human confirmation.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🎯</div>
                  <div class="card-title">Scenario Objectives</div>
                </div>
                <div class="card-body">
                  <ul>
                    <li><strong>Advise & Simulate:</strong> Handle natural language member inquiries, verify cohort eligibility, compute 25% vs 50% draw amounts, and project continuing work accruals using 4 read-only tools and a policy KB.</li>
                    <li><strong>Govern:</strong> Route formal pension filings through an interactive approval flow (<code>ove_submit_application</code>) where the internal registration tool is never attached to the agent.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 7 • Agent Paradigm",
            subtitle: "Unstructured member inquiries with messy timelines cannot be resolved by rigid decision trees without frustrating customers.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Traditional Approach</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Members call call centers or submit email forms with partial information; advisors spend 15–30 minutes manually looking up Arek registers, birth cohort tables, and calculating scenarios.</li>
                      <li>Members struggle with self-service calculators because they do not understand the permanence of the 0.4%/mo penalty or the ongoing 1.5% TyEL work accrual.</li>
                      <li>High risk of applications being submitted by ineligible members (under cohort age or on active disability pension), causing administrative rework and customer frustration.</li>
                    </ul>
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">🤖</div>
                    <div class="card-title">Agentic Approach</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li><strong>Natural language discovery:</strong> The agent engages in conversation, disambiguates member goals, and retrieves member profiles and accrual baselines on demand.</li>
                      <li><strong>Dynamic scenario modeling:</strong> Automatically calculates exact actuarial penalties, projects combined income with planned future salaries, and compares 25% vs 50% options side-by-side.</li>
                      <li><strong>Policy grounding & governance:</strong> Grounded in statutory policy docs (<code>OVE-POL-01</code> to <code>04</code>), automatically halts on benefit conflicts, and gates official filings behind human approval.</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-purple">⚖️</div>
                  <div class="card-title">Agent-Washing Test: Why a Pure Flowchart is Not Enough</div>
                </div>
                <div class="card-body">
                  <div class="grid-3">
                    <div>
                      <strong>Open-Ended Inquiry</strong><br>
                      <span style="font-size:13px; color:var(--text-muted);">Inquiries arrive with vague plans ("I want to cut hours and start OVE next spring"). The agent must ask clarifying questions and extract parameters iteratively.</span>
                    </div>
                    <div>
                      <strong>Multi-Scenario Comparison</strong><br>
                      <span style="font-size:13px; color:var(--text-muted);">Members want to see trade-offs: 25% vs 50% draw, working full-time vs 80% vs 60%, and the effect on their final pension at age 65.</span>
                    </div>
                    <div>
                      <strong>Strict Action Gating</strong><br>
                      <span style="font-size:13px; color:var(--text-muted);">The calculation and advice are flexible, but the formal submission is deterministic and locked behind a human-in-the-loop approval flow.</span>
                    </div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 7 • Architecture",
            subtitle: "ReAct reasoning loop combining 4 read-only diagnostic tools, a statutory policy knowledge base, and a governed submission flow.",
            render: () => `
              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-blue">🔄</div>
                  <div class="card-title">Agent Execution Pattern</div>
                </div>
                <div class="card-body">
                  <div class="grid-4" style="text-align:center;">
                    <div style="background:var(--bg-secondary); padding:12px; border-radius:8px; border:1px solid var(--border);">
                      <div style="font-size:20px; margin-bottom:4px;">1️⃣ Disambiguate</div>
                      <div style="font-size:12px; color:var(--text-muted);">Extracts member ID, desired draw (25/50%), and salary plan</div>
                    </div>
                    <div style="background:var(--bg-secondary); padding:12px; border-radius:8px; border:1px solid var(--border);">
                      <div style="font-size:20px; margin-bottom:4px;">2️⃣ Retrieve & Check</div>
                      <div style="font-size:12px; color:var(--text-muted);">Queries accrual baseline & checks cohort age & benefit conflicts</div>
                    </div>
                    <div style="background:var(--bg-secondary); padding:12px; border-radius:8px; border:1px solid var(--border);">
                      <div style="font-size:20px; margin-bottom:4px;">3️⃣ Compute & Advise</div>
                      <div style="font-size:12px; color:var(--text-muted);">Applies 0.4%/mo penalty, life coeff & 1.5% work accrual with policy citation</div>
                    </div>
                    <div style="background:var(--bg-secondary); padding:12px; border-radius:8px; border:1px solid var(--border);">
                      <div style="font-size:20px; margin-bottom:4px;">4️⃣ Governed Filing</div>
                      <div style="font-size:12px; color:var(--text-muted);">Flow renders confirmation form; Approve registers application</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">🛠️</div>
                    <div class="card-title">Connected Tools & Flow</div>
                  </div>
                  <div class="card-body">
                    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px;">
                      <span class="badge badge-blue">ove_get_member_profile</span>
                      <span class="badge badge-blue">ove_get_accrued_pension</span>
                      <span class="badge badge-blue">ove_calculate_reduction</span>
                      <span class="badge badge-blue">ove_simulate_combined_income</span>
                      <span class="badge badge-purple">ove_submit_application (Flow)</span>
                    </div>
                    <div style="font-size:13px; color:var(--text-muted);">
                      The write tool <code>ove_create_application_record</code> is internal to the flow and never exposed to the agent LLM.
                    </div>
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">📚</div>
                    <div class="card-title">Statutory Policy Knowledge Base</div>
                  </div>
                  <div class="card-body">
                    <div style="margin-bottom:8px;"><strong>pension_ove_policy:</strong></div>
                    <ul style="font-size:13px;">
                      <li><code>OVE-POL-01</code>: Cohort minimum age limits (1958–1967+)</li>
                      <li><code>OVE-POL-02</code>: 25% and 50% draw rules & disability exclusions</li>
                      <li><code>OVE-POL-03</code>: 0.4%/mo penalty & 1.5% annual work accrual</li>
                      <li><code>OVE-POL-04</code>: Life expectancy coefficient & taxation</li>
                    </ul>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 7 • Enterprise Integration",
            subtitle: "How the mock components map to actual Finnish pension IT infrastructure and central registries.",
            render: () => `
              <div class="card">
                <div class="card-body" style="padding:0;">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Lab Mock Component</th>
                        <th>WXO Resource</th>
                        <th>Production Enterprise System</th>
                        <th>Protocol / Interface</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><code>members.py</code></td>
                        <td><code>ove_get_member_profile</code></td>
                        <td><strong>Arek Pension Identity & Policy Registry</strong></td>
                        <td>REST / SOAP XML / JSON API</td>
                      </tr>
                      <tr>
                        <td><code>accruals.py</code></td>
                        <td><code>ove_get_accrued_pension</code></td>
                        <td><strong>Central Earnings Register (ETK Ansiorekisteri)</strong></td>
                        <td>Secure B2B API / ISO 20022</td>
                      </tr>
                      <tr>
                        <td><code>cohort_tables.py</code></td>
                        <td><code>ove_calculate_reduction</code></td>
                        <td><strong>Actuarial Calculation Engine & STM Tables</strong></td>
                        <td>Internal Rule Microservice</td>
                      </tr>
                      <tr>
                        <td><code>pension_ove_policy.yaml</code></td>
                        <td><code>pension_ove_policy</code></td>
                        <td><strong>Statutory Rules Repository & Handbook</strong></td>
                        <td>watsonx Vector Store / milvus</td>
                      </tr>
                      <tr>
                        <td><code>submit_ove_application.py</code></td>
                        <td><code>ove_submit_application</code></td>
                        <td><strong>Core Claims Processing & Electronic Mailbox (Suomi.fi)</strong></td>
                        <td>BPMN / Camunda / IBM BAW Flow</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            `
          },

          // Slide 5: Business and Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 7 • Business Value",
            subtitle: "Scaling personalized pension advisory while maintaining 100% statutory compliance and governance.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">⚡</div>
                    <div class="card-title">Instant Personalized Advisory</div>
                  </div>
                  <div class="card-body">Members receive immediate, accurate simulations of complex pension and salary combinations in natural language, reducing advisory contact center call backlogs.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🎯</div>
                    <div class="card-title">100% Statutory Compliance</div>
                  </div>
                  <div class="card-body">Strict enforcement of birth cohort age limits, statutory penalty formulas, and benefit conflict exclusions prevents invalid claim submissions and administrative rework.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Auditable Human Governance</div>
                  </div>
                  <div class="card-body">AI advises and calculates, but formal benefit registrations require structured human confirmation, providing complete audit trails for regulatory compliance (FIN-FSA / Fiva).</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">💡</div>
                  <div class="card-title">Presenter Takeaway</div>
                </div>
                <div class="card-body">
                  "In statutory insurance, conversational AI cannot be an ungoverned black box. watsonx Orchestrate pairs generative conversation with exact programmatic calculation tools and mandatory human approval gates for high-stakes decisions."
                </div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 7 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Vague Opening & Clarification</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Hi, I am thinking about taking partial pension early while continuing my job. Can you help me?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The agent should ask for the member ID first rather than guessing figures. Watch for a single, focused clarifying question.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Main Path (50% OVE & Continuing Salary)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">I turn 62 next month and want to explore taking 50% partial early old-age pension (OVE) while continuing my job. My member ID is MEM-101 and my current monthly salary is 4200 euros.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Matti Virtanen (MEM-101). Watch the agent apply the 0.4%/mo penalty, life expectancy coefficient, and calculate the continuing 1.5% TyEL work accrual.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Cohort Age Limit Refusal</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">Can I take 25% OVE starting next month? My member ID is MEM-102 and I am a 59-year-old teacher.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Liisa Korhonen (MEM-102). Cohort 1966 requires age 62. The agent cites OVE-POL-01, states the shortfall months, and refuses early filing.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Multi-Scenario Comparison (25% vs 50%)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">I want to compare taking 25% vs 50% OVE. My member ID is MEM-103 and I plan to reduce my work hours to 80% with a salary of 2800 euros per month.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Antti Mäkinen (MEM-103). The agent simulates both 25% and 50% options side-by-side with 80% work hours and explains the trade-offs.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5</span>
                      <span class="prompt-title">Governed Application Filing Flow</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">Please submit my formal application for 50% OVE starting 2026-05-01 for member MEM-101.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Triggers the ove_submit_application approval form in the chat UI. Click 'Approve' to issue the application reference ID.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 6</span>
                      <span class="prompt-title">Benefit Conflict Restraint</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-6', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-6">I want to apply for 50% OVE. My member ID is MEM-104.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Eeva Koskinen (MEM-104). The agent detects active Kuntoutustuki, cites OVE-POL-02, and halts without filing an application.</span>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
