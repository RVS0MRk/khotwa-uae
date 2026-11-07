// Static template event bindings. Dynamic controls use delegation.
document
  .querySelector('[data-onclick="event-0"]')
  .addEventListener("click", function (event) {
    toggleTheme();
  });
document
  .querySelector('[data-onclick="event-1"]')
  .addEventListener("click", function (event) {
    toggleLang();
  });
document
  .querySelector('[data-onclick="event-2"]')
  .addEventListener("click", function (event) {
    chooseEntry("discover");
  });
document
  .querySelector('[data-onclick="event-3"]')
  .addEventListener("click", function (event) {
    chooseEntry("existing");
  });
document
  .querySelector('[data-onclick="event-4"]')
  .addEventListener("click", function (event) {
    discoverIdeas();
  });
document
  .querySelector('[data-onchange="event-5"]')
  .addEventListener("change", function (event) {
    this.dataset.touched = "true";
  });
document
  .querySelector('[data-oninput="event-6"]')
  .addEventListener("input", function (event) {
    updateBudget(this.value);
  });
document
  .querySelector('[data-onclick="event-7"]')
  .addEventListener("click", function (event) {
    generate();
  });
document
  .querySelector('[data-onclick="event-8"]')
  .addEventListener("click", function (event) {
    exportPDF();
  });
document
  .querySelector('[data-onclick="event-9"]')
  .addEventListener("click", function (event) {
    resetApp();
  });
document
  .querySelector('[data-onclick="event-10"]')
  .addEventListener("click", function (event) {
    selectPanel(1);
    document
      .getElementById("lbl-proof")
      .scrollIntoView({ behavior: motionBehavior(), block: "start" });
  });
document
  .querySelector('[data-onclick="event-11"]')
  .addEventListener("click", function (event) {
    copyPassport();
  });
document
  .querySelector('[data-onclick="event-12"]')
  .addEventListener("click", function (event) {
    exportCSV();
  });
document
  .querySelector('[data-onclick="event-13"]')
  .addEventListener("click", function (event) {
    clearProof();
  });
document
  .querySelector('[data-onclick="event-14"]')
  .addEventListener("click", function (event) {
    copyWA();
  });
document
  .querySelector('[data-onclick="event-15"]')
  .addEventListener("click", function (event) {
    openWA();
  });
document
  .querySelector('[data-onclick="event-16"]')
  .addEventListener("click", function (event) {
    copyShare();
  });
document
  .querySelector('[data-onclick="event-17"]')
  .addEventListener("click", function (event) {
    toggleChat();
  });
document
  .querySelector('[data-onclick="event-18"]')
  .addEventListener("click", function (event) {
    toggleChat();
  });
document
  .querySelector('[data-onclick="event-19"]')
  .addEventListener("click", function (event) {
    toggleChat();
  });
document
  .querySelector('[data-onkeydown="event-20"]')
  .addEventListener("keydown", function (event) {
    if (event.key === "Enter") askQuestion();
  });
document
  .querySelector('[data-onclick="event-21"]')
  .addEventListener("click", function (event) {
    askQuestion();
  });
document.addEventListener("input", (event) => {
  if (event.target.matches(".p-price,.p-freq,.p-concern")) calcProof();
});
document.addEventListener("change", (event) => {
  if (event.target.matches(".p-int,.p-pre")) calcProof();
});
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-copy]");
  if (button) copyText(button.dataset.copy, button);
});

document.getElementById("footer-language").onclick = toggleLang;
