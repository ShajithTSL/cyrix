// >>> CHANGE THIS to your app name (the folder that contains customer_hub_api.py and crm_hub_api.py) <<<
window.CUSTOMER_HUB_API = window.CUSTOMER_HUB_API || "cyrix.cyrix_tsl.page.customer_hub.customer_hub_api";

/* Styles are bundled here so the page always matches this code. */
(function () {
	var CSS = ".ch {\n\t--ch-bg: var(--card-bg, #fff);\n\t--ch-fg: var(--text-color, #171717);\n\t--ch-muted: var(--text-muted, #6b6b6b);\n\t--ch-light: var(--text-light, #9a9a9a);\n\t--ch-border: var(--border-color, #ededed);\n\t--ch-subtle: var(--subtle-fg, #f6f6f6);\n\t--ch-hover: var(--fg-hover-color, #f3f3f3);\n\t--ch-ink: var(--text-color, #171717);\n\t--ch-ink-fg: var(--card-bg, #fff);\n\tfont-family: var(--font-stack, \"Inter\", system-ui, -apple-system, \"Segoe UI\", sans-serif);\n\tfont-size: 13px;\n\tline-height: 1.45;\n\tcolor: var(--ch-fg);\n\tbackground: var(--ch-bg);\n\tborder: 1px solid var(--ch-border);\n\tborder-radius: 12px;\n\toverflow: hidden;\n}\n.ch *, .ch *::before, .ch *::after { box-sizing: border-box; }\n:where(.ch) button { font: inherit; color: inherit; cursor: pointer; background: none; border: 0; padding: 0; }\n.ch :focus-visible { outline: 2px solid var(--ch-ink); outline-offset: 2px; border-radius: 6px; }\n.ch h2 { font-size: 15px; font-weight: 600; margin: 0; }\n.ch h3 { font-size: 13px; font-weight: 600; margin: 0; }\n.ch-i { flex: none; }\n.ch [hidden] { display: none !important; }\n.ch-muted { color: var(--ch-muted); font-size: 12px; }\n.ch-light { color: var(--ch-light); font-style: normal; }\n.ch-sub { color: var(--ch-light); font-size: 11px; }\n.ch-nowrap { white-space: nowrap; }\n.ch-r { text-align: right; }\n\n/* top bar */\n.ch-top { display: flex; gap: 8px; align-items: center; padding: 10px 14px; border-bottom: 1px solid var(--ch-border); flex-wrap: wrap; }\n.ch-cust-slot { flex: 1 1 260px; max-width: 360px; }\n.ch-cust-slot .frappe-control { margin: 0; }\n.ch-cust-slot .form-group { margin: 0; }\n.ch-select { position: relative; display: inline-flex; align-items: center; }\n.ch-select select, .ch-cust-slot > select {\n\tappearance: none; font: inherit; color: var(--ch-fg); background: var(--ch-subtle);\n\tborder: 1px solid transparent; border-radius: 8px; height: 30px; padding: 0 28px 0 10px; cursor: pointer;\n}\n.ch-cust-slot > select { width: 100%; font-weight: 500; }\n.ch-select .ch-i { position: absolute; right: 9px; pointer-events: none; color: var(--ch-muted); }\n.ch-select-sm select { height: 28px; font-size: 12px; }\n.ch-btn { display: inline-flex; align-items: center; gap: 6px; height: 30px; padding: 0 12px; border-radius: 8px; font-weight: 500; white-space: nowrap; }\n.ch-btn-sm { height: 26px; padding: 0 9px; font-size: 12px; }\n.ch-btn:disabled { opacity: .5; cursor: default; }\n.ch-primary { background: var(--ch-ink) !important; color: var(--ch-ink-fg) !important; }\n.ch-ghost { width: 30px; padding: 0; justify-content: center; background: var(--ch-subtle) !important; color: var(--ch-muted) !important; }\n.ch-ghost:hover { color: var(--ch-fg) !important; }\n.ch-link { color: var(--ch-muted); font-size: 12px; text-decoration: underline; text-underline-offset: 2px; }\n\n/* layout */\n.ch-body { min-height: 560px; }\n.ch-hub { display: grid; grid-template-columns: minmax(0, 1fr) 300px; min-height: 560px; }\n.ch-list { padding: 18px 22px 28px; }\n.ch-cell-id { display: flex; gap: 10px; align-items: center; }\n.ch-cell-id .ch-av { width: 28px; height: 28px; font-size: 12px; margin: 0; }\n.ch-more { display: flex; justify-content: center; padding: 14px 0 0; }\n.ch-soft { background: var(--ch-subtle) !important; color: var(--ch-fg) !important; }\n.ch-soft:hover { background: var(--ch-hover) !important; }\n.ch-scope { margin-top: 2px; }\n.ch-main { min-width: 0; border-right: 1px solid var(--ch-border); }\n.ch-side { padding: 14px 16px 24px; }\n\n/* tabs (Frappe CRM style) */\n.ch-tabs { display: flex; gap: 2px; padding: 0 10px; border-bottom: 1px solid var(--ch-border); overflow-x: auto; scrollbar-width: thin; }\n.ch-tab { display: inline-flex; align-items: center; gap: 6px; padding: 11px 8px 10px; color: var(--ch-muted); white-space: nowrap; border-bottom: 2px solid transparent; margin-bottom: -1px; }\n.ch-tab:hover { color: var(--ch-fg); }\n.ch-tab.is-active { color: var(--ch-fg); border-bottom-color: var(--ch-ink); font-weight: 500; }\n.ch-tab em { font-style: normal; font-size: 11px; background: var(--ch-subtle); color: var(--ch-muted); border-radius: 6px; padding: 0 5px; min-width: 18px; text-align: center; }\n.ch-content { padding: 18px 22px 28px; }\n.ch-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }\n.ch-head-tools { display: flex; gap: 8px; align-items: center; }\n.ch-search { display: inline-flex; align-items: center; gap: 6px; background: var(--ch-subtle); border-radius: 8px; height: 30px; padding: 0 10px; color: var(--ch-muted); }\n.ch-search input { border: 0; background: none; outline: none; font: inherit; color: var(--ch-fg); width: 170px; }\n\n/* stats */\n.ch-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid var(--ch-border); border-radius: 10px; overflow: hidden; margin-bottom: 16px; }\n.ch-stat { display: flex; flex-direction: column; gap: 2px; padding: 12px 14px; text-align: left; border-right: 1px solid var(--ch-border); border-bottom: 1px solid var(--ch-border); background: var(--ch-bg); }\n.ch-stat:nth-child(3n) { border-right: 0; }\n.ch-stat:nth-last-child(-n+3) { border-bottom: 0; }\nbutton.ch-stat:hover { background: var(--ch-hover); }\n.ch-stat-l { color: var(--ch-muted); font-size: 12px; }\n.ch-stat-v { font-size: 20px; font-weight: 600; letter-spacing: -.01em; font-variant-numeric: tabular-nums; }\n.ch-stat-s { color: var(--ch-light); font-size: 11.5px; }\n.ch-stat-red .ch-stat-s { color: #dc2626; }\n\n.ch-card { border: 1px solid var(--ch-border); border-radius: 10px; padding: 14px 16px; margin-bottom: 16px; }\n.ch-card-h { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }\n\n/* chart */\n.ch-chart-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; margin-bottom: 18px; }\n.ch-chart-head h3 { margin-bottom: 8px; }\n.ch-seg { display: inline-flex; background: var(--ch-subtle); border-radius: 8px; padding: 2px; }\n.ch :where(.ch-seg) button { padding: 4px 11px; border-radius: 6px; font-size: 12px; color: var(--ch-muted); }\n.ch :where(.ch-seg) button.is-on { background: var(--ch-bg); color: var(--ch-fg); font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,.08), 0 0 0 1px var(--ch-border); }\n.ch-chart-sum { display: flex; gap: 22px; margin: 0; flex-wrap: wrap; }\n.ch-chart-sum div { min-width: 0; }\n.ch-chart-sum dt { color: var(--ch-muted); font-size: 11.5px; }\n.ch-chart-sum dd { margin: 2px 0 0; font-size: 15px; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; }\n.ch-plot { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 8px; height: 220px; }\n.ch-yaxis { display: flex; flex-direction: column; justify-content: space-between; padding-bottom: 22px; font-size: 10.5px; color: var(--ch-light); text-align: right; font-variant-numeric: tabular-nums; }\n.ch-yaxis span { line-height: 0; }\n.ch-plot-area { position: relative; }\n.ch-grid { position: absolute; inset: 0 0 22px 0; display: flex; flex-direction: column; justify-content: space-between; pointer-events: none; }\n.ch-grid i { display: block; border-top: 1px dashed var(--ch-border); }\n.ch-grid i:last-child { border-top-style: solid; }\n.ch-cols { position: absolute; inset: 0; display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); }\n.ch-col { position: relative; display: flex; flex-direction: column; align-items: center; outline: none; cursor: default; }\n.ch-col-track { flex: 1; width: 100%; display: flex; align-items: flex-end; justify-content: center; border-radius: 6px 6px 0 0; }\n.ch-col:hover .ch-col-track, .ch-col:focus-visible .ch-col-track { background: var(--ch-hover); }\n.ch-col-bar { width: min(28px, 58%); background: var(--ch-fg); opacity: .78; border-radius: 4px 4px 1px 1px; }\n.ch-col.is-best .ch-col-bar { opacity: 1; }\n.ch-col.is-now .ch-col-bar { opacity: 1; background: repeating-linear-gradient(135deg, var(--ch-fg) 0 4px, var(--ch-muted) 4px 7px); }\n.ch-col-x { height: 22px; line-height: 22px; font-size: 10.5px; color: var(--ch-light); }\n.ch-col.is-now .ch-col-x { color: var(--ch-fg); font-weight: 600; }\n.ch-tip { position: absolute; top: 4px; left: 50%; transform: translateX(-50%); z-index: 5; display: none; flex-direction: column; gap: 1px; background: var(--ch-fg); color: var(--ch-bg); border-radius: 8px; padding: 7px 10px; font-size: 12px; white-space: nowrap; pointer-events: none; }\n.ch-tip b { font-weight: 600; }\n.ch-tip small { opacity: .7; font-size: 11px; }\n.ch-col.tip-start .ch-tip { left: 0; transform: none; }\n.ch-col.tip-end .ch-tip { left: auto; right: 0; transform: none; }\n.ch-col:hover .ch-tip, .ch-col:focus-visible .ch-tip { display: flex; }\n.ch-empty-chart { padding: 50px 16px; }\n\n/* flow */\n.ch-flow { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; }\n.ch-flow-step { display: inline-flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 8px; background: var(--ch-subtle); color: var(--ch-muted); }\n.ch-flow-step b { color: var(--ch-fg); font-variant-numeric: tabular-nums; }\n.ch-flow-step:hover { background: var(--ch-hover); color: var(--ch-fg); }\n.ch-flow-arrow { color: var(--ch-light); display: inline-flex; }\n\n/* timeline */\n.ch-tl { list-style: none; margin: 0; padding: 0; position: relative; }\n.ch-tl::before { content: \"\"; position: absolute; left: 11px; top: 6px; bottom: 6px; width: 1px; background: var(--ch-border); }\n.ch-tl li { display: flex; gap: 14px; padding: 7px 0; position: relative; }\n.ch-tl-ic { flex: none; width: 23px; height: 23px; display: grid; place-items: center; border-radius: 50%; background: var(--ch-bg); color: var(--ch-muted); position: relative; z-index: 1; }\n.ch-tl-body { flex: 1; min-width: 0; }\n.ch-tl-line { display: flex; gap: 8px; align-items: flex-start; min-height: 23px; }\n.ch-tl-text { flex: 1; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; padding-top: 2px; }\n.ch-tl-line time { color: var(--ch-light); font-size: 11.5px; white-space: nowrap; padding-top: 3px; }\n.ch-tl-line b { font-weight: 500; }\n.ch-av { flex: none; width: 20px; height: 20px; border-radius: 50%; display: grid; place-items: center; background: var(--ch-subtle); color: var(--ch-muted); font-size: 10.5px; font-weight: 600; margin-top: 1px; }\n.ch-av-lg { width: 44px; height: 44px; font-size: 18px; margin: 0; }\n.ch-ref { font-weight: 500; text-decoration: underline; text-decoration-color: var(--ch-border); text-underline-offset: 3px; }\n.ch-ref:hover { text-decoration-color: currentColor; }\n.ch-amt { font-variant-numeric: tabular-nums; font-weight: 500; }\n.ch-bubble { margin-top: 6px; background: var(--ch-subtle); border-radius: 10px; padding: 10px 12px; white-space: normal; overflow-wrap: anywhere; }\n.ch-mail { border: 1px solid var(--ch-border); border-radius: 10px; padding: 10px 12px; }\n.ch-mail-sub { font-weight: 500; margin: 2px 0; }\n.ch-mail p { margin: 8px 0 0; color: var(--ch-muted); border-top: 1px solid var(--ch-border); padding-top: 8px; }\n.ch-composer { border: 1px solid var(--ch-border); border-radius: 10px; padding: 8px; margin-bottom: 14px; display: flex; flex-direction: column; gap: 6px; }\n.ch-composer textarea { border: 0; outline: none; resize: vertical; font: inherit; color: var(--ch-fg); background: none; padding: 4px; }\n.ch-composer > div { display: flex; justify-content: flex-end; }\n\n/* badges & progress */\n.ch-badge { display: inline-flex; align-items: center; height: 20px; padding: 0 7px; border-radius: 6px; font-size: 11.5px; font-weight: 500; white-space: nowrap; }\n.ch-gray { background: rgba(120,120,120,.13); color: var(--ch-muted); }\n.ch-green { background: rgba(22,163,74,.13); color: #15803d; }\n.ch-amber { background: rgba(217,119,6,.14); color: #b45309; }\n.ch-red { background: rgba(220,38,38,.12); color: #dc2626; }\n.ch-blue { background: rgba(37,99,235,.12); color: #2563eb; }\n.ch-prog { width: 70px; height: 5px; border-radius: 3px; background: var(--ch-subtle); overflow: hidden; display: inline-block; vertical-align: middle; margin-right: 6px; }\n.ch-prog i { display: block; height: 100%; background: var(--ch-ink); }\n\n/* table */\n.ch-table-wrap { overflow-x: auto; border: 1px solid var(--ch-border); border-radius: 10px; }\n.ch-table { width: 100%; border-collapse: collapse; }\n.ch-table th { text-align: left; font-weight: 500; color: var(--ch-muted); font-size: 12px; padding: 9px 12px; border-bottom: 1px solid var(--ch-border); background: var(--ch-bg); }\n.ch-table th.ch-r { text-align: right; }\n.ch-table td { padding: 9px 12px; border-bottom: 1px solid var(--ch-border); vertical-align: middle; }\n.ch-table td b { font-weight: 500; }\n.ch-table tbody tr { cursor: pointer; }\n.ch-table tbody tr:hover { background: var(--ch-hover); }\n.ch-table tfoot td { border-bottom: 0; color: var(--ch-muted); font-size: 12px; font-weight: 500; }\n.ch-table tfoot td.ch-r { color: var(--ch-fg); }\n\n/* side */\n.ch-side-id { font-weight: 600; font-size: 13px; padding-bottom: 12px; border-bottom: 1px solid var(--ch-border); margin: 0 -16px 14px; padding-left: 16px; }\n.ch-side-hero { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 14px; }\n.ch-side-name { font-size: 16px; font-weight: 600; line-height: 1.25; margin-bottom: 6px; overflow-wrap: anywhere; }\n.ch-side-actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }\n.ch-icon-btn { width: 26px; height: 26px; display: grid; place-items: center; border-radius: 7px; background: var(--ch-subtle); color: var(--ch-muted) !important; }\n.ch-icon-btn:hover { color: var(--ch-fg) !important; }\n.ch-new { position: relative; }\n.ch-menu { position: absolute; z-index: 20; top: 30px; right: 0; min-width: 180px; background: var(--ch-bg); border: 1px solid var(--ch-border); border-radius: 10px; padding: 4px; box-shadow: 0 8px 24px rgba(0,0,0,.12); }\n.ch-menu button { display: flex; gap: 8px; align-items: center; width: 100%; padding: 7px 9px; border-radius: 7px; text-align: left; }\n.ch-menu button:hover { background: var(--ch-hover); }\n.ch-side details { border-top: 1px solid var(--ch-border); padding: 10px 0 6px; }\n.ch-side summary { list-style: none; display: flex; align-items: center; gap: 6px; font-weight: 600; cursor: pointer; margin-bottom: 6px; }\n.ch-side summary::-webkit-details-marker { display: none; }\n.ch-side details:not([open]) summary .ch-i { transform: rotate(-90deg); }\n.ch-kv { display: grid; grid-template-columns: 110px minmax(0, 1fr); gap: 8px; padding: 5px 0; font-size: 12.5px; }\n.ch-kv > span:first-child { color: var(--ch-muted); }\n.ch-kv > span:last-child { overflow-wrap: anywhere; }\n.ch-warn { background: rgba(220,38,38,.1); color: #dc2626; border-radius: 8px; padding: 7px 10px; font-size: 12px; margin-bottom: 12px; }\n\n/* states */\n.ch-empty { color: var(--ch-muted); text-align: center; padding: 36px 16px; border: 1px dashed var(--ch-border); border-radius: 10px; }\n.ch-empty-lg { border: 0; padding: 90px 16px; display: flex; flex-direction: column; align-items: center; gap: 10px; }\n.ch-empty-lg p { max-width: 380px; margin: 0; }\n.ch-loading { display: flex; gap: 6px; justify-content: center; padding: 80px 0; }\n.ch-loading span { width: 7px; height: 7px; border-radius: 50%; background: var(--ch-light); animation: ch-pulse 1s infinite ease-in-out; }\n.ch-loading span:nth-child(2) { animation-delay: .15s; }\n.ch-loading span:nth-child(3) { animation-delay: .3s; }\n@keyframes ch-pulse { 0%, 100% { opacity: .25; } 50% { opacity: 1; } }\n@media (prefers-reduced-motion: reduce) { .ch-loading span { animation: none; opacity: .6; } }\n\n/* responsive */\n@media (max-width: 1000px) {\n\t.ch-hub { grid-template-columns: 1fr; }\n\t.ch-main { border-right: 0; border-bottom: 1px solid var(--ch-border); order: 2; }\n\t.ch-side { order: 1; border-bottom: 1px solid var(--ch-border); }\n\t.ch-side-id { display: none; }\n}\n@media (max-width: 640px) {\n\t.ch-content { padding: 14px 12px 22px; }\n\t.ch-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }\n\t.ch-stat:nth-child(3n) { border-right: 1px solid var(--ch-border); }\n\t.ch-stat:nth-child(2n) { border-right: 0; }\n\t.ch-stat:nth-last-child(-n+3) { border-bottom: 1px solid var(--ch-border); }\n\t.ch-stat:nth-last-child(-n+2) { border-bottom: 0; }\n\t.ch-hide-sm { display: none; }\n\t.ch-search input { width: 110px; }\n\t.ch-cust-slot { flex-basis: 100%; max-width: none; }\n}\n.ch-search input:focus-visible { outline: none; }\n.ch-search:focus-within { box-shadow: 0 0 0 1px var(--ch-muted); }\n.ch-rank { width: 34px; text-align: center !important; color: var(--ch-muted); font-variant-numeric: tabular-nums; font-weight: 600; }\n.ch-meter { height: 3px; border-radius: 2px; background: var(--ch-subtle); margin-top: 5px; margin-left: auto; width: 90px; overflow: hidden; }\n.ch-meter i { display: block; height: 100%; margin-left: auto; background: var(--ch-fg); opacity: .7; }\n.ch-av { color: var(--ch-fg) !important; }\n\n/* ageing */\n.ch { --ch-b0: #16a34a; --ch-b1: #eab308; --ch-b2: #f97316; --ch-b3: #ef4444; --ch-b4: #991b1b; }\n.ch-age-card { padding: 16px 18px; }\n.ch-age { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 24px; align-items: center; }\n.ch-age-total { display: flex; flex-direction: column; gap: 2px; }\n.ch-age-v { font-size: 22px; font-weight: 600; letter-spacing: -.01em; font-variant-numeric: tabular-nums; white-space: nowrap; }\n.ch-age-od { display: block; color: #dc2626; font-weight: 500; margin-top: 2px; }\n.ch-age-bar { display: flex; height: 10px; border-radius: 5px; overflow: hidden; background: var(--ch-subtle); gap: 2px; margin-bottom: 12px; }\n.ch-age-bar i { display: block; height: 100%; min-width: 3px; }\n.ch-age-buckets { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }\n.ch-age-buckets > div { display: flex; flex-direction: column; gap: 1px; min-width: 0; }\n.ch-age-l { display: inline-flex; align-items: center; gap: 6px; color: var(--ch-muted); font-size: 11.5px; white-space: nowrap; }\n.ch-age-a { font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }\n.ch-dot { width: 8px; height: 8px; border-radius: 2px; display: inline-block; flex: none; }\n.ch-b0 { background: var(--ch-b0); } .ch-b1 { background: var(--ch-b1); } .ch-b2 { background: var(--ch-b2); }\n.ch-b3 { background: var(--ch-b3); } .ch-b4 { background: var(--ch-b4); }\n.ch-age-pill { display: inline-flex; align-items: center; height: 20px; padding: 0 7px; border-radius: 6px; font-size: 11.5px; font-weight: 500; white-space: nowrap; }\n.ch-b0-soft { background: rgba(22,163,74,.13); color: #15803d; }\n.ch-b1-soft { background: rgba(234,179,8,.16); color: #a16207; }\n.ch-b2-soft { background: rgba(249,115,22,.15); color: #c2410c; }\n.ch-b3-soft { background: rgba(239,68,68,.14); color: #dc2626; }\n.ch-b4-soft { background: rgba(153,27,27,.85); color: #fff; }\n.ch-list .ch-age-card { margin-bottom: 14px; }\n@media (max-width: 900px) {\n\t.ch-age { grid-template-columns: 1fr; gap: 14px; }\n\t.ch-age-buckets { grid-template-columns: repeat(3, minmax(0, 1fr)); }\n}\n.ch-age-ok { display: block; color: #15803d; font-weight: 500; margin-top: 2px; }\n\n/* list filters */\n.ch-filters { display: flex; gap: 14px; align-items: flex-end; flex-wrap: wrap; margin: -4px 0 14px; }\n.ch-filters:empty { display: none; }\n.ch-filter-f { display: flex; flex-direction: column; gap: 3px; margin: 0; font-weight: 400; }\n.ch-filter-f > span:first-child { font-size: 11px; color: var(--ch-muted); }\n.ch-filter-f select { min-width: 160px; }\n.ch-select.is-set select { background: var(--ch-ink); color: var(--ch-ink-fg); }\n.ch-select.is-set .ch-i { color: var(--ch-ink-fg); }\n.ch-f-clear { align-self: center; margin-top: 14px; }\n.ch :where(.ch-age-btn) { text-align: left; padding: 6px 8px; margin: -6px -8px; border-radius: 8px; display: flex; flex-direction: column; gap: 1px; min-width: 0; }\n.ch-age-btn:hover { background: var(--ch-hover); }\n.ch-age-btn.is-on { background: var(--ch-subtle); box-shadow: inset 0 0 0 1.5px var(--ch-fg); }\n\n/* ===================== Home / sales day view ===================== */\n.ch-nav button { display: inline-flex; align-items: center; gap: 6px; }\n.ch-home { padding: 20px 22px 30px; }\n.ch-home-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }\n.ch-home-head h2 { font-size: 20px; letter-spacing: -.01em; margin-bottom: 3px; }\n.ch-red-t { color: #dc2626; }\n.ch-stats-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }\n.ch-stats-4 .ch-stat { border-bottom: 0 !important; }\n.ch-stats-4 .ch-stat:nth-child(3n) { border-right: 1px solid var(--ch-border); }\n.ch-stats-4 .ch-stat:last-child { border-right: 0; }\n.ch-home-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr); gap: 16px; align-items: start; }\n.ch-card-h h3 { display: inline-flex; align-items: center; gap: 7px; }\n.ch-count { font-style: normal; font-size: 11px; font-weight: 600; background: var(--ch-subtle); color: var(--ch-muted); border-radius: 6px; padding: 0 6px; }\n.ch-empty-sm { padding: 26px 12px; display: flex; flex-direction: column; align-items: center; gap: 6px; border-style: dashed; }\n.ch-empty-sm p { margin: 0; }\n\n/* follow-ups */\n.ch-fu-group + .ch-fu-group { margin-top: 10px; }\n.ch-fu-gl { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; color: var(--ch-muted); margin-bottom: 4px; }\n.ch-fu-gl span { font-weight: 500; color: var(--ch-light); }\n.ch-fu { list-style: none; margin: 0; padding: 0; }\n.ch-fu li { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; border-top: 1px solid var(--ch-border); transition: opacity .2s; }\n.ch-fu li:first-child { border-top: 0; }\n.ch-fu li.is-done { opacity: .35; }\n.ch-fu li.is-done .ch-fu-title { text-decoration: line-through; }\n.ch :where(.ch-done) { flex: none; width: 20px; height: 20px; margin-top: 1px; border-radius: 6px; border: 1.5px solid var(--ch-light); display: grid; place-items: center; color: transparent; }\n.ch-done:hover, .ch-done:focus-visible { border-color: #16a34a; color: #16a34a; }\n.ch-fu li.is-done .ch-done { background: #16a34a; border-color: #16a34a; color: #fff; }\n.ch-fu-main { flex: 1; min-width: 0; }\n.ch-fu-title { overflow-wrap: anywhere; }\n.ch-fu-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; font-size: 12px; margin-top: 1px; }\n.ch-fu-meta:empty { display: none; }\n.ch-fu li > .ch-badge { flex: none; }\n.ch-tag { font-size: 10.5px; font-weight: 600; background: var(--ch-subtle); color: var(--ch-muted); border-radius: 4px; padding: 0 5px; }\n\n/* needs attention */\n.ch-att-sec + .ch-att-sec { margin-top: 14px; }\n.ch-att-h { display: flex; align-items: center; gap: 7px; font-weight: 600; font-size: 12.5px; margin-bottom: 4px; }\n.ch-att-ic { width: 20px; height: 20px; border-radius: 6px; display: grid; place-items: center; }\n.ch-att, .ch-leads { list-style: none; margin: 0; padding: 0; }\n.ch-att-row, .ch-leads li { display: flex; align-items: center; gap: 10px; padding: 7px 0; border-top: 1px solid var(--ch-border); }\n.ch-att-row:first-child, .ch-leads li:first-child { border-top: 0; }\n.ch :where(.ch-att-main) { flex: 1; min-width: 0; display: flex; flex-direction: column; text-align: left; }\n.ch-att-main b { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.ch-att-main:hover b { text-decoration: underline; text-underline-offset: 2px; }\n.ch-att-main .ch-muted { font-size: 11.5px; }\n.ch-att-amt { font-variant-numeric: tabular-nums; font-weight: 600; white-space: nowrap; font-size: 12.5px; }\n.ch-att-actions { display: flex; gap: 6px; align-items: center; flex: none; }\n.ch-fu-form-li { list-style: none; padding: 4px 0 10px; }\n.ch-fu-form { background: var(--ch-subtle); border-radius: 10px; padding: 10px; display: flex; flex-direction: column; gap: 8px; }\n.ch-fu-form .ch-fu-text { width: 100%; border: 1px solid var(--ch-border); background: var(--ch-bg); color: var(--ch-fg); border-radius: 8px; padding: 6px 9px; font: inherit; }\n.ch-fu-when { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }\n.ch :where(.ch-chip-btn) { padding: 3px 9px; border-radius: 999px; border: 1px solid var(--ch-border); background: var(--ch-bg); font-size: 12px; }\n.ch-chip-btn.is-on { background: var(--ch-ink); color: var(--ch-ink-fg); border-color: var(--ch-ink); }\n.ch-fu-date { border: 1px solid var(--ch-border); background: var(--ch-bg); color: var(--ch-fg); border-radius: 8px; padding: 3px 7px; font: inherit; font-size: 12px; height: 26px; }\n.ch-fu-btns { display: flex; gap: 6px; justify-content: flex-end; }\n\n/* pipeline */\n.ch-pipe { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(190px, 1fr); gap: 10px; overflow-x: auto; padding-bottom: 4px; }\n.ch-pipe-col { background: var(--ch-subtle); border-radius: 10px; padding: 10px; display: flex; flex-direction: column; gap: 6px; min-width: 0; }\n.ch-pipe-h { display: flex; align-items: center; gap: 6px; font-size: 12.5px; }\n.ch-pipe-h b { font-weight: 600; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.ch-pipe-v { font-size: 11.5px; color: var(--ch-muted); font-variant-numeric: tabular-nums; margin-top: -4px; }\n.ch :where(.ch-deal) { background: var(--ch-bg); border: 1px solid var(--ch-border); border-radius: 8px; padding: 7px 9px; text-align: left; display: flex; flex-direction: column; gap: 1px; font-size: 12px; }\n.ch-deal:hover { border-color: var(--ch-muted); }\n.ch-deal b { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.ch-deal span { color: var(--ch-muted); font-variant-numeric: tabular-nums; }\n.ch-pipe-more, .ch-pipe-empty { font-size: 11.5px; text-align: center; color: var(--ch-light); }\n.ch-pc-gray { background: #9ca3af; } .ch-pc-blue { background: #3b82f6; } .ch-pc-green { background: #22c55e; }\n.ch-pc-red { background: #ef4444; } .ch-pc-orange { background: #f97316; } .ch-pc-yellow { background: #eab308; }\n.ch-pc-purple { background: #a855f7; } .ch-pc-pink { background: #ec4899; } .ch-pc-cyan { background: #06b6d4; }\n.ch-pc-teal { background: #14b8a6; } .ch-pc-violet { background: #8b5cf6; } .ch-pc-amber { background: #f59e0b; }\n.ch-leads li > .ch-badge { flex: none; }\n\n/* composer kinds, side follow-ups, call icon */\n.ch-composer { gap: 8px; }\n.ch-log-kind { align-self: flex-start; }\n.ch-log-kind button { display: inline-flex; align-items: center; gap: 5px; }\n.ch-composer-foot { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }\n.ch-tl-ic.ch-tl-call { color: #2563eb; }\n.ch-side-fu .ch-fu li { padding: 6px 0; }\n.ch-side-note { margin: 2px 0 8px; font-size: 12px; }\n.ch-side-add { margin: 4px 0 6px; }\n\n@media (max-width: 1000px) {\n\t.ch-home-grid { grid-template-columns: 1fr; }\n}\n@media (max-width: 640px) {\n\t.ch-home { padding: 14px 12px 22px; }\n\t.ch-stats-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }\n\t.ch-stats-4 .ch-stat:nth-child(2n) { border-right: 0; }\n\t.ch-stats-4 .ch-stat:nth-child(-n+2) { border-bottom: 1px solid var(--ch-border) !important; }\n\t.ch-att-row { flex-wrap: wrap; }\n\t.ch-att-actions { width: 100%; justify-content: flex-end; }\n\t.ch-top .ch-nav { order: -1; }\n}\n@media (max-width: 640px) { .ch-fu-card .ch-card-h > .ch-muted { display: none; } }\n\n/* ===================== CRM (leads, deals, contacts) ===================== */\n.ch-crm { padding: 18px 22px 28px; }\n.ch-crm-chips { display: flex; gap: 6px; flex-wrap: wrap; margin: -4px 0 14px; }\n.ch-crm-chips:empty { display: none; }\n.ch-crm-chips .ch-chip-btn { display: inline-flex; align-items: center; gap: 6px; }\n.ch-crm-chips .ch-chip-btn span { color: var(--ch-light); font-variant-numeric: tabular-nums; }\n.ch-crm-chips .ch-chip-btn.is-on span { color: inherit; opacity: .7; }\n.ch-st { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; font-size: 12.5px; }\n.ch-crm-table td { white-space: nowrap; }\n.ch-crm-table td:first-child { white-space: normal; min-width: 180px; }\n.ch-tel { color: inherit; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; }\n.ch-tel:hover { text-decoration: underline; }\n\n/* board */\n.ch-board { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(220px, 1fr); gap: 10px; overflow-x: auto; padding-bottom: 6px; min-height: 380px; }\n.ch-bcol { background: var(--ch-subtle); border-radius: 12px; padding: 10px; display: flex; flex-direction: column; gap: 6px; min-width: 0; border: 1.5px dashed transparent; transition: border-color .12s, background .12s; }\n.ch-bcol.is-closed { opacity: .85; }\n.ch-bcol.is-over { border-color: var(--ch-muted); background: var(--ch-hover); }\n.ch-bcards { display: flex; flex-direction: column; gap: 6px; flex: 1; min-height: 60px; }\n.ch-dcard { cursor: grab; }\n.ch-dcard:active { cursor: grabbing; }\n.ch-dcard.is-dragging { opacity: .4; }\n\n/* modal form */\n.ch-modal { position: fixed; inset: 0; z-index: 1065; display: grid; place-items: center; padding: 16px; }\n.ch-modal-scrim { position: absolute; inset: 0; background: rgba(0,0,0,.32); }\n.ch-modal-box { position: relative; width: min(680px, 100%); max-height: calc(100vh - 32px); display: flex; flex-direction: column; background: var(--ch-bg); color: var(--ch-fg); border-radius: 14px; box-shadow: 0 20px 60px rgba(0,0,0,.25); animation: ch-pop .15s ease-out; }\n@keyframes ch-pop { from { transform: translateY(8px) scale(.99); opacity: 0; } to { transform: none; opacity: 1; } }\n@media (prefers-reduced-motion: reduce) { .ch-modal-box { animation: none; } }\n.ch-crm-form { display: flex; flex-direction: column; min-height: 0; }\n.ch-modal-h { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px 12px; border-bottom: 1px solid var(--ch-border); }\n.ch-modal-body { padding: 16px 18px; overflow: auto; }\n.ch-modal-f { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--ch-border); }\n.ch-fgrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 14px; }\n.ch-frow { display: flex; flex-direction: column; gap: 4px; margin: 0; font-weight: 400; min-width: 0; }\n.ch-frow > span:first-child { font-size: 12px; color: var(--ch-muted); }\n.ch-frow-wide { grid-column: 1 / -1; }\n.ch-in { width: 100%; font: inherit; color: var(--ch-fg); background: var(--ch-subtle); border: 1px solid transparent; border-radius: 8px; padding: 6px 9px; min-height: 32px; }\n.ch-in:focus { outline: none; border-color: var(--ch-muted); background: var(--ch-bg); }\ntextarea.ch-in { resize: vertical; }\n.ch-in-check { width: 16px; height: 16px; min-height: 0; accent-color: var(--ch-fg); }\n.ch-in-wrap { width: 100%; }\n.ch-in-wrap select.ch-in { appearance: none; padding-right: 28px; height: 32px; cursor: pointer; }\n.ch-form-err { margin-top: 12px; background: rgba(220,38,38,.1); color: #dc2626; border-radius: 8px; padding: 8px 10px; font-size: 12.5px; }\n.ch-form-hint { margin: 12px 0 0; font-size: 12px; }\n\n/* link autocomplete */\n.ch-ac { position: relative; display: block; width: 100%; }\n.ch-ac-list { position: absolute; top: calc(100% + 4px); left: 0; right: 0; z-index: 30; background: var(--ch-bg); border: 1px solid var(--ch-border); border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,.14); padding: 4px; max-height: 260px; overflow: auto; }\n.ch :where(.ch-ac-opt) { display: flex; flex-direction: column; width: 100%; text-align: left; padding: 6px 9px; border-radius: 7px; }\n.ch-ac-opt b { font-weight: 500; }\n.ch-ac-opt span { font-size: 11.5px; color: var(--ch-muted); }\n.ch-ac-opt.is-on, .ch-ac-opt:hover { background: var(--ch-hover); }\n.ch :where(.ch-ac-new) { flex-direction: row; align-items: center; gap: 6px; color: var(--ch-fg); font-weight: 500; }\n.ch-ac-none { padding: 8px 10px; color: var(--ch-muted); font-size: 12.5px; }\n\n/* record page */\n.ch-rec-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 14px 22px 12px; border-bottom: 1px solid var(--ch-border); flex-wrap: wrap; }\n.ch-rec-title { display: flex; align-items: baseline; gap: 6px; min-width: 0; }\n.ch-rec-title h2 { font-size: 17px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.ch-rec-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }\n.ch-owner { display: inline-flex; align-items: center; gap: 6px; margin: 0; font-weight: 400; color: var(--ch-muted); }\n.ch-owner .ch-in-wrap { width: auto; }\n.ch-owner select.ch-in, .ch-st-select select.ch-in { min-height: 30px; height: 30px; padding-top: 0; padding-bottom: 0; color: var(--ch-fg); }\n.ch-st-select { width: auto; position: relative; }\n.ch-st-select > .ch-dot { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); pointer-events: none; z-index: 1; }\n.ch-st-select select.ch-in { padding-left: 24px; font-weight: 500; }\n.ch-rec .ch-tabs { padding-top: 2px; }\n.ch :where(.ch-iv) { width: 100%; text-align: left; border-radius: 6px; padding: 2px 6px; margin: -2px -6px; overflow-wrap: anywhere; }\n.ch-iv:hover { background: var(--ch-hover); }\n.ch-iv-edit { display: block; min-width: 0; }\n.ch-iv-edit .ch-in { min-height: 28px; padding: 3px 8px; font-size: 12.5px; }\n.ch-iv-edit select.ch-in { height: 28px; }\n.ch-tl-small { padding: 4px 0 !important; }\n.ch-tl-small .ch-tl-text { font-size: 12.5px; color: var(--ch-muted); }\n.ch-tl-small .ch-tl-text b { color: var(--ch-fg); }\n.ch-tl-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ch-light); display: block; }\n.ch-chg { background: var(--ch-subtle); border-radius: 5px; padding: 0 6px; color: var(--ch-fg); }\n.ch-crm-composer .ch-crm-title { background: var(--ch-subtle); }\n.ch-notes { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }\n.ch-note { border: 1px solid var(--ch-border); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }\n.ch-note p { margin: 0; color: var(--ch-muted); overflow-wrap: anywhere; }\n.ch-note .ch-muted { font-size: 11.5px; margin-top: auto; }\n.ch-task-desc { font-size: 12px; margin-top: 2px; }\n.ch-done-list { margin-top: 12px; }\n.ch-done-list summary { cursor: pointer; color: var(--ch-muted); font-size: 12.5px; }\n.ch-contacts { list-style: none; margin: 0 0 6px; padding: 0; }\n.ch-contacts li { display: flex; align-items: center; gap: 6px; padding: 5px 0; }\n.ch-add-contact { margin: 4px 0 8px; }\n.ch-add-contact .ch-in { min-height: 28px; padding: 3px 8px; font-size: 12.5px; }\n.ch-ok-note { display: flex; align-items: center; gap: 6px; background: rgba(22,163,74,.1); color: #15803d; border-radius: 8px; padding: 7px 10px; font-size: 12px; margin-bottom: 12px; }\n.ch-home-head .ch-head-tools { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }\n\n@media (max-width: 640px) {\n\t.ch-crm { padding: 14px 12px 22px; }\n\t.ch-fgrid { grid-template-columns: 1fr; }\n\t.ch-rec-head { padding: 12px; }\n\t.ch-nav { overflow-x: auto; max-width: 100%; }\n\t.ch-nav button { white-space: nowrap; }\n}\n.ch-crm-composer > .ch-seg { align-self: flex-start; }\n.ch-crm-composer > .ch-seg button { display: inline-flex; align-items: center; gap: 5px; }\n\n/* ===================== Email & attachments ===================== */\n.ch-mail-composer.is-over, .ch-drop.is-over { outline: 2px dashed var(--ch-muted); outline-offset: 2px; background: var(--ch-hover); }\n.ch-mail-row { display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--ch-border); padding-bottom: 6px; }\n.ch-mail-row label { width: 56px; flex: none; margin: 0; font-size: 12px; color: var(--ch-muted); font-weight: 400; }\n.ch-mail-row .ch-in { background: transparent; border-color: transparent; padding-left: 0; min-height: 28px; }\n.ch-mail-row .ch-in:focus { background: transparent; border-color: transparent; }\n.ch-mail-body { min-height: 120px; }\n.ch-mail-files { display: flex; flex-wrap: wrap; gap: 6px; }\n.ch-mail-files:empty { display: none; }\n.ch :where(.ch-file-chip) { display: inline-flex; align-items: center; gap: 5px; max-width: 260px; padding: 3px 9px; border-radius: 999px; border: 1px solid var(--ch-border); background: var(--ch-bg); font-size: 12px; color: var(--ch-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.ch-file-chip.is-on { background: var(--ch-ink); color: var(--ch-ink-fg); border-color: var(--ch-ink); }\n.ch-file-chip.is-busy { opacity: .6; }\n.ch-mail-hint { font-size: 11.5px; }\n.ch-drop { display: flex; flex-direction: column; align-items: center; gap: 6px; text-align: center; padding: 22px 16px; border: 1.5px dashed var(--ch-border); border-radius: 12px; color: var(--ch-muted); cursor: pointer; margin-bottom: 14px; }\n.ch-drop b { color: var(--ch-fg); font-weight: 500; }\n.ch-drop:hover { border-color: var(--ch-muted); }\n.ch-drop .ch-muted { font-size: 11.5px; }\n.ch-files { list-style: none; margin: 0; padding: 0; border: 1px solid var(--ch-border); border-radius: 10px; overflow: hidden; }\n.ch-file { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-bottom: 1px solid var(--ch-border); }\n.ch-file:last-child { border-bottom: 0; }\n.ch-file-busy { border: 1px dashed var(--ch-border); border-radius: 10px; margin-bottom: 8px; opacity: .7; }\n.ch-file-ic { width: 38px; height: 38px; flex: none; border-radius: 8px; background: var(--ch-subtle); display: grid; place-items: center; overflow: hidden; color: var(--ch-muted); }\n.ch-file-ic img { width: 100%; height: 100%; object-fit: cover; }\n.ch-file-ic em { font-style: normal; font-size: 10px; font-weight: 700; letter-spacing: .03em; }\n.ch :where(.ch-file-main) { flex: 1; min-width: 0; display: flex; flex-direction: column; text-align: left; }\n.ch-file-main b { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.ch-file-main:hover b { text-decoration: underline; text-underline-offset: 2px; }\n.ch-file-main .ch-muted { font-size: 11.5px; }\n.ch-mail .ch-tl-line .ch-btn-sm { margin-left: auto; height: 22px; padding: 0 7px; font-size: 11.5px; }\n@media (max-width: 640px) { .ch-mail-row label { width: 48px; } }\n.ch-mail-composer .ch-mail-files { justify-content: flex-start; }\n.ch-mail-composer .ch-mail-row { justify-content: flex-start; }\n\n/* ===================== Follow-ups, visits, lead type ===================== */\n.ch-home-col { display: flex; flex-direction: column; gap: 16px; min-width: 0; }\n.ch-home-col .ch-card { margin-bottom: 0; }\n.ch-fu-type { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 600; color: var(--ch-muted); background: var(--ch-subtle); border-radius: 5px; padding: 0 6px; margin-right: 4px; vertical-align: 1px; }\n.ch-nf { display: inline-flex; align-items: center; gap: 5px; color: var(--ch-muted); }\n.ch-nf-none { opacity: .75; }\n.ch-card-fu { align-self: flex-start; margin-top: 3px; display: inline-flex; gap: 4px; }\n.ch-tl-ic.ch-tl-visit { color: #7c3aed; }\n.ch-next { border: 1px solid var(--ch-border); border-radius: 10px; padding: 10px 12px; margin-bottom: 14px; display: flex; flex-direction: column; gap: 8px; }\n.ch-next-h { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; color: var(--ch-muted); }\n.ch-next-row { display: flex; align-items: flex-start; gap: 8px; }\n.ch-next-visit { color: #7c3aed; }\n.ch-next-visit .ch-fu-title { color: var(--ch-fg); }\n.ch-next .ch-btn-sm { align-self: flex-start; }\n.ch-visit-form { display: flex; flex-direction: column; gap: 10px; }\n.ch-v-time { display: flex; gap: 8px; }\n.ch-v-time > * { flex: 1; min-width: 0; }\n.ch-visits { list-style: none; margin: 0; padding: 0; }\n.ch-visit { display: flex; gap: 12px; padding: 10px 0; border-top: 1px solid var(--ch-border); align-items: flex-start; }\n.ch-visit:first-child { border-top: 0; }\n.ch-visit.is-past { opacity: .8; }\n.ch-visit-date { width: 44px; flex: none; text-align: center; border-radius: 9px; background: var(--ch-subtle); padding: 5px 0; display: flex; flex-direction: column; line-height: 1.1; }\n.ch-visit-date b { font-size: 17px; }\n.ch-visit-date span { font-size: 10.5px; text-transform: uppercase; color: var(--ch-muted); letter-spacing: .04em; }\n.ch-visit-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }\n.ch-visit-main b { font-weight: 500; }\n.ch-visit-main .ch-muted { font-size: 12px; display: inline-flex; align-items: center; gap: 3px; flex-wrap: wrap; }\n.ch-visit-notes { font-size: 12px; color: var(--ch-muted); margin-top: 3px; }\n.ch-visit-outcome { font-size: 12.5px; margin-top: 4px; background: rgba(22,163,74,.08); border-radius: 7px; padding: 5px 8px; }\n.ch-visit-act { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }\n.ch-visit-side { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; flex: none; }\n.ch-visit-btns { display: flex; gap: 5px; align-items: center; }\n@media (max-width: 640px) {\n\t.ch-visit { flex-wrap: wrap; }\n\t.ch-visit-side { width: 100%; flex-direction: row; justify-content: space-between; align-items: center; }\n}\n\n/* ===================== Visit plans ===================== */\n.ch-vls { list-style: none; margin: 0 0 12px; padding: 0; display: flex; flex-direction: column; gap: 10px; }\n.ch-vl { display: flex; gap: 12px; border: 1px solid var(--ch-border); border-left: 3px solid #3b82f6; border-radius: 10px; padding: 10px 12px; position: relative; transition: opacity .15s; }\n.ch-vl-visited { border-left-color: #16a34a; }\n.ch-vl-not-visited { border-left-color: #dc2626; }\n.ch-vl-rescheduled { border-left-color: #f59e0b; }\n.ch-vl-cancelled { border-left-color: #9ca3af; opacity: .7; }\n.ch-vl.is-saving { opacity: .6; }\n.ch-vl-num { width: 24px; height: 24px; flex: none; border-radius: 50%; background: var(--ch-subtle); display: grid; place-items: center; font-size: 12px; font-weight: 600; color: var(--ch-muted); margin-top: 18px; }\n.ch-vl-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px; }\n.ch-vl-head { display: grid; grid-template-columns: 110px 130px minmax(0, 1fr) 150px; gap: 8px 10px; align-items: start; }\n.ch-vl-grid { display: grid; grid-template-columns: 160px minmax(0, 1fr) minmax(0, 1.3fr); gap: 8px 10px; }\n.ch-vl-grid .ch-vl-wide:nth-of-type(4) { grid-column: 1 / 3; }\n.ch-vl-f { display: flex; flex-direction: column; gap: 3px; margin: 0; font-weight: 400; min-width: 0; }\n.ch-vl-f > span:first-child { font-size: 11px; color: var(--ch-muted); }\n.ch-vl-f .ch-in { min-height: 30px; padding: 4px 8px; font-size: 12.5px; }\n.ch-vl-f select.ch-in { height: 30px; }\n.ch-vl-f textarea.ch-in { resize: vertical; min-height: 30px; }\n.ch-vl-party { display: flex; gap: 6px; align-items: center; }\n.ch-vl-party .ch-ac { flex: 1; }\n.ch-vl-pname { font-size: 11.5px; color: var(--ch-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.ch-vl-note { font-size: 11px; color: #15803d; display: inline-flex; align-items: center; gap: 3px; margin-top: 2px; }\n.ch-vl-rm { position: absolute; top: 8px; right: 8px; }\n.ch-vl-head { padding-right: 30px; }\n.ch-vl-add { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }\n.ch-vl-add .ch-muted { font-size: 12px; }\n.ch-prog-wide { width: 100%; height: 6px; display: block; margin: 4px 0; }\n.ch-vp-big { font-size: 20px; }\n@media (max-width: 1100px) {\n\t.ch-vl-head { grid-template-columns: 100px 120px minmax(0, 1fr); }\n\t.ch-vl-head > .ch-vl-f:last-child { grid-column: 1 / -1; }\n\t.ch-vl-grid { grid-template-columns: 1fr 1fr; }\n\t.ch-vl-grid .ch-vl-wide { grid-column: 1 / -1 !important; }\n}\n@media (max-width: 640px) {\n\t.ch-vl { flex-direction: column; gap: 6px; }\n\t.ch-vl-num { margin-top: 0; }\n\t.ch-vl-head, .ch-vl-grid { grid-template-columns: 1fr 1fr; }\n\t.ch-vl-head .ch-vl-wide { grid-column: 1 / -1; }\n}\n\n/* ===================== Visit plan lines v2 (planned = editable, finished = locked) ===================== */\n.ch ol.ch-vls, .ch ul.ch-vls { list-style: none !important; padding: 0 !important; margin: 0 0 12px !important; display: flex; flex-direction: column; gap: 10px; }\n.ch .ch-vls > li { list-style: none !important; }\n.ch .ch-vls > li::marker { content: \"\"; }\n.ch .ch-vl { display: flex; align-items: flex-start; gap: 12px; border: 1px solid var(--ch-border); border-left: 3px solid #3b82f6; border-radius: 10px; padding: 12px 14px; margin: 0; background: var(--ch-bg); }\n.ch .ch-vl.is-locked { background: var(--ch-subtle); padding: 10px 14px; }\n.ch .ch-vl-num { margin-top: 2px; }\n.ch .ch-vl.ch-vl-planned .ch-vl-num { margin-top: 20px; }\n.ch .ch-vl-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 10px; }\n.ch .ch-vl-row { display: flex; gap: 10px; align-items: flex-start; flex-wrap: wrap; }\n.ch .ch-vl-f { display: flex; flex-direction: column; gap: 4px; margin: 0; min-width: 0; flex: 0 0 auto; }\n.ch .ch-vl-row1 > .ch-vl-f:nth-child(1) { width: 120px; }\n.ch .ch-vl-row1 > .ch-vl-f:nth-child(2) { width: 130px; }\n.ch .ch-vl-row1 > .ch-vl-f:nth-child(4) { width: 170px; }\n.ch .ch-vl-row2 > .ch-vl-f:nth-child(1) { width: 260px; }\n.ch .ch-vl-f.ch-vl-grow { flex: 1 1 220px; }\n.ch .ch-vl-lbl { display: block; font-size: 11px; line-height: 1.2; color: var(--ch-muted); font-weight: 400; margin: 0; }\n.ch .ch-vl-f .ch-in { height: 32px; min-height: 32px; padding: 4px 9px; font-size: 12.5px; margin: 0; width: 100%; box-sizing: border-box; }\n.ch .ch-vl-f .ch-in-wrap { width: 100%; }\n.ch .ch-vl-f select.ch-in { padding-right: 26px; }\n.ch .ch-vl-party { display: flex; gap: 6px; align-items: center; width: 100%; }\n.ch .ch-vl-party .ch-ac { flex: 1; min-width: 0; }\n.ch .ch-vl-actions, .ch .ch-vl-finish-f { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }\n.ch .ch-grow { flex: 1; }\n.ch .ch-vl-ok { color: #15803d !important; }\n.ch .ch-vl-finish { background: var(--ch-subtle); border-radius: 9px; padding: 10px; display: flex; flex-direction: column; gap: 8px; }\n.ch .ch-vl-finish-h { display: flex; align-items: center; gap: 8px; font-size: 12.5px; }\n.ch .ch-vl-finish textarea.ch-in { background: var(--ch-bg); min-height: 56px; resize: vertical; }\n.ch .ch-vl-inline { display: inline-flex; align-items: center; gap: 8px; margin: 0; font-size: 12px; color: var(--ch-muted); font-weight: 400; }\n.ch .ch-vl-inline .ch-in { width: 160px; height: 30px; min-height: 30px; background: var(--ch-bg); }\n.ch .ch-vl-sum { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }\n.ch .ch-vl-time { font-variant-numeric: tabular-nums; font-weight: 600; }\n.ch .ch-vl-status { display: inline-flex; align-items: center; gap: 6px; margin-left: auto; }\n.ch .ch-vl-lock { color: var(--ch-muted); display: inline-flex; }\n.ch .ch-vl-line { font-size: 12.5px; }\n.ch .ch-vl-line .ch-vl-lbl, .ch .ch-vl-outcome-ro .ch-vl-lbl { display: inline; margin-right: 4px; }\n.ch .ch-vl-outcome-ro { font-size: 12.5px; background: var(--ch-bg); border-radius: 7px; padding: 6px 9px; }\n.ch .ch-vl-reopen { flex: none; align-self: center; }\n.ch .ch-vl-add { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }\n.ch label { margin-bottom: 0; }\n@media (max-width: 760px) {\n\t.ch .ch-vl-row > .ch-vl-f { width: calc(50% - 5px) !important; flex: 0 0 auto !important; }\n\t.ch .ch-vl-row > .ch-vl-f.ch-vl-grow { width: 100% !important; }\n\t.ch .ch-vl.ch-vl-planned .ch-vl-num { margin-top: 2px; }\n\t.ch .ch-vl-status { margin-left: 0; }\n}\n.ch .ch-vl.ch-vl-visited { border-left-color: #16a34a; }\n.ch .ch-vl.ch-vl-not-visited { border-left-color: #dc2626; }\n.ch .ch-vl.ch-vl-rescheduled { border-left-color: #f59e0b; }\n.ch .ch-vl.ch-vl-cancelled { border-left-color: #9ca3af; opacity: .75; }\n\n/* ===================== Layout safety: never wider than the Desk page ===================== */\n.customer-hub-root { min-width: 0; max-width: 100%; }\n.ch { contain: inline-size; max-width: 100%; box-sizing: border-box; }\n.ch-pipe, .ch-board, .ch-table-wrap { max-width: 100%; }\n\n/* ===================== Bigger, simpler CRM ===================== */\n.ch-nav-big button { padding: 7px 14px; font-size: 13px; }\n.ch-quick { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 16px; }\n.ch :where(.ch-quick-btn) { display: grid; grid-template-columns: auto 1fr; grid-template-rows: auto auto; column-gap: 12px; align-items: center; text-align: left;\n\tpadding: 14px 16px; border: 1px solid var(--ch-border); border-radius: 12px; background: var(--ch-bg); }\n.ch-quick-btn:hover { border-color: var(--ch-muted); background: var(--ch-hover); }\n.ch-quick-btn .ch-i { grid-row: 1 / 3; width: 36px; height: 36px; padding: 8px; border-radius: 10px; background: var(--ch-ink); color: var(--ch-ink-fg); }\n.ch-quick-btn b { font-size: 14px; font-weight: 600; }\n.ch-quick-btn span { font-size: 12px; color: var(--ch-muted); }\n.ch-today-grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 16px; align-items: start; margin-bottom: 16px; }\n.ch-today-grid .ch-card { margin-bottom: 0; }\n.ch-todo { list-style: none; margin: 0; padding: 0; }\n.ch-todo-i { display: flex; align-items: flex-start; gap: 12px; padding: 10px 0; border-top: 1px solid var(--ch-border); }\n.ch-todo-i:first-child { border-top: 0; }\n.ch-todo-i.is-done { opacity: .35; }\n.ch-todo-ic { width: 24px; height: 24px; flex: none; display: grid; place-items: center; border-radius: 7px; background: rgba(124,58,237,.12); color: #7c3aed; margin-top: 1px; }\n.ch-todo-ic.ch-todo-lead { background: rgba(234,179,8,.16); color: #a16207; }\n.ch-todo-i .ch-done { width: 24px; height: 24px; }\n.ch-todo-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }\n.ch-todo-main b { font-weight: 500; overflow-wrap: anywhere; }\n.ch-todo-main .ch-muted { font-size: 12px; }\n.ch-todo-btns { display: flex; gap: 6px; flex: none; flex-wrap: wrap; justify-content: flex-end; }\n.ch-todo-btns a.ch-btn { text-decoration: none; color: var(--ch-fg); }\n.ch-todo-finish { margin-top: 8px; }\n.ch-todo-small .ch-todo-i { padding: 7px 0; }\n.ch-mini-kpis { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px; }\n.ch :where(.ch-mini-kpis button) { display: flex; flex-direction: column; text-align: left; padding: 10px 12px; border-radius: 10px; background: var(--ch-subtle); }\n.ch-mini-kpis span { font-size: 11.5px; color: var(--ch-muted); }\n.ch-mini-kpis b { font-size: 20px; }\n.ch-mini-kpis em { font-style: normal; font-size: 11.5px; color: var(--ch-muted); }\n.ch-more-f { margin-top: 14px; }\n.ch-more-f summary { cursor: pointer; color: var(--ch-muted); font-size: 12.5px; margin-bottom: 10px; }\n\n/* Customer Hub: needs-attention box above the list */\n.ch-att-card { padding: 12px 16px; margin-bottom: 14px; }\n.ch-att-card > summary { list-style: none; cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 10px; }\n.ch-att-card > summary::-webkit-details-marker { display: none; }\n.ch-att-card > summary > span:first-child { display: inline-flex; align-items: center; gap: 7px; }\n.ch-att-card[open] > summary { margin-bottom: 10px; }\n.ch-att-cols { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }\n.ch-att-cols > .ch-att-sec + .ch-att-sec { margin-top: 0; }\n.ch-att-cols .ch-att-row { flex-wrap: wrap; }\n.ch-att-cols .ch-att-actions { width: 100%; justify-content: flex-end; }\n@media (max-width: 1100px) { .ch-att-cols { grid-template-columns: 1fr; } }\n@media (max-width: 900px) { .ch-today-grid { grid-template-columns: 1fr; } }\n@media (max-width: 640px) {\n\t.ch-todo-i { flex-wrap: wrap; }\n\t.ch-todo-btns { width: 100%; justify-content: flex-start; padding-left: 36px; }\n\t.ch-nav-big button { padding: 6px 10px; }\n}\n@media (max-width: 640px) {\n\t.ch-quick { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }\n\t.ch :where(.ch-quick-btn) { grid-template-columns: 1fr; justify-items: center; text-align: center; padding: 10px 6px; row-gap: 6px; }\n\t.ch-quick-btn .ch-i { grid-row: auto; }\n\t.ch-quick-btn b { font-size: 12.5px; }\n\t.ch-quick-btn span { display: none; }\n}\n\n/* @mentions */\n.ch-composer { position: relative; }\n.ch .ch-mention-list { position: absolute; width: min(320px, calc(100% - 24px)); right: auto; z-index: 40; }\n.ch-mention { background: rgba(37,99,235,.12); color: #1d4ed8; border-radius: 4px; padding: 0 3px; font-weight: 500; }\n\n/* view switch (Sales CRM | Customer Hub) */\n.customer-hub-view[hidden] { display: none !important; }\n.ch-app-switch { background: var(--ch-ink) !important; padding: 3px; }\n.ch :where(.ch-app-switch button) { color: var(--ch-ink-fg); opacity: .88; display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 7px; font-weight: 500; }\n.ch .ch-app-switch button.is-on { background: var(--ch-ink-fg) !important; color: var(--ch-ink) !important; opacity: 1; box-shadow: none; }\n@media (max-width: 640px) { .ch-app-switch { width: 100%; } .ch :where(.ch-app-switch button) { flex: 1; justify-content: center; } }\n.ch-next-steps { display: inline-flex; align-items: center; gap: 6px; flex-wrap: wrap; padding-left: 8px; border-left: 1px solid var(--ch-border); }\n.ch-next-steps .ch-btn:disabled { opacity: .45; cursor: not-allowed; }\n.ch .ch-app-switch button:not(.is-on) { color: var(--ch-ink-fg) !important; opacity: .9; }\n.ch .ch-app-switch button:not(.is-on):hover { opacity: 1; }\n";
	var el = document.getElementById("customer-hub-css");
	if (!el) { el = document.createElement("style"); el.id = "customer-hub-css"; document.head.appendChild(el); }
	el.textContent = CSS;
})();

