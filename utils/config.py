"""
設定檔管理模組
處理 config.json 的讀取、寫入和驗證
"""
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any


CONFIG_FILE = Path(__file__).parent.parent / "config.json"
CONFIG_EXAMPLE_FILE = Path(__file__).parent.parent / "config.example.json"


def load_config() -> Dict[str, Any]:
    """載入設定檔"""
    if not CONFIG_FILE.exists():
        # 如果設定檔不存在，優先從範本建立；否則用內建預設值建立
        if CONFIG_EXAMPLE_FILE.exists():
            try:
                with open(CONFIG_EXAMPLE_FILE, "r", encoding="utf-8") as f:
                    example = json.load(f)
                save_config(example)
                return example
            except Exception:
                # 回退到內建預設值
                pass

        default_config = get_default_config()
        save_config(default_config)
        return default_config
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 如果啟用自動偵測，更新 Git 使用者設定
        if config.get('git', {}).get('auto_detect', True):
            git_user = detect_git_user()
            if git_user:
                if 'git' not in config:
                    config['git'] = {}
                if 'user' not in config['git']:
                    config['git']['user'] = {}
                config['git']['user']['name'] = git_user['name']
                config['git']['user']['email'] = git_user['email']
        
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"設定檔格式錯誤: {e}")
    except Exception as e:
        raise ValueError(f"無法讀取設定檔: {e}")


def save_config(config: Dict[str, Any]) -> None:
    """儲存設定檔"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise ValueError(f"無法儲存設定檔: {e}")


def get_default_config() -> Dict[str, Any]:
    """取得預設設定檔"""
    return {
        "redmine": {
            "url": "https://redmine.example.com",
            "api_key": "your_api_key_here",
            "user_id": None
        },
        "git": {
            "user": {
                "name": "",
                "email": ""
            },
            "auto_detect": True
        },
        "ai": {
            "provider": "claude",  # "claude"、"gemini" 或 "opencode"
            "claude": {
                "cli_path": "claude",
                "model": "haiku",
                "timeout": 60,
                "system_prompt_file": "prompts/redmine_analysis.txt"
            },
            "gemini": {
                "cli_path": "gemini",
                "model": "gemini-2.0-flash-exp",  # 可選：gemini-2.0-flash-exp, gemini-1.5-pro 等
                "timeout": 60,
                "system_prompt_file": "prompts/redmine_analysis.txt"
            },
            "opencode": {
                "cli_path": "opencode",
                "timeout": 120,
                "system_prompt_file": "prompts/redmine_analysis.txt"
            }
        },
        # 保留舊的 claude 設定以向後相容
        "claude": {
            "use_cli": True,
            "cli_path": "claude",
            "model": "haiku",
            "timeout": 60,
            "output_format": "json",
            "system_prompt_file": "prompts/redmine_analysis.txt"
        },
        "repositories": [],
        "scan_paths": [],
        "default_time_range": "本週",
        "ui": {
            "theme": "light",
            "language": "zh-TW"
        }
    }


def detect_git_user() -> Optional[Dict[str, str]]:
    """
    自動偵測 Git 使用者設定
    先嘗試全域設定，如果沒有則嘗試本地設定
    """
    try:
        # 嘗試讀取全域設定
        name = subprocess.check_output(
            ['git', 'config', '--global', 'user.name'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        email = subprocess.check_output(
            ['git', 'config', '--global', 'user.email'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        
        if name and email:
            return {'name': name, 'email': email}
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    try:
        # 嘗試讀取本地設定
        name = subprocess.check_output(
            ['git', 'config', 'user.name'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        email = subprocess.check_output(
            ['git', 'config', 'user.email'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        
        if name and email:
            return {'name': name, 'email': email}
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return None


def validate_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    驗證設定檔
    回傳 (是否有效, 錯誤訊息)
    """
    # 檢查 Redmine 設定
    redmine = config.get('redmine', {})
    if not redmine.get('url') or redmine.get('url') == 'https://redmine.example.com':
        return False, "請設定 Redmine URL"
    
    if not redmine.get('api_key') or redmine.get('api_key') == 'your_api_key_here':
        return False, "請設定 Redmine API Key"
    
    # 檢查 Git 使用者設定（如果未啟用自動偵測）
    if not config.get('git', {}).get('auto_detect', True):
        git_user = config.get('git', {}).get('user', {})
        if not git_user.get('name') or not git_user.get('email'):
            return False, "請設定 Git 使用者名稱和 Email（或啟用自動偵測）"
    
    return True, None


def get_git_user(config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
    """
    取得當前 Git 使用者資訊
    如果 config 為 None，會自動載入設定檔
    """
    if config is None:
        config = load_config()
    
    # 如果啟用自動偵測，嘗試從 Git 設定檔讀取
    if config.get('git', {}).get('auto_detect', True):
        git_user = detect_git_user()
        if git_user:
            return git_user
    
    # 否則使用設定檔中的值
    git_user = config.get('git', {}).get('user', {})
    name = git_user.get('name', '').strip()
    email = git_user.get('email', '').strip()
    
    if name and email:
        return {'name': name, 'email': email}
    
    return None
