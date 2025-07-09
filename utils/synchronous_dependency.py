import subprocess
import sys
import re
def update_requirements():
    """
    自动更新 requirements.txt 文件，包含当前环境中的所有可远程安装的依赖，并过滤掉本地路径或其他无法正常安装的依赖。
    """
    try:
        # 使用 pip freeze 获取所有已安装的依赖及其版本
        output = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        dependencies = output.decode("utf-8").split("\n")
        
        # 过滤规则
        filtered_dependencies = []
        for dep in dependencies:
            # 去除前后空白
            dep = dep.strip()
            
            # 跳过空行和注释
            if not dep or dep.startswith('#'):
                continue
            
            # 匹配标准的依赖格式（支持 version specifier）
            if re.match(r'^[a-zA-Z0-9\-_]+(?:==[a-zA-Z0-9\.]+)?$', dep):
                filtered_dependencies.append(dep)
            else:
                # 跳过不符合标准格式的依赖
                pass
                # print(f"跳过不符合远程安装规则的依赖：{dep}")
        
        # 将过滤后的依赖写入 requirements.txt 文件
        with open("requirements.txt", "w") as f:
            for dep in filtered_dependencies:
                f.write(dep + "\n")
        print("requirements.txt 文件已成功更新！")
    except Exception as e:
        print(f"生成 requirements.txt 文件时出错：{e}")