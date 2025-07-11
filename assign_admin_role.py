#!/usr/bin/env python3
"""
为admin用户分配admin角色
"""

import asyncio
from modules.tornadoapp.model.user_model import User
from modules.tornadoapp.model.permission_model import Role, UserRole
from modules.tornadoapp.db.dbUtil import init_beanie


async def assign_admin_role():
    """为admin用户分配admin角色"""
    print("开始为admin用户分配admin角色...")
    
    # 初始化数据库连接
    await init_beanie()
    
    try:
        # 查找admin用户
        admin_user = await User.find_one({"username": "admin"})
        if not admin_user:
            print("错误：找不到admin用户")
            return
        
        # 查找admin角色
        admin_role = await Role.find_one({"name": "admin"})
        if not admin_role:
            print("错误：找不到admin角色")
            return
        
        # 检查是否已经分配了该角色
        existing_role = await UserRole.find_one({
            "user_id": str(admin_user.id),
            "role_id": str(admin_role.id),
            "is_active": True
        })
        
        if existing_role:
            print("admin用户已经拥有admin角色")
        else:
            # 分配角色
            user_role = UserRole(
                user_id=str(admin_user.id),
                role_id=str(admin_role.id),
                assigned_by=str(admin_user.id)  # 自己分配给自己
            )
            await user_role.insert()
            print("成功为admin用户分配admin角色")
        
        print("操作完成")
        
    except Exception as e:
        print(f"操作失败: {e}")
        raise
    finally:
        print("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(assign_admin_role()) 