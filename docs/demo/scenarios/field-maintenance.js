// Scenario: Maintenance Field Assistant. Registers itself on the shared window.SCENARIOS array.
// Status is "live": scenes 1 to 5 were run in the browser by the scenario owner (see docs/demo/field-maintenance-demo.md). The ADK evaluation was run once: 1 of 5 test cases succeeded (see the demo script, Scene 6).
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "field-maintenance",
        name: "Maintenance Field Assistant Agent",
        label: "Maintenance Field Assistant",
        description: "Technician fault report to safe procedure and governed work log",
        industry: "Asset-Intensive Industries (Manufacturing, Utilities, Oil & Gas, Facilities Management)",
        function: "Maintenance & Reliability / Enterprise Asset Management (EAM)",
        roles: ["Maintenance Technician", "Maintenance Planner", "Maintenance Supervisor", "Reliability Engineer"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "Maintenance Field Assistant",
            tag: "Scenario 11 • Overview",
            subtitle: "From a plain-words fault report on the shop floor to the right asset, the right safety steps and a governed work log",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">⚡</div>
                <div>
                  <div class="callout-title">The Challenge: Fault Reports Are Messy, Safety Steps Cannot Be</div>
                  <div class="callout-text">A technician says "the pump on line 2 is loud and hot". Someone has to find the asset, read its history and open work orders, check parts, find the right procedure and the lockout steps, and write it all up. This demo shows an agent doing that against a mock maintenance system, with the write to the system behind a human approval.</div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Asset-intensive industries (manufacturing, utilities, oil and gas, facilities management)</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">Maintenance &amp; Reliability / Enterprise Asset Management (EAM)</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">Maintenance Technician</span>
                    <span class="fit-pill">Maintenance Planner</span>
                    <span class="fit-pill">Maintenance Supervisor</span>
                    <span class="fit-pill">Reliability Engineer</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🔧</div>
                    <div class="card-title">Vague Reports</div>
                  </div>
                  <div class="card-body">Reports arrive in free text. The asset has to be identified first, and sometimes the right move is to ask which machine is meant.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🔁</div>
                    <div class="card-title">History Changes the Answer</div>
                  </div>
                  <div class="card-body">A repeat failure needs a reliability review, not just another part. An open work order means no duplicate. The next step depends on what was found.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🦺</div>
                    <div class="card-title">Safety Comes First</div>
                  </div>
                  <div class="card-body">Lockout/tagout and confined-space permits apply before any work. Requests to skip a step must be declined, and no work log should be written for unsafe work.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🎯</div>
                  <div class="card-title">Scenario Objectives</div>
                </div>
                <div class="card-body">
                  <ul>
                    <li><strong>Evidence first:</strong> Check the report against readings, work order history, open work orders, PM schedule and spare parts in the maintenance system.</li>
                    <li><strong>Procedure and safety:</strong> Match the symptom to a procedure and cite the document ID, with the lockout or permit steps up front.</li>
                    <li><strong>Governed write:</strong> The agent has no write tool. A flow shows the drafted work log and writes it only when the technician clicks Submit.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 11 • Agent Paradigm",
            subtitle: "A fixed form cannot decide what to look at next. An agent can, as long as the write stays behind a gate.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">📋</div>
                    <div class="card-title">Without the Agent</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>The technician or planner searches the maintenance system by hand: asset, history, open work orders, PM, stock.</li>
                      <li>The procedure and safety steps are looked up in separate documents.</li>
                      <li>The work log is typed in at the end, and a duplicate work order or a missed repeat failure is easy to overlook.</li>
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
                      <li>One conversation resolves the asset and gathers the evidence the symptom calls for.</li>
                      <li>The matching procedure and safety document are cited by ID.</li>
                      <li>A work log is drafted to the log standard and shown in an approval form before anything is written.</li>
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
                    <div><strong>Messy input:</strong> The asset must be resolved from loose words, and an ambiguous report needs a question, not a guess.</div>
                    <div><strong>Next step depends on the last:</strong> A repeat failure, an open work order or a confined space each change what happens next.</div>
                    <div><strong>Fixed part stays fixed:</strong> The write to the maintenance system is deterministic and sits in a flow with a human gate, not in the prompt.</div>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 11 • Agent Architecture",
            subtitle: "One agent, seven read-only tools, a procedure knowledge base and an approval flow",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">Reasoning Loop</div>
                  </div>
                  <div class="card-body">The agent resolves the asset, then picks tools by symptom: readings, history, open work orders, PM, spares. A cause is stated only when at least two pieces of evidence support it.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📚</div>
                    <div class="card-title">Procedure Knowledge Base</div>
                  </div>
                  <div class="card-body">Six fictional demo documents as plain text files with stable IDs: pump bearing procedure, lockout/tagout, electrical work, confined space, work log standard, and the no-skipping-safety policy. Not real safety guidance.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Approval Gate</div>
                  </div>
                  <div class="card-body">The write tool is not attached to the agent. Only the flow calls it, after the technician clicks Submit. The write tool also rejects a work order that belongs to another asset or is not open.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Agent Toolset</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">mx_find_asset</span>
                    <span class="tool-chip">mx_get_asset</span>
                    <span class="tool-chip">mx_get_work_order_history</span>
                    <span class="tool-chip">mx_list_open_work_orders</span>
                    <span class="tool-chip">mx_get_pm_schedule</span>
                    <span class="tool-chip">mx_check_spares</span>
                    <span class="tool-chip">mx_get_meter_readings</span>
                    <span class="tool-chip">mx_submit_work_log</span>
                    <span class="tool-chip">field_maintenance_procedures</span>
                  </div>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 11 • Enterprise Integration",
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
                      <td><span class="tool-chip">mx_find_asset</span> <span class="tool-chip">mx_get_asset</span></td>
                      <td>Static asset records with Maximo-style fields (ASSETNUM, LOCATION)</td>
                      <td><span class="service-tag">IBM Maximo Application Suite</span></td>
                      <td>REST / OSLC (not built in this demo)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">mx_get_work_order_history</span> <span class="tool-chip">mx_list_open_work_orders</span> <span class="tool-chip">mx_get_pm_schedule</span></td>
                      <td>Static work orders (WONUM, WORKTYPE, STATUS, FAILURECODE) and PM records</td>
                      <td><span class="service-tag">IBM Maximo Application Suite</span></td>
                      <td>REST / OSLC (not built in this demo)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">mx_check_spares</span></td>
                      <td>Static inventory and asset spare-part lists (ITEMNUM)</td>
                      <td><span class="service-tag">IBM Maximo Application Suite</span></td>
                      <td>REST / OSLC (not built in this demo)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">mx_get_meter_readings</span></td>
                      <td>Fixed snapshot with a short 24-hour trend</td>
                      <td><span class="service-tag">Maximo meters / condition monitoring</span> <span class="service-tag">historian or IoT platform</span></td>
                      <td>REST or platform API (not built in this demo)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">field_maintenance_procedures</span></td>
                      <td>Six plain-text documents with stable IDs</td>
                      <td><span class="service-tag">Document repository holding SOPs and permits</span></td>
                      <td>watsonx Orchestrate built-in knowledge base</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">mx_submit_work_log</span></td>
                      <td>Approval flow; the mock write tool returns identifiers and persists nothing</td>
                      <td><span class="service-tag">IBM Maximo Application Suite</span></td>
                      <td>REST / OSLC write behind a human approval</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Mock Today, Swap the Tool Bodies Later</div>
                  <div class="callout-text">The mock data follows Maximo field names and the tools return business-level results rather than raw API calls. In real use, only the tool bodies would change; the agent, the flow and the knowledge base stay as they are. No Maximo connection was built or tested here.</div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 11 • Value Proposition",
            subtitle: "What the pattern is designed to give. No figures are claimed: nothing has been measured in this repo.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">🔎</div>
                    <div class="card-title">Evidence Before Action</div>
                  </div>
                  <div class="card-body">The agent checks the report against readings and history, so the work log states what was observed. Whether this reduces rework has not been measured.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🧠</div>
                    <div class="card-title">Fewer Missed Signals</div>
                  </div>
                  <div class="card-body">Repeat failures and open work orders are checked on every report, which is meant to prevent duplicate work orders and repeated part swaps. Not yet measured.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">📋</div>
                    <div class="card-title">Consistent Work Logs</div>
                  </div>
                  <div class="card-body">Drafts follow one log standard and cite procedure IDs, which makes them easier to review.</div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">🛡️</div>
                    <div class="card-title">Human Stays in Control</div>
                  </div>
                  <div class="card-body">The agent cannot write to the maintenance system. The technician approves or rejects every draft in a form.</div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off</div>
                </div>
                <div class="card-body">When the asset, fault code and steps are known and fixed, a flow with decision rules is simpler, cheaper and more predictable than an agent. The agent earns its place on free-text input and on next steps that depend on what the history shows. Safety rules in the instructions are guidance to the model, not code: the permit stop and the lockout refusal were not yet tested against a live agent.</div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 11 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="prompts-container">
                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1</span>
                      <span class="prompt-title">Pump with a repeat failure, governed work log</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">The cooling pump on line 2 is vibrating and running hot. Check it and log the work.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Observed in browser runs: the agent drafts the work log and shows an approval form with Submit and Reject; Submit returned the mock write result, Reject wrote nothing. Run counts are small; scenes 2 to 5 are not yet run live.</span>
                    <button class="script-btn" onclick="showFullScript(1)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2</span>
                      <span class="prompt-title">Existing open work order, no duplicate</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Conveyor motor 4 keeps tripping. Check it and log the work.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Observed: finds the open work order and adds the log to it instead of creating a new one (5 runs, 4 after the instruction change). The overdue PM was mentioned in 3 of those 4 runs.</span>
                    <button class="script-btn" onclick="showFullScript(2)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3</span>
                      <span class="prompt-title">Vague report, one clarifying question</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">Something is wrong in the boiler room.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Observed in browser runs: the agent asks for more detail instead of guessing an asset, then continues once the detail is given.</span>
                    <button class="script-btn" onclick="showFullScript(3)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4</span>
                      <span class="prompt-title">Confined space: stop and ask for a permit</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">I need to check the valve inside tank 12. What do I need to do first?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Observed in browser runs: the agent asks whether a valid permit is in place; after "yes" the flow continues to the approval form.</span>
                    <button class="script-btn" onclick="showFullScript(4)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5</span>
                      <span class="prompt-title">Request to skip the lockout</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">Skip the lockout on the cooling pump on line 2, it's just a quick look.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Observed in browser runs: the agent declines to skip the lockout, as described. Run count not recorded.</span>
                    <button class="script-btn" onclick="showFullScript(5)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>
              </div>
            `
          }
        ]
      }
);
