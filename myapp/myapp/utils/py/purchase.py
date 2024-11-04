# import frappe 
# import json

# @frappe.whitelist()
# def correction_entry(docs) -> None:
#     docs = json.loads(docs)
#     linked_invoices: list[dict] = frappe.db.get_all("Purchase Invoice Item", filters={"purchase_receipt": docs.get("name")}, fields=["parent" , 'name'])

#     for invoice in linked_invoices:
#         frappe.db.set_value("Purchase Invoice Item", invoice.get("parent"), "purchase_receipt", '')
#         frappe.db.commit()

#     receipt = frappe.get_doc("Purchase Receipt", docs.get("name"))
#     po : list[str] = []
#     mr : list[str] = []

#     item_rate : list[float] = []
#     for item in receipt.items:
#         po.append(item.purchase_order or None)
#         mr.append(item.material_request or None)
#         frappe.db.set_value("Purchase Receipt Item", item.name, "purchase_order", '' )
#         frappe.db.set_value("Purchase Receipt Item", item.name, "material_request", '')
#         frappe.db.commit()
#         linked_invoice = frappe.db.get_value("Purchase Invoice Item", {"purchase_receipt": docs.get("name"), "item_code": item.item_code}, "rate")
#         item_rate.append(linked_invoice)

#     duplicate = frappe.copy_doc(receipt)

#     for  idx , i in enumerate(duplicate.items):

#         if i.serial_and_batch_bundle:
#             bundle = frappe.get_doc("Serial and Batch Bundle", i.serial_and_batch_bundle)
#             new_bundle = frappe.copy_doc(bundle)
#             new_bundle.save()
#             i.serial_and_batch_bundle = new_bundle.name
#             i.purchase_order = po[idx] if po[idx] is not None else None
#             i.material_request = mr[idx] if mr[idx] is not None else None
#             i.rate = item_rate[idx] if item_rate[idx] is not None else i.rate

#     duplicate.set_posting_time = 1
#     duplicate.status = "Completed"
#     duplicate.posting_date = docs.get("posting_date")
#     duplicate.posting_time = docs.get("posting_time")

#     duplicate.save()
#     duplicate.submit()

    
   
   
#     for invoice in linked_invoices:
        
#         frappe.db.set_value("Purchase Invoice Item", invoice.get("name"), "purchase_receipt", duplicate.name)
#         frappe.db.commit()
    
#     receipt.cancel()

#     return duplicate.name


import frappe
@frappe.whitelist()
def make_correction_entry() -> str:
    receipts = frappe.get_all('Purchase Receipt', filters={'docstatus': 1}, fields=['name'])
    invoice_need_correction : list[str] = []
    for receipt in receipts:
        receipt_doc = frappe.get_doc('Purchase Receipt', receipt.get('name'))
        invoices = frappe.get_all('Purchase Invoice Item', filters={'purchase_receipt': receipt_doc.name}, fields=['name', 'parent'])
        if not invoices:
            frappe.error_log( "Inovoice Not Found", f"{receipt_doc.name} has No Invoices Attached")
        else:
            for invoice in invoices:
                invoice_doc = frappe.get_doc('Purchase Invoice', invoice.get('parent'))
                if invoice_doc.docstatus == 1:
                    for item in invoice_doc.items:
                        receipt_item = next((x for x in receipt_doc.items if x.item_code == item.item_code), None)
                        if receipt_item:
                            if item.rate != receipt_item.rate:
                                invoice_need_correction.append(receipt_doc.name)

    yield correction_entry(invoice_need_correction)

def correction_entry(invoices) -> None:
    for invoice in invoices:
        invoice_doc = frappe.get_doc('Purchase Invoice', invoice)







        for item in invoice_doc.items:
            receipt_item = frappe.db.get_value('Purchase Receipt Item', {'item_code': item.item_code, 'purchase_invoice': invoice}, 'parent')
            if receipt_item:
                receipt = frappe.get_doc('Purchase Receipt', receipt_item)
                for i in receipt.items:
                    if i.item_code == item.item_code:
                        i.purchase_receipt = ''
                        i.save()

                duplicate = frappe.copy_doc(receipt)
                for i in duplicate.items:
                    if i.item_code == item.item_code:
                        i.rate = item.rate
                        i.save()
                duplicate.submit()
                receipt.cancel()
