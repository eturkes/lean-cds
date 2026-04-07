/* Verifiable Clinical Decision Support — Lean keyword tooltip popovers.
 *
 * Plain-English explanations for the Lean 4 tokens that the host process
 * decorates with `data-lean-tip` attributes. Uses event delegation on the
 * document so that HTMX swaps of the scenario panel keep working without
 * re-binding listeners.
 */
(function () {
  "use strict";

  var TIP_TEXTS = {
    "axiom":
      "axiom — A starting fact the kernel accepts without proof. In this " +
      "audit each axiom is either a published clinical guideline or one " +
      "of the patient's chart-derived findings.",
    "theorem":
      "theorem — A claim Lean must verify before it is accepted. Unlike " +
      "an axiom, a theorem is only true if it is mechanically proven from " +
      "the surrounding axioms and previously-checked theorems.",
    "absurd":
      "absurd — The audit's final theorem. Its goal is False, so " +
      "successfully proving it means the encoded guidelines are mutually " +
      "impossible for this patient.",
    "exact":
      "exact — A tactic that closes the current goal by supplying a " +
      "previously-derived term whose type matches the goal exactly.",
    "apply":
      "apply — A tactic that reduces the current goal to the premises of " +
      "a chosen lemma or axiom; Lean then asks the proof to discharge each " +
      "remaining premise in turn.",
    "and-intro":
      "And.intro — The introduction rule for logical conjunction (∧). To " +
      "prove P ∧ Q you must supply both a proof of P and a proof of Q.",
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
