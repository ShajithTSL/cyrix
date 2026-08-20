import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import get_jenv
from frappe import whitelist
from frappe.utils import (
    DATE_FORMAT,
    formatdate,
    add_days,
    add_to_date,
    cint,
    comma_and,
    date_diff,
    flt,
    get_link_to_form,
    getdate,
)
from datetime import datetime


@frappe.whitelist()
def download_custom_payroll_pdf(docname):
    doctype = "Payroll Entry"
    print_format_name = "Payroll Entry"  # Your existing Jinja-based print format in Frappe UI

    doc = frappe.get_doc(doctype, docname)
    print_format = frappe.get_doc("Print Format", print_format_name)

    # Create a Jinja environment
    jenv = get_jenv()
    template = jenv.from_string(print_format.html)

    # Render template with custom print_context
    html = template.render({
        "doc": doc,
        "print_format": print_format_name,
        "no_letterhead": 0,
        "print_context": {}
    })

    # Convert to PDF
    pdf = get_pdf(html)

    # Save the PDF to File and return public URL
    _file = frappe.get_doc({
        "doctype": "File",
        "file_name": f"{docname}.pdf",
        "is_private": 0,
        "content": pdf
    })
    _file.save()
    return _file.file_url


@frappe.whitelist()
def salary_register(name,docstatus):
    doc = frappe.get_doc("Payroll Entry",name)
    if doc.get("company") == "Cyrix TSL - Kuwait":
        filters = {'from_date': doc.get("start_date"), 'to_date': doc.get("end_date"), 'currency': 'KWD', 'company': doc.get("company"), 'docstatus': docstatus}
    if doc.get("company") in ["Company Al-Halloul Faniye Medical"]:
        filters = {'from_date': doc.get("start_date"), 'to_date': doc.get("end_date"), 'currency': 'SAR', 'company': doc.get("company"), 'docstatus': docstatus}
    if doc.get("company") == "Cyrix TSL - UAE":
        filters = {'from_date': doc.get("start_date"), 'to_date': doc.get("end_date"), 'currency': 'AED', 'company': doc.get("company"), 'docstatus': docstatus}
    from cyrix.cyrix_tsl.report.salary_register_report.salary_register_report import execute
    result = execute(filters)
    headers = result[0]
    records = result[1]
    if records:
        skip_columns = ['basic','housing','food','transport','others','total_deduction','loan','total_loan_repayment','company','salary_slip_id', 'branch', 'date_of_joining', 'start_date', 'end_date','currency','leave_without_pay']
        int_columns = ['leave_without_pay', 'payment_days',"civil_id_no"]
        currency_columns = [header['fieldname'] for header in headers if header.get('fieldtype') == 'Currency']
        filtered_headers = []
        for header in headers:
            if header['fieldname'] in skip_columns:
                continue
            if header["label"] and frappe.db.get_value("Salary Component",header["label"],'name_in_report'):
                header["label"] = frappe.db.get_value("Salary Component",header["label"],'name_in_report')
            filtered_headers.append(header)


        # Add Civil ID header after employee_name
        for index, header in enumerate(filtered_headers):
            if header['fieldname'] == 'employee_name' and doc.get("company") in ["Company Al-Halloul Faniye Medical"]:
                # Create a new header for Civil ID
                civil_id_header = {
                    'fieldname': 'civil_id_no',
                    'label': 'Civil ID',
                    'fieldtype': 'Data'  # Assuming it's a string
                }
                filtered_headers.insert(index + 1, civil_id_header)  # Insert after employee_name

        totals = {fieldname: 0.0 for fieldname in currency_columns}
        
        # Generate HTML table headers
        data = """<style>
            table.custom-bordered-table {
                border-collapse: collapse;
                width: 100%;
            }
            table.custom-bordered-table, 
            table.custom-bordered-table th, 
            table.custom-bordered-table td {
                border: 1px solid #000;
            }
            table.custom-bordered-table th, 
            table.custom-bordered-table td {
                padding: 3px 3px 3px 3px !important;
                text-align: left;
            }
        </style>
        """
        data += '<table class="custom-bordered-table" border="1" width="100%"><tr><td style="text-align:right;font-size:7px;font-weight:bold">#</td>'
        data += ''.join(f'<td style="font-size:7px;font-weight:bold">{header["label"]}</td>' for header in filtered_headers)

        data += '</tr>'
        records = sorted(records, key=lambda x: int(x.get('employee', 0)))
        # Generate HTML table rows
        sl_no = 1
        for record in records:
            data += '<tr>'
            data += f'<td style="font-size:7px">{sl_no}</td>'

            for header in filtered_headers:
                fieldname = header['fieldname']
                if fieldname == "civil_id_no" and doc.get("company") in ["Company Al-Halloul Faniye Medical"]:
                    fieldtype = "Data"
                    cell_value = frappe.db.get_value("Employee",record.get("employee"),'civil_id_no')  # Default to 0 if None
                
                elif fieldname == "ctc":
                    fieldtype = "Currency"
                    cell_value = frappe.db.get_value("Employee",record.get("employee"),'ctc')  # Default to 0 if None
                
                else:
                    fieldtype = header.get('fieldtype', '')
                    cell_value = record.get(fieldname, 0)  # Default to 0 if None
                
                # Update totals for currency columns
                if fieldname in currency_columns:
                    totals[fieldname] += float(cell_value) if isinstance(cell_value, (float, int)) else 0
                
                # Format cell value
                if fieldtype == 'Currency':
                    cell_value = "{:,.2f}".format(cell_value) if isinstance(cell_value, (float, int)) else "0.000"
                elif isinstance(cell_value, float):
                    # cell_value = f"{cell_value:.2f}"
                    cell_value = "{:,.2f}".format(cell_value)
                elif fieldtype == 'Date':
                    cell_value = formatdate(cell_value)
                data += f'<td style="font-size:7px">{cell_value or ""}</td>'
            data += '</tr>'
            sl_no += 1

        # Generate totals row for currency columns
        data += '<tr>'

        # Determine the number of non-currency columns before the first currency column
        first_currency_index = next((i for i, header in enumerate(filtered_headers) if header['fieldname'] in currency_columns), len(filtered_headers))
        non_currency_colspan = first_currency_index + 1

        # Add merged cell for 'Total' title
        if non_currency_colspan > 0:
            data += f'<td style="font-size:7px;font-weight:bold;text-align:center" colspan="{non_currency_colspan}">Total</td>'

        # Add empty cells for any columns between the merged 'Total' cell and the first currency column
        for i in range(non_currency_colspan, first_currency_index):
            data += '<td></td>'

        # Add total values for currency columns and empty cells for non-currency columns after 'Total'
        for i, header in enumerate(filtered_headers[first_currency_index:], start=first_currency_index):
            fieldname = header['fieldname']
            if fieldname in currency_columns:
                total_value = "{:,.2f}".format(totals[fieldname])
            else:
                total_value = ''
            data += f'<td style="font-size:7px;font-weight:bold">{total_value}</td>'
            
        data += '</tr>'

        data += '</table>'

        return data
    else:
        return ''