if (!window.CustomerHubUI) {
/* Customer Hub UI — framework-free renderer.
   The host (Frappe page or preview) passes in api / navigation / formatting hooks. */
(function (global) {
	const esc = (s) =>
		String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
	const t = (s) => (global.__ ? global.__(s) : s);

	const ICONS = {
		grid: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
		activity: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
		file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
		cart: '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>',
		tool: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
		box: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
		truck: '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
		receipt: '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1z"/><path d="M16 8H8M16 12H8M13 16H8"/>',
		send: '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
		invoice: '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
		wallet: '<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
		comment: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
		mail: '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
		plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
		ext: '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
		refresh: '<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
		chev: '<polyline points="6 9 12 15 18 9"/>',
		search: '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
		phone: '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
		back: '<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>',
		home: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
		users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
		check: '<polyline points="20 6 9 17 4 12"/>',
		x: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
		lock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
		sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
		pin: '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
		clip: '<path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
		send: '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
		reply: '<polyline points="9 17 4 12 9 7"/><path d="M20 18v-2a4 4 0 0 0-4-4H4"/>',
		download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
		upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
		calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
		alert: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
		clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
		moon: '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
		target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
		star: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
		arrow: '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
	};
	const icon = (n, s = 14) =>
		`<svg class="ch-i" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n] || ""}</svg>`;

	const PROGRESS_LABEL = { "Sales Order": "Delivered", "Delivery Note": "Billed" };
	const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
	const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	const niceStep = (max, n) => {
		const raw = max / n, p = Math.pow(10, Math.floor(Math.log10(raw || 1))), f = raw / p;
		return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
	};

	const PERIODS = [
		["all", "All time"], ["this_month", "This month"], ["last_3", "Last 3 months"],
		["this_year", "This year"], ["last_12", "Last 12 months"],
	];

	function statusTone(s) {
		s = (s || "").toLowerCase();
		if (/cancel|overdue|lost|expired|stopped|reject|declin/.test(s)) return "red";
		if (/draft/.test(s)) return "gray";
		if (/completed|paid|ordered|delivered|closed|submitted|received|supplied|done|approved|accepted|won|sent/.test(s) && !/partly|partially|to |pending|waiting/.test(s)) return "green";
		if (/to bill|to deliver|to receive|unpaid|partly|partially|in process|in progress|pending|waiting|review|open|hold/.test(s)) return "amber";
		return "blue";
	}
	const badge = (s) => (s ? `<span class="ch-badge ch-${statusTone(s)}">${esc(t(s))}</span>` : "");

	function timeAgo(ts) {
		if (!ts) return "";
		const d = new Date(String(ts).replace(" ", "T"));
		const s = (Date.now() - d.getTime()) / 1000;
		if (isNaN(s)) return "";
		if (s < 60) return t("just now");
		const units = [[31536000, "year"], [2592000, "month"], [604800, "week"], [86400, "day"], [3600, "hour"], [60, "minute"]];
		for (const [n, u] of units) {
			const v = Math.floor(s / n);
			if (v >= 1) return `${v} ${u}${v > 1 ? "s" : ""} ago`;
		}
		return "";
	}

	const BUCKETS = [
		["not_due", "Not yet due", "b0"], ["d1_30", "1–30 days", "b1"], ["d31_60", "31–60 days", "b2"],
		["d61_90", "61–90 days", "b3"], ["d90_plus", "90+ days", "b4"],
	];
	const ageTone = (d) => (d == null ? "" : d <= 30 ? "b1" : d <= 60 ? "b2" : d <= 90 ? "b3" : "b4");

	const isoDay = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
	const addDays = (n) => { const d = new Date(); d.setDate(d.getDate() + n); return isoDay(d); };
	const daysFrom = (iso) => {
		if (!iso) return null;
		const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
		const a = new Date(y, m - 1, d), b = new Date();
		b.setHours(0, 0, 0, 0);
		return Math.round((a - b) / 86400000);
	};
	const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
	const CALL_PREFIX = "Call: ";

	class CustomerHubUI {
		constructor(root, opts) {
			this.root = root;
			this.o = opts;
			this.app = opts.app === "crm" ? "crm" : "customers";
			this.mode = opts.startMode || (this.app === "crm" ? "home" : "list");
			this.prevMode = "home";
			this.team = false;
			this.home = null;
			this.logKind = "note";
			this.tab = "overview";
			this.period = "all";
			this.filter = "";
			this.actFilter = "all";
			this.chartMode = "invoiced";
			this.customer = null;
			this.data = null;
			this.list = { txt: "", rows: [], has_more: false, start: 0, top: 0, rank_by: "sales", sales_person: "", branch: "", age: "", options: null };
			this.statusFilter = "";
			this.shell();
		}

		money(v, cur) {
			return this.o.fmtMoney(v || 0, cur || (this.data && this.data.currency) || this.list.currency);
		}
		date(d) {
			return d ? this.o.fmtDate(d) : "";
		}
		tabMeta(dt) {
			return ((this.data && this.data.tabs) || []).find((x) => x.dt === dt) || { dt, label: dt, short: dt, icon: "file" };
		}

		shell() {
			this.root.innerHTML = `
			<div class="ch">
				<div class="ch-top">
					${this.o.appSwitch ? `<div class="ch-seg ch-app-switch" role="tablist" aria-label="${t("Switch view")}">
						<button role="tab" data-app-switch="crm" class="${this.app === "crm" ? "is-on" : ""}" aria-selected="${this.app === "crm"}">${icon("target", 13)} ${t("Sales CRM")}</button>
						<button role="tab" data-app-switch="customers" class="${this.app === "customers" ? "is-on" : ""}" aria-selected="${this.app === "customers"}">${icon("users", 13)} ${t("Customer Hub")}</button>
					</div>` : ""}
					${this.app === "crm" ? `<div class="ch-seg ch-nav ch-nav-big" role="tablist" aria-label="${t("Sections")}">
						<button role="tab" data-nav="home">${icon("sun", 14)} ${t("Today")}</button>
						<button role="tab" data-nav="lead" class="ch-nav-crm" hidden>${icon("star", 14)} ${t("Leads")}</button>
						<button role="tab" data-nav="deal" class="ch-nav-crm" hidden>${icon("target", 14)} ${t("Deals")}</button>
						<button role="tab" data-nav="visit" class="ch-nav-crm" hidden>${icon("pin", 14)} ${t("Visits")}</button>
						<button role="tab" data-nav="contact" class="ch-nav-crm" hidden>${icon("phone", 14)} ${t("Contacts")}</button>
					</div>` : `<div class="ch-nav" hidden></div>`}
					<button class="ch-btn ch-soft ch-back" hidden>${icon("back")} ${t("Back")}</button>
					<div class="ch-cust-slot"></div>
					<label class="ch-select ch-period-wrap" title="${t("Period")}">
						<select class="ch-period" aria-label="${t("Period")}">${PERIODS.map(([v, l]) => `<option value="${v}">${t(l)}</option>`).join("")}</select>
						${icon("chev", 12)}
					</label>
					<button class="ch-btn ch-ghost ch-refresh" title="${t("Reload")}" aria-label="${t("Reload")}">${icon("refresh")}</button>
				</div>
				<div class="ch-body"></div>
			</div>`;
			this.$ = (sel) => this.root.querySelector(sel);
			if (this.app === "customers" && this.o.mountCustomerPicker) this.o.mountCustomerPicker(this.$(".ch-cust-slot"), (c) => this.setCustomer(c));
			else this.$(".ch-cust-slot").remove();
			this.$(".ch-period").addEventListener("change", (e) => {
				this.period = e.target.value;
				this.mode === "hub" ? this.load() : this.loadCustomers(true);
			});
			this.$(".ch-refresh").addEventListener("click", () =>
				this.mode === "hub" ? this.load() : this.mode === "home" ? this.loadHome()
				: this.mode === "crm-list" ? this.loadCrmList() : this.mode === "crm-record" ? this.loadCrmRecord() : this.loadCustomers(true));
			this.$(".ch-back").addEventListener("click", () => this.goBack());
			this.root.addEventListener("click", (e) => this.onClick(e));
			this.root.addEventListener("submit", (e) => {
				const f = e.target.closest(".ch-crm-form");
				if (f) { e.preventDefault(); this.crmSubmitForm(f); }
			});
			this.bindBoardDnD();
			this.mode === "list" ? this.showList() : this.showHome();
			if (this.app === "crm") this._crmReady = this.crmInit();
		}

		setModeChrome() {
			const detail = this.mode === "hub" || this.mode === "crm-record";
			this.$(".ch-back").hidden = !detail;
			this.$(".ch-period-wrap").hidden = !(this.mode === "list" || this.mode === "hub");
			const navKey = this.mode === "crm-list" ? this.crm.entity : this.mode;
			this.root.querySelectorAll(".ch-nav [data-nav]").forEach((b) => {
				const on = b.dataset.nav === navKey;
				b.classList.toggle("is-on", on);
				b.setAttribute("aria-selected", on);
			});
		}

		/* ================= Home (sales day view) ================= */
		showHome() {
			this.mode = "home";
			this.stack = [];
			this.customer = null;
			this.data = null;
			this.setModeChrome();
			this.o.onHomeShown && this.o.onHomeShown();
			this.$(".ch-body").innerHTML = `<div class="ch-home"><div class="ch-loading"><span></span><span></span><span></span></div></div>`;
			this.loadHome();
		}

		async loadHome() {
			const req = ++this._homeReq;
			try {
				const h = await this.o.api.home(this.team ? 1 : 0, "crm");
				if (req !== this._homeReq || this.mode !== "home") return;
				this.home = h;
				this.renderHome();
			} catch (err) {
				console.error(err);
				const b = this.$(".ch-home");
				if (b) b.innerHTML = `<div class="ch-empty">${t("Could not load your day. Reload to try again.")}</div>`;
			}
		}

		hmoney(v) {
			return this.o.fmtMoney(v || 0, this.home && this.home.currency);
		}

		dueLabel(iso) {
			const d = daysFrom(iso);
			if (d == null) return { text: t("No date"), tone: "gray" };
			if (d < 0) return { text: `${-d} ${t(-d === 1 ? "day late" : "days late")}`, tone: "red" };
			if (d === 0) return { text: t("Today"), tone: "amber" };
			if (d === 1) return { text: t("Tomorrow"), tone: "blue" };
			if (d < 7) return { text: t(WEEKDAYS[new Date(Date.now() + d * 86400000).getDay()]), tone: "blue" };
			return { text: this.date(iso), tone: "gray" };
		}

		renderHome() {
			const h = this.home, k = h.kpis || {};
			const hour = new Date().getHours();
			const hello = hour < 12 ? t("Good morning") : hour < 17 ? t("Good afternoon") : t("Good evening");
			const today = isoDay(new Date());
			const fu = h.followups || [], vis = h.visits || [];
			const dOf = (iso) => (iso || "").slice(0, 10);
			const firstLeadStatus = (this.crm && this.crm.meta && this.crm.meta.entities && this.crm.meta.entities.lead && (this.crm.meta.entities.lead.statuses[0] || {}).name) || "New";
			const newLeads = (h.leads || []).filter((l) => !l.status || l.status === firstLeadStatus).slice(0, 5);

			const now = [
				...vis.filter((v) => dOf(v.starts_on) <= today).map((v) => ({ kind: "visit", sort: dOf(v.starts_on) + (v.starts_on || "").slice(11, 16), v })),
				...fu.filter((f) => !f.date || f.date <= today).map((f) => ({ kind: "fu", sort: (f.date || today) + "99", f })),
				...newLeads.map((l) => ({ kind: "lead", sort: today + "zz", l })),
			].sort((a, b) => (a.sort < b.sort ? -1 : 1));
			const later = [
				...vis.filter((v) => dOf(v.starts_on) > today).map((v) => ({ kind: "visit", sort: v.starts_on, v })),
				...fu.filter((f) => f.date && f.date > today && daysFrom(f.date) <= 7).map((f) => ({ kind: "fu", sort: f.date + " 99", f })),
			].sort((a, b) => (a.sort < b.sort ? -1 : 1));
			const lateCount = now.filter((x) => (x.kind === "fu" && x.f.date && x.f.date < today) || (x.kind === "visit" && dOf(x.v.starts_on) < today)).length;
			const M = this.crm && this.crm.meta && this.crm.meta.entities ? this.crm.meta.entities : {};

			this.$(".ch-home").innerHTML = `
			<div class="ch-home-head">
				<div><h2>${hello}, ${esc(h.user.first_name)}</h2>
				<div class="ch-muted">${esc(t(WEEKDAYS[new Date().getDay()]))} ${esc(this.date(h.today))} · ${now.length ? `${now.length} ${t(now.length === 1 ? "thing to do" : "things to do")}${lateCount ? `, <b class="ch-red-t">${lateCount} ${t("late")}</b>` : ""}` : t("nothing due right now")}</div></div>
				${h.user.can_team ? `<div class="ch-seg" role="radiogroup" aria-label="${t("Whose work")}">
					<button role="radio" data-team="0" class="${!this.team ? "is-on" : ""}" aria-checked="${!this.team}">${t("Mine")}</button>
					<button role="radio" data-team="1" class="${this.team ? "is-on" : ""}" aria-checked="${this.team}">${t("Team")}</button></div>` : ""}
			</div>
			<div class="ch-quick">
				${M.lead && M.lead.can_create ? `<button class="ch-quick-btn" data-crm-new="lead">${icon("star", 18)}<b>${t("New lead")}</b><span>${t("Someone called or walked in")}</span></button>` : ""}
				${M.visit && M.visit.can_create ? `<button class="ch-quick-btn" data-quick-visit>${icon("pin", 18)}<b>${t("Plan a visit")}</b><span>${t("Adds it to today's plan")}</span></button>` : ""}
				${M.deal && M.deal.can_create ? `<button class="ch-quick-btn" data-crm-new="deal">${icon("target", 18)}<b>${t("New deal")}</b><span>${t("A real opportunity")}</span></button>` : ""}
			</div>
			<div class="ch-today-grid">
				<section class="ch-card ch-today">
					<div class="ch-card-h"><h3>${icon("sun", 14)} ${t("To do now")} <em class="ch-count">${now.length}</em></h3></div>
					${now.length ? `<ul class="ch-todo">${now.map((x) => this.todoItem(x, today)).join("")}</ul>`
						: `<div class="ch-empty ch-empty-sm">${icon("check", 18)}<p>${t("All done. Plan a visit or call a lead.")}</p></div>`}
				</section>
				<section class="ch-card">
					<div class="ch-card-h"><h3>${icon("calendar", 14)} ${t("Coming up")} <em class="ch-count">${later.length}</em></h3><span class="ch-muted">${t("next 7 days")}</span></div>
					${later.length ? `<ul class="ch-todo ch-todo-small">${later.map((x) => this.todoItem(x, today, true)).join("")}</ul>` : `<p class="ch-muted ch-side-note">${t("Nothing planned this week.")}</p>`}
					${k.deals != null ? `<div class="ch-mini-kpis">
						<button data-nav="deal"><span>${t("Open deals")}</span><b>${k.deals}</b><em>${esc(this.hmoney(k.deal_value))}</em></button>
						<button data-nav="visit"><span>${t("Visits this week")}</span><b>${vis.filter((v) => dOf(v.starts_on) >= today).length}</b><em>${t("planned")}</em></button>
					</div>` : ""}
				</section>
			</div>
			${h.pipeline ? this.pipeline(h.pipeline) : ""}`;
		}

		todoItem(x, today, small) {
			const ent = (dt) => DOCTYPE_ENTITY[dt];
			const refBtn = (dt, name, label) => ent(dt) ? `<button class="ch-ref" data-crm-open="${ent(dt)}" data-name="${esc(name)}">${esc(label || name)}</button>`
				: dt === "Customer" ? `<button class="ch-ref" data-customer="${esc(name)}">${esc(label || name)}</button>` : esc(label || name || "");
			if (x.kind === "fu") {
				const f = x.f, due = this.dueLabel(f.date);
				return `<li class="ch-todo-i">
					<button class="ch-done" data-done="${esc(f.kind)}" data-name="${esc(f.name)}" title="${t("Mark as done")}" aria-label="${t("Mark as done")}">${icon("check", 12)}</button>
					<div class="ch-todo-main"><b>${esc(f.title)}</b><span class="ch-muted">${f.ref_name ? refBtn(f.ref_doctype, f.ref_name, f.ref_label) : ""}${this.home.user.team && f.owner ? ` · ${esc(f.owner)}` : ""}</span></div>
					<span class="ch-badge ch-${due.tone}">${esc(due.text)}</span></li>`;
			}
			if (x.kind === "visit") {
				const v = x.v, d = (v.starts_on || "").slice(0, 10), late = d < today;
				const act = this.homeVisitAct && this.homeVisitAct.name === v.name ? this.homeVisitAct.status : null;
				return `<li class="ch-todo-i ch-todo-visit">
					<span class="ch-todo-ic">${icon("pin", 14)}</span>
					<div class="ch-todo-main"><b>${esc(v.type || t("Visit"))}${v.ref_label ? ` · ${refBtn(v.ref_doctype, v.ref_name, v.ref_label)}` : ""}</b>
						<span class="ch-muted">${esc((v.starts_on || "").slice(11, 16))}${v.location ? ` · ${esc(v.location)}` : ""}${v.plan ? ` · <button class="ch-ref" data-crm-open="visit" data-name="${esc(v.plan)}">${esc(v.plan)}</button>` : ""}${this.home.user.team ? ` · ${esc(v.by)}` : ""}</span>
						${act ? `<div class="ch-vl-finish ch-todo-finish"><textarea class="ch-in ch-hv-outcome" rows="2" placeholder="${t(act === "Visited" ? "How did it go?" : "Why didn't it happen?")}"></textarea>
							<div class="ch-vl-finish-f"><label class="ch-vl-inline">${t("Next follow-up")} <input type="date" class="ch-in ch-hv-nfd"></label><span class="ch-grow"></span>
							<button class="ch-btn ch-soft ch-btn-sm" data-hv-back>${t("Back")}</button>
							<button class="ch-btn ch-primary ch-btn-sm" data-hv-save="${esc(act)}" data-plan="${esc(v.plan)}" data-line="${esc(v.name)}">${icon("lock", 12)} ${t("Save")}</button></div></div>` : ""}
					</div>
					${small ? `<span class="ch-badge ch-blue">${esc(this.dueLabel(d).text)}</span>`
						: act ? "" : v.plan ? `<div class="ch-todo-btns"><button class="ch-btn ch-soft ch-btn-sm ch-vl-ok" data-hv="Visited" data-name="${esc(v.name)}">${icon("check", 12)} ${t("Visited")}</button>
							<button class="ch-btn ch-soft ch-btn-sm" data-hv="Not Visited" data-name="${esc(v.name)}">${t("Not visited")}</button></div>`
						: `<span class="ch-badge ch-${late ? "red" : "amber"}">${t(late ? "Late" : "Today")}</span>`}
				</li>`;
			}
			const l = x.l;
			return `<li class="ch-todo-i">
				<span class="ch-todo-ic ch-todo-lead">${icon("star", 14)}</span>
				<div class="ch-todo-main"><b><button class="ch-ref" data-crm-open="lead" data-name="${esc(l.name)}">${esc(l.lead_name)}</button></b><span class="ch-muted">${esc(t("New lead"))}${l.organization ? ` · ${esc(l.organization)}` : ""}</span></div>
				<div class="ch-todo-btns">${l.mobile_no ? `<a class="ch-btn ch-soft ch-btn-sm" href="tel:${esc(l.mobile_no)}">${icon("phone", 12)} ${t("Call")}</a>` : ""}
					<button class="ch-btn ch-soft ch-btn-sm" data-crm-open="lead" data-name="${esc(l.name)}">${t("Open")}</button></div></li>`;
		}

		followupList(list, opt = {}) {
			if (!list.length)
				return `<div class="ch-empty ch-empty-sm">${icon("check", 18)}<p>${t("You're all caught up.")}</p></div>`;
			const groups = [
				["Late", (d) => d != null && d < 0],
				["Today", (d) => d === 0],
				["This week", (d) => d != null && d > 0 && d < 7],
				["Later", (d) => d == null || d >= 7],
			];
			return groups.map(([label, test]) => {
				const items = list.filter((f) => test(daysFrom(f.date)));
				if (!items.length) return "";
				return `<div class="ch-fu-group"><div class="ch-fu-gl ${label === "Late" ? "ch-red-t" : ""}">${t(label)} <span>${items.length}</span></div>
					<ul class="ch-fu">${items.map((f) => {
						const due = this.dueLabel(f.date);
						const ref = f.ref_doctype === "Customer"
							? `<button class="ch-ref" data-customer="${esc(f.ref_name)}">${esc(f.ref_label)}</button>`
							: f.ref_name && DOCTYPE_ENTITY[f.ref_doctype] ? `<button class="ch-ref" data-crm-open="${DOCTYPE_ENTITY[f.ref_doctype]}" data-name="${esc(f.ref_name)}">${esc(f.ref_label || f.ref_name)}</button>`
							: f.ref_name ? `<button class="ch-ref" data-open-ref="${esc(f.ref_doctype)}" data-name="${esc(f.ref_name)}">${esc(f.ref_label || f.ref_name)}</button>` : "";
						return `<li>
							<button class="ch-done" data-done="${esc(f.kind)}" data-name="${esc(f.name)}" title="${t("Mark as done")}" aria-label="${t("Mark as done")}">${icon("check", 12)}</button>
							<div class="ch-fu-main"><div class="ch-fu-title">${esc(f.title)}</div>
								<div class="ch-fu-meta">${opt.showRef && ref ? ref : ""}${f.kind === "crm_task" ? `<span class="ch-tag">CRM</span>` : ""}${opt.showOwner && f.owner ? `<span class="ch-muted">${esc(f.owner)}</span>` : ""}</div></div>
							<span class="ch-badge ch-${due.tone}">${esc(due.text)}</span></li>`;
					}).join("")}</ul></div>`;
			}).join("");
		}

		attention(att) {
			const actions = (c, text) => `<div class="ch-att-actions">
				${c.mobile_no ? `<a class="ch-icon-btn" href="tel:${esc(c.mobile_no)}" title="${t("Call")} ${esc(c.mobile_no)}" aria-label="${t("Call")}">${icon("phone")}</a>` : ""}
				<button class="ch-btn ch-soft ch-btn-sm" data-fu-open="${esc(c.customer)}" data-fu-text="${esc(text)}">${icon("calendar", 12)} ${t("Follow up")}</button></div>`;
			const row = (c, sub, right, text) => `<li class="ch-att-row">
				<button class="ch-att-main" data-customer="${esc(c.customer)}"><b>${esc(c.customer_name)}</b><span class="ch-muted">${sub}</span></button>
				${right}${actions(c, text)}</li>`;
			const sec = (title, ic, tone, items, render) => items.length ? `<div class="ch-att-sec"><div class="ch-att-h"><span class="ch-att-ic ch-${tone}">${icon(ic, 12)}</span>${t(title)} <span class="ch-muted">${items.length}</span></div><ul class="ch-att">${items.map(render).join("")}</ul></div>` : "";
			const html =
				sec("Overdue payments", "alert", "red", att.overdue, (c) => row(c, `${t("oldest invoice")} ${c.days} ${t("days late")}`,
					`<span class="ch-att-amt">${esc(this.hmoney(c.amount))}</span>`, `${t("Chase payment")} ${this.hmoney(c.amount)}`)) +
				sec("Quotations expiring", "clock", "amber", att.expiring, (q) => {
					const d = daysFrom(q.valid_till);
					const when = d < 0 ? `${t("expired")} ${-d} ${t(-d === 1 ? "day ago" : "days ago")}` : d === 0 ? t("expires today") : d === 1 ? t("expires tomorrow") : `${t("expires in")} ${d} ${t("days")}`;
					return row(q, `${esc(q.name)} · ${when}`, `<span class="ch-att-amt">${esc(this.o.fmtMoney(q.amount, q.currency))}</span>`, `${t("Follow up quotation")} ${q.name}`);
				}) +
				sec("Gone quiet", "moon", "blue", att.quiet, (c) => row(c, `${t("last invoice")} ${c.days} ${t("days ago")}`,
					`<span class="ch-att-amt ch-muted" title="${t("Invoiced in the last 18 months")}">${esc(this.hmoney(c.sales))}</span>`, t("Check in: no order recently")));
			return html || `<div class="ch-empty ch-empty-sm">${icon("star", 18)}<p>${t("Nothing urgent. Nice work.")}</p></div>`;
		}

		fuForm(customer, text) {
			return `<div class="ch-fu-form">
				<input type="text" class="ch-fu-text" value="${esc(text)}" aria-label="${t("What to follow up")}">
				<div class="ch-fu-when">${[["Tomorrow", 1], ["In 3 days", 3], ["Next week", 7]].map(([l, n], i) =>
					`<button class="ch-chip-btn ${i === 0 ? "is-on" : ""}" data-fu-days="${n}">${t(l)}</button>`).join("")}
					<input type="date" class="ch-fu-date" value="${addDays(1)}" aria-label="${t("Date")}"></div>
				<div class="ch-fu-btns"><button class="ch-btn ch-soft ch-btn-sm ch-fu-cancel">${t("Cancel")}</button>
				<button class="ch-btn ch-primary ch-btn-sm ch-fu-save" data-fu-customer="${esc(customer)}">${icon("check", 12)} ${t("Save follow-up")}</button></div></div>`;
		}

		pipeline(p) {
			if (!p.columns.length) return "";
			return `<section class="ch-card">
				<div class="ch-card-h"><h3>${icon("target", 14)} ${t("Deal pipeline")} <em class="ch-count">${p.count}</em></h3>
					<span class="ch-muted">${this.hmoney(p.value)} · <button class="ch-link" data-nav="deal">${t("All deals")}</button></span></div>
				<div class="ch-pipe">${p.columns.map((c) => `<div class="ch-pipe-col">
					<div class="ch-pipe-h"><span class="ch-dot ch-pc-${esc(c.color)}"></span><b>${esc(c.status)}</b><span class="ch-muted">${c.count}</span></div>
					<div class="ch-pipe-v">${this.hmoney(c.value)}</div>
					${c.deals.map((d) => `<button class="ch-deal" data-crm-open="deal" data-name="${esc(d.name)}">
						<b>${esc(d.organization)}</b>
						<span>${d.value ? esc(this.o.fmtMoney(d.value, d.currency)) : ""}${d.close_date ? ` · ${esc(this.date(d.close_date))}` : ""}</span>
						${this.home.user.team && d.owner ? `<span class="ch-muted">${esc(d.owner)}</span>` : ""}</button>`).join("")}
					${c.count > c.deals.length ? `<div class="ch-muted ch-pipe-more">+${c.count - c.deals.length} ${t("more")}</div>` : ""}
					${!c.count ? `<div class="ch-pipe-empty">—</div>` : ""}
				</div>`).join("")}</div></section>`;
		}

		leadsList(leads) {
			const url = this.home.crm_route || "/crm";
			return `<section class="ch-card">
				<div class="ch-card-h"><h3>${icon("star", 14)} ${t("My latest leads")}</h3><button class="ch-link" data-nav="lead">${t("All leads")}</button></div>
				<ul class="ch-leads">${leads.map((l) => `<li>
					<button class="ch-att-main" data-crm-open="lead" data-name="${esc(l.name)}"><b>${esc(l.lead_name)}</b><span class="ch-muted">${esc(l.organization || "")}</span></button>
					${badge(l.status)}
					${l.mobile_no ? `<a class="ch-icon-btn" href="tel:${esc(l.mobile_no)}" title="${t("Call")} ${esc(l.mobile_no)}" aria-label="${t("Call")}">${icon("phone")}</a>` : ""}
					${l.email ? `<a class="ch-icon-btn" href="mailto:${esc(l.email)}" title="${t("Email")}" aria-label="${t("Email")}">${icon("mail")}</a>` : ""}
				</li>`).join("")}</ul></section>`;
		}

		/* ================= Customer list (landing) ================= */
		showList() {
			this.mode = "list";
			this.stack = [];
			this.customer = null;
			this.data = null;
			this.setModeChrome();
			this.o.onListShown && this.o.onListShown();
			this.$(".ch-body").innerHTML = `<div class="ch-list">
				<div class="ch-head"><div><h2>${t("Customers")}</h2><div class="ch-muted ch-scope"></div></div>
					<div class="ch-head-tools">
						<label class="ch-select ch-select-sm"><select class="ch-top-n" aria-label="${t("Show")}">${[[0, "All customers"], [10, "Top 10"], [20, "Top 20"], [50, "Top 50"]]
							.map(([v, l]) => `<option value="${v}" ${+this.list.top === v ? "selected" : ""}>${t(l)}</option>`).join("")}</select>${icon("chev", 12)}</label>
						<label class="ch-select ch-select-sm ch-rank-wrap" ${this.list.top ? "" : "hidden"}><select class="ch-rank-by" aria-label="${t("Rank by")}">${[["sales", "By sales"], ["outstanding", "By outstanding"]]
							.map(([v, l]) => `<option value="${v}" ${this.list.rank_by === v ? "selected" : ""}>${t(l)}</option>`).join("")}</select>${icon("chev", 12)}</label>
						<label class="ch-search">${icon("search")}<input class="ch-cust-search" value="${esc(this.list.txt)}" placeholder="${t("Search customers")}" aria-label="${t("Search customers")}"></label>
					</div></div>
				<div class="ch-list-att"></div>
				<div class="ch-filters"></div>
				<div class="ch-list-body"><div class="ch-loading"><span></span><span></span><span></span></div></div>
			</div>`;
			this.loadCustomers(true);
			this.loadAttention();
		}

		async loadAttention() {
			if (!this.o.api.home) return;
			try {
				const h = await this.o.api.home(0, "customers");
				this.home = h;
				const box = this.$(".ch-list-att");
				if (!box || this.mode !== "list") return;
				const att = h.attention, n = new Set([...att.overdue, ...att.expiring, ...att.quiet].map((x) => x.customer)).size;
				if (!n) { box.innerHTML = ""; return; }
				box.innerHTML = `<details class="ch-card ch-att-card" ${this._attOpen === false ? "" : "open"}>
					<summary><span>${icon("alert", 14)} <b>${t("Needs attention")}</b> <em class="ch-count">${n}</em></span><span class="ch-muted">${t("customers to chase today")}</span></summary>
					<div class="ch-att-cols">${this.attention(att)}</div></details>`;
				box.querySelector("details").addEventListener("toggle", (e) => (this._attOpen = e.target.open));
			} catch (e) { /* attention box is optional */ }
		}

		async loadCustomers(reset) {
			if (reset) this.list.start = 0;
			const req = ++this._listReq;
			try {
				const [from_date, to_date] = this.range();
				const res = await this.o.api.customers(this.list.txt, this.list.start, {
					top: this.list.top, rank_by: this.list.rank_by, from_date, to_date,
					sales_person: this.list.sales_person, branch: this.list.branch, age: this.list.age,
				});
				if (req !== this._listReq || this.mode !== "list") return;
				this.list.rows = reset ? res.rows : this.list.rows.concat(res.rows);
				this.list.has_more = res.has_more;
				this.list.currency = res.currency;
				this.list.ageing = res.ageing;
				if (res.filters) this.list.options = res.filters;
				this.list.restricted = res.restricted;
				this.list.sales_persons = res.sales_persons || [];
				this.renderList();
			} catch (err) {
				console.error(err);
				const b = this.$(".ch-list-body");
				if (b) b.innerHTML = `<div class="ch-empty">${t("Could not load customers. Reload to try again.")}</div>`;
			}
		}

		ageing(a, opts = {}) {
			if (!a) return "";
			const pos = BUCKETS.map(([k]) => Math.max(0, a[k] || 0));
			const sumPos = pos.reduce((x, y) => x + y, 0) || 1;
			const overdue = a.total - (a.not_due || 0);
			return `<div class="ch-age ${opts.compact ? "ch-age-compact" : ""}">
				<div class="ch-age-total">
					<span class="ch-stat-l">${t(opts.title || "Total outstanding")}</span>
					<span class="ch-age-v">${esc(this.money(a.total))}</span>
					<span class="ch-stat-s">${opts.sub || ""}${overdue > 0 ? `<b class="ch-age-od">${esc(this.money(overdue))} ${t("overdue")}</b>` : `<b class="ch-age-ok">${t("Nothing overdue")}</b>`}</span>
				</div>
				<div class="ch-age-main">
					<div class="ch-age-bar" role="img" aria-label="${t("Outstanding by age")}">${BUCKETS.map(([k, , c], i) =>
						pos[i] ? `<i class="ch-${c}" style="width:${(pos[i] / sumPos) * 100}%"></i>` : "").join("")}</div>
					<div class="ch-age-buckets">${BUCKETS.map(([k, l, c]) => {
						const tag = opts.clickable ? "button" : "div";
						const attrs = opts.clickable ? ` data-age="${k}" class="ch-age-btn ${opts.active === k ? "is-on" : ""}" aria-pressed="${opts.active === k}" title="${t("Show customers whose oldest invoice is")} ${t(l).toLowerCase()}"` : "";
						return `<${tag}${attrs}>
						<span class="ch-age-l"><i class="ch-dot ch-${c}"></i>${t(l)}</span>
						<span class="ch-age-a ${a[k] ? "" : "ch-light"}">${esc(this.money(a[k] || 0))}</span>
						<span class="ch-sub">${a.total ? Math.round(((a[k] || 0) / a.total) * 100) : 0}%</span></${tag}>`;
					}).join("")}</div>
				</div>
			</div>`;
		}

		renderFilters() {
			const L = this.list, O = L.options || { sales_persons: [], branches: [] };
			const el = this.$(".ch-filters");
			if (!el) return;
			const sel = (cls, label, all, opts, val) => `<label class="ch-filter-f"><span>${t(label)}</span>
				<span class="ch-select ch-select-sm ${val ? "is-set" : ""}"><select class="${cls}" aria-label="${t(label)}">
				<option value="">${t(all)}</option>${opts.map(([v, l]) => `<option value="${esc(v)}" ${v === val ? "selected" : ""}>${esc(t(l))}</option>`).join("")}
				</select>${icon("chev", 12)}</span></label>`;
			const ages = [["outstanding", "Has outstanding"], ["overdue", "Any overdue"], ["not_due", "Not yet due"],
				["d1_30", "1–30 days overdue"], ["d31_60", "31–60 days overdue"], ["d61_90", "61–90 days overdue"], ["d90_plus", "90+ days overdue"]];
			const sp = O.sales_persons.length > 1 || L.sales_person
				? sel("ch-f-sp", "Sales person", "All sales persons", O.sales_persons.map((x) => [x, x]), L.sales_person) : "";
			const br = O.branch_mode ? sel("ch-f-branch", "Branch", "All branches", O.branches.map((x) => [x, x]), L.branch) : "";
			el.innerHTML = `${sp}${br}${sel("ch-f-age", "Age", "All ages", ages, L.age)}
				${L.sales_person || L.branch || L.age ? `<button class="ch-link ch-f-clear">${t("Clear filters")}</button>` : ""}`;
		}

		renderList() {
			const L = this.list;
			this.renderFilters();
			const scope = this.$(".ch-scope");
			const periodLabel = t((PERIODS.find((p) => p[0] === this.period) || PERIODS[0])[1]).toLowerCase();
			const topText = L.top ? ` · ${t("Top")} ${L.top} ${L.rank_by === "outstanding" ? t("by outstanding") : `${t("by sales")}, ${periodLabel}`}` : "";
			if (scope)
				scope.textContent = (!L.restricted
					? t("All customers")
					: L.sales_persons.length
					? `${t("Customers assigned to")} ${L.sales_persons.join(", ")}`
						: t("Customers where you are the account manager")) + topText;
			const body = this.$(".ch-list-body");
			if (!body) return;
			if (!L.rows.length) {
				body.innerHTML = `<div class="ch-empty">${
					L.txt
						? t("No customer matches your search.")
						: L.sales_person || L.branch || L.age
						? t("No customer matches these filters.")
						: L.top
						? t("No invoiced customers in this period.")
						: L.restricted && !L.sales_persons.length
						? t("Your user is not linked to a Sales Person. Ask an admin to set your user on an Employee, and that Employee on a Sales Person.")
						: t("No customers are assigned to you yet.")
				}</div>`;
				return;
			}
			const max = Math.max(...L.rows.map((r) => (L.rank_by === "outstanding" ? r.outstanding : r.sales)), 1);
			const A = L.ageing;
			const filtered = L.sales_person || L.branch || L.age;
			body.innerHTML = `${A ? `<section class="ch-card ch-age-card">${this.ageing(A, {
				title: filtered ? "Outstanding (filtered)" : L.restricted ? "Outstanding on your customers" : "Total outstanding",
				sub: `${A.customers} ${t("customers")} · ${A.invoices} ${t("invoices")}`,
				clickable: true, active: L.age,
			})}</section>` : ""}<div class="ch-table-wrap"><table class="ch-table">
				<thead><tr>${L.top ? `<th class="ch-rank">#</th>` : ""}<th>${t("Customer")}</th><th class="ch-hide-sm">${t("Territory")}</th>
				<th class="ch-hide-sm">${t("Sales person")}</th><th class="ch-r">${t("Sales")}</th><th class="ch-r">${t("Outstanding")}</th><th>${t("Age")}</th><th class="ch-hide-sm">${t("Last invoice")}</th></tr></thead>
				<tbody>${L.rows
					.map(
						(r, i) => `<tr data-customer="${esc(r.name)}" tabindex="0">
						${L.top ? `<td class="ch-rank">${i + 1}</td>` : ""}
						<td><div class="ch-cell-id"><span class="ch-av">${esc((r.customer_name || "?").trim().charAt(0).toUpperCase())}</span><div><b>${esc(r.customer_name)}</b>${(r.customer_name || "").trim() !== (r.name || "").trim() ? `<div class="ch-sub">${esc(r.name)}</div>` : ""}</div></div></td>
						<td class="ch-hide-sm ch-muted">${esc(r.territory)}</td>
						<td class="ch-hide-sm ch-muted">${esc((r.sales_persons || []).join(", "))}</td>
						<td class="ch-r ch-nowrap ${r.sales ? "" : "ch-light"}">${esc(this.money(r.sales))}${L.top && L.rank_by === "sales" ? `<div class="ch-meter"><i style="width:${(r.sales / max) * 100}%"></i></div>` : ""}</td>
						<td class="ch-r ch-nowrap ${r.outstanding > 0 ? "" : "ch-light"}">${esc(this.money(r.outstanding))}${L.top && L.rank_by === "outstanding" ? `<div class="ch-meter"><i style="width:${(r.outstanding / max) * 100}%"></i></div>` : ""}</td>
						<td class="ch-nowrap">${r.age_days != null
							? `<span class="ch-age-pill ch-${ageTone(r.age_days)}-soft" title="${t("Oldest unpaid invoice is overdue by")} ${r.age_days} ${t("days")}">${r.age_days} ${t("days")}</span>`
							: r.outstanding > 0 ? `<span class="ch-age-pill ch-b0-soft">${t("Not due")}</span>` : `<i class="ch-light">—</i>`}</td>
						<td class="ch-hide-sm ch-nowrap">${r.last_invoice ? esc(this.date(r.last_invoice)) : `<i class="ch-light">—</i>`}</td></tr>`
					)
					.join("")}</tbody></table></div>
				${L.has_more ? `<div class="ch-more"><button class="ch-btn ch-soft ch-load-more">${t("Load more")}</button></div>` : ""}`;
		}

		/* ================= Customer hub ================= */
		setCustomer(c, noPush) {
			if (!c || (c === this.customer && this.mode === "hub")) return;
			if (!noPush) this.pushView();
			this.customer = c;
			this.mode = "hub";
			this.setModeChrome();
			this.$(".ch-body").innerHTML = `<div class="ch-hub"><div class="ch-main"><nav class="ch-tabs" role="tablist"></nav><div class="ch-content"></div></div><aside class="ch-side"></aside></div>`;
			this.o.onCustomerShown && this.o.onCustomerShown(c);
			this.load();
		}

		range() {
			const now = new Date();
			const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
			const to = iso(now);
			switch (this.period) {
				case "this_month": return [iso(new Date(now.getFullYear(), now.getMonth(), 1)), to];
				case "last_3": return [iso(new Date(now.getFullYear(), now.getMonth() - 2, 1)), to];
				case "this_year": return [iso(new Date(now.getFullYear(), 0, 1)), to];
				case "last_12": return [iso(new Date(now.getFullYear(), now.getMonth() - 11, 1)), to];
				default: return [null, null];
			}
		}

		async load() {
			if (!this.customer || this.mode !== "hub") return;
			this.$(".ch-content").innerHTML = `<div class="ch-loading"><span></span><span></span><span></span></div>`;
			try {
				const [f, to] = this.range();
				const data = await this.o.api.load(this.customer, f, to);
				if (this.mode !== "hub" || !this.$(".ch-content")) return;
				this.data = data;
				if (this.tab !== "overview" && this.tab !== "activity" && !data.tabs.some((x) => x.dt === this.tab)) this.tab = "overview";
				this.renderAll();
			} catch (err) {
				console.error(err);
				this.$(".ch-tabs").innerHTML = "";
				this.$(".ch-side").innerHTML = "";
				this.$(".ch-content").innerHTML = `<div class="ch-empty">${t("You can't open this customer. It may not be assigned to your Sales Person, or you lack read access.")}</div>`;
			}
		}

		renderAll() {
			this.renderTabs();
			this.renderSide();
			this.renderContent();
		}

		count(dt) {
			return (this.data.docs[dt] || []).length;
		}

		renderTabs() {
			const tabs = [
				{ key: "overview", label: "Overview", icon: "grid" },
				{ key: "activity", label: "Activity", icon: "activity", n: this.data.activity.length },
				...this.data.tabs.map((d) => ({ key: d.dt, label: d.label, icon: d.icon, n: this.count(d.dt) })),
			];
			this.$(".ch-tabs").innerHTML = tabs
				.map(
					(x) => `<button role="tab" class="ch-tab ${this.tab === x.key ? "is-active" : ""}" data-tab="${esc(x.key)}" aria-selected="${this.tab === x.key}">
						${icon(x.icon)}<span>${t(x.label)}</span>${x.n != null ? `<em>${x.n}</em>` : ""}</button>`
				)
				.join("");
		}

		renderContent() {
			const c = this.$(".ch-content");
			if (this.tab === "overview") c.innerHTML = this.overview();
			else if (this.tab === "activity") c.innerHTML = this.activityView();
			else c.innerHTML = this.docView(this.tab);
		}

		/* ---------------- Overview ---------------- */
		overview() {
			const k = this.data.kpis, cur = this.data.currency;
			const stats = [
				{ l: "Total sales", v: this.money(k.total_sales, cur), s: `${k.invoice_count} ${t("invoices")}`, tab: "Sales Invoice" },
				{ l: "Outstanding", v: this.money(k.outstanding, cur), s: k.overdue ? `${this.money(k.overdue, cur)} ${t("overdue")}` : t("Nothing overdue"), tone: k.overdue ? "red" : "" },
				{ l: "Open quotations", v: k.open_quotations, s: this.money(k.open_quotation_value, cur), tab: "Quotation" },
				{ l: "Payments received", v: this.money(k.received, cur), s: `${k.payment_count} ${t("payments")}`, tab: "Payment Entry" },
			];
			for (const [dt, c] of Object.entries(k.custom || {})) {
				stats.push({ l: this.tabMeta(dt).label, v: c.count, s: `${c.open} ${t("open")}${c.amount ? ", " + this.money(c.amount, cur) : ""}`, tab: dt });
			}
			const notes = (this.data.setup_notes || []).map((n) => `<div class="ch-warn">${esc(n)}</div>`).join("");
			return `${notes}
			<div class="ch-head"><h2>${t("Overview")}</h2>
				<span class="ch-muted">${k.last_invoice_date ? `${t("Last invoice")} ${this.date(k.last_invoice_date)}` : t("No invoices yet")}${k.conversion_rate != null ? ` &nbsp;|&nbsp; ${t("Quote to order")} ${k.conversion_rate}%` : ""}</span></div>
			<div class="ch-stats">${stats
				.map(
					(s) => `<${s.tab ? `button data-tab="${esc(s.tab)}"` : "div"} class="ch-stat ${s.tone ? "ch-stat-" + s.tone : ""}">
						<span class="ch-stat-l">${t(s.l)}</span><span class="ch-stat-v">${s.v}</span><span class="ch-stat-s">${s.s}</span></${s.tab ? "button" : "div"}>`
				)
				.join("")}</div>
			${k.ageing && k.ageing.invoices ? `<section class="ch-card ch-age-card">${this.ageing(k.ageing, {
				title: "Outstanding by age",
				sub: `${k.ageing.invoices} ${t("unpaid invoices")}${k.ageing.max_days ? `, ${t("oldest")} ${k.ageing.max_days} ${t("days overdue")}` : ""}`,
			})}</section>` : ""}
			<section class="ch-card ch-chart-card">${this.chart()}</section>
			<section class="ch-card">
				<div class="ch-card-h"><h3>${t("Document flow")}</h3><span class="ch-muted">${t("Click a step to open its list")}</span></div>
				${this.flow(this.data.tabs.map((x) => x.dt))}
			</section>
			<section class="ch-card">
				<div class="ch-card-h"><h3>${t("Recent activity")}</h3><button class="ch-link" data-tab="activity">${t("View all")}</button></div>
				${this.timeline(this.data.activity.slice(0, 6))}
			</section>`;
		}

		chart() {
			const modes = [["invoiced", "Invoiced", "invoices"], ["received", "Received", "payments"], ["quoted", "Quoted", "quotations"]];
			const [, , unit] = modes.find((m) => m[0] === this.chartMode);
			const m = (this.data.monthly && this.data.monthly[this.chartMode]) || [];
			const total = m.reduce((a, x) => a + x.value, 0);
			const active = m.filter((x) => x.value).length;
			const best = m.reduce((b, x) => (x.value > (b ? b.value : 0) ? x : b), null);
			const label = (x, long) => { const [y, mo] = x.month.split("-"); return long ? `${MONTHS[+mo - 1]} ${y}` : MONTHS[+mo - 1]; };
			const max = Math.max(...m.map((x) => x.value), 0);
			const step = max ? niceStep(max, 4) : 1;
			const top = max ? Math.ceil(max / step) * step : 4;
			const ticks = [];
			for (let v = top; v >= 0; v -= step) ticks.push(v);
			const nowKey = (() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; })();

			return `
			<div class="ch-chart-head">
				<div>
					<h3>${t("Last 12 months")}</h3>
					<div class="ch-seg" role="radiogroup" aria-label="${t("Chart data")}">${modes
						.map(([k, l]) => `<button role="radio" aria-checked="${k === this.chartMode}" class="${k === this.chartMode ? "is-on" : ""}" data-chart="${k}">${t(l)}</button>`)
						.join("")}</div>
				</div>
				<dl class="ch-chart-sum">
					<div><dt>${t("Total")}</dt><dd>${esc(this.money(total))}</dd></div>
					<div><dt>${t("Monthly average")}</dt><dd>${esc(this.money(total / 12))}</dd></div>
					<div><dt>${t("Best month")}</dt><dd>${best ? esc(label(best, true)) : "—"}</dd></div>
				</dl>
			</div>
			${!active ? `<div class="ch-empty ch-empty-chart">${t("Nothing")} ${t(this.chartMode)} ${t("in the last 12 months.")}</div>` : `
			<div class="ch-plot">
				<div class="ch-yaxis">${ticks.map((v) => `<span>${compact.format(v)}</span>`).join("")}</div>
				<div class="ch-plot-area">
					<div class="ch-grid">${ticks.map(() => "<i></i>").join("")}</div>
					<div class="ch-cols">${m
						.map((x, i) => {
							const h = top ? (x.value / top) * 100 : 0;
							const cls = ["ch-col", x.month === nowKey ? "is-now" : "", x === best ? "is-best" : "", i > 8 ? "tip-end" : i < 3 ? "tip-start" : ""].join(" ");
							return `<div class="${cls}" tabindex="0" aria-label="${esc(label(x, true))}: ${esc(this.money(x.value))}">
								<div class="ch-col-track"><div class="ch-col-bar" style="height:${x.value ? Math.max(h, 1.5) : 0}%"></div></div>
								<span class="ch-col-x">${label(x)}</span>
								<span class="ch-tip"><b>${esc(label(x, true))}${x.month === nowKey ? ` (${t("so far")})` : ""}</b>${esc(this.money(x.value))}<small>${x.count} ${t(unit)}</small></span>
							</div>`;
						})
						.join("")}</div>
				</div>
			</div>`}`;
		}

		flow(list) {
			return `<div class="ch-flow">${list
				.map((dt, i) => {
					const d = this.tabMeta(dt);
					return `${i ? `<span class="ch-flow-arrow">${icon("arrow", 12)}</span>` : ""}
					<button class="ch-flow-step" data-tab="${esc(dt)}">${icon(d.icon)}<b>${this.count(dt)}</b><span>${t(d.label)}</span></button>`;
				})
				.join("")}</div>`;
		}

		/* ---------------- Activity ---------------- */
		activityView() {
			const opts = [["all", "Everything"], ["comment", "Notes & calls"], ["email", "Emails"], ...this.data.tabs.map((d) => [d.dt, d.label])];
			const list = this.data.activity.filter((e) =>
				this.actFilter === "all" ? true : this.actFilter === "comment" || this.actFilter === "email" ? e.kind === this.actFilter : e.kind === "doc" && e.doctype === this.actFilter
			);
			return `
			<div class="ch-head"><h2>${t("Activity")}</h2>
				<label class="ch-select ch-select-sm"><select class="ch-act-filter" aria-label="${t("Filter activity")}">${opts
					.map(([v, l]) => `<option value="${esc(v)}" ${v === this.actFilter ? "selected" : ""}>${t(l)}</option>`)
					.join("")}</select>${icon("chev", 12)}</label></div>
			${this.composer()}
			${this.timeline(list)}`;
		}

		composer() {
			const k = this.logKind;
			const kinds = [["note", "comment", "Note"], ["call", "phone", "Call"], ["followup", "calendar", "Follow-up"]];
			const ph = { note: "Add a note about this customer…", call: "What was the call about? Outcome, next step…", followup: "What should happen next? e.g. Send revised quotation" }[k];
			const btn = { note: "Save note", call: "Log call", followup: "Save follow-up" }[k];
			return `<div class="ch-composer">
				<div class="ch-seg ch-log-kind" role="radiogroup" aria-label="${t("What to log")}">${kinds.map(([v, ic, l]) =>
					`<button role="radio" data-log="${v}" class="${k === v ? "is-on" : ""}" aria-checked="${k === v}">${icon(ic, 12)} ${t(l)}</button>`).join("")}</div>
				<textarea class="ch-comment-input" rows="2" placeholder="${t(ph)}"></textarea>
				<div class="ch-composer-foot">
					${k === "followup" ? `<div class="ch-fu-when">${[["Tomorrow", 1], ["In 3 days", 3], ["Next week", 7]].map(([l, n], i) =>
						`<button class="ch-chip-btn ${i === 0 ? "is-on" : ""}" data-fu-days="${n}">${t(l)}</button>`).join("")}
						<input type="date" class="ch-fu-date" value="${addDays(1)}" aria-label="${t("Date")}"></div>` : "<span></span>"}
					<button class="ch-btn ch-primary ch-comment-save">${icon(k === "call" ? "phone" : k === "followup" ? "calendar" : "comment")} ${t(btn)}</button>
				</div>
			</div>`;
		}

		timeline(list) {
			if (!list.length) return `<div class="ch-empty">${t("No activity in this period.")}</div>`;
			return `<ol class="ch-tl">${list.map((e) => this.event(e)).join("")}</ol>`;
		}

		docRef(dt, name) {
			const d = this.tabMeta(dt);
			return `<button class="ch-ref" data-open="${esc(dt)}" data-name="${esc(name)}">${esc(t(d.short || dt))} ${esc(name)}</button>`;
		}

		event(e) {
			const when = `<time title="${esc(e.ts)}">${timeAgo(e.ts)}</time>`;
			const av = (n) => `<span class="ch-av">${esc((n || "?").trim().charAt(0).toUpperCase())}</span>`;
			if (e.kind === "comment") {
				const on = e.doctype === "Customer" ? "" : ` ${t("on")} ${this.docRef(e.doctype, e.name)}`;
				const isCall = (e.content || "").startsWith(CALL_PREFIX);
				const text = isCall ? e.content.slice(CALL_PREFIX.length) : e.content;
				return `<li><span class="ch-tl-ic ${isCall ? "ch-tl-call" : ""}">${icon(isCall ? "phone" : "comment")}</span><div class="ch-tl-body">
					<div class="ch-tl-line">${av(e.owner)}<span class="ch-tl-text"><b>${esc(e.owner)}</b> ${isCall ? t("logged a call") : t("added a note")}${on}</span>${when}</div>
					<div class="ch-bubble">${this.hl(text)}</div></div></li>`;
			}
			if (e.kind === "email") {
				return `<li><span class="ch-tl-ic">${icon("mail")}</span><div class="ch-tl-body"><div class="ch-mail">
					<div class="ch-tl-line"><span class="ch-tl-text"><b>${esc(e.owner)}</b> ${e.direction === "Received" ? t("wrote") : t("sent an email")}</span>${when}</div>
					<div class="ch-mail-sub">${esc(e.subject)}</div>
					<div class="ch-muted">${t("To")}: ${esc(e.recipients)} &nbsp; ${e.doctype !== "Customer" ? this.docRef(e.doctype, e.name) : ""}</div>
					${e.content ? `<p>${esc(e.content)}</p>` : ""}</div></div></li>`;
			}
			const d = this.tabMeta(e.doctype);
			return `<li><span class="ch-tl-ic">${icon(d.icon)}</span><div class="ch-tl-body">
				<div class="ch-tl-line">${av(e.owner)}<span class="ch-tl-text"><b>${esc(e.owner)}</b> ${t("created")} ${this.docRef(e.doctype, e.name)}
				${badge(e.status)}${e.amount != null ? `<span class="ch-amt">${esc(this.money(e.amount, e.currency))}</span>` : ""}
				${e.info ? `<span class="ch-muted">${esc(e.info)}</span>` : ""}</span>${when}</div></div></li>`;
		}

		/* ---------------- Document tables ---------------- */
		docView(dt) {
			const d = this.tabMeta(dt);
			const q = this.filter.toLowerCase();
			const all = this.data.docs[dt] || [];
			const counts = {};
			all.forEach((r) => (counts[r.status] = (counts[r.status] || 0) + 1));
			if (this.statusFilter && !counts[this.statusFilter]) this.statusFilter = "";
			const rows = all.filter((r) => (!this.statusFilter || r.status === this.statusFilter) && (!q || [r.name, r.status, r.info].join(" ").toLowerCase().includes(q)));
			const showAmt = rows.some((r) => r.amount != null);
			const showProg = PROGRESS_LABEL[dt] && rows.some((r) => r.progress != null);
			const total = rows.filter((r) => r.status !== "Draft").reduce((a, r) => a + (+r.amount || 0), 0);
			return `
			<div class="ch-head"><h2>${t(d.label)}</h2>
				<div class="ch-head-tools">
					<label class="ch-select ch-select-sm"><select class="ch-status-filter" aria-label="${t("Status")}">
						<option value="">${t("All statuses")} (${all.length})</option>${Object.keys(counts).sort()
							.map((st) => `<option value="${esc(st)}" ${st === this.statusFilter ? "selected" : ""}>${esc(t(st))} (${counts[st]})</option>`).join("")}</select>${icon("chev", 12)}</label>
					<label class="ch-search">${icon("search")}<input class="ch-filter" value="${esc(this.filter)}" placeholder="${t("Search")}" aria-label="${t("Search")}"></label>
					${d.creatable && this.o.newDoc ? `<button class="ch-btn ch-primary" data-new="${esc(dt)}">${icon("plus")} ${t("New")}</button>` : ""}
				</div></div>
			${rows.length ? `<div class="ch-table-wrap"><table class="ch-table">
				<thead><tr><th>${t("Document")}</th><th>${t("Date")}</th><th class="ch-hide-sm">${t("Details")}</th><th>${t("Status")}</th>
				${showProg ? `<th class="ch-hide-sm">${t(PROGRESS_LABEL[dt])}</th>` : ""}${showAmt ? `<th class="ch-r">${t("Amount")}</th>` : ""}</tr></thead>
				<tbody>${rows
					.map(
						(r) => `<tr data-open="${esc(dt)}" data-name="${esc(r.name)}" tabindex="0">
						<td><b>${esc(r.name)}</b><div class="ch-sub">${esc(r.owner)}</div></td>
						<td class="ch-nowrap">${esc(this.date(r.date))}</td>
						<td class="ch-hide-sm ch-muted">${esc(r.info)}</td>
						<td>${badge(r.status)}</td>
						${showProg ? `<td class="ch-hide-sm">${r.progress != null ? `<div class="ch-prog"><i style="width:${Math.min(100, r.progress)}%"></i></div><span class="ch-sub">${r.progress}%</span>` : ""}</td>` : ""}
						${showAmt ? `<td class="ch-r ch-nowrap">${r.amount != null ? esc(this.money(r.amount, r.currency)) : ""}</td>` : ""}</tr>`
					)
					.join("")}</tbody>
				${showAmt ? `<tfoot><tr><td colspan="${3 + (showProg ? 2 : 1)}">${rows.length} ${t("documents")} (${t("total excludes drafts")})</td><td class="ch-r ch-nowrap">${esc(this.money(total))}</td></tr></tfoot>` : ""}
			</table></div>` : `<div class="ch-empty">${this.filter || this.statusFilter ? t("Nothing matches these filters.") : `${t("No")} ${esc(t(d.label).toLowerCase())} ${t("for this customer in this period.")}`}</div>`}`;
		}

		/* ---------------- Side panel ---------------- */
		renderSide() {
			const c = this.data.customer, k = this.data.kpis, cur = this.data.currency;
			const row = (l, v) => `<div class="ch-kv"><span>${t(l)}</span><span>${v ? esc(v) : `<i class="ch-light">—</i>`}</span></div>`;
			const creatable = this.data.tabs.filter((d) => d.creatable);
			this.$(".ch-side").innerHTML = `
			<div class="ch-side-id">${esc(c.name)}</div>
			<div class="ch-side-hero">
				<span class="ch-av ch-av-lg">${esc((c.customer_name || "?").trim().charAt(0).toUpperCase())}</span>
				<div><div class="ch-side-name">${esc(c.customer_name)}</div>
				<div class="ch-side-actions">
					${c.email_id ? `<a class="ch-icon-btn" href="mailto:${esc(c.email_id)}" title="${t("Email")}" aria-label="${t("Email")}">${icon("mail")}</a>` : ""}
					${c.mobile_no ? `<a class="ch-icon-btn" href="tel:${esc(c.mobile_no)}" title="${t("Call")}" aria-label="${t("Call")}">${icon("phone")}</a>` : ""}
					<button class="ch-icon-btn" data-open="Customer" data-name="${esc(c.name)}" title="${t("Open customer record")}" aria-label="${t("Open customer record")}">${icon("ext")}</button>
					${this.o.newDoc && creatable.length ? `<div class="ch-new"><button class="ch-btn ch-primary ch-btn-sm ch-new-toggle">${icon("plus", 12)} ${t("New")} ${icon("chev", 11)}</button>
						<div class="ch-menu" hidden>${creatable.map((d) => `<button data-new="${esc(d.dt)}">${icon(d.icon)} ${esc(t(d.short || d.dt))}</button>`).join("")}</div></div>` : ""}
				</div></div>
			</div>
			${c.disabled ? `<div class="ch-warn">${t("This customer is disabled.")}</div>` : ""}
			<details open class="ch-side-fu"><summary>${icon("chev", 12)} ${t("Follow-ups")} ${(this.data.followups || []).length ? `<em class="ch-count">${this.data.followups.length}</em>` : ""}</summary>
				${(this.data.followups || []).length ? this.followupList(this.data.followups, { showOwner: true }) : `<p class="ch-muted ch-side-note">${t("Nothing planned.")}</p>`}
				<button class="ch-btn ch-soft ch-btn-sm ch-side-add" data-log-goto="followup">${icon("plus", 12)} ${t("Add follow-up")}</button>
			</details>
			<details open><summary>${icon("chev", 12)} ${t("Details")}</summary>
				${row("Type", c.customer_type)}${row("Group", c.customer_group)}${row("Territory", c.territory)}
				${row("Sales person", (c.sales_persons || []).join(", "))}${row("Account manager", c.account_manager)}
				${row("Tax ID", c.tax_id)}${row("Customer since", this.date(c.since))}
			</details>
			<details open><summary>${icon("chev", 12)} ${t("Contact")}</summary>
				${row("Contact", c.contact)}${row("Email", c.email_id)}${row("Mobile", c.mobile_no)}${row("Address", c.address)}
			</details>
			<details open><summary>${icon("chev", 12)} ${t("Account")}</summary>
				${row("Currency", cur)}${row("Credit limit", c.credit_limit ? this.money(c.credit_limit) : "")}
				${row("Outstanding", this.money(k.outstanding))}${row("Overdue", k.overdue ? this.money(k.overdue) : "")}
			</details>`;
		}

		/* ---------------- Events ---------------- */
		async onClick(e) {
			const el = (sel) => e.target.closest(sel);
			let x;
			if ((x = el("[data-app-switch]"))) {
				if (x.dataset.appSwitch !== this.app && this.o.switchApp) this.o.switchApp(x.dataset.appSwitch);
				return;
			}
			if ((x = el("[data-quick-visit]"))) {
				x.disabled = true;
				try {
					const plan = await this.o.api.crmMyPlan();
					await this.showCrmRecord("visit", plan);
					if (this.crm.rec && !(this.crm.rec.lines || []).some((l) => l.status === "Planned" && !l.party)) this.$("[data-vl-add]")?.click();
				} catch (err) { x.disabled = false; this.o.notify && this.o.notify((err && err.message) || t("Could not open today's plan")); }
				return;
			}
			if ((x = el("[data-hv]"))) { this.homeVisitAct = { name: x.dataset.name, status: x.dataset.hv }; this.renderHome(); this.$(".ch-hv-outcome")?.focus(); return; }
			if (el("[data-hv-back]")) { this.homeVisitAct = null; this.renderHome(); return; }
			if ((x = el("[data-hv-save]"))) {
				const box = x.closest(".ch-todo-finish"), outcome = box.querySelector(".ch-hv-outcome").value.trim();
				if (!outcome) { box.querySelector(".ch-hv-outcome").focus(); return; }
				x.disabled = true;
				try {
					await this.o.api.crmVisitLine(x.dataset.plan, "finish", x.dataset.line, { status: x.dataset.hvSave, outcome, next_followup_date: box.querySelector(".ch-hv-nfd").value || "" });
					this.homeVisitAct = null;
					this.o.notify && this.o.notify(t("Visit saved"), "green");
					this.loadHome();
				} catch (err) { x.disabled = false; this.o.notify && this.o.notify((err && err.message) || t("Could not save")); }
				return;
			}
			if (await this.crmClick(e)) return;
			if ((x = el("[data-nav]"))) {
				const n = x.dataset.nav;
				return n === "list" ? this.showList() : n === "home" ? this.showHome() : this.showCrmList(n);
			}
			if ((x = el("[data-team]"))) {
				this.team = x.dataset.team === "1";
				return this.loadHome();
			}
			if ((x = el("[data-url]"))) return this.o.openUrl ? this.o.openUrl(x.dataset.url) : window.open(x.dataset.url, "_blank");
			if ((x = el("[data-open-ref]"))) return this.o.openDoc(x.dataset.openRef, x.dataset.name);
			if ((x = el("[data-done]"))) {
				x.disabled = true;
				const li = x.closest("li");
				li && li.classList.add("is-done");
				try {
					await this.o.api.completeFollowup(x.dataset.done, x.dataset.name);
					this.toast && this.toast(t("Done"));
					setTimeout(() => (this.mode === "home" ? this.loadHome() : this.load()), 350);
				} catch (err) {
					x.disabled = false;
					li && li.classList.remove("is-done");
				}
				return;
			}
			if ((x = el("[data-fu-open]"))) {
				const li = x.closest("li");
				const open = li.nextElementSibling && li.nextElementSibling.classList.contains("ch-fu-form-li");
				this.root.querySelectorAll(".ch-fu-form-li").forEach((n) => n.remove());
				if (open) return;
				const f = document.createElement("li");
				f.className = "ch-fu-form-li";
				f.innerHTML = this.fuForm(x.dataset.fuOpen, x.dataset.fuText);
				li.after(f);
				f.querySelector(".ch-fu-text").focus();
				return;
			}
			if ((x = el("[data-fu-days]"))) {
				const box = x.closest(".ch-fu-when");
				box.querySelectorAll("[data-fu-days]").forEach((b) => b.classList.toggle("is-on", b === x));
				box.querySelector(".ch-fu-date").value = addDays(+x.dataset.fuDays);
				return;
			}
			if (el(".ch-fu-cancel")) return el(".ch-fu-form-li").remove();
			if ((x = el(".ch-fu-save"))) {
				const form = x.closest(".ch-fu-form");
				const text = form.querySelector(".ch-fu-text").value.trim();
				if (!text) return form.querySelector(".ch-fu-text").focus();
				x.disabled = true;
				try {
					await this.o.api.addFollowup("Customer", x.dataset.fuCustomer, form.querySelector(".ch-fu-date").value, text);
					this.o.notify && this.o.notify(t("Follow-up saved"), "green");
					this.mode === "home" ? this.loadHome() : this.loadAttention();
				} catch (err) {
					x.disabled = false;
				}
				return;
			}
			if ((x = el("[data-log]"))) {
				this.logKind = x.dataset.log;
				const ta = this.$(".ch-comment-input"), keep = ta ? ta.value : "", km = ta && ta._mentions;
				this.$(".ch-composer").outerHTML = this.composer();
				const nta = this.$(".ch-comment-input");
				nta.value = keep;
				nta._mentions = km;
				nta.focus();
				return;
			}
			if ((x = el("[data-log-goto]"))) {
				this.logKind = x.dataset.logGoto;
				this.tab = "activity";
				this.renderTabs();
				this.renderContent();
				this.$(".ch-comment-input")?.focus();
				return;
			}
			if ((x = el("[data-chart]"))) {
				this.chartMode = x.dataset.chart;
				this.$(".ch-chart-card").innerHTML = this.chart();
				this.$(`.ch-seg [data-chart="${this.chartMode}"]`)?.focus();
				return;
			}
			if ((x = el("[data-customer]"))) return this.selectCustomer(x.dataset.customer);
			if ((x = el("[data-age]"))) {
				this.list.age = this.list.age === x.dataset.age ? "" : x.dataset.age;
				return this.loadCustomers(true);
			}
			if (el(".ch-f-clear")) {
				Object.assign(this.list, { sales_person: "", branch: "", age: "" });
				return this.loadCustomers(true);
			}
			if (el(".ch-load-more")) {
				this.list.start = this.list.rows.length;
				return this.loadCustomers(false);
			}
			if ((x = el("[data-tab]"))) {
				this.tab = x.dataset.tab;
				this.filter = "";
				this.statusFilter = "";
				this.renderTabs();
				this.renderContent();
				return;
			}
			if ((x = el("[data-open]"))) return this.o.openDoc(x.dataset.open, x.dataset.name);
			if ((x = el("[data-new]"))) {
				this.root.querySelector(".ch-menu")?.setAttribute("hidden", "");
				return this.o.newDoc(x.dataset.new, this.customer);
			}
			if (el(".ch-new-toggle")) {
				const m = this.root.querySelector(".ch-menu");
				m.hidden ? m.removeAttribute("hidden") : m.setAttribute("hidden", "");
				return;
			}
			this.root.querySelector(".ch-menu")?.setAttribute("hidden", "");
			if (el(".ch-comment-save")) {
				const btn = el(".ch-comment-save");
				const ta = this.$(".ch-comment-input");
				const v = ta.value.trim();
				if (!v) return ta.focus();
				btn.disabled = true;
				try {
					if (this.logKind === "followup")
						await this.o.api.addFollowup("Customer", this.customer, this.$(".ch-fu-date").value, v);
					else await this.o.api.addComment(this.customer, v, this.logKind, this.mentionsOf(this.$(".ch-comment-input")));
					await this.load();
				} catch (err) {
					btn.disabled = false;
				}
			}
		}

		selectCustomer(name) {
			if (this.app === "crm") return this.o.openCustomer ? this.o.openCustomer(name) : null;
			if (this.o.setPicker) this.o.setPicker(name);
			this.setCustomer(name);
		}
	}
	CustomerHubUI.prototype._listReq = 0;
	CustomerHubUI.prototype._homeReq = 0;

	/* ======================================================================
	   CRM inside the hub: Leads, Deals, Contacts
	   ====================================================================== */
	const ENT = {
		lead: { one: "Lead", many: "Leads", icon: "star" },
		deal: { one: "Deal", many: "Deals", icon: "target" },
		contact: { one: "Contact", many: "Contacts", icon: "users" },
		visit: { one: "Visit plan", many: "Visit plans", icon: "pin" },
	};
	const DOCTYPE_ENTITY = { "CRM Lead": "lead", "CRM Deal": "deal", Contact: "contact", "Visit Plan": "visit" };
	const PT_LABEL = { "CRM Lead": "Lead", "CRM Deal": "Deal", Customer: "Customer" };
	const P = CustomerHubUI.prototype;

	P.crmInit = async function () {
		if (!this.o.api.crmMeta) return;
		this.crm = { meta: null, entity: "lead", lists: {}, rec: null };
		for (const e of Object.keys(ENT)) this.crm.lists[e] = { txt: "", status: "", owner: "mine", view: e === "deal" ? "board" : "list", rows: [], counts: {} };
		try {
			this.crm.meta = await this.o.api.crmMeta();
		} catch (e) {
			this.crm.meta = { installed: false };
		}
		const on = this.crm.meta && this.crm.meta.installed;
		this.root.querySelectorAll(".ch-nav-crm").forEach((b) => (b.hidden = !on || !this.crm.meta.entities[b.dataset.nav]));
		if (on && this.mode === "home" && this.home) this.renderHome();
		if (this._pendingCrm && on) {
			const [e, n] = this._pendingCrm;
			this._pendingCrm = null;
			n ? this.showCrmRecord(e, n, true) : this.showCrmList(e);
		}
	};

	P.userName = function (u) {
		const m = this.crm && this.crm.meta;
		const f = m && m.users && m.users.find((x) => x.name === u);
		return f ? f.full_name : u || "";
	};
	P.statusOf = function (entity, name) {
		const s = (this.crm.meta.entities[entity].statuses || []).find((x) => x.name === name);
		return s || { name, color: "gray", type: "Open" };
	};
	P.statusPill = function (entity, name) {
		if (!name) return "";
		const s = this.statusOf(entity, name);
		return `<span class="ch-st"><i class="ch-dot ch-pc-${esc(s.color)}"></i>${esc(t(name))}</span>`;
	};

	P.fmtVal = function (def, v, row) {
		if (v == null || v === "") return `<i class="ch-light">—</i>`;
		switch (def && def.fieldtype) {
			case "Check": return v ? t("Yes") : t("No");
			case "Date": return esc(this.date(String(v).slice(0, 10)));
			case "Datetime": return esc(this.date(String(v).slice(0, 10)));
			case "Currency": return esc(this.o.fmtMoney(v, (row && row.currency) || this.crm.meta.currency));
			case "Percent": return `${esc(v)}%`;
			case "Int": case "Float": return esc(Number(v).toLocaleString());
			case "Link": return def.options === "User" ? esc(this.userName(v)) : esc(v);
			default: return esc(v);
		}
	};

	/* ---------------- field inputs ---------------- */
	P.fieldInput = function (def, v, extra = "") {
		const name = esc(def.fieldname);
		const val = v == null ? "" : v;
		const base = `data-fname="${name}" ${extra}`;
		switch (def.fieldtype) {
			case "Select":
				return `<span class="ch-select ch-select-sm ch-in-wrap"><select class="ch-in" ${base}>${(def.options || [""]).map((o) =>
					`<option value="${esc(o)}" ${o === val ? "selected" : ""}>${esc(t(o)) || "—"}</option>`).join("")}</select>${icon("chev", 12)}</span>`;
			case "Check":
				return `<input type="checkbox" class="ch-in ch-in-check" ${base} ${val ? "checked" : ""}>`;
			case "Date":
				return `<input type="date" class="ch-in" ${base} value="${esc(String(val).slice(0, 10))}">`;
			case "Datetime":
				return `<input type="date" class="ch-in" ${base} value="${esc(String(val).slice(0, 10))}">`;
			case "Currency": case "Float": case "Int": case "Percent":
				return `<input type="number" step="any" class="ch-in" ${base} value="${esc(val)}">`;
			case "Small Text": case "Text": case "Long Text": case "Text Editor":
				return `<textarea class="ch-in" rows="2" ${base}>${esc(val)}</textarea>`;
			case "Link": {
				if (def.fieldname === "status") return this.statusSelect(def._entity, val, base);
				if (def.options === "User") {
					const users = this.crm.meta.users;
					return `<span class="ch-select ch-select-sm ch-in-wrap"><select class="ch-in" ${base}><option value="">—</option>${users.map((u) =>
						`<option value="${esc(u.name)}" ${u.name === val ? "selected" : ""}>${esc(u.full_name)}</option>`).join("")}</select>${icon("chev", 12)}</span>`;
				}
				return `<span class="ch-ac"><input type="text" class="ch-in ch-ac-in" autocomplete="off" ${base} data-link="${esc(def.options)}" value="${esc(val)}"
					placeholder="${t("Search")} ${esc(t(def.label))}…"><span class="ch-ac-list" hidden></span></span>`;
			}
			default:
				return `<input type="${def.options === "Email" ? "email" : def.options === "Phone" ? "tel" : "text"}" class="ch-in" ${base} value="${esc(val)}">`;
		}
	};
	P.statusSelect = function (entity, val, attrs) {
		const sts = this.crm.meta.entities[entity].statuses;
		return `<span class="ch-select ch-select-sm ch-in-wrap ch-st-select"><i class="ch-dot ch-pc-${esc(this.statusOf(entity, val).color)}"></i><select class="ch-in" ${attrs}>${sts.map((s) =>
			`<option value="${esc(s.name)}" ${s.name === val ? "selected" : ""}>${esc(t(s.name))}</option>`).join("")}</select>${icon("chev", 12)}</span>`;
	};
	P.readInput = function (el) {
		if (el.type === "checkbox") return el.checked ? 1 : 0;
		return el.value;
	};

	/* ---------------- list / board ---------------- */
	P.showCrmList = function (entity) {
		if (!this.crm || !this.crm.meta) { this._pendingCrm = [entity]; return; }
		this.mode = "crm-list";
		this.crm.entity = entity;
		this.customer = null;
		this.stack = [];
		this.setModeChrome();
		this.o.onCrmShown && this.o.onCrmShown(entity);
		const E = ENT[entity], L = this.crm.lists[entity], M = this.crm.meta.entities[entity];
		this.$(".ch-body").innerHTML = `<div class="ch-crm">
			<div class="ch-head"><div><h2>${t(E.many)}</h2><div class="ch-muted ch-crm-total"></div></div>
				<div class="ch-head-tools">
					${M.owner || entity === "contact" ? `<div class="ch-seg" role="radiogroup" aria-label="${t("Whose")}">
						<button role="radio" data-crm-owner="mine" class="${L.owner === "mine" ? "is-on" : ""}" aria-checked="${L.owner === "mine"}">${t("Mine")}</button>
						<button role="radio" data-crm-owner="" class="${L.owner ? "" : "is-on"}" aria-checked="${!L.owner}">${t("All")}</button></div>` : ""}
					${entity === "deal" ? `<div class="ch-seg" role="radiogroup" aria-label="${t("View")}">
						<button role="radio" data-crm-view="board" class="${L.view === "board" ? "is-on" : ""}" aria-checked="${L.view === "board"}">${t("Board")}</button>
						<button role="radio" data-crm-view="list" class="${L.view === "list" ? "is-on" : ""}" aria-checked="${L.view === "list"}">${t("List")}</button></div>` : ""}
					${M.fields.custom_lead_type && M.fields.custom_lead_type.fieldtype === "Select" && entity === "lead" ? `<span class="ch-select ch-select-sm ${L.lead_type ? "is-set" : ""}"><select class="ch-crm-ltype" aria-label="${t("Lead type")}"><option value="">${t("All types")}</option>${M.fields.custom_lead_type.options.filter(Boolean).map((o) => `<option ${o === L.lead_type ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>${icon("chev", 12)}</span>` : ""}
					<label class="ch-search">${icon("search")}<input class="ch-crm-search" value="${esc(L.txt)}" placeholder="${t("Search")} ${t(E.many).toLowerCase()}" aria-label="${t("Search")}"></label>
					${M.can_create ? `<button class="ch-btn ch-primary" data-crm-new="${entity}">${icon("plus")} ${t("New")} ${t(E.one).toLowerCase()}</button>` : ""}
				</div></div>
			<div class="ch-crm-chips"></div>
			<div class="ch-crm-body"><div class="ch-loading"><span></span><span></span><span></span></div></div>
		</div>`;
		this.loadCrmList();
	};

	P.loadCrmList = async function () {
		const entity = this.crm.entity, L = this.crm.lists[entity];
		const req = ++this._crmReq;
		const board = entity === "deal" && L.view === "board";
		try {
			const res = await this.o.api.crmList(entity, { txt: L.txt, status: board ? "" : L.status, owner: L.owner, lead_type: L.lead_type || "", page_len: board ? 500 : 100 });
			if (req !== this._crmReq || this.mode !== "crm-list" || this.crm.entity !== entity) return;
			Object.assign(L, { rows: res.rows, counts: res.counts, has_more: res.has_more });
			this.renderCrmList();
		} catch (err) {
			console.error(err);
			const b = this.$(".ch-crm-body");
			if (b) b.innerHTML = `<div class="ch-empty">${t("Could not load. Reload to try again.")}</div>`;
		}
	};

	P.renderCrmList = function () {
		const entity = this.crm.entity, L = this.crm.lists[entity], M = this.crm.meta.entities[entity];
		const board = entity === "deal" && L.view === "board";
		const total = Object.values(L.counts).reduce((a, b) => a + b, 0) || L.rows.length;
		this.$(".ch-crm-total").textContent = `${total} ${t(total === 1 ? ENT[entity].one : ENT[entity].many).toLowerCase()}${L.owner === "mine" ? " · " + t("yours") : ""}`;
		this.$(".ch-crm-chips").innerHTML = M.statuses.length && !board ? `<button class="ch-chip-btn ${!L.status ? "is-on" : ""}" data-crm-status="">${t("All")} <span>${total}</span></button>` +
			M.statuses.map((s) => `<button class="ch-chip-btn ${L.status === s.name ? "is-on" : ""}" data-crm-status="${esc(s.name)}"><i class="ch-dot ch-pc-${esc(s.color)}"></i>${esc(t(s.name))} <span>${L.counts[s.name] || 0}</span></button>`).join("") : "";
		const body = this.$(".ch-crm-body");
		if (board) return (body.innerHTML = this.crmBoard(L.rows));
		if (!L.rows.length) {
			body.innerHTML = `<div class="ch-empty ch-empty-lg">${icon(ENT[entity].icon, 22)}<p>${L.txt || L.status ? t("Nothing matches. Try another search or status.") : `${t("No")} ${t(ENT[entity].many).toLowerCase()} ${t("yet.")}`}</p>
				${M.can_create && !L.txt && !L.status ? `<button class="ch-btn ch-primary" data-crm-new="${entity}">${icon("plus")} ${t("Create the first one")}</button>` : ""}</div>`;
			return;
		}
		const cols = M.list.filter((f) => !(entity === "deal" && f === "status" && false));
		body.innerHTML = `<div class="ch-table-wrap"><table class="ch-table ch-crm-table">
			<thead><tr><th>${t(entity === "deal" ? "Organization" : entity === "visit" ? "Plan" : "Name")}</th>${cols.map((f) => `<th class="${["Currency", "Float", "Int", "Percent"].includes(M.fields[f].fieldtype) && f !== "completed_visits" ? "ch-r" : ""} ${["email", "email_id", "source", "designation", "probability"].includes(f) ? "ch-hide-sm" : ""}">${esc(M.fields[f].label)}</th>`).join("")}${(entity === "lead" || entity === "deal") && this.crm.meta.has_tasks ? `<th>${t("Next follow-up")}</th>` : ""}<th class="ch-hide-sm">${t("Updated")}</th></tr></thead>
			<tbody>${L.rows.map((r) => `<tr data-crm-open="${entity}" data-name="${esc(r.name)}" tabindex="0">
				<td><div class="ch-cell-id"><span class="ch-av">${esc((r.title || "?").trim().charAt(0).toUpperCase())}</span><div><b>${esc(r.title)}</b>${entity !== "contact" && r.title !== r.name ? `<div class="ch-sub">${esc(r.name)}</div>` : ""}</div></div></td>
				${cols.map((f) => {
					const d = M.fields[f];
					const num = ["Currency", "Float", "Int", "Percent"].includes(d.fieldtype);
					const cls = `${num ? "ch-r ch-nowrap" : ""} ${["email", "email_id", "source", "designation", "probability"].includes(f) ? "ch-hide-sm" : ""}`;
					if (f === "status") return `<td>${this.statusPill(entity, r.status)}</td>`;
					if (f === "completed_visits") {
						const tot = +r.total_visits || 0, done = +r.completed_visits || 0;
						return `<td class="ch-nowrap"><div class="ch-prog"><i style="width:${tot ? Math.round((done / tot) * 100) : 0}%"></i></div><span class="ch-sub">${done} / ${tot}</span></td>`;
					}
					if (f === "mobile_no" && r[f]) return `<td class="ch-nowrap"><a class="ch-tel" href="tel:${esc(r[f])}">${icon("phone", 12)} ${esc(r[f])}</a></td>`;
					return `<td class="${cls}">${this.fmtVal(d, r[f], r)}</td>`;
				}).join("")}
				${(entity === "lead" || entity === "deal") && this.crm.meta.has_tasks ? `<td class="ch-nowrap">${r.next_followup ? (() => { const d = r.next_followup.date ? this.dueLabel(r.next_followup.date) : null; return `<span class="ch-nf" title="${esc(r.next_followup.title || "")}">${r.next_followup.type ? icon(FU_ICON[r.next_followup.type] || "calendar", 11) : ""}${d ? `<span class="ch-badge ch-${d.tone}">${esc(d.text)}</span>` : esc(r.next_followup.title || "")}</span>`; })() : `<span class="ch-badge ch-red ch-nf-none" title="${t("No follow-up planned")}">${t("None")}</span>`}</td>` : ""}
				<td class="ch-hide-sm ch-muted ch-nowrap">${timeAgo(r.modified)}</td></tr>`).join("")}</tbody></table></div>
			${L.has_more ? `<p class="ch-muted ch-more">${t("Showing the latest 100. Search to find older ones.")}</p>` : ""}`;
	};

	P.crmBoard = function (rows) {
		const M = this.crm.meta.entities.deal;
		const vf = M.fields.deal_value ? "deal_value" : M.fields.annual_revenue ? "annual_revenue" : null;
		const cols = M.statuses.map((s) => ({ ...s, deals: rows.filter((r) => r.status === s.name) }));
		const extra = rows.filter((r) => !M.statuses.some((s) => s.name === r.status));
		if (extra.length) cols.push({ name: t("Other"), color: "gray", type: "Open", deals: extra, nodrop: 1 });
		return `<div class="ch-board">${cols.map((c) => `<div class="ch-bcol ${c.type !== "Open" ? "is-closed" : ""}" data-drop-status="${c.nodrop ? "" : esc(c.name)}">
			<div class="ch-pipe-h"><i class="ch-dot ch-pc-${esc(c.color)}"></i><b>${esc(t(c.name))}</b><span class="ch-muted">${c.deals.length}</span></div>
			<div class="ch-pipe-v">${vf ? esc(this.o.fmtMoney(c.deals.reduce((a, d) => a + (+d[vf] || 0), 0), this.crm.meta.currency)) : ""}</div>
			<div class="ch-bcards">${c.deals.map((d) => `<div class="ch-deal ch-dcard" draggable="true" data-drag-deal="${esc(d.name)}" data-crm-open="deal" data-name="${esc(d.name)}" tabindex="0">
				<b>${esc(d.title)}</b>
				<span>${vf && d[vf] ? esc(this.o.fmtMoney(d[vf], d.currency)) : ""}${d.expected_closure_date ? ` · ${esc(this.date(d.expected_closure_date))}` : ""}</span>
				${d.deal_owner ? `<span class="ch-muted">${esc(this.userName(d.deal_owner))}</span>` : ""}
				${d.next_followup && d.next_followup.date ? (() => { const x = this.dueLabel(d.next_followup.date); return `<span class="ch-badge ch-${x.tone} ch-card-fu">${icon("calendar", 10)} ${esc(x.text)}</span>`; })() : ""}</div>`).join("") || `<div class="ch-pipe-empty">${t("Drop deals here")}</div>`}</div>
		</div>`).join("")}</div>`;
	};

	/* ---------------- create form (modal) ---------------- */
	P.crmModal = function (html) {
		this.crmCloseModal();
		const m = document.createElement("div");
		m.className = "ch-modal";
		m.innerHTML = `<div class="ch-modal-scrim" data-modal-close></div><div class="ch-modal-box" role="dialog" aria-modal="true">${html}</div>`;
		this.root.querySelector(".ch").appendChild(m);
		this._modalFocus = document.activeElement;
		setTimeout(() => {
			const fs = [...m.querySelectorAll("input:not([type=checkbox]), select, textarea")];
			(fs.find((f) => !f.value) || fs[0])?.focus(); // start in the first empty field (pre-filled ones are done)
		}, 30);
		return m;
	};
	P.crmCloseModal = function () {
		const m = this.root.querySelector(".ch-modal");
		if (m) {
			m.remove();
			this._modalFocus && this._modalFocus.focus && this._modalFocus.focus();
		}
	};

	P.crmNewForm = function (entity, preset = {}) {
		const M = this.crm.meta.entities[entity];
		const vals = { ...preset };
		if (M.owner && !vals[M.owner]) vals[M.owner] = this.crm.meta.me;
		if (entity === "visit") {
			vals.plan_date = vals.plan_date || addDays(0);
			vals.status = vals.status || "Planned";
		}
		if (M.fields.status && !vals.status && M.statuses.length) vals.status = M.statuses[0].name;
		if (M.fields.currency && !vals.currency) vals.currency = this.crm.meta.currency;
		const quick = (M.quick || []).filter((f) => M.create.includes(f) || M.fields[f]);
		const fields = (quick.length ? quick : M.create).map((f) => ({ ...M.fields[f], _entity: entity }));
		const extra = quick.length ? M.create.filter((f) => !quick.includes(f)).map((f) => ({ ...M.fields[f], _entity: entity })) : [];
		const SHORT = { first_name: "Name", mobile_no: "Mobile", custom_lead_type: "Type", expected_closure_date: "Expected close", deal_value: "Value" };
		if (quick.length) fields.forEach((d) => SHORT[d.fieldname] && (d.label = t(SHORT[d.fieldname])));
		const row = (d) => `<label class="ch-frow ${["Small Text", "Text", "Long Text", "Text Editor"].includes(d.fieldtype) ? "ch-frow-wide" : ""}"><span>${esc(d.label)}${d.reqd ? ` <b class="ch-red-t">*</b>` : ""}</span>${this.fieldInput(d, vals[d.fieldname])}</label>`;
		const contactPick = entity === "deal" ? `<label class="ch-frow"><span>${t("Contact")}</span>${this.fieldInput({ fieldname: "contact", fieldtype: "Link", options: "Contact", label: "Contact" }, vals.contact)}</label>` : "";
		this.crmModal(`<form class="ch-crm-form" data-crm-form="${entity}" novalidate>
			<div class="ch-modal-h"><h2>${t("New")} ${t(ENT[entity].one).toLowerCase()}</h2><button type="button" class="ch-icon-btn" data-modal-close aria-label="${t("Close")}">${icon("x")}</button></div>
			<div class="ch-modal-body"><div class="ch-fgrid">${fields.map(row).join("")}${contactPick}</div>
			${extra.length ? `<details class="ch-more-f"><summary>${t("More details")}</summary><div class="ch-fgrid">${extra.map(row).join("")}</div></details>` : ""}
			${entity === "deal" ? `<p class="ch-muted ch-form-hint">${t("Type a new organization name to create it, or pick an existing one.")}</p>` : ""}
			<div class="ch-form-err" hidden></div></div>
			<div class="ch-modal-f"><button type="button" class="ch-btn ch-soft" data-modal-close>${t("Cancel")}</button>
			<button type="submit" class="ch-btn ch-primary">${icon("check", 12)} ${t("Create")}</button></div>
		</form>`);
	};

	P.crmSubmitForm = async function (form) {
		const entity = form.dataset.crmForm;
		const vals = {};
		form.querySelectorAll("[data-fname]").forEach((el) => (vals[el.dataset.fname] = this.readInput(el)));
		const M = this.crm.meta.entities[entity];
		const missing = M.create.filter((f) => M.fields[f].reqd && !vals[f]).map((f) => M.fields[f].label);
		if (entity === "contact" && !vals.first_name) missing.push(t("First Name"));
		const err = form.querySelector(".ch-form-err");
		if (missing.length) {
			err.hidden = false;
			err.textContent = `${t("Please fill in")}: ${[...new Set(missing)].join(", ")}`;
			return;
		}
		const btn = form.querySelector("[type=submit]");
		btn.disabled = true;
		try {
			const name = await this.o.api.crmCreate(entity, vals);
			this.crmCloseModal();
			this.showCrmRecord(entity, name);
		} catch (e) {
			btn.disabled = false;
			err.hidden = false;
			err.textContent = (e && e.message) || t("Could not save. Check the fields and try again.");
		}
	};

	/* ---------------- record page ---------------- */
	P.showCrmRecord = async function (entity, name, noPush) {
		if (!this.crm || !this.crm.meta) { this._pendingCrm = [entity, name]; return; }
		if (!noPush) this.pushView();
		this.mode = "crm-record";
		this.crm.entity = entity;
		const same = this.crm.recName === name;
		this.crm.recTab = this.crm.recTab && same ? this.crm.recTab : entity === "visit" ? "lines" : "activity";
		if (!same) { this.crm.logKind = "comment"; this.crm.mail = null; this.crm.uploading = []; }
		this.crm.recName = name;
		this.customer = null;
		this.setModeChrome();
		this.o.onCrmShown && this.o.onCrmShown(entity, name);
		this.$(".ch-body").innerHTML = `<div class="ch-hub ch-rec"><div class="ch-main"><div class="ch-loading"><span></span><span></span><span></span></div></div><aside class="ch-side"></aside></div>`;
		await this.loadCrmRecord();
	};

	P.loadCrmRecord = async function (data) {
		const entity = this.crm.entity, name = this.crm.recName;
		try {
			const rec = data || (await this.o.api.crmGet(entity, name));
			if (this.mode !== "crm-record" || this.crm.recName !== name) return;
			this.crm.rec = rec;
			this.renderCrmRecord();
		} catch (err) {
			console.error(err);
			this.$(".ch-main").innerHTML = `<div class="ch-empty">${t("You can't open this record, or it was deleted.")}</div>`;
		}
	};

	P.renderCrmRecord = function () {
		const entity = this.crm.entity, R = this.crm.rec, D = R.doc, M = this.crm.meta.entities[entity];
		const tabs = entity === "visit" ? [["lines", "Visits", "pin", (R.lines || []).length]] : [];
		tabs.push(["activity", "Activity", "activity", R.activity.length]);
		if (this.crm.meta.has_notes) tabs.push(["notes", "Notes", "file", R.notes.length]);
		if (this.crm.meta.has_tasks && entity !== "visit") tabs.push(["tasks", "Follow-ups", "calendar", R.tasks.filter((x) => !["Done", "Canceled"].includes(x.status)).length]);
		if (this.crm.meta.has_visits && (entity === "lead" || entity === "deal")) tabs.push(["visits", "Visits", "pin", (R.visits || []).filter((v) => v.status === "Open").length]);
		tabs.push(["attachments", "Attachments", "clip", (R.attachments || []).length]);
		if (entity === "contact") tabs.push(["linked", "Deals & leads", "target", (R.deals || []).length + (R.leads || []).length]);
		const ownerF = M.owner;
		const head = `<div class="ch-rec-head">
			<div class="ch-rec-title"><span class="ch-muted">${t(ENT[entity].many)} /</span> <h2>${esc(D.title)}</h2></div>
			<div class="ch-rec-actions">
				${ownerF ? `<label class="ch-owner" title="${t("Owner")}">${icon("users", 12)}${R.can_write ? this.fieldInput({ ...M.fields[ownerF], _entity: entity }, D[ownerF], 'data-crm-set="1"') : esc(this.userName(D[ownerF]))}</label>` : ""}
				${M.fields.status ? (R.can_write ? this.statusSelect(entity, D.status, `data-fname="status" data-crm-set="1"`) : this.statusPill(entity, D.status)) : ""}
				${entity === "lead" && !R.converted && R.can_write ? `<button class="ch-btn ch-primary" data-crm-convert>${icon("arrow", 12)} ${t("Convert to deal")}</button>` : ""}
				${entity === "lead" && R.deal ? `<button class="ch-btn ch-soft" data-crm-open="deal" data-name="${esc(R.deal)}">${icon("target", 12)} ${t("Open deal")}</button>` : ""}
				${entity === "deal" && R.customer ? `<button class="ch-btn ch-soft" data-customer="${esc(R.customer)}">${icon("users", 12)} ${t("Open customer")}</button>` : ""}
				${entity === "deal" && (R.next_steps || []).length ? `<span class="ch-next-steps"><span class="ch-muted">${t("Next")}:</span>${R.next_steps.map((st, i) =>
					`<button class="ch-btn ch-soft" data-next-step="${i}" ${st.needs_customer ? `disabled title="${t("Link a customer first (Request > Customer)")}"` : `title="${t("Create")} ${esc(t(st.label))} ${t("for this customer")}"`}>${icon("plus", 12)} ${esc(t(st.label))}</button>`).join("")}</span>` : ""}
				${entity === "visit" && R.can_write && !R.plan_locked ? `<button class="ch-btn ch-primary" data-vl-add>${icon("plus", 12)} ${t("Add visit")}</button>` : ""}
				${entity === "deal" && !R.customer && R.status_type === "Won" ? `<button class="ch-btn ch-primary" data-crm-to-customer>${icon("plus", 12)} ${t("Create customer")}</button>` : ""}
			</div></div>`;
		const tab = this.crm.recTab;
		this.$(".ch-main").innerHTML = `${head}
			<nav class="ch-tabs" role="tablist">${tabs.map(([k, l, ic, n]) => `<button role="tab" class="ch-tab ${tab === k ? "is-active" : ""}" data-crm-tab="${k}" aria-selected="${tab === k}">${icon(ic)}<span>${t(l)}</span><em>${n}</em></button>`).join("")}</nav>
			<div class="ch-content">${tab === "notes" ? this.crmNotes() : tab === "tasks" ? this.crmTasks() : tab === "linked" ? this.crmLinked() : tab === "attachments" ? this.crmAttachments() : tab === "visits" ? this.crmVisits() : tab === "lines" ? this.crmLines() : this.crmActivity()}</div>`;
		this.renderCrmSide();
	};

	P.activityKinds = function () {
		const e = this.crm.entity;
		return ["comment", "email", "call"].concat(this.crm.meta.has_tasks && e !== "visit" ? ["task"] : [],
			this.crm.meta.has_visits && (e === "lead" || e === "deal") ? ["visit"] : [], this.crm.meta.has_notes ? ["note"] : []);
	};
	const KIND = { comment: ["comment", "Comment"], email: ["mail", "Email"], call: ["phone", "Call"], note: ["file", "Note"], task: ["calendar", "Follow-up"], visit: ["pin", "Visit"] };
	const FU_ICON = { Call: "phone", Email: "mail", WhatsApp: "comment", Meeting: "users", Visit: "pin" };
	const hm = (iso) => (iso || "").slice(11, 16);

	const fsize = (n) => (n > 1048576 ? `${(n / 1048576).toFixed(1)} MB` : n > 1024 ? `${Math.round(n / 1024)} KB` : `${n || 0} B`);
	const fext = (n) => ((n || "").split(".").pop() || "").slice(0, 4).toUpperCase();

	P.mailState = function () {
		const R = this.crm.rec;
		if (!this.crm.mail || this.crm.mail.rec !== this.crm.recName) {
			const first = (R.emails || [])[0];
			this.crm.mail = { rec: this.crm.recName, to: first ? first.email : "", cc: "", showCc: false, subject: "", body: "", files: [] };
		}
		return this.crm.mail;
	};
	P.readMail = function () {
		const m = this.crm.mail;
		if (!m) return;
		const v = (s) => this.$(s) && this.$(s).value;
		if (this.$(".ch-mail-to")) Object.assign(m, { to: v(".ch-mail-to"), cc: v(".ch-mail-cc") ?? m.cc, subject: v(".ch-mail-subject"), body: v(".ch-mail-body") });
	};

	P.emailComposer = function (kinds) {
		const m = this.mailState(), R = this.crm.rec;
		const all = KIND;
		const att = R.attachments || [];
		return `<div class="ch-composer ch-crm-composer ch-mail-composer">
			<div class="ch-seg" role="radiogroup" aria-label="${t("What to add")}">${kinds.map((v) => `<button role="radio" data-crm-kind="${v}" class="${v === "email" ? "is-on" : ""}" aria-checked="${v === "email"}">${icon(all[v][0], 12)} ${t(all[v][1])}</button>`).join("")}</div>
			<div class="ch-mail-row"><label>${t("To")}</label><input class="ch-in ch-mail-to" list="ch-mail-sugg" value="${esc(m.to)}" placeholder="${t("name@company.com, …")}" autocomplete="off">
				${m.showCc ? "" : `<button class="ch-link" data-mail-cc>${t("Cc")}</button>`}</div>
			<datalist id="ch-mail-sugg">${(R.emails || []).map((e) => `<option value="${esc(e.email)}">${esc(e.label || "")}</option>`).join("")}</datalist>
			${m.showCc ? `<div class="ch-mail-row"><label>${t("Cc")}</label><input class="ch-in ch-mail-cc" list="ch-mail-sugg" value="${esc(m.cc)}" autocomplete="off"></div>` : ""}
			<div class="ch-mail-row"><label>${t("Subject")}</label><input class="ch-in ch-mail-subject" value="${esc(m.subject)}"></div>
			<textarea class="ch-comment-input ch-mail-body" rows="6" placeholder="${t("Write your email…")}">${esc(m.body)}</textarea>
			<div class="ch-mail-files">
				${att.map((f) => {
					const on = m.files.includes(f.name);
					return `<button class="ch-file-chip ${on ? "is-on" : ""}" data-mail-file="${esc(f.name)}" aria-pressed="${on}" title="${on ? t("Attached. Click to remove from this email") : t("Click to attach to this email")}">${icon(on ? "check" : "clip", 11)} ${esc(f.file_name)}</button>`;
				}).join("")}
				${(this.crm.uploading || []).map((n) => `<span class="ch-file-chip is-busy">${icon("upload", 11)} ${esc(n)}…</span>`).join("")}
			</div>
			<div class="ch-composer-foot">
				<div class="ch-fu-when"><button class="ch-btn ch-soft ch-btn-sm" data-pick-files="mail">${icon("clip", 12)} ${t("Attach files")}</button>
					${att.length ? `<span class="ch-muted ch-mail-hint">${t("Click a file above to include it")}</span>` : ""}</div>
				<button class="ch-btn ch-primary" data-mail-send>${icon("send")} ${t("Send email")}</button>
			</div>
			<input type="file" class="ch-file-input" data-for="mail" multiple hidden>
		</div>`;
	};

	P.crmComposer = function (kinds) {
		const k = kinds.includes(this.crm.logKind) ? this.crm.logKind : kinds[0];
		this.crm.logKind = k;
		if (k === "email") return this.emailComposer(kinds);
		if (k === "visit") return this.visitComposer(kinds);
		const all = KIND;
		const ph = { comment: "Add a comment…", call: "What was the call about? Outcome, next step…", note: "Write a note…", task: "Details (optional)" }[k];
		return `<div class="ch-composer ch-crm-composer">
			<div class="ch-seg" role="radiogroup" aria-label="${t("What to add")}">${kinds.map((v) => `<button role="radio" data-crm-kind="${v}" class="${k === v ? "is-on" : ""}" aria-checked="${k === v}">${icon(all[v][0], 12)} ${t(all[v][1])}</button>`).join("")}</div>
			${k === "note" || k === "task" ? `<input type="text" class="ch-in ch-crm-title" placeholder="${t(k === "task" ? "What to follow up, e.g. Call back about the quotation" : "Title")}">` : ""}
			<textarea class="ch-comment-input ch-crm-text" rows="2" placeholder="${t(ph)}"></textarea>
			<div class="ch-composer-foot">
				${k === "task" ? `<div class="ch-fu-when">${(this.crm.meta.followup_types || []).length ? `<span class="ch-select ch-select-sm"><select class="ch-crm-futype" aria-label="${t("Follow-up type")}">${this.crm.meta.followup_types.map((x) => `<option>${esc(t(x))}</option>`).join("")}</select>${icon("chev", 12)}</span>` : ""}
					${[["Today", 0], ["Tomorrow", 1], ["Next week", 7]].map(([l, n], i) => `<button class="ch-chip-btn ${i === 1 ? "is-on" : ""}" data-fu-days="${n}">${t(l)}</button>`).join("")}
					<input type="date" class="ch-fu-date" value="${addDays(1)}" aria-label="${t("Due date")}">
					<span class="ch-select ch-select-sm"><select class="ch-crm-assign" aria-label="${t("Assign to")}">${this.crm.meta.users.map((u) => `<option value="${esc(u.name)}" ${u.name === this.crm.meta.me ? "selected" : ""}>${esc(u.full_name)}</option>`).join("")}</select>${icon("chev", 12)}</span></div>` : "<span></span>"}
				<button class="ch-btn ch-primary" data-crm-add>${icon(all[k][0])} ${t(k === "call" ? "Log call" : k === "task" ? "Add follow-up" : k === "note" ? "Save note" : "Comment")}</button>
			</div></div>`;
	};

	P.crmActivity = function () {
		const R = this.crm.rec, entity = this.crm.entity;
		const kinds = this.activityKinds();
		const av = (n) => `<span class="ch-av">${esc((n || "?").trim().charAt(0).toUpperCase())}</span>`;
		const items = R.activity.map((e) => {
			const when = `<time title="${esc(e.ts)}">${timeAgo(e.ts)}</time>`;
			if (e.kind === "change") {
				const isStatus = e.field === (this.crm.meta.entities[entity].fields.status || {}).label;
				return `<li class="ch-tl-small"><span class="ch-tl-ic"><i class="ch-tl-dot"></i></span><div class="ch-tl-body"><div class="ch-tl-line"><span class="ch-tl-text"><b>${esc(e.by)}</b> ${t("changed")} <b>${esc(e.field)}</b>
					${e.from ? `${t("from")} ${isStatus ? this.statusPill(entity, e.from) : `<span class="ch-chg">${esc(e.from)}</span>`}` : ""} ${t("to")} ${isStatus ? this.statusPill(entity, e.to) : `<span class="ch-chg">${esc(e.to || "—")}</span>`}</span>${when}</div></div></li>`;
			}
			if (e.kind === "comment" || e.kind === "call")
				return `<li><span class="ch-tl-ic ${e.kind === "call" ? "ch-tl-call" : ""}">${icon(e.kind === "call" ? "phone" : "comment")}</span><div class="ch-tl-body">
					<div class="ch-tl-line">${av(e.by)}<span class="ch-tl-text"><b>${esc(e.by)}</b> ${e.kind === "call" ? t("logged a call") : t("added a comment")}</span>${when}</div>
					<div class="ch-bubble">${this.hl(e.content)}</div></div></li>`;
			if (e.kind === "note")
				return `<li><span class="ch-tl-ic">${icon("file")}</span><div class="ch-tl-body">
					<div class="ch-tl-line">${av(e.by)}<span class="ch-tl-text"><b>${esc(e.by)}</b> ${t("added a note")}</span>${when}</div>
					<div class="ch-bubble"><b>${esc(e.title)}</b>${e.content && e.content !== e.title ? `<br>${this.hl(e.content)}` : ""}</div></div></li>`;
			if (e.kind === "visit") {
				const v = e.visit;
				return `<li><span class="ch-tl-ic ch-tl-visit">${icon("pin")}</span><div class="ch-tl-body"><div class="ch-tl-line"><span class="ch-tl-text">
					<b>${esc(v.type || t("Visit"))}</b> ${esc(this.date((v.starts_on || "").slice(0, 10)))} ${esc(hm(v.starts_on))}${v.location ? ` · ${esc(v.location)}` : ""} ${this.visitBadge(v)}<span class="ch-muted">· ${esc(v.by_name)}</span></span>${when}</div>
					${v.outcome ? `<div class="ch-bubble"><b>${t("Outcome")}:</b> ${esc(v.outcome)}</div>` : ""}</div></li>`;
			}
			if (e.kind === "task")
				return `<li><span class="ch-tl-ic">${icon(FU_ICON[e.type] || "calendar")}</span><div class="ch-tl-body"><div class="ch-tl-line"><span class="ch-tl-text">${esc(t(e.type || "Follow-up"))} <b>${esc(e.title)}</b> ${badge(e.status)}${e.due_date ? `<span class="ch-muted">${t("due")} ${esc(this.date(e.due_date))}</span>` : ""}${e.by ? `<span class="ch-muted">· ${esc(e.by)}</span>` : ""}</span>${when}</div></div></li>`;
			if (e.kind === "file")
				return `<li class="ch-tl-small"><span class="ch-tl-ic">${icon("clip", 12)}</span><div class="ch-tl-body"><div class="ch-tl-line"><span class="ch-tl-text"><b>${esc(e.by)}</b> ${t("attached")} <button class="ch-ref" data-open-file="${esc(e.file_url)}">${esc(e.file_name)}</button></span>${when}</div></div></li>`;
			if (e.kind === "email")
				return `<li><span class="ch-tl-ic">${icon("mail")}</span><div class="ch-tl-body"><div class="ch-mail">
					<div class="ch-tl-line"><span class="ch-tl-text"><b>${esc(e.by)}</b> ${e.direction === "Received" ? t("wrote") : t("sent an email")}</span>
					<button class="ch-btn ch-soft ch-btn-sm" data-reply="${esc(JSON.stringify({ to: e.direction === "Received" ? e.by : e.recipients, subject: e.subject }))}">${icon("reply", 12)} ${t("Reply")}</button>${when}</div>
					<div class="ch-mail-sub">${esc(e.subject)}</div><div class="ch-muted">${t("To")}: ${esc(e.recipients)}</div>
					${e.content ? `<p>${esc(e.content)}</p>` : ""}</div></div></li>`;
			return "";
		});
		items.push(`<li class="ch-tl-small"><span class="ch-tl-ic"><i class="ch-tl-dot"></i></span><div class="ch-tl-body"><div class="ch-tl-line"><span class="ch-tl-text"><b>${esc(R.created.by)}</b> ${t("created this")} ${t(ENT[entity].one).toLowerCase()}</span><time>${timeAgo(R.created.ts)}</time></div></div></li>`);
		return `${R.can_write || true ? this.crmComposer(kinds) : ""}<ol class="ch-tl">${items.join("")}</ol>`;
	};

	P.crmNotes = function () {
		const R = this.crm.rec;
		this.crm.logKind = "note";
		return `${this.crmComposer(["note"])}${R.notes.length ? `<div class="ch-notes">${R.notes.map((n) => `<article class="ch-note">
			<h3>${esc(n.title)}</h3>${n.content && n.content !== n.title ? `<p>${esc(n.content).replace(/\n/g, "<br>")}</p>` : ""}
			<div class="ch-muted">${esc(n.by)} · ${timeAgo(n.ts)}</div></article>`).join("")}</div>` : `<div class="ch-empty">${t("No notes yet.")}</div>`}`;
	};

	P.crmTasks = function () {
		const R = this.crm.rec;
		this.crm.logKind = "task";
		const open = R.tasks.filter((x) => !["Done", "Canceled"].includes(x.status));
		const done = R.tasks.filter((x) => ["Done", "Canceled"].includes(x.status));
		const row = (x) => {
			const due = x.due_date ? this.dueLabel(x.due_date) : null;
			const isDone = x.status === "Done";
			return `<li class="${isDone ? "is-done" : ""}"><button class="ch-done" data-task-toggle="${esc(x.name)}" data-to="${isDone ? "Todo" : "Done"}" aria-label="${isDone ? t("Reopen") : t("Mark as done")}" title="${isDone ? t("Reopen") : t("Mark as done")}">${icon("check", 12)}</button>
				<div class="ch-fu-main"><div class="ch-fu-title">${x.type ? `<span class="ch-fu-type">${icon(FU_ICON[x.type] || "calendar", 11)} ${esc(t(x.type))}</span> ` : ""}${esc(x.title)}</div><div class="ch-fu-meta">${badge(x.status)}${x.priority ? `<span class="ch-muted">${esc(t(x.priority))}</span>` : ""}<span class="ch-muted">${esc(x.assigned_name)}</span></div>
				${x.description ? `<div class="ch-muted ch-task-desc">${esc(x.description)}</div>` : ""}</div>
				${due && !isDone ? `<span class="ch-badge ch-${due.tone}">${esc(due.text)}</span>` : ""}</li>`;
		};
		return `${this.crmComposer(["task"])}${open.length ? `<ul class="ch-fu">${open.map(row).join("")}</ul>` : `<div class="ch-empty ch-empty-sm">${icon("calendar", 18)}<p>${t("No follow-ups planned.")}</p></div>`}
			${done.length ? `<details class="ch-done-list"><summary>${t("Done")} (${done.length})</summary><ul class="ch-fu">${done.map(row).join("")}</ul></details>` : ""}`;
	};

	P.visitBadge = function (v) {
		const late = v.status === "Open" && daysFrom((v.starts_on || "").slice(0, 10)) < 0;
		const [txt, tone] = v.status === "Completed" ? ["Completed", "green"] : v.status === "Cancelled" ? ["Cancelled", "gray"] : late ? ["Overdue", "red"] : ["Planned", "blue"];
		return `<span class="ch-badge ch-${tone}">${t(txt)}</span>`;
	};

	P.visitForm = function () {
		const R = this.crm.rec, D = R.doc, M = this.crm.meta;
		const loc = [D.organization, D.territory].filter(Boolean).join(", ");
		return `<div class="ch-visit-form">
			<div class="ch-fgrid">
				<label class="ch-frow"><span>${t("Visit type")}</span><span class="ch-select ch-select-sm ch-in-wrap"><select class="ch-in ch-v-type">${(M.visit_types || ["Site Visit"]).map((x) => `<option>${esc(t(x))}</option>`).join("")}</select>${icon("chev", 12)}</span></label>
				<label class="ch-frow"><span>${t("Visit by")}</span><span class="ch-select ch-select-sm ch-in-wrap"><select class="ch-in ch-v-by">${M.users.map((u) => `<option value="${esc(u.name)}" ${u.name === (D[this.crm.meta.entities[this.crm.entity].owner] || M.me) ? "selected" : ""}>${esc(u.full_name)}</option>`).join("")}</select>${icon("chev", 12)}</span></label>
				<label class="ch-frow"><span>${t("Date")}</span><input type="date" class="ch-in ch-v-date" value="${addDays(1)}"></label>
				<div class="ch-frow"><span>${t("Time and duration")}</span><div class="ch-v-time"><input type="time" class="ch-in ch-v-time-in" value="10:00" aria-label="${t("Time")}">
					<span class="ch-select ch-select-sm ch-in-wrap"><select class="ch-in ch-v-min" aria-label="${t("Duration")}">${[[30, "30 min"], [60, "1 hour"], [120, "2 hours"], [240, "Half day"], [480, "Full day"]].map(([v, l]) => `<option value="${v}" ${v === 60 ? "selected" : ""}>${t(l)}</option>`).join("")}</select>${icon("chev", 12)}</span></div></div>
				<label class="ch-frow ch-frow-wide"><span>${t("Location")}</span><input class="ch-in ch-v-loc" value="${esc(loc)}" placeholder="${t("Site address or area")}"></label>
				<label class="ch-frow ch-frow-wide"><span>${t("Purpose")}</span><input class="ch-in ch-v-purpose" placeholder="${t("e.g. Site survey for bed installation")}"></label>
				<label class="ch-frow ch-frow-wide"><span>${t("Notes")}</span><textarea class="ch-in ch-v-notes" rows="2" placeholder="${t("What to bring, who to meet…")}"></textarea></label>
			</div>
			<div class="ch-fu-btns"><button class="ch-btn ch-primary" data-visit-plan>${icon("pin", 12)} ${t("Plan visit")}</button></div>
		</div>`;
	};

	P.visitComposer = function (kinds) {
		return `<div class="ch-composer ch-crm-composer">
			<div class="ch-seg" role="radiogroup" aria-label="${t("What to add")}">${kinds.map((v) => `<button role="radio" data-crm-kind="${v}" class="${v === "visit" ? "is-on" : ""}" aria-checked="${v === "visit"}">${icon(KIND[v][0], 12)} ${t(KIND[v][1])}</button>`).join("")}</div>
			${this.visitForm()}</div>`;
	};

	P.crmVisits = function () {
		const list = this.crm.rec.visits || [];
		const open = list.filter((v) => v.status === "Open").sort((a, b) => (a.starts_on < b.starts_on ? -1 : 1));
		const past = list.filter((v) => v.status !== "Open");
		const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
		const row = (v) => {
			const [y, m, d] = (v.starts_on || "").slice(0, 10).split("-");
			const act = this.crm.visitAct && this.crm.visitAct.name === v.name ? this.crm.visitAct.action : null;
			return `<li class="ch-visit ${v.status !== "Open" ? "is-past" : ""}">
				<div class="ch-visit-date"><b>${+d || ""}</b><span>${MON[+m - 1] || ""}</span></div>
				<div class="ch-visit-main"><b>${esc(v.subject)}</b>
					<span class="ch-muted">${esc(t(v.type || "Visit"))} · ${esc(hm(v.starts_on))}${v.ends_on ? "–" + esc(hm(v.ends_on)) : ""}${v.location ? ` · ${icon("pin", 10)} ${esc(v.location)}` : ""}</span>
					<span class="ch-muted">${esc(v.by_name)}${v.plan ? ` · <button class="ch-ref" data-crm-open="visit" data-name="${esc(v.plan)}">${esc(v.plan)}</button>` : ""}</span>
					${v.notes ? `<span class="ch-visit-notes">${esc(v.notes)}</span>` : ""}
					${v.outcome ? `<span class="ch-visit-outcome"><b>${t("Outcome")}:</b> ${esc(v.outcome)}</span>` : ""}
					${act === "complete" ? `<div class="ch-visit-act"><textarea class="ch-in ch-v-outcome" rows="2" placeholder="${t("How did it go? Next step…")}"></textarea>
						<div class="ch-fu-btns"><button class="ch-btn ch-soft ch-btn-sm" data-visit-cancel-act>${t("Cancel")}</button><button class="ch-btn ch-primary ch-btn-sm" data-visit-save="complete" data-visit="${esc(v.name)}">${icon("check", 12)} ${t("Mark completed")}</button></div></div>` : ""}
					${act === "reschedule" ? `<div class="ch-visit-act"><div class="ch-v-time"><input type="date" class="ch-in ch-v-date" value="${esc((v.starts_on || "").slice(0, 10))}"><input type="time" class="ch-in ch-v-time-in" value="${esc(hm(v.starts_on))}"></div>
						<div class="ch-fu-btns"><button class="ch-btn ch-soft ch-btn-sm" data-visit-cancel-act>${t("Cancel")}</button><button class="ch-btn ch-primary ch-btn-sm" data-visit-save="reschedule" data-visit="${esc(v.name)}">${icon("calendar", 12)} ${t("Save new time")}</button></div></div>` : ""}
				</div>
				<div class="ch-visit-side">${this.visitBadge(v)}
					${this.crm.rec.can_write || true ? (v.status === "Open"
						? `<div class="ch-visit-btns"><button class="ch-btn ch-soft ch-btn-sm" data-visit-act="complete" data-visit="${esc(v.name)}">${icon("check", 12)} ${t("Done")}</button>
							<button class="ch-icon-btn" data-visit-act="reschedule" data-visit="${esc(v.name)}" title="${t("Reschedule")}" aria-label="${t("Reschedule")}">${icon("calendar")}</button>
							<button class="ch-icon-btn" data-visit-save="cancel" data-visit="${esc(v.name)}" title="${t("Cancel visit")}" aria-label="${t("Cancel visit")}">${icon("x")}</button></div>`
						: this.crm.rec.can_unlock ? `<button class="ch-link" data-visit-save="reopen" data-visit="${esc(v.name)}">${t("Reopen")}</button>` : `<span class="ch-vl-lock" title="${t("Locked")}">${icon("lock", 12)}</span>`) : ""}</div>
			</li>`;
		};
		return `<section class="ch-card"><div class="ch-card-h"><h3>${icon("pin", 14)} ${t("Plan a visit")}</h3><span class="ch-muted">${this.crm.meta.has_visit_plans ? t("Added to that day's visit plan") : t("Shows in the Desk calendar")}</span></div>${this.visitForm()}</section>
			<section class="ch-card"><div class="ch-card-h"><h3>${t("Upcoming")} <em class="ch-count">${open.length}</em></h3></div>
				${open.length ? `<ul class="ch-visits">${open.map(row).join("")}</ul>` : `<p class="ch-muted">${t("No visits planned.")}</p>`}</section>
			${past.length ? `<section class="ch-card"><div class="ch-card-h"><h3>${t("Done & cancelled")} <em class="ch-count">${past.length}</em></h3></div><ul class="ch-visits">${past.map(row).join("")}</ul></section>` : ""}`;
	};

	P.lineBadge = function (st) {
		const tone = { Planned: "blue", Visited: "green", "Not Visited": "red", Rescheduled: "amber", Cancelled: "gray" }[st] || "gray";
		return `<span class="ch-badge ch-${tone}">${esc(t(st || "Planned"))}</span>`;
	};

	P.crmLines = function () {
		const R = this.crm.rec, L = R.lines || [], LM = R.line_meta || { party_types: [], visit_types: [], statuses: [] };
		const FIN = ["Visited", "Not Visited", "Rescheduled", "Cancelled"];
		const planClosed = ["Completed", "Cancelled"].includes(R.doc.status);
		const sel = (k, opts, val, label) => `<span class="ch-select ch-select-sm ch-in-wrap"><select class="ch-in" data-k="${k}">${opts.map((o) =>
			`<option value="${esc(o)}" ${o === val ? "selected" : ""}>${esc(t(label ? label(o) : o))}</option>`).join("")}</select>${icon("chev", 12)}</span>`;
		const fld = (label, html, cls = "") => `<div class="ch-vl-f ${cls}"><span class="ch-vl-lbl">${t(label)}</span>${html}</div>`;
		const partyLink = (l) => l.party ? `<button class="ch-ref" data-vl-open="${esc(l.party)}" data-pt="${esc(l.party_type)}">${esc(l.party_name || l.party)}</button>` : `<i class="ch-light">${t("not set")}</i>`;

		const locked = (l, i) => `<li class="ch-vl is-locked ch-vl-${esc((l.status || "").toLowerCase().replace(/\s+/g, "-"))}" data-line="${esc(l.name)}">
			<div class="ch-vl-num">${i + 1}</div>
			<div class="ch-vl-body">
				<div class="ch-vl-sum">
					<b class="ch-vl-time">${esc(l.visit_time || "—")}</b>
					<span class="ch-tag">${esc(t(PT_LABEL[l.party_type] || l.party_type || ""))}</span>
					${partyLink(l)}
					<span class="ch-muted">${esc(t(l.visit_type || ""))}${l.location ? ` · ${esc(l.location)}` : ""}</span>
					<span class="ch-vl-status">${this.lineBadge(l.status)} <span class="ch-vl-lock" title="${t("Locked: finished visits can't be edited")}">${icon("lock", 12)}</span></span>
				</div>
				${l.purpose ? `<div class="ch-vl-line"><span class="ch-vl-lbl">${t("Purpose")}</span> ${esc(l.purpose)}</div>` : ""}
				${l.outcome ? `<div class="ch-vl-outcome-ro"><span class="ch-vl-lbl">${t("Outcome")}</span> ${esc(l.outcome)}</div>` : ""}
				${l.next_followup_date ? `<div class="ch-vl-line"><span class="ch-vl-lbl">${t("Next follow-up")}</span> ${esc(this.date(l.next_followup_date))}${l.followup_created ? ` <span class="ch-vl-note">${icon("check", 10)} ${t("follow-up created")}</span>` : ""}</div>` : ""}
			</div>
			${R.can_unlock ? `<button class="ch-link ch-vl-reopen" data-vl-reopen="${esc(l.name)}" title="${t("Managers only")}">${t("Reopen")}</button>` : ""}
		</li>`;

		const open = (l, i) => {
			const act = this.crm.lineAct && this.crm.lineAct.name === l.name ? this.crm.lineAct.status : null;
			return `<li class="ch-vl ch-vl-planned" data-line="${esc(l.name)}">
			<div class="ch-vl-num">${i + 1}</div>
			<div class="ch-vl-body">
				<div class="ch-vl-row ch-vl-row1">
					${fld("Time", `<input type="time" class="ch-in" data-k="visit_time" value="${esc(l.visit_time || "")}">`)}
					${fld("Visit for", sel("party_type", LM.party_types, l.party_type, (o) => PT_LABEL[o] || o))}
					${fld("Name", `<div class="ch-vl-party"><span class="ch-ac"><input type="text" class="ch-in ch-ac-in" data-k="party" data-fname="party" data-link="${esc(l.party_type)}" autocomplete="off"
						value="${esc(l.party || "")}" placeholder="${t("Search")} ${esc(t(PT_LABEL[l.party_type] || "record")).toLowerCase()}…"><span class="ch-ac-list" hidden></span></span>
						${l.party ? `<button class="ch-icon-btn" data-vl-open="${esc(l.party)}" data-pt="${esc(l.party_type)}" title="${t("Open")}" aria-label="${t("Open")}">${icon("ext")}</button>` : ""}</div>
						${l.party_name && l.party_name !== l.party ? `<span class="ch-vl-pname">${esc(l.party_name)}</span>` : ""}`, "ch-vl-grow")}
					${fld("Visit type", sel("visit_type", LM.visit_types, l.visit_type))}
				</div>
				<div class="ch-vl-row ch-vl-row2">
					${fld("Location", `<input class="ch-in" data-k="location" value="${esc(l.location || "")}" placeholder="${t("Site / area")}">`)}
					${fld("Purpose", `<input class="ch-in" data-k="purpose" value="${esc(l.purpose || "")}" placeholder="${t("Why are we going?")}">`, "ch-vl-grow")}
				</div>
				${act ? `<div class="ch-vl-finish">
					<div class="ch-vl-finish-h">${this.lineBadge(act)} ${t(act === "Visited" ? "How did it go? This locks the visit." : "Why didn't it happen? This locks the visit.")}</div>
					<textarea class="ch-in ch-vl-outcome" rows="2" placeholder="${t(act === "Visited" ? "Outcome, decisions, next step…" : "Reason, e.g. client cancelled")}"></textarea>
					<div class="ch-vl-finish-f">
						<label class="ch-vl-inline">${t("Next follow-up")} <input type="date" class="ch-in ch-vl-nfd"></label>
						<span class="ch-grow"></span>
						<button class="ch-btn ch-soft ch-btn-sm" data-vl-finish-cancel>${t("Back")}</button>
						<button class="ch-btn ch-primary ch-btn-sm" data-vl-finish-save="${esc(act)}" data-line="${esc(l.name)}">${icon("lock", 12)} ${t("Save & lock")}</button>
					</div></div>`
				: `<div class="ch-vl-actions">
					<span class="ch-vl-status">${this.lineBadge("Planned")}</span>
					<span class="ch-grow"></span>
					<button class="ch-btn ch-soft ch-btn-sm ch-vl-ok" data-vl-finish="Visited" data-line="${esc(l.name)}">${icon("check", 12)} ${t("Visited")}</button>
					<button class="ch-btn ch-soft ch-btn-sm" data-vl-finish="Not Visited" data-line="${esc(l.name)}">${t("Not visited")}</button>
					<button class="ch-btn ch-soft ch-btn-sm" data-vl-cancel-visit="${esc(l.name)}">${t("Cancel")}</button>
					<button class="ch-icon-btn" data-vl-remove="${esc(l.name)}" title="${t("Remove visit")}" aria-label="${t("Remove visit")}">${icon("x")}</button>
				</div>`}
			</div>
		</li>`;
		};

		const rows = L.map((l, i) => (FIN.includes(l.status) || (planClosed && !R.can_unlock) || !R.can_write ? locked(l, i) : open(l, i))).join("");
		const canAdd = R.can_write && !R.plan_locked;
		return `${R.plan_locked ? `<div class="ch-ok-note">${icon("lock", 12)} ${t("This plan is")} ${esc(t(R.doc.status))}. ${t("Ask a manager to reopen it.")}</div>` : ""}
			${L.length ? `<ol class="ch-vls">${rows}</ol>` : `<div class="ch-empty ch-empty-lg">${icon("pin", 22)}<p>${t("No visits in this plan yet.")}</p></div>`}
			${canAdd ? `<div class="ch-vl-add"><button class="ch-btn ch-soft" data-vl-add>${icon("plus", 12)} ${t("Add visit")}</button>
				<span class="ch-muted">${t("Planned visits save as you type. Marking a visit Visited / Not visited asks for the outcome and then locks it.")}</span></div>` : ""}`;
	};

	P.saveLine = async function (li) {
		const old = (this.crm.rec.lines || []).find((x) => x.name === li.dataset.line);
		if (!old) return;
		const vals = {};
		// the Name box only counts once a suggestion was picked (typed text alone is not a valid link)
		li.querySelectorAll("[data-k]").forEach((el) => (vals[el.dataset.k] = el.classList.contains("ch-ac-in") ? (el.dataset.picked ?? old.party ?? "") : el.value));
		const changed = Object.keys(vals).filter((k) => String(vals[k] || "") !== String(old[k] || ""));
		if (!changed.length) return;
		li.classList.add("is-saving");
		try {
			const rec = await this.o.api.crmVisitLine(this.crm.recName, "update", li.dataset.line, vals);
			if (this.mode !== "crm-record" || this.crm.recName !== rec.doc.name) return;
			this.crm.rec = rec;
			if (changed.some((k) => ["party", "party_type", "status", "next_followup_date"].includes(k))) this.renderCrmRecord();
			else { li.classList.remove("is-saving"); this.renderCrmSide(); }
		} catch (e) {
			li.classList.remove("is-saving");
			this.o.notify && this.o.notify((e && e.message) || t("Could not save the visit"));
		}
	};

	P.crmAttachments = function () {
		const R = this.crm.rec, list = R.attachments || [];
		const isImg = (f) => /\.(png|jpe?g|gif|webp|svg)$/i.test(f.file_name || "");
		return `${R.can_write ? `<div class="ch-drop" data-dropzone tabindex="0" role="button" aria-label="${t("Upload files")}">
				${icon("upload", 20)}<div><b>${t("Drop files here")}</b> ${t("or")} <button class="ch-link" data-pick-files="att">${t("browse")}</button></div>
				<span class="ch-muted">${t("Files are private: only people who can open this record can see them.")}</span>
				<input type="file" class="ch-file-input" data-for="att" multiple hidden></div>` : ""}
			${(this.crm.uploading || []).map((n) => `<div class="ch-file ch-file-busy"><span class="ch-file-ic">${icon("upload", 14)}</span><b>${esc(n)}</b><span class="ch-muted">${t("Uploading…")}</span></div>`).join("")}
			${list.length ? `<ul class="ch-files">${list.map((f) => `<li class="ch-file">
				<span class="ch-file-ic">${isImg(f) ? `<img src="${esc(f.file_url)}" alt="" loading="lazy">` : `<em>${esc(fext(f.file_name)) || icon("file", 14)}</em>`}</span>
				<button class="ch-file-main" data-open-file="${esc(f.file_url)}" title="${t("Open")}"><b>${esc(f.file_name)}</b><span class="ch-muted">${fsize(f.file_size)} · ${esc(f.by)} · ${timeAgo(f.ts)}</span></button>
				<button class="ch-icon-btn" data-open-file="${esc(f.file_url)}" data-download="1" title="${t("Download")}" aria-label="${t("Download")}">${icon("download")}</button>
				<button class="ch-icon-btn" data-mail-with="${esc(f.name)}" title="${t("Email this file")}" aria-label="${t("Email this file")}">${icon("mail")}</button>
				${R.can_write ? `<button class="ch-icon-btn" data-att-remove="${esc(f.name)}" title="${t("Remove")}" aria-label="${t("Remove")}">${icon("x")}</button>` : ""}
			</li>`).join("")}</ul>` : !(this.crm.uploading || []).length ? `<div class="ch-empty">${t("No attachments yet.")}</div>` : ""}`;
	};

	P.crmUpload = async function (files, forMail) {
		const R = this.crm.rec, M = this.crm.meta.entities[this.crm.entity];
		const list = [...files];
		if (!list.length) return;
		this.readMail();
		this.crm.uploading = (this.crm.uploading || []).concat(list.map((f) => f.name));
		this.renderCrmRecord();
		for (const f of list) {
			try {
				const doc = await this.o.api.upload(M.doctype, R.doc.name, f);
				R.attachments = [{ name: doc.name, file_name: doc.file_name || f.name, file_url: doc.file_url, file_size: doc.file_size || f.size, by: t("You"), ts: new Date().toISOString().replace("T", " ").slice(0, 19) }, ...(R.attachments || [])];
				if (forMail) this.mailState().files.push(doc.name);
			} catch (e) {
				this.o.notify && this.o.notify(`${t("Could not upload")} ${f.name}${e && e.message ? ": " + e.message : ""}`);
			}
			this.crm.uploading = this.crm.uploading.filter((n) => n !== f.name);
			if (this.mode === "crm-record") this.renderCrmRecord();
		}
	};

	P.crmLinked = function () {
		const R = this.crm.rec;
		const list = (entity, rows) => rows.length ? `<ul class="ch-leads">${rows.map((r) => `<li><button class="ch-att-main" data-crm-open="${entity}" data-name="${esc(r.name)}"><b>${esc(r.title)}</b><span class="ch-muted">${esc(r.name)}</span></button>${this.statusPill(entity, r.status)}</li>`).join("")}</ul>` : `<p class="ch-muted">${t("None.")}</p>`;
		return `<section class="ch-card"><div class="ch-card-h"><h3>${icon("target", 14)} ${t("Deals")}</h3></div>${list("deal", R.deals || [])}</section>
			<section class="ch-card"><div class="ch-card-h"><h3>${icon("star", 14)} ${t("Leads")}</h3><span class="ch-muted">${t("matched by email")}</span></div>${list("lead", R.leads || [])}</section>`;
	};

	P.renderCrmSide = function () {
		const entity = this.crm.entity, R = this.crm.rec, D = R.doc, M = this.crm.meta.entities[entity];
		const iv = (f) => {
			const d = { ...M.fields[f], _entity: entity };
			if (!d.fieldname) return "";
			const val = D[f];
			const shown = f === "mobile_no" || f === "phone" ? (val ? `${esc(val)}` : `<i class="ch-light">${t("Add")}…</i>`) : val == null || val === "" ? `<i class="ch-light">${t("Add")} ${esc(d.label).toLowerCase()}…</i>` : this.fmtVal(d, val, D);
			const editable = R.can_write && !d.read_only;
			return `<div class="ch-kv"><span>${esc(d.label)}</span>${editable ? `<button class="ch-iv" data-iv="${esc(f)}" title="${t("Click to edit")}">${shown}</button>` : `<span>${shown}</span>`}</div>`;
		};
		const email = D.email || D.email_id, phone = D.mobile_no || D.phone;
		this.$(".ch-side").innerHTML = `
			<div class="ch-side-id">${esc(D.name)}</div>
			<div class="ch-side-hero"><span class="ch-av ch-av-lg">${esc((D.title || "?").trim().charAt(0).toUpperCase())}</span>
				<div><div class="ch-side-name">${esc(D.title)}</div><div class="ch-side-actions">
					${email ? `<a class="ch-icon-btn" href="mailto:${esc(email)}" title="${t("Email")} ${esc(email)}" aria-label="${t("Email")}">${icon("mail")}</a>` : ""}
					${phone ? `<a class="ch-icon-btn" href="tel:${esc(phone)}" title="${t("Call")} ${esc(phone)}" aria-label="${t("Call")}">${icon("phone")}</a>` : ""}
					<button class="ch-icon-btn" data-open-desk="${esc(M.doctype)}" data-name="${esc(D.name)}" title="${t("Open in Desk")}" aria-label="${t("Open in Desk")}">${icon("ext")}</button>
				</div></div></div>
			${entity === "lead" && R.converted ? `<div class="ch-ok-note">${icon("check", 12)} ${t("Converted to a deal")}</div>` : ""}
			${entity === "visit" ? (() => {
				const L = R.lines || [], live = L.filter((l) => l.status !== "Cancelled");
				const done = L.filter((l) => l.status === "Visited").length;
				const by = {};
				L.forEach((l) => (by[l.status] = (by[l.status] || 0) + 1));
				return `<div class="ch-next"><div class="ch-next-h">${t("Progress")}</div>
					<div><b class="ch-vp-big">${done}</b> ${t("of")} ${live.length} ${t("visited")}</div>
					<div class="ch-prog ch-prog-wide"><i style="width:${live.length ? Math.round((done / live.length) * 100) : 0}%"></i></div>
					<div class="ch-fu-meta">${Object.entries(by).map(([k, n]) => `${this.lineBadge(k)} <span class="ch-muted">${n}</span>`).join(" ")}</div></div>`;
			})() : ""}
			${(entity === "lead" || entity === "deal") && this.crm.meta.has_tasks ? (() => {
				const nx = R.tasks.filter((x) => !["Done", "Canceled"].includes(x.status)).sort((a, b) => ((a.due_date || "9") < (b.due_date || "9") ? -1 : 1))[0];
				const nv = (R.visits || []).filter((v) => v.status === "Open").sort((a, b) => (a.starts_on < b.starts_on ? -1 : 1))[0];
				return `<div class="ch-next">
					<div class="ch-next-h">${t("Next follow-up")}</div>
					${nx ? `<div class="ch-next-row"><button class="ch-done" data-task-toggle="${esc(nx.name)}" data-to="Done" title="${t("Mark as done")}" aria-label="${t("Mark as done")}">${icon("check", 12)}</button>
						<div class="ch-fu-main"><div class="ch-fu-title">${nx.type ? `${icon(FU_ICON[nx.type] || "calendar", 11)} ` : ""}${esc(nx.title)}</div></div>
						${nx.due_date ? (() => { const d = this.dueLabel(nx.due_date); return `<span class="ch-badge ch-${d.tone}">${esc(d.text)}</span>`; })() : ""}</div>`
						: `<button class="ch-btn ch-soft ch-btn-sm" data-log-crm="task">${icon("plus", 12)} ${t("Add follow-up")}</button>`}
					${this.crm.meta.has_visits ? (nv ? `<div class="ch-next-row ch-next-visit">${icon("pin", 12)}<div class="ch-fu-main"><div class="ch-fu-title">${esc(nv.type || t("Visit"))} · ${esc(this.date((nv.starts_on || "").slice(0, 10)))} ${esc(hm(nv.starts_on))}</div>${nv.location ? `<div class="ch-muted">${esc(nv.location)}</div>` : ""}</div>${this.visitBadge(nv)}</div>`
						: `<button class="ch-btn ch-soft ch-btn-sm" data-crm-tab="visits">${icon("pin", 12)} ${t("Plan visit")}</button>`) : ""}
				</div>`;
			})() : ""}
			${entity === "deal" ? `<details open><summary>${icon("chev", 12)} ${t("Contacts")} <em class="ch-count">${R.contacts.length}</em></summary>
				${R.contacts.length ? `<ul class="ch-contacts">${R.contacts.map((c) => `<li>
					<button class="ch-att-main" data-crm-open="contact" data-name="${esc(c.name)}"><b>${esc(c.title)}${c.is_primary ? ` <span class="ch-tag">${t("Primary")}</span>` : ""}</b><span class="ch-muted">${esc(c.email_id || c.mobile_no || "")}</span></button>
					${c.mobile_no ? `<a class="ch-icon-btn" href="tel:${esc(c.mobile_no)}" aria-label="${t("Call")}">${icon("phone")}</a>` : ""}
					${R.can_write ? `<button class="ch-icon-btn" data-deal-contact="remove" data-contact="${esc(c.name)}" title="${t("Remove from deal")}" aria-label="${t("Remove from deal")}">${icon("x")}</button>` : ""}</li>`).join("")}</ul>` : `<p class="ch-muted ch-side-note">${t("No contacts yet.")}</p>`}
				${R.can_write ? `<div class="ch-add-contact">${this.fieldInput({ fieldname: "add_contact", fieldtype: "Link", options: "Contact", label: "contact" }, "", "data-add-contact")}</div>` : ""}
			</details>` : ""}
			${M.panel.map(([g, fs]) => fs.length ? `<details open><summary>${icon("chev", 12)} ${t(g)}</summary>${fs.map(iv).join("")}</details>` : "").join("")}
			${entity === "deal" && R.lead ? `<details open><summary>${icon("chev", 12)} ${t("From lead")}</summary><button class="ch-ref" data-crm-open="lead" data-name="${esc(R.lead)}">${esc(R.lead)}</button></details>` : ""}`;
	};

	P.crmInlineEdit = function (btn) {
		const f = btn.dataset.iv, entity = this.crm.entity, M = this.crm.meta.entities[entity];
		const d = { ...M.fields[f], _entity: entity };
		const wrap = document.createElement("span");
		wrap.className = "ch-iv-edit";
		wrap.innerHTML = this.fieldInput(d, this.crm.rec.doc[f], 'data-crm-set="1"');
		btn.replaceWith(wrap);
		const inp = wrap.querySelector("[data-fname]");
		inp.focus();
		if (inp.select && inp.type === "text") inp.select();
		const finish = (save) => {
			if (wrap._done) return;
			wrap._done = true;
			if (save) this.crmSave(f, this.readInput(inp));
			else this.renderCrmSide();
		};
		inp.addEventListener("keydown", (e) => {
			if (e.key === "Enter" && inp.tagName !== "TEXTAREA" && !inp.classList.contains("ch-ac-in")) { e.preventDefault(); finish(true); }
			if (e.key === "Escape") { e.stopPropagation(); finish(false); }
		});
		inp.addEventListener("blur", () => setTimeout(() => {
			if (wrap.contains(document.activeElement) || wrap.querySelector(".ch-ac-list:not([hidden])")) return;
			finish(String(this.readInput(inp)) !== String(this.crm.rec.doc[f] ?? ""));
		}, 150));
		if (inp.tagName === "SELECT" || inp.type === "date" || inp.type === "checkbox") inp.addEventListener("change", () => finish(true));
		inp._commit = () => finish(true);
	};

	P.crmSave = async function (field, value) {
		const entity = this.crm.entity, name = this.crm.recName;
		try {
			const rec = await this.o.api.crmSet(entity, name, field, value);
			this.loadCrmRecord(rec);
		} catch (e) {
			this.o.notify ? this.o.notify((e && e.message) || t("Could not save")) : alert(t("Could not save"));
			this.loadCrmRecord();
		}
	};

	/* ---------------- link autocomplete ---------------- */
	P.acSearch = async function (inp) {
		const list = inp.parentElement.querySelector(".ch-ac-list");
		const q = inp.value.trim();
		const req = (inp._req = (inp._req || 0) + 1);
		let rows = [];
		try { rows = await this.o.api.crmSearch(inp.dataset.link, q); } catch (e) { rows = []; }
		if (req !== inp._req) return;
		const canNew = inp.dataset.fname === "organization" && q && !rows.some((r) => r.value.toLowerCase() === q.toLowerCase());
		list.innerHTML = rows.map((r, i) => `<button type="button" class="ch-ac-opt ${i === 0 ? "is-on" : ""}" data-ac="${esc(r.value)}"><b>${esc(r.label)}</b>${r.sub ? `<span>${esc(r.sub)}</span>` : r.label !== r.value ? `<span>${esc(r.value)}</span>` : ""}</button>`).join("")
			+ (canNew ? `<button type="button" class="ch-ac-opt ch-ac-new ${rows.length ? "" : "is-on"}" data-ac="${esc(q)}">${icon("plus", 12)} ${t("Create")} “${esc(q)}”</button>` : "")
			+ (!rows.length && !canNew ? `<div class="ch-ac-none">${t("No matches")}</div>` : "");
		list.hidden = false;
	};
	P.acPick = function (inp, value) {
		inp.value = value;
		const list = inp.parentElement.querySelector(".ch-ac-list");
		list.hidden = true;
		if (inp.closest(".ch-vl")) { inp.dataset.picked = value; return this.saveLine(inp.closest(".ch-vl")); }
		if (inp.hasAttribute("data-add-contact")) return this.crmDealContact("add", value);
		if (inp._commit) inp._commit();
	};

	P.crmDealContact = async function (action, contact) {
		try {
			const rec = await this.o.api.crmDealContact(this.crm.recName, contact, action);
			this.loadCrmRecord(rec);
		} catch (e) {
			this.o.notify && this.o.notify((e && e.message) || t("Could not update contacts"));
		}
	};

	/* ---------------- clicks for CRM ---------------- */
	P.crmClick = async function (e) {
		const el = (s) => e.target.closest(s);
		let x;
		if (el("[data-modal-close]")) { this.crmCloseModal(); return true; }
		if ((x = el("[data-open-desk]"))) { (this.o.openDesk || this.o.openDoc)(x.dataset.openDesk, x.dataset.name); return true; }
		if ((x = el("[data-next-step]"))) {
			const st = (this.crm.rec.next_steps || [])[+x.dataset.nextStep];
			if (st) this.o.newDoc(st.doctype, this.crm.rec.customer, st.values);
			return true;
		}
		if ((x = el("[data-ac]"))) { e.preventDefault(); this.acPick(x.closest(".ch-ac").querySelector(".ch-ac-in"), x.dataset.ac); return true; }
		if (!this.crm || !this.crm.meta) return false;
		if ((x = el("[data-crm-new]"))) { this.crmNewForm(x.dataset.crmNew); return true; }
		if ((x = el("[data-crm-owner]"))) { this.crm.lists[this.crm.entity].owner = x.dataset.crmOwner; this.showCrmList(this.crm.entity); return true; }
		if ((x = el("[data-crm-view]"))) { this.crm.lists.deal.view = x.dataset.crmView; this.showCrmList("deal"); return true; }
		if ((x = el("[data-crm-status]"))) { this.crm.lists[this.crm.entity].status = x.dataset.crmStatus; this.loadCrmList(); return true; }
		if ((x = el("[data-crm-tab]"))) {
			this.crm.recTab = x.dataset.crmTab;
			if (this.crm.recTab === "activity") this.crm.logKind = "comment";
			this.renderCrmRecord();
			return true;
		}
		if ((x = el("[data-crm-kind]"))) {
			this.crm.logKind = x.dataset.crmKind;
			const keep = this.$(".ch-crm-text")?.value || this.$(".ch-mail-body")?.value || "";
			this.readMail();
			const keptMentions = (this.$(".ch-crm-text") || {})._mentions;
			this.$(".ch-crm-composer").outerHTML = this.crmComposer(this.crm.recTab === "activity" ? this.activityKinds() : [this.crm.logKind]);
			const ta = this.$(".ch-crm-text");
			if (ta) { ta.value = keep; ta._mentions = keptMentions; (this.$(".ch-crm-title") || ta).focus(); }
			else (this.$(".ch-mail-to").value ? this.$(".ch-mail-subject") : this.$(".ch-mail-to")).focus();
			return true;
		}
		if (el("[data-vl-add]")) {
			const R = this.crm.rec, L = R.lines || [], last = L[L.length - 1];
			let time = "09:00";
			if (last && last.visit_time) { const [h, m] = last.visit_time.split(":").map(Number); time = `${String(Math.min(h + 1, 23)).padStart(2, "0")}:${String(m || 0).padStart(2, "0")}`; }
			try {
				this.crm.rec = await this.o.api.crmVisitLine(this.crm.recName, "add", null, {
					visit_time: time, party_type: last ? last.party_type : "CRM Lead", visit_type: (R.line_meta && R.line_meta.visit_types[0]) || "", status: "Planned",
				});
				this.crm.recTab = "lines";
				this.renderCrmRecord();
				const items = this.root.querySelectorAll(".ch-vl");
				items[items.length - 1]?.querySelector('[data-k="party"]')?.focus();
			} catch (err) { this.o.notify && this.o.notify((err && err.message) || t("Could not add the visit")); }
			return true;
		}
		if ((x = el("[data-vl-finish]"))) {
			const li = x.closest(".ch-vl");
			await this.saveLine(li);
			const line = (this.crm.rec.lines || []).find((l) => l.name === x.dataset.line);
			if (line && !line.party) { this.o.notify && this.o.notify(t("Pick who you visited first")); li.querySelector('[data-k="party"]')?.focus(); return true; }
			this.crm.lineAct = { name: x.dataset.line, status: x.dataset.vlFinish };
			this.renderCrmRecord();
			this.$(".ch-vl-outcome")?.focus();
			return true;
		}
		if (el("[data-vl-finish-cancel]")) { this.crm.lineAct = null; this.renderCrmRecord(); return true; }
		if ((x = el("[data-vl-finish-save]"))) {
			const box = x.closest(".ch-vl-finish"), outcome = box.querySelector(".ch-vl-outcome").value.trim();
			if (!outcome) { box.querySelector(".ch-vl-outcome").focus(); return true; }
			x.disabled = true;
			try {
				this.crm.rec = await this.o.api.crmVisitLine(this.crm.recName, "finish", x.dataset.line,
					{ status: x.dataset.vlFinishSave, outcome, next_followup_date: box.querySelector(".ch-vl-nfd").value || "" });
				this.crm.lineAct = null;
				this.renderCrmRecord();
			} catch (err) { x.disabled = false; this.o.notify && this.o.notify((err && err.message) || t("Could not save")); }
			return true;
		}
		if ((x = el("[data-vl-cancel-visit]"))) {
			if (!(await this.confirm(t("Cancel this visit? It will be locked.")))) return true;
			try {
				this.crm.rec = await this.o.api.crmVisitLine(this.crm.recName, "finish", x.dataset.vlCancelVisit, { status: "Cancelled", outcome: "" });
				this.renderCrmRecord();
			} catch (err) { this.o.notify && this.o.notify((err && err.message) || t("Could not cancel")); }
			return true;
		}
		if ((x = el("[data-vl-reopen]"))) {
			if (!(await this.confirm(t("Reopen this visit so it can be edited again?")))) return true;
			try {
				this.crm.rec = await this.o.api.crmVisitLine(this.crm.recName, "reopen", x.dataset.vlReopen, {});
				this.renderCrmRecord();
			} catch (err) { this.o.notify && this.o.notify((err && err.message) || t("Could not reopen")); }
			return true;
		}
		if ((x = el("[data-vl-remove]"))) {
			if (!(await this.confirm(t("Remove this visit from the plan?")))) return true;
			try {
				this.crm.rec = await this.o.api.crmVisitLine(this.crm.recName, "remove", x.dataset.vlRemove, {});
				this.renderCrmRecord();
			} catch (err) { this.o.notify && this.o.notify((err && err.message) || t("Could not remove")); }
			return true;
		}
		if ((x = el("[data-vl-open]"))) {
			const pt = x.dataset.pt;
			if (pt === "Customer") this.selectCustomer(x.dataset.vlOpen);
			else if (DOCTYPE_ENTITY[pt]) this.showCrmRecord(DOCTYPE_ENTITY[pt], x.dataset.vlOpen);
			return true;
		}
		if (el("[data-visit-plan]")) {
			const q = (s) => this.$(s) && this.$(s).value;
			const vals = { type: q(".ch-v-type"), by: q(".ch-v-by"), date: q(".ch-v-date"), time: q(".ch-v-time-in"), minutes: q(".ch-v-min"),
				location: q(".ch-v-loc"), purpose: q(".ch-v-purpose"), notes: q(".ch-v-notes") };
			if (!vals.date) { this.$(".ch-v-date").focus(); return true; }
			const b = el("[data-visit-plan]");
			b.disabled = true;
			try {
				if (this.crm.meta.has_visit_plans) {
					const plan = await this.o.api.crmAddToPlan(this.crm.entity, this.crm.recName, vals);
					this.o.notify && this.o.notify(`${t("Added to visit plan")} ${plan}`, "green");
				} else {
					this.crm.rec.visits = await this.o.api.crmPlanVisit(this.crm.entity, this.crm.recName, vals);
					this.o.notify && this.o.notify(t("Visit planned"), "green");
				}
				await this.loadCrmRecord();
			} catch (err) {
				b.disabled = false;
				this.o.notify && this.o.notify((err && err.message) || t("Could not plan the visit"));
			}
			return true;
		}
		if ((x = el("[data-visit-act]"))) { this.crm.visitAct = { name: x.dataset.visit, action: x.dataset.visitAct }; this.renderCrmRecord(); this.$(".ch-v-outcome, .ch-visit-act .ch-v-date")?.focus(); return true; }
		if (el("[data-visit-cancel-act]")) { this.crm.visitAct = null; this.renderCrmRecord(); return true; }
		if ((x = el("[data-visit-save]"))) {
			const action = x.dataset.visitSave, box = x.closest(".ch-visit");
			if (action === "cancel" && !(await this.confirm(t("Cancel this visit?")))) return true;
			if (action === "complete" && !box.querySelector(".ch-v-outcome").value.trim()) { box.querySelector(".ch-v-outcome").focus(); return true; }
			const vals = action === "complete" ? { outcome: box.querySelector(".ch-v-outcome").value }
				: action === "reschedule" ? { date: box.querySelector(".ch-v-date").value, time: box.querySelector(".ch-v-time-in").value } : {};
			x.disabled = true;
			try {
				this.crm.rec.visits = await this.o.api.crmUpdateVisit(this.crm.entity, this.crm.recName, x.dataset.visit, action, vals);
				this.crm.visitAct = null;
				await this.loadCrmRecord();
			} catch (err) {
				x.disabled = false;
				this.o.notify && this.o.notify((err && err.message) || t("Could not update the visit"));
			}
			return true;
		}
		if ((x = el("[data-mail-cc]"))) { this.readMail(); this.crm.mail.showCc = true; this.$(".ch-crm-composer").outerHTML = this.crmComposer(this.activityKinds()); this.$(".ch-mail-cc").focus(); return true; }
		if ((x = el("[data-mail-file]"))) {
			this.readMail();
			const m = this.mailState(), f = x.dataset.mailFile;
			m.files = m.files.includes(f) ? m.files.filter((k) => k !== f) : m.files.concat(f);
			this.$(".ch-crm-composer").outerHTML = this.crmComposer(this.activityKinds());
			return true;
		}
		if ((x = el("[data-pick-files]"))) {
			e.preventDefault();
			this.root.querySelector(`.ch-file-input[data-for="${x.dataset.pickFiles}"]`)?.click();
			return true;
		}
		if ((x = el("[data-dropzone]")) && e.target === x) { x.querySelector(".ch-file-input").click(); return true; }
		if ((x = el("[data-open-file]"))) {
			const url = x.dataset.openFile;
			if (x.dataset.download) { const a = document.createElement("a"); a.href = url; a.download = ""; document.body.appendChild(a); a.click(); a.remove(); }
			else window.open(url, "_blank", "noopener");
			return true;
		}
		if ((x = el("[data-att-remove]"))) {
			const f = (this.crm.rec.attachments || []).find((a) => a.name === x.dataset.attRemove);
			if (!(await this.confirm(`${t("Remove")} ${f ? f.file_name : t("this file")}?`))) return true;
			try {
				this.crm.rec.attachments = await this.o.api.crmRemoveAttachment(this.crm.entity, this.crm.recName, x.dataset.attRemove);
				if (this.crm.mail) this.crm.mail.files = this.crm.mail.files.filter((k) => k !== x.dataset.attRemove);
				this.renderCrmRecord();
			} catch (err) { this.o.notify && this.o.notify((err && err.message) || t("Could not remove the file")); }
			return true;
		}
		if ((x = el("[data-mail-with]"))) {
			const m = this.mailState();
			if (!m.files.includes(x.dataset.mailWith)) m.files.push(x.dataset.mailWith);
			this.crm.logKind = "email";
			this.crm.recTab = "activity";
			this.renderCrmRecord();
			this.$(m.to ? ".ch-mail-subject" : ".ch-mail-to")?.focus();
			return true;
		}
		if ((x = el("[data-reply]"))) {
			const r = JSON.parse(x.dataset.reply);
			const m = this.mailState();
			m.to = (r.to || "").split(",")[0].trim();
			m.subject = /^re:/i.test(r.subject || "") ? r.subject : `Re: ${r.subject || ""}`;
			this.crm.logKind = "email";
			this.renderCrmRecord();
			this.$(".ch-mail-body")?.focus();
			this.$(".ch-main")?.scrollTo?.({ top: 0, behavior: "smooth" });
			return true;
		}
		if ((x = el("[data-mail-send]"))) {
			this.readMail();
			const m = this.crm.mail;
			if (!m.to.trim()) { this.$(".ch-mail-to").focus(); return true; }
			if (!m.subject.trim()) { this.$(".ch-mail-subject").focus(); return true; }
			if (!m.body.trim() && !(await this.confirm(t("Send without a message?")))) return true;
			x.disabled = true;
			x.innerHTML = `${icon("send")} ${t("Sending…")}`;
			try {
				await this.o.api.crmSendEmail(this.crm.entity, this.crm.recName, { recipients: m.to, cc: m.cc, subject: m.subject, content: m.body, attachments: m.files });
				this.crm.mail = null;
				this.o.toast ? this.o.toast(t("Email sent")) : this.o.notify && this.o.notify(t("Email sent"), "green");
				await this.loadCrmRecord();
			} catch (err) {
				x.disabled = false;
				x.innerHTML = `${icon("send")} ${t("Send email")}`;
				this.o.notify && this.o.notify((err && err.message) || t("Could not send. Check the outgoing email account."));
			}
			return true;
		}
		if ((x = el("[data-crm-add]"))) {
			const kind = this.crm.logKind;
			const text = this.$(".ch-crm-text").value.trim();
			const title = this.$(".ch-crm-title")?.value.trim();
			if ((kind === "task" && !title) || (kind !== "task" && kind !== "note" && !text) || (kind === "note" && !text && !title)) {
				(this.$(".ch-crm-title") || this.$(".ch-crm-text")).focus();
				return true;
			}
			x.disabled = true;
			try {
				await this.o.api.crmAdd(this.crm.entity, this.crm.recName, kind, {
					content: text, title, due_date: kind === "task" ? this.$(".ch-fu-date").value : null,
					mentions: this.mentionsOf(this.$(".ch-crm-text")),
					assigned_to: kind === "task" ? this.$(".ch-crm-assign").value : null,
					followup_type: kind === "task" && this.$(".ch-crm-futype") ? this.$(".ch-crm-futype").value : null,
				});
				await this.loadCrmRecord();
			} catch (err) {
				x.disabled = false;
			}
			return true;
		}
		if ((x = el("[data-task-toggle]"))) {
			x.disabled = true;
			x.closest("li")?.classList.toggle("is-done");
			try { await this.o.api.crmTaskStatus(x.dataset.taskToggle, x.dataset.to); } catch (err) {}
			await this.loadCrmRecord();
			return true;
		}
		if ((x = el("[data-iv]"))) { this.crmInlineEdit(x); return true; }
		if ((x = el("[data-log-crm]"))) {
			this.crm.recTab = "activity";
			this.crm.logKind = x.dataset.logCrm;
			this.renderCrmRecord();
			(this.$(".ch-crm-title") || this.$(".ch-crm-text"))?.focus();
			return true;
		}
		if (el("[data-crm-convert]")) {
			if (!(await this.confirm(t("Convert this lead to a deal? A contact and organization are created from the lead's details.")))) return true;
			try {
				const deal = await this.o.api.crmConvertLead(this.crm.recName);
				this.showCrmRecord("deal", deal);
			} catch (err) { this.o.notify && this.o.notify((err && err.message) || t("Could not convert")); }
			return true;
		}
		if (el("[data-crm-to-customer]")) {
			try {
				const c = await this.o.api.crmDealToCustomer(this.crm.recName);
				this.selectCustomer(c);
			} catch (err) { this.o.notify && this.o.notify((err && err.message) || t("Could not create the customer")); }
			return true;
		}
		if ((x = el("[data-deal-contact]"))) { this.crmDealContact(x.dataset.dealContact, x.dataset.contact); return true; }
		if ((x = el("[data-crm-open]"))) {
			if (e.target.closest("a")) return false;
			this.showCrmRecord(x.dataset.crmOpen, x.dataset.name);
			return true;
		}
		return false;
	};

	P.confirm = function (msg) {
		return this.o.confirm ? this.o.confirm(msg) : Promise.resolve(window.confirm(msg));
	};

	/* ---------------- navigation history ---------------- */
	P.pushView = function () {
		this.stack = this.stack || [];
		const v = { mode: this.mode, entity: this.crm && this.crm.entity, name: this.crm && this.crm.recName, customer: this.customer };
		if (v.mode === "crm-record" || v.mode === "hub" || v.mode === "home" || v.mode === "list" || v.mode === "crm-list") this.stack.push(v);
		if (this.stack.length > 20) this.stack.shift();
	};
	P.goBack = function () {
		const v = (this.stack || []).pop();
		if (!v || v.mode === "home") return this.showHome();
		if (v.mode === "list") return this.showList();
		if (v.mode === "crm-list") return this.showCrmList(v.entity);
		if (v.mode === "crm-record") return this.showCrmRecord(v.entity, v.name, true);
		if (v.mode === "hub") { this.mode = "x"; return this.setCustomer(v.customer, true); }
		return this.showHome();
	};
	P._crmReq = 0;

	// drag & drop deals between stages on the board (+ file drops on attachments)
	P.bindBoardDnD = function () {
		let dragging = null;
		this.root.addEventListener("change", (e) => {
			const li = e.target.closest && e.target.closest(".ch-vl");
			if (li && e.target.dataset.k && !e.target.classList.contains("ch-ac-in")) {
				if (e.target.dataset.k === "party_type") {
					const p = li.querySelector('[data-k="party"]');
					p.value = "";
					p.dataset.picked = "";
					p.dataset.link = e.target.value;
				}
				this.saveLine(li);
				return;
			}
			if (!e.target.classList.contains("ch-file-input")) return;
			const files = e.target.files;
			if (files && files.length) this.crmUpload(files, e.target.dataset.for === "mail");
			e.target.value = "";
		});
		const fileDrag = (e) => e.dataTransfer && [...(e.dataTransfer.types || [])].includes("Files");
		this.root.addEventListener("dragover", (e) => {
			const z = e.target.closest && e.target.closest("[data-dropzone], .ch-mail-composer");
			if (!z || !fileDrag(e)) return;
			e.preventDefault();
			z.classList.add("is-over");
		});
		this.root.addEventListener("dragleave", (e) => {
			const z = e.target.closest && e.target.closest("[data-dropzone], .ch-mail-composer");
			if (z && !z.contains(e.relatedTarget)) z.classList.remove("is-over");
		});
		this.root.addEventListener("drop", (e) => {
			const z = e.target.closest && e.target.closest("[data-dropzone], .ch-mail-composer");
			if (!z || !fileDrag(e)) return;
			e.preventDefault();
			z.classList.remove("is-over");
			this.crmUpload(e.dataTransfer.files, z.classList.contains("ch-mail-composer"));
		});
		this.root.addEventListener("dragstart", (e) => {
			const c = e.target.closest && e.target.closest("[data-drag-deal]");
			if (!c) return;
			dragging = c.dataset.dragDeal;
			c.classList.add("is-dragging");
			e.dataTransfer.effectAllowed = "move";
			e.dataTransfer.setData("text/plain", dragging);
		});
		this.root.addEventListener("dragend", (e) => {
			e.target.closest && e.target.closest("[data-drag-deal]")?.classList.remove("is-dragging");
			this.root.querySelectorAll(".ch-bcol.is-over").forEach((c) => c.classList.remove("is-over"));
		});
		this.root.addEventListener("dragover", (e) => {
			const col = e.target.closest && e.target.closest("[data-drop-status]");
			if (!col || !dragging || !col.dataset.dropStatus) return;
			e.preventDefault();
			this.root.querySelectorAll(".ch-bcol.is-over").forEach((c) => c !== col && c.classList.remove("is-over"));
			col.classList.add("is-over");
		});
		this.root.addEventListener("drop", async (e) => {
			const col = e.target.closest && e.target.closest("[data-drop-status]");
			if (!col || !dragging) return;
			e.preventDefault();
			const name = dragging, status = col.dataset.dropStatus;
			dragging = null;
			const L = this.crm.lists.deal;
			const row = L.rows.find((r) => r.name === name);
			if (!row || row.status === status) return this.renderCrmList();
			const old = row.status;
			row.status = status;
			this.renderCrmList();
			try {
				await this.o.api.crmSet("deal", name, "status", status);
			} catch (err) {
				row.status = old;
				this.renderCrmList();
				this.o.notify && this.o.notify((err && err.message) || t("Could not move the deal"));
			}
		});
	};

	/* ---------------- @mentions ---------------- */
	P.mentionUsers = async function () {
		if (this.crm && this.crm.meta && this.crm.meta.users) return this.crm.meta.users;
		if (!this._mUsers) {
			try { this._mUsers = this.o.api.mentionUsers ? await this.o.api.mentionUsers() : []; } catch (e) { this._mUsers = []; }
		}
		return this._mUsers;
	};
	P.hl = function (text) {
		let h = esc(text || "").replace(/\n/g, "<br>");
		const us = (this.crm && this.crm.meta && this.crm.meta.users) || this._mUsers || [];
		for (const u of us) {
			const tok = "@" + esc(u.full_name);
			if (u.full_name && h.includes(tok)) h = h.split(tok).join(`<span class="ch-mention">${tok}</span>`);
		}
		return h;
	};
	P.mentionsOf = function (ta) {
		const m = (ta && ta._mentions) || {};
		return Object.keys(m).filter((id) => ta.value.includes("@" + m[id]));
	};
	P.mentionInput = async function (ta) {
		const before = ta.value.slice(0, ta.selectionStart);
		const m = before.match(/(?:^|\s)@([^\s@]{0,30})$/);
		let box = ta._mbox;
		if (!m) { if (box) box.hidden = true; return; }
		const q = m[1].toLowerCase();
		const users = (await this.mentionUsers()).filter((u) => `${u.full_name} ${u.name}`.toLowerCase().includes(q)).slice(0, 7);
		if (!box || !box.isConnected) {
			box = document.createElement("div");
			box.className = "ch-ac-list ch-mention-list";
			box.setAttribute("role", "listbox");
			ta.insertAdjacentElement("afterend", box);
			ta._mbox = box;
			box._ta = ta;
		}
		box.style.top = `${ta.offsetTop + ta.offsetHeight + 4}px`;
		box.style.left = `${ta.offsetLeft}px`;
		box.innerHTML = users.length
			? users.map((u, i) => `<button type="button" role="option" class="ch-ac-opt ${i === 0 ? "is-on" : ""}" data-mention="${esc(u.name)}" data-mname="${esc(u.full_name)}"><b>${esc(u.full_name)}</b><span>${esc(u.name)}</span></button>`).join("")
			: `<div class="ch-ac-none">${t("No user matches")} “${esc(m[1])}”</div>`;
		box.hidden = false;
	};
	P.mentionPick = function (box, id, name) {
		const ta = box._ta, pos = ta.selectionStart;
		const before = ta.value.slice(0, pos), after = ta.value.slice(pos);
		const start = before.lastIndexOf("@");
		const ins = `@${name} `;
		ta.value = before.slice(0, start) + ins + after;
		const c = start + ins.length;
		ta.focus();
		ta.setSelectionRange(c, c);
		ta._mentions = { ...(ta._mentions || {}), [id]: name };
		box.hidden = true;
	};
	const MENTION_TA = "textarea.ch-comment-input, textarea.ch-crm-text";
	document.addEventListener("input", (e) => {
		if (!e.target.matches || !e.target.matches(MENTION_TA)) return;
		const hub = e.target.closest(".ch")?.parentElement?.__hub;
		if (hub) hub.mentionInput(e.target);
	});
	document.addEventListener("mousedown", (e) => {
		if (e.target.closest && e.target.closest(".ch-mention-list")) e.preventDefault(); // keep the cursor in the box
	});
	document.addEventListener("click", (e) => {
		const b = e.target.closest && e.target.closest(".ch-mention-list [data-mention]");
		if (!b) return;
		const hub = b.closest(".ch")?.parentElement?.__hub;
		if (hub) hub.mentionPick(b.closest(".ch-mention-list"), b.dataset.mention, b.dataset.mname);
	});
	document.addEventListener("keydown", (e) => {
		if (!e.target.matches || !e.target.matches(MENTION_TA)) return;
		const box = e.target._mbox;
		if (!box || box.hidden) return;
		const opts = [...box.querySelectorAll("[data-mention]")];
		const i = opts.findIndex((o) => o.classList.contains("is-on"));
		if ((e.key === "ArrowDown" || e.key === "ArrowUp") && opts.length) {
			e.preventDefault();
			const n = (i + (e.key === "ArrowDown" ? 1 : -1) + opts.length) % opts.length;
			opts.forEach((o, k) => o.classList.toggle("is-on", k === n));
		} else if ((e.key === "Enter" || e.key === "Tab") && opts[i]) {
			e.preventDefault();
			e.stopPropagation();
			const hub = e.target.closest(".ch")?.parentElement?.__hub;
			hub && hub.mentionPick(box, opts[i].dataset.mention, opts[i].dataset.mname);
		} else if (e.key === "Escape") {
			e.stopPropagation();
			box.hidden = true;
		}
	}, true);
	document.addEventListener("focusout", (e) => {
		if (e.target.matches && e.target.matches(MENTION_TA) && e.target._mbox) setTimeout(() => (e.target._mbox.hidden = true), 150);
	});

	// delegated input / keyboard handlers
	let searchTimer;
	document.addEventListener("input", (e) => {
		const hub = e.target.closest(".ch")?.parentElement?.__hub;
		if (!hub) return;
		if (e.target.classList.contains("ch-filter")) {
			hub.filter = e.target.value;
			const pos = e.target.selectionStart;
			hub.renderContent();
			const inp = hub.$(".ch-filter");
			inp.focus();
			inp.setSelectionRange(pos, pos);
		}
		if (e.target.classList.contains("ch-crm-search")) {
			hub.crm.lists[hub.crm.entity].txt = e.target.value.trim();
			clearTimeout(searchTimer);
			searchTimer = setTimeout(() => hub.loadCrmList(), 300);
		}
		if (e.target.classList.contains("ch-ac-in")) {
			clearTimeout(e.target._t);
			e.target._t = setTimeout(() => hub.acSearch(e.target), 200);
		}
		if (e.target.classList.contains("ch-cust-search")) {
			hub.list.txt = e.target.value.trim();
			clearTimeout(searchTimer);
			searchTimer = setTimeout(() => hub.loadCustomers(true), 250);
		}
	});
	document.addEventListener("change", (e) => {
		const hub = e.target.closest(".ch")?.parentElement?.__hub;
		if (!hub) return;
		const cl = e.target.classList;
		if (cl.contains("ch-crm-ltype")) {
			hub.crm.lists.lead.lead_type = e.target.value;
			hub.showCrmList("lead");
			return;
		}
		if (e.target.matches("[data-crm-set]") && !e.target.closest(".ch-iv-edit")) {
			hub.crmSave(e.target.dataset.fname, hub.readInput(e.target));
			return;
		}
		if (cl.contains("ch-act-filter")) {
			hub.actFilter = e.target.value;
			hub.renderContent();
		} else if (cl.contains("ch-status-filter")) {
			hub.statusFilter = e.target.value;
			hub.renderContent();
			hub.$(".ch-status-filter")?.focus();
		} else if (cl.contains("ch-top-n")) {
			hub.list.top = +e.target.value;
			const w = hub.$(".ch-rank-wrap");
			if (w) w.hidden = !hub.list.top;
			hub.loadCustomers(true);
		} else if (cl.contains("ch-f-sp") || cl.contains("ch-f-branch") || cl.contains("ch-f-age")) {
			const key = cl.contains("ch-f-sp") ? "sales_person" : cl.contains("ch-f-branch") ? "branch" : "age";
			hub.list[key] = e.target.value;
			hub.loadCustomers(true);
		} else if (cl.contains("ch-rank-by")) {
			hub.list.rank_by = e.target.value;
			hub.loadCustomers(true);
		}
	});
	document.addEventListener("keydown", (e) => {
		if (e.key === "Enter" && e.target.matches(".ch tr[data-open], .ch tr[data-customer], .ch [data-crm-open][tabindex], .ch [data-dropzone]")) e.target.click();
		const hub = e.target.closest && e.target.closest(".ch")?.parentElement?.__hub;
		if (!hub) return;
		if (e.key === "Escape" && hub.root.querySelector(".ch-modal") && !e.target.closest(".ch-iv-edit")) {
			const open = e.target.closest(".ch-ac") && e.target.closest(".ch-ac").querySelector(".ch-ac-list:not([hidden])");
			if (open) { open.hidden = true; return; }
			e.stopPropagation();
			hub.crmCloseModal();
		}
		if (e.target.classList.contains("ch-ac-in")) {
			const list = e.target.parentElement.querySelector(".ch-ac-list");
			const opts = [...list.querySelectorAll(".ch-ac-opt")];
			const i = opts.findIndex((o) => o.classList.contains("is-on"));
			if ((e.key === "ArrowDown" || e.key === "ArrowUp") && opts.length) {
				e.preventDefault();
				list.hidden = false;
				const n = (i + (e.key === "ArrowDown" ? 1 : -1) + opts.length) % opts.length;
				opts.forEach((o, k) => o.classList.toggle("is-on", k === n));
			} else if (e.key === "Enter" && !list.hidden && opts[i]) {
				e.preventDefault();
				hub.acPick(e.target, opts[i].dataset.ac);
			} else if (e.key === "Escape") {
				list.hidden = true;
			}
		}
	});
	document.addEventListener("focusin", (e) => {
		if (!e.target.classList || !e.target.classList.contains("ch-ac-in")) return;
		const hub = e.target.closest(".ch")?.parentElement?.__hub;
		if (hub) hub.acSearch(e.target);
	});
	document.addEventListener("focusout", (e) => {
		if (!e.target.classList || !e.target.classList.contains("ch-ac-in")) return;
		setTimeout(() => {
			const ac = e.target.closest(".ch-ac");
			if (ac && !ac.contains(document.activeElement)) {
				ac.querySelector(".ch-ac-list").hidden = true;
				const edit = ac.closest(".ch-iv-edit");
				const hub = ac.closest(".ch")?.parentElement?.__hub;
				if (edit && !edit._done && hub) { edit._done = true; hub.renderCrmSide(); }
			}
		}, 180);
	});

	global.CustomerHubUI = function (root, opts) {
		const hub = new CustomerHubUI(root, opts);
		root.__hub = hub;
		return hub;
	};
})(window);

}

/* ---------- Frappe Desk pages (shared by customer-hub and sales-crm) ---------- */
if (!window.mountCustomerHub) {
// CRM functions live in crm_hub_api.py next to customer_hub_api.py (same app folder)
const CUSTOMER_HUB_API = window.CUSTOMER_HUB_API;
const CRM_HUB_API = CUSTOMER_HUB_API.replace(/customer_hub_api$/, "crm_hub_api");


// Two Desk pages share this code:
//   customer-hub : customers, outstanding & ageing, customer 360   (app "customers")
//   sales-crm    : Today, Leads, Deals, Visits, Contacts           (app "crm")
const HUB_PAGES = { customers: { route: "customer-hub", title: "Customer Hub" }, crm: { route: "sales-crm", title: "Sales CRM" } };

window.mountCustomerHub = function (wrapper, app) {
	const P = HUB_PAGES[app];
	const base = `/app/${P.route}`;
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __(P.title), single_column: true });
	page.set_title(__(P.title));
	const root = $('<div class="customer-hub-root" style="margin-bottom:24px"></div>').appendTo(page.main)[0];
	// Never draw wider than what is visible: some Desk layouts are wider than the screen (e.g. the icon sidebar
	// isn't subtracted), which cut off the right edge. Measure and cap; flex parents also get min-width:0.
	for (let el = root.parentElement; el && el !== document.body; el = el.parentElement) el.style.minWidth = "0";
	const fit = () => {
		if (!root.isConnected || !root.offsetParent) return;
		root.style.maxWidth = "";
		const left = root.getBoundingClientRect().left;
		const avail = Math.floor(document.documentElement.clientWidth - Math.max(left, 0) - 16);
		if (avail > 300 && root.getBoundingClientRect().right > document.documentElement.clientWidth - 8) root.style.maxWidth = `${avail}px`;
	};
	wrapper._fitHub = fit;
	window.addEventListener("resize", () => requestAnimationFrame(fit));
	if (window.ResizeObserver) new ResizeObserver(() => requestAnimationFrame(fit)).observe(document.body);
	setTimeout(fit, 0);
	const setUrl = (path) => history.replaceState(history.state, "", path);
	const call = (method, args) => frappe.xcall(`${CUSTOMER_HUB_API}.${method}`, args);
	const crm = (method, args) => frappe.xcall(`${CRM_HUB_API}.${method}`, args);

	// Amounts as "1,234.56 SAR": avoids currency symbols the font can't draw (e.g. the new Saudi Riyal sign)
	const precision = cint(frappe.boot.sysdefaults.currency_precision) || 2;
	const fmtMoney = (v, cur) => `${format_number(flt(v), null, precision)}${cur ? " " + cur : ""}`;

	// Both views (Sales CRM and Customer Hub) live in this one page; the switch at the top flips between them.
	const views = (wrapper.views = {});
	const CRM_DT = { "CRM Lead": "lead", "CRM Deal": "deal", "Visit Plan": "visit", Contact: "contact" };
	const makeOpts = (viewApp) => ({
		app: viewApp,
		appSwitch: true,
		switchApp: (a) => switchTo(a),
		openCustomer: (c) => {
			const h = switchTo("customers");
			h.setCustomer(c);
			wrapper.picker && wrapper.picker.set_value(c);
		},
		openDesk: (doctype, name) => frappe.set_route("Form", doctype, name),
		api: {
			home: (team, part) => call("get_home", { team, part: part || "all" }),
			crmMyPlan: () => crm("crm_my_plan"),
			customers: (txt, start, opts) => call("get_customers", { txt, start, ...opts }),
			load: (customer, from_date, to_date) => call("get_customer_hub", { customer, from_date, to_date }),
			addComment: (customer, content, kind, mentions) =>
				call("add_comment", { customer, content, kind, mentions: JSON.stringify(mentions || []) }),
			mentionUsers: () => call("mention_users"),
			addFollowup: (reference_doctype, reference_name, date, description) =>
				call("add_followup", { reference_doctype, reference_name, date, description }),
			completeFollowup: (kind, name) => call("complete_followup", { kind, name }),
			// CRM
			crmMeta: () => crm("crm_meta"),
			crmList: (entity, o) => crm("crm_list", { entity, ...o }),
			crmGet: (entity, name) => crm("crm_get", { entity, name }),
			crmCreate: (entity, values) => crm("crm_create", { entity, values }),
			crmSet: (entity, name, field, value) => crm("crm_set", { entity, name, field, value }),
			crmAdd: (entity, name, kind, o) => crm("crm_add", { entity, name, kind, ...o, mentions: JSON.stringify((o && o.mentions) || []) }),
			crmTaskStatus: (name, status) => crm("crm_task_status", { name, status }),
			crmConvertLead: (name) => crm("crm_convert_lead", { name }),
			crmDealContact: (name, contact, action) => crm("crm_deal_contact", { name, contact, action }),
			crmDealToCustomer: (name) => crm("crm_deal_to_customer", { name }),
			crmSearch: (doctype, txt) => crm("crm_search", { doctype, txt }),
			crmSendEmail: (entity, name, o) =>
				crm("crm_send_email", { entity, name, ...o, attachments: JSON.stringify(o.attachments || []) }),
			crmRemoveAttachment: (entity, name, file) => crm("crm_remove_attachment", { entity, name, file }),
			crmPlanVisit: (entity, name, values) => crm("crm_plan_visit", { entity, name, values: JSON.stringify(values) }),
			crmAddToPlan: (entity, name, values) => crm("crm_add_to_plan", { entity, name, values: JSON.stringify(values) }),
			crmVisitLine: (plan, action, line, values) =>
				crm("crm_visit_line", { plan, action, line, values: JSON.stringify(values || {}) }),
			crmUpdateVisit: (entity, name, visit, action, values) =>
				crm("crm_update_visit", { entity, name, visit, action, values: JSON.stringify(values || {}) }),
			// standard Frappe upload: file is attached (private) to the record
			upload: async (doctype, docname, file) => {
				const fd = new FormData();
				fd.append("file", file, file.name);
				fd.append("doctype", doctype);
				fd.append("docname", docname);
				fd.append("is_private", 1);
				const r = await fetch("/api/method/upload_file", {
					method: "POST", body: fd, headers: { "X-Frappe-CSRF-Token": frappe.csrf_token, Accept: "application/json" },
				});
				const j = await r.json().catch(() => ({}));
				if (!r.ok || !j.message) {
					let msg = "";
					try { msg = JSON.parse(JSON.parse(j._server_messages)[0]).message; } catch (e) { msg = j.exception || r.statusText; }
					throw new Error(frappe.utils.html2text ? frappe.utils.html2text(msg || "") : msg);
				}
				return j.message;
			},
		},
		onCrmShown: (entity, name) => {
			wrapper.picker && wrapper.picker.set_value("");
			setUrl(`${base}/${entity}${name ? "/" + encodeURIComponent(name) : ""}`);
		},
		notify: (msg, color) => frappe.show_alert({ message: msg, indicator: color || "red" }),
		confirm: (msg) => new Promise((resolve) => frappe.confirm(msg, () => resolve(true), () => resolve(false))),
		mountCustomerPicker(slot, onChange) {
			const ctl = frappe.ui.form.make_control({
				parent: slot,
				df: {
					fieldtype: "Link",
					options: "Customer",
					fieldname: "customer",
					placeholder: __("Find a customer"),
					// only customers allowed for this user's Sales Person
					get_query: () => ({ query: `${CUSTOMER_HUB_API}.customer_query` }),
					change() {
						const v = ctl.get_value();
						if (v && (!wrapper.hub || v !== wrapper.hub.customer)) onChange(v);
					},
				},
				render_input: true,
			});
			ctl.$wrapper.find(".control-label, .help-box").remove();
			wrapper.picker = ctl;
		},
		setPicker: (v) => wrapper.picker && wrapper.picker.set_value(v),
		onHomeShown: () => {
			wrapper.picker && wrapper.picker.set_value("");
			setUrl(base);
		},
		onListShown: () => {
			wrapper.picker && wrapper.picker.set_value("");
			setUrl(base);
		},
		onCustomerShown: (c) => setUrl(`${base}/${encodeURIComponent(c)}`),
		openDoc: (doctype, name) => (CRM_DT[doctype] ? switchTo("crm").showCrmRecord(CRM_DT[doctype], name) : frappe.set_route("Form", doctype, name)),
		openUrl: (url) => window.open(url, "_blank", "noopener"),
		newDoc: (doctype, customer, values) => {
			if (doctype === "CRM Deal") {
				// new request for an existing customer: open the deal form in the CRM view, linked to this customer
				const c = views.customers && views.customers.data && views.customers.data.customer;
				const h = switchTo("crm");
				return (h._crmReady || Promise.resolve()).then(() =>
					h.crmNewForm("deal", { custom_customer: customer, organization: (c && c.customer_name) || customer }));
			}
			frappe.new_doc(doctype, values || (doctype === "Quotation" ? { quotation_to: "Customer", party_name: customer } : { customer }));
		},
		fmtMoney,
		fmtDate: (d) => frappe.datetime.str_to_user(d),
	});
	const switchTo = (a) => {
		if (!views[a]) {
			const r = document.createElement("div");
			r.className = "customer-hub-view";
			root.appendChild(r);
			views[a] = new CustomerHubUI(r, makeOpts(a));
		} else if (wrapper.active !== a) {
			const h = views[a];
			if (h.mode === "home" || h.mode === "list" || h.mode === "crm-list") setUrl(base);
		}
		Object.entries(views).forEach(([k, h]) => (h.root.hidden = k !== a));
		wrapper.active = a;
		wrapper.hub = views[a];
		page.set_title(__(HUB_PAGES[a].title));
		setTimeout(fit, 0);
		return views[a];
	};
	wrapper.switchTo = switchTo;
	switchTo(app);
};

window.showCustomerHub = function (wrapper, app) {
	const P = HUB_PAGES[app];
	// breadcrumb (otherwise some versions show "undefined")
	try {
		frappe.breadcrumbs.add({ type: "Custom", label: __(P.title), route: `/app/${P.route}` });
	} catch (e) {}
	if (!wrapper.switchTo) return;
	wrapper._fitHub && setTimeout(wrapper._fitHub, 50);
	const arg = frappe.get_route()[1] || (frappe.route_options && frappe.route_options.customer);
	const crmArg = ["lead", "deal", "contact", "visit"].includes(arg);
	if (!wrapper._shown) wrapper.switchTo(crmArg ? "crm" : arg ? "customers" : app);
	else if (crmArg) wrapper.switchTo("crm");
	else if (arg) wrapper.switchTo("customers");
	app = wrapper.active;
	const hub = wrapper.hub;
	frappe.route_options = null;
	const first = !wrapper._shown;
	wrapper._shown = true;
	if (!arg) {
		const start = app === "crm" ? "home" : "list";
		if (hub.mode !== start) start === "home" ? hub.showHome() : hub.showList();
		else if (!first) start === "home" ? hub.loadHome() : hub.loadCustomers(true); // coming back: refresh
		return;
	}
	if (app === "crm" && ["lead", "deal", "contact", "visit"].includes(arg)) {
		const name = frappe.get_route()[2];
		if (name) {
			if (!(hub.mode === "crm-record" && hub.crm && hub.crm.recName === name)) hub.showCrmRecord(arg, decodeURIComponent(name));
			else hub.loadCrmRecord();
		} else if (!(hub.mode === "crm-list" && hub.crm && hub.crm.entity === arg)) hub.showCrmList(arg);
		return;
	}
	if (arg === "customers") {
		if (hub.mode !== "list") hub.showList();
		return;
	}
	if (arg !== hub.customer) {
		hub.setCustomer(arg);
		wrapper.picker && wrapper.picker.set_value(arg);
	} else {
		hub.load(); // back from a document: refresh
	}
};

}

/* ---------- this file is the "sales-crm" page ---------- */
frappe.pages["sales-crm"].on_page_load = (wrapper) => mountCustomerHub(wrapper, "crm");
frappe.pages["sales-crm"].on_page_show = (wrapper) => showCustomerHub(wrapper, "crm");