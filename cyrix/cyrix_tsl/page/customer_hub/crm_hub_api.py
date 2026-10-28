# Put this file at: apps/YOUR_APP/YOUR_APP/crm_hub_api.py  (next to customer_hub_api.py)
"""CRM inside Customer Hub: leads, deals, contacts, notes, tasks and activity.

Works on the Frappe CRM app's own DocTypes (CRM Lead, CRM Deal, CRM Organization, CRM Note,
CRM Task) and the standard Contact, so records created here also appear in Frappe CRM and
the other way round. All reads and writes go through normal Frappe permissions.
"""

import json

import frappe
from frappe import _
from frappe.utils import cint, escape_html, flt, nowdate, strip_html

# ============================== Settings ==============================
ENTITIES = {
	"lead": {"doctype": "CRM Lead", "status_doctype": "CRM Lead Status", "owner": "lead_owner"},
	"deal": {"doctype": "CRM Deal", "status_doctype": "CRM Deal Status", "owner": "deal_owner"},
	"contact": {"doctype": "Contact", "status_doctype": None, "owner": None},
	"visit": {"doctype": "Visit Plan", "status_doctype": None, "owner": "sales_user",
	          "statuses": [["Draft", "gray"], ["Planned", "blue"], ["In Progress", "orange"],
	                       ["Completed", "green"], ["Cancelled", "red"]]},
}

# Options for the fields added by setup_crm_fields() (edit, then run it again)
LEAD_TYPES = ["Enquiry", "Tender", "Quotation Request", "Service Request", "Spare Parts", "Partnership", "Other"]
FOLLOWUP_TYPES = ["Call", "Email", "WhatsApp", "Meeting", "Visit", "Other"]
VISIT_TYPES = ["Site Visit", "Meeting", "Demo", "Delivery / Installation", "Service", "Other"]
LEAD_TYPE_FIELD = "custom_lead_type"

# ---- Requests from existing customers (deal = one request / unit) ----
REQUEST_TYPES = ["Repair", "Evaluation & Quotation", "New Unit", "Spare Parts", "Service Contract", "Other"]
# Next-step buttons shown on a deal, by Request Type: (button label, DocType). Missing DocTypes are skipped.
NEXT_STEPS = {
	"Repair": [("Work Order Data", "Work Order Data"), ("Quotation", "Quotation")],
	"Evaluation & Quotation": [("Work Order Data", "Work Order Data"), ("Quotation", "Quotation")],
	"New Unit": [("Quotation", "Quotation"), ("Supply Order Data", "Supply Order Data")],
	"Spare Parts": [("Quotation", "Quotation"), ("Supply Order Data", "Supply Order Data")],
	"Service Contract": [("Quotation", "Quotation")],
	"Other": [("Quotation", "Quotation")],
}
FOLLOWUP_TYPE_FIELD = "custom_followup_type"
VISIT_FIELDS = {"type": "custom_visit_type", "location": "custom_visit_location",
                "by": "custom_visit_assigned_to", "outcome": "custom_visit_outcome"}

# Short create forms: only these show first; everything else is under "More details".
QUICK_FIELDS = {
	"lead": ["first_name", "mobile_no", "organization", "custom_lead_type", "source"],
	"deal": ["custom_customer", "organization", "custom_request_type", "custom_unit_model", "custom_requirements",
	         "deal_value", "expected_closure_date"],
	"contact": ["first_name", "last_name", "mobile_no", "email_id", "company_name"],
	"visit": ["plan_date", "sales_user"],
}

# Fields per screen, in order. Fields that don't exist on your version are skipped.
FIELDS = {
	"lead": {
		"create": ["custom_lead_type", "salutation", "first_name", "last_name", "email", "mobile_no", "organization",
		           "website", "job_title", "industry", "source", "territory", "status", "lead_owner"],
		"panel": [["Details", ["custom_lead_type", "organization", "website", "territory", "industry", "job_title",
		                       "source", "lead_owner"]],
		          ["Person", ["salutation", "first_name", "last_name", "email", "mobile_no", "phone"]]],
		"list": ["custom_lead_type", "organization", "status", "mobile_no", "territory", "lead_owner", "source"],
	},
	"deal": {
		"create": ["custom_customer", "organization", "custom_request_type", "custom_unit_model", "custom_unit_serial",
		           "custom_requirements", "status", "deal_value", "currency", "probability", "expected_closure_date",
		           "deal_owner", "source", "next_step"],
		"panel": [["Request", ["custom_customer", "custom_request_type", "custom_unit_model", "custom_unit_serial",
		                       "custom_requirements"]],
		          ["Deal", ["organization", "custom_lead_type", "deal_value", "currency", "probability",
		                    "expected_closure_date", "next_step", "source", "deal_owner", "lost_reason"]],
		          ["Organization", ["website", "territory", "industry", "no_of_employees"]]],
		"list": ["custom_request_type", "status", "deal_value", "annual_revenue", "expected_closure_date", "territory", "deal_owner"],
	},
	"visit": {
		"create": ["plan_date", "sales_user", "territory", "status", "notes"],
		"panel": [["Plan", ["plan_date", "sales_user", "sales_person", "territory", "notes"]]],
		"list": ["plan_date", "sales_user", "territory", "status", "total_visits", "completed_visits"],
	},
	"contact": {
		"create": ["salutation", "first_name", "last_name", "email_id", "mobile_no", "company_name", "designation"],
		"panel": [["Contact", ["salutation", "first_name", "last_name", "email_id", "mobile_no", "phone",
		                       "company_name", "designation"]]],
		"list": ["company_name", "email_id", "mobile_no", "designation"],
	},
}
TITLE_FIELDS = {"lead": ["lead_name", "first_name", "last_name"], "deal": ["organization", "currency"],
                "visit": ["title"],
                "contact": ["full_name", "first_name", "last_name"]}
SEARCH_FIELDS = {"lead": ["lead_name", "organization", "email", "mobile_no"],
                 "visit": ["name", "title", "territory"],
                 "deal": ["organization", "name"], "contact": ["full_name", "email_id", "mobile_no", "company_name"]}
CALL_PREFIX = "Call: "

# Small lookup lists everyone may pick from in forms, even without read permission on them
LOOKUPS = {"CRM Territory", "CRM Industry", "CRM Lead Source", "CRM Lost Reason", "Salutation", "Currency",
           "Territory", "Industry Type", "Gender"}
# Frappe CRM lists that mirror an ERPNext list: (ERPNext DocType, field that holds the name on the CRM side).
# The ERPNext values are offered too, and the CRM record is created automatically when one is picked.
LINK_MIRRORS = {"CRM Territory": ("Territory", "territory_name"), "CRM Industry": ("Industry Type", "industry")}
SKIP_CHANGES = {"modified", "modified_by", "_assign", "_comments", "_liked_by", "idx", "lead_name", "full_name"}
# ======================================================================


STD_FIELDS = {"name", "owner", "creation", "modified", "modified_by", "docstatus", "parent", "parenttype"}


def _fields(doctype, fields):
	"""Keep only fields that exist on this site's version of the DocType ("field as alias" allowed)."""
	meta = frappe.get_meta(doctype)
	return [f for f in fields if f.split(" as ")[0].strip() in STD_FIELDS or meta.has_field(f.split(" as ")[0].strip())]


def _safe(fn, default):
	"""Run one part of a page; if it fails, log it and carry on with the rest."""
	try:
		return fn()
	except Exception:
		frappe.log_error(title="Customer Hub CRM", message=frappe.get_traceback())
		return default


def _first_line(text, n=140):
	return (strip_html(text or "").strip().split("\n")[0])[:n]


