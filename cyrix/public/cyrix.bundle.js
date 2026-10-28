frappe.views.ListView = class ListView extends frappe.views.ListView {
    refresh() {
		let fullwidth = JSON.parse(localStorage.container_fullwidth || "false");
		$(document.body).toggleClass("full-width", fullwidth);
        super.refresh();

        try {
            const default_company = frappe.defaults.get_default("company");
            if (!default_company || frappe.ignore_company) return;

            // ✅ Only apply logic if doctype has company field
            if (!frappe.meta.has_field(this.doctype, "company")) {
                return;
            }

            const company_input = this.page?.fields_dict?.company;

            if (company_input) {
                company_input.df.read_only = 1;
                company_input.refresh();
                company_input.set_input(default_company);
            }

            const exists = this.filter_area.get().some(
                f => f[1] === "company" && f[3] === default_company
            );

            if (!exists) {
                // this.filter_area.clear(true);
                this.filter_area.add([
                    [this.doctype, "company", "=", default_company]
                ]);

                this.on_filter_change();
                super.refresh();
            }

        } catch (e) {
            console.warn("Auto-company filter failed:", e);
        }
    }
};

frappe.ui.form.ControlAttach = class ControlAttach extends frappe.ui.form.ControlAttach {
    clear_attachment() {
		let me = this;
		if (this.frm) {
			me.parse_validate_and_set_in_model(null);
			me.refresh();
			me.frm.attachments.remove_attachment_by_filename(me.value, async () => {
				await me.parse_validate_and_set_in_model(null);
				me.refresh();
				// me.frm.doc.docstatus == 1 ? me.frm.save("Update") : me.frm.save();
			});
		} else {
			this.dataurl = null;
			this.fileobj = null;
			this.set_input(null);
			this.parse_validate_and_set_in_model(null);
			this.refresh();
		}
	}
    async on_upload_complete(attachment) {
		if (this.frm) {
			await this.parse_validate_and_set_in_model(attachment.file_url);
			this.frm.attachments.update_attachment(attachment);
			// this.frm.doc.docstatus == 1 ? this.frm.save("Update") : this.frm.save();
		}
		this.set_value(attachment.file_url);
	}
}
frappe.ui.form.ControlAttachImage = class ControlAttachImage extends frappe.ui.form.ControlAttach{
	make_input() {
		super.make_input();

		let $file_link = this.$value.find(".attached-file-link");
		$file_link.popover({
			trigger: "hover",
			placement: "top",
			content: () => {
				return `<div>
					<img src="${this.get_value()}"
						width="150px"
						style="object-fit: contain;"
					/>
				</div>`;
			},
			html: true,
		});
	}
	set_upload_options() {
		super.set_upload_options();
		this.upload_options.restrictions.allowed_file_types = ["image/*"];
	}
};

// Moves the Comments + Activity footer into the right sidebar,
// collapsed by default, on every DocType form.

$(document).on("form-refresh", function (e, frm) {
	// give Frappe a tick to finish rendering the footer
	setTimeout(() => move_activity_to_sidebar(frm), 200);
});
//comment and activity
const SKIP_DOCTYPES = ["User", "Print Format Builder","Evaluation Report"]; // add any you don't want touched

let $panel, $handle, $anchor;
let active_frm = null;

$(document).on("form-refresh", function (e, frm) {
	setTimeout(() => setup_activity_panel(frm), 200);
});

function setup_activity_panel(frm) {
	if (!frm || !frm.doc || frm.is_new() || frm.doc.__islocal
		|| SKIP_DOCTYPES.includes(frm.doctype)) {
		return hide_handle();
	}

	const $footer = frm.footer && frm.footer.wrapper;
	if (!$footer || !$footer.length) return hide_handle();

	// a different doc was opened while the panel was open
	if (active_frm && active_frm !== frm) close_panel();

	active_frm = frm;
	$footer.addClass("activity-hidden");

	build_panel();
	$handle.show();
}

function build_panel() {
	if ($panel) return;

	$handle = $(`
		<div class="activity-handle">
			<span>${__("Comments & Activity")}</span>
		</div>
	`).appendTo("body");

	$panel = $(`
		<div class="activity-panel">
			<div class="activity-panel-header">
				<span>${__("Comments & Activity")}</span>
				<span class="activity-panel-close">&times;</span>
			</div>
			<div class="activity-panel-body"></div>
		</div>
	`).appendTo("body");

	$handle.on("click", () => ($panel.hasClass("open") ? close_panel() : open_panel()));
	$panel.find(".activity-panel-close").on("click", close_panel);

	$(document).on("keydown.activity", (e) => {
		if (e.key === "Escape" && $panel.hasClass("open")) close_panel();
	});

	// put the footer back before Frappe tears the form down
	// on any navigation: stash the footer back, then hide the tab.
	// form-refresh will re-show it only if we land on a real form.
	frappe.router.on("change", () => {
		close_panel();
		if ($handle) $handle.hide();
		active_frm = null;
	});
}

function open_panel() {
	if (!active_frm || !active_frm.footer) return;

	const $footer = active_frm.footer.wrapper;
	$anchor = $('<div class="activity-anchor"></div>');
	$footer.after($anchor);

	$panel.find(".activity-panel-body").append($footer.removeClass("activity-hidden"));
	$panel.addClass("open");
	$handle.addClass("open");

	hide_view_logs($panel);
	setTimeout(() => hide_view_logs($panel), 600);   // timeline loads lazily
}

function close_panel() {
	if (!$panel || !$panel.hasClass("open")) return;

	const $footer = $panel.find(".form-footer");
	if ($anchor && $anchor.length && $footer.length) {
		$anchor.replaceWith($footer.addClass("activity-hidden"));
	}
	$anchor = null;

	$panel.removeClass("open");
	$handle.removeClass("open");
}

function hide_handle() {
	close_panel();
	active_frm = null;
	if ($handle) $handle.hide();
}

function hide_view_logs($ctx) {
	$ctx.find(".timeline-item").each(function () {
		if (/viewed this/i.test($(this).find(".timeline-content").text() || "")) {
			$(this).hide();
		}
	});
}

frappe.dom.set_style(`
	.form-footer.activity-hidden { display: none !important; }

	.activity-handle {
		position: fixed;
		right: 0;
		top: 45%;
		z-index: 1035;
		display: none;
		writing-mode: vertical-rl;
		padding: 14px 7px;
		background: var(--fg-color);
		border: 1px solid var(--border-color);
		border-right: none;
		border-radius: var(--border-radius) 0 0 var(--border-radius);
		box-shadow: var(--shadow-base);
		font-size: var(--text-sm);
		font-weight: 500;
		cursor: pointer;
		user-select: none;
		transition: right 0.25s ease;
	}
	.activity-handle:hover { background: var(--bg-color); }
	.activity-handle.open { right: 440px; }

	.activity-panel {
		position: fixed;
		top: 0;
		right: -460px;
		width: 440px;
		height: 100vh;
		z-index: 1034;
		background: var(--fg-color);
		border-left: 1px solid var(--border-color);
		box-shadow: -2px 0 12px rgba(0,0,0,0.08);
		display: flex;
		flex-direction: column;
		transition: right 0.25s ease;
	}
	.activity-panel.open { right: 0; }

	.activity-panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 14px 16px;
		border-bottom: 1px solid var(--border-color);
		font-weight: 600;
	}
	.activity-panel-close { cursor: pointer; font-size: 22px; line-height: 1; opacity: 0.6; }
	.activity-panel-close:hover { opacity: 1; }

	.activity-panel-body { flex: 1; overflow-y: auto; padding: 12px 16px; }
	.activity-panel-body .form-footer { padding: 0; border: none; margin: 0; }
	.activity-panel-body .comment-box .frappe-control { width: 100%; }
	.activity-panel-body .new-timeline { padding-left: 0; }

	@media (max-width: 991px) {
		.activity-panel { width: 100%; right: -100%; }
		.activity-handle.open { right: 0; }
	}
`);

/* =====================================================================
   Company + Branch: navbar buttons + sidebar bottom block (v16)
   Includes CSS directly inside this JS file.
   Opens Session Defaults (frappe.ui.toolbar.setup_session_defaults),
   labels reflect current session-default values, re-mounts on route change.
   ===================================================================== */

/* =====================================================================
   COMPANY + BRANCH — FRAPPE / ERPNEXT V16
   ===================================================================== */