@frappe.whitelist()

def salary_register1(name, docstatus):

    doc = frappe.get_doc("Payroll Entry", name)

    # =========================
    # FILTER BUILDING
    # =========================
    if doc.get("company") == "Cyrix TSL - Kuwait":
        filters = {
            'from_date': doc.get("start_date"),
            'to_date': doc.get("end_date"),
            'currency': 'KWD',
            'company': doc.get("company"),
            'docstatus': docstatus
        }

    elif doc.get("company") in [ "Company Al-Halloul Faniye Medical"]:
        filters = {
            'from_date': doc.get("start_date"),
            'to_date': doc.get("end_date"),
            'currency': 'SAR',
            'company': doc.get("company"),
            'docstatus': docstatus
        }

    elif doc.get("company") == "Cyrix TSL - UAE":
        currency = 'AED'
        filters = {
            'from_date': doc.get("start_date"),
            'to_date': doc.get("end_date"),
            'currency': currency,
            'company': doc.get("company"),
            'docstatus': docstatus
        }

    # =========================
    # EXECUTE REPORT
    # =========================
    from cyrix.cyrix_tsl.report.salary_register_report.salary_register_report import execute
    headers, records = execute(filters)

    if not records:
        return ""

    # =========================
    # FORCE REQUIRED HEADERS
    # =========================
    def add_header(fieldname, label):
        if fieldname not in [h.get("fieldname") for h in headers]:
            headers.append({
                "fieldname": fieldname,
                "label": label,
                "fieldtype": "Currency"
            })

    add_header("date_of_joining", "Date of Joining")
    add_header("employee_advance", "Advance")
    add_header("other_deduction", "Other Deduction")
    add_header("loan", "Loan")
    add_header("worked_days", "Worked Days")

    # =========================
    # COLUMN ORDER
    # =========================
    details_order = [
        'employee',
        'employee_name',
        'date_of_joining',
        'designation',
        # 'department'
    ]

    fixed_order = ['basic', 'housing', 'food', 'transport', 'others','gross_pay']
    summary_order = [ 'worked_days','additions']
    deduction_order = ['employee_advance', 'other_deduction', 'loan']
    final_order = ['net_pay']

    header_map = {h.get("fieldname"): h for h in headers}

    details_headers = [header_map[f] for f in details_order if f in header_map]
    fixed_headers = [header_map[f] for f in fixed_order if f in header_map]
    summary_headers = [header_map[f] for f in summary_order if f in header_map]
    deduction_headers = [header_map[f] for f in deduction_order if f in header_map]
    final_headers = [header_map[f] for f in final_order if f in header_map]

    filtered_headers = (
        details_headers +
        fixed_headers +
        summary_headers +
        deduction_headers +
        final_headers
    )
    totals = {h.get("fieldname"): 0 for h in filtered_headers if h.get("fieldname")}    # =========================
    # HTML START
    # =========================
    data = """
    <style>
        table.custom-bordered-table {
            border-collapse: collapse;
            width: 100%;
        }
        table.custom-bordered-table, th, td {
            border: 1px solid #000;
        }
        th, td {
            padding: 3px !important;
            font-size: 8px;
        }
    </style>
    """

    data += '<table class="custom-bordered-table">'

    # HEADER ROW
    data += '<tr><td style="background:#C0C0C0;text-align:center"></td>'
    data += f'<td  style="background:#C0C0C0;text-align:center"  colspan="{len(details_headers)}"><b></b></td>'
    data += f'<td style="background:#98FB98;text-align:center" colspan="{len(fixed_headers)}"><b>Fixed</b></td>'
    data += f'<td style="background:#C0C0C0;text-align:center" colspan="{len(summary_headers)}"></td>'
    data += f'<td style="background:#FA8072;text-align:center" colspan="{len(deduction_headers)}"><b>Deductions</b></td>'
    data += f'<td style="background:#87CEFA;text-align:center" colspan="{len(final_headers)}"><b></b></td>'
    data += '</tr>'

   # =========================
