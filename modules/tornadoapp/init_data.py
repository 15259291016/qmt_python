#!/usr/bin/env python3
"""
初始化基础数据脚本
用于创建系统基础角色和权限
"""

import asyncio
from datetime import datetime
from modules.tornadoapp.model.permission_model import Role, Permission
from modules.tornadoapp.model.user_model import User
from modules.tornadoapp.utils.auth import AuthUtils
from modules.tornadoapp.db.dbUtil import init_beanie


async def init_basic_permissions():
    """初始化基础权限"""
    print("正在初始化基础权限...")
    
    # 定义基础权限
    basic_permissions = [
        # 用户管理权限
        {"name": "user:read", "resource": "user", "action": "read", "description": "查看用户信息"},
        {"name": "user:write", "resource": "user", "action": "write", "description": "创建/编辑用户"},
        {"name": "user:delete", "resource": "user", "action": "delete", "description": "删除用户"},
        {"name": "user:admin", "resource": "user", "action": "admin", "description": "用户管理"},
        
        # 角色管理权限
        {"name": "role:read", "resource": "role", "action": "read", "description": "查看角色信息"},
        {"name": "role:write", "resource": "role", "action": "write", "description": "创建/编辑角色"},
        {"name": "role:delete", "resource": "role", "action": "delete", "description": "删除角色"},
        
        # 权限管理权限
        {"name": "permission:read", "resource": "permission", "action": "read", "description": "查看权限信息"},
        {"name": "permission:write", "resource": "permission", "action": "write", "description": "创建权限"},
        {"name": "permission:delete", "resource": "permission", "action": "delete", "description": "删除权限"},
        
        # 数据管理权限
        {"name": "data:read", "resource": "data", "action": "read", "description": "查看数据"},
        {"name": "data:write", "resource": "data", "action": "write", "description": "创建/编辑数据"},
        {"name": "data:delete", "resource": "data", "action": "delete", "description": "删除数据"},
        
        # 系统管理权限
        {"name": "system:read", "resource": "system", "action": "read", "description": "查看系统信息"},
        {"name": "system:write", "resource": "system", "action": "write", "description": "系统配置"},
    ]
    
    created_permissions = []
    for perm_data in basic_permissions:
        # 检查权限是否已存在
        existing_perm = await Permission.find_one({"name": perm_data["name"]})
        if not existing_perm:
            permission = Permission(**perm_data)
            await permission.insert()
            created_permissions.append(permission)
            print(f"创建权限: {perm_data['name']}")
        else:
            created_permissions.append(existing_perm)
            print(f"权限已存在: {perm_data['name']}")
    
    return created_permissions


async def init_basic_roles():
    """初始化基础角色"""
    print("正在初始化基础角色...")
    
    # 获取所有权限
    all_permissions = await Permission.find({"is_active": True}).to_list()
    perm_map = {perm.name: str(perm.id) for perm in all_permissions}
    
    # 定义基础角色
    basic_roles = [
        {
            "name": "admin",
            "description": "系统管理员，拥有所有权限",
            "permissions": list(perm_map.values()),
            "is_system": True
        },
        {
            "name": "user_manager",
            "description": "用户管理员，负责用户管理",
            "permissions": [
                perm_map.get("user:read"),
                perm_map.get("user:write"),
                perm_map.get("user:delete"),
                perm_map.get("user:admin"),
                perm_map.get("role:read"),
                perm_map.get("permission:read")
            ],
            "is_system": True
        },
        {
            "name": "data_manager",
            "description": "数据管理员，负责数据管理",
            "permissions": [
                perm_map.get("data:read"),
                perm_map.get("data:write"),
                perm_map.get("data:delete"),
                perm_map.get("system:read")
            ],
            "is_system": True
        },
        {
            "name": "user",
            "description": "普通用户，基础权限",
            "permissions": [
                perm_map.get("data:read"),
                perm_map.get("system:read")
            ],
            "is_system": True
        }
    ]
    
    created_roles = []
    for role_data in basic_roles:
        # 过滤掉None值
        role_data["permissions"] = [p for p in role_data["permissions"] if p is not None]
        
        # 检查角色是否已存在
        existing_role = await Role.find_one({"name": role_data["name"]})
        if not existing_role:
            role = Role(**role_data)
            await role.insert()
            created_roles.append(role)
            print(f"创建角色: {role_data['name']}")
        else:
            created_roles.append(existing_role)
            print(f"角色已存在: {role_data['name']}")
    
    return created_roles


async def init_admin_user():
    """初始化管理员用户"""
    print("正在初始化管理员用户...")
    
    # 检查是否已存在管理员用户
    admin_user = await User.find_one({"username": "admin"})
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password_hash=AuthUtils.hash_password("admin123"),
            full_name="系统管理员",
            is_active=True,
            is_admin=True
        )
        await admin_user.insert()
        print("创建管理员用户: admin (密码: admin123)")
    else:
        print("管理员用户已存在: admin")
    
    return admin_user


async def main():
    """主函数"""
    print("开始初始化基础数据...")
    
    # 初始化数据库连接
    await init_beanie()
    
    try:
        # 初始化权限
        permissions = await init_basic_permissions()
        print(f"权限初始化完成，共 {len(permissions)} 个权限")
        
        # 初始化角色
        roles = await init_basic_roles()
        print(f"角色初始化完成，共 {len(roles)} 个角色")
        
        # 初始化管理员用户
        admin_user = await init_admin_user()
        print("管理员用户初始化完成")
        
        print("\n=== 初始化完成 ===")
        print("管理员账号: admin")
        print("管理员密码: admin123")
        print("管理员邮箱: admin@example.com")
        print("\n请及时修改管理员密码！")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        raise
    finally:
        # 关闭数据库连接
        print("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main()) 