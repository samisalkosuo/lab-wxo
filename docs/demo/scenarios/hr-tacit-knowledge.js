// Scenario: HR Tacit Knowledge. Registers itself on the shared window.SCENARIOS array.
// Order of <script src> tags in presentation.html decides the sidebar number.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "hr-tacit-knowledge",
        name: "HR Tacit Knowledge Agent",
        label: "HR Tacit Knowledge",
        description: "Captures tacit HR knowledge from work artefacts, gets expert review, and answers new-hire questions with citations",
        industry: "Cross-Industry",
        function: "HR Shared Services & Knowledge Management",
        roles: ["HR Specialist", "HR Operations Lead", "People Experience Manager", "New Hire / Role-changer"],
        status: "live",
        slides: [
          // Slide 1: Overview
          {
            title: "HR Tacit Knowledge Capture & Guide",
            tag: "Scenario 10 • Overview",
            subtitle: "Two agents: one that captures undocumented HR know-how from everyday work artefacts, and one that delivers it to new hires with citations.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">📚</div>
                <div>
                  <div class="callout-title">The Invisible Knowledge Problem</div>
                  <div class="callout-text">
                    When an experienced HR specialist leaves or changes role, the workarounds, edge-case
                    procedures, and "why we do it this way" knowledge go with them.
                    New hires read stale intranet pages, ask the wrong person, or make the same expensive
                    mistakes their predecessors already solved.
                  </div>
                </div>
              </div>

              <div class="fit-card">
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">🏢</span> Industry</div>
                  <div class="fit-value">Cross-Industry</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">⚙️</span> Function</div>
                  <div class="fit-value">HR Shared Services &amp; Knowledge Management</div>
                </div>
                <div class="fit-group">
                  <div class="fit-label"><span class="fit-label-icon">👥</span> Target Roles</div>
                  <div class="fit-pills">
                    <span class="fit-pill">HR Specialist (Expert / Content Owner)</span>
                    <span class="fit-pill">HR Operations Lead</span>
                    <span class="fit-pill">People Experience Manager</span>
                    <span class="fit-pill">New Hire / Role-changer</span>
                  </div>
                </div>
              </div>

              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">🚨</div>
                    <div class="card-title">Knowledge Lives in Inboxes</div>
                  </div>
                  <div class="card-body">
                    Resolved tickets, chat threads, and personal notes contain hard-won
                    procedures that never make it into official documentation.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">📄</div>
                    <div class="card-title">Stale Intranet Pages</div>
                  </div>
                  <div class="card-body">
                    Intranet pages are updated infrequently. New hires follow outdated
                    procedures — wrong forms, wrong deadlines, wrong cutoff dates.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔒</div>
                    <div class="card-title">PII in Expert Notes</div>
                  </div>
                  <div class="card-body">
                    Expert notes and case write-ups often include employee names, IDs,
                    and health information. Capturing the lesson requires removing the
                    personal data first — reliably, not by hope.
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
                    <li><strong>Capture with minimal expert effort:</strong> Harvest knowledge from work already done (tickets, chat, documents). The expert reviews a draft — they do not write from scratch.</li>
                    <li><strong>Govern what goes into the KB:</strong> PII is scanned in code before any draft reaches the expert. Publishing only happens after explicit expert confirmation in a flow. Reject means nothing is written.</li>
                    <li><strong>Answer new-hire questions with citations:</strong> The guide agent answers from the KB, cites the article ID, and routes gaps to the right expert so the answer becomes a new article.</li>
                  </ul>
                </div>
              </div>
            `
          },

          // Slide 2: Why & How the Agent is Used
          {
            title: "Why & How the Agent is Used",
            tag: "Scenario 10 • Agent Paradigm",
            subtitle: "Two separate agents, two audiences — and an honest account of where an agent is and is not justified.",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-red">⏱️</div>
                    <div class="card-title">Without the Agent</div>
                  </div>
                  <div class="card-body">
                    <ul>
                      <li>Expert manually reviews batches of tickets and notes, decides what is worth documenting, writes the article, checks it for employee data, publishes it to the intranet.</li>
                      <li>New hire reads a possibly stale intranet page, asks a colleague, or escalates to the wrong team — same question answered repeatedly by different people.</li>
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
                      <li><strong>Curator agent:</strong> triages a batch of artefacts, drafts the article, scans for PII, opens the review form. The expert reads and clicks Confirm or Reject.</li>
                      <li><strong>Guide agent:</strong> answers from the KB with a citation, or names the right expert and, with the learner's confirmation, routes the gap into a new draft.</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-purple">🧠</div>
                  <div class="card-title">Why an Agentic Solution? (Honest Version)</div>
                </div>
                <div class="card-body">
                  <div class="grid-3" style="margin-bottom:0;">
                    <div><strong>Not all agentic:</strong> PII detection is deterministic regex + term lists, not the agent. Publishing is a flow gate. Only the open-ended parts justify an agent.</div>
                    <div><strong>Judgment calls:</strong> What counts as tacit knowledge in a mixed batch? Is it a workaround, routine chatter, or a near-duplicate? The decision tree cannot be drawn in advance — the agent is justified here.</div>
                    <div><strong>Vague questions:</strong> Learner questions are messy and role-dependent. Whether the KB covers the answer decides between answering and routing — another open-ended decision the agent handles.</div>
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">📋</div>
                  <div class="card-title">Six Demo Cases</div>
                </div>
                <div class="card-body">
                  <table style="width:100%; border-collapse:collapse; font-size:13px;">
                    <thead>
                      <tr style="border-bottom:1px solid var(--border);">
                        <th style="text-align:left; padding:4px 8px;">ID</th>
                        <th style="text-align:left; padding:4px 8px;">Agent</th>
                        <th style="text-align:left; padding:4px 8px;">Entry</th>
                        <th style="text-align:left; padding:4px 8px;">Teaches</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:4px 8px;"><strong>TK-001</strong></td>
                        <td style="padding:4px 8px;">Curator</td>
                        <td style="padding:4px 8px;">Review harvested items (batch of 4)</td>
                        <td style="padding:4px 8px;">Triage: NEW vs DUPLICATE vs IGNORE; draft + review flow</td>
                      </tr>
                      <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:4px 8px;"><strong>TK-002</strong></td>
                        <td style="padding:4px 8px;">Curator</td>
                        <td style="padding:4px 8px;">Same batch, artifact A-105</td>
                        <td style="padding:4px 8px;">Contradiction detection — UPDATE an existing article, not a duplicate</td>
                      </tr>
                      <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:4px 8px;"><strong>TK-003</strong></td>
                        <td style="padding:4px 8px;">Curator</td>
                        <td style="padding:4px 8px;">Expert pastes a document in chat</td>
                        <td style="padding:4px 8px;">PII redaction; draft + conflict flag; confirm/reject</td>
                      </tr>
                      <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:4px 8px;"><strong>TK-004</strong></td>
                        <td style="padding:4px 8px;">Guide</td>
                        <td style="padding:4px 8px;">New hire asks about employment certificates</td>
                        <td style="padding:4px 8px;">Answer from current article; ignore superseded red herring</td>
                      </tr>
                      <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:4px 8px;"><strong>TK-005</strong></td>
                        <td style="padding:4px 8px;">Guide</td>
                        <td style="padding:4px 8px;">New hire asks about work permit letter</td>
                        <td style="padding:4px 8px;">KB gap: name the right expert; ask before routing</td>
                      </tr>
                      <tr>
                        <td style="padding:4px 8px;"><strong>TK-006</strong></td>
                        <td style="padding:4px 8px;">Curator</td>
                        <td style="padding:4px 8px;">Expert clicks Reject in the review form</td>
                        <td style="padding:4px 8px;">Governance: nothing published on Reject</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            `
          },

          // Slide 3: How & Why the Agent Works
          {
            title: "How & Why the Agent Works",
            tag: "Scenario 10 • Agent Architecture",
            subtitle: "Two agents with different tool sets, one shared knowledge base, and deterministic governance enforced in code.",
            render: () => `
              <div class="grid-3">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔄</div>
                    <div class="card-title">Curator Agent (hr_tk_curator)</div>
                  </div>
                  <div class="card-body">
                    Read-only tools: list artefacts, fetch full text, scan for PII, find related KB articles, find the right expert.
                    Write path: the <strong>hr_tk_review_draft</strong> flow — only after explicit expert confirmation does the flow call the publish tool.
                    The agent never calls the publish tool directly.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📖</div>
                    <div class="card-title">Guide Agent (hr_tk_guide)</div>
                  </div>
                  <div class="card-body">
                    Answers learner questions from <strong>hr_tk_knowledge</strong> with article citations.
                    When the KB has no answer, calls <strong>hr_tk_find_expert</strong> and — after the learner confirms — starts the <strong>hr_tk_answer_gap</strong> flow to capture the expert's answer as a new draft.
                    No access to PII, draft, or publish tools.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-amber">🛡️</div>
                    <div class="card-title">Governance in Code</div>
                  </div>
                  <div class="card-body">
                    PII scanner: deterministic regex + known name list. Publish tool re-checks PII and refuses if anything remains (<strong>PII_REMAINING</strong>).
                    Publish tool also enforces: valid ISO date, non-empty title/body/sources/approver, status = current or superseded, no update to a superseded article.
                    These rules run in Python — not in prompts.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-teal">🛠️</div>
                  <div class="card-title">Tools — Curator</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">hr_tk_list_new_artifacts</span>
                    <span class="tool-chip">hr_tk_get_artifact</span>
                    <span class="tool-chip">hr_tk_scan_pii</span>
                    <span class="tool-chip">hr_tk_find_related_articles</span>
                    <span class="tool-chip">hr_tk_find_expert</span>
                    <span class="tool-chip">hr_tk_review_draft</span>
                    <span class="tool-chip" style="background:var(--surface); color:var(--text-muted); border:1px solid var(--border);">hr_tk_publish_article (flow-only)</span>
                    <span class="tool-chip" style="background:var(--surface); color:var(--text-muted); border:1px solid var(--border);">hr_tk_notify_expert (flow-only)</span>
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-purple">🛠️</div>
                  <div class="card-title">Tools — Guide</div>
                </div>
                <div class="card-body">
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                    <span class="tool-chip">hr_tk_get_employee_profile</span>
                    <span class="tool-chip">hr_tk_find_expert</span>
                    <span class="tool-chip">hr_tk_answer_gap</span>
                  </div>
                  <p style="margin-top:8px; font-size:13px; color:var(--text-muted);">
                    Knowledge base: <span class="tool-chip">hr_tk_knowledge</span>
                    (6 seeded articles, HR-TK-ART-01 to ART-06, plain text, two with intentionally stale facts for the demo)
                  </p>
                </div>
              </div>
            `
          },

          // Slide 4: Real-Life Backend Services Mapping
          {
            title: "Real-Life Backend Services Mapping",
            tag: "Scenario 10 • Enterprise Integration",
            subtitle: "How the mock tools in this demo translate to production enterprise systems in your technology stack.",
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
                      <td><span class="tool-chip">hr_tk_list_new_artifacts</span><br><span class="tool-chip">hr_tk_get_artifact</span></td>
                      <td>Static Python dict (tickets, chat threads, doc text)</td>
                      <td><span class="service-tag">ServiceNow</span> <span class="service-tag">Microsoft Teams</span> <span class="service-tag">SharePoint</span></td>
                      <td>REST API / Graph API / ServiceNow Table API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_tk_scan_pii</span></td>
                      <td>Deterministic regex + name list (Python, no model)</td>
                      <td><span class="service-tag">Microsoft Presidio</span> <span class="service-tag">AWS Comprehend</span> <span class="service-tag">Azure AI Language</span></td>
                      <td>Library call or REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_tk_find_related_articles</span></td>
                      <td>Keyword matching against in-memory article metadata</td>
                      <td><span class="service-tag">WXO Built-in KB (hr_tk_knowledge)</span> <span class="service-tag">Elasticsearch</span></td>
                      <td>KB semantic search / vector store query</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_tk_find_expert</span></td>
                      <td>Static expert directory (Python dict)</td>
                      <td><span class="service-tag">Active Directory / Azure AD</span> <span class="service-tag">Workday</span> <span class="service-tag">SAP SuccessFactors</span></td>
                      <td>LDAP / SCIM / HCM REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_tk_get_employee_profile</span></td>
                      <td>Static learner profiles (Python dict)</td>
                      <td><span class="service-tag">Workday</span> <span class="service-tag">SAP SuccessFactors</span> <span class="service-tag">BambooHR</span></td>
                      <td>HCM REST API</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_tk_publish_article</span> (flow-only)</td>
                      <td>Returns article text; does NOT write to disk. Re-import needed.</td>
                      <td><span class="service-tag">SharePoint / Confluence</span> <span class="service-tag">WXO KB re-import</span></td>
                      <td>REST API + <code>orchestrate knowledge-bases import</code></td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_tk_notify_expert</span> (flow-only)</td>
                      <td>Simulated — returns delivered: false</td>
                      <td><span class="service-tag">Microsoft Teams</span> <span class="service-tag">Outlook</span> <span class="service-tag">Slack</span></td>
                      <td>Graph API / SMTP / Slack Webhooks</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_tk_review_draft</span> (flow)</td>
                      <td>WXO flow with an editable form; Confirm → publish; Reject → nothing</td>
                      <td><span class="service-tag">WXO Approval Flow</span></td>
                      <td>WXO Flow Builder (native)</td>
                    </tr>
                    <tr>
                      <td><span class="tool-chip">hr_tk_knowledge</span> (KB)</td>
                      <td>6 plain-text (.txt) articles in <code>knowledge/hr-tacit-knowledge/articles/</code></td>
                      <td><span class="service-tag">SharePoint</span> <span class="service-tag">Confluence</span> <span class="service-tag">WXO Built-in KB</span></td>
                      <td>File connector sync / KB import</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="callout-banner">
                <div class="callout-icon">💡</div>
                <div>
                  <div class="callout-title">Publishing is not instant</div>
                  <div class="callout-text">
                    In this demo, <code>hr_tk_publish_article</code> validates governance rules and returns the final article text —
                    it does NOT write to disk or update the live KB.
                    In a real deployment the article would be written to a connected document store and the KB re-indexed.
                    The agent always says "not yet searchable until re-import" after a successful publish.
                  </div>
                </div>
              </div>
            `
          },

          // Slide 5: Business & Operational Benefits
          {
            title: "Business & Operational Benefits",
            tag: "Scenario 10 • Value Proposition",
            subtitle: "What this approach achieves — and what it honestly does not (no measured numbers in this demo).",
            render: () => `
              <div class="grid-2">
                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-green">📉</div>
                    <div class="card-title">Capture Without Extra Work</div>
                  </div>
                  <div class="card-body">
                    Tacit knowledge is harvested from tickets, chat threads and documents the expert already wrote.
                    The expert's job is to review a draft and click Confirm — not to write the article from scratch.
                    Minimum interruption; maximum capture rate.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-blue">🔍</div>
                    <div class="card-title">Stale Knowledge Surfaced</div>
                  </div>
                  <div class="card-body">
                    When a new artefact contradicts an existing KB article (different form, different cutoff date),
                    the curator flags it as an UPDATE — not a duplicate and not a new article.
                    Stale information is identified and corrected, not silently buried alongside the current version.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-teal">🔒</div>
                    <div class="card-title">PII Removed Before Expert Sees the Draft</div>
                  </div>
                  <div class="card-body">
                    Expert notes often contain employee names, IDs, health conditions, salary amounts.
                    The PII scan runs in code — not in a prompt — before the draft is sent for review.
                    The publish tool re-checks and refuses if anything remains.
                    The expert never approves a draft that still contains personal data.
                  </div>
                </div>

                <div class="card">
                  <div class="card-header">
                    <div class="card-icon icon-purple">📖</div>
                    <div class="card-title">Cited Answers for New Hires</div>
                  </div>
                  <div class="card-body">
                    The guide cites the article ID in every answer.
                    If the KB does not cover a question, it names the right expert and routes the gap —
                    turning an unanswered question into a future KB article with the expert's confirmation.
                    Knowledge gaps close automatically over time.
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-icon icon-amber">⚖️</div>
                  <div class="card-title">Agent vs. Plain Script Trade-off (Honest)</div>
                </div>
                <div class="card-body">
                  The fixed governance parts (PII scan, publish validation) are deterministic code — they would work equally well in a plain script.
                  The agent is justified for the open-ended parts: classifying a mixed batch of artefacts, deciding whether an artefact is NEW / UPDATE / DUPLICATE / IGNORE based on what the KB search returns, and answering vague learner questions.
                  These decisions depend on intermediate results and cannot be drawn as a fixed flowchart in advance.
                  <strong>Not measured in this demo:</strong> how often the agent classifies correctly, time saved per expert session, or quality vs. human-written articles.
                  This scenario demonstrates the architecture and governance pattern; it does not prove efficiency numbers.
                </div>
              </div>
            `
          },

          // Slide 6: Live Demo Prompts
          {
            title: "Live Demo Prompts",
            tag: "Scenario 10 • WXO Chat Assistant",
            subtitle: "Copy and paste these prompts directly into the watsonx Orchestrate chat interface during your live demo.",
            render: () => `
              <div class="callout-banner" style="margin-bottom:12px;">
                <div class="callout-icon">⚠️</div>
                <div>
                  <div class="callout-title">Two agents — select the right one for each scene</div>
                  <div class="callout-text">
                    Curator scenes (TK-001, TK-002, TK-003, TK-006) use the <strong>HR Tacit Knowledge Curator</strong> agent
                    (<code>hr_tk_curator</code>). Guide scenes (TK-004, TK-005) use the <strong>HR Tacit Knowledge Guide</strong>
                    agent (<code>hr_tk_guide</code>). Start a fresh conversation for each scene.
                  </div>
                </div>
              </div>

              <div class="prompts-container">

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 1 — TK-001</span>
                      <span class="prompt-title">Batch Triage (Curator)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-1', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-1">Review the newly harvested items.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Agent: hr_tk_curator. Expect triage of A-101..A-104 (NEW / DUPLICATE / IGNORE), then a draft article for A-101 and the review form. Red herring: A-102 and A-103 look like new knowledge but are already covered by HR-TK-ART-03.</span>
                    <button class="script-btn" onclick="showFullScript(1)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 2 — TK-002</span>
                      <span class="prompt-title">Contradiction Detection (Curator)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-2', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-2">Review the newly harvested items. Focus on ticket A-105.</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Agent: hr_tk_curator. A-105 contradicts HR-TK-ART-04 (form HR-22 / 10 days is stale; real: e-form PR-1 / 5 days). Red herring: HR-TK-ART-05 covers Sweden, not Finland. The agent should propose UPDATE to ART-04, not ART-05.</span>
                    <button class="script-btn" onclick="showFullScript(2)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 3 — TK-003</span>
                      <span class="prompt-title">Document Drop-in with PII (Curator)</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-3">I have some personal notes about correcting retroactive leave start dates. Can you turn this into a KB article? Here are my notes:</div>
                  <div class="prompt-card-top" style="margin-top:4px;">
                    <div class="prompt-meta">
                      <span class="scene-pill">Step 2</span>
                      <span class="prompt-title">Sample document — paste after the prompt</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('sample-doc-3', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Document
                    </button>
                  </div>
                  <div class="prompt-box" id="sample-doc-3" data-sample-doc="hr-tk-sample/expert-notes-retroactive-leave-dates.txt">Loading document…</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Agent: hr_tk_curator. Two copy steps: click Copy Prompt and paste it into the chat (do not send), then come back, click Copy Document and paste it right after the colon. PII includes names, national IDs, phone numbers, salary amounts, health terms. The agent should also flag that the document says the cutoff is the 22nd while HR-TK-ART-01 says the 18th.</span>
                    <button class="script-btn" onclick="showFullScript(3)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 4 — TK-004</span>
                      <span class="prompt-title">Guide: Current Article + Superseded Red Herring</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-4', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-4">I'm Emilia Saarinen, new HR Coordinator at the Finland desk. How do I get an employment certificate for an employee who needs it for a bank?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Agent: hr_tk_guide. Expects citation of HR-TK-ART-03 (current). Red herring: HR-TK-ART-02 is superseded — the agent must not cite it as current guidance. The guide may optionally call hr_tk_get_employee_profile to read Emilia's role.</span>
                    <button class="script-btn" onclick="showFullScript(4)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 5 — TK-005</span>
                      <span class="prompt-title">Guide: KB Gap — Route to Expert</span>
                    </div>
                    <button class="copy-btn" onclick="copyPrompt('prompt-5', this)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                      Copy Prompt
                    </button>
                  </div>
                  <div class="prompt-box" id="prompt-5">An employee is asking for a work permit support letter from HR. I've never handled this before. Who should I ask about this?</div>
                  <div class="prompt-tip">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Agent: hr_tk_guide. The KB description explicitly excludes visa and work permit documentation. The agent should name Janne Korhonen (X-102, HR Operations Lead) and ask whether to route the question — NOT start the flow immediately.</span>
                    <button class="script-btn" onclick="showFullScript(5)" title="Open the full demo script for this scene">Show full script</button>
                  </div>
                </div>

                <div class="prompt-card">
                  <div class="prompt-card-top">
                    <div class="prompt-meta">
                      <span class="scene-pill">Scene 6 — TK-006</span>
                      <span class="prompt-title">Governance: Expert Rejects the Draft</span>
                    </div>
                    <div style="font-size:12px; color:var(--text-muted); align-self:center;">Browser only — no copy prompt</div>
                  </div>
                  <div class="prompt-tip" style="margin-top:8px;">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    <span>Run TK-001 or TK-002, wait for the review form, then click <strong>Reject</strong>. The agent should report "REJECTED BY EXPERT. Nothing was published." Verify that hr_tk_publish_article was NOT called. This scene can only be driven in the browser.</span>
                  </div>
                </div>

              </div>
            `
          }
        ]
      }
);
