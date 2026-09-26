"""
Accessible styling for the Streamlit UI.

Targets WCAG 2.1 AA: high-contrast text/background pairs, visible focus
rings for keyboard navigation, minimum touch target sizing, and no
color-only signaling (icons/text are always paired with color cues).
"""

ACCESSIBLE_CSS = """
<style>
:root {
    --lai-bg: #ffffff;
    --lai-fg: #111111;
    --lai-accent: #1a4d2e;
    --lai-accent-contrast: #ffffff;
    --lai-warning-bg: #fff4e5;
    --lai-warning-fg: #7a4b00;
    --lai-focus: #0b5cff;
}

html, body, [class*="css"] {
    color: var(--lai-fg);
    font-size: 16px;
    line-height: 1.5;
}

/* Visible, high-contrast focus ring for all interactive elements (keyboard nav) */
button:focus-visible, a:focus-visible, input:focus-visible,
textarea:focus-visible, select:focus-visible, [tabindex]:focus-visible {
    outline: 3px solid var(--lai-focus) !important;
    outline-offset: 2px !important;
}

/* Ensure buttons have a minimum comfortable touch target (WCAG 2.5.5) */
.stButton > button {
    min-height: 44px;
    font-weight: 600;
    border: 2px solid var(--lai-accent);
}

.stButton > button:hover {
    filter: brightness(0.95);
}

/* Persistent, high-contrast disclaimer banner */
.lai-disclaimer {
    background-color: var(--lai-warning-bg);
    color: var(--lai-warning-fg);
    border: 2px solid var(--lai-warning-fg);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

/* Section headers get a strong left border for non-color structural cues */
.lai-section {
    border-left: 4px solid var(--lai-accent);
    padding-left: 0.75rem;
    margin: 1rem 0;
}

/* Risk items always paired with a text label, never color alone */
.lai-risk {
    color: #7a0010;
    font-weight: 600;
}

.lai-obligation {
    color: #10406b;
    font-weight: 600;
}
</style>
"""
