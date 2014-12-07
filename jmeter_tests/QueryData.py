import re

# Specifications of the various queries.
queries = [
{
	"test": "Point_NoJoin_NoGroup_Pri1.jmx",
	"template": "Template_2Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select * from store_sales where ss_item_sk = ? and ss_ticket_number=?
""",
		"TEMPLATE_ARGUMENTS": "${item},${ticket}",
		"TEMPLATE_TYPES": "INTEGER,INTEGER",
		"TEMPLATE_VAR1_NAME": "ticket",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "500000",
		"TEMPLATE_VAR2_NAME": "item",
		"TEMPLATE_VAR2_MIN":  "1",
		"TEMPLATE_VAR2_MAX":  "26000",
		"TEMPLATE_SAMPLER":   "false"
	}
},

{
	"test": "Point_NoJoin_NoGroup_Pri2.jmx",
	"template": "Template_2Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select * from store_sales where ss_item_sk = ? and ss_store_sk=?
""",
		"TEMPLATE_ARGUMENTS": "${item},${store}",
		"TEMPLATE_TYPES": "INTEGER,INTEGER",
		"TEMPLATE_VAR1_NAME": "store",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "22",
		"TEMPLATE_VAR2_NAME": "item",
		"TEMPLATE_VAR2_MIN":  "1",
		"TEMPLATE_VAR2_MAX":  "26000",
		"TEMPLATE_SAMPLER":   "false"
	}
},

{
	"test": "Point_NoJoin_NoGroup_Pri3.jmx",
	"template": "Template_2Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select * from store_sales where ss_ticket_number=? and ss_store_sk=?
""",
		"TEMPLATE_ARGUMENTS": "${ticket},${store}",
		"TEMPLATE_TYPES": "INTEGER,INTEGER",
		"TEMPLATE_VAR1_NAME": "store",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "22",
		"TEMPLATE_VAR2_NAME": "ticket",
		"TEMPLATE_VAR2_MIN":  "1",
		"TEMPLATE_VAR2_MAX":  "480000",
		"TEMPLATE_SAMPLER":   "true"
	}
},

{
	"test": "Point_NoJoin_NoGroup_Pri4.jmx",
	"template": "Template_2Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select * from store_sales where ss_ticket_number=? and ss_customer_sk=?
""",
		"TEMPLATE_ARGUMENTS": "${ticket},${customer}",
		"TEMPLATE_TYPES": "INTEGER,INTEGER",
		"TEMPLATE_VAR1_NAME": "ticket",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "480000",
		"TEMPLATE_VAR2_NAME": "customer",
		"TEMPLATE_VAR2_MIN":  "1",
		"TEMPLATE_VAR2_MAX":  "144000",
		"TEMPLATE_SAMPLER":   "true"
	}
},

{
	"test": "Point_NoJoin_NoGroup_Pri5.jmx",
	"template": "Template_2Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select * from store_sales where ss_customer_sk=? and ss_ticket_number=?
""",
		"TEMPLATE_ARGUMENTS": "${customer},${ticket}",
		"TEMPLATE_TYPES": "INTEGER,INTEGER",
		"TEMPLATE_VAR1_NAME": "customer",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "144000",
		"TEMPLATE_VAR2_NAME": "ticket",
		"TEMPLATE_VAR2_MIN":  "1",
		"TEMPLATE_VAR2_MAX":  "480000",
		"TEMPLATE_SAMPLER":   "true"
	}
},

{
	"test": "Point_NoJoin_NoGroup_Pri6.jmx",
	"template": "Template_2Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select * from store_sales where ss_ticket_number=? and ss_cdemo_sk=?
""",
		"TEMPLATE_ARGUMENTS": "${ticket},${cdemo}",
		"TEMPLATE_TYPES": "INTEGER,INTEGER",
		"TEMPLATE_VAR1_NAME": "ticket",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "480000",
		"TEMPLATE_VAR2_NAME": "cdemo",
		"TEMPLATE_VAR2_MIN":  "1",
		"TEMPLATE_VAR2_MAX":  "1000000",
		"TEMPLATE_SAMPLER":   "true"
	}
},

