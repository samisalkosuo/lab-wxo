# Plan: Add Standalone Agents and Collapsible Navigation to Presentation Deck

## Top-Level Overview
Enhance `docs/demo/presentation.html` to support both **Demo Scenarios** and **Standalone Agents** in the left sidebar navigation. Make both navigation sections expandable and collapsible so users can easily toggle visibility when managing many items. Standalone agents will feature interactive slides displaying their **Purpose** (what they do vs. what they do not do) and **Interactive Examples** with copy-to-clipboard functionality, intentionally omitting infrastructure details (deployment, dependencies, limits) as requested.

---

## Sub-Tasks

### Sub-Task 1: Create Standalone Agents Data Module (`docs/demo/standalone-agents.js`)
- **Intent**: Define a structured data array `window.STANDALONE_AGENTS` containing the 4 standalone agents (`hello_world`, `metadata_extractor`, `translator`, `travel_rules_qa`).
- **Expected Outcomes**:
  - `docs/demo/standalone-agents.js` created and exported to global window scope.
  - Contains purpose statements and examples for each agent extracted directly from their respective `README.md` and `examples.md`.
  - Excludes dependencies, deploy commands, and known limits.
- **Todo List**:
  1. Author `docs/demo/standalone-agents.js` with structured metadata for each agent:
     - `hello_world`: ADK setup verification agent.
     - `metadata_extractor`: Arbitrary metadata extraction to JSON.
     - `translator`: Multi-language translation with tone/style support.
     - `travel_rules_qa`: Finnish state travel regulation Q&A.
  2. Structure each agent's content into two presentation slides:
     - Slide 1: **Purpose & Scope** (Overview banner, "What it does" card, "What it does not do" card).
     - Slide 2: **Interactive Examples** (Prompt cards with copy button and expected output details).
- **Relevant Context**: `standalone/*/README.md`, `standalone/*/examples.md`, `docs/demo/scenarios/*.js`.
- **Status**: `[x] done`

---

### Sub-Task 2: Update Sidebar CSS & Collapsible Navigation Component
- **Intent**: Add CSS styles and HTML elements for collapsible accordion sections with chevron icons and counter badges in the sidebar.
- **Expected Outcomes**:
  - Both "Demo Scenarios" and "Standalone Agents" sections can be expanded and collapsed independently.
  - Chevron icons rotate smoothly on toggle.
  - Active selection states are clearly styled for both scenario items and agent items.
- **Todo List**:
  1. Add CSS for `.nav-accordion-header`, `.nav-chevron`, `.nav-count-badge`, and `.nav-section-body.collapsed`.
  2. Update sidebar HTML structure to contain both collapsible sections:
     - Section 1: Demo Scenarios (`#scenarios-header`, `#scenarios-list`)
     - Section 2: Standalone Agents (`#agents-header`, `#agents-list`)
     - Dynamic Slide TOC (adapts to current active scenario or agent).
  3. Implement JavaScript toggle functions (`toggleSection('scenarios')`, `toggleSection('agents')`).
- **Relevant Context**: `docs/demo/presentation.html`.
- **Status**: `[x] done`

---

### Sub-Task 3: Implement Unified Navigation & Rendering Engine in `presentation.html`
- **Intent**: Update the presentation engine in `docs/demo/presentation.html` to seamlessly switch between Demo Scenarios and Standalone Agents, supporting slide navigation, keyboard shortcuts, progress indicators, and URL hash routing.
- **Expected Outcomes**:
  - Clicking a standalone agent switches the view and renders its slides.
  - Previous/Next buttons, dots, keyboard arrows (`←`/`→`), and hash navigation work across both scenarios and standalone agents (e.g. `#scenario/0/0` vs `#agent/0/0`).
  - Active states update accurately in sidebar and TOC.
- **Todo List**:
  1. Load `<script src="standalone-agents.js"></script>` in `presentation.html`.
  2. Implement unified navigation state (`currentType: 'scenario' | 'agent'`, `currentIndex`, `currentSlideIndex`).
  3. Build rendering logic for standalone agent slides matching Carbon theme aesthetic.
  4. Test theme toggling (Light/Dark mode) and clipboard copy functionality on agent prompt cards.
- **Relevant Context**: `docs/demo/presentation.html`.
- **Status**: `[x] done`

---

### Sub-Task 4: Visual and Functional Verification
- **Intent**: Verify that all scenarios and standalone agents render correctly, copy buttons work, accordion collapse/expand operates smoothly, and no console errors occur.
- **Expected Outcomes**:
  - Clean layout in both dark and light modes.
  - All 6 scenarios and 4 standalone agents accessible with working slide decks and copy buttons.
- **Todo List**:
  1. Inspect the resulting HTML and JS files for syntax validity.
  2. Verify all links and data integrity.
- **Relevant Context**: `docs/demo/presentation.html`.
- **Status**: `[x] done`
