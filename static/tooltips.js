/* Verifiable Clinical Decision Support — Lean keyword tooltip popovers.
 *
 * Plain-English explanations for the Lean 4 tokens that the host
 * process decorates with `data-lean-tip` attributes. The server-side
 * decorator in `lean_decorate.py` composes the tooltip text *per
 * source line*, baking the declaration name, type, proof body, or
 * tactic argument into each occurrence — so there is no shared
 * dictionary here; the attribute value *is* the text to display.
 *
 * Uses event delegation on the document so HTMX swaps of the scenario
 * panel keep working without re-binding listeners.
 */
(function () {
  "use strict";

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
    var text = target.getAttribute("data-lean-tip");
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