(function () {

    "use strict";

    /* Prevent duplicate loading */
    if (window.__mtv16_company_branch_loaded) {
        return;
    }

    window.__mtv16_company_branch_loaded = true;


    /* =================================================================
       CSS
       ================================================================= */

    function injectCSS() {

        if (document.getElementById("mtv16-company-css")) {
            return;
        }

        var style = document.createElement("style");

        style.id = "mtv16-company-css";

        style.textContent = `

        /* =============================================================
           NAVBAR COMPANY / BRANCH BUTTONS
           ============================================================= */

        #mtv16-company-btn,
        #mtv16-branch-btn {

            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: #2490ef !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 6px 14px !important;
            margin-right: 5px !important;
            font-size: 13px !important;
            font-weight: 550 !important;
            line-height: 1 !important;
            white-space: nowrap !important;
            cursor: pointer !important;
            visibility: visible !important;
            opacity: 1 !important;
            box-shadow: 0 2px 8px rgba(36, 144, 239, 0.20) !important;
        }

        #mtv16-company-btn:hover,
        #mtv16-branch-btn:hover {
            background: #1677cb !important;
            color: #ffffff !important;
        }

        #mtv16-company-btn .company-label,
        #mtv16-branch-btn .company-label {
            color: #ffffff !important;
        }


        /* =============================================================
           SIDEBAR ORGANIZATION BLOCK
           IMPORTANT:
           Do NOT position this absolutely.
           Let Frappe control the sidebar layout.
           ============================================================= */

        #mtv16-sidebar-org {

            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            box-sizing: border-box !important;
            width: calc(100% - 20px) !important;
            margin: 8px 10px !important;
            padding: 8px 10px !important;
            min-height: 46px !important;
            border-radius: 10px !important;
            cursor: pointer !important;
            background: #f8fafc !important;
            border: 1px solid #d9e1ea !important;
            color: #1f2937 !important;
            visibility: visible !important;
            opacity: 1 !important;
            flex-shrink: 0 !important;
            transition:
                background-color 150ms ease,
                border-color 150ms ease !important;
        }

        #mtv16-sidebar-org:hover {
            background: #eef6ff !important;
            border-color: #2490ef !important;
        }


        /* =============================================================
           COMPANY BADGE
           ============================================================= */

        #mtv16-sidebar-org .mtv16-org-badge {

            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 30px !important;
            height: 30px !important;
            min-width: 30px !important;
            max-width: 30px !important;
            flex: 0 0 30px !important;
            border-radius: 8px !important;
            background: #2490ef !important;
            color: #ffffff !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            line-height: 1 !important;
            visibility: visible !important;
            opacity: 1 !important;
        }


        /* =============================================================
           TEXT
           ============================================================= */

        #mtv16-sidebar-org .mtv16-org-text {
            display: block !important;
            min-width: 0 !important;
            flex: 1 1 auto !important;
            overflow: hidden !important;
        }

        #mtv16-sidebar-org .mtv16-org-company {
            display: block !important;
            width: 100% !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            line-height: 18px !important;
            color: #1f2937 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        #mtv16-sidebar-org .mtv16-org-branch {
            display: block !important;
            width: 100% !important;
            margin-top: 1px !important;
            font-size: 11px !important;
            line-height: 15px !important;
            color: #64748b !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }


        /* =============================================================
           DARK MODE
           ============================================================= */

        [data-theme="dark"] #mtv16-sidebar-org {
            background: #1e293b !important;
            border-color: #334155 !important;
            color: #ffffff !important;
        }

        [data-theme="dark"] #mtv16-sidebar-org:hover {
            background: #26364a !important;
            border-color: #2490ef !important;
        }

        [data-theme="dark"] #mtv16-sidebar-org .mtv16-org-company {
            color: #f1f5f9 !important;
        }

        [data-theme="dark"] #mtv16-sidebar-org .mtv16-org-branch {
            color: #94a3b8 !important;
        }


        /* =============================================================
           COLLAPSED SIDEBAR — center org block under the avatar

           Two selectors:
             .body-sidebar.collapsed  -> Frappe's own collapsed class
             .mtv16-collapsed         -> our JS-added fallback class
           ============================================================= */

        .body-sidebar.collapsed #mtv16-sidebar-org,
        #mtv16-sidebar-org.mtv16-collapsed {

            width: 38px !important;
            min-width: 38px !important;
            max-width: 38px !important;
            padding: 4px !important;

            /* center horizontally instead of pinning to the left */
            margin: 8px auto !important;

            gap: 0 !important;
            justify-content: center !important;
            align-self: center !important;
        }

        .body-sidebar.collapsed #mtv16-sidebar-org .mtv16-org-text,
        #mtv16-sidebar-org.mtv16-collapsed .mtv16-org-text {
            display: none !important;
        }

        .body-sidebar.collapsed #mtv16-sidebar-org .mtv16-org-badge,
        #mtv16-sidebar-org.mtv16-collapsed .mtv16-org-badge {
            width: 28px !important;
            height: 28px !important;
            min-width: 28px !important;
            max-width: 28px !important;
            margin: 0 auto !important;
            border-radius: 8px !important;
            font-size: 10px !important;
        }


        /* =============================================================
           WHEN SIDEBAR IS OPEN — explicitly restore everything.
           ============================================================= */

        .body-sidebar:not(.collapsed) #mtv16-sidebar-org:not(.mtv16-collapsed) {
            width: calc(100% - 20px) !important;
            min-width: 0 !important;
            max-width: none !important;
            padding: 8px 10px !important;
            margin: 8px 10px !important;
            gap: 10px !important;
            justify-content: flex-start !important;
        }

        .body-sidebar:not(.collapsed) #mtv16-sidebar-org:not(.mtv16-collapsed) .mtv16-org-text {
            display: block !important;
        }

        .body-sidebar:not(.collapsed) #mtv16-sidebar-org:not(.mtv16-collapsed) .mtv16-org-badge {
            width: 30px !important;
            height: 30px !important;
            min-width: 30px !important;
            max-width: 30px !important;
        }


        /* =============================================================
           NAVBAR SEARCH
           ============================================================= */

        .navbar input[type="text"],
        .navbar #navbar-search,
        #navbar-search {
            padding-left: 40px !important;
        }

        `;

        document.head.appendChild(style);
    }


    /* =================================================================
       GET SESSION DEFAULT
       ================================================================= */

    function getDefault(key) {

        try {

            var value = "";

            if (
                frappe.defaults &&
                typeof frappe.defaults.get_default === "function"
            ) {
                value = frappe.defaults.get_default(key);
            }

            if (!value && frappe.boot && frappe.boot.user_defaults) {
                value = frappe.boot.user_defaults[key];
            }

            if (Array.isArray(value)) {
                value = value[0];
            }

            return value || "";

        } catch (e) {
            return "";
        }
    }


    /* =================================================================
       INITIALS
       ================================================================= */

    function getInitials(value) {

        if (!value) {
            return "?";
        }

        return value
            .trim()
            .split(/[\s\-\u00b7]+/)
            .filter(Boolean)
            .slice(0, 2)
            .map(function (word) {
                return word.charAt(0);
            })
            .join("")
            .toUpperCase();
    }


    /* =================================================================
       OPEN SESSION DEFAULTS
       ================================================================= */

    function openDefaults() {

        try {
            if (
                frappe.ui &&
                frappe.ui.toolbar &&
                typeof frappe.ui.toolbar.setup_session_defaults === "function"
            ) {
                frappe.ui.toolbar.setup_session_defaults();
            }
        } catch (e) {}

        /* Refresh after Frappe saves the new defaults. */
        setTimeout(refreshValues, 500);
        setTimeout(refreshValues, 1200);
        setTimeout(refreshValues, 2000);
    }


    /* =================================================================
       CREATE NAVBAR BUTTON
       ================================================================= */

    function createButton(id, label) {

        var button = document.createElement("button");
        button.id = id;
        button.type = "button";
        button.className = "company-btn company-alert";

        var span = document.createElement("span");
        span.className = "company-label";
        span.textContent = label;

        button.appendChild(span);
        button.addEventListener("click", openDefaults);

        return button;
    }


    /* =================================================================
       BUILD NAVBAR
       ================================================================= */

    function buildNavbar() {

        var bar = document.querySelector(".desktop-navbar");
        if (!bar) {
            return false;
        }

        var host = bar.querySelector(".navbar-right");
        if (!host) {
            host = bar.lastElementChild;
        }
        if (!host) {
            return false;
        }

        /* Branch */
        if (!document.getElementById("mtv16-branch-btn")) {
            var branchButton = createButton(
                "mtv16-branch-btn",
                getDefault("branch") || "Select Branch"
            );
            host.insertBefore(branchButton, host.firstChild);
        }

        /* Company */
        if (!document.getElementById("mtv16-company-btn")) {
            var companyButton = createButton(
                "mtv16-company-btn",
                getDefault("company") || "Select Company"
            );
            host.insertBefore(companyButton, host.firstChild);
        }

        return true;
    }


    /* =================================================================
       BUILD SIDEBAR
       ================================================================= */

    function buildSidebar() {

        var sidebar = document.querySelector(".body-sidebar");
        if (!sidebar) {
            return false;
        }

        var block = document.getElementById("mtv16-sidebar-org");
        if (block) {
            return true;
        }

        block = document.createElement("div");
        block.id = "mtv16-sidebar-org";

        block.innerHTML = `
            <div class="mtv16-org-badge"></div>
            <div class="mtv16-org-text">
                <div class="mtv16-org-company"></div>
                <div class="mtv16-org-branch"></div>
            </div>
        `;

        block.title = "Change Company / Branch";
        block.addEventListener("click", openDefaults);

        /* Find Frappe's sidebar footer/user section. */
        var footer = sidebar.querySelector(".sidebar-footer");
        if (!footer) {
            footer = sidebar.querySelector('[class*="sidebar-footer"]');
        }
        if (!footer) {
            footer = sidebar.querySelector(".body-sidebar-footer");
        }

        /* Put organization block immediately before footer. */
        if (footer && footer.parentNode === sidebar) {
            sidebar.insertBefore(block, footer);
        } else {
            sidebar.appendChild(block);
        }

        return true;
    }


    /* =================================================================
       REFRESH VALUES
       ================================================================= */

    function refreshValues() {

        var company = getDefault("company") || "Select Company";
        var branch  = getDefault("branch")  || "Select Branch";

        var companyLabel = document.querySelector("#mtv16-company-btn .company-label");
        if (companyLabel) {
            companyLabel.textContent = company;
        }

        var branchLabel = document.querySelector("#mtv16-branch-btn .company-label");
        if (branchLabel) {
            branchLabel.textContent = branch;
        }

        var sidebarCompany = document.querySelector("#mtv16-sidebar-org .mtv16-org-company");
        if (sidebarCompany) {
            sidebarCompany.textContent = company;
        }

        var sidebarBranch = document.querySelector("#mtv16-sidebar-org .mtv16-org-branch");
        if (sidebarBranch) {
            sidebarBranch.textContent = branch;
        }

        var badge = document.querySelector("#mtv16-sidebar-org .mtv16-org-badge");
        if (badge) {
            badge.textContent = getInitials(company);
        }
    }


    /* =================================================================
       COLLAPSE STATE — keep our block centered when collapsed
       ================================================================= */

    function markCollapse() {

        var sidebar = document.querySelector(".body-sidebar");
        var block   = document.getElementById("mtv16-sidebar-org");

        if (!sidebar || !block) {
            return;
        }

        var collapsed =
            sidebar.classList.contains("collapsed") ||
            (sidebar.offsetWidth > 0 && sidebar.offsetWidth < 100);

        block.classList.toggle("mtv16-collapsed", collapsed);
    }

    function watchCollapse() {

        var sidebar = document.querySelector(".body-sidebar");

        if (!sidebar) {
            setTimeout(watchCollapse, 500);
            return;
        }

        markCollapse();

        try {
            new MutationObserver(markCollapse).observe(sidebar, {
                attributes: true,
                attributeFilter: ["class", "style"]
            });
        } catch (e) {}

        window.addEventListener("resize", markCollapse);

        /* re-check right after the user clicks the collapse toggle */
        document.addEventListener("click", function () {
            setTimeout(markCollapse, 50);
            setTimeout(markCollapse, 300);
        });
    }


    /* =================================================================
       BUILD EVERYTHING
       ================================================================= */

    function build() {
        injectCSS();
        buildNavbar();
        buildSidebar();
        refreshValues();
        markCollapse();
    }


    /* =================================================================
       INITIALIZE
       ================================================================= */

    function initialize() {

        build();
        watchCollapse();

        /* Frappe creates some sidebar elements slightly later. */
        setTimeout(build, 300);
        setTimeout(build, 800);
        setTimeout(build, 1500);
    }


    /* =================================================================
       INITIAL LOAD
       ================================================================= */

    if (
        typeof frappe !== "undefined" &&
        typeof frappe.after_ajax === "function"
    ) {
        frappe.after_ajax(initialize);
    } else if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }


    /* =================================================================
       ROUTE CHANGE
       ================================================================= */

    try {
        if (frappe.router && typeof frappe.router.on === "function") {
            frappe.router.on("change", function () {
                setTimeout(function () {
                    if (
                        !document.getElementById("mtv16-company-btn") ||
                        !document.getElementById("mtv16-sidebar-org")
                    ) {
                        build();
                    } else {
                        refreshValues();
                        markCollapse();
                    }
                }, 300);
            });
        }
    } catch (e) {}


    /* =================================================================
       PAGE CHANGE
       ================================================================= */

    document.addEventListener("page-change", function () {
        setTimeout(function () {
            if (!document.getElementById("mtv16-sidebar-org")) {
                build();
            } else {
                refreshValues();
                markCollapse();
            }
        }, 300);
    });

})();