def _standalone(*candidates):
	"""First DocType in `candidates` that exists, is NOT a child table and links to a record
	(reference_doctype + reference_docname). Frappe CRM's notes are "FCRM Note"; ERPNext's
	"CRM Note" is a child table of Lead/Opportunity and must not be used here."""
	for dt in candidates:
		if not frappe.db.exists("DocType", dt):
			continue
		meta = frappe.get_meta(dt)
		if meta.istable or not (meta.has_field("reference_doctype") and meta.has_field("reference_docname")):
			continue
		return dt
	return None


def NOTE_DT():
	return _standalone("FCRM Note", "CRM Note")


def TASK_DT():
	return _standalone("CRM Task")


def _ent(entity):
	if entity not in ENTITIES:
		frappe.throw(_("Unknown section {0}").format(entity))
	e = ENTITIES[entity]
	if not frappe.db.exists("DocType", e["doctype"]):
		frappe.throw(_("{0} is not installed").format(e["doctype"]))
	return e


def _fullname(user, cache={}):
	if not user:
		return ""
	if user not in cache:
		cache[user] = frappe.utils.get_fullname(user) or user
	return cache[user]


def _all_fields(entity):
	f = FIELDS[entity]
	out = list(f["create"]) + list(f["list"]) + [x for _g, fs in f["panel"] for x in fs]
	return list(dict.fromkeys(out + ["status"]))


def _fdef(meta, f):
	df = meta.get_field(f)
	if not df:
		return None
	d = {"fieldname": f, "label": _(df.label or f), "fieldtype": df.fieldtype, "options": df.options,
	     "reqd": cint(df.reqd), "read_only": cint(df.read_only)}
	if df.fieldtype == "Select":
		d["options"] = [o for o in (df.options or "").split("\n")]
	if meta.name == "Contact" and f in ("email_id", "mobile_no", "phone"):
		d.update(fieldtype="Data", read_only=0)  # edited through the Contact's email / phone tables
	return d


def _val(v):
	if v is None:
		return None
	if hasattr(v, "isoformat"):
		return str(v)
	return v


def _statuses(entity):
	if ENTITIES[entity].get("statuses"):
		return [{"name": n, "color": c, "type": "Won" if n == "Completed" else "Lost" if n == "Cancelled" else "Open"}
		        for n, c in ENTITIES[entity]["statuses"]]
	sdt = ENTITIES[entity]["status_doctype"]
	if not sdt or not frappe.db.exists("DocType", sdt):
		return []
	m = frappe.get_meta(sdt)
	fields = ["name"] + [f for f in ("color", "position", "type") if m.has_field(f)]
	order = "position asc" if m.has_field("position") else "name asc"
	return [{"name": s.name, "color": s.get("color") or "gray",
	         "type": s.get("type") or ("Won" if s.name == "Won" else "Lost" if s.name == "Lost" else "Open")}
	        for s in frappe.get_all(sdt, fields=fields, order_by=order)]


# ----------------------------------------------------------------------
@frappe.whitelist()
def crm_meta():
	key = f"crm_hub:meta:{frappe.session.user}"
	cached = frappe.cache().get_value(key)
	if cached:
		return cached
	installed = bool(frappe.db.exists("DocType", "CRM Lead"))
	out = {"installed": installed, "entities": {}, "users": [], "me": frappe.session.user,
	       "currency": frappe.defaults.get_global_default("default_currency")}
	if installed:
		for entity, e in ENTITIES.items():
			if not frappe.db.exists("DocType", e["doctype"]):
				continue
			meta = frappe.get_meta(e["doctype"])
			defs = {}
			for f in _all_fields(entity):
				d = _fdef(meta, f)
				if d:
					defs[f] = d
			out["entities"][entity] = {
				"doctype": e["doctype"], "owner": e["owner"] if e["owner"] and meta.has_field(e["owner"]) else None,
				"fields": defs,
				"create": [f for f in FIELDS[entity]["create"] if f in defs],
				"quick": [f for f in QUICK_FIELDS.get(entity, []) if f in defs],
				"panel": [[g, [f for f in fs if f in defs]] for g, fs in FIELDS[entity]["panel"]],
				"list": [f for f in FIELDS[entity]["list"] if f in defs],
				"statuses": _statuses(entity),
				"can_create": frappe.has_permission(e["doctype"], "create"),
			}
		out["users"] = [{"name": u.name, "full_name": u.full_name or u.name} for u in frappe.get_all(
			"User", filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Guest"]},
			fields=["name", "full_name"], order_by="full_name asc")]
		out["has_notes"] = bool(NOTE_DT())
		out["has_tasks"] = bool(TASK_DT())
		out["has_visit_plans"] = bool(frappe.db.exists("DocType", "Visit Plan"))
		out["has_visits"] = _visits_ready() or out["has_visit_plans"]
		out["followup_types"] = FOLLOWUP_TYPES if TASK_DT() and frappe.get_meta(TASK_DT()).has_field(FOLLOWUP_TYPE_FIELD) else []
		out["visit_types"] = VISIT_TYPES
	frappe.cache().set_value(key, out, expires_in_sec=300)
	return out


@frappe.whitelist()
def crm_list(entity, txt=None, status=None, owner=None, start=0, page_len=50, lead_type=None):
	e = _ent(entity)
	dt, meta, user = e["doctype"], frappe.get_meta(e["doctype"]), frappe.session.user
	start, page_len = cint(start), min(cint(page_len) or 50, 500)
	fields = ["name", "modified", "creation"] + [f for f in TITLE_FIELDS[entity] + FIELDS[entity]["list"]
	                                             if meta.has_field(f)]
	fields = list(dict.fromkeys(fields))
	base = []
	if lead_type and meta.has_field(LEAD_TYPE_FIELD):
		base.append([LEAD_TYPE_FIELD, "=", lead_type])
	if owner == "mine":
		base.append([e["owner"] if e["owner"] and meta.has_field(e["owner"]) else "owner", "=", user])
	or_filters = None
	if txt:
		or_filters = [[f, "like", f"%{txt}%"] for f in SEARCH_FIELDS[entity] if f == "name" or meta.has_field(f)]

	# status counts (for the filter chips) before applying the status filter
	counts = {}
	if meta.has_field("status"):
		for r in frappe.get_list(dt, filters=base, or_filters=or_filters, fields=["status"], limit_page_length=5000):
			counts[r.status] = counts.get(r.status, 0) + 1
	filters = base + ([["status", "=", status]] if status else [])
	rows = frappe.get_list(dt, filters=filters, or_filters=or_filters, fields=fields,
	                       order_by="plan_date desc, modified desc" if entity == "visit" else "modified desc",
	                       limit_start=start, limit_page_length=page_len + 1)
	out = [{k: _val(v) for k, v in r.items()} for r in rows[:page_len]]
	nxt = _safe(lambda: _next_followups(dt, [r["name"] for r in out]), {}) if entity in ("lead", "deal") else {}
	for r in out:
		r["title"] = _title(entity, r)
		r["next_followup"] = nxt.get(r["name"])
	return {"rows": out, "has_more": len(rows) > page_len, "counts": counts, "total": sum(counts.values()) or len(out)}


def _title(entity, r):
	if entity == "lead":
		return r.get("lead_name") or " ".join(x for x in [r.get("first_name"), r.get("last_name")] if x) or r.get("name")
	if entity == "deal":
		return r.get("organization") or r.get("name")
	if entity == "visit":
		return r.get("title") or r.get("name")
	return r.get("full_name") or " ".join(x for x in [r.get("first_name"), r.get("last_name")] if x) or r.get("name")