{
	"test": "Point_NoJoin_NoGroup_Pri7.jmx",
	"template": "Template_2Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select * from store_sales where ss_ticket_number=? and ss_hdemo_sk=?
""",
		"TEMPLATE_ARGUMENTS": "${ticket},${hdemo}",
		"TEMPLATE_TYPES": "INTEGER,INTEGER",
		"TEMPLATE_VAR1_NAME": "ticket",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "480000",
		"TEMPLATE_VAR2_NAME": "hdemo",
		"TEMPLATE_VAR2_MIN":  "1",
		"TEMPLATE_VAR2_MAX":  "7200",
		"TEMPLATE_SAMPLER":   "true"
	}
},

{
	"test": "Point_NoJoin_NoGroup_Pri8.jmx",
	"template": "Template_2Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select * from store_sales where ss_ticket_number=? and ss_wholesale_cost=?
""",
		"TEMPLATE_ARGUMENTS": "${ticket},${cost}",
		"TEMPLATE_TYPES": "INTEGER,FLOAT",
		"TEMPLATE_VAR1_NAME": "ticket",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "480000",
		"TEMPLATE_VAR2_NAME": "cost",
		"TEMPLATE_VAR2_MIN":  "1",
		"TEMPLATE_VAR2_MAX":  "100",
		"TEMPLATE_SAMPLER":   "true"
	}
},

{
	"test": "Range_Join_Group_CovGloIndex.jmx",
	"template": "Template_0Var_Date.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select
        sum(ss_net_profit)
from
        store_sales
        join date_dim on store_sales.ss_sold_date_sk = date_dim.d_date_sk
where
        date_dim.d_date between to_date(?) and to_date(?)
group by
        ss_store_sk
""",
		"TEMPLATE_SAMPLER":   "true"
	}
},

{
	"test": "Range_Join_NoGroup_CovGloIndex.jmx",
	"template": "Template_0Var_Date.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select
        sum(ss_net_profit)
from
        store_sales
        join date_dim on store_sales.ss_sold_date_sk = date_dim.d_date_sk
where
        date_dim.d_date between to_date(?) and to_date(?)
""",
		"TEMPLATE_SAMPLER":   "true"
	}
},

{
	"test": "Range_NoJoin_NoGroup_Pri.jmx",
	"template": "Template_1Var_NoDate.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select sum(ss_net_paid) from store_sales where ss_ticket_number = ?
""",
		"TEMPLATE_ARGUMENTS": "${ticket}",
		"TEMPLATE_TYPES": "INTEGER",
		"TEMPLATE_VAR1_NAME": "ticket",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "480000",
		"TEMPLATE_SAMPLER":   "false"
	}
},

{
	"test": "Range_Join_NoGroup_Index.jmx",
	"template": "Template_1Var_Date.jmx",
	"variables": {
		"TEMPLATE_QUERY": """
select
        count(*)
from
        store_sales
        join date_dim on store_sales.ss_sold_date_sk = date_dim.d_date_sk
where
        ss_item_sk = ?
        and date_dim.d_date between to_date(?) and to_date(?)
""",
		"TEMPLATE_ARGUMENTS": "${item}",
		"TEMPLATE_TYPES": "INTEGER",
		"TEMPLATE_VAR1_NAME": "item",
		"TEMPLATE_VAR1_MIN":  "1",
		"TEMPLATE_VAR1_MAX":  "26000",
		"TEMPLATE_SAMPLER":   "true"
	}
},

]

queryNames = {}
for query in queries:
	if queryNames.has_key(query["test"]):
		assert False, "Duplicate query name " + query["test"]
	queryNames[query["test"]] = 1
	with open(query["template"]) as input:
		template = input.read()
		for var in query["variables"].keys():
			val = query["variables"][var]
			if template.find(var) == -1:
				assert False, "Undefined varible " + var
			template = template.replace(var, val)

		m = re.search('(TEMPLATE_[A-Z_]+)', template)
		if m:
			varname = m.group(0)
			assert False, "Variable " + varname + " was not substituted in " + query["template"]
		output = open(query["test"], "w")
		output.write(template)
		output.close()
