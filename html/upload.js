"use strict";

import { elemGenerator } from "https://javajawa.github.io/elems.js/elems.js";

const upload = document.getElementById("upload");
const list   = document.getElementById("list");
const submit = document.getElementById("submit");
const reader = new FileReader();

const input  = elemGenerator("input");
const label  = elemGenerator("label");
const li     = elemGenerator("li");

upload.addEventListener("change", () => reader.readAsText(upload.files[0]));
list.addEventListener("change", () => {
	submit.setAttribute("disabled", "");
	list.querySelectorAll("input").forEach(i => {
		i.checked && submit.removeAttribute("disabled")
	});
});
reader.addEventListener("load", processEmpires);


document.addEventListener("mouseover", e => {
	if (e.target.tagName !== "BUTTON") return;

	const tooltip = e.target.querySelector("span");

	if (!tooltip) return;

	tooltip.style.left = (Math.min(e.offsetX, 400) + 10) + "px";
	tooltip.style.top  = (Math.max(e.offsetY, 10) + 10)  + "px";
} );

function processEmpires()
{
	while (list.lastChild) {
		list.removeChild(list.lastChild);
	}
	submit.setAttribute("disabled", "");

	const data = reader.result;

	// Offset where the current empire starts.
	let start  = 0;
	// Offset we have read up to.
	let offset = data.indexOf("{");
	// The nesting level of `{}` we're at.
	let depth  = 1;
	// Where the next `{` and `}` are.
	let nextOpen, nextClose;

	while (true) {
		// Find the next braces.
		nextOpen  = data.indexOf("{", offset + 1);
		nextClose = data.indexOf("}", offset + 1);

		// If no more braces, we're done
		if (nextOpen === -1 && nextClose === -1) {
			return;
		}

		if (nextOpen !== -1 && nextOpen < nextClose) {
			++depth;
			offset = nextOpen;
			continue;
		}

		// We're up one level of nested
		--depth;

		// If depth > 0, we're still in an empire definitions.
		if (depth) {
			offset = nextClose;
			continue;
		}

		// If depth == 0, everything between `start`
		processEmpire(data.substring(start, nextClose));

		// If there are no { after this empire, then no more empires.
		if (nextOpen === -1) {
			return;
		}

		start  = nextClose + 1;
		offset = nextOpen;
		depth  = 1;
	}
}

function processEmpire(text) {
	const lines = text.trim().split("\n");

	let name = lines[0].trim();

	while (name.endsWith("{") || name.endsWith("=")) {
		name = name.substring(0, name.length - 1).trim();
	}

	let ethics = [];

	lines.map(line => line.trim())
		.filter(line => line.startsWith("ethic"))
		.map(line => line.replace(/^ethic="/, ""))
		.map(line => line.replace(/^ethic_/, ""))
		.map(line => line.replace("_", " "))
		.map(line => line.replace(/"$/, ""))
		.forEach(line => ethics.push(line))
	;

	list.appendChild(li(
		input({id: name, type: "checkbox", name: "select", value: name}),
		label({"for": name}, name + " [" + ethics.join(", ") + "]")
	));
}

fetch("/username").then(r => r.text()).then(username => {
	document.getElementById("username").textContent = username;
});
