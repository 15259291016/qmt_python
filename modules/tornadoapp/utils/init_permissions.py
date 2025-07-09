from datetime import datetime
from modules.tornadoapp.model.permission_model import Role, Permission, PermissionGroup
from modules.tornadoapp.db.dbUtil import init_beanie


async def init_system_permissions():
    """初始化系统权限"""
    print("开始初始化系统权限...")
    
    # 创建基础权限
    permissions = [
        # 用户管理权限
        {"name": "user:read", "resource": "user", "action": "read", "description": "读取用户信息"},
        {"name": "user:write", "resource": "user", "action": "write", "description": "创建/更新用户"},
        {"name": "user:delete", "resource": "user", "action": "delete", "description": "删除用户"},
        {"name": "user:admin", "resource": "user", "action": "admin", "description": "用户管理"},
        
        # 角色管理权限
        {"name": "role:read", "resource": "role", "action": "read", "description": "读取角色信息"},
        {"name": "role:write", "resource": "role", "action": "write", "description": "创建/更新角色"},
        {"name": "role:delete", "resource": "role", "action": "delete", "description": "删除角色"},
        {"name": "role:admin", "resource": "role", "action": "admin", "description": "角色管理"},
        
        # 权限管理权限
        {"name": "permission:read", "resource": "permission", "action": "read", "description": "读取权限信息"},
        {"name": "permission:write", "resource": "permission", "action": "write", "description": "创建/更新权限"},
        {"name": "permission:delete", "resource": "permission", "action": "delete", "description": "删除权限"},
        {"name": "permission:admin", "resource": "permission", "action": "admin", "description": "权限管理"},
        
        # 系统管理权限
        {"name": "system:read", "resource": "system", "action": "read", "description": "读取系统信息"},
        {"name": "system:write", "resource": "system", "action": "write", "description": "修改系统配置"},
        {"name": "system:admin", "resource": "system", "action": "admin", "description": "系统管理"},
        
        # 数据管理权限
        {"name": "data:read", "resource": "data", "action": "read", "description": "读取数据"},
        {"name": "data:write", "resource": "data", "action": "write", "description": "创建/更新数据"},
        {"name": "data:delete", "resource": "data", "action": "delete", "description": "删除数据"},
        {"name": "data:admin", "resource": "data", "action": "admin", "description": "数据管理"},
    ]
    
    # 创建权限记录
    for perm_data in permissions:
        existing_perm = await Permission.find_one({"name": perm_data["name"]})
        if not existing_perm:
            permission = Permission(**perm_data)
            await permission.insert()
            print(f"创建权限: {perm_data['name']}")
        else:
            print(f"权限已存在: {perm_data['name']}")
    
    print("权限初始化完成")


async def init_system_roles():
    """初始化系统角色"""
    print("开始初始化系统角色...")
    
    # 创建系统角色
    roles = [
        {
            "name": "super_admin",
            "description": "超级管理员",
            "permissions": [
                "user:admin", "role:admin", "permission:admin", 
                "system:admin", "data:admin"
            ],
            "is_system": True
        },
        {
            "name": "admin",
            "description": "管理员",
            "permissions": [
                "user:read", "user:write", "user:delete",
                "role:read", "role:write",
                "permission:read", "permission:write",
                "system:read", "system:write",
                "data:admin"
            ],
            "is_system": True
        },
        {
            "name": "user_manager",
            "description": "用户管理员",
            "permissions": [
                "user:read", "user:write", "user:delete",
                "role:read"
            ],
            "is_system": True
        },
        {
            "name": "data_manager",
            "description": "数据管理员",
            "permissions": [
                "data:read", "data:write", "data:delete",
                "user:read"
            ],
            "is_system": True
        },
        {
            "name": "user",
            "description": "普通用户",
            "permissions": [
                "user:read",
                "data:read", "data:write"
            ],
            "is_system": True
        },
        {
            "name": "guest",
            "description": "访客",
            "permissions": [
                "data:read"
            ],
            "is_system": True
        }
    ]
    
    # 创建角色记录
    for role_data in roles:
        existing_role = await Role.find_one({"name": role_data["name"]})
        if not existing_role:
            role = Role(**role_data)
            await role.insert()
            print(f"创建角色: {role_data['name']}")
        else:
            print(f"角色已存在: {role_data['name']}")
    
    print("角色初始化完成")


async def init_permission_groups():
    """初始化权限组"""
    print("开始初始化权限组...")
    
    # 创建权限组
    groups = [
        {
            "name": "user_management",
            "description": "用户管理权限组",
            "permissions": ["user:read", "user:write", "user:delete", "user:admin"]
        },
        {
            "name": "role_management",
            "description": "角色管理权限组",
            "permissions": ["role:read", "role:write", "role:delete", "role:admin"]
        },
        {
            "name": "permission_management",
            "description": "权限管理权限组",
            "permissions": ["permission:read", "permission:write", "permission:delete", "permission:admin"]
        },
        {
            "name": "system_management",
            "description": "系统管理权限组",
            "permissions": ["system:read", "system:write", "system:admin"]
        },
        {
            "name": "data_management",
            "description": "数据管理权限组",
            "permissions": ["data:read", "data:write", "data:delete", "data:admin"]
        }
    ]
    
    # 创建权限组记录
    for group_data in groups:
        existing_group = await PermissionGroup.find_one({"name": group_data["name"]})
        if not existing_group:
            group = PermissionGroup(**group_data)
            await group.insert()
            print(f"创建权限组: {group_data['name']}")
        else:
            print(f"权限组已存在: {group_data['name']}")
    
    print("权限组初始化完成")


async def init_all():
    """初始化所有权限相关数据"""
    print("=== 开始初始化权限管理系统 ===")
    
    # 确保数据库连接
    await init_beanie()
    
    # 初始化权限
    await init_system_permissions()
    
    # 初始化角色
    await init_system_roles()
    
    # 初始化权限组
    await init_permission_groups()
    
    print("=== 权限管理系统初始化完成 ===")


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_all()) 