@frappe.whitelist()
def crm_get(entity, name):
	e = _ent(entity)
	dt = e["doctype"]
	doc = frappe.get_doc(dt, name)
	doc.check_permission("read")
	meta = frappe.get_meta(dt)
	data = {f: _val(doc.get(f)) for f in _all_fields(entity) + TITLE_FIELDS[entity] if meta.has_field(f)}
	data["name"] = doc.name
	data["title"] = _title(entity, data)
	out = {
		"entity": entity, "doc": data, "can_write": bool(frappe.has_permission(dt, "write", doc)),
		"created": {"by": _fullname(doc.owner), "ts": str(doc.creation)},
		"activity": _safe(lambda: _timeline(dt, name, meta), []),
		"notes": _safe(lambda: _notes(dt, name), []), "tasks": _safe(lambda: _tasks(dt, name), []),
		"attachments": _safe(lambda: _attachments(dt, name), []),
		"visits": _safe(lambda: _plan_visits(dt, name) + _visits(dt, name), []) if entity in ("lead", "deal") else [],
	}
	out["can_unlock"] = _is_visit_manager()
	if entity == "visit":
		out["lines"] = [_line(r) for r in doc.items]
		out["line_meta"] = _line_meta()
		out["plan_locked"] = doc.status in CLOSED_PLAN and not out["can_unlock"]
	if entity == "lead":
		out["converted"] = cint(doc.get("converted"))
		out["deal"] = _safe(lambda: frappe.db.get_value("CRM Deal", {"lead": name}, "name")
		                    if frappe.get_meta("CRM Deal").has_field("lead") else None, None)
	elif entity == "deal":
		out["contacts"] = _safe(lambda: _deal_contacts(doc), [])
		out["lead"] = doc.get("lead")
		out["status_type"] = next((s["type"] for s in _statuses("deal") if s["name"] == doc.status), "Open")
		out["customer"] = doc.get("custom_customer") or _safe(lambda: frappe.db.get_value("Customer", {"customer_name": doc.organization}, "name")
		                        if doc.get("organization") and frappe.db.exists("DocType", "Customer") else None, None)
		out["next_steps"] = _safe(lambda: _next_steps(doc, out["customer"]), [])
	elif entity == "contact":
		pass
	out["emails"] = _safe(lambda: _email_suggestions(entity, doc, out), [])
	if entity == "contact":
		def linked_deals():
			if not frappe.db.exists("DocType", "CRM Contacts"):
				return []
			parents = frappe.get_all("CRM Contacts", filters={"contact": name, "parenttype": "CRM Deal"}, pluck="parent")
			if not parents:
				return []
			return [{**{k: _val(v) for k, v in d.items()}, "title": d.get("organization") or d.name}
			        for d in frappe.get_list("CRM Deal", filters={"name": ["in", parents]},
			                                 fields=_fields("CRM Deal", ["name", "organization", "status", "modified"]))]

		def linked_leads():
			if not doc.get("email_id") or not frappe.get_meta("CRM Lead").has_field("email"):
				return []
			return [{**{k: _val(v) for k, v in l.items()}, "title": l.get("lead_name") or l.name}
			        for l in frappe.get_list("CRM Lead", filters={"email": doc.email_id},
			                                 fields=_fields("CRM Lead", ["name", "lead_name", "status", "modified"]))]

		out["deals"] = _safe(linked_deals, [])
		out["leads"] = _safe(linked_leads, [])
	return out


def _deal_contacts(doc):
	out = []
	for row in doc.get("contacts") or []:
		c = frappe.db.get_value("Contact", row.contact, _fields("Contact", ["name", "full_name", "first_name", "last_name",
		                                                                    "email_id", "mobile_no"]), as_dict=True)
		if c:
			out.append({"name": c.name, "title": c.get("full_name") or " ".join(x for x in [c.get("first_name"), c.get("last_name")] if x) or c.name,
			            "email_id": c.email_id, "mobile_no": c.mobile_no, "is_primary": cint(row.get("is_primary"))})
	return out


def _notes(dt, name):
	ndt = NOTE_DT()
	if not ndt:
		return []
	rows = frappe.get_all(ndt, filters={"reference_doctype": dt, "reference_docname": name},
	                      fields=_fields(ndt, ["name", "title", "content", "owner", "modified"]),
	                      order_by="modified desc")
	return [{"name": n.name, "title": n.get("title") or _first_line(n.get("content")),
	         "content": strip_html(n.get("content") or ""), "by": _fullname(n.owner), "ts": str(n.modified)}
	        for n in rows]


def _tasks(dt, name):
	tdt = TASK_DT()
	if not tdt:
		return []
	meta = frappe.get_meta(tdt)
	rows = frappe.get_all(tdt, filters={"reference_doctype": dt, "reference_docname": name},
	                      fields=_fields(tdt, ["name", "title", "description", "status", "priority", "due_date",
	                                           "assigned_to", "modified", FOLLOWUP_TYPE_FIELD]),
	                      order_by=("due_date asc, " if meta.has_field("due_date") else "") + "modified desc")
	return [{"name": t.name, "title": t.get("title") or _first_line(t.get("description")) or t.name,
	         "description": strip_html(t.get("description") or ""), "status": t.get("status"),
	         "priority": t.get("priority"), "due_date": str(t.due_date)[:10] if t.get("due_date") else None,
	         "assigned_to": t.get("assigned_to"), "assigned_name": _fullname(t.get("assigned_to")),
	         "type": t.get(FOLLOWUP_TYPE_FIELD), "ts": str(t.modified)}
	        for t in rows]


def _timeline(dt, name, meta):
	ev = []
	for part in (_tl_versions, _tl_comments, _tl_notes_tasks, _tl_emails, _tl_files, _tl_visits):
		ev += _safe(lambda part=part: part(dt, name, meta), [])
	ev.sort(key=lambda x: x["ts"], reverse=True)
	return ev


def _tl_versions(dt, name, meta):
	ev = []
	user_fields = {d.fieldname for d in meta.fields if d.fieldtype == "Link" and d.options == "User"}
	for v in frappe.get_all("Version", filters={"ref_doctype": dt, "docname": name},
	                        fields=["data", "owner", "creation"], order_by="creation desc", limit_page_length=150):
		try:
			data = json.loads(v.data or "{}")
		except Exception:
			continue
		for ch in data.get("changed") or []:
			if len(ch) < 3 or ch[0] in SKIP_CHANGES:
				continue
			df = meta.get_field(ch[0])
			if not df or df.fieldtype in ("Table", "Text Editor", "HTML"):
				continue
			old, new = ch[1], ch[2]
			if ch[0] in user_fields:
				old, new = _fullname(old), _fullname(new)
			ev.append({"kind": "change", "ts": str(v.creation), "by": _fullname(v.owner), "field": _(df.label),
			           "from": "" if old in (None, "") else str(old), "to": "" if new in (None, "") else str(new)})
	return ev


def _tl_comments(dt, name, meta):
	ev = []
	for c in frappe.get_all("Comment", filters={"reference_doctype": dt, "reference_name": name, "comment_type": "Comment"},
	                        fields=["content", "owner", "creation"], order_by="creation desc", limit_page_length=200):
		text = strip_html(c.content or "")
		call = text.startswith(CALL_PREFIX)
		ev.append({"kind": "call" if call else "comment", "ts": str(c.creation), "by": _fullname(c.owner),
		           "content": text[len(CALL_PREFIX):] if call else text})
	return ev


