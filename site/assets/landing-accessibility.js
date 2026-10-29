(() => {
  const stage = document.querySelector("[data-demo-stage]");
  if (!stage || !window.matchMedia) return;

  const coarsePointer = window.matchMedia("(any-pointer: coarse)");
  const updateStage = () => stage.toggleAttribute("inert", coarsePointer.matches);

  updateStage();
  coarsePointer.addEventListener?.("change", updateStage);
})();
