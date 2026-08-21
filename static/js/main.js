const menuButton = document.querySelector(".menu-button");
const navigation = document.querySelector(".site-nav");

if (menuButton && navigation) {
  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    navigation.classList.toggle("is-open", !isOpen);
  });
}

const year = document.querySelector("[data-current-year]");
if (year) year.textContent = new Date().getFullYear();

const message = document.querySelector("#body");
const counter = document.querySelector("[data-character-count]");
if (message && counter) {
  const updateCount = () => { counter.textContent = message.value.length; };
  message.addEventListener("input", updateCount);
  updateCount();
}
