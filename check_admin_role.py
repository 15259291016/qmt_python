#!/usr/bin/env python3
"""
检查admin角色的权限配置
"""

import asyncio
from modules.tornadoapp.model.permission_model import Role, Permission
from modules.tornadoapp.db.dbUtil import init_beanie


async def check_admin_role():
    """检查admin角色的权限配置"""
    print("检查admin角色的权限配置...")
    
    # 初始化数据库连接
    await init_beanie()
    
    try:
        # 查找admin角色
        admin_role = await Role.find_one({"name": "admin"})
        if not admin_role:
            print("错误：找不到admin角色")
            return
        
        print(f"Admin角色: {admin_role.name}")
        print(f"描述: {admin_role.description}")
        print(f"权限数量: {len(admin_role.permissions) if admin_role.permissions else 0}")
        
        if admin_role.permissions:
            print("权限列表:")
            for perm_id in admin_role.permissions:
                permission = await Permission.get(perm_id)
                if permission:
                    print(f"  - {permission.name}: {permission.description}")
                else:
                    print(f"  - {perm_id}: 权限不存在")
        else:
            print("Admin角色没有任何权限！")
        
        print("\n检查完成")
        
    except Exception as e:
        print(f"检查失败: {e}")
        raise
    finally:
        print("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(check_admin_role()) 