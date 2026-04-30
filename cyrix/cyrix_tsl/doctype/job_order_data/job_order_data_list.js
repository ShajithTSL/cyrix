frappe.listview_settings['Job Order Data'] = {
        add_fields: ["status","name"],
	refresh:function(){
		cur_list.page.clear_primary_action()
        },
	
	onload: function (listview) {
                if(frappe.user.has_role("Technician") && frappe.session.user !="Administrator" ){
                        listview.filter_area.add([[ "Job Order Data", "status" ,"in", ["NE-Need Evaluation","AP-Available Parts","SP-Searching Parts","NER-Need Evaluation Return"] ]]);
                        listview.refresh()
                }
        },
	get_indicator: function (doc) {
        if (doc.status === "UE-Under Evaluation") {
                return [__("UE-Under Evaluation"), "yellow", "status,=,UE-Under Evaluation"];

        } else if (doc.status === "AP-Available Parts") {
                return [__("AP-Available Parts"), "orange", "status,=,AP-Available Parts"];
                
        } else if (doc.status === "SP-Searching Parts") {
                return [__("SP-Searching Parts"), "yellow", "status,=,SP-Searching Parts"];
        }
        else if (doc.status === "Q-Quoted") {
                return [__("Q-Quoted"), "green", "status,=,Q-Quoted"];
        }
        else if (doc.status === "IQ-Internally Quoted") {
                return [__("IQ-Internally Quoted"), "cyan", "status,=,IQ-Internally Quoted"];
        }
        else if (doc.status === "RNP-Return No Parts") {
                return [__("RNP-Return No Parts"), "grey", "status,=,RNP-Return No Parts"];
        }
        else if (doc.status === "A-Approved") {
                return [__("A-Approved"), "green", "status,=,A-Approved"];
        }
        else if (doc.status === "RNA-Return Not Approved") {
                return [__("RNA-Return Not Approved"), "grey", "status,=,RNA-Return Not Approved"];
        }
        else if (doc.status === "TR-Technician Repair") {
                return [__("TR-Technician Repair"), "yellow", "status,=,TR-Technician Repair"];
        }
        else if (doc.status === "RSC-Repaired and Shipped Client") {
                return [__("RSC-Repaired and Shipped Client"), "green", "status,=,RSC-Repaired and Shipped Client"];
        }
        else if (doc.status === "WP-Waiting Parts") {
                return [__("WP-Waiting Parts"), "cyan", "status,=,WP-Waiting Parts"];
        }
        else if (doc.status === "EP-Extra Parts") {
                return [__("EP-Extra Parts"), "pink", "status,=,EP-Extra Parts"];
        }
        else if (doc.status === "IP-Internal Extra Parts") {
                return [__("IP-Internal Extra Parts"), "pink", "status,=,IP-Internal Extra Parts"];
        }
        else if (doc.status === "RNAC-Return Not Approved Client") {
                return [__("RNAC-Return Not Approved Client"), "darkgrey", "status,=,RNAC-Return Not Approved Client"];
        }
        else if (doc.status === "RS-Repaired and Shipped") {
                return [__("RS-Repaired and Shipped"), "green", "status,=,RS-Repaired and Shipped"];
        }
        else if (doc.status === "RNR-Return Not Repaired") {
                return [__("RNR-Return Not Repaired"), "grey", "status,=,RNR-Return Not Repaired"];
        }
        else if (doc.status === "RNRC-Return Not Repaired Client") {
                return [__("RNRC-Return Not Repaired Client"), "darkgrey", "status,=,RNRC-Return Not Repaired Client"];
        }
        else if (doc.status === "W-Working") {
                return [__("W-Working"), "pink", "status,=,W-Working"];
        }
        else if (doc.status === "P-Paid") {
                return [__("P-Paid"), "green", "status,=,P-Paid"];
        }
        else if (doc.status === "C-Comparison") {
                return [__("C-Comparison"), "cyan", "status,=,C-Comparison"];
        }
        else if (doc.status === "CC-Comparison Client") {
                return [__("CC-Comparison Client"), "pink", "status,=,CC-Comparison Client"];
        }
        else if (doc.status === "NER-Need Evaluation Return") {
                return [__("NER-Need Evaluation Return"), "yellow", "status,=,NER-Need Evaluation Return"];
        }
        else if (doc.status === "Unpaid") {
                return [__("Unpaid"), "red", "status,=,Unpaid"];
        }
        else if (doc.status === "Partially Paid") {
                return [__("Partially Paid"), "yellow", "status,=,Partially Paid"];
        }
        else if (doc.status === "RNPC-Return No Parts Client") {
                return [__("RNPC-Return No Parts Client"), "darkgrey", "status,=,RNPC-Return No Parts Client"];
        }
        else if (doc.status === "UTR-Under Technician Repair") {
                return [__("UTR-Under Technician Repair"), "pink", "status,=,UTR-Under Technician Repair"];
        }
        else if (doc.status === "Board Evaluation") {
                return [__("Board Evaluation"), "red", "status,=,Board Evaluation"];
        }
        else if (doc.status === "RNF-Return No Fault") {
                return [__("RNF-Return No Fault"), "green", "status,=,RNF-Return No Fault"];
        }
        else if (doc.status === "RNFC-Return No Fault Client") {
                return [__("RNFC-Return No Fault Client"), "green", "status,=,RNFC-Return No Fault Client"];
        }
        else if (doc.status === "Parts Priced") {
                return [__("Parts Priced"), "green", "status,=,Parts Priced"];
        }
        else if (doc.status === "Pending Internal Approval") {
                return [__("Pending Internal Approval"), "orange", "status,=,Pending Internal Approval"];
        }
        else if(doc.status === "NE-Need Evaluation"){
                return [__("NE-Need Evaluation"), "blue", "status,=,NE-Need Evaluation"];
        }
        else if (doc.status === "RSI-Repaired and Shipped Invoiced") {
                return[__("RSI-Repaired and Shipped Invoiced"),"pink","status,=,RSI-Repaired and Shipped Invoiced"];
        }
        else if (doc.status === "CT-Customer Testing") {
                return[__("CT-Customer Testing"),"red","status,=,CT-Customer Testing"];
                }
        else if (doc.status === "NEA-Need Evaluation Approved") {
                return[__("NEA-Need Evaluation Approved"),"red","status,=,NEA-Need Evaluation Approved"];
                    }

        else if (doc.status === "TP-Third Party") {
                return[__("TP-Third Party"),"blue","status,=,TP-Third Party"];
                    }
        else if (doc.status === "C-Cancelled") {
                return[__("C-Cancelled"),"red","status,=,C-Cancelled"];
                    }
        
        else if (doc.status === "Replace") {
                return[__("Replace"),"red","status,=,Replace"];
                    }
          
      },
};
