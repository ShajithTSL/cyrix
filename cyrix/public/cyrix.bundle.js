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
                this.filter_area.clear(true);
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
const SKIP_DOCTYPES = ["User", "Print Format Builder"]; // add any you don't want touched

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