def _tl_notes_tasks(dt, name, meta):
	ev = []
	for n in _notes(dt, name):
		ev.append({"kind": "note", "ts": n["ts"], "by": n["by"], "title": n["title"], "content": n["content"]})
	for t in _tasks(dt, name):
		ev.append({"kind": "task", "ts": t["ts"], "by": t["assigned_name"], "title": t["title"], "status": t["status"],
		           "due_date": t["due_date"], "type": t.get("type")})
	return ev


def _tl_emails(dt, name, meta):
	ev = []
	if frappe.has_permission("Communication", "read"):
		for m in frappe.get_list("Communication", filters={"reference_doctype": dt, "reference_name": name,
		                                                  "communication_type": "Communication"},
		                         fields=["subject", "sender", "recipients", "content", "sent_or_received", "creation"],
		                         order_by="creation desc", limit_page_length=100):
			ev.append({"kind": "email", "ts": str(m.creation), "by": m.sender, "subject": m.subject,
			           "recipients": m.recipients, "direction": m.sent_or_received,
			           "content": strip_html(m.content or "")[:500]})
	return ev


# ----------------------------------------------------------------------
def _ensure_organization(value):
	if not value or not frappe.db.exists("DocType", "CRM Organization"):
		return value
	if frappe.db.exists("CRM Organization", value):
		return value
	found = frappe.db.get_value("CRM Organization", {"organization_name": value}, "name")
	if found:
		return found
	return frappe.get_doc({"doctype": "CRM Organization", "organization_name": value}).insert().name


def _ensure_link(doctype, value):
	"""For mirrored lists (e.g. CRM Territory <- ERPNext Territory): create the CRM record if the user
	picked an ERPNext value that doesn't exist on the CRM side yet."""
	if not value or doctype not in LINK_MIRRORS or not frappe.db.exists("DocType", doctype):
		return value
	if frappe.db.exists(doctype, value):
		return value
	src, field = LINK_MIRRORS[doctype]
	if not (frappe.db.exists("DocType", src) and frappe.db.exists(src, value)):
		return value  # unknown value: let normal validation report it
	data = {"doctype": doctype}
	if frappe.get_meta(doctype).has_field(field):
		data[field] = value
	doc = frappe.get_doc(data)
	doc.flags.ignore_permissions = True  # only ever copies an existing ERPNext value
	doc.insert(set_name=value)
	return doc.name


def _ensure_links(meta, data):
	for f, v in list(data.items()):
		df = meta.get_field(f)
		if df and df.fieldtype == "Link" and v:
			data[f] = _ensure_link(df.options, v)
	return data


@frappe.whitelist()
def crm_create(entity, values):
	e = _ent(entity)
	values = frappe.parse_json(values) or {}
	if entity == "contact":
		return _create_contact(values)
	dt, meta = e["doctype"], frappe.get_meta(e["doctype"])
	allowed = set(FIELDS[entity]["create"]) | {"status"}
	data = {k: v for k, v in values.items() if k in allowed and meta.has_field(k) and v not in (None, "")}
	if e["owner"] and meta.has_field(e["owner"]) and not data.get(e["owner"]):
		data[e["owner"]] = frappe.session.user
	if entity == "deal" and data.get("custom_customer") and not data.get("organization"):
		data["organization"] = frappe.db.get_value("Customer", data["custom_customer"], "customer_name")
	if entity == "deal" and data.get("organization"):
		data["organization"] = _ensure_organization(data["organization"])
	data = _ensure_links(meta, data)
	doc = frappe.get_doc({"doctype": dt, **data})
	if entity == "deal" and values.get("contact") and meta.has_field("contacts"):
		doc.append("contacts", {"contact": values["contact"], "is_primary": 1})
	doc.insert()
	return doc.name


def _create_contact(values):
	c = frappe.new_doc("Contact")
	for f in ("salutation", "first_name", "last_name", "company_name", "designation"):
		if values.get(f):
			c.set(f, values[f])
	if not c.first_name:
		frappe.throw(_("First name is required"))
	if values.get("email_id"):
		c.append("email_ids", {"email_id": values["email_id"], "is_primary": 1})
	if values.get("mobile_no"):
		c.append("phone_nos", {"phone": values["mobile_no"], "is_primary_mobile_no": 1})
	c.insert()
	return c.name


def _set_contact_channel(doc, field, value):
	if field == "email_id":
		row = next((r for r in doc.email_ids if r.is_primary), None) or (doc.email_ids[0] if doc.email_ids else None)
		if value and row:
			row.email_id = value
			row.is_primary = 1
		elif value:
			doc.append("email_ids", {"email_id": value, "is_primary": 1})
		elif row:
			doc.remove(row)
		doc.email_id = value or None
	else:
		flag = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		row = next((r for r in doc.phone_nos if r.get(flag)), None)
		if value and row:
			row.phone = value
		elif value:
			doc.append("phone_nos", {"phone": value, flag: 1})
		elif row:
			doc.remove(row)
		doc.set(field, value or None)


@frappe.whitelist()
def crm_set(entity, name, field, value=None):
	"""Change one field (inline edit, status, owner)."""
	e = _ent(entity)
	doc = frappe.get_doc(e["doctype"], name)
	doc.check_permission("write")
	if field not in _all_fields(entity):
		frappe.throw(_("Field {0} can't be changed here").format(field))
	if entity == "contact" and field in ("email_id", "mobile_no", "phone"):
		_set_contact_channel(doc, field, value)
	else:
		if not doc.meta.has_field(field):
			frappe.throw(_("Field {0} not found").format(field))
		if entity == "deal" and field == "organization" and value:
			value = _ensure_organization(value)
		elif value:
			df = doc.meta.get_field(field)
			if df.fieldtype == "Link":
				value = _ensure_link(df.options, value)
		doc.set(field, value if value not in ("",) else None)
	doc.save()
	return crm_get(entity, name)


@frappe.whitelist()
def crm_convert_lead(name):
	"""Convert a lead to a deal using Frappe CRM's own logic (creates contact + organization)."""
	frappe.has_permission("CRM Lead", "write", name, throw=True)
	try:
		fn = frappe.get_attr("crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal")
	except Exception:
		fn = None
	if fn:
		deal = fn(lead=name)
	else:
		lead = frappe.get_doc("CRM Lead", name)
		contact = lead.create_contact(False)
		org = lead.create_organization()
		deal = lead.create_deal(contact, org)
	_safe(lambda: _copy_lead_type(name, deal), None)
	return deal


def _copy_lead_type(lead, deal):
	if not (deal and frappe.get_meta("CRM Lead").has_field(LEAD_TYPE_FIELD)
	        and frappe.get_meta("CRM Deal").has_field(LEAD_TYPE_FIELD)):
		return
	v = frappe.db.get_value("CRM Lead", lead, LEAD_TYPE_FIELD)
	if v:
		frappe.db.set_value("CRM Deal", deal, LEAD_TYPE_FIELD, v)


@frappe.whitelist()
def crm_deal_contact(name, contact, action="add"):
	doc = frappe.get_doc("CRM Deal", name)
	doc.check_permission("write")
	if action == "add":
		if not any(r.contact == contact for r in doc.contacts):
			doc.append("contacts", {"contact": contact, "is_primary": 0 if doc.contacts else 1})
	elif action == "primary":
		for r in doc.contacts:
			r.is_primary = 1 if r.contact == contact else 0
	else:
		doc.contacts = [r for r in doc.contacts if r.contact != contact]
	doc.save()
	return crm_get("deal", name)


