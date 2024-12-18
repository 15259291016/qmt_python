from elasticsearch import Elasticsearch, exceptions

# 创建Elasticsearch客户端配置
source_es_config = {
    'host': '21.6.210.119',
    'port': 9200,
    'http_auth': ('elastic', '6116988.niu'),  # 确认用户名和密码
    'scheme': 'https',  # 如果使用HTTPS
    'verify_certs': True,  # 确保正确配置SSL验证
    # 'ca_certs': '/path/to/ca.pem',  # 如果需要指定CA证书路径
    'timeout': 60
}

# 创建Elasticsearch客户端
source_es = Elasticsearch([{
    'host': source_es_config['host'],
    'port': source_es_config['port'],
    'scheme': source_es_config['scheme']
}], 
    http_auth=source_es_config['http_auth'],
    verify_certs=source_es_config['verify_certs'],
    # ca_certs=source_es_config.get('ca_certs'),  # 可选，取决于是否需要指定CA证书
    timeout=source_es_config['timeout']
)

try:
    # 测试连接
    if not source_es.ping():
        print("Connection failed")
    else:
        print("Connected to Elasticsearch")

    # 列出所有索引
    response = source_es.cat.indices(format="json", v=True, s="index")
    for index_info in response:
        print(index_info)

except exceptions.AuthenticationException as e:
    print(f"Authentication error: {e}")
except exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")