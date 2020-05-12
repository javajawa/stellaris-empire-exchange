'use strict';

import { elemGenerator } from 'https://javajawa.github.io/elems.js/elems.js';

const upload = document.getElementById('upload');
const list   = document.getElementById('list');
const submit = document.getElementById('submit');
const reader = new FileReader();

const li     = elemGenerator('li');
const label  = elemGenerator('label');
const input  = elemGenerator('input');

upload.addEventListener('change', e => reader.readAsText(upload.files[0]));
list.addEventListener('change', e => {
	submit.setAttribute("disabled", "");
	list.querySelectorAll('input').forEach(i => {
		i.checked && submit.removeAttribute("disabled")
	});
});
reader.addEventListener('load', processEmpires);

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
	let offset = data.indexOf('{');
	// The nesting level of `{}` we're at.
	let depth  = 1;
	// Where the next `{` and `}` are.
	let nextOpen, nextClose;

	while (true) {
		// Find the next braces.
		nextOpen  = data.indexOf('{', offset + 1);
		nextClose = data.indexOf('}', offset + 1);

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

	while (name.endsWith('{') || name.endsWith('=')) {
		name = name.substring(0, -1).trim();
	}

	let ethics = [];

	lines.map(line => line.trim())
		.filter(line => line.startsWith('ethic'))
		.map(line => line.replace(/^ethic=\"/, ''))
		.map(line => line.replace(/^ethic_/, ''))
		.map(line => line.replace('_', ' '))
		.map(line => line.replace(/"$/, ''))
		.forEach(line => ethics.push(line))
	;

	list.appendChild(li(
		input({id: name, type: "checkbox", name: "select", value: name}),
		label({"for": name}, name + ' [' + ethics.join(", ") + ']')
	));
}

fetch('/username').then(r => r.text()).then(username => {
	document.getElementById("username").textContent = username;
	let count = 0;
	let approved = 0;

	function updateHint() {
		document.getElementById('empire-count').textContent =
			count + ", of which " + approved + " moderated.";
	}

	fetch('/ajax-approved').then(r => r.json())
		.then(r => r.map(e => li(`${e.name} by ${e.author} [${e.ethics.join(", ")}]`)))
		.then(r => {
			const p = document.getElementById('approved');
			r.forEach(e => p.appendChild(e));

			count += r.length;
			approved += r.length;
			updateHint();
		}
	);

	fetch('/ajax-pending').then(r => r.json())
		.then(r => r.map(e => li(`${e.name} by ${e.author} [${e.ethics.join(", ")}]`)))
		.then(r => {
			const p = document.getElementById('pending');
			r.forEach(e => p.appendChild(e));

			count += r.length;
			updateHint();
		}
	);
});
