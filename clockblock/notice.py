# 设置TTL时间
# username_id.create_index([("time", pymongo.ASCENDING)], expireAfterSeconds=60)

# 设置自增id
"""
思路为：
维护一张id表，每次通过具有原子性的find_and_modify去从这张表取id，然后设置到其它需要的表中
id表创建语句：
username_id = db['user_id']
username_id.insert_one(({'_id': "userid", 'sequence_value': 0}))

自增函数：
def getNextValue(user_Name):
    ret = username_id.find_and_modify({"_id": user_Name}, {"$inc": {"sequence_value": 1}}, safe=True, new=True)
    new = ret["sequence_value"]
    return new
"""