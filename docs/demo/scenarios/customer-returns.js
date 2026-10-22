// Scenario: Customer Returns. Registers itself on the shared window.SCENARIOS array.
// Sidebar position 2 — second <script src> tag in presentation.html.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "customer-returns",
        name: "Customer Returns Agent",
        label: "Customer Returns",
        description: "Messy input, return policy KB & governed refund flow",
        industry: "Retail, E-Commerce & Consumer Goods",
        function: "Customer Service & Post-Purchase Operations",
        roles: ["Customer Support Agent", "Support Lead / Supervisor", "E-Commerce Operations Specialist", "Store / CX Manager"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Customer Returns & Refunds",
            tag: "Scenario 2 • Overview",
            subtitle: "Conversational returns handling: vague customer input, policy-grounded eligibility, and a governed refund flow.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">🛒</div>
                <div>
                  <div class="callout-title">The Returns Handling Challenge</div>
                  <div class="callout-text">Customers rarely provide a clean order ID, reason, and product name. They say "I want to return something" and expect a resolution. Policy eligibility depends on age, channel, warranty, and reason — all of which must be looked up, not assumed.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Retail, E-Commerce & Consumer Goods</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Customer Service & Post-Purchase Operations</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">Customer Support Agent</span>
                    <span class="fit-pill">Support Lead / Supervisor</span>
                    <span class="fit-pill">E-Commerce Operations Specialist</span>
                    <span class="fit-pill">Store / CX Manager</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">Vague & Incomplete Requests</div>
                  </div>
                  <div class="card-body">
                    Customers omit order IDs, reasons, and product details. Gift recipients have no receipt at all. A fixed form cannot handle this variability.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔍</div>
                    <div class="card-title">Multiple Overlapping Policies</div>
                  </div>
                  <div class="card-body">
                    Warranty claims, 30-day no-reason windows, and gift-return rules overlap. The right policy depends on what the order lookup reveals, not on what the customer says.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">Refund Governance Risk</div>
                  </div>
                  <div class="card-body">
                    Issuing a refund or replacement without eligibility verification and human sign-off is a financial and compliance risk. The decision must not rest on an LLM alone.
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
                    <li><strong>Agent / flow split:</strong> the agent handles vague input and policy lookup; a Decisions-node flow enforces the eligibility rule and requires human approval before any refund is issued.</li>
                    <li><strong>Knowledge-base grounding:</strong> eligibility decisions cite a specific policy document (RP-WARRANTY-01, RP-STANDARD-01, RP-GIFT-01) retrieved at query time.</li>
                    <li><strong>Least privilege:</strong> the write tool (<code>returns_issue_refund</code>) is never attached to the agent — only the flow calls it, only after Approve.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 2 • Agent Paradigm",
            subtitle: "From rigid return forms to a conversational agent that handles messy input and routes decisions correctly.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Traditional Approach</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Customer fills a structured return form — requires order ID, product SKU, reason code.</li>
                      <li>Form validation fails on gift recipients with no order ID; agent or rep must handle exception manually.</li>
                      <li>Eligibility logic is hard-coded per form version; policy changes require a deployment.</li>
                      <li>Human reviews every request regardless of eligibility — a deterministic rule applied manually.</li>
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
                      <li>Customer describes the situation in natural language; the agent asks only for what it cannot look up.</li>
                      <li>Gift recipients can provide a serial number; the agent resolves the linked order automatically.</li>
                      <li>Policy documents live in a knowledge base; updates do not require a code change.</li>
                      <li>The flow's Decisions node checks eligibility deterministically; humans review only eligible cases.</li>
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
                    <div><strong>Vague input:</strong> the customer's next statement changes what the agent looks up next — order lookup, then warranty check, then KB retrieval. A fixed script cannot branch this way.</div>
                    <div><strong>Unknown policy path:</strong> which of the four policies applies depends on what the tools return, not on what the customer said upfront.</div>
                    <div><strong>Deterministic gate:</strong> the refund decision is not in the LLM — it is in a Decisions node. The agent proposes; the flow decides; the human approves.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 2 • Agent Architecture",
            subtitle: "Tools, a policy knowledge base, and a governed flow — each component doing only what it does best.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">Read-Only Investigation</div>
                  </div>
                  <div class="card-body">The agent calls read-only tools to gather facts: order age, warranty coverage (with SKU matching), prior return history, and product lookup by serial number. It never guesses.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Policy Knowledge Base</div>
                  </div>
                  <div class="card-body">Four policy documents (warranty, 30-day window, gift return, escalation) are stored in the <code>customer_returns_policy</code> KB as <code>.txt</code> files. The agent retrieves the matching document and cites its ID.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Decisions Node + Approval Gate</div>
                  </div>
                  <div class="card-body">The <code>returns_process_return</code> flow checks eligibility with a Decisions node before showing the approval form. Ineligible cases return immediately — no form, no human interruption. Eligible cases require human Approve or Reject.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Tools Attached to the Agent</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">returns_lookup_order</span>
                    <span class="tool-chip">returns_check_warranty</span>
                    <span class="tool-chip">returns_get_return_history</span>
                    <span class="tool-chip">returns_lookup_by_serial</span>
                    <span class="tool-chip">returns_list_orders</span>
                    <span class="tool-chip">returns_process_return</span>
                  </div>
                  <p style="margin-top:8px; font-size:0.85em; color:#666;">
                    <code>returns_issue_refund</code> is <strong>not</strong> in this list.
                    It is a write tool called only by the flow after human approval.
                  </p>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 2 • Enterprise Integration",
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
                      <td><span class="tool-chip">returns_lookup_order</span></td>
                      <td>Static Python dict of 5 orders</td>
                      <td><span class="service-tag">OMS / ERP</span></td>
                      <td>REST API / SOAP</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">returns_check_warranty</span></td>
                      <td>Static Python dict of 4 warranty records</td>
                      <td><span class="service-tag">Warranty Management System</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">returns_get_return_history</span></td>
                      <td>Static Python dict (empty — clean demo state)</td>
                      <td><span class="service-tag">Returns Management System</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">returns_lookup_by_serial</span></td>
                      <td>Static serial-number registry</td>
                      <td><span class="service-tag">Product Registry / PIM</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">returns_process_return</span> (flow)</td>
                      <td>WXO approval flow with Decisions node</td>
                      <td><span class="service-tag">Approval Workflow / ERP Write</span></td>
                      <td>WXO Flow</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">customer_returns_policy</span> (KB)</td>
                      <td>4 policy .txt documents</td>
                      <td><span class="service-tag">Policy Repository / Confluence</span></td>
                      <td>WXO Built-in KB</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Same agent, real systems</div>
                  <div class="callout-text">Each mock tool is a Python function returning static data. In production, replace the function body with an API call. The agent YAML, KB, and flow stay unchanged.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 2 • Value Proposition",
            subtitle: "What changes when a conversational agent handles returns — and what does not.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📉</div>
                    <div class="card-title">Handles Incomplete Input</div>
                  </div>
                  <div class="card-body">The agent works from a single vague sentence. It asks only for what it cannot look up. Gift recipients with no order ID are handled via serial-number lookup — no special form required. (Illustrative; not measured against a baseline.)</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Policy-Grounded Decisions</div>
                  </div>
                  <div class="card-body">Eligibility is determined by what the tools return and what the knowledge base says — not by the model's training. Updating a policy means editing a .txt file, not retraining or redeploying the agent.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">📋</div>
                    <div class="card-title">Deterministic Eligibility Gate</div>
                  </div>
                  <div class="card-body">The Decisions node in the flow applies the eligibility rule without LLM involvement. Ineligible cases (e.g. outside 30-day window) are rejected before the approval form is shown. The rule cannot be overridden by a well-phrased prompt.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Governed Write Path</div>
                  </div>
                  <div class="card-body">No refund or replacement is issued without human approval. The write tool is not attached to the agent. The flow validates order ownership before calling it (Rule 7: validate in code, not in a prompt).</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">The eligibility rule and the approval gate are deterministic — a script or a pure flow handles them correctly and without an LLM. The agent adds value on the front end: handling vague input, choosing between four overlapping policies, and asking targeted clarifying questions. If your customer input is always well-formed (order ID + reason code), a flow alone is sufficient. This demo is honest about that split.</div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 2 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Vague Opening</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Hi, I bought something a while ago and I want to return it. Can you help?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The agent should ask for the order ID — not guess eligibility. Watch for a single clarifying question.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Warranty Defect + Red Herring</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">I bought a ProBlend 500 blender last month and it broke after a few uses. My order number is ORD-1001.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Alice has two warranty records. The agent must select SN-BLND-500-A101, not the PRO model warranty. Watch which serial it cites.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Outside 30-Day Window — Denied</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">I bought some headphones about six weeks ago. Order ORD-1002. I just don't like them anymore, I want a refund.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>46 days old — outside the 30-day window. The Decisions node should return ineligible without showing the approval form.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Gift Return by Serial Number</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">I received a kitchen scale as a gift and I'd like to return it. I don't have an order number but the serial number on the box is SN-KTCH-780-C103.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>No order ID — the agent uses serial-number lookup to find ORD-1003. Gift-return policy applies: store credit, not cash.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5 &amp; 6</span>
                      <span class="prompt-title">Approval Flow (Approve / Reject) — same prompt as Scene 2</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">I bought a ProBlend 500 blender last month and it broke after a few uses. My order number is ORD-1001.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Use a fresh conversation for each path. Approve: returns_issue_refund runs and returns a REF-NNNNN reference. Reject: nothing executes.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 6</span>
                      <span class="prompt-title">Out-of-Scope Escalation</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-6', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-6">I was charged twice for my order ORD-1004. I need a refund for the duplicate charge.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Billing dispute — not a product return. The agent should cite RP-ESCALATE-01 and direct to the Billing team. No flow should be triggered.</span>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
