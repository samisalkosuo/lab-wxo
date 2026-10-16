// Scenario: Customer Returns and Refunds (placeholder). Registers itself on window.SCENARIOS.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {
        id: "customer-returns",
        name: "Customer Returns & Refunds Agent",
        label: "Customer Returns",
        description: "Messy input, return policy & deterministic refund rules",
        status: "soon",
        slides: [
          {
            title: "Customer Returns & Refunds",
            tag: "Scenario 2 • Overview",
            subtitle: "Conversational returns handling with policy lookup and rule-based refund decisions.",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">🚀</div>
                <div>
                  <div class="callout-title">Scenario Under Development</div>
                  <div class="callout-text">This scenario template is ready for your team's upcoming Customer Returns agent workflows and demo scripts.</div>
                </div>
              </div>
            `
          }
        ]
      }
);