@frappe.whitelist()
def crm_deal_to_customer(name):
	"""Create (or find) the ERPNext Customer for a won deal."""
	deal = frappe.get_doc("CRM Deal", name)
	deal.check_permission("read")
	cname = deal.organization or name
	existing = frappe.db.get_value("Customer", {"customer_name": cname}, "name")
	if existing:
		return existing
	frappe.has_permission("Customer", "create", throw=True)

	def default(doctype, settings_field):
		v = frappe.db.get_single_value("Selling Settings", settings_field)
		return v or frappe.db.get_value(doctype, {"is_group": 0}, "name")

	cust = frappe.get_doc({
		"doctype": "Customer", "customer_name": cname, "customer_type": "Company",
		"customer_group": default("Customer Group", "customer_group"),
		"territory": deal.get("territory") if deal.get("territory") and frappe.db.exists("Territory", deal.territory)
		else default("Territory", "territory"),
		"website": deal.get("website"),
	})
	# give the customer the deal owner's Sales Person, so it shows up in their hub
	owner = deal.get("deal_owner")
	if owner:
		emp = frappe.db.get_value("Employee", {"user_id": owner}, "name")
		sp = frappe.db.get_value("Sales Person", {"employee": emp}, "name") if emp else None
		if sp:
			cust.append("sales_team", {"sales_person": sp, "allocated_percentage": 100})
	cust.insert()
	return cust.name


@frappe.whitelist()
def mention_html(text, mentions=None):
	"""Plain text -> HTML. Every "@Full Name" of a picked user becomes a Frappe mention, which notifies
	that user (bell notification; Frappe CRM also sends its own mention alert)."""
	html = escape_html(text or "").replace("\n", "<br>")
	for uid in dict.fromkeys(frappe.parse_json(mentions) or []):
		if not uid or not frappe.db.exists("User", uid):
			continue
		full = frappe.utils.get_fullname(uid) or uid
		token = "@" + escape_html(full)
		span = (f'<span class="mention" data-id="{escape_html(uid)}" data-value="{escape_html(full)}" '
		        f'data-denotation-char="@">@{escape_html(full)}</span>')
		html = html.replace(token, span)
	return f"<p>{html}</p>"


def _notify_mentions(dt, name, html):
	"""Comments notify by themselves; notes don't, so do it here."""
	try:
		from frappe.desk.notifications import notify_mentions
		notify_mentions(dt, name, html)
	except Exception:
		frappe.log_error(title="Customer Hub mention", message=frappe.get_traceback())


@frappe.whitelist()
def crm_add(entity, name, kind, content=None, title=None, due_date=None, priority=None, assigned_to=None,
            followup_type=None, mentions=None):
	"""kind: comment | call | note | task"""
	e = _ent(entity)
	dt = e["doctype"]
	frappe.has_permission(dt, "read", name, throw=True)
	content = (content or "").strip()
	html = "<p>" + escape_html(content).replace("\n", "<br>") + "</p>" if content else ""
	if kind in ("comment", "call"):
		if not content:
			frappe.throw(_("Write something first"))
		text = (CALL_PREFIX if kind == "call" else "") + content
		return frappe.get_doc(dt, name).add_comment("Comment", text=mention_html(text, mentions)).name
	if kind == "note":
		if not (title or content):
			frappe.throw(_("Write something first"))
		ndt = NOTE_DT()
		if mentions and content:
			html = mention_html(content, mentions)
		if ndt:
			data = {"title": title or content.split("\n")[0][:140], "content": html,
			        "reference_doctype": dt, "reference_docname": name}
			meta = frappe.get_meta(ndt)
			if not meta.has_field("title") and title:
				data["content"] = f"<p><b>{escape_html(title)}</b></p>" + html
			note = frappe.get_doc({"doctype": ndt, **{k: v for k, v in data.items() if meta.has_field(k)}}).insert()
			if mentions:
				_notify_mentions(dt, name, data["content"])
			return note.name
		return frappe.get_doc(dt, name).add_comment("Comment", text=html).name
	if kind == "task":
		if not title:
			frappe.throw(_("Give the task a title"))
		tdt = TASK_DT()
		if tdt:
			data = {"title": title, "description": html, "status": "Todo", "priority": priority or "Medium",
			        "due_date": due_date or None, "assigned_to": assigned_to or frappe.session.user,
			        "reference_doctype": dt, "reference_docname": name, FOLLOWUP_TYPE_FIELD: followup_type or None}
			meta = frappe.get_meta(tdt)
			return frappe.get_doc({"doctype": tdt, **{k: v for k, v in data.items() if meta.has_field(k)}}).insert().name
		return frappe.get_doc({"doctype": "ToDo", "description": escape_html(title), "date": due_date or None,
		                       "allocated_to": assigned_to or frappe.session.user, "reference_type": dt,
		                       "reference_name": name}).insert().name
	frappe.throw(_("Unknown type"))


@frappe.whitelist()
def crm_task_status(name, status):
	t = frappe.get_doc("CRM Task", name)
	t.status = status
	t.save()
	return t.name


@frappe.whitelist()
def crm_search(doctype, txt=""):
	"""Search for Link fields in forms."""
	if not frappe.db.exists("DocType", doctype):
		return []
	if doctype == "User":
		return [{"value": u.name, "label": u.full_name or u.name} for u in frappe.get_all(
			"User", filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Guest"]},
			or_filters=[["name", "like", f"%{txt}%"], ["full_name", "like", f"%{txt}%"]],
			fields=["name", "full_name"], limit_page_length=10)]
	meta = frappe.get_meta(doctype)
	title = meta.title_field if meta.title_field and meta.has_field(meta.title_field) else None
	if doctype == "Contact":
		title = "full_name"
	fields = ["name"] + ([f"{title} as label"] if title else [])
	or_filters = [["name", "like", f"%{txt}%"]] + ([[title, "like", f"%{txt}%"]] if title else [])
	if doctype == "Contact":
		or_filters += [["email_id", "like", f"%{txt}%"], ["company_name", "like", f"%{txt}%"]]
		fields += ["email_id", "company_name"]
	try:
		rows = frappe.get_list(doctype, or_filters=or_filters, fields=fields, order_by="modified desc",
		                       limit_page_length=10)
	except frappe.PermissionError:
		if doctype not in LOOKUPS:
			return []
		rows = frappe.get_all(doctype, or_filters=or_filters, fields=fields, order_by="modified desc",
		                      limit_page_length=10)
	out = []
	for r in rows:
		label = r.get("label") or r.name
		sub = " · ".join(x for x in [r.get("company_name"), r.get("email_id")] if x)
		out.append({"value": r.name, "label": label, "sub": sub})

	# mirrored list: also offer the ERPNext values (e.g. your ERPNext Territories)
	if doctype in LINK_MIRRORS:
		src = LINK_MIRRORS[doctype][0]
		if frappe.db.exists("DocType", src):
			have = {o["value"].lower() for o in out}
			for n in frappe.get_all(src, filters={"name": ["like", f"%{txt}%"]}, pluck="name", order_by="name asc", limit_page_length=20):
				if n.lower() not in have and not n.startswith("All "):
					out.append({"value": n, "label": n, "sub": _("from ERPNext")})
					have.add(n.lower())
	return out[:20]



# ============================== Email & attachments ==============================

def _attachments(dt, name):
	rows = frappe.get_all("File", filters={"attached_to_doctype": dt, "attached_to_name": name, "is_folder": 0},
	                      fields=["name", "file_name", "file_url", "file_size", "is_private", "owner", "creation"],
	                      order_by="creation desc")
	return [{"name": f.name, "file_name": f.file_name or (f.file_url or "").split("/")[-1], "file_url": f.file_url,
	         "file_size": f.file_size or 0, "is_private": f.is_private, "by": _fullname(f.owner),
	         "ts": str(f.creation)} for f in rows]


