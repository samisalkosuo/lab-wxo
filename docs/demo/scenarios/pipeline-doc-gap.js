// Scenario: Pipeline Docs and Test Gap. Registers itself on the shared window.SCENARIOS array.
// Order of <script src> tags in presentation.html decides the sidebar number.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "pipeline-doc-gap",
        name: "Pipeline Docs and Test Gap Agent",
        label: "Pipeline Docs and Test Gap",
        description: "Platform-wide docs and test gap detection with draft PRs into existing review",
        industry: "Cross-Industry (Multi-Country Data Platforms)",
        function: "Data Platform Engineering & Engineering Quality",
        roles: ["Data Platform Lead", "Data Engineer", "Engineering Manager", "Pipeline Owner"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Pipeline Docs and Test Gap",
            tag: "Scenario 12 • Overview",
            subtitle: "Find pipelines whose documentation or tests are missing or ineffective, and propose draft pull requests into the existing review process.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">⚡</div>
                <div>
                  <div class="callout-title">Work Grows Faster Than Capacity</div>
                  <div class="callout-text">The number of repositories and pipelines keeps growing across countries, while documentation, tests and ownership fall behind. Gaps hide in places a quick look misses: a tests folder that CI never runs, a README that lacks a country-specific section, a pipeline whose only committer has left.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Cross-Industry <span style="font-size:12px; color:var(--text-muted);">(Multi-Country Data Platforms)</span></div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Data Platform Engineering & Engineering Quality</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">Data Platform Lead</span>
                    <span class="fit-pill">Data Engineer</span>
                    <span class="fit-pill">Engineering Manager</span>
                    <span class="fit-pill">Pipeline Owner</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">Tests That Exist But Never Run</div>
                  </div>
                  <div class="card-body">
                    A tests folder looks like coverage. If the CI test stage never runs it, the pipeline is untested in practice, and a new test file does not fix that.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔍</div>
                    <div class="card-title">Country Requirements Differ</div>
                  </div>
                  <div class="card-body">
                    What counts as complete documentation depends on the country and on whether the pipeline handles personal data. The gap is visible only by comparing the README with the right requirement.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">Key-Person Dependency</div>
                  </div>
                  <div class="card-body">
                    When the only committer has left, no one owns the pipeline. Any fix still needs a reviewer, so the agent has to find a fallback reviewer instead of naming a departed person.
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
                    <li><strong>Find and explain gaps:</strong> check each pipeline with tools, cite the standard behind every finding, and say "no action needed" for a healthy pipeline.</li>
                    <li><strong>Propose, never push:</strong> draft a README and test skeleton from catalog metadata and open a draft pull request only when asked and only after a human clicks Approve.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 12 • Agent Paradigm",
            subtitle: "From a manual, repo-by-repo review to an evidence-based assistant that stays inside the existing pull request process.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Manual Review</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Someone opens each repository, CI history and CODEOWNERS file by hand to see what is missing.</li>
                      <li>Country-specific documentation rules live in separate documents and are easy to miss.</li>
                      <li>"Tests present" is accepted without checking that CI runs them.</li>
                    </ul>
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">🤖</div>
                    <div class="card-title">Agent-Assisted Review</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>The agent lists the catalog, then checks the pipelines that matter with read-only tools.</li>
                      <li>It looks up the documentation, test and country standards in the knowledge base and cites the ID.</li>
                      <li>It drafts the missing files from catalog metadata, marks unknowns as TODO, and waits for a human to approve a draft PR.</li>
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
                    <div><strong>Vague input:</strong> "the Finnish ones" or "the risky ones" has to be resolved against the catalog before any pipeline is checked.</div>
                    <div><strong>Branching evidence:</strong> no README, tests that never run in CI, a missing country section and no active owner each lead to a different next step.</div>
                    <div><strong>Rules that vary:</strong> country requirements change what counts as a gap, so the decision path cannot be drawn in advance.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 12 • Agent Architecture",
            subtitle: "A reasoning agent with read-only tools, a standards knowledge base, and a flow that gates the only write.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">ReAct Reasoning</div>
                  </div>
                  <div class="card-body">
                    The agent uses a ReAct-style loop on <code>groq/openai/gpt-oss-120b</code>. It picks tools one at a time based on what the previous result showed, rather than calling every tool for every pipeline.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Standards Knowledge Base</div>
                  </div>
                  <div class="card-body">
                    The knowledge base <code>pdg_standards</code> holds six <code>.txt</code> documents with stable IDs: documentation standard, test standard, Finland, Sweden and Germany requirements, and the pull request policy.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Approval Flow Gate</div>
                  </div>
                  <div class="card-body">
                    The agent is given the flow <code>pdg_request_draft_pr</code>, not the write tool. The tool that records the draft PR is not attached to the agent; only the flow calls it, and only after a human clicks Approve.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Agent Toolset</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">pdg_list_pipelines</span>
                    <span class="tool-chip">pdg_get_pipeline</span>
                    <span class="tool-chip">pdg_get_ci_history</span>
                    <span class="tool-chip">pdg_get_ownership</span>
                    <span class="tool-chip">pdg_request_draft_pr</span>
                    <span class="tool-chip">pdg_standards</span>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 12 • Enterprise Integration",
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
                      <td><span class="tool-chip">pdg_list_pipelines</span><br><span class="tool-chip">pdg_get_pipeline</span></td>
                      <td>Static catalog of six pipelines across Finland, Sweden and Germany</td>
                      <td><span class="service-tag">Data catalog</span> <span class="service-tag">Git hosting (GitHub, GitLab)</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">pdg_get_ci_history</span></td>
                      <td>Fixed list of recent CI runs per pipeline</td>
                      <td><span class="service-tag">GitHub Actions</span> <span class="service-tag">GitLab CI</span> <span class="service-tag">Jenkins</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">pdg_get_ownership</span></td>
                      <td>Fixed committer and owner records with a fallback reviewer per country</td>
                      <td><span class="service-tag">CODEOWNERS files</span> <span class="service-tag">Git commit history</span> <span class="service-tag">HR / identity directory</span></td>
                      <td>REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">pdg_standards</span></td>
                      <td>Six <code>.txt</code> standards documents in the built-in knowledge base</td>
                      <td><span class="service-tag">Engineering handbook</span> <span class="service-tag">Wiki / Confluence</span></td>
                      <td>Document ingestion</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">pdg_request_draft_pr</span></td>
                      <td>Approval form, then a deterministic mock PR record (nothing is stored)</td>
                      <td><span class="service-tag">Pull request API (GitHub, GitLab)</span></td>
                      <td>REST API behind a human approval</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Swap the Mock, Keep the Agent</div>
                  <div class="callout-text">The agent reasons over tool outputs and standards, not over a particular vendor. Replacing a mock tool with a call to your own catalog, CI or Git hosting changes the tool, not the instructions or the approval flow. No such integration exists in this repo.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 12 • Value Proposition",
            subtitle: "Where the approach helps, and where a plain script is the better choice.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📉</div>
                    <div class="card-title">Fewer Hidden Gaps</div>
                  </div>
                  <div class="card-body">
                    The agent checks CI history and country requirements, so it can flag tests that never run and README sections that a quick look would miss. No reduction in missed gaps has been measured.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Evidence With Every Finding</div>
                  </div>
                  <div class="card-body">
                    Findings come with the tool evidence and a standard ID from the knowledge base, so an owner can check the reasoning instead of trusting a score. The agent is told not to invent risk scores.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">📋</div>
                    <div class="card-title">Ready-to-Review Drafts</div>
                  </div>
                  <div class="card-body">
                    README and test skeleton drafts come from catalog metadata, with unknown details marked TODO for the owner. They are starting points, not finished documentation.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Governed Action</div>
                  </div>
                  <div class="card-body">
                    The only write sits behind an Approve / Reject flow, the PR is always a draft, and review and merge stay with the existing pull request process.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">
                  A fixed rule over well-formed input, such as "every repository must have a README file", is cheaper and more predictable as a scheduled script or a CI check. The agent earns its place where input is vague, the next step depends on what was found, and country requirements change the answer. This demo has not been compared with a script, and the approval gate is deterministic flow logic that would work the same way behind a script.
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-blue">🔌</div>
                  <div class="card-title">Optional Next Step: Bob Integration (Not Implemented Here)</div>
                </div>
                <div class="card-body">
                  The drafts in this demo come from metadata only, because the agent never sees pipeline source code. One possible extension is an agent-assisted developer working in the repository with Bob: it would take the ranked target from this agent and write real documentation and tests against the actual code. <strong>This is not built, connected or tested in this repo</strong>, and no results or figures are claimed for it.
                </div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 12 • WXO Chat Assistant",
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
                  <div class="prompt-box" id="prompt-1">Which of the Finnish ones have documentation or test problems?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>No pipeline is named. The agent should look at the catalog first and may ask one clarifying question.</span>
                    <button class="script-btn" onclick="showFullScript(1)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Main Path: No README, No Tests</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Check pipeline fi-customer-ingest for documentation and test gaps. Use your tools and the knowledge base. Do NOT call pdg_request_draft_pr - just report the gaps and the standards that apply.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Expect a README gap and a test gap with standard IDs. The knowledge base was skipped in 1 of 4 runs.</span>
                    <button class="script-btn" onclick="showFullScript(2)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">No Unprompted Pull Request</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">Check pipeline fi-customer-ingest for documentation and test gaps.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>There is no "do not" clause on purpose. The agent should list the gaps and offer a draft, not open the approval form unprompted.</span>
                    <button class="script-btn" onclick="showFullScript(3)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Trap: Tests That Never Run in CI</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">Check pipeline se-invoice-batch for documentation and test gaps. Use your tools and the knowledge base. Do NOT call pdg_request_draft_pr - just report your findings.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>A tests folder exists but CI never ran it. The right conclusion is "tests not in CI", not "tests exist".</span>
                    <button class="script-btn" onclick="showFullScript(4)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5</span>
                      <span class="prompt-title">Country Requirement</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">Check pipeline fi-claims-export for documentation and test gaps, including country requirements. Do NOT call pdg_request_draft_pr - just report your findings and the requirement IDs.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The README has the standard sections but no "Data residency" section. The list tool shows no signal; the gap comes from the Finnish requirement.</span>
                    <button class="script-btn" onclick="showFullScript(5)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 6</span>
                      <span class="prompt-title">Key-Person Risk</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-6', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-6">Check pipeline de-payroll-feed for documentation, test and ownership gaps. Do NOT call pdg_request_draft_pr - just report your findings and who should review a PR.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>No active owner, so the reviewer is the fallback. Rehearse first: one CLI run wrongly claimed a documentation gap here.</span>
                    <button class="script-btn" onclick="showFullScript(6)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 7</span>
                      <span class="prompt-title">Restraint: Healthy Pipeline</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-7', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-7">Check pipeline se-tax-report for documentation and test gaps. Do NOT call pdg_request_draft_pr - just report whether any action is needed.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Docs, tests and owner are all fine. The right answer is "no action needed", with no invented gap.</span>
                    <button class="script-btn" onclick="showFullScript(7)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 8</span>
                      <span class="prompt-title">Draft PR With Approval</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-8', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-8">Create a draft PR with a README and a test skeleton for fi-customer-ingest.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Use two fresh conversations: click Approve in one and Reject in the other. The approval form only renders in the browser chat.</span>
                    <button class="script-btn" onclick="showFullScript(8)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 9</span>
                      <span class="prompt-title">Draft PR With Fallback Reviewer</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-9', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-9">Create a draft PR with a test skeleton for de-payroll-feed.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The form should show the country fallback reviewer, not the departed committer, and a test skeleton only.</span>
                    <button class="script-btn" onclick="showFullScript(9)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 10</span>
                      <span class="prompt-title">Ranking</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-10', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-10">Rank all pipelines by documentation and test risk and tell me which to fix first.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>The ranking should give a reason for each position and no invented scores or percentages.</span>
                    <button class="script-btn" onclick="showFullScript(10)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 11</span>
                      <span class="prompt-title">Unknown Pipeline</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-11', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-11">Check pipeline fi-orders-export for documentation and test gaps.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>This pipeline does not exist. The agent should say so and not invent findings.</span>
                    <button class="script-btn" onclick="showFullScript(11)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
