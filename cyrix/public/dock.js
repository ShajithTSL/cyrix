// session_context_dock.js  (Option C)
//
// Adds a small circular "Company/Branch" badge into the permanent workspace
// dock rail (the 50px icon strip at the far left of Desk), pinned just
// above the user-avatar button. Clicking it opens the built-in Session
// Defaults settings tab.
//
// Why the dock and not the body sidebar (Option A): per
// frappe/public/js/frappe/ui/sidebar/sidebar.js — "The workspace dock is
// always on. Apps can no longer opt out" — so a badge placed here is visible
// on every page, including while the body sidebar is collapsed. That makes
// it more robust than anchoring inside `.body-sidebar`, which can be hidden
// entirely (body.sidebar-collapsed) or rebuilt in ways that vary across
// builds/versions.
//
// This version deliberately does NOT depend on any custom document event
// (e.g. "sidebar_setup") firing under a specific name, since that's the
// most likely reason a previous version showed nothing on your instance —
// internal event names/timing can drift between Frappe builds. Instead it
// polls for the dock's own DOM (`.workspace-dock`), which is guaranteed to
// exist by the time anything is visible on screen, and self-heals if the
// badge ever gets removed by a dock re-render.

(function () {
	console.log("[session_context_dock] script loaded"); // first thing to check in DevTools console

	const FIELDS = [
		{ fieldname: "company", label: "Company" },
		{ fieldname: "branch", label: "Branch" },
	];
	const BADGE_CLASS = "session-context-dock-item";
	const DIVIDER_CLASS = "session-context-dock-divider";

	function get_rows() {
		if (!window.frappe || !frappe.defaults) return [];
		return FIELDS.map((f) => ({ ...f, value: frappe.defaults.get_default(f.fieldname) })).filter(
			(f) => !!f.value
		);
	}

	function initials(text) {
		return text
			.split(/\s+/)
			.filter(Boolean)
			.slice(0, 2)
			.map((w) => w[0].toUpperCase())
			.join("");
	}

	function open_session_defaults() {
		frappe.require("user_settings_dialog.bundle.js").then(() => {
			frappe.ui.show_user_settings("session-defaults");
		});
	}

	function build_badge(rows) {
		const tooltip = rows.map((r) => `${r.label}: ${r.value}`).join(" · ");
		const $badge = $(`
			<button type="button" class="workspace-dock-item ${BADGE_CLASS}"
				data-toggle="tooltip" data-placement="right"
				title="${frappe.utils.escape_html(tooltip)}"
				aria-label="${frappe.utils.escape_html(tooltip)}">
				<span class="session-context-initials">${frappe.utils.escape_html(
					initials(rows[0].value)
				)}</span>
			</button>
		`);
		$badge.on("click", open_session_defaults);
		return $badge;
	}

	function render() {
		const $dock = $(".workspace-dock");
		if (!$dock.length) return; // dock not created yet — polling will retry

		const rows = get_rows();
		const existing = $dock.find(`.${BADGE_CLASS}`);

		if (!rows.length) {
			existing.length && $(`.${BADGE_CLASS}, .${DIVIDER_CLASS}`).tooltip?.("dispose");
			$dock.find(`.${BADGE_CLASS}, .${DIVIDER_CLASS}`).remove();
			return;
		}

		const tooltip_text = rows.map((r) => `${r.label}: ${r.value}`).join(" · ");
		if (existing.length) {
			// values already shown and unchanged (or just refresh title/initials in place)
			existing.attr("title", tooltip_text).attr("aria-label", tooltip_text);
			existing.find(".session-context-initials").text(initials(rows[0].value));
			return;
		}

		const $user = $dock.find(".workspace-dock-user");
		const $divider = $(
			`<div class="workspace-dock-divider ${DIVIDER_CLASS}" role="separator"></div>`
		);
		const $badge = build_badge(rows);

		if ($user.length) {
			$divider.insertBefore($user);
			$badge.insertBefore($user);
		} else {
			$dock.append($divider, $badge);
		}

		$badge.tooltip({ boundary: "window", container: "body", trigger: "hover" });
	}

	// Cheap self-healing poll: handles the dock's lazy/async creation on cold
	// boot and re-inserts the badge if a dock re-render ever wipes it. A
	// plain interval avoids relying on any specific internal event name.
	setInterval(render, 800);
	$(document).ready(render);
})();