(() => {
    function hide_kw_dashboard() {
        const current_user = (frappe.session.user || "").trim().toLowerCase();

        if (current_user === "info@cyrix-tsl.com") {
            $(".sidebar-item-label").filter(function () {
                return $(this).text().trim() === "KW Dashboard";
            }).each(function () {
                $(this).closest("a").show();
            });

            return;
        }

        $(".sidebar-item-label").filter(function () {
            return $(this).text().trim() === "KW Dashboard";
        }).each(function () {
            $(this).closest("a").hide();
        });
    }

    hide_kw_dashboard();

    new MutationObserver(hide_kw_dashboard).observe(document.body, {
        childList: true,
        subtree: true
    });
})();

/**
 * Grouped List View + Quick View for every DocType — Frappe / ERPNext v15
 * Single file: styles are injected by this script (no separate CSS needed).
 *
 * hooks.py:   app_include_js = ["/assets/<your_app>/js/grouped_list_view.js"]
 *
 * Optional per-DocType tuning:
 *   frappe.listview_settings["Work Order Data"] = Object.assign(frappe.listview_settings["Work Order Data"] || {}, {
 *     grouped_view: {
 *       field: "status",            // default group-by field
 *       default: true,              // open grouped by default
 *       fields: ["customer", "sales_rep", "technician", "priority_status"], // popup summary fields, in order
 *       quick_view: true,           // false = ID click opens the form as usual
 *       disable: false,             // true = feature off for this DocType
 *     },
 *   });
 */