# COLUMN HEADER ROW
# =========================
    data += '<tr>'

    # row number column
    data += '<td style="font-weight:bold;text-align:center;background:#C0C0C0">#</td>'

    # details columns
    data += ''.join(
        f'<td style="font-weight:bold;text-align:center;background:#C0C0C0">{h.get("label")}</td>'
        for h in details_headers
    )

    # earnings columns
    data += ''.join(
        f'<td style="font-weight:bold;text-align:center;background:#98FB98">{h.get("label")}</td>'
        for h in fixed_headers
    )

    # worked days columns
    data += ''.join(
        f'<td style="font-weight:bold;text-align:center;background:#C0C0C0">{h.get("label")}</td>'
        for h in summary_headers
    )

    # deduction columns
    data += ''.join(
        f'<td style="font-weight:bold;text-align:center;background:#FA8072">{h.get("label")}</td>'
        for h in deduction_headers
    )

    # net pay columns
    data += ''.join(
        f'<td style="font-weight:bold;text-align:center;background:#87CEFA">{h.get("label")}</td>'
        for h in final_headers
    )

    data += '</tr>'
    # SORT
    records = sorted(records, key=lambda x: int(x.get('employee') or 0))

    # =========================
    # ROW DATA (FIXED SOURCES)
    # =========================
    employee_map = {
    d.name: d for d in frappe.db.sql("""
        SELECT name,
               basic,
               housing_allowance,
               food_allowance,
               transport_allowance,
               other_allowances
        FROM `tabEmployee`
    """, as_dict=1)
}
    for i, record in enumerate(records, 1):
        data += '<tr>'
        data += f'<td>{i}</td>'

        emp = record.get("employee")

        for header in filtered_headers:
            fieldname = header.get("fieldname")

            # FIXED SALARY FROM EMPLOYEE
            emp_data = employee_map.get(emp) or {}
            gross_salary = (
            (emp_data.get("basic") or 0)
            + (emp_data.get("housing_allowance") or 0)
            + (emp_data.get("food_allowance") or 0)
            + (emp_data.get("transport_allowance") or 0)
            + (emp_data.get("other_allowances") or 0)
        )

            if fieldname == "basic":
                value = record.get("base", 0)

            elif fieldname == "housing":
                value = record.get("housing_allowance", 0)

            elif fieldname == "food":
                value = record.get("food_allowance", 0)

            elif fieldname == "transport":
                value = record.get("transport_allowance", 0)

            elif fieldname == "others":
                value = record.get("other_allowances", 0)
            elif fieldname == "gross_pay":
                value = gross_salary

            elif fieldname == "net_pay":
                value = record.get("net_pay", 0)

            
            

            # DATE OF JOINING
            elif fieldname == "date_of_joining":
                doj = frappe.db.get_value("Employee", emp, "date_of_joining")

                value = frappe.utils.formatdate(doj, "dd-MM-yyyy") if doj else ""

            # WORKED DAYS (CORRECT SOURCE)
            elif fieldname == "worked_days":
                query = """
                    SELECT SUM(payment_days)
                    FROM `tabSalary Slip`
                    WHERE employee = %s
                    AND start_date BETWEEN %s AND %s
                """
                value = frappe.db.sql(query, (emp, doc.get("start_date"), doc.get("end_date")))[0][0] or 0
                value = int(float(value))
                

            # ADVANCE
            elif fieldname == "employee_advance":
                query = """
                    SELECT SUM(sd.amount)
                    FROM `tabSalary Detail` sd
                    JOIN `tabSalary Slip` ss ON ss.name = sd.parent
                    WHERE ss.employee = %s
                    AND ss.start_date BETWEEN %s AND %s
                    AND sd.salary_component IN ('Employee Advance', 'Employee Advance Staff')
                    
                """
                value = frappe.db.sql(query, (emp, doc.get("start_date"), doc.get("end_date")))[0][0] or 0
                value = int(float(value))
            # OTHER DEDUCTION
            elif fieldname == "other_deduction":
                query = """
                    SELECT SUM(sd.amount)
                    FROM `tabSalary Detail` sd
                    JOIN `tabSalary Slip` ss ON ss.name = sd.parent
                    WHERE ss.employee = %s
                    AND ss.start_date BETWEEN %s AND %s
                    AND sd.salary_component IN ('Other Deductions Staff', 'Other Deductions Due')
                 
                """
                value = frappe.db.sql(query, (emp, doc.get("start_date"), doc.get("end_date")))[0][0] or 0
                value = int(float(value))
            # LOAN
            elif fieldname == "loan":
                query = """
                SELECT  
                IFNULL(SUM(DISTINCT sd.total_payment), 0) AS loan_payment,
                IFNULL(SUM(
                    CASE 
                         WHEN sdet.salary_component IN ('Loan', 'Loan Due')
                        THEN sdet.amount ELSE 0 
                    END
                ), 0) AS salary_loan_amount

            FROM `tabSalary Slip` ss

            LEFT JOIN `tabLoan Details` sd 
                ON ss.name = sd.parent

            LEFT JOIN `tabSalary Detail` sdet 
                ON ss.name = sdet.parent

            WHERE ss.employee = %s
            AND ss.start_date BETWEEN %s AND %s
        """
                result = frappe.db.sql(query, (emp, doc.get("start_date"), doc.get("end_date")))

                loan_payment = result[0][0] if result and result[0] else 0
                salary_loan = result[0][1] if result and result[0] else 0

                # If you want total loan:
                value = loan_payment + salary_loan
                
            # DEFAULT
            else:
                value = record.get(fieldname, "")
            if isinstance(value, (int, float)):
                totals[fieldname] += value
                
            data += f'<td>{value or ""}</td>'
           

        data += '</tr>'
    # =========================
    # TOTAL ROW
    # =========================
    data += '<tr style="font-weight:bold;background:#f2f2f2;">'
    data += '<td>Total</td>'

    for header in filtered_headers:
        fieldname = header.get("fieldname")

        if fieldname in ['employee', 'employee_name', 'designation', 'department', 'date_of_joining']:
            data += '<td></td>'
        else:
            value = totals.get(fieldname, 0) or 0

            data += f'<td>{float(value):,.2f}</td>'

    data += '</tr>'

    data += '</table>'
   

    return data


