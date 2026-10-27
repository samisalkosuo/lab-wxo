// Scenario: Disability Pension & Vocational Rehabilitation Triage. Registers itself on the shared window.SCENARIOS array.
// Sidebar position: 9 (9th <script src> tag in presentation.html).
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "pension-disability-triage",
        name: "Disability Pension & Vocational Rehabilitation Triage Agent",
        label: "Disability Pension & Rehab Triage",
        description: "Statutory disability claims triage with rehabilitation-first enforcement and medical board referral flow",
        industry: "Finnish Statutory Pension Insurance / Social Security",
        function: "Disability Claims Management & Occupational Rehabilitation",
        roles: ["Disability Claims Handler", "Rehabilitation Specialist", "Medical Case Coordinator", "Claims Team Lead"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Disability Pension & Vocational Rehabilitation Triage",
            tag: "Scenario 9 • Overview",
            subtitle: "AI-assisted triage for Finnish statutory disability pension claims — enforcing statutory rehabilitation priority, verifying qualifying conditions, and governing medical board referrals.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">⚕️</div>
                <div>
                  <div class="callout-title">Disability pension dossiers are complex, multi-source, and high-stakes</div>
                  <div class="callout-text">Claims arrive with unstructured B-statements, fragmented insurance records, employer duty-to-accommodate reports, and statutory exception clauses. Missing a rehabilitation pathway or a qualifying-months waiver causes costly reversals and regulatory risk.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Finnish Statutory Pension Insurance / Social Security (Työeläkeyhtiöt &amp; Keva)</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Disability Claims Management &amp; Occupational Rehabilitation</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">Disability Claims Handler</span>
                    <span class="fit-pill">Rehabilitation Specialist</span>
                    <span class="fit-pill">Medical Case Coordinator</span>
                    <span class="fit-pill">Claims Team Lead</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">Statutory Priority Errors</div>
                  </div>
                  <div class="card-body">Granting a pension to a claimant with significant recovery potential and unexhausted rehabilitation options violates the "Rehabilitation before Pension" principle (TyEL § 25) and exposes the institution to reversal decisions.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔍</div>
                    <div class="card-title">Qualifying Condition Complexity</div>
                  </div>
                  <div class="card-body">The 36/60-month insurance condition, tuleva aika eligibility, occupational accident waivers, and bilateral treaty aggregation rules must all be evaluated before any medical assessment begins. A missed waiver means a wrongful refusal.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">Governance Risk</div>
                  </div>
                  <div class="card-body">Formal referral to the Chief Medical Officer (Asiantuntijalääkäri) is legally mandatory for every pension-eligible case. Submitting a referral without claims handler sign-off bypasses the institution's governance controls.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🎯</div>
                  <div class="card-title">Scenario Objectives</div>
                </div>
                <div class="card-body">
                  <ul>
                    <li><strong>Statutory compliance:</strong> Enforce the rehabilitation-first rule, qualifying months gate, and occupational accident waiver automatically — with policy citation on every decision.</li>
                    <li><strong>Governed referral:</strong> Route every official Medical Board or Vocational Rehab referral through a human-in-the-loop approval flow; nothing is recorded without claims handler sign-off.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 9 • Agent Paradigm",
            subtitle: "Why a fixed workflow cannot replace a triage agent for disability pension claims.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Traditional Manual Triage</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Handler manually checks qualifying months, medical B-statement, and employer report across separate systems — order varies by handler experience.</li>
                      <li>Rehabilitation pathway assessment is skipped or incomplete when the medical evidence looks strong; statutory priority errors go undetected until appeal.</li>
                      <li>Occupational accident waivers are missed when dossiers arrive incomplete or the accident date is close to the contribution boundary.</li>
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
                      <li>Agent follows a fixed statutory priority order: qualifying months → medical evidence → rehabilitation assessment → disposition — every time, regardless of how the request is phrased.</li>
                      <li>Each step cites the relevant policy document ID (DIS-POL-01 through DIS-POL-04), giving the handler an auditable reasoning trail.</li>
                      <li>Referral to the Medical Board or Vocational Rehab Unit only proceeds after the claims handler approves the triage summary — no write action is possible without that sign-off.</li>
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
                    <div><strong>Dynamic branching:</strong> The next step depends on what the previous tool found — a waiver flag, a recovery potential score, or a contribution gap. A fixed flowchart cannot represent all paths.</div>
                    <div><strong>Messy inputs:</strong> Claim requests arrive in free text ("check this member", "back surgery case"). The agent extracts the claimant ID, calls the right tools, and asks for clarification if needed.</div>
                    <div><strong>Exception handling:</strong> Occupational accident waivers and bilateral treaty aggregation are triggered by evidence in the dossier — not by form fields. The agent must reason about presence or absence of evidence.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 9 • Agent Architecture",
            subtitle: "ReAct reasoning loop, policy knowledge base, and a governed write gate.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">ReAct Reasoning Loop</div>
                  </div>
                  <div class="card-body">The agent uses a Reason-Act cycle: it reads the claim request, decides which tool to call next based on the previous result, and iterates until a disposition is reached. The triage protocol is encoded in the agent instructions — the LLM decides the sequence, but the tools constrain what it can discover.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Policy Knowledge Base</div>
                  </div>
                  <div class="card-body">Four plain-text policy documents (DIS-POL-01 through DIS-POL-04) are indexed in a built-in vector KB (<span class="tool-chip">pension_disability_policy</span>). The agent retrieves the relevant section and cites the document ID in its reasoning — without the IDs being hard-coded in the instructions.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Governed Write Gate</div>
                  </div>
                  <div class="card-body">The write tool <code>pdis_dispatch_referral</code> is not on the agent's tool list. It is only callable through the <span class="tool-chip">pdis_refer_claim</span> approval flow — after the claims handler reviews the triage summary and clicks Approve. The platform enforces this; the agent cannot bypass it.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Agent Toolset</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">pdis_get_claim_dossier</span>
                    <span class="tool-chip">pdis_verify_qualifying_months</span>
                    <span class="tool-chip">pdis_get_medical_summary</span>
                    <span class="tool-chip">pdis_assess_rehab_eligibility</span>
                    <span class="tool-chip">pdis_refer_claim</span>
                    <span class="tool-chip">pension_disability_policy</span>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 9 • Enterprise Integration",
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
                      <td><span class="tool-chip">pdis_get_claim_dossier</span></td>
                      <td>Static Python dict (claimants.py)</td>
                      <td><span class="service-tag">Arek / Pension Core System</span></td>
                      <td>REST API or IBM MQ message</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">pdis_verify_qualifying_months</span></td>
                      <td>Static Python dict (insurance_periods.py)</td>
                      <td><span class="service-tag">Arek Earnings Register</span> <span class="service-tag">ETK Pension Data</span></td>
                      <td>REST API / ETK interoperability interface</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">pdis_get_medical_summary</span> <span class="tool-chip">pdis_assess_rehab_eligibility</span></td>
                      <td>Static Python dict (medical_dossiers.py)</td>
                      <td><span class="service-tag">Kanta Patient Data Repository</span> <span class="service-tag">Electronic B-statement system</span></td>
                      <td>HL7 FHIR R4 / Kanta API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">pension_disability_policy</span> (KB)</td>
                      <td>4 plain-text .txt policy files, vector-indexed</td>
                      <td><span class="service-tag">Internal policy document repository</span> <span class="service-tag">ETK statutory guidelines</span></td>
                      <td>Document ingestion pipeline</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">pdis_refer_claim</span> (flow) + pdis_dispatch_referral</td>
                      <td>Mock referral ID generator (deterministic hash)</td>
                      <td><span class="service-tag">Case Management System (Arek)</span> <span class="service-tag">CMO Referral Queue</span></td>
                      <td>REST API / workflow integration</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Each tool is a thin adapter</div>
                  <div class="callout-text">In production, each mock Python dict is replaced by a REST call to the relevant system. The agent instructions, triage logic, KB, and flow governance stay unchanged — only the data source changes.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 9 • Value Proposition",
            subtitle: "Compliance, quality, and governance improvements — illustrative arguments, not measured results from this demo.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📋</div>
                    <div class="card-title">Consistent Statutory Compliance</div>
                  </div>
                  <div class="card-body">Every triage follows the same priority order — qualifying months before medical evidence, rehabilitation check before pension evaluation — regardless of handler experience. Policy citations (DIS-POL-01 through DIS-POL-04) are attached to every disposition recommendation.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Exception Detection</div>
                  </div>
                  <div class="card-body">Occupational accident waivers and bilateral treaty aggregation are flagged automatically when the dossier evidence supports them — reducing the risk of wrongful refusals that trigger costly appeal and reversal processes.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">🛡️</div>
                    <div class="card-title">Governance by Design</div>
                  </div>
                  <div class="card-body">No referral can be submitted without claims handler approval. The write tool is architecturally unreachable by the agent — the platform enforces least-privilege. The approval form records the triage summary and policy reference for audit purposes.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Auditable Reasoning Trail</div>
                  </div>
                  <div class="card-body">Each agent response cites a specific policy document ID and lists the tool results it used to reach the disposition. Claims handlers can verify the reasoning step-by-step, supporting quality review and regulatory audit.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">A deterministic rules engine handles fully structured, machine-readable inputs more reliably than a ReAct agent. The agent adds value when inputs are unstructured (free-text claim requests, partial dossiers) and when the decision path branches on what evidence is actually present. The scenario has not been run on a live WXO instance; tool reliability is verified locally, agent reasoning reliability has not been measured.</div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 9 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Full Disability Evaluation — CLM-701</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Evaluate the disability pension claim for member CLM-701. Use your tools to check the qualifying months, review the medical evidence, and assess rehabilitation eligibility. Do NOT call pdis_refer_claim — just report your triage disposition and which referral type you would recommend.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Main path: qualifying condition met, rehab exhausted, work capacity 30%. Expected disposition: pension eligible → medical board referral (DIS-POL-01).</span>
                    <button class="script-btn" onclick="showFullScript(1)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Rehabilitation Before Pension — CLM-702</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Member CLM-702 has applied for a disability pension following back surgery. Use your tools to evaluate the claim. Do NOT call pdis_refer_claim — just report whether a pension can be granted at this stage or whether another pathway applies, and cite the relevant policy.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Trap: work capacity 55%, recovery potential significant, no workplace trial. Agent must recommend vocational rehabilitation, not pension. Cite DIS-POL-02.</span>
                    <button class="script-btn" onclick="showFullScript(2)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Occupational Accident Waiver — CLM-703</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">Young worker CLM-703 is claiming incapacity following a factory accident and has only 14 months of work history. Use your tools to evaluate eligibility. Do NOT call pdis_refer_claim — just explain whether and why the standard qualifying condition applies and what disposition you recommend.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Red herring: 14 months looks like a refusal. Waiver applies (tyotapaturma, TyEL § 12). Agent must confirm accident documentation before accepting. Cite DIS-POL-04.</span>
                    <button class="script-btn" onclick="showFullScript(3)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Governed Referral Flow — CLM-701</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">Evaluate the disability pension claim for member CLM-701 and, once you have completed the triage, use the referral flow to submit a referral to the Medical Board.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Governed action: flow form appears for claims handler review. Approve submits referral (REF-XXXXX); Reject returns rejection message. Flow not verified in a browser yet.</span>
                    <button class="script-btn" onclick="showFullScript(4)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5</span>
                      <span class="prompt-title">Refusal / Red Herring — CLM-704</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">Member CLM-704 is requesting a disability pension after several years of uninsured residency abroad. Use your tools to check the qualifying condition. Do NOT call pdis_refer_claim — just report the eligibility outcome and what the claimant should be advised.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Restraint: 35% work capacity passes the medical threshold but 8/60 insured months fails the qualifying condition. No waiver. Agent must stop and refer to Kela (DIS-POL-04).</span>
                    <button class="script-btn" onclick="showFullScript(5)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