def _tl_files(dt, name, meta):
	return [{"kind": "file", "ts": f["ts"], "by": f["by"], "file_name": f["file_name"], "file_url": f["file_url"]}
	        for f in _attachments(dt, name)]


def _email_suggestions(entity, doc, out):
	emails = []
	if entity == "lead" and doc.get("email"):
		emails.append({"email": doc.email, "label": out["doc"].get("title")})
	if entity == "contact":
		for r in doc.get("email_ids") or []:
			emails.append({"email": r.email_id, "label": out["doc"].get("title")})
	if entity == "deal":
		for c in out.get("contacts") or []:
			if c.get("email_id"):
				emails.append({"email": c["email_id"], "label": c["title"]})
		if doc.get("email"):
			emails.append({"email": doc.email, "label": doc.get("organization")})
	seen, uniq = set(), []
	for e in emails:
		if e["email"] and e["email"].lower() not in seen:
			seen.add(e["email"].lower())
			uniq.append(e)
	return uniq


@frappe.whitelist()
def crm_send_email(entity, name, recipients, subject, content, cc=None, bcc=None, attachments=None):
	"""Send an email from a lead / deal / contact. It is saved as a Communication linked to the record,
	so it shows in the hub timeline, in Frappe CRM and on the Desk form. Replies to it come back there too."""
	e = _ent(entity)
	dt = e["doctype"]
	frappe.has_permission(dt, "read", name, throw=True)
	if not (recipients or "").strip():
		frappe.throw(_("Add at least one recipient"))
	if not (subject or "").strip():
		frappe.throw(_("Add a subject"))
	# only files that are attached to this record can be sent from here
	wanted = frappe.parse_json(attachments) or []
	allowed = set(frappe.get_all("File", filters={"attached_to_doctype": dt, "attached_to_name": name}, pluck="name"))
	files = [f for f in wanted if f in allowed]
	html = "".join(f"<p>{escape_html(line) or '&nbsp;'}</p>" for line in (content or "").split("\n"))
	from frappe.core.doctype.communication.email import make

	res = make(doctype=dt, name=name, subject=subject.strip(), content=html, sent_or_received="Sent",
	           recipients=recipients, cc=cc or None, bcc=bcc or None, send_email=True, attachments=files)
	return res.get("name") if isinstance(res, dict) else res


@frappe.whitelist()
def crm_remove_attachment(entity, name, file):
	e = _ent(entity)
	dt = e["doctype"]
	frappe.get_doc(dt, name).check_permission("write")
	f = frappe.get_doc("File", file)
	if f.attached_to_doctype != dt or f.attached_to_name != name:
		frappe.throw(_("This file is not attached to this record"))
	frappe.delete_doc("File", f.name, ignore_permissions=True)  # checked above: user can edit the record
	return _attachments(dt, name)



# ============================== Follow-ups & visits ==============================

def _next_followups(dt, names):
	"""{record: {date, title, type}} = earliest open follow-up (CRM Task) per record."""
	tdt = TASK_DT()
	if not tdt or not names:
		return {}
	fields = _fields(tdt, ["reference_docname", "title", "due_date", FOLLOWUP_TYPE_FIELD])
	rows = frappe.get_all(tdt, filters={"reference_doctype": dt, "reference_docname": ["in", names],
	                                    "status": ["not in", ["Done", "Canceled"]]},
	                      fields=fields, order_by="due_date asc", limit_page_length=0)
	out = {}
	for r in rows:
		if r.reference_docname not in out:
			out[r.reference_docname] = {"date": str(r.due_date)[:10] if r.get("due_date") else None,
			                            "title": r.get("title"), "type": r.get(FOLLOWUP_TYPE_FIELD)}
	return out


def _visits_ready():
	return frappe.db.exists("DocType", "Event") and frappe.get_meta("Event").has_field(VISIT_FIELDS["type"])


def _visit_row(e):
	return {
		"name": e.name, "subject": e.subject, "starts_on": str(e.starts_on) if e.starts_on else None,
		"ends_on": str(e.ends_on) if e.get("ends_on") else None, "status": e.status,
		"type": e.get(VISIT_FIELDS["type"]), "location": e.get(VISIT_FIELDS["location"]),
		"by": e.get(VISIT_FIELDS["by"]) or e.owner, "by_name": _fullname(e.get(VISIT_FIELDS["by"]) or e.owner),
		"outcome": e.get(VISIT_FIELDS["outcome"]), "notes": strip_html(e.get("description") or ""),
		"ts": str(e.modified),
	}


def _visits(dt, name):
	if not _visits_ready():
		return []
	parents = frappe.get_all("Event Participants", filters={"reference_doctype": dt, "reference_docname": name,
	                                                         "parenttype": "Event"}, pluck="parent")
	if not parents:
		return []
	fields = _fields("Event", ["name", "subject", "starts_on", "ends_on", "status", "description", "owner", "modified"]
	                 + list(VISIT_FIELDS.values()))
	rows = frappe.get_all("Event", filters={"name": ["in", parents], VISIT_FIELDS["type"]: ["is", "set"]},
	                      fields=fields, order_by="starts_on desc")
	return [_visit_row(e) for e in rows]


def _tl_visits(dt, name, meta):
	ev = []
	for v in _visits(dt, name):
		ev.append({"kind": "visit", "ts": v["ts"], "by": v["by_name"], "visit": v})
	return ev


def _visit_times(date, time=None, minutes=60):
	from frappe.utils import add_to_date, get_datetime
	if not date:
		frappe.throw(_("Pick a date for the visit"))
	t = (time or "09:00").strip()
	if len(t) == 5:
		t += ":00"
	start = get_datetime(f"{date} {t}")
	return start, add_to_date(start, minutes=cint(minutes) or 60)


@frappe.whitelist()
def crm_plan_visit(entity, name, values):
	"""Plan a visit for a lead or deal. Saved as a calendar Event linked to the record."""
	if not _visits_ready():
		frappe.throw(_("Visits are not set up yet. Run setup_crm_fields once (see the instructions)."))
	e = _ent(entity)
	dt = e["doctype"]
	frappe.has_permission(dt, "read", name, throw=True)
	v = frappe.parse_json(values) or {}
	if not v.get("date"):
		frappe.throw(_("Pick a date for the visit"))
	start, end = _visit_times(v["date"], v.get("time"), v.get("minutes"))
	title = frappe.db.get_value(dt, name, "lead_name" if entity == "lead" else "organization") or name
	ev = frappe.get_doc({
		"doctype": "Event",
		"subject": (v.get("purpose") or "").strip() or f"{v.get('type') or 'Visit'}: {title}",
		"starts_on": start, "ends_on": end, "event_category": "Meeting", "event_type": "Public", "status": "Open",
		"description": escape_html(v.get("notes") or "").replace("\n", "<br>"),
		VISIT_FIELDS["type"]: v.get("type") or VISIT_TYPES[0],
		VISIT_FIELDS["location"]: v.get("location") or None,
		VISIT_FIELDS["by"]: v.get("by") or frappe.session.user,
		"event_participants": [{"reference_doctype": dt, "reference_docname": name}],
	})
	ev.insert()
	return _visits(dt, name)


