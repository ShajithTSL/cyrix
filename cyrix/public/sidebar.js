// session_context_sidebar.js
//
// Adds a "session defaults" context chip (Company / Branch) to the desk
// workspace sidebar — pinned directly under the app/workspace switcher
// header and above the nav list.
//
// Verified against frappe/frappe@develop:
//   - sidebar.js fires "sidebar_setup" (on every workspace/route change)
//     and "sidebar-expand" (on collapse/expand) on `document`.
//   - sidebar_header.js removes + re-prepends `.sidebar-header` on every
//     re-render, so we anchor on the selector, not a fixed DOM index.
//   - user_settings_dialog.js exposes a "session-defaults" tab, opened via
//     frappe.ui.show_user_settings("session-defaults"), lazy-loaded through
//     the same bundle the core sidebar itself requires for the user menu.
//   - defaults.js's frappe.defaults.get_default(key) is the same call core
//     code (e.g. print_utils.js) uses to read the effective default.

(function () {
	// Which session-default fields to surface, in display order.
	// `icon` is any frappe.utils.icon() name (feather-style icon set).
	const CONTEXT_FIELDS = [
		{ fieldname: "company", label: __("Company"), icon: "building" },
		{ fieldname: "branch", label: __("Branch"), icon: "map-pin" },
	];

	function get_context_rows() {
		return CONTEXT_FIELDS.map((f) => ({
			...f,
			value: frappe.defaults.get_default(f.fieldname),
		})).filter((f) => !!f.value);
	}

	function open_session_defaults() {
		frappe.require("user_settings_dialog.bundle.js").then(() => {
			frappe.ui.show_user_settings("session-defaults");
		});
	}

	function build_chip() {
		const rows = get_context_rows();
		if (!rows.length) return null;

		const $chip = $(`
			<div class="session-context-chip" tabindex="0" role="button"
				aria-label="${__("Session Defaults: {0}", [
					rows.map((r) => r.value).join(", "),
				])}">
				<div class="session-context-icon">
					${frappe.utils.icon(rows[0].icon, "sm")}
				</div>
				<div class="session-context-text"></div>
				<div class="session-context-caret">
					${frappe.utils.icon("chevron-down", "xs")}
				</div>
			</div>
		`);

		const $text = $chip.find(".session-context-text");
		rows.forEach((row, i) => {
			$(`<span class="session-context-row session-context-row-${i === 0 ? "primary" : "secondary"}"></span>`)
				// .text() escapes for us — no need for a manual escape_html call
				.text(row.value)
				.attr("title", `${row.label}: ${row.value}`)
				.appendTo($text);
		});

		$chip.on("click", open_session_defaults);
		$chip.on("keydown", (e) => {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				open_session_defaults();
			}
		});

		return $chip;
	}

	function render() {
		const $sidebar = $(".body-sidebar");
		if (!$sidebar.length) return;

		// Drop any previous instance before re-inserting — render() can run
		// multiple times per navigation (sidebar_setup can fire more than
		// once while the sidebar resolves), so this keeps it idempotent.
		$sidebar.find(".session-context-chip").remove();

		const $chip = build_chip();
		if (!$chip) return;

		const $header = $sidebar.find(".sidebar-header");
		if ($header.length) {
			$chip.insertAfter($header);
		} else {
			// Fallback for a boot race where the header hasn't rendered yet.
			$chip.prependTo($sidebar.find(".body-sidebar-top"));
		}
	}

	$(document).on("sidebar_setup", render);
	$(document).on("sidebar-expand", render);
	// Covers the very first paint, before any workspace navigation has
	// happened to fire "sidebar_setup" yet.
	$(document).on("app_ready", render);
})();
