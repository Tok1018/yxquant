"""
安全性增强模块
提供API密钥管理、数据加密、访问控制等安全功能
"""
import os
import json
import hashlib
import hmac
import base64
import secrets
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import bcrypt

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """安全配置"""
    secret_key: str
    jwt_secret: str
    encryption_key: str
    password_salt: str
    token_expiry_hours: int = 24
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    enable_2fa: bool = False
    enable_audit_log: bool = True

@dataclass
class User:
    """用户信息"""
    user_id: str
    username: str
    email: str
    password_hash: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None

@dataclass
class APIKey:
    """API密钥信息"""
    key_id: str
    user_id: str
    key_name: str
    key_hash: str
    permissions: List[str]
    is_active: bool = True
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class EncryptionManager:
    """加密管理器"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        self.fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """创建Fernet加密器"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'yxquant_salt',  # 在生产环境中应该使用随机盐
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False

class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self, db_path: str, encryption_manager: EncryptionManager):
        self.db_path = db_path
        self.encryption_manager = encryption_manager
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            ''')
            
            # 创建API密钥表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    key_name TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # 创建审计日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            ''')
            
            conn.commit()
    
    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> str:
        """创建用户"""
        try:
            user_id = secrets.token_urlsafe(16)
            password_hash = self.encryption_manager.hash_password(password)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (user_id, username, email, password_hash, is_admin)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, email, password_hash, is_admin))
                conn.commit()
            
            logger.info(f"用户创建成功: {username}")
            return user_id
            
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, email, password_hash, is_active, is_admin,
                           created_at, last_login, failed_attempts, locked_until
                    FROM users WHERE username = ?
                ''', (username,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                user = User(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    is_active=bool(row[4]),
                    is_admin=bool(row[5]),
                    created_at=datetime.fromisoformat(row[6]),
                    last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                    failed_attempts=row[8],
                    locked_until=datetime.fromisoformat(row[9]) if row[9] else None
                )
                
                # 检查账户是否被锁定
                if user.locked_until and datetime.now() < user.locked_until:
                    logger.warning(f"用户账户被锁定: {username}")
                    return None
                
                # 检查账户是否激活
                if not user.is_active:
                    logger.warning(f"用户账户未激活: {username}")
                    return None
                
                # 验证密码
                if self.encryption_manager.verify_password(password, user.password_hash):
                    # 重置失败次数
                    self._reset_failed_attempts(user.user_id)
                    # 更新最后登录时间
                    self._update_last_login(user.user_id)
                    return user
                else:
                    # 增加失败次数
                    self._increment_failed_attempts(user.user_id)
                    return None
                    
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None
    
    def _reset_failed_attempts(self, user_id: str):
        """重置失败次数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET failed_attempts = 0, locked_until = NULL
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    def _increment_failed_attempts(self, user_id: str):
        """增加失败次数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET failed_attempts = failed_attempts + 1
                WHERE user_id = ?
            ''', (user_id,))
            
            # 检查是否需要锁定账户
            cursor.execute('SELECT failed_attempts FROM users WHERE user_id = ?', (user_id,))
            failed_attempts = cursor.fetchone()[0]
            
            if failed_attempts >= 5:  # 5次失败后锁定30分钟
                locked_until = datetime.now() + timedelta(minutes=30)
                cursor.execute('''
                    UPDATE users SET locked_until = ?
                    WHERE user_id = ?
                ''', (locked_until.isoformat(), user_id))
            
            conn.commit()
    
    def _update_last_login(self, user_id: str):
        """更新最后登录时间"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            conn.commit()
    
    def create_api_key(self, user_id: str, key_name: str, permissions: List[str], 
                      expires_days: int = None) -> str:
        """创建API密钥"""
        try:
            key_id = secrets.token_urlsafe(16)
            api_key = secrets.token_urlsafe(32)
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            expires_at = None
            if expires_days:
                expires_at = datetime.now() + timedelta(days=expires_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO api_keys (key_id, user_id, key_name, key_hash, permissions, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (key_id, user_id, key_name, json.dumps(permissions), expires_at.isoformat() if expires_at else None))
                conn.commit()
            
            logger.info(f"API密钥创建成功: {key_name}")
            return api_key
            
        except Exception as e:
            logger.error(f"创建API密钥失败: {e}")
            raise
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """验证API密钥"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key_id, user_id, key_name, key_hash, permissions, is_active,
                           created_at, last_used, expires_at
                    FROM api_keys WHERE key_hash = ?
                ''', (key_hash,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                api_key_obj = APIKey(
                    key_id=row[0],
                    user_id=row[1],
                    key_name=row[2],
                    key_hash=row[3],
                    permissions=json.loads(row[4]),
                    is_active=bool(row[5]),
                    created_at=datetime.fromisoformat(row[6]),
                    last_used=datetime.fromisoformat(row[7]) if row[7] else None,
                    expires_at=datetime.fromisoformat(row[8]) if row[8] else None
                )
                
                # 检查密钥是否激活
                if not api_key_obj.is_active:
                    return None
                
                # 检查密钥是否过期
                if api_key_obj.expires_at and datetime.now() > api_key_obj.expires_at:
                    return None
                
                # 更新最后使用时间
                self._update_api_key_usage(api_key_obj.key_id)
                
                return api_key_obj
                
        except Exception as e:
            logger.error(f"验证API密钥失败: {e}")
            return None
    
    def _update_api_key_usage(self, key_id: str):
        """更新API密钥使用时间"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE api_keys SET last_used = ?
                WHERE key_id = ?
            ''', (datetime.now().isoformat(), key_id))
            conn.commit()
    
    def revoke_api_key(self, key_id: str, user_id: str):
        """撤销API密钥"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE api_keys SET is_active = 0
                    WHERE key_id = ? AND user_id = ?
                ''', (key_id, user_id))
                conn.commit()
            
            logger.info(f"API密钥已撤销: {key_id}")
            
        except Exception as e:
            logger.error(f"撤销API密钥失败: {e}")
            raise
    
    def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        """获取用户的API密钥列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key_id, user_id, key_name, key_hash, permissions, is_active,
                           created_at, last_used, expires_at
                    FROM api_keys WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                api_keys = []
                for row in cursor.fetchall():
                    api_keys.append(APIKey(
                        key_id=row[0],
                        user_id=row[1],
                        key_name=row[2],
                        key_hash=row[3],
                        permissions=json.loads(row[4]),
                        is_active=bool(row[5]),
                        created_at=datetime.fromisoformat(row[6]),
                        last_used=datetime.fromisoformat(row[7]) if row[7] else None,
                        expires_at=datetime.fromisoformat(row[8]) if row[8] else None
                    ))
                
                return api_keys
                
        except Exception as e:
            logger.error(f"获取API密钥列表失败: {e}")
            return []
    
    def log_audit_event(self, user_id: str, action: str, resource: str = None,
                       ip_address: str = None, user_agent: str = None, details: str = None):
        """记录审计日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_logs (user_id, action, resource, ip_address, user_agent, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, action, resource, ip_address, user_agent, details))
                conn.commit()
                
        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")

class JWTManager:
    """JWT令牌管理器"""
    
    def __init__(self, secret_key: str, expiry_hours: int = 24):
        self.secret_key = secret_key
        self.expiry_hours = expiry_hours
    
    def create_token(self, user_id: str, username: str, is_admin: bool = False) -> str:
        """创建JWT令牌"""
        try:
            payload = {
                'user_id': user_id,
                'username': username,
                'is_admin': is_admin,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=self.expiry_hours)
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            return token
            
        except Exception as e:
            logger.error(f"创建JWT令牌失败: {e}")
            raise
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("JWT令牌无效")
            return None
        except Exception as e:
            logger.error(f"验证JWT令牌失败: {e}")
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """刷新JWT令牌"""
        try:
            payload = self.validate_token(token)
            if payload:
                return self.create_token(
                    payload['user_id'],
                    payload['username'],
                    payload.get('is_admin', False)
                )
            return None
            
        except Exception as e:
            logger.error(f"刷新JWT令牌失败: {e}")
            return None

class SecurityManager:
    """安全管理器"""
    
    def __init__(self, config: SecurityConfig, db_path: str):
        self.config = config
        self.encryption_manager = EncryptionManager(config.encryption_key)
        self.api_key_manager = APIKeyManager(db_path, self.encryption_manager)
        self.jwt_manager = JWTManager(config.jwt_secret, config.token_expiry_hours)
    
    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> str:
        """创建用户"""
        return self.api_key_manager.create_user(username, email, password, is_admin)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        return self.api_key_manager.authenticate_user(username, password)
    
    def create_jwt_token(self, user: User) -> str:
        """创建JWT令牌"""
        return self.jwt_manager.create_token(user.user_id, user.username, user.is_admin)
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        return self.jwt_manager.validate_token(token)
    
    def create_api_key(self, user_id: str, key_name: str, permissions: List[str], 
                      expires_days: int = None) -> str:
        """创建API密钥"""
        return self.api_key_manager.create_api_key(user_id, key_name, permissions, expires_days)
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """验证API密钥"""
        return self.api_key_manager.validate_api_key(api_key)
    
    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        return self.encryption_manager.encrypt(data)
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        return self.encryption_manager.decrypt(encrypted_data)
    
    def log_audit_event(self, user_id: str, action: str, resource: str = None,
                       ip_address: str = None, user_agent: str = None, details: str = None):
        """记录审计日志"""
        self.api_key_manager.log_audit_event(user_id, action, resource, ip_address, user_agent, details)

# 创建默认安全配置
def create_default_security_config() -> SecurityConfig:
    """创建默认安全配置"""
    return SecurityConfig(
        secret_key=os.getenv('SECRET_KEY', secrets.token_urlsafe(32)),
        jwt_secret=os.getenv('JWT_SECRET', secrets.token_urlsafe(32)),
        encryption_key=os.getenv('ENCRYPTION_KEY', secrets.token_urlsafe(32)),
        password_salt=os.getenv('PASSWORD_SALT', secrets.token_urlsafe(16)),
        token_expiry_hours=24,
        max_login_attempts=5,
        lockout_duration_minutes=30,
        enable_2fa=False,
        enable_audit_log=True
    )

# 创建全局安全管理器实例
security_config = create_default_security_config()
security_manager = SecurityManager(security_config, "data/quant.db")

# 便捷函数
def create_user(username: str, email: str, password: str, is_admin: bool = False) -> str:
    """创建用户的便捷函数"""
    return security_manager.create_user(username, email, password, is_admin)

def authenticate_user(username: str, password: str) -> Optional[User]:
    """用户认证的便捷函数"""
    return security_manager.authenticate_user(username, password)

def create_jwt_token(user: User) -> str:
    """创建JWT令牌的便捷函数"""
    return security_manager.create_jwt_token(user)

def validate_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT令牌的便捷函数"""
    return security_manager.validate_jwt_token(token)

def create_api_key(user_id: str, key_name: str, permissions: List[str], 
                  expires_days: int = None) -> str:
    """创建API密钥的便捷函数"""
    return security_manager.create_api_key(user_id, key_name, permissions, expires_days)

def validate_api_key(api_key: str) -> Optional[APIKey]:
    """验证API密钥的便捷函数"""
    return security_manager.validate_api_key(api_key)

def encrypt_data(data: str) -> str:
    """加密数据的便捷函数"""
    return security_manager.encrypt_data(data)

def decrypt_data(encrypted_data: str) -> str:
    """解密数据的便捷函数"""
    return security_manager.decrypt_data(encrypted_data)

def log_audit_event(user_id: str, action: str, resource: str = None,
                   ip_address: str = None, user_agent: str = None, details: str = None):
    """记录审计日志的便捷函数"""
    security_manager.log_audit_event(user_id, action, resource, ip_address, user_agent, details)
