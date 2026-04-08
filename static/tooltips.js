/* Verifiable Clinical Decision Support — Lean keyword tooltip popovers.
 *
 * Plain-English explanations for the Lean 4 tokens that the host process
 * decorates with `data-lean-tip` attributes. Uses event delegation on the
 * document so that HTMX swaps of the scenario panel keep working without
 * re-binding listeners.
 */
(function () {
  "use strict";

  // Tooltip copy is written for a reader with no Lean / functional
  // programming / formal-verification background: a clinician, an
  // engineering manager, a regulator. The format is always:
  //     `<token>` — short gloss. Concrete reading. Why it matters here.
  // Every entry stays under ~60 words so the popover fits on screen.
  var TIP_TEXTS = {
    // ---- File structure --------------------------------------------------
    "import":
      "import — Loads another Lean file. `import MedicalKnowledge` pulls " +
      "in the shared vocabulary: what a Patient is, the list of treatments, " +
      "and the published clinical-guideline axioms. Nothing in that file is " +
      "re-typed here — it is just made available.",
    "namespace":
      "namespace — Opens a named section. Every declaration inside is " +
      "prefixed with the namespace name from the outside, so each scenario " +
      "can have its own `collision_detected` without clashing. Must be " +
      "closed by a matching `end`.",
    "open":
      "open — Lets this file refer to names inside a namespace without " +
      "writing the prefix every time. `open ClinicalAudit` means we can " +
      "write `Patient` instead of `ClinicalAudit.Patient`.",
    "end":
      "end — Closes the `namespace` that was opened earlier. Everything " +
      "between `namespace X` and `end X` belongs to that namespace.",

    // ---- Declarations ----------------------------------------------------
    "axiom":
      "axiom — A starting fact Lean accepts without proof. In this audit " +
      "every axiom is either a published clinical guideline or a finding " +
      "from the patient's chart — the two kinds of statement the proof is " +
      "allowed to treat as ground truth.",
    "theorem":
      "theorem — A claim Lean will only accept after mechanically checking " +
      "a proof of it. Unlike an axiom (taken on trust), a theorem must be " +
      "derived step by step from the surrounding axioms and previously " +
      "checked theorems.",
    "colon":
      "`:` — Read it as “is a” or “has type”. `JohnDoe : Patient` reads " +
      "“JohnDoe is a Patient”. In a theorem header, `name : SomeClaim` " +
      "reads “name is a proof of SomeClaim” — in Lean, a finished proof is " +
      "itself a value, and the claim it proves is that value's type.",
    "coloneq":
      "`:=` — “is defined as”. The name on the left becomes another way " +
      "of writing the content on the right. Compare with “let x := 2” in " +
      "everyday maths: it names a fresh definition, not an equation the " +
      "kernel has to verify.",

    // ---- Proof tactics ---------------------------------------------------
    "by":
      "by — Switches from writing a proof directly to writing step-by-step " +
      "*tactics*. Everything indented after `by` is a recipe that tells " +
      "Lean how to assemble the proof; the block runs until the goal is " +
      "closed.",
    "unfold":
      "unfold X — Tactic: “replace the name X with its definition here.” " +
      "`Collision` is defined as `Indicated ∧ Contraindicated`, so " +
      "`unfold Collision` rewrites the goal so those two halves become " +
      "visible and can be attacked separately.",
    "apply":
      "apply L — Tactic: “the conclusion of lemma L matches the current " +
      "goal; use L and let me prove its premises next.” If L needs two " +
      "inputs to reach its conclusion, Lean now asks you to prove those " +
      "two inputs as fresh sub-goals.",
    "exact":
      "exact E — Tactic: “the term E is exactly a proof of the current " +
      "goal — accept it as the answer and close this step.” No further " +
      "sub-goals are produced.",
    "bullet":
      "`·` — Focuses the next sub-goal. When a tactic like `apply And.intro` " +
      "leaves more than one goal open, each `·` begins a mini-proof of one " +
      "of them, keeping the branches visually separated.",
    "and-intro":
      "And.intro — To prove a claim of the form “P and Q”, you must supply " +
      "a proof of P and a proof of Q separately. `And.intro` is Lean's name " +
      "for that “here are the two halves” step.",

    // ---- Audit target & meta --------------------------------------------
    "false":
      "False — The proposition that is never true. Proving `False` from a " +
      "set of axioms means the axioms are mutually impossible — which is " +
      "exactly what this audit surfaces: two published guidelines that " +
      "cannot both apply to the same patient.",
    "absurd":
      "absurd — The audit's final theorem. Its claim is `False`, so a " +
      "successful proof of it means the two encoded clinical guidelines " +
      "are logically contradictory for this specific patient.",
    "print-axioms":
      "#print axioms — A meta-command, not part of the proof. It asks Lean " +
      "to print the exact list of axioms the proof of `absurd` actually " +
      "depended on. The host process reads that list to confirm no `sorry` " +
      "(a placeholder that would silently invalidate the proof) was used.",
  };

  var popover = null;
  var currentTarget = null;

  function ensurePopover() {
    if (popover) return popover;
    popover = document.createElement("div");
    popover.className = "lean-tooltip-popover";
    popover.setAttribute("role", "tooltip");
    popover.setAttribute("aria-hidden", "true");
    document.body.appendChild(popover);
    return popover;
  }

  function showTooltip(target) {
    var key = target.getAttribute("data-lean-tip");
    var text = TIP_TEXTS[key];
    if (!text) return;
    var tip = ensurePopover();
    tip.textContent = text;
    tip.classList.add("is-visible");
    tip.setAttribute("aria-hidden", "false");
    currentTarget = target;
    positionTooltip(target, tip);
  }

  function positionTooltip(target, tip) {
    var rect = target.getBoundingClientRect();
    // measure once after content is set
    var tipRect = tip.getBoundingClientRect();
    var margin = 8;
    var placement = "top";
    var top = rect.top - tipRect.height - margin;
    if (top < margin) {
      top = rect.bottom + margin;
      placement = "bottom";
    }
    var left = rect.left + rect.width / 2 - tipRect.width / 2;
    var maxLeft = window.innerWidth - tipRect.width - margin;
    if (left < margin) left = margin;
    if (left > maxLeft) left = maxLeft;
    tip.style.top = Math.round(top) + "px";
    tip.style.left = Math.round(left) + "px";
    tip.dataset.placement = placement;
  }

  function hideTooltip() {
    if (!popover) return;
    popover.classList.remove("is-visible");
    popover.setAttribute("aria-hidden", "true");
    currentTarget = null;
  }

  function nearestTip(node) {
    if (!node || node.nodeType !== 1) return null;
    return node.closest ? node.closest("[data-lean-tip]") : null;
  }

  document.addEventListener("mouseover", function (e) {
    var t = nearestTip(e.target);
    if (t && t !== currentTarget) showTooltip(t);
  });
  document.addEventListener("mouseout", function (e) {
    var t = nearestTip(e.target);
    if (!t) return;
    var related = nearestTip(e.relatedTarget);
    if (related === t) return;
    hideTooltip();
  });
  document.addEventListener("focusin", function (e) {
    var t = nearestTip(e.target);
    if (t) showTooltip(t);
  });
  document.addEventListener("focusout", function (e) {
    var t = nearestTip(e.target);
    if (t) hideTooltip();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hideTooltip();
  });
  window.addEventListener("scroll", hideTooltip, true);
  window.addEventListener("resize", hideTooltip);
})();