@frappe.whitelist()
def crm_update_visit(entity, name, visit, action, values=None):
	"""action: complete (with outcome) | cancel | reschedule (date/time/minutes) | reopen"""
	e = _ent(entity)
	dt = e["doctype"]
	frappe.has_permission(dt, "read", name, throw=True)
	if frappe.db.exists("DocType", "Visit Plan Item") and frappe.db.exists("Visit Plan Item", visit):
		_update_plan_line(dt, name, visit, action, frappe.parse_json(values) or {})
		return _plan_visits(dt, name) + _visits(dt, name)
	if visit not in frappe.get_all("Event Participants", filters={"reference_doctype": dt, "reference_docname": name},
	                               pluck="parent"):
		frappe.throw(_("This visit is not linked to this record"))
	v = frappe.parse_json(values) or {}
	ev = frappe.get_doc("Event", visit)
	if action == "complete":
		ev.status = "Completed"
		ev.set(VISIT_FIELDS["outcome"], (v.get("outcome") or "").strip() or None)
	elif action == "cancel":
		ev.status = "Cancelled"
	elif action == "reopen":
		ev.status = "Open"
	elif action == "reschedule":
		start, end = _visit_times(v.get("date"), v.get("time"), v.get("minutes") or 60)
		ev.starts_on, ev.ends_on, ev.status = start, end, "Open"
	else:
		frappe.throw(_("Unknown action"))
	ev.save()
	return _visits(dt, name)


def setup_crm_fields():
	"""One-time: add Lead Type, Follow-up Type and Visit fields.
	Run:  bench --site <site> execute YOUR_APP.crm_hub_api.setup_crm_fields
	Safe to run again (e.g. after changing LEAD_TYPES / FOLLOWUP_TYPES / VISIT_TYPES)."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	opts = lambda xs: "\n" + "\n".join(xs)
	fields = {
		"Event": [
			{"fieldname": VISIT_FIELDS["type"], "label": "Visit Type", "fieldtype": "Select",
			 "options": opts(VISIT_TYPES), "insert_after": "event_category"},
			{"fieldname": VISIT_FIELDS["location"], "label": "Visit Location", "fieldtype": "Data",
			 "insert_after": VISIT_FIELDS["type"]},
			{"fieldname": VISIT_FIELDS["by"], "label": "Visit By", "fieldtype": "Link", "options": "User",
			 "insert_after": VISIT_FIELDS["location"]},
			{"fieldname": VISIT_FIELDS["outcome"], "label": "Visit Outcome", "fieldtype": "Small Text",
			 "insert_after": "description"},
		],
	}
	if frappe.db.exists("DocType", "CRM Lead"):
		fields["CRM Lead"] = [{"fieldname": LEAD_TYPE_FIELD, "label": "Lead Type", "fieldtype": "Select",
		                       "options": opts(LEAD_TYPES), "insert_after": "status", "in_standard_filter": 1}]
	if frappe.db.exists("DocType", "CRM Deal"):
		fields["CRM Deal"] = [
			{"fieldname": LEAD_TYPE_FIELD, "label": "Lead Type", "fieldtype": "Select",
			 "options": opts(LEAD_TYPES), "insert_after": "status", "in_standard_filter": 1},
			{"fieldname": "custom_customer", "label": "Customer", "fieldtype": "Link", "options": "Customer",
			 "insert_after": LEAD_TYPE_FIELD, "in_standard_filter": 1},
			{"fieldname": "custom_request_type", "label": "Request Type", "fieldtype": "Select",
			 "options": opts(REQUEST_TYPES), "insert_after": "custom_customer", "in_standard_filter": 1},
			{"fieldname": "custom_unit_model", "label": "Unit / Model", "fieldtype": "Data", "insert_after": "custom_request_type"},
			{"fieldname": "custom_unit_serial", "label": "Serial No.", "fieldtype": "Data", "insert_after": "custom_unit_model"},
			{"fieldname": "custom_requirements", "label": "Requirements", "fieldtype": "Small Text",
			 "insert_after": "custom_unit_serial"},
		]
	if TASK_DT():
		fields[TASK_DT()] = [{"fieldname": FOLLOWUP_TYPE_FIELD, "label": "Follow-up Type", "fieldtype": "Select",
		                      "options": opts(FOLLOWUP_TYPES), "insert_after": "title"}]
	create_custom_fields(fields, update=True)
	frappe.db.commit()
	frappe.clear_cache()
	for dt, fs in fields.items():
		print("ok:", dt, [f["fieldname"] for f in fs])



# ============================== Visit Plans (separate section) ==============================
LINE_FIELDS = ["visit_time", "party_type", "party", "visit_type", "location", "purpose", "status", "outcome",
               "next_followup_date"]
PLAN_EDIT_FIELDS = ["visit_time", "party_type", "party", "visit_type", "location", "purpose"]  # editable while Planned
FINISHED_LINE = {"Visited", "Not Visited", "Rescheduled", "Cancelled"}
CLOSED_PLAN = {"Completed", "Cancelled"}
VISIT_MANAGERS = {"System Manager", "Sales Manager"}  # only these can reopen / change finished visits


def _is_visit_manager():
	return bool(VISIT_MANAGERS & set(frappe.get_roles()))


def _locked(row, plan):
	return (row.status in FINISHED_LINE or plan.status in CLOSED_PLAN) and not _is_visit_manager()


def _hhmm(v):
	if v is None or v == "":
		return ""
	if hasattr(v, "total_seconds"):
		secs = int(v.total_seconds())
		return f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}"
	return str(v)[:5]


def _line(r):
	return {"name": r.name, "idx": r.idx, "visit_time": _hhmm(r.visit_time), "party_type": r.party_type, "party": r.party,
	        "party_name": r.party_name, "visit_type": r.visit_type, "location": r.location, "purpose": r.purpose,
	        "status": r.status, "outcome": r.outcome,
	        "next_followup_date": str(r.next_followup_date) if r.next_followup_date else None,
	        "followup_created": cint(r.get("followup_created"))}


def _line_meta():
	m = frappe.get_meta("Visit Plan Item")
	opts = lambda f: [o for o in (m.get_field(f).options or "").split("\n") if o] if m.get_field(f) else []
	return {"party_types": opts("party_type"), "visit_types": opts("visit_type"), "statuses": opts("status")}


@frappe.whitelist()
def crm_visit_line(plan, action, line=None, values=None):
	"""Visit lines of a Visit Plan.
	add | update (only while Planned) | finish (status Visited / Not Visited / Cancelled + outcome, then locked)
	| reopen (managers only) | remove (only while Planned)."""
	doc = frappe.get_doc("Visit Plan", plan)
	doc.check_permission("write")
	v = frappe.parse_json(values) or {}
	manager = _is_visit_manager()
	row = next((r for r in doc.items if r.name == line), None) if line else None
	if line and not row:
		frappe.throw(_("Visit line not found. Reload the page."))

	if action == "add":
		if doc.status in CLOSED_PLAN and not manager:
			frappe.throw(_("This plan is {0}. Ask a manager to reopen it.").format(_(doc.status)))
		data = {k: (v[k] if v[k] != "" else None) for k in PLAN_EDIT_FIELDS if k in v}
		data.setdefault("party_type", "CRM Lead")
		data["status"] = "Planned"
		doc.append("items", data)
	elif action == "update":
		if _locked(row, doc):
			frappe.throw(_("This visit is {0} and locked. Ask a manager to reopen it.").format(_(row.status)))
		fields = LINE_FIELDS if manager else PLAN_EDIT_FIELDS
		data = {k: (v[k] if v[k] != "" else None) for k in fields if k in v}
		if "party_type" in data and data["party_type"] != row.party_type and "party" not in data:
			data["party"] = None
		row.update(data)
	elif action == "finish":
		if _locked(row, doc):
			frappe.throw(_("This visit is already {0}.").format(_(row.status)))
		status = v.get("status")
		if status not in ("Visited", "Not Visited", "Cancelled"):
			frappe.throw(_("Choose Visited, Not Visited or Cancelled"))
		outcome = (v.get("outcome") or "").strip()
		if status in ("Visited", "Not Visited") and not outcome:
			frappe.throw(_("Write the outcome (or the reason it didn't happen)"))
		if not row.party:
			frappe.throw(_("Pick who was visited before completing the visit"))
		row.status, row.outcome = status, outcome or row.outcome
		if v.get("next_followup_date"):
			row.next_followup_date = v["next_followup_date"]
	elif action == "reopen":
		if not manager:
			frappe.throw(_("Only a Sales Manager can reopen a finished visit"), frappe.PermissionError)
		row.status = "Planned"
		if doc.status in CLOSED_PLAN:
			doc.status = "In Progress"
	elif action == "remove":
		if _locked(row, doc):
			frappe.throw(_("Finished visits can't be removed. Ask a manager."))
		doc.items = [r for r in doc.items if r.name != line]
		for i, r in enumerate(doc.items, 1):
			r.idx = i
	else:
		frappe.throw(_("Unknown action"))
	doc.flags.hub_manager_override = manager
	doc.save()
	return crm_get("visit", plan)


def _plan_for(user, date, create=True, territory=None):
	found = frappe.get_all("Visit Plan", filters={"sales_user": user, "plan_date": date,
	                                               "status": ["in", ["Draft", "Planned", "In Progress"]]},
	                       pluck="name", order_by="creation asc", limit_page_length=1)
	if found:
		return frappe.get_doc("Visit Plan", found[0])
	if not create:
		return None
	return frappe.get_doc({"doctype": "Visit Plan", "plan_date": date, "sales_user": user, "status": "Planned",
	                       "territory": territory if territory and frappe.db.exists("Territory", territory) else None})


@frappe.whitelist()
def crm_add_to_plan(entity, name, values):
	"""From a lead / deal page: add a visit line to that person's plan for the day (creates the plan if needed)."""
	e = _ent(entity)
	dt = e["doctype"]
	frappe.has_permission(dt, "read", name, throw=True)
	v = frappe.parse_json(values) or {}
	if not v.get("date"):
		frappe.throw(_("Pick a date for the visit"))
	user = v.get("by") or frappe.session.user
	plan = _plan_for(user, v["date"], territory=frappe.db.get_value(dt, name, "territory") if frappe.get_meta(dt).has_field("territory") else None)
	plan.append("items", {"visit_time": v.get("time") or None, "party_type": dt, "party": name,
	                      "visit_type": v.get("type") or None, "location": v.get("location") or None,
	                      "purpose": (v.get("purpose") or "").strip() or None, "status": "Planned"})
	if v.get("notes"):
		plan.notes = ((plan.notes or "") + "\n" + v["notes"]).strip()
	plan.save() if not plan.is_new() else plan.insert()
	return plan.name


