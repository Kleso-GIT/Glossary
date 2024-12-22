document.addEventListener("DOMContentLoaded", () => {

  const addTermForm = document.querySelector("form[action='/glossary/']");
  if (addTermForm) {
    addTermForm.addEventListener("submit", async (event) => {
      event.preventDefault();


      const formData = new FormData(addTermForm);
      const jsonData = Object.fromEntries(formData.entries());

      const response = await fetch("/glossary/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(jsonData),
      });

      if (response.ok) {
        alert("Term added successfully!");
        window.location.href = "/terms";
      } else {
        const error = await response.json();
        alert("Error: " + error.detail);
      }
    });
  }
});