(() => {
	if (!window.frappe || !frappe.views || !frappe.views.ListView) return;

	const GV = frappe.provide("grouped_view");
	GV.config = {
		exclude_doctypes: ["File", "DocType", "Report", "Page", "Workspace", "Error Log", "Version", "Comment"],
		quick_view: true,
		summary_fields: 8,
		max_child_rows: 50,
	};

	const SKIP = new Set(["Section Break", "Column Break", "Tab Break", "HTML", "Button", "Fold", "Heading", "Table",
		"Table MultiSelect", "Password", "Signature", "Geolocation", "HTML Editor", "Code", "JSON"]);
	const LONG = new Set(["Text Editor", "Small Text", "Text", "Long Text", "Markdown Editor"]);
	const NUMERIC = new Set(["Int", "Float", "Currency", "Percent"]);
	const COLORS = ["blue", "orange", "purple", "green", "yellow", "pink", "cyan", "red", "gray"];
	const esc = (v) => frappe.utils.escape_html(v == null ? "" : String(v));

	/* ============================== styles ============================== */
	const CSS = `
.gv-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 15px;margin:0 0 4px;border-bottom:1px solid var(--border-color);font-size:var(--text-sm)}
.gv-bar .gv-label{color:var(--text-muted);white-space:nowrap}
.gv-bar select.gv-field{display:inline-block;width:auto;min-width:180px;max-width:260px;height:28px;padding:2px 28px 2px 10px;font-size:var(--text-sm)}
.gv-bar .btn{white-space:nowrap}
.gv-bar .gv-spacer{flex:1}
.gv-bar .gv-hint{color:var(--text-light);white-space:nowrap}
@media(max-width:768px){.gv-bar .gv-hint{display:none}}
.frappe-list .gv-group-head{grid-column:1/-1;position:sticky;left:0;z-index:1;box-sizing:border-box;width:100%;display:flex;align-items:center;gap:10px;padding:9px 15px;background:var(--subtle-fg);border-top:1px solid var(--border-color);border-bottom:1px solid var(--border-color);cursor:pointer;user-select:none}
.frappe-list .gv-group-head:hover{background:var(--fg-hover-color)}
.frappe-list .gv-group-head:focus-visible{outline:2px solid var(--primary);outline-offset:-2px}
.gv-caret{flex:none;width:7px;height:7px;border-right:1.5px solid var(--text-muted);border-bottom:1.5px solid var(--text-muted);transform:rotate(45deg) translate(-2px,-2px);transition:transform .15s}
.gv-collapsed .gv-caret{transform:rotate(-45deg)}
.gv-group-head .indicator-pill{font-weight:500}
.gv-count{color:var(--text-muted);font-size:var(--text-sm);font-variant-numeric:tabular-nums}

.frappe-list .gv-more-row{grid-column:1/-1;position:sticky;left:0;box-sizing:border-box;width:100%;background:var(--fg-color);display:flex;align-items:center;gap:8px;padding:8px 15px 10px;border-bottom:1px solid var(--border-color)}
.frappe-list .gv-more-row[hidden]{display:none}
.frappe-list .gv-hide{display:none!important}
.gv-more-row .gv-rem{color:var(--text-muted);font-size:var(--text-sm)}

body.gv-peek-lock{overflow:hidden}
.gv-peek-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.28);z-index:1035;opacity:0;pointer-events:none;transition:opacity .2s}
.gv-peek-backdrop.open{opacity:1;pointer-events:auto}
.gv-peek{position:fixed;top:8px;right:8px;bottom:8px;width:min(800px,calc(100vw - 16px));background:var(--modal-bg,var(--fg-color));color:var(--text-color);border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,.08),0 18px 48px rgba(0,0,0,.22);z-index:1036;display:flex;flex-direction:column;outline:none;
  visibility:hidden;transform:translateX(calc(100% + 16px));transition:transform .22s ease,opacity .2s ease,top .2s ease,left .2s ease,right .2s ease,bottom .2s ease,width .2s ease,visibility 0s linear .22s}
.gv-peek.open{visibility:visible;transform:none;transition:transform .22s ease,opacity .2s ease,top .2s ease,left .2s ease,right .2s ease,bottom .2s ease,width .2s ease,visibility 0s}
.gv-peek[data-layout="modal"]{top:5vh;bottom:auto;max-height:90vh;left:calc(50% - min(440px,50vw - 16px));right:auto;width:min(880px,calc(100vw - 32px));transform:translateY(12px) scale(.98);opacity:0}
.gv-peek[data-layout="modal"].open{transform:none;opacity:1}
.gv-peek[data-layout="modal"] .gv-peek-tabs{display:none}
.gv-peek[data-layout="modal"] .gv-peek-head{padding-bottom:12px;border-bottom:1px solid var(--border-color)}
.gv-peek[data-layout="modal"] .gv-peek-body{padding:16px 20px 20px}
@media(prefers-reduced-motion:reduce){.gv-peek,.gv-peek.open,.gv-peek-backdrop{transition:none}}
@media(max-width:640px){.gv-peek,.gv-peek[data-layout]{top:0;left:0;right:0;bottom:0;width:100vw;border-radius:0}.gv-layout-btn{display:none!important}}
.gv-peek-head{position:relative;display:flex;align-items:center;gap:12px;padding:14px 16px 6px}
.gv-layout-pop{position:absolute;top:46px;right:12px;z-index:3;display:flex;gap:6px;padding:10px;background:var(--modal-bg,var(--fg-color));border:1px solid var(--border-color);border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,.08),0 12px 32px rgba(0,0,0,.16)}
.gv-layout-pop[hidden]{display:none}
.gv-lopt{display:flex;flex-direction:column;align-items:center;gap:7px;padding:8px;border:1px solid transparent;border-radius:9px;background:none;color:var(--text-muted);font-size:var(--text-sm);cursor:pointer}
.gv-lopt:hover{background:var(--subtle-fg);color:var(--text-color)}
.gv-lopt[aria-checked="true"]{background:var(--bg-green);color:var(--text-on-green);border-color:var(--bg-green)}
.gv-lthumb{position:relative;width:78px;height:50px;border-radius:6px;border:1px solid var(--border-color);background:var(--subtle-fg);overflow:hidden}
.gv-lthumb::before{content:"";position:absolute;top:4px;left:5px;width:14px;height:3px;border-radius:2px;background:linear-gradient(90deg,#ff6159 0 3px,transparent 3px 5.5px,#ffbd2e 5.5px 8.5px,transparent 8.5px 11px,#28c941 11px 14px)}
.gv-lthumb i{position:absolute;border-radius:3px;background:var(--text-muted);opacity:.35}
.gv-lthumb.modal i{left:14px;right:14px;top:12px;bottom:6px}
.gv-lthumb.sidebar i{right:4px;top:11px;bottom:4px;width:42%}
.gv-lopt[aria-checked="true"] .gv-lthumb{border-color:currentColor}
.gv-lopt[aria-checked="true"] .gv-lthumb i{background:currentColor;opacity:.5}
.gv-peek-crumb{display:flex;align-items:center;gap:6px;min-width:0;flex:1;font-size:var(--text-lg);line-height:1.3}
.gv-peek-crumb .gv-dt{color:var(--text-muted);white-space:nowrap}
.gv-peek-crumb .gv-sep{color:var(--text-light)}
.gv-peek-crumb .gv-nm{font-weight:600;color:var(--heading-color);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gv-peek-crumb .indicator-pill{flex:none}
.gv-peek-actions{display:flex;align-items:center;gap:2px;flex:none}
.gv-peek-nav{display:inline-flex;align-items:center;gap:2px;margin-right:6px;color:var(--text-muted);font-size:var(--text-sm);font-variant-numeric:tabular-nums}
.gv-peek-nav[hidden]{display:none}
.gv-ibtn{display:inline-grid;place-items:center;width:28px;height:28px;border:0;border-radius:6px;background:none;color:var(--text-muted);cursor:pointer;padding:0}
.gv-ibtn:hover{background:var(--fg-hover-color,var(--subtle-fg));color:var(--text-color)}
.gv-ibtn[disabled]{opacity:.35;cursor:default;background:none}
.gv-ibtn svg{width:16px;height:16px}
.gv-peek-tabs{display:flex;gap:22px;padding:0 16px;border-bottom:1px solid var(--border-color);overflow-x:auto;scrollbar-width:none}
.gv-peek-tabs::-webkit-scrollbar{display:none}
.gv-tab{border:0;background:none;padding:10px 0 9px;color:var(--text-muted);font-size:var(--text-base);white-space:nowrap;cursor:pointer;border-bottom:1px solid transparent;margin-bottom:-1px}
.gv-tab:hover{color:var(--text-color)}
.gv-tab[aria-selected="true"]{color:var(--text-color);border-bottom-color:var(--text-color);font-weight:500}
.gv-tab .gv-badge{margin-left:5px;font-size:var(--text-xs);color:var(--text-muted)}
.gv-peek-body{flex:1;overflow-y:auto;padding:20px 16px 28px;overscroll-behavior:contain}
.gv-loading{padding:60px 0;text-align:center;color:var(--text-muted)}
.gv-ps{padding:0 0 22px;margin:0 0 20px;border-bottom:1px solid var(--border-color)}
.gv-ps:last-child{border-bottom:0;margin-bottom:0}
.gv-ps-title{font-size:var(--text-base);font-weight:600;margin:0 0 14px;color:var(--heading-color)}
.gv-pcols{display:grid;grid-template-columns:repeat(var(--cols),minmax(0,1fr));gap:0 16px}
@media(max-width:640px){.gv-pcols{grid-template-columns:minmax(0,1fr)}}
.gv-pcol{display:flex;flex-direction:column;gap:14px;min-width:0}
.gv-pl{font-size:var(--text-sm);color:var(--text-color);margin-bottom:5px;line-height:1.3}
.gv-req{color:var(--red-500,#e24c4c);margin-left:2px}
.gv-pv{background:var(--control-bg);border-radius:var(--border-radius);padding:6px 9px;min-height:30px;font-size:var(--text-sm);line-height:1.45;overflow-wrap:anywhere;color:var(--text-color)}
.gv-pv.gv-ro{color:var(--text-muted)}
.gv-pv.gv-bold{font-weight:600}
.gv-pv.gv-long{white-space:pre-line;max-height:180px;overflow-y:auto}
.gv-pv a{color:inherit}
.gv-pcheck{display:flex;align-items:center;gap:8px;font-size:var(--text-sm);padding:4px 0}
.gv-cb{flex:none;width:14px;height:14px;border-radius:4px;border:1px solid var(--gray-400,#c0c6cc);background:var(--fg-color);display:grid;place-items:center}
.gv-cb.on{background:var(--primary,#171717);border-color:var(--primary,#171717)}
.gv-cb.on::after{content:"";width:7px;height:4px;border-left:1.5px solid #fff;border-bottom:1.5px solid #fff;transform:rotate(-45deg) translate(1px,-1px)}
.gv-thumb{width:64px;height:64px;object-fit:cover;border-radius:6px;display:block}
.gv-ptable{margin-top:16px;border:1px solid var(--border-color);border-radius:var(--border-radius-md,8px)}
.gv-ptable>summary{list-style:none;cursor:pointer;padding:10px 12px;font-size:var(--text-sm);font-weight:600;display:flex;align-items:center;gap:8px}
.gv-ptable>summary::-webkit-details-marker{display:none}
.gv-ptable>summary::before{content:"";width:7px;height:7px;border-right:1.5px solid var(--text-muted);border-bottom:1.5px solid var(--text-muted);transform:rotate(-45deg);transition:transform .15s}
.gv-ptable[open]>summary::before{transform:rotate(45deg)}
.gv-ptable .gv-muted{font-weight:400;color:var(--text-muted)}
.gv-table-wrap{overflow-x:auto;border-top:1px solid var(--border-color)}
.gv-table{width:100%;border-collapse:collapse;font-size:var(--text-sm)}
.gv-table th{font-weight:500;color:var(--text-muted);background:var(--subtle-fg);text-align:left;padding:7px 10px;white-space:nowrap;border-bottom:1px solid var(--border-color)}
.gv-table td{padding:8px 10px;border-bottom:1px solid var(--border-color);vertical-align:top}
.gv-table tr:last-child td{border-bottom:0}
.gv-table .gv-n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.gv-table .gv-idx{color:var(--text-muted);width:34px}
.gv-table-more{padding:8px 12px;font-size:var(--text-xs);color:var(--text-muted);border-top:1px solid var(--border-color)}
.gv-activity{list-style:none;margin:0;padding:0}
.gv-activity li{display:grid;grid-template-columns:22px 1fr auto;gap:10px;align-items:start;padding:9px 0;font-size:var(--text-sm);color:var(--text-muted);border-bottom:1px solid var(--border-color)}
.gv-activity li:last-child{border-bottom:0}
.gv-activity b{color:var(--text-color);font-weight:500}
.gv-activity .gv-when{white-space:nowrap;font-size:var(--text-xs);padding-top:1px}
.gv-files{display:flex;flex-direction:column;gap:6px;font-size:var(--text-sm)}
.gv-empty-note{color:var(--text-muted);font-size:var(--text-sm)}
.gv-card{border:1px solid var(--border-color);border-radius:var(--border-radius-md,8px);padding:14px 16px;margin-bottom:14px}
.gv-card:last-child{margin-bottom:0}
.gv-card-title{font-size:var(--text-sm);font-weight:600;margin:0 0 12px;display:flex;align-items:center;gap:8px}
.gv-muted{color:var(--text-muted);font-weight:400}
.gv-meta-line{color:var(--text-muted);font-size:var(--text-sm);margin:0 0 14px}
.gv-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px 20px}
@media(max-width:820px){.gv-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.gv-f{min-width:0}
.gv-f.gv-wide{grid-column:1/-1}
.gv-k{font-size:var(--text-xs);color:var(--text-muted);margin-bottom:2px}
.gv-v{font-weight:500;overflow-wrap:anywhere;line-height:1.4}
.gv-v a{color:inherit}
.gv-clamp{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;white-space:pre-line;font-weight:400}
.gv-clamp.open{display:block}
.gv-link-btn{border:0;background:none;padding:2px 0 0;color:var(--text-muted);font-size:var(--text-xs);cursor:pointer}
.gv-link-btn:hover{color:var(--text-color)}
details.gv-card>summary{list-style:none;cursor:pointer;font-size:var(--text-sm);font-weight:600;display:flex;align-items:center;gap:8px}
details.gv-card>summary::-webkit-details-marker{display:none}
details.gv-card>summary::before{content:"";width:7px;height:7px;border-right:1.5px solid var(--text-muted);border-bottom:1.5px solid var(--text-muted);transform:rotate(-45deg);transition:transform .15s}
details.gv-card[open]>summary::before{transform:rotate(45deg)}
details.gv-card[open]>summary{margin-bottom:12px}
details.gv-card .gv-table-wrap{margin:0 -16px -14px}
.gv-section-label{font-size:var(--text-xs);color:var(--text-muted);font-weight:600;margin:16px 0 8px;padding-top:12px;border-top:1px dashed var(--border-color)}
.gv-section-label:first-child{border-top:0;padding-top:0;margin-top:0}
`;
	if (!document.getElementById("gv-style")) $("<style id='gv-style'>").text(CSS).appendTo("head");

	/* ============================== settings ============================== */
	GV._cache = {};
	GV.lv_settings = (dt) => (frappe.listview_settings[dt] && frappe.listview_settings[dt].grouped_view) || {};
	GV.enabled_for = (dt) => !GV.config.exclude_doctypes.includes(dt) && GV.lv_settings(dt).disable !== true;
	GV.get = (dt) => {
		if (!GV._cache[dt]) {
			const us = (frappe.get_user_settings && frappe.get_user_settings(dt)) || {};
			GV._cache[dt] = Object.assign({}, us.grouped_view || {});
		}
		return GV._cache[dt];
	};
	GV.set = (dt, patch) => {
		const s = Object.assign(GV.get(dt), patch);
		try { frappe.model.user_settings.save(dt, "grouped_view", s); } catch (e) { /* ignore */ }
		return s;
	};

	/* ============================== grouping helpers ============================== */
	GV.candidates = (dt) => {
		const meta = frappe.get_meta(dt);
		if (!meta) return [];
		const out = [];
		if (meta.is_submittable) out.push({ fieldname: "docstatus", label: __("Document Status"), fieldtype: "_docstatus" });
		meta.fields.forEach((df) => { if (["Select", "Link"].includes(df.fieldtype) && !df.hidden && !df.is_virtual) out.push(df); });
		return out;
	};
	GV.default_field = (dt) => {
		const pref = GV.lv_settings(dt).field;
		if (pref) return pref;
		const c = GV.candidates(dt);
		try {
			if (frappe.model.has_workflow(dt)) {
				const wf = frappe.workflow.get_state_fieldname(dt);
				if (c.some((d) => d.fieldname === wf)) return wf;
			}
		} catch (e) { /* ignore */ }
		const p = c.find((d) => d.fieldname === "status") || c.find((d) => d.fieldtype === "Select") || c[0];
		return p && p.fieldname;
	};
	GV.group_order = (dt, field, keys) => {
		if (field === "docstatus") return ["0", "1", "2"].filter((k) => keys.includes(k));
		const df = frappe.meta.get_docfield(dt, field);
		const order = df && df.fieldtype === "Select" ? (df.options || "").split("\n").map((s) => s.trim()).filter(Boolean) : [];
		const rest = keys.filter((k) => !order.includes(k)).sort((a, b) => (a === "" ? 1 : b === "" ? -1 : a.localeCompare(b)));
		return order.filter((k) => keys.includes(k)).concat(rest);
	};
	GV.label = (field, k) => field === "docstatus" ? __({ 0: "Draft", 1: "Submitted", 2: "Cancelled" }[k] || k) : (k === "" ? __("Not Set") : __(k));
	GV.color = (dt, field, k, sample) => {
		if (field === "docstatus") return { 0: "red", 1: "blue", 2: "gray" }[k] || "gray";
		if (k === "") return "gray";
		try {
			const ind = sample && frappe.get_indicator(sample, dt);
			if (ind && ind[1] && (ind[0] === __(k) || ind[0] === k)) return ind[1];
		} catch (e) { /* ignore */ }
		let h = 0;
		for (const ch of k) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
		return COLORS[h % COLORS.length];
	};

	/* ============================== list view ============================== */
	frappe.views.ListView = class GroupedListView extends frappe.views.ListView {
		_gv_state() {
			if (!GV.enabled_for(this.doctype)) return {};
			const st = GV.get(this.doctype);
			if (st.enabled === undefined) st.enabled = !!GV.lv_settings(this.doctype).default;
			if (!st.field || !GV.candidates(this.doctype).some((d) => d.fieldname === st.field)) st.field = GV.default_field(this.doctype);
			st.collapsed = st.collapsed || {};
			return st;
		}
		_gv_ensure_field(f) {
			if (f && !this.fields.some((x) => x[0] === f && x[1] === this.doctype)) this.fields.push([f, this.doctype]);
		}
		get_args() {
			const st = this._gv_state();
			if (st.enabled && st.field) this._gv_ensure_field(st.field);
			return super.get_args();
		}
		_gv_toggle(on) { GV.set(this.doctype, { enabled: !!on }); this.refresh(); }

		_gv_setup() {
			if (this._gv_ready || !GV.enabled_for(this.doctype)) return;
			this._gv_ready = true;

			// rows stay direct children of .result (v16 lays rows out on the list's own column grid),
			// so a group is: head + rows tagged data-gv-key + more-row, all siblings.
			this.$result.on("click", ".gv-group-head", (e) => {
				const key = $(e.currentTarget).attr("data-gv-key");
				const st = this._gv_state();
				this._gv_collapse(key, !st.collapsed[key]);
				GV.set(this.doctype, { collapsed: st.collapsed });
			});
			this.$result.on("click", ".gv-load-more, .gv-load-all", (e) => {
				e.stopPropagation();
				this._gv_load_more($(e.currentTarget).closest(".gv-more-row").attr("data-gv-key"), $(e.currentTarget).hasClass("gv-load-all"));
			});
			this.$result.on("keydown", ".gv-group-head", (e) => {
				if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $(e.currentTarget).trigger("click"); }
			});

			if (GV.config.quick_view && GV.lv_settings(this.doctype).quick_view !== false) {
				this.$result.on("click", ".list-subject a", (e) => {
					if (e.ctrlKey || e.metaKey || e.shiftKey || e.which > 1) return;
					const $a = $(e.currentTarget);
					const name = $a.attr("data-name") || $a.closest(".list-row").find(".list-row-checkbox").attr("data-name");
					if (!name) return;
					e.preventDefault();
					e.stopPropagation();
					GV.quick_view(this.doctype, name, this);
				});
			}
			if (!GV._switcher_patched) {
				this.page.add_menu_item(__("Toggle Grouped View"), () => this._gv_toggle(!this._gv_state().enabled));
			}
		}

		_gv_render_bar(st) {
			if (!this.$gv_bar) {
				this.$gv_bar = $(`
					<div class="gv-bar">
						<span class="gv-label">${__("Group by")}</span>
						<select class="form-control gv-field" aria-label="${__("Group by field")}"></select>
						<button class="btn btn-xs btn-default gv-collapse-all">${__("Collapse all")}</button>
						<button class="btn btn-xs btn-default gv-expand-all">${__("Expand all")}</button>
						<span class="gv-spacer"></span>
						<span class="gv-hint">${__("Click an ID for a quick view")}</span>
						<button class="btn btn-xs btn-default gv-off">${__("Ungroup")}</button>
					</div>`).insertBefore(this.$result);
				this.$gv_bar.on("change", ".gv-field", (e) => { GV.set(this.doctype, { field: e.target.value, collapsed: {} }); this.refresh(); });
				this.$gv_bar.on("click", ".gv-off", () => this._gv_toggle(false));
				this.$gv_bar.on("click", ".gv-collapse-all, .gv-expand-all", (e) => {
					const collapse = $(e.currentTarget).hasClass("gv-collapse-all");
					const s = this._gv_state();
					this.$result.children(".gv-group-head").each((_, h) => this._gv_collapse($(h).attr("data-gv-key"), collapse));
					GV.set(this.doctype, { collapsed: s.collapsed });
				});
			}
			this.$gv_bar.find(".gv-field").html(GV.candidates(this.doctype)
				.map((df) => `<option value="${esc(df.fieldname)}" ${df.fieldname === st.field ? "selected" : ""}>${esc(__(df.label))}</option>`).join(""));
			this.$gv_bar.toggle(!!st.enabled);
		}

		_gv_sync_switcher(st) {
			const $menu = this.views_menu && $(this.views_menu);
			if (!$menu || !$menu.length) return;
			const $label = $menu.parent().find(".custom-btn-group-label");
			if ($label.length) $label.text(st.enabled ? __("Grouped View") : __("List View"));
			$menu.find('[data-view="Grouped"]').toggle(!st.enabled);
			$menu.find('[data-view="List"]').toggle(!!st.enabled);
		}

		_gv_part(key, selector) {
			// elements of one group; compares attributes directly so no selector escaping is needed
			return this.$result.children(selector).filter((_, el) => el.getAttribute("data-gv-key") === key);
		}

		_gv_collapse(key, collapsed) {
			const st = this._gv_state();
			st.collapsed[key] = collapsed;
			this._gv_part(key, ".gv-group-head").toggleClass("gv-collapsed", collapsed).attr("aria-expanded", String(!collapsed));
			this._gv_part(key, ".list-row-container, .gv-more-row").toggleClass("gv-hide", collapsed);
		}

		render_list() {
			this.$result.children(".gv-group-head, .gv-more-row").remove();
			this._gv_setup();
			const st = this._gv_state();
			if (this._gv_ready) { this._gv_render_bar(st); this._gv_sync_switcher(st); }

			if (!st.enabled || !st.field) {
				this.$result.children(".list-row-container").removeAttr("data-gv-key").removeClass("gv-hide");
				this._gv_order = (this.data || []).map((d) => d.name);
				return super.render_list();
			}

			// 1. sort the loaded data into group order (stable inside each group)
			const field = st.field;
			const key_of = (d) => (d[field] == null ? "" : String(d[field]));
			const buckets = new Map();
			(this.data || []).forEach((d) => {
				const k = key_of(d);
				if (!buckets.has(k)) buckets.set(k, []);
				buckets.get(k).push(d);
			});
			const keys = GV.group_order(this.doctype, field, [...buckets.keys()]);
			this.data = keys.flatMap((k) => buckets.get(k));
			this._gv_order = this.data.map((d) => d.name);

			// 2. let Frappe render the rows itself, so every version-specific step
			//    (v16 column widths, scroll sync, likes, checkboxes) runs untouched
			super.render_list();

			// 3. decorate: tag rows and insert group heads + "load more" rows between them
			const key_by_name = new Map(this.data.map((d) => [String(d.name), key_of(d)]));
			const doc_by_key = new Map(keys.map((k) => [k, buckets.get(k)[0]]));
			let current = null, $last = null;
			const close_group = () => {
				if (current === null || !$last) return;
				$last.after(`<div class="gv-more-row ${st.collapsed[current] ? "gv-hide" : ""}" data-gv-key="${esc(current)}" hidden>
					<button class="btn btn-xs btn-default gv-load-more"></button>
					<button class="btn btn-xs btn-default gv-load-all" hidden></button>
					<span class="gv-rem"></span></div>`);
			};
			this.$result.children(".list-row-container").each((_, el) => {
				const $row = $(el);
				const name = $row.find(".list-row-checkbox").attr("data-name") || $row.find(".list-subject a").attr("data-name");
				const k = key_by_name.has(String(name)) ? key_by_name.get(String(name)) : "";
				const collapsed = !!st.collapsed[k];
				if (k !== current) {
					close_group();
					current = k;
					const n = buckets.has(k) ? buckets.get(k).length : 0;
					$row.before(`
						<div class="gv-group-head ${collapsed ? "gv-collapsed" : ""}" data-gv-key="${esc(k)}" role="button" tabindex="0" aria-expanded="${!collapsed}">
							<span class="gv-caret" aria-hidden="true"></span>
							<span class="indicator-pill ${GV.color(this.doctype, field, k, doc_by_key.get(k))} ellipsis"><span class="ellipsis">${esc(GV.label(field, k))}</span></span>
							<span class="gv-count">${n}</span>
						</div>`);
				}
				$row.attr("data-gv-key", k).toggleClass("gv-hide", collapsed);
				$last = $row;
			});
			close_group();
			this._gv_fetch_counts(field);
		}

		async _gv_fetch_counts(field) {
			if (field === "docstatus") return;
			const filters = JSON.stringify(this.get_filters_for_args());
			const key = field + "|" + filters;
			try {
				if (this._gv_counts_key !== key) {
					const res = await frappe.xcall("frappe.desk.listview.get_group_by_count", { doctype: this.doctype, current_filters: filters, field });
					this._gv_counts_key = key;
					this._gv_counts = {};
					(res || []).forEach((r) => { this._gv_counts[r.name == null ? "" : String(r.name)] = r.count; });
				}
				this.$result.children(".gv-group-head").each((_, h) => this._gv_update_group($(h).attr("data-gv-key")));
			} catch (e) { /* counts are optional */ }
		}

		_gv_step() { return Math.max(this.page_length || 20, 20); }

		_gv_update_group(key) {
			const total = (this._gv_counts || {})[key] || 0;
			const loaded = this._gv_part(key, ".list-row-container").length;
			this._gv_part(key, ".gv-group-head").find(".gv-count").text(total > loaded ? __("{0} of {1}", [loaded, total]) : loaded);
			const rem = Math.max(total - loaded, 0);
			const step = this._gv_step();
			const $m = this._gv_part(key, ".gv-more-row").prop("hidden", rem <= 0);
			$m.find(".gv-load-more").text(__("Load {0} more", [Math.min(rem, step)]));
			$m.find(".gv-load-all").text(__("Load all {0}", [rem])).prop("hidden", rem <= step || rem > 500);
			$m.find(".gv-rem").text(__("{0} remaining", [rem]));
		}

		async _gv_load_more(key, all) {
			const st = this._gv_state();
			const field = st.field;
			const $m = this._gv_part(key, ".gv-more-row");
			const loaded = this._gv_part(key, ".list-row-container").length;
			const total = (this._gv_counts || {})[key] || 0;
			const count = all ? Math.min(total - loaded, 500) : this._gv_step();
			if (count <= 0) return;

			const args = Object.assign({}, this.get_args());
			args.filters = (args.filters || []).concat([
				key === "" ? [this.doctype, field, "is", "not set"] : [this.doctype, field, "=", key],
			]);
			args.start = loaded;
			args.page_length = count;

			$m.find("button").prop("disabled", true);
			try {
				const r = await frappe.call({ method: this.method || "frappe.desk.reportview.get", args });
				const m = r.message || {};
				const rows = Array.isArray(m) ? m : frappe.utils.dict(m.keys || [], m.values || []);
				const have = new Set(this.data.map((d) => String(d.name)));
				const fresh = rows.filter((d) => !have.has(String(d.name)));
				// insert after the last loaded row of this group, then re-render through Frappe
				let at = -1;
				this.data.forEach((d, i) => { if ((d[field] == null ? "" : String(d[field])) === key) at = i; });
				this.data.splice(at + 1, 0, ...fresh);
				if (typeof this.render === "function") this.render(); else this.render_list();
			} finally {
				$m.find("button").prop("disabled", false);
				this._gv_update_group(key);
			}
		}
	};

	/* ============================== v15 view switcher ============================== */
	const LVS = frappe.views.ListViewSelect;
	const refresh_if_current = (dt) => {
		if (window.cur_list && cur_list.doctype === dt && cur_list.view_name === "List") { cur_list.refresh(); return true; }
		return false;
	};
	if (LVS && LVS.prototype.setup_views && LVS.prototype.add_view_to_menu) {
		GV._switcher_patched = true;
		const orig_add = LVS.prototype.add_view_to_menu;
		const orig_setup = LVS.prototype.setup_views;
		LVS.prototype.add_view_to_menu = function (view, action) {
			if (view === "List" && GV.enabled_for(this.doctype)) {
				const original = action;
				action = (...a) => { GV.set(this.doctype, { enabled: false }); original(...a); refresh_if_current(this.doctype); };
			}
			return orig_add.call(this, view, action);
		};
		LVS.prototype.setup_views = function (...args) {
			orig_setup.apply(this, args);
			if (!GV.enabled_for(this.doctype)) return;
			try {
				this.icon_map = this.icon_map || {};
				this.label_map = this.label_map || {};
				this.icon_map.Grouped = this.icon_map.Grouped || this.icon_map.List || "list";
				this.label_map.Grouped = this.label_map.Grouped || __("Grouped View");
				orig_add.call(this, "Grouped", () => {
					GV.set(this.doctype, { enabled: true });
					if (!refresh_if_current(this.doctype)) frappe.set_route("List", this.doctype);
				});
				if (this.current_view === "List") {
					orig_add.call(this, "List", () => { GV.set(this.doctype, { enabled: false }); refresh_if_current(this.doctype); });
				}
			} catch (e) { console.warn("grouped_list_view: switcher entry not added", e); }
		};
	}

	/* ============================== quick view (side panel) ============================== */
	const HIDE = new Set(["HTML", "Button", "Fold", "Heading", "Password", "Signature", "Geolocation", "HTML Editor", "Code", "JSON", "Image"]);
	const STD = new Set(["name", "owner", "creation", "modified", "modified_by", "docstatus", "idx", "parent", "parentfield", "parenttype", "doctype"]);
	const ICON = {
		left: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3.5 5.5 8l4.5 4.5"/></svg>',
		right: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3.5 10.5 8 6 12.5"/></svg>',
		open: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3.5h6.5V10M12.5 3.5 4 12"/></svg>',
		layout: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><rect x="2" y="3" width="12" height="10" rx="2"/><path d="M9.5 3v10"/></svg>',
		close: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="m4 4 8 8M12 4l-8 8"/></svg>',
	};

	GV.load = async (dt, name) => {
		const r = await frappe.call({ method: "frappe.desk.form.load.getdoc", args: { doctype: dt, name } });
		const doc = (r.docs || []).find((d) => d.doctype === dt && d.name === name) || (r.docs || [])[0];
		if (!doc) throw new Error("not found");
		return { doc, info: r.docinfo || {} };
	};
	GV.is_empty = (v) => v == null || v === "" || (Array.isArray(v) && !v.length);
	GV.can_read = (dt, df) => { try { return frappe.perm.has_perm(dt, df.permlevel || 0, "read"); } catch (e) { return true; } };
	GV.form_link = (dt, name) => {
		try { return frappe.utils.get_form_link(dt, name); } catch (e) { return `/app/${frappe.router.slug(dt)}/${encodeURIComponent(name)}`; }
	};

	GV.value_html = (df, v, doc) => {
		if (GV.is_empty(v)) return "";
		if (df.fieldtype === "Attach Image") return `<a href="${esc(v)}" target="_blank" rel="noopener"><img class="gv-thumb" src="${esc(v)}" alt="${esc(__(df.label))}"></a>`;
		if (df.fieldtype === "Attach") return `<a href="${esc(v)}" target="_blank" rel="noopener">${esc(String(v).split("/").pop())}</a>`;
		if (df.fieldtype === "Table MultiSelect") {
			return esc(v.map((r) => { const k = Object.keys(r).find((x) => !STD.has(x) && !x.startsWith("__")); return k ? r[k] : ""; }).filter(Boolean).join(", "));
		}
		if (df.fieldtype === "Text Editor") return esc((new DOMParser().parseFromString(v, "text/html").body.textContent || "").trim());
		if (LONG.has(df.fieldtype)) return esc(String(v));
		return frappe.format(v, df, { inline: true }, doc);
	};

	GV.build_layout = (dt, doc) => {
		const meta = frappe.get_meta(dt);
		const tabs = [];
		let tab, sec, col;
		const new_sec = (label) => { sec = { label, columns: [[]], tables: [], has_value: false }; tab.sections.push(sec); col = sec.columns[0]; };
		const new_tab = (label) => { tab = { label, sections: [] }; tabs.push(tab); new_sec(""); };
		new_tab(__("Details"));
		meta.fields.forEach((df) => {
			if (df.fieldtype === "Tab Break") return new_tab(__(df.label || "Details"));
			if (df.fieldtype === "Section Break") return new_sec(df.label ? __(df.label) : "");
			if (df.fieldtype === "Column Break") { col = []; sec.columns.push(col); return; }
			if (df.hidden || HIDE.has(df.fieldtype) || !GV.can_read(dt, df)) return;
			const v = doc[df.fieldname];
			const empty = GV.is_empty(v);
			if (df.fieldtype === "Table") { if (!empty) { sec.tables.push(df); sec.has_value = true; } return; }
			// like the real form: empty read-only and conditional fields stay hidden
			if (empty && (df.read_only || df.depends_on || df.fieldtype === "Table MultiSelect")) return;
			col.push(df);
			if (!empty && !(df.fieldtype === "Check" && !+v)) sec.has_value = true;
		});
		tabs.forEach((t) => {
			t.sections = t.sections.filter((s) => s.has_value);
			t.sections.forEach((s) => { s.columns = s.columns.filter((c) => c.length); });
		});
		return tabs.filter((t) => t.sections.length);
	};

	GV.table_html = async (df, rows) => {
		await frappe.model.with_doctype(df.options);
		const cm = frappe.get_meta(df.options);
		let cols = cm.fields.filter((f) => f.in_list_view && !SKIP.has(f.fieldtype));
		if (!cols.length) cols = cm.fields.filter((f) => !SKIP.has(f.fieldtype) && !f.hidden).slice(0, 5);
		cols = cols.slice(0, 8);
		const shown = rows.slice(0, GV.config.max_child_rows);
		return `<details class="gv-ptable"><summary>${esc(__(df.label || df.options))} <span class="gv-muted">${rows.length}</span></summary>
			<div class="gv-table-wrap"><table class="gv-table">
			<thead><tr><th class="gv-idx">#</th>${cols.map((c) => `<th class="${NUMERIC.has(c.fieldtype) ? "gv-n" : ""}">${esc(__(c.label))}</th>`).join("")}</tr></thead>
			<tbody>${shown.map((r) => `<tr><td class="gv-idx">${r.idx}</td>${cols.map((c) => `<td class="${NUMERIC.has(c.fieldtype) ? "gv-n" : ""}">${GV.is_empty(r[c.fieldname]) ? "" : frappe.format(r[c.fieldname], c, { inline: true }, r)}</td>`).join("")}</tr>`).join("")}</tbody>
			</table></div>
			${rows.length > shown.length ? `<div class="gv-table-more">${__("{0} more rows in the full form", [rows.length - shown.length])}</div>` : ""}</details>`;
	};

	GV.field_html = (df, doc) => {
		const v = doc[df.fieldname];
		if (df.fieldtype === "Check") {
			return `<div class="gv-pcheck"><span class="gv-cb ${+v ? "on" : ""}" role="img" aria-label="${+v ? __("Yes") : __("No")}"></span><span>${esc(__(df.label))}</span></div>`;
		}
		const cls = ["gv-pv", df.read_only ? "gv-ro" : "", df.bold ? "gv-bold" : "", LONG.has(df.fieldtype) ? "gv-long" : ""].join(" ");
		return `<div class="gv-pf"><div class="gv-pl">${esc(__(df.label))}${df.reqd ? '<span class="gv-req">*</span>' : ""}</div><div class="${cls}">${GV.value_html(df, v, doc)}</div></div>`;
	};

	GV.activity = (dt, doc, info) => {
		const items = [];
		(info.versions || []).forEach((v) => {
			let data;
			try { data = typeof v.data === "string" ? JSON.parse(v.data) : v.data; } catch (e) { return; }
			((data && data.changed) || []).forEach(([f, o, n]) => {
				const df = frappe.meta.get_docfield(dt, f);
				if (!df || df.hidden) return;
				const show = (x) => (x === "" || x == null ? "—" : String(x));
				items.push({ who: v.owner, when: v.creation, html: `${__("changed")} <b>${esc(__(df.label))}</b> ${__("from")} ${esc(show(o))} ${__("to")} <b>${esc(show(n))}</b>` });
			});
		});
		(info.comments || []).forEach((c) => {
			const t = (new DOMParser().parseFromString(c.content || "", "text/html").body.textContent || "").trim();
			if (t) items.push({ who: c.owner, when: c.creation, html: `${__("commented")}: ${esc(t.length > 240 ? t.slice(0, 240) + "…" : t)}` });
		});
		items.push({ who: doc.owner, when: doc.creation, html: __("created this document") });
		items.sort((a, b) => (a.when < b.when ? 1 : -1));
		return items.slice(0, 40);
	};

	/* ---------- modal layout: summary cards (the earlier popup) ---------- */
	GV.cards_html = async (dt, doc, info, acts) => {
		const meta = frappe.get_meta(dt);
		const lvs = GV.lv_settings(dt);
		const blank = (v, df) => GV.is_empty(v) || (df.fieldtype === "Check" && !+v);
		const status_df = frappe.meta.get_docfield(dt, "status");
		const skip = new Set([meta.title_field, status_df && status_df.fieldname, "naming_series", "amended_from"].filter(Boolean));
		let section = "";
		const all = [];
		meta.fields.forEach((df) => {
			if (df.fieldtype === "Section Break" || df.fieldtype === "Tab Break") { section = df.label ? __(df.label) : section; return; }
			if (SKIP.has(df.fieldtype) || HIDE.has(df.fieldtype) || df.hidden || skip.has(df.fieldname)) return;
			if (blank(doc[df.fieldname], df) || !GV.can_read(dt, df)) return;
			all.push({ df, section });
		});
		let summary;
		if (Array.isArray(lvs.fields) && lvs.fields.length) {
			summary = lvs.fields.map((f) => all.find((x) => x.df.fieldname === f)).filter(Boolean);
		} else {
			const score = (df) => (df.in_list_view ? 8 : 0) + (df.in_standard_filter ? 4 : 0) + (df.bold ? 2 : 0) + (df.reqd ? 1 : 0);
			const short = all.filter((x) => !LONG.has(x.df.fieldtype) && x.df.fieldtype !== "Attach Image");
			summary = short.slice().sort((a, b) => score(b.df) - score(a.df)).slice(0, GV.config.summary_fields)
				.concat(all.filter((x) => LONG.has(x.df.fieldtype)).slice(0, 2));
		}
		const used = new Set(summary.map((x) => x.df.fieldname));
		const rest = all.filter((x) => !used.has(x.df.fieldname));
		const cell = ({ df }) => {
			const v = doc[df.fieldname];
			const long = LONG.has(df.fieldtype);
			const val = df.fieldtype === "Check" ? __("Yes") : long ? `<div class="gv-clamp">${GV.value_html(df, v, doc)}</div>` : GV.value_html(df, v, doc);
			return `<div class="gv-f ${long ? "gv-wide" : ""}"><div class="gv-k">${esc(__(df.label))}</div><div class="gv-v">${val}</div>
				${long ? `<button class="gv-link-btn gv-expand" hidden>${__("Show more")}</button>` : ""}</div>`;
		};

		let html = `<div class="gv-meta-line">${__("Created by {0}", [esc(frappe.user.full_name(doc.owner))])} · ${__("modified")} ${frappe.datetime.comment_when(doc.modified)}</div>`;
		if (summary.length) html += `<div class="gv-card"><div class="gv-card-title">${__("Details")}</div><div class="gv-grid">${summary.map(cell).join("")}</div></div>`;

		for (const tdf of meta.fields) {
			if (tdf.fieldtype !== "Table" || tdf.hidden || !GV.can_read(dt, tdf)) continue;
			const rows = doc[tdf.fieldname] || [];
			if (!rows.length) continue;
			const t = await GV.table_html(tdf, rows); // <details class="gv-ptable">…
			html += t.replace('<details class="gv-ptable">', '<details class="gv-card">');
		}

		if (rest.length) {
			let body = "", last = null, bucket = [];
			const flush = () => { if (bucket.length) body += `<div class="gv-grid">${bucket.map(cell).join("")}</div>`; bucket = []; };
			rest.forEach((x) => {
				if (x.section !== last) { flush(); if (x.section) body += `<div class="gv-section-label">${esc(x.section)}</div>`; last = x.section; }
				bucket.push(x);
			});
			flush();
			html += `<details class="gv-card"><summary>${__("All fields")} <span class="gv-muted">${rest.length}</span></summary>${body}</details>`;
		}

		html += `<div class="gv-card"><div class="gv-card-title">${__("Recent activity")}</div><ul class="gv-activity">
			${acts.slice(0, 6).map((a) => `<li>${frappe.avatar(a.who, "avatar-xs")}<span><b>${esc(frappe.user.full_name(a.who))}</b> ${a.html}</span><span class="gv-when">${frappe.datetime.comment_when(a.when, true)}</span></li>`).join("")}
		</ul></div>`;
		return html;
	};

	GV.peek = {
		ensure() {
			if (this.$el) return;
			this.$bd = $('<div class="gv-peek-backdrop"></div>').appendTo("body");
			this.$el = $(`
				<aside class="gv-peek" role="dialog" aria-modal="true" tabindex="-1" aria-label="${__("Quick view")}">
					<header class="gv-peek-head">
						<div class="gv-peek-crumb"></div>
						<div class="gv-peek-actions">
							<span class="gv-peek-nav">
								<button class="gv-ibtn" data-nav="-1" title="${__("Previous")}" aria-label="${__("Previous")}">${ICON.left}</button>
								<span class="gv-pos"></span>
								<button class="gv-ibtn" data-nav="1" title="${__("Next")}" aria-label="${__("Next")}">${ICON.right}</button>
							</span>
							<button class="gv-ibtn gv-layout-btn" title="${__("Switch layout")}" aria-label="${__("Switch layout")}" aria-haspopup="true" aria-expanded="false">${ICON.layout}</button>
							<a class="gv-ibtn gv-open" title="${__("Open Full Form")}" aria-label="${__("Open Full Form")}">${ICON.open}</a>
							<button class="gv-ibtn gv-close" title="${__("Close")} (Esc)" aria-label="${__("Close")}">${ICON.close}</button>
						</div>
						<div class="gv-layout-pop" role="radiogroup" aria-label="${__("Layout")}" hidden>
							${[["modal", __("Modal")], ["sidebar", __("Sidebar")]].map(([k, l]) =>
								`<button class="gv-lopt" role="radio" data-layout="${k}" aria-checked="false"><span class="gv-lthumb ${k}"><i></i></span>${l}</button>`).join("")}
						</div>
					</header>
					<nav class="gv-peek-tabs" role="tablist"></nav>
					<div class="gv-peek-body"></div>
				</aside>`).appendTo("body");

			try { this.layout_mode = localStorage.getItem("gv_peek_layout") || "sidebar"; } catch (e) { this.layout_mode = "sidebar"; }
			this.set_layout(this.layout_mode, false);
			const $pop = this.$el.find(".gv-layout-pop");
			const toggle_pop = (show) => {
				$pop.prop("hidden", !show);
				this.$el.find(".gv-layout-btn").attr("aria-expanded", String(show));
			};
			this.$el.on("click", ".gv-layout-btn", (e) => { e.stopPropagation(); toggle_pop($pop.prop("hidden")); });
			this.$el.on("click", ".gv-lopt", (e) => { this.set_layout($(e.currentTarget).attr("data-layout"), true); toggle_pop(false); });
			this.$el.on("click", (e) => { if (!$(e.target).closest(".gv-layout-pop, .gv-layout-btn").length) toggle_pop(false); });
			this.toggle_pop = toggle_pop;
			this.$bd.on("click", () => this.close());
			this.$el.on("click", ".gv-close", () => this.close());
			this.$el.on("click", "[data-nav]", (e) => {
				const order = (this.lv && this.lv._gv_order) || [];
				const next = order[order.indexOf(this.name) + +$(e.currentTarget).attr("data-nav")];
				if (next) this.show(next);
			});
			this.$el.on("click", ".gv-open", (e) => {
				if (e.ctrlKey || e.metaKey || e.shiftKey || e.which > 1) return;
				e.preventDefault();
				const { dt, name } = this;
				this.close();
				frappe.set_route("Form", dt, name);
			});
			this.$el.on("click", ".gv-tab", (e) => { this.tab = $(e.currentTarget).attr("data-tab"); this.render_tab(); });
			$(document).on("keydown.gvpeek", (e) => {
				if (!this.$el.hasClass("open")) return;
				if (e.key === "Escape") {
					e.preventDefault(); e.stopPropagation();
					if (!this.$el.find(".gv-layout-pop").prop("hidden")) return this.toggle_pop(false);
					this.close();
				}
			});
			try { frappe.router.on("change", () => this.close()); } catch (e) { /* older router */ }
		},

		set_layout(mode, save) {
			if (!["modal", "sidebar"].includes(mode)) mode = "sidebar";
			this.layout_mode = mode;
			this.$el.attr("data-layout", mode);
			this.$el.find(".gv-lopt").each((_, b) => $(b).attr("aria-checked", String($(b).attr("data-layout") === mode)));
			if (save) { try { localStorage.setItem("gv_peek_layout", mode); } catch (e) { /* private mode */ } }
			if (this.doc && this.$el.hasClass("open")) this.render_content();
		},

		open(dt, name, lv) {
			this.ensure();
			this.dt = dt;
			this.lv = lv;
			this.last_focus = document.activeElement;
			this.$bd.addClass("open");
			this.$el.addClass("open");
			$("body").addClass("gv-peek-lock");
			this.show(name);
			setTimeout(() => this.$el.trigger("focus"), 60);
		},

		close() {
			if (!this.$el || !this.$el.hasClass("open")) return;
			this.toggle_pop && this.toggle_pop(false);
			this.$el.removeClass("open");
			this.$bd.removeClass("open");
			$("body").removeClass("gv-peek-lock");
			if (this.last_focus && this.last_focus.focus) this.last_focus.focus();
		},

		async show(name) {
			const dt = this.dt;
			this.name = name;
			const order = (this.lv && this.lv._gv_order) || [];
			const i = order.indexOf(name);
			this.$el.find(".gv-peek-nav").prop("hidden", order.length < 2 || i < 0);
			this.$el.find(".gv-pos").text(`${i + 1} / ${order.length}`);
			this.$el.find('[data-nav="-1"]').prop("disabled", i <= 0);
			this.$el.find('[data-nav="1"]').prop("disabled", i >= order.length - 1);
			this.$el.find(".gv-open").attr("href", GV.form_link(dt, name));
			this.$el.find(".gv-peek-crumb").html(`<span class="gv-dt">${esc(__(dt))}</span><span class="gv-sep">/</span><span class="gv-nm" title="${esc(name)}">${esc(name)}</span>`);
			this.$el.find(".gv-peek-tabs").empty();
			this.$el.find(".gv-peek-body").html(`<div class="gv-loading">${__("Loading…")}</div>`);
			try {
				const { doc, info } = await GV.load(dt, name);
				if (this.name !== name) return; // user already moved on
				this.doc = doc;
				this.info = info;
				let ind = null;
				try { ind = frappe.get_indicator(doc, dt); } catch (e) { /* ignore */ }
				if (ind) this.$el.find(".gv-peek-crumb").append(`<span class="indicator-pill ${ind[1]}"><span>${esc(ind[0])}</span></span>`);
				this.layout = GV.build_layout(dt, doc);
				this.acts = GV.activity(dt, doc, info);
				this.render_content();
			} catch (e) {
				this.$el.find(".gv-peek-body").html(`<div class="gv-empty-note">${__("Could not load {0}. You may not have permission to read it.", [esc(name)])}</div>`);
			}
		},

		async render_content() {
			if (this.layout_mode === "modal") {
				const $body = this.$el.find(".gv-peek-body");
				const html = await GV.cards_html(this.dt, this.doc, this.info, this.acts);
				$body.html(html).scrollTop(0);
				$body.find(".gv-clamp").each((_, el) => {
					if (el.scrollHeight > el.clientHeight + 2) $(el).closest(".gv-f").find(".gv-expand").prop("hidden", false);
				});
				$body.off("click.gvx").on("click.gvx", ".gv-expand", (e) => {
					const $c = $(e.currentTarget).closest(".gv-f").find(".gv-clamp").toggleClass("open");
					$(e.currentTarget).text($c.hasClass("open") ? __("Show less") : __("Show more"));
				});
				return;
			}
			const labels = this.layout.map((t) => t.label).concat([__("Activity")]);
			if (!labels.includes(this.tab)) this.tab = labels[0];
			this.$el.find(".gv-peek-tabs").html(labels.map((l) =>
				`<button class="gv-tab" role="tab" data-tab="${esc(l)}" aria-selected="${l === this.tab}">${esc(l)}${l === __("Activity") ? `<span class="gv-badge">${this.acts.length}</span>` : ""}</button>`).join(""));
			this.render_tab();
		},

		async render_tab() {
			const $body = this.$el.find(".gv-peek-body");
			this.$el.find(".gv-tab").each((_, b) => $(b).attr("aria-selected", String($(b).attr("data-tab") === this.tab)));
			const doc = this.doc;
			if (this.tab === __("Activity")) {
				const files = (this.info.attachments || []);
				$body.html(`
					<section class="gv-ps"><h4 class="gv-ps-title">${__("Activity")}</h4>
						<ul class="gv-activity">${this.acts.map((a) => `<li>${frappe.avatar(a.who, "avatar-xs")}<span><b>${esc(frappe.user.full_name(a.who))}</b> ${a.html}</span><span class="gv-when">${frappe.datetime.comment_when(a.when, true)}</span></li>`).join("")}</ul>
					</section>
					${files.length ? `<section class="gv-ps"><h4 class="gv-ps-title">${__("Attachments")} <span class="gv-muted">${files.length}</span></h4>
						<div class="gv-files">${files.map((f) => `<a href="${esc(f.file_url)}" target="_blank" rel="noopener">${esc(f.file_name || f.file_url)}</a>`).join("")}</div></section>` : ""}`);
				$body.scrollTop(0);
				return;
			}
			const tab = this.layout.find((t) => t.label === this.tab);
			if (!tab) return;
			const parts = [];
			for (const s of tab.sections) {
				const tables = [];
				for (const tdf of s.tables) tables.push(await GV.table_html(tdf, doc[tdf.fieldname] || []));
				parts.push(`<section class="gv-ps">
					${s.label ? `<h4 class="gv-ps-title">${esc(s.label)}</h4>` : ""}
					${s.columns.length ? `<div class="gv-pcols" style="--cols:${s.columns.length}">${s.columns.map((c) => `<div class="gv-pcol">${c.map((df) => GV.field_html(df, doc)).join("")}</div>`).join("")}</div>` : ""}
					${tables.join("")}
				</section>`);
			}
			$body.html(parts.join("")).scrollTop(0);
		},
	};

	GV.quick_view = (dt, name, lv) => GV.peek.open(dt, name, lv);
})();