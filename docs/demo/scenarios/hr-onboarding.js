// Scenario: HR Onboarding (placeholder). Registers itself on window.SCENARIOS.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "hr-onboarding",
        name: "HR Onboarding Agent",
        label: "HR Onboarding",
        description: "Employee provisioning & workflow automation",
        status: "soon",
        slides: [
          {
            title: "HR Onboarding Automation",
            tag: "Scenario 4 • Overview",
            subtitle: "End-to-end employee provisioning, access governance, and department workflows.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">🚀</div>
                <div>
                  <div class="callout-title">Scenario Under Development</div>
                  <div class="callout-text">This scenario template is ready for your team's upcoming HR Onboarding agent workflows and demo scripts.</div>
                </div>
              </div>
            `
          }
        ]
      }
);
