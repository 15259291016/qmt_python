/**
 * 无感刷新认证管理
 */
class AuthManager {
    constructor() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.baseURL = '/api';
    }

    /**
     * 设置token
     */
    setTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }

    /**
     * 清除token
     */
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    /**
     * 发送API请求，自动处理无感刷新
     */
    async request(url, options = {}) {
        if (!this.accessToken) {
            throw new Error('No access token available');
        }

        // 设置默认headers
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.accessToken}`,
            ...options.headers
        };

        try {
            const response = await fetch(`${this.baseURL}${url}`, {
                ...options,
                headers
            });

            // 检查响应头中是否有新的token
            const newAccessToken = response.headers.get('X-New-Access-Token');
            const newRefreshToken = response.headers.get('X-New-Refresh-Token');
            const tokenRefreshed = response.headers.get('X-Token-Refreshed');

            if (tokenRefreshed === 'true' && newAccessToken && newRefreshToken) {
                console.log('Token automatically refreshed');
                this.setTokens(newAccessToken, newRefreshToken);
            }

            if (response.status === 401) {
                // token已过期，尝试手动刷新
                const refreshed = await this.refreshTokenManually();
                if (refreshed) {
                    // 重新发送原请求
                    return this.request(url, options);
                } else {
                    // 刷新失败，跳转到登录页
                    this.clearTokens();
                    window.location.href = '/login';
                    return;
                }
            }

            return response;
        } catch (error) {
            console.error('Request failed:', error);
            throw error;
        }
    }

    /**
     * 手动刷新token
     */
    async refreshTokenManually() {
        if (!this.refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken
                })
            });

            if (response.ok) {
                const data = await response.json();
                const { access_token, refresh_token } = data.data.tokens;
                this.setTokens(access_token, refresh_token);
                return true;
            }
        } catch (error) {
            console.error('Manual token refresh failed:', error);
        }

        return false;
    }

    /**
     * 登录
     */
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            const { access_token, refresh_token } = data.data.tokens;
            this.setTokens(access_token, refresh_token);
            return data;
        } else {
            throw new Error('Login failed');
        }
    }

    /**
     * 登出
     */
    async logout() {
        try {
            await this.request('/auth/logout', { method: 'POST' });
        } catch (error) {
            console.error('Logout request failed:', error);
        } finally {
            this.clearTokens();
        }
    }

    /**
     * 获取用户资料
     */
    async getProfile() {
        const response = await this.request('/auth/profile');
        if (response.ok) {
            const data = await response.json();
            
            // 检查响应中是否有token刷新信息
            if (data.data.token_refreshed) {
                console.log('Token was refreshed during profile request');
                const { access_token, refresh_token } = data.data.new_tokens;
                this.setTokens(access_token, refresh_token);
            }
            
            return data;
        } else {
            throw new Error('Failed to get profile');
        }
    }

    /**
     * 更新用户资料
     */
    async updateProfile(profileData) {
        const response = await this.request('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });

        if (response.ok) {
            const data = await response.json();
            
            // 检查响应中是否有token刷新信息
            if (data.data.token_refreshed) {
                console.log('Token was refreshed during profile update');
                const { access_token, refresh_token } = data.data.new_tokens;
                this.setTokens(access_token, refresh_token);
            }
            
            return data;
        } else {
            throw new Error('Failed to update profile');
        }
    }
}

// 创建全局认证管理器实例
window.authManager = new AuthManager();

// 使用示例
async function exampleUsage() {
    try {
        // 登录
        await authManager.login('username', 'password');
        
        // 获取用户资料（会自动处理无感刷新）
        const profile = await authManager.getProfile();
        console.log('User profile:', profile);
        
        // 更新用户资料（会自动处理无感刷新）
        const updatedProfile = await authManager.updateProfile({
            full_name: 'New Name'
        });
        console.log('Updated profile:', updatedProfile);
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// 页面加载时检查token状态
document.addEventListener('DOMContentLoaded', () => {
    if (authManager.accessToken) {
        // 验证token是否有效
        authManager.getProfile().catch(() => {
            // token无效，清除并跳转到登录页
            authManager.clearTokens();
            window.location.href = '/login';
        });
    }
}); 