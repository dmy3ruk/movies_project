document.addEventListener("DOMContentLoaded", function () {
  const filmsBtn = document.getElementById("filmsBtn");
  const filmsDropdown = document.getElementById("filmsDropdown");

  filmsBtn.addEventListener("click", function (event) {
    event.preventDefault();
    filmsDropdown.style.display =
      filmsDropdown.style.display === "grid" ? "none" : "grid";
  });

  document.addEventListener("click", function (event) {
    if (
      !filmsBtn.contains(event.target) &&
      !filmsDropdown.contains(event.target)
    ) {
      filmsDropdown.style.display = "none";
    }
  });
});
document.addEventListener("DOMContentLoaded", function () {
    const serialsBtn = document.getElementById("serialsBtn");
    const serialsDropdown = document.getElementById("serialsDropdown");
  
    serialsBtn.addEventListener("click", function (event) {
      event.preventDefault();
      serialsDropdown.style.display =
      serialsDropdown.style.display === "grid" ? "none" : "grid";
    });
  
    document.addEventListener("click", function (event) {
      if (
        !serialsBtn.contains(event.target) &&
        !serialsDropdown.contains(event.target)
      ) {
        serialsDropdown.style.display = "none";
      }
    });
  });
  