def _plan_visits(dt, name):
	"""Lines of Visit Plans for this lead / deal, in the same shape as calendar visits."""
	if not frappe.db.exists("DocType", "Visit Plan Item"):
		return []
	rows = frappe.get_all("Visit Plan Item", filters={"party_type": dt, "party": name, "parenttype": "Visit Plan"},
	                      fields=["name", "parent", "visit_time", "visit_type", "location", "purpose", "status",
	                              "outcome", "modified"])
	if not rows:
		return []
	plans = {p.name: p for p in frappe.get_all("Visit Plan", filters={"name": ["in", list({r.parent for r in rows})]},
	                                           fields=["name", "plan_date", "sales_user", "status"])}
	out = []
	for r in rows:
		p = plans.get(r.parent)
		if not p:
			continue
		st = "Cancelled" if p.status == "Cancelled" else {"Planned": "Open", "Visited": "Completed"}.get(r.status, "Cancelled")
		t = _hhmm(r.visit_time) or "09:00"
		out.append({"name": r.name, "plan": r.parent, "source": "plan", "line_status": r.status,
		            "subject": r.purpose or r.visit_type or _("Visit"), "starts_on": f"{p.plan_date} {t}:00",
		            "ends_on": None, "status": st, "type": r.visit_type, "location": r.location,
		            "by": p.sales_user, "by_name": _fullname(p.sales_user), "outcome": r.outcome, "notes": "",
		            "ts": str(r.modified)})
	return out


def _update_plan_line(dt, name, line, action, v):
	plan_name = frappe.db.get_value("Visit Plan Item", line, "parent")
	plan = frappe.get_doc("Visit Plan", plan_name)
	plan.check_permission("write")
	row = next(r for r in plan.items if r.name == line)
	if row.party_type != dt or row.party != name:
		frappe.throw(_("This visit is not linked to this record"))
	if action == "reopen" and not _is_visit_manager():
		frappe.throw(_("Only a Sales Manager can reopen a finished visit"), frappe.PermissionError)
	if action != "reopen" and _locked(row, plan):
		frappe.throw(_("This visit is {0} and locked.").format(_(row.status)))
	if action == "complete" and not (v.get("outcome") or "").strip():
		frappe.throw(_("Write the outcome of the visit"))
	if action == "complete":
		row.status, row.outcome = "Visited", (v.get("outcome") or "").strip() or row.outcome
	elif action == "cancel":
		row.status = "Cancelled"
	elif action == "reopen":
		row.status = "Planned"
	elif action == "reschedule":
		if str(plan.plan_date) == str(v.get("date")):
			row.visit_time = v.get("time") or row.visit_time
		else:
			# move the line to the plan for the new date
			new = _plan_for(plan.sales_user, v.get("date"), territory=plan.territory)
			new.append("items", {k: row.get(k) for k in LINE_FIELDS if k not in ("status", "outcome")} |
			           {"visit_time": v.get("time") or row.visit_time, "status": "Planned"})
			new.save() if not new.is_new() else new.insert()
			row.status = "Rescheduled"
			row.outcome = (_("Moved to {0}").format(new.name) + ("\n" + row.outcome if row.outcome else ""))
	plan.save()


@frappe.whitelist()
def crm_my_plan(date=None):
	"""Today's (or `date`'s) open Visit Plan for the current user; creates it if there is none."""
	if not frappe.db.exists("DocType", "Visit Plan"):
		frappe.throw(_("Visit Plan is not installed yet"))
	plan = _plan_for(frappe.session.user, date or nowdate())
	if plan.is_new():
		plan.insert()
	return plan.name



def _customer_link_field(doctype):
	meta = frappe.get_meta(doctype)
	return next((d.fieldname for d in meta.fields if d.fieldtype == "Link" and d.options == "Customer"), None)


def _next_steps(deal, customer):
	"""Buttons on a deal: create the next document (Quotation, Work Order Data, ...) pre-filled for the customer."""
	rtype = deal.get("custom_request_type") or "Other"
	steps = []
	for label, dt in NEXT_STEPS.get(rtype, NEXT_STEPS["Other"]):
		if not frappe.db.exists("DocType", dt) or not frappe.has_permission(dt, "create"):
			continue
		if dt == "Quotation":
			values = {"quotation_to": "Customer", "party_name": customer} if customer else {}
		else:
			f = _customer_link_field(dt)
			values = {f: customer} if (f and customer) else {}
		meta = frappe.get_meta(dt)
		for src, dst in (("custom_unit_model", ("model", "model_num", "unit_model", "custom_model")),
		                 ("custom_unit_serial", ("serial_no", "serial_number", "unit_serial"))):
			fld = next((x for x in dst if meta.has_field(x)), None)
			if fld and deal.get(src):
				values[fld] = deal.get(src)
		steps.append({"label": label, "doctype": dt, "values": values, "needs_customer": not customer})
	return steps