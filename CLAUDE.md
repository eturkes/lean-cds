# CLAUDE.md

## 1. Agentic Execution & Skill Utilization
* **Evaluate Before Invoking:** Do not blindly assume the names or signatures of available tools. Always evaluate your available toolset (e.g., agent skills) and proactively select the ones that best fit the current objective.
* **System Check Requirement (Anti-Redundancy):** Before attempting to install system-level tools, runtimes, or package managers, check if they already exist in the environment (e.g., `command -v [tool]`). Do not redundantly install existing tools.
* **Verify Work via Execution:** Do not just write code and assume it works. You must actually execute the code (e.g., running compilers or executing tests) to verify it is syntactically correct and produces the expected output.

## 2. "System 2" Two-Phase Workflow
When tasked with building a new project or feature, execute in two distinct phases:
* **Phase 1: Research & Selection:** Pause and use research/lookup skills to investigate the *current* state-of-the-art for the required ecosystem. Output a brief "Decision" explaining the selected stack.
* **Phase 2: Implementation:** Proceed with implementation using *only* the modern tools identified in Phase 1. 

## 3. Environment & Tooling (Negative Constraints)
* **Force Modern Tooling:** Do not regress to legacy tools heavily represented in old training data. 
* **Isolation:** Always opt for virtual environments or isolated dependency management to avoid tainting the root or home directories of the host system or container.

## 4. UI/UX & Design Standards
* **Enterprise-Grade UI:** Design interfaces to be professional, conservative, and suitable for a professional or academic setting. 
* **Theme Awareness:** UIs MUST respect the host system's native light/dark mode settings (e.g., via CSS `prefers-color-scheme` or native framework detection). Do not force dark mode on a light mode system.
* **End-User Focus:** Never expose backend, system, or development information (like the package manager used, environment variables, or framework names) in the frontend UI. The UI must strictly serve the end-user's domain needs.
