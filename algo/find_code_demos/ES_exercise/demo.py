from elasticsearch import Elasticsearch

# 连接到本地的 Elasticsearch 实例
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}], basic_auth=('elastic', '6116988.niu'))

# 检查连接是否成功
if es.ping():
    print("Connected to Elasticsearch")
else:
    print("Could not connect to Elasticsearch")

# 查询所有的索引
indices = es.cat.indices(format='json')
print("All indices:")
for index in indices:
    print(index['index'])

# 查看特定索引的 settings 和 mappings
index_name = 'aigc-text-test'

# 获取索引的 settings
settings = es.indices.get_settings(index=index_name)
print(f"Settings for index '{index_name}':")
print(settings[index_name]['settings'])

# 获取索引的 mappings
mappings = es.indices.get_mapping(index=index_name)
print(f"Mappings for index '{index_name}':")
print(mappings[index_name]['mappings'])

