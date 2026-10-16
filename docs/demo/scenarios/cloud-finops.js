// Scenario: Cloud FinOps (placeholder). Registers itself on window.SCENARIOS.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "cloud-finops",
        name: "Cloud FinOps Agent",
        label: "Cloud FinOps",
        description: "Cost optimization & resource rightsizing",
        status: "soon",
        slides: [
          {
            title: "Cloud FinOps & Cost Optimization",
            tag: "Scenario 5 • Overview",
            subtitle: "Automated cloud spend anomaly detection, idle resource reclamation, and rightsizing.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">🚀</div>
                <div>
                  <div class="callout-title">Scenario Under Development</div>
                  <div class="callout-text">This scenario template is ready for your team's upcoming Cloud FinOps agent workflows and demo scripts.</div>
                </div>
              </div>
            `
          }
        ]
      }
);
