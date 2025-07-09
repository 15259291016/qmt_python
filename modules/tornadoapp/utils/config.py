"""
Author: hanlinwu
E-mail: hanlinwu@tencent.com
Description: 配置管理
"""
import os
import urllib.parse

import bios

ENV = os.getenv("DEPLOY_ENV", default="release")

if "local" in (env_name := ENV.lower()):
    configs = {
        # "env": ENV,
        "env": "develop",
        "mysql_config": bios.read(f"./configs/{env_name}/mysql_config.yaml"),
        "url_config": bios.read(f"./configs/{env_name}/url.yaml"),
        "admin": bios.read(f"./configs/{env_name}/admin.yaml"),
        "mongodb_config": bios.read(f"./configs/{env_name}/mongodb_config.yaml"),
        "static_file_path": bios.read(f"./configs/{env_name}/static_file_path.yaml"),
        "pipelines":  bios.read(f"./configs/{env_name}/pipelines.yaml"),
        "mongodb_annotation_config": bios.read(f"./configs/{env_name}/mongodb_annotation_config.yaml"),
        "annotation_file_path": bios.read(f"./configs/{env_name}/annotation_file_path.yaml"),
        "mongodb_user_admin_config": bios.read(f"./configs/{env_name}/mongodb_user_admin_config.yaml"),
        "zhiyan_config": bios.read(f"./configs/{env_name}/zhiyan_config.yaml"),
        "wechat_notification": bios.read(f"./configs/{env_name}/wechat_notification.yaml"),
        # 通用db配置文件，之后能够统一的配置会放到这个文件
        "common_db_config": bios.read(f"./configs/{env_name}/common_db_config.yaml"),
        "yuanmeng_report_mongodb": bios.read(f"./configs/{env_name}/yuanmeng_report_mongodb.yaml"),     # 这个配置预计可以删除
        "rainbow_config": bios.read(f"./configs/{env_name}/rainbow_config.yaml"),
        "source_config": bios.read('./configs/source.yaml'),
        "xdj_redis_cfg": bios.read(f"./configs/{env_name}/xiaodaji_redis_cfg.yaml"),
        "tencent_doc_config": bios.read(f'./configs/{env_name}/tencent_doc_config.yaml'),
        "zhiyan_monitor": bios.read(f"./configs/{env_name}/zhiyan_monitor.yaml"),
        "shared_rainbow_conf": bios.read(f"./configs/{env_name}/shared_rainbow_conf.yaml"),
    }
else:
    # configs = {
    #     "tencent_doc_config": bios.read(f'./configs/{env_name}/tencent_doc_config.yaml'),
    # }

    # configs["mysql_config"] = bios.read("./configs/mysql_config.yaml")

    # configs["url_config"] = bios.read("./configs/url.yaml")
    # configs["source_config"] = bios.read('./configs/source.yaml')
    # configs["admin"] = bios.read("./configs/admin.yaml")
    # ## 区分正式/开发环境
    # configs["mongodb_config"] = bios.read(f"./configs/{ENV}/mongodb_config.yaml")
    # configs["static_file_path"] = bios.read(f"./configs/{ENV}/static_file_path.yaml")
    # configs["pipelines"] = bios.read(f"./configs/{ENV}/pipelines.yaml")

    # configs["mongodb_annotation_config"] = bios.read(
    #     f"./configs/{ENV}/mongodb_annotation_config.yaml"
    # )
    # configs["annotation_file_path"] = bios.read("./configs/annotation_file_path.yaml")
    # configs["env"] = os.environ.get("DEPLOY_ENV", "develop")

    # configs["mongodb_user_admin_config"] = bios.read(
    #     "./configs/mongodb_user_admin_config.yaml"
    # )
    # configs["zhiyan_config"] = bios.read(f"./configs/{ENV}/zhiyan_config.yaml")
    # configs["wechat_notification"] = bios.read("./configs/wechat_notification.yaml")
    # # 通用db配置文件，之后能够统一的配置会放到这个文件
    # configs["common_db_config"] = bios.read(f"./configs/{env_name}/common_db_config.yaml")
    # configs["yuanmeng_report_mongodb"] = bios.read(f"./configs/{env_name}/yuanmeng_report_mongodb.yaml")
    # # 七彩石配置文件的 url 的配置
    # configs["rainbow_config"] = bios.read(f"./configs/{env_name}/rainbow_config.yaml")
    # # 小妲己 redis 配置，用于热更新
    # configs["xdj_redis_cfg"] = bios.read(f"./configs/{env_name}/xiaodaji_redis_cfg.yaml")
    # configs["rainbow_config"] = bios.read(f"./configs/{env_name}/rainbow_config.yaml")
    # configs["zhiyan_monitor"] = bios.read(f"./configs/{env_name}/zhiyan_monitor.yaml")

    # # 多环境共用的七彩石配置
    # configs["shared_rainbow_conf"] = bios.read(f"./configs/shared_rainbow_conf.yaml")
    pass


# configs["cos_config"] = bios.read(f"./configs/{env_name}/cos_config.yaml")
# configs["devops_cfg"] = bios.read(f"./configs/{env_name}/devops_cfg.yaml")
# configs["link_keys"] = bios.read("./configs/link_keys.conf")

# 用于区分本地调试还是线上部署,便于测例库那边调试
configs = {
    "env": "develop"
}
configs["run_mode"] = os.getenv("RUN_MODE", default="online")

configs["ai_model_env"] = "dev" if configs["env"] == "develop" else configs["env"]

# configs["elastic_search_cfg"] = bios.read(f"./configs/{env_name}/elastic_search_cfg.yaml")


if os.path.exists(log_config_path := f"./configs/{env_name}/log_config.yaml"):
    configs["log_config"] = bios.read(log_config_path)
else:
    configs["log_config"] = {}


def get_config(key):
    return configs.get(key)


def get_admin_secret():
    return configs.get("admin")["secretkey"]


def get_common_db_url(common_db_config):
    ip = common_db_config["mongo_ip"]
    port = common_db_config["mongo_port"]
    user = common_db_config.get("user", "")
    passwd = common_db_config.get("passwd", "") 

    if user:
        db_url = f"mongodb://{user}:{passwd}@{ip}:{port}"
    else: 
        db_url = f"mongodb://{ip}:{port}"
    return db_url

