document.addEventListener("mouseover", e => {
	if (e.target.tagName !== "BUTTON") return;

	const tooltip = e.target.querySelector("span");

	if (!tooltip) return;

	tooltip.style.left = Math.min(e.offsetX, 400) + 10 + "px";
	tooltip.style.top = Math.max(e.offsetY, 10) + 10 + "px";
});

fetch("/username")
	.then(r => r.text())
	.then(username => {
		document.getElementById("username").textContent = username;
	});
