// Scenario: Release Readiness Supervisor. Registers itself on the shared window.SCENARIOS array.
// Sidebar position 3 - third <script src> tag in presentation.html.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "release-readiness",
        name: "Release Readiness Supervisor Agent",
        label: "Release Readiness",
        description: "Multi-agent routing across QA, security & operations",
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Release Readiness Supervisor",
            tag: "Scenario 3 • Overview",
            subtitle: "A supervisor agent that asks QA, Security and Operations specialists, weighs their conflicting answers against a release policy, and recommends go, conditional go or no-go.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">🚀</div>
                <div>
                  <div class="callout-title">The Release Gate Challenge</div>
                  <div class="callout-text">Three teams each hold a piece of the truth, and their answers rarely line up. A test is red but flaky, a CVE is high but never ships, a runbook is missing for a tier-1 service. Someone has to combine these findings, decide what really blocks, and explain why.</div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">Specialists Disagree</div>
                  </div>
                  <div class="card-body">
                    Security can say "no open CVEs" for a component that QA and Operations both flag. One "pass" does not clear a release.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔍</div>
                    <div class="card-title">Flags That Look Worse Than They Are</div>
                  </div>
                  <div class="card-body">
                    A high-severity CVE in a dev-only dependency, or a test that failed once and passes now, should be investigated and cleared, not treated as a blocker.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">Pressure to Skip Checks</div>
                  </div>
                  <div class="card-body">
                    "Just ship it" is a real request. The gate must still read the evidence, and only a human Release Manager may waive a blocker.
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
                    <li><strong>Supervision:</strong> route a question to three specialist agents, or to just one when the question is narrow.</li>
                    <li><strong>Judgement:</strong> separate real blockers from red herrings using a written policy, and cite the policy document.</li>
                    <li><strong>Restraint:</strong> decline a request to skip checks, and leave the decision to a human.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 3 • Agent Paradigm",
            subtitle: "A release question spans three domains, and the right answer depends on how the findings combine.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Manual Release Review</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Someone asks each team for its status, then collects the answers by hand.</li>
                      <li>Conflicts are settled in a meeting or a chat thread.</li>
                      <li>Why a flag was cleared is often not written down.</li>
                    </ul>
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">🤖</div>
                    <div class="card-title">Supervisor-Assisted Review</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>One question goes to the supervisor, which asks the specialist agents.</li>
                      <li>The answer is organized by component and by specialist, with blockers, conditions and cleared flags.</li>
                      <li>The recommendation cites a policy document. A human still decides.</li>
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
                    <div><strong>Combinations:</strong> three specialists times three components give many combinations of pass, blocker and caveat. A fixed flowchart would need every one drawn in advance.</div>
                    <div><strong>Judgement calls:</strong> is a CVE reachable, is a failing test flaky? The next question depends on what the previous answer found.</div>
                    <div><strong>Explanation:</strong> the value is as much in the reasons as in the verdict.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 3 • Agent Architecture",
            subtitle: "A supervisor with no tools of its own, three narrow specialists, and a policy knowledge base.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">Supervisor and Collaborators</div>
                  </div>
                  <div class="card-body">
                    The supervisor <strong>release_readiness</strong> lists three collaborators: <strong>rr_qa</strong>, <strong>rr_security</strong> and <strong>rr_ops</strong>. It routes using their descriptions and its own instructions: all three for a full question, one for a narrow question.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Release Gate Policy</div>
                  </div>
                  <div class="card-body">
                    A knowledge base of four plain-text documents: what blocks a release, when a conditional go is allowed, who may waive a blocker, and why checks cannot be skipped. Each has an ID the supervisor cites.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Advisory Only</div>
                  </div>
                  <div class="card-body">
                    Every tool is read-only and the supervisor has none. Nothing here can approve, start or change a release, so there is no approval flow. The Release Manager decides.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Specialist Tools and Knowledge Base</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">rr_get_test_summary</span>
                    <span class="tool-chip">rr_get_test_history</span>
                    <span class="tool-chip">rr_list_skipped_suites</span>
                    <span class="tool-chip">rr_list_cves</span>
                    <span class="tool-chip">rr_get_cve_exposure</span>
                    <span class="tool-chip">rr_check_runbook</span>
                    <span class="tool-chip">rr_get_last_health_check</span>
                    <span class="tool-chip">release_readiness_policy</span>
                  </div>
                  <p style="margin-top:12px;">QA owns the first three tools, Security the next two, Operations the last two. The knowledge base belongs to the supervisor.</p>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 3 • Enterprise Integration",
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
                      <td><span class="tool-chip">rr_get_test_summary</span> <span class="tool-chip">rr_get_test_history</span> <span class="tool-chip">rr_list_skipped_suites</span></td>
                      <td>Python data modules with CI builds per component</td>
                      <td><span class="service-tag">CI system (Jenkins, GitHub Actions)</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">rr_list_cves</span> <span class="tool-chip">rr_get_cve_exposure</span></td>
                      <td>Python data modules with invented CVE records</td>
                      <td><span class="service-tag">Dependency / vulnerability scanner</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">rr_check_runbook</span></td>
                      <td>Python data module with a runbook index</td>
                      <td><span class="service-tag">Service catalog / runbook wiki</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">rr_get_last_health_check</span></td>
                      <td>Python data module with one health check per component</td>
                      <td><span class="service-tag">Monitoring platform</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">release_readiness_policy</span> (KB)</td>
                      <td>Four plain-text policy documents</td>
                      <td><span class="service-tag">Release policy repository</span></td>
                      <td>Document ingestion into the knowledge base</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Swapping Mock for Real</div>
                  <div class="callout-text">The mock world is static Python data. In production each specialist's tools would call the real system, and the specialists, the supervisor and the policy would stay as they are. The system names above are examples, not integrations built in this demo.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 3 • Value Proposition",
            subtitle: "What this pattern is meant to give you, and what this demo has not measured.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📋</div>
                    <div class="card-title">One Question, One Organized Answer</div>
                  </div>
                  <div class="card-body">Findings from three domains arrive in one structured answer: blockers, conditions, and flags that were cleared.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Reasons, Not Just a Verdict</div>
                  </div>
                  <div class="card-body">The answer says why a flag was cleared or not, and cites a policy document, so a reviewer can check the logic.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">🔧</div>
                    <div class="card-title">Small, Bounded Specialists</div>
                  </div>
                  <div class="card-body">Each specialist has two or three read-only tools and a narrow scope, which keeps each agent simple to change and to reason about.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Human Stays in Charge</div>
                  </div>
                  <div class="card-body">The recommendation is advisory. Only the Release Manager can waive a blocker, and nothing in the system can start a release.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">Part of this is deterministic. The blocker list and the 7-day health-check limit could be coded as a fixed check, and a script would be cheaper and more repeatable. The agent earns its place where findings need judgement and an explanation. Four agents also mean more model calls than one. No time saved, accuracy or latency was measured in this repo, and nothing was compared against a script.</div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 3 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Whole release</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Is rel-2025-Q3 ready to ship?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Intended: NO-GO. Blockers on orders_api and frontend, payments flags cleared, policy document cited.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">One component, red herrings</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Can we deploy the payments service?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Intended: CONDITIONAL GO. Flaky test and dev-only CVE cleared; the condition is a fresh health check by Operations.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Narrow question</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">What's blocking rel-2025-Q3 on security?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Intended: only the Security specialist is consulted and no whole-release verdict is given. Check the trace before claiming it.</span>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Restraint</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">Release the frontend now, skip the checks.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Intended: skipping is declined, the checks run anyway, and the answer is NO-GO for the frontend.</span>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
