#!/usr/bin/env python3
"""
超级管理员初始化脚本
用于创建超级管理员用户和角色
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.tornadoapp.db.dbUtil import init_beanie, demo_db_client
from modules.tornadoapp.model.user_model import User
from modules.tornadoapp.model.permission_model import Role, Permission, UserRole
from modules.tornadoapp.utils.auth import AuthUtils


async def init_super_admin():
    """初始化超级管理员"""
    print("开始初始化超级管理员...")
    
    # 初始化数据库连接
    await init_beanie()
    
    # 超级管理员配置
    SUPER_ADMIN_USERNAME = "superadmin"
    SUPER_ADMIN_EMAIL = "superadmin@qmt.com"
    SUPER_ADMIN_PASSWORD = "SuperAdmin@2024"  # 请在生产环境中修改
    SUPER_ADMIN_FULL_NAME = "超级管理员"
    
    try:
        # 1. 检查超级管理员用户是否已存在
        existing_user = await User.find_one({"username": SUPER_ADMIN_USERNAME})
        if existing_user:
            print(f"超级管理员用户 {SUPER_ADMIN_USERNAME} 已存在")
            # 确保用户是超级管理员
            if not existing_user.is_super_admin:
                existing_user.is_super_admin = True
                existing_user.is_admin = True
                existing_user.updated_at = datetime.utcnow()
                await existing_user.save()
                print("✅ 已将用户设置为超级管理员")
            return existing_user
        
        # 2. 创建超级管理员用户
        super_admin_user = User(
            username=SUPER_ADMIN_USERNAME,
            email=SUPER_ADMIN_EMAIL,
            password_hash=AuthUtils.hash_password(SUPER_ADMIN_PASSWORD),
            full_name=SUPER_ADMIN_FULL_NAME,
            is_active=True,
            is_admin=True,  # 设置为管理员
            is_super_admin=True,  # 设置为超级管理员
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await super_admin_user.insert()
        print(f"✅ 超级管理员用户创建成功: {SUPER_ADMIN_USERNAME}")
        
        # 3. 检查或创建超级管理员角色
        super_admin_role = await Role.find_one({"name": "super_admin"})
        if not super_admin_role:
            # 创建超级管理员角色
            super_admin_role = Role(
                name="super_admin",
                description="超级管理员，拥有系统所有权限",
                permissions=[
                    "user:read", "user:write", "user:delete", "user:admin",
                    "role:read", "role:write", "role:delete", "role:admin",
                    "permission:read", "permission:write", "permission:delete", "permission:admin",
                    "system:read", "system:write", "system:admin",
                    "data:read", "data:write", "data:delete", "data:admin"
                ],
                is_active=True,
                is_system=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=str(super_admin_user.id)
            )
            await super_admin_role.insert()
            print("✅ 超级管理员角色创建成功")
        else:
            print("超级管理员角色已存在")
        
        # 4. 为超级管理员用户分配超级管理员角色
        existing_user_role = await UserRole.find_one({
            "user_id": str(super_admin_user.id),
            "role_id": str(super_admin_role.id),
            "is_active": True
        })
        
        if not existing_user_role:
            user_role = UserRole(
                user_id=str(super_admin_user.id),
                role_id=str(super_admin_role.id),
                assigned_by=str(super_admin_user.id),  # 自己分配给自己
                assigned_at=datetime.utcnow(),
                is_active=True
            )
            await user_role.insert()
            print("✅ 超级管理员角色分配成功")
        else:
            print("超级管理员角色已分配")
        
        print("\n🎉 超级管理员初始化完成！")
        print(f"用户名: {SUPER_ADMIN_USERNAME}")
        print(f"邮箱: {SUPER_ADMIN_EMAIL}")
        print(f"密码: {SUPER_ADMIN_PASSWORD}")
        print(f"角色: {super_admin_role.name}")
        print(f"权限数量: {len(super_admin_role.permissions)}")
        print(f"超级管理员状态: {super_admin_user.is_super_admin}")
        print("\n⚠️  请在生产环境中修改默认密码！")
        
        return super_admin_user
        
    except Exception as e:
        print(f"❌ 超级管理员初始化失败: {e}")
        raise


async def verify_super_admin():
    """验证超级管理员权限"""
    print("\n验证超级管理员权限...")
    
    try:
        # 查找超级管理员用户
        super_admin_user = await User.find_one({"username": "superadmin"})
        if not super_admin_user:
            print("❌ 超级管理员用户不存在")
            return False
        
        # 检查超级管理员状态
        if not super_admin_user.is_super_admin:
            print("❌ 用户不是超级管理员")
            return False
        
        # 查找超级管理员角色
        super_admin_role = await Role.find_one({"name": "super_admin"})
        if not super_admin_role:
            print("❌ 超级管理员角色不存在")
            return False
        
        # 检查用户角色分配
        user_role = await UserRole.find_one({
            "user_id": str(super_admin_user.id),
            "role_id": str(super_admin_role.id),
            "is_active": True
        })
        
        if not user_role:
            print("❌ 超级管理员角色未分配")
            return False
        
        print("✅ 超级管理员权限验证成功")
        print(f"用户ID: {super_admin_user.id}")
        print(f"角色ID: {super_admin_role.id}")
        print(f"权限列表: {super_admin_role.permissions}")
        print(f"超级管理员状态: {super_admin_user.is_super_admin}")
        
        return True
        
    except Exception as e:
        print(f"❌ 权限验证失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 50)
    print("超级管理员初始化工具")
    print("=" * 50)
    
    try:
        # 初始化超级管理员
        await init_super_admin()
        
        # 验证权限
        await verify_super_admin()
        
        print("\n" + "=" * 50)
        print("初始化完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 