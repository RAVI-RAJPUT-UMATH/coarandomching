/* ==========================================================================
   JK Classes Barnagar - admin panel behaviour
   1. Sidebar menu on small screens
   2. "Edit" buttons fill the form at the top of the page
   3. Image preview before uploading
   4. Confirmation before deleting anything
   ========================================================================== */

(function () {
  "use strict";

  /* --------------------------------------------------- 1. sidebar ------- */
  var burger = document.getElementById("burger");
  var sidebar = document.getElementById("sidebar");
  var scrim = document.getElementById("scrim");

  function closeSidebar() {
    sidebar.classList.remove("is-open");
    scrim.classList.remove("is-open");
    burger.setAttribute("aria-expanded", "false");
  }

  if (burger && sidebar && scrim) {
    burger.addEventListener("click", function () {
      var open = sidebar.classList.toggle("is-open");
      scrim.classList.toggle("is-open", open);
      burger.setAttribute("aria-expanded", String(open));
    });
    scrim.addEventListener("click", closeSidebar);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { closeSidebar(); }
    });
  }

  /* ----------------------------------------- 2. edit fills the form ----- */
  var form = document.querySelector("[data-edit-form]");
  var formTitle = document.getElementById("formTitle");
  var cancelButton = document.querySelector("[data-cancel-edit]");

  if (form) {
    var originalTitle = formTitle ? formTitle.textContent : "";

    document.querySelectorAll("[data-edit]").forEach(function (button) {
      button.addEventListener("click", function () {
        var data;
        try {
          data = JSON.parse(button.getAttribute("data-edit"));
        } catch (err) {
          return;
        }

        Object.keys(data).forEach(function (key) {
          var input = form.querySelector('[name="' + key + '"]');
          if (!input) { return; }

          if (input.type === "checkbox") {
            input.checked = Boolean(data[key]) && data[key] !== 0;
          } else {
            input.value = data[key] === null ? "" : data[key];
          }
        });

        if (formTitle) {
          formTitle.textContent = originalTitle.replace(/^Add/, "Edit");
        }
        if (cancelButton) { cancelButton.hidden = false; }

        form.scrollIntoView({ behavior: "smooth", block: "start" });
        var firstField = form.querySelector('input[type="text"]');
        if (firstField) { firstField.focus({ preventScroll: true }); }
      });
    });

    if (cancelButton) {
      cancelButton.addEventListener("click", function () {
        var idField = form.querySelector('[name="id"]');
        if (idField) { idField.value = ""; }
        if (formTitle) { formTitle.textContent = originalTitle; }
        cancelButton.hidden = true;
        document.querySelectorAll(".preview[id]").forEach(function (p) { p.hidden = true; });
      });
    }
  }

  /* -------------------------------------------- 3. image preview -------- */
  document.querySelectorAll("input[type=file][data-preview]").forEach(function (input) {
    var box = document.getElementById(input.getAttribute("data-preview"));
    if (!box) { return; }

    var image = box.querySelector("img");
    var label = box.querySelector("span");

    input.addEventListener("change", function () {
      var files = input.files;
      if (!files || !files.length) {
        box.hidden = true;
        return;
      }

      var file = files[0];
      image.src = URL.createObjectURL(file);
      label.textContent = files.length > 1
        ? files.length + " photos selected"
        : file.name + " (" + Math.round(file.size / 1024) + " KB)";
      box.hidden = false;
    });
  });

  /* --------------------------------------- 4. confirm before deleting --- */
  document.querySelectorAll("form[data-confirm]").forEach(function (deleteForm) {
    deleteForm.addEventListener("submit", function (event) {
      if (!window.confirm(deleteForm.getAttribute("data-confirm"))) {
        event.preventDefault();
      }
    });
  });
})();
