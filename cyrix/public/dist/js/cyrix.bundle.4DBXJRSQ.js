(() => {
  // frappe-html:/home/shajith/cyrix-bench/apps/cyrix/cyrix/public/navbar.html
  frappe.templates["navbar"] = `<div class="sticky-top">
	<header class="navbar navbar-expand" role="navigation">
		<div class="container">
			<a class="navbar-brand navbar-home" href="/app">
				<img
					class="app-logo"
					src="{{ frappe.boot.app_logo_url }}"
					alt="{{ __("App Logo") }}"
				>
			</a>
			<ul class="nav navbar-nav d-none d-sm-flex" id="navbar-breadcrumbs"></ul>
			<div class="collapse navbar-collapse justify-content-end">
				<form class="form-inline fill-width justify-content-end" role="search" onsubmit="return false;">
					
					<button class="nav-link timelink checkin_time" id="checkinout"
						onclick="company_change()">
						{% if frappe.defaults.get_user_default("Company") %}
						<span class="indicator-pill red no-indicator-dot">
							{%= frappe.defaults.get_user_default("Company") %}
						</span>
						{% else %}
						<span class="indicator-pill red no-indicator-dot">
							Select Company
						</span>
						{% endif %}

					</button>
					{% if (frappe.boot.read_only) { %}
						<span class="indicator-pill yellow no-indicator-dot" title="{%= __("Your site is undergoing maintenance or being updated.") %}">
							{%= __("Read Only Mode") %}
						</span>
					{% } %}
					{% if (frappe.boot.user.impersonated_by) { %}
						<span class="indicator-pill red no-indicator-dot" title="{%= __("You are impersonating as another user.") %}">
							{%= __("Impersonating {0}", [frappe.boot.user.name]) %}
						</span>
					{% } %}
					
					<div class="input-group search-bar text-muted hidden">
						<input
							id="navbar-search"
							type="text"
							class="form-control"
							placeholder="{%= __('Search or type a command ({0})', [frappe.utils.is_mac() ? '\u2318 + G' : 'Ctrl + G']) %}"
							aria-haspopup="true"
						>
						<span class="search-icon">
							<svg class="icon icon-sm"><use href="#icon-search"></use></svg>
						</span>
					</div>
				</form>
				<ul class="navbar-nav">
					<li class="nav-item dropdown dropdown-notifications dropdown-mobile hidden">
						<button
							class="btn-reset nav-link notifications-icon text-muted"
							data-toggle="dropdown"
							aria-haspopup="true"
							aria-expanded="false"
						>
							<span class="notifications-seen">
								<span class="sr-only">{{ __("No new notifications") }}</span>
								<svg class="es-icon icon-sm" style="stroke:none;"><use href="#es-line-notifications"></use></svg>
							</span>
							<span class="notifications-unseen">
								<span class="sr-only">{{ __("You have unseen notifications") }}</span>
								<svg class="es-icon icon-sm"><use href="#es-line-notifications-unseen"></use></svg>
							</span>
						</button>
						<div class="dropdown-menu notifications-list dropdown-menu-right" role="menu">
							<div class="notification-list-header">
								<div class="header-items"></div>
								<div class="header-actions"></div>
							</div>
							<div class="notification-list-body">
								<div class="panel-notifications"></div>
								<div class="panel-events"></div>
								<div class="panel-changelog-feed"></div>
							</div>
						</div>
					</li>
					<li class="nav-item dropdown dropdown-message dropdown-mobile hidden">
						<button
							class="btn-reset nav-link notifications-icon text-muted"
							data-toggle="dropdown"
							aria-haspopup="true"
							aria-expanded="true"
						>
							<span>
								<svg class="es-icon icon-sm"><use href="#es-line-chat-alt"></use></svg>
							</span>
						</button>
					</li>
					<li class="vertical-bar d-none d-sm-block"></li>
					<li class="nav-item dropdown dropdown-help dropdown-mobile d-none d-lg-block">
						<button
							class="btn-reset nav-link"
							data-toggle="dropdown"
							aria-controls="toolbar-help"
							aria-label="{{ __("Help Dropdown") }}"
						>
							<span>
								{{ __("Help") }}
								<svg class="es-icon icon-xs"><use href="#es-line-down"></use></svg>
							</span>
						</button>
						<div class="dropdown-menu dropdown-menu-right" id="toolbar-help" role="menu">
							<div id="help-links"></div>
							<div class="dropdown-divider documentation-links"></div>
							{% for item in navbar_settings.help_dropdown %}
								{% if (!item.hidden) { %}
									{% if (item.route) { %}
										<a class="dropdown-item" href="{{ item.route }}">
											{%= __(item.item_label) %}
										</a>
									{% } else if (item.action) { %}
										<button class="btn-reset dropdown-item" onclick="return {{ item.action }}">
											{%= __(item.item_label) %}
										</button>
									{% } else { %}
										<div class="dropdown-divider"></div>
									{% } %}
								{% } %}
							{% endfor %}
						</div>
					</li>
					<li class="nav-item dropdown dropdown-navbar-user dropdown-mobile">
						<button
							class="btn-reset nav-link"
							data-toggle="dropdown"
							aria-label="{{ __("User Menu") }}"
						>
							{{ avatar }}
						</button>
						<div class="dropdown-menu dropdown-menu-right" id="toolbar-user" role="menu">
							{% for item in navbar_settings.settings_dropdown %}
								{% var condition = item.condition ? eval(item.condition) : true %}
								{% if (condition && !item.hidden) { %}
									{% if (item.route) { %}
										<a class="dropdown-item" href="{{ item.route }}">
											{%= __(item.item_label) %}
										</a>
									{% } else if (item.action) { %}
										<button class="btn-reset dropdown-item" onclick="return {{ item.action }}">
											{%= __(item.item_label) %}
										</button>
									{% } else { %}
										<div class="dropdown-divider"></div>
									{% } %}
								{% } %}
							{% endfor %}
						</div>
					</li>
				</ul>
			</div>
		</div>
	</header>

	{% if !localStorage.getItem("dismissed_announcement_widget") && strip_html(navbar_settings.announcement_widget) != '' %}
	<div class="announcement-widget form-message p-2 m-0" style="position: relative; z-index: -1; border-radius: 0; background-color: var(--bg-blue);">
		<div class="container flex justify-between align-center mx-auto">
			{{ navbar_settings.announcement_widget }}
			<div class="close-message p-0 mr-2" style="position: relative;">
			{{ frappe.utils.icon("close") }}
			</div>
		</div>
	</div>
	{% endif %}

</div>
<style>
	#checkinout {
		background-color: transparent;
		border: 2px solid transparent;
		border-radius: 5px;
		padding: 8px 20px;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.2s ease;
		display: inline-flex; /* ensures pill stays aligned */
		align-items: center;
		gap: 10px; /* space between text and pill */
	}

	#checkinout:hover {
		background-color: transparent; /* keep button transparent */
		color: transparent; /* maybe slightly darker text on hover */
	}

	#checkinout .indicator-pill {
		background-color: #FF4500;   /* pill color stays intact */
		color: white;
		padding: 3px 10px;
		border-radius: 50px;
		font-size: 14px;
		font-weight: bold;
		transition: all 0.2s ease;
	}

	/* optional: pill hover effect */
	#checkinout:hover .indicator-pill {
		background-color: #FF6347; /* slightly lighter red on hover */
	}

</style>
<script>
window.company_change = function() {
	frappe.ui.toolbar.setup_session_defaults();
}
<\/script>`;

  // ../cyrix/cyrix/public/cyrix.bundle.js
  frappe.ui.form.on("*", {
    onload: function(frm) {
      console.log("Vanakkam");
    }
  });
})();
//# sourceMappingURL=cyrix.bundle.4DBXJRSQ.js.map
