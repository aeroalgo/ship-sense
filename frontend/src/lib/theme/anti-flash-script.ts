export const ANTI_FLASH_SCRIPT = `(function () {
  try {
    var t = localStorage.getItem("shipsense-theme");
    var d = localStorage.getItem("shipsense-design");
    if (t === "day" || t === "night" || t === "dim") {
      document.documentElement.setAttribute("data-theme", t);
    } else {
      document.documentElement.setAttribute("data-theme", "day");
    }
    if (d === "d01" || d === "d02" || d === "d03" || d === "d04" || d === "d05") {
      document.documentElement.setAttribute("data-design", d);
    } else {
      document.documentElement.setAttribute("data-design", "d01");
    }
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "day");
    document.documentElement.setAttribute("data-design", "d01");
  }
})();`;
