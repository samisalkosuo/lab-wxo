// Scenario: {{NAME}}. Registers itself on the shared window.SCENARIOS array.
// Copy to docs/demo/scenarios/{{ID}}.js (replacing the placeholder file), replace every {{PLACEHOLDER}},
// then make sure presentation.html has <script src="scenarios/{{ID}}.js"></script>.
//
// AUTHOR NOTES (delete every "AUTHOR NOTE" before you finish; `python wxodemo.py validate {{ID}}` fails on leftovers):
// - Mirrors the six Incident Triage slides: Overview, Why & How the Agent is Used, How & Why the Agent Works,
//   Real-Life Backend Services Mapping, Business & Operational Benefits, Live Demo Prompts.
// - {{N}} in each tag is this scenario's position in the sidebar = its position among the <script src>
//   tags in presentation.html (1-based). Slide tags are static text, so they must be updated by hand if the
//   order changes. `wxodemo validate` verifies this.
// - Set status to "live" only when the scenario is deployed and the demo script exists.
// - Numbers and claims: do not state a number (minutes saved, % reduction, seconds) unless it was measured in
//   this repo. Otherwise omit it or write "illustrative". Describe knowledge-base documents by their real file
//   format (the built-in KB uses .txt, not markdown). Do not claim "zero glue code", "always", or "guarantees"
//   unless the repo shows it.
// - Classes available (defined in presentation.html): card, card-header, card-icon (icon-blue|purple|teal|green|
//   amber|red), card-title, card-body, grid-2, grid-3, callout-banner, fit-card, fit-group, fit-label, fit-value,
//   fit-pills, fit-pill, tool-chip, service-tag, table-container, prompt-card, prompt-box, scene-pill, copy-btn,
//   prompt-tip. Do not add new CSS for a scenario.
// - Slide 1 (Overview) includes a dedicated .fit-card directly under .callout-banner with Industry (specific vertical
//   or "Cross-Industry"), Function, and Target Roles pills.
// - Each prompt-box needs a unique id (prompt-1, prompt-2, ...) and its copy button must call copyPrompt('<same id>', this).
// - Prompt text must be identical to the "Prompt (type exactly)" blocks in docs/demo/{{ID}}-demo.md.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "{{ID}}",
        name: "{{NAME}} Agent",
        label: "{{NAME}}",
        description: "{{ONE_LINE_DESCRIPTION}}",
        status: "live",
        slides: [
          // Slide 1: Overview (problem callout, target fit & audience card, 3 challenge cards, objectives)
          {
            title: "{{TITLE_1}}",
            tag: "Scenario {{N}} • Overview",
            subtitle: "{{SUBTITLE_1}}",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">⚡</div>
                <div>
                  <div class="callout-title">{{CALLOUT_TITLE}}</div>
                  <div class="callout-text">{{CALLOUT_TEXT}}</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">{{INDUSTRY_OR_CROSS_INDUSTRY}}</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">{{BUSINESS_OR_TECHNICAL_FUNCTION}}</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">{{ROLE_1}}</span>
                    <span class="fit-pill">{{ROLE_2}}</span>
                    <span class="fit-pill">{{ROLE_3}}</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">{{CHALLENGE_1_TITLE}}</div>
                  </div>
                  <div class="card-body">{{CHALLENGE_1_TEXT}}</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔍</div>
                    <div class="card-title">{{CHALLENGE_2_TITLE}}</div>
                  </div>
                  <div class="card-body">{{CHALLENGE_2_TEXT}}</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🛡️</div>
                    <div class="card-title">{{CHALLENGE_3_TITLE}}</div>
                  </div>
                  <div class="card-body">{{CHALLENGE_3_TEXT}}</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🎯</div>
                  <div class="card-title">Scenario Objectives</div>
                </div>
                <div class="card-body">
                  <ul>
                    <li><strong>{{OBJECTIVE_1_LABEL}}:</strong> {{OBJECTIVE_1_TEXT}}</li>
                    <li><strong>{{OBJECTIVE_2_LABEL}}:</strong> {{OBJECTIVE_2_TEXT}}</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used (before/after; why agentic -- the agent-washing reasoning)
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario {{N}} • Agent Paradigm",
            subtitle: "{{SUBTITLE_2}}",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">{{TRADITIONAL_TITLE}}</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>{{TRADITIONAL_1}}</li>
                      <li>{{TRADITIONAL_2}}</li>
                    </ul>
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">🤖</div>
                    <div class="card-title">{{AGENT_ASSISTED_TITLE}}</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>{{AGENT_ASSISTED_1}}</li>
                      <li>{{AGENT_ASSISTED_2}}</li>
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
                    <div><strong>{{WHY_1_LABEL}}:</strong> {{WHY_1_TEXT}}</div>
                    <div><strong>{{WHY_2_LABEL}}:</strong> {{WHY_2_TEXT}}</div>
                    <div><strong>{{WHY_3_LABEL}}:</strong> {{WHY_3_TEXT}}</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works (architecture: model, knowledge base, flow gate, tool chips)
          {
            title: "How & Why the Agent Works",
            tag: "Scenario {{N}} • Agent Architecture",
            subtitle: "{{SUBTITLE_3}}",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">{{ARCH_1_TITLE}}</div>
                  </div>
                  <div class="card-body">{{ARCH_1_TEXT}}</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">{{ARCH_2_TITLE}}</div>
                  </div>
                  <div class="card-body">{{ARCH_2_TEXT}}</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">{{ARCH_3_TITLE}}</div>
                  </div>
                  <div class="card-body">{{ARCH_3_TEXT}}</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">{{TOOLSET_TITLE}}</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <!-- AUTHOR NOTE: one chip per tool ATTACHED to the agent (scenario.yaml tools.attached) plus the flow name. -->
                    <span class="tool-chip">{{TOOL_NAME_1}}</span>
                    <span class="tool-chip">{{TOOL_NAME_2}}</span>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping (tool -> mock -> real systems -> protocol)
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario {{N}} • Enterprise Integration",
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
                    <!-- AUTHOR NOTE: one row per tool or group of tools. Chips must be real names from scenario.yaml
                         (tool names, flow names, knowledge base names). List only systems you can name accurately. -->
                    <tr>
                      <td><span class="tool-chip">{{TOOL_NAME_1}}</span></td>
                      <td>{{MOCK_ENV_1}}</td>
                      <td><span class="service-tag">{{REAL_SYSTEMS_1}}</span></td>
                      <td>{{PROTOCOL_1}}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">{{INTEGRATION_CALLOUT_TITLE}}</div>
                  <div class="callout-text">{{INTEGRATION_CALLOUT_TEXT}}</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits (4 benefit cards + agent-vs-script trade-off)
          {
            title: "Business & Operational Benefits",
            tag: "Scenario {{N}} • Value Proposition",
            subtitle: "{{SUBTITLE_5}}",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📉</div>
                    <div class="card-title">{{BENEFIT_1_TITLE}}</div>
                  </div>
                  <div class="card-body">{{BENEFIT_1_TEXT}}</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">{{BENEFIT_2_TITLE}}</div>
                  </div>
                  <div class="card-body">{{BENEFIT_2_TEXT}}</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">📋</div>
                    <div class="card-title">{{BENEFIT_3_TITLE}}</div>
                  </div>
                  <div class="card-body">{{BENEFIT_3_TEXT}}</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">{{BENEFIT_4_TITLE}}</div>
                  </div>
                  <div class="card-body">{{BENEFIT_4_TEXT}}</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">{{TRADEOFF_TEXT}}</div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts (one prompt-card per demo scene that has a prompt)
          {
            title: "Live Demo Prompts",
            tag: "Scenario {{N}} • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <!-- AUTHOR NOTE: duplicate the prompt-card block below for every scene that has a prompt in the demo
                     script. Increment the scene number and the prompt-N id (in BOTH the prompt-box id and the
                     copyPrompt call). Keep the order identical to the demo script. -->
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">{{SCENE_1_PILL_TITLE}}</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">{{PROMPT_1}}</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>{{PROMPT_1_TIP}}</span>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
