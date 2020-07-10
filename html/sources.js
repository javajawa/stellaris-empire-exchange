"use strict";

import { elemGenerator } from "https://javajawa.github.io/elems.js/elems.js";

const h3     = elemGenerator("h3");
const image  = elemGenerator("img");
const input  = elemGenerator("input");
const label  = elemGenerator("label");
const li     = elemGenerator("li");
const p      = elemGenerator("p");
const span   = elemGenerator("span");
const ul     = elemGenerator("ul");

const zone = document.getElementById("listings");
const opts = document.getElementById("sources");

let count = 0;
let authors = [];

fetch("/sources-list").then(r => r.json()).then(loadSources);

function updateHint() {
	document.getElementById("empire-count").textContent =
		count + " by " + authors.length + " authors.";
}

function showEmpire(e) {
	return li(
		e.ethics.map(ethic =>
			image({
				src: `/ethic/${ethic.replace(" ", "_")}.png`,
				width: 12, height: 12, alt: ethic, title: ethic,
				style: "margin: 0 1px;"
			})
		),
		" ",
		span(e.name, {"class": "highlight", "title": e.bio}),
		" by ",
		span(e.author, {"class": "highlight"})
	);
}

function handleSource(source, empires)
{
	if (!empires.length) {
		return;
	}

	zone.appendChild(h3(source.title));

	if (source.description)
	{
		zone.appendChild(p(source.description));
	}

	zone.appendChild(ul(empires.map(showEmpire)));


	opts.appendChild(li(
		input({
			id: "source-" + source.source,
			type: "checkbox",
			name: "sources",
			value: source.source
		}),
		label(
			{"for": "source-" + source.source, title: source.description},
			`${source.title} (${empires.length} "${source.source}")`
		)
	));

	count  += empires.length;
	authors = authors.concat(empires.map(e => e.author)).filter((v, k, s) => s.indexOf(v) === k);

	updateHint();
}

async function loadSources(sources)
{
	for (let source of sources)
	{
		console.log(source);
		const empires = await fetch("/ajax/" + source.source).then(r => r.json());

		handleSource(source, empires);
	}
}
