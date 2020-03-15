# bcdb_test.py
from Jumpscale import j

bcdb = j.data.bcdb.system

schema_1 = """
@url = jumpscale.bcdb.test.house
name** = "" (S)
active** = "" (B)
enum = "a,b,c" (E)
cost** =  (N)

@url = jumpscale.bcdb.test.room1
name** = "" (S)
"""

model = bcdb.model_get(schema=schema_1)
schema_md5 = model.schema._md5

model_obj = model.new(name="test")
model_obj.cost = "10 USD"
model_obj.not_cost = "0 USD"
model_obj.save()

j.shell()