import openpyxl
from openpyxl import Workbook
from six import BytesIO, string_types
from openpyxl.styles import Font, Alignment, Border, Side
@frappe.whitelist()
def salary_register_excel():
    args = frappe.local.form_dict
    filename = "Salary Summary"
    if frappe.session.user == "finance@tsl-me.com":
        skip_columns = ['base','housing_allowance','food_allowance','transport_allowance','other_allowances','total_deduction','loan','total_loan_repayment','company','salary_slip_id', 'branch', 'date_of_joining', 'start_date', 'end_date','currency','department','leave_without_pay']

        test = build_xlsx_response(filename, skip_columns)
    else:
        skip_columns = ['basic','housing','food','transport','others','total_deduction','loan','total_loan_repayment','company','salary_slip_id', 'branch', 'date_of_joining', 'start_date', 'end_date','currency','department','leave_without_pay']
        test = build_xlsx_response(filename, skip_columns)




def make_xlsx(data, skip_columns, sheet_name=None, wb=None, column_widths=None):
    args = frappe.local.form_dict
    column_widths = column_widths or []
    if wb is None:
        wb = openpyxl.Workbook()

    ws = wb.create_sheet(sheet_name, 0)

    doc = frappe.get_doc("Payroll Entry",args.name)
    company = doc.company
    docstatus = args.doc_status
    from datetime import timedelta
    current_year = datetime.now().year
    if company == "Cyrix TSL - Kuwait":
        filters = {'from_date': doc.get("start_date"), 'to_date': doc.get("end_date"), 'currency': 'KWD', 'company': doc.get("company"), 'docstatus': docstatus}
    if company in ["Company Al-Halloul Faniye Medical"]:
        filters = {'from_date': doc.get("start_date"), 'to_date': doc.get("end_date"), 'currency': 'SAR', 'company': doc.get("company"), 'docstatus': docstatus}
    if company == "Cyrix TSL - UAE":
        filters = {'from_date': doc.get("start_date"), 'to_date': doc.get("end_date"), 'currency': 'AED', 'company': doc.get("company"), 'docstatus': docstatus}
    from cyrix.cyrix_tsl.report.salary_register_report.salary_register_report import execute
    result = execute(filters)
    headers = result[0]
    records = result[1]
    frappe.log_error('sk',records)
    int_columns = ['leave_without_pay', 'payment_days',"civil_id_no"]
    currency_columns = [header['fieldname'] for header in headers if header.get('fieldtype') == 'Currency']
    filtered_headers = []
    for header in headers:
        if header['fieldname'] in skip_columns:
            continue
        if header["label"] and frappe.db.get_value("Salary Component",header["label"],'name_in_report'):
            header["label"] = frappe.db.get_value("Salary Component",header["label"],'name_in_report')
        filtered_headers.append(header)

    for index, header in enumerate(filtered_headers):
        if company in ["Company Al-Halloul Faniye Medical"] and header['fieldname'] == 'employee_name':
            # Create a new header for Civil ID
            civil_id_header = {
                'fieldname': 'civil_id_no',
                'label': 'Civil ID',
                'fieldtype': 'Data'  # Assuming it's a string
            }
            filtered_headers.insert(index + 1, civil_id_header)  # Insert after employee_name

    totals = {fieldname: 0.0 for fieldname in currency_columns}
    ws.append(["SALARY SUMMARY"])
    ws.append([""])
    ws.append([company])

    title = ["Sl.No."]
    for header in filtered_headers:
        title.append(header["label"])
    ws.append(title)
    cl_no = len(filtered_headers)+1
    for header in ws.iter_rows(min_row=1 , max_row=4, min_col=1, max_col=cl_no):
        for cell in header:
            cell.font = Font(bold=True)
    records = sorted(records, key=lambda x: int(x.get('employee', 0)))
    sl_no = 1
    for record in records:
        columns = [sl_no]
        for header in filtered_headers:
            fieldname = header['fieldname']
            if fieldname == "civil_id_no" and company in ["Company Al-Halloul Faniye Medical"]:
                fieldtype = "Data"
                cell_value = frappe.db.get_value("Employee",record.get("employee"),'civil_id_no')  # Default to 0 if None

            elif fieldname == "ctc":
                fieldtype = "Currency"
                cell_value = frappe.db.get_value("Employee",record.get("employee"),'ctc')

            else:
                fieldtype = header.get('fieldtype', '')
                cell_value = record.get(fieldname, 0)  # Default to 0 if None
            if fieldname in currency_columns:
                totals[fieldname] += float(cell_value) if isinstance(cell_value, (float, int)) else 0
            if fieldtype == 'Currency':
                cell_value = "{:,.2f}".format(cell_value) if isinstance(cell_value, (float, int)) else "0.000"
            elif isinstance(cell_value, float):
                cell_value = "{:,.2f}".format(cell_value)
            columns.append(cell_value)
        ws.append(columns)
        sl_no += 1
    total_row = []
    first_currency_index = next((i for i, header in enumerate(filtered_headers) if header['fieldname'] in currency_columns), len(filtered_headers))
    non_currency_colspan = first_currency_index + 1
    total_row.append("Total")
    if non_currency_colspan > 0:
        for _ in range(non_currency_colspan-1):
            total_row.append("")
    for i in range(non_currency_colspan, first_currency_index):
        data += '<td></td>'
        total_row.append("")
    for i, header in enumerate(filtered_headers[first_currency_index:], start=first_currency_index):
        fieldname = header['fieldname']
        if fieldname in currency_columns:
            total_value = "{:,.2f}".format(totals[fieldname])
        else:
            total_value = ''
        total_row.append(total_value)
    ws.append(total_row)
    align_center = Alignment(horizontal='center',vertical='center')
    ws.merge_cells(start_row=sl_no+4, start_column=1, end_row=sl_no+4, end_column=non_currency_colspan )
    ws.merge_cells(start_row=1, start_column=1, end_row=2, end_column=cl_no )
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=cl_no )

    for header in ws.iter_rows(min_row=sl_no+4 , max_row=sl_no+4, min_col=1, max_col=non_currency_colspan):
        for cell in header:
            cell.font = Font(bold=True)
    border_thin = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin'))
    header_range = ws['A1':ws.cell(row=sl_no+4, column=cl_no).coordinate]
    for row in header_range:
        for cell in row:
            cell.border = border_thin
            cell.alignment = align_center

    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    return xlsx_file

def build_xlsx_response(filename, skip_columns):
    xlsx_file = make_xlsx(filename, skip_columns)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'