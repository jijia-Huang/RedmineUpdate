"""
AI 分析服務
整合 Claude Code CLI 和 Gemini CLI 進行 commit 分析
"""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class AnalyzeService:
    """AI 分析服務類別"""

    # CLI 可用性檢查快取（避免每次分析都跑 `--version`，在某些環境會很慢/卡住）
    # key: (provider, resolved_cli_path, use_npx)
    # value: {"ok": bool, "error": Optional[str], "ts": float}
    _CLI_CHECK_CACHE: dict = {}
    _CLI_CHECK_CACHE_TTL_SECONDS = 300.0  # 5 分鐘
    
    def __init__(
        self,
        provider: str = "claude",  # "claude"、"gemini" 或 "opencode"
        cli_path: str = "claude",
        timeout: int = None,  # None 表示使用預設值
        system_prompt_file: str = "prompts/redmine_analysis.txt",
        model: str = "haiku",
    ):
        """
        初始化分析服務
        
        Args:
            provider: AI 服務提供者（"claude"、"gemini" 或 "opencode"）
            cli_path: CLI 執行檔路徑
            timeout: 執行超時時間（秒）
            system_prompt_file: 系統提示詞檔案路徑
            model: 模型名稱（Claude: haiku/sonnet/opus, Gemini: gemini-2.0-flash-exp/gemini-1.5-pro 等, OpenCode: 不使用）
        """
        self.provider = provider.lower()
        self.cli_path = cli_path
        # 根據 provider 設定預設超時時間：Gemini 和 OpenCode 需要更長時間
        if timeout is None:
            if self.provider == "gemini" or self.provider == "opencode":
                self.timeout = 120
            else:
                self.timeout = 60
        else:
            self.timeout = timeout
        self.system_prompt_file = Path(system_prompt_file)
        self.model = model
        # Gemini CLI 在 Windows 上常是透過 npm/nvm 安裝，可能沒有 gemini.exe/cmd 在 PATH。
        # 若偵測不到 gemini，允許 fallback 走 `npx gemini ...`
        self._gemini_use_npx = False

    def _resolve_cli_path(self) -> Optional[str]:
        """
        解析 CLI 執行檔路徑。
        - 若使用者在設定中填的是完整路徑且存在，直接使用。
        - 否則使用 shutil.which() 從 PATH 解析（Windows 會處理 PATHEXT）。
        """
        try:
            raw = (self.cli_path or "").strip()
            if not raw:
                return None

            p = Path(raw)
            if p.is_file():
                return str(p)

            resolved = shutil.which(raw)
            if resolved:
                return resolved

            # Gemini 專用 fallback：如果找不到 gemini 指令，嘗試用 npx 來執行
            if self.provider == "gemini" and raw.lower() == "gemini":
                npx = shutil.which("npx")
                if npx:
                    self._gemini_use_npx = True
                    return npx

            return None
        except Exception:
            return None
    
    def _resolve_gemini_model(self, model: str) -> str:
        """
        解析 Gemini 模型名稱，處理 Auto 選項
        
        Args:
            model: 模型名稱（可能包含 auto 選項）
        
        Returns:
            實際使用的模型名稱
        """
        model_lower = model.lower().strip()
        
        # Auto (Gemini 3) - 優先使用 pro，fallback 到 flash
        if model_lower in ['auto-gemini-3', 'auto (gemini 3)', 'gemini-3-auto']:
            # 優先嘗試 pro，如果不可用 CLI 會自動 fallback
            return 'gemini-3-pro-preview'
        
        # Auto (Gemini 2.5) - 優先使用 pro，fallback 到 flash
        if model_lower in ['auto-gemini-2.5', 'auto (gemini 2.5)', 'gemini-2.5-auto']:
            # 優先嘗試 pro，如果不可用 CLI 會自動 fallback
            return 'gemini-2.5-pro'
        
        # 直接支援的模型名稱（不需要轉換）
        supported_models = [
            'gemini-3-pro-preview',
            'gemini-3-flash-preview',
            'gemini-2.5-pro',
            'gemini-2.5-flash',
            'gemini-2.0-flash-exp',
            'gemini-1.5-pro',
            'gemini-1.5-flash',
        ]
        
        # 如果模型名稱在支援列表中，直接返回
        if model_lower in [m.lower() for m in supported_models]:
            return model  # 保持原始大小寫
        
        # 其他模型直接返回
        return model
    
    def check_cli_available(self) -> tuple[bool, Optional[str]]:
        """
        檢查 CLI 是否可用
        
        Returns:
            (是否可用, 錯誤訊息)
        """
        if self.provider == "claude":
            provider_name = "Claude CLI"
        elif self.provider == "gemini":
            provider_name = "Gemini CLI"
        elif self.provider == "opencode":
            provider_name = "OpenCode CLI"
        else:
            provider_name = "AI CLI"

        resolved = self._resolve_cli_path()
        if not resolved:
            return (
                False,
                f"找不到 {provider_name}（設定值: {self.cli_path!r}）。\n"
                f"請先安裝並確保指令可在終端機直接執行；或在「設定」頁把 CLI 路徑改成完整路徑。\n\n"
                f"你可以用以下指令檢查：\n"
                f"- Windows PowerShell：where {self.cli_path}\n"
                f"- 版本檢查：{self.cli_path} --version\n"
            )

        # 嘗試執行基本命令檢查
        try:
            cache_key = (self.provider, resolved, bool(self._gemini_use_npx))
            now = time.monotonic()
            cached = self._CLI_CHECK_CACHE.get(cache_key)
            if cached and (now - float(cached.get("ts", 0.0)) <= self._CLI_CHECK_CACHE_TTL_SECONDS):
                ok = bool(cached.get("ok", False))
                err = cached.get("error")
                if ok:
                    self.cli_path = resolved
                    return True, None
                return False, err or f"{provider_name} 暫時不可用（快取結果）。"

            # Gemini CLI 跳過 --version 檢查（某些環境會很慢或卡住）
            if self.provider == "gemini":
                logger.info(f"跳過 {provider_name} 的 --version 檢查，直接使用解析後的路徑")
                self.cli_path = resolved
                self._CLI_CHECK_CACHE[cache_key] = {"ok": True, "error": None, "ts": now}
                return True, None

            # 其他 provider（Claude、OpenCode）執行 --version 檢查
            check_cmd = [resolved, "--version"]
            check_timeout = 5
            
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=check_timeout,
            )
            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                stdout = (result.stdout or "").strip()
                msg = stderr or stdout or "未知錯誤"
                err = f"{provider_name} 執行失敗：{msg}"
                self._CLI_CHECK_CACHE[cache_key] = {"ok": False, "error": err, "ts": now}
                return False, err
        except subprocess.TimeoutExpired:
            err = f"{provider_name} 回應超時（`--version` 超過 {check_timeout} 秒）。"
            self._CLI_CHECK_CACHE[cache_key] = {"ok": False, "error": err, "ts": now}
            return False, err
        except FileNotFoundError:
            err = (
                False,
                f"找不到 {provider_name}（解析後路徑: {resolved!r}）。\n"
                f"請在設定填入正確的可執行檔完整路徑，或把它加入 PATH。"
            )
            self._CLI_CHECK_CACHE[cache_key] = {"ok": False, "error": err[1], "ts": now}  # type: ignore[index]
            return err
        except Exception as e:
            err = f"無法執行 {provider_name}: {e}"
            self._CLI_CHECK_CACHE[cache_key] = {"ok": False, "error": err, "ts": now}
            return False, err

        # 成功
        self.cli_path = resolved
        self._CLI_CHECK_CACHE[cache_key] = {"ok": True, "error": None, "ts": now}
        return True, None
    
    def format_commit_data(
        self,
        commits: List[Dict[str, Any]],
        issue_id: int,
        issue_title: str,
        start_date: str,
        end_date: str
    ) -> str:
        """
        格式化 commit 資料為文字格式
        
        Args:
            commits: Commit 列表
            issue_id: Issue ID
            issue_title: Issue 標題
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            格式化後的文字
        """
        commit_lines = []
        for commit in commits:
            commit_lines.append(
                f"Commit: {commit['hash']}\n"
                f"作者: {commit['author']['name']} ({commit['author']['email']})\n"
                f"日期: {commit['date']}\n"
                f"訊息: {commit['message']}\n"
                f"檔案變更: +{commit['files_changed']['added']} "
                f"-{commit['files_changed']['deleted']} "
                f"~{commit['files_changed']['modified']}\n"
            )
        
        return "\n".join(commit_lines)
    
    def load_system_prompt(
        self,
        issue_id: int,
        issue_title: str,
        start_date: str,
        end_date: str,
        commit_list_text: str
    ) -> str:
        """
        載入並格式化系統提示詞
        
        Args:
            issue_id: Issue ID
            issue_title: Issue 標題
            start_date: 開始日期
            end_date: 結束日期
            commit_list_text: Commit 列表文字
        
        Returns:
            格式化後的系統提示詞
        """
        if not self.system_prompt_file.exists():
            raise ValueError(
                f"系統提示詞檔案不存在: {self.system_prompt_file}\n"
                f"請確認檔案路徑正確。"
            )
        
        try:
            with open(self.system_prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()

            # 注意：prompt 內可能包含 JSON 範例（含 `{` `}`）。
            # 不能用 `str.format()`，否則像 `{ "summary": ... }` 會被當成格式化欄位導致 KeyError。
            # 這裡只針對我們定義的少數佔位符做安全替換。
            prompt = prompt_template
            prompt = prompt.replace("{issue_id}", str(issue_id))
            prompt = prompt.replace("{issue_title}", str(issue_title))
            prompt = prompt.replace("{start_date}", str(start_date))
            prompt = prompt.replace("{end_date}", str(end_date))
            prompt = prompt.replace("{commit_list}", str(commit_list_text))

            return prompt
        except Exception as e:
            raise ValueError(f"無法載入系統提示詞: {e}")
    
    def analyze_commits(
        self,
        commits: List[Dict[str, Any]],
        issue_id: int,
        issue_title: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        使用 Claude CLI 分析 commit
        
        Args:
            commits: Commit 列表
            issue_id: Issue ID
            issue_title: Issue 標題
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            分析結果（包含 summary、completed_items 等）
        
        Raises:
            ValueError: 如果 CLI 不可用、執行失敗或輸出格式錯誤
        """
        # 檢查 CLI 是否可用
        available, error_msg = self.check_cli_available()
        if not available:
            raise ValueError(error_msg)
        
        logger.info(f"開始分析 {len(commits)} 個 commit，Issue #{issue_id}")
        
        # 格式化 commit 資料
        commit_list_text = self.format_commit_data(
            commits, issue_id, issue_title, start_date, end_date
        )
        
        # 載入系統提示詞
        system_prompt = self.load_system_prompt(
            issue_id, issue_title, start_date, end_date, commit_list_text
        )
        
        if self.provider == "claude":
            provider_name = "Claude CLI"
        elif self.provider == "gemini":
            provider_name = "Gemini CLI"
        elif self.provider == "opencode":
            provider_name = "OpenCode CLI"
        else:
            provider_name = "AI CLI"
        logger.info(f"系統提示詞已載入，準備呼叫 {provider_name}...")
        
        # 準備 CLI 輸入資料（JSON 格式）
        commit_data_json = json.dumps(
            {
            'commits': commits,
            'issue_id': issue_id,
            'issue_title': issue_title,
            'start_date': start_date,
            'end_date': end_date
            },
            ensure_ascii=False,
            indent=2,
        )

        # 檢查系統提示詞檔案
        if not self.system_prompt_file.exists():
            raise ValueError(f"系統提示詞檔案不存在: {self.system_prompt_file}")

        try:
            # 根據 provider 構建不同的命令
            if self.provider == "claude":
                # Claude CLI 命令格式
                logger.info(f"執行 Claude CLI (模型: {self.model}, 超時: {self.timeout}秒)...")
                cmd = [
                    self.cli_path,
                    "-p",
                    "請分析 stdin 中的 commit JSON，並依照系統提示生成 Redmine 進度回報。",
                    "--output-format",
                    "json",
                    "--system-prompt-file",
                    str(self.system_prompt_file),
                    "--model",
                    self.model,
                ]
            elif self.provider == "opencode":
                # OpenCode CLI 命令格式：opencode run "prompt" --format json
                # 讀取系統提示詞並與用戶提示合併
                with open(self.system_prompt_file, 'r', encoding='utf-8') as f:
                    system_prompt_content = f.read()
                
                # 替換系統提示詞中的佔位符
                system_prompt_content = system_prompt_content.replace("{issue_id}", str(issue_id))
                system_prompt_content = system_prompt_content.replace("{issue_title}", str(issue_title))
                system_prompt_content = system_prompt_content.replace("{start_date}", str(start_date))
                system_prompt_content = system_prompt_content.replace("{end_date}", str(end_date))
                system_prompt_content = system_prompt_content.replace("{commit_list}", commit_list_text)
                
                # OpenCode CLI 使用 run 指令，將系統提示詞和資料合併到提示中
                # 注意：將換行符號替換為空格，避免命令列執行問題
                full_prompt = f"{system_prompt_content}\n\n【輸入資料（commit JSON）】\n{commit_data_json}"
                # 將換行符號替換為空格，保持內容連貫
                full_prompt_single_line = full_prompt.replace('\n', ' ').replace('\r', ' ')
                # 移除多餘的空格（連續空格變為單一空格）
                import re
                full_prompt_single_line = re.sub(r'\s+', ' ', full_prompt_single_line).strip()
                
                logger.info(f"執行 OpenCode CLI (超時: {self.timeout}秒)...")
                cmd = [
                    self.cli_path,
                    "run",
                    full_prompt_single_line,
                    "--format",
                    "json",
                ]
                # 顯示完整命令以便調試（prompt 可能很長，但完整顯示有助於除錯）
                cmd_str = f"{cmd[0]} {cmd[1]} \"{cmd[2]}\" {' '.join(cmd[3:])}"
                logger.info(f"OpenCode CLI 完整命令 (prompt 長度: {len(full_prompt_single_line)} 字元):")
                logger.info(f"  {cmd_str}")
                # 如果 prompt 很長，也顯示前 200 字元預覽
                if len(full_prompt_single_line) > 200:
                    logger.info(f"  Prompt 預覽 (前 200 字元): {full_prompt_single_line[:200]}...")
            
            else:  # gemini
                # Gemini CLI 命令格式
                # 讀取系統提示詞並與用戶提示合併
                with open(self.system_prompt_file, 'r', encoding='utf-8') as f:
                    system_prompt_content = f.read()
                
                # 替換系統提示詞中的佔位符
                system_prompt_content = system_prompt_content.replace("{issue_id}", str(issue_id))
                system_prompt_content = system_prompt_content.replace("{issue_title}", str(issue_title))
                system_prompt_content = system_prompt_content.replace("{start_date}", str(start_date))
                system_prompt_content = system_prompt_content.replace("{end_date}", str(end_date))
                system_prompt_content = system_prompt_content.replace("{commit_list}", commit_list_text)
                
                # Gemini CLI 使用 -p 指定提示
                # 構建完整的提示（系統提示 + 資料）
                # 注意：Gemini CLI 可能不支援系統提示詞檔案，所以我們將系統提示詞和資料合併到提示中
                # 另外：Gemini CLI 可能會啟用工具模式，模型會嘗試呼叫工具（例如 run_shell_command）
                # 在我們這個後端場景不需要、也不允許工具使用，因此用強制規則壓制。
                no_tools_guard = (
                    "【強制規則】\n"
                    "1) 你不得呼叫任何工具/指令/外部能力（包含但不限於 run_shell_command、Bash、File system）。\n"
                    "2) 你必須只輸出「純 JSON」(不要 Markdown、不要額外文字)。\n"
                    "3) JSON 必須包含以下欄位：summary, completed_items, technical_details, blockers, next_steps, estimated_hours, suggested_percent_done。\n"
                    "4) 若無資料請用空陣列 [] 或空字串 \"\"，estimated_hours 用數字，suggested_percent_done 用 0-100 整數。\n"
                )
                full_prompt = f"{no_tools_guard}\n\n{system_prompt_content}\n\n【輸入資料（commit JSON）】\n{commit_data_json}"
                
                # 將換行符號替換為空格，避免命令列執行問題
                import re
                full_prompt_single_line = full_prompt.replace('\n', ' ').replace('\r', ' ')
                # 移除多餘的空格（連續空格變為單一空格）
                full_prompt_single_line = re.sub(r'\s+', ' ', full_prompt_single_line).strip()
                
                # 處理 Auto 模型選項：根據模型名稱選擇實際使用的模型
                actual_model = self._resolve_gemini_model(self.model)
                
                logger.info(f"執行 Gemini CLI (模型: {self.model} -> {actual_model}, 超時: {self.timeout}秒)...")
                if self._gemini_use_npx:
                    # 使用 npx 執行 gemini（避免 PATH 找不到 gemini）
                    # 根據文件：使用 -p 指定 prompt，--output-format json，-m 指定模型
                    cmd = [
                        self.cli_path,
                        "--yes",
                        "gemini",
                        "-p",
                        full_prompt_single_line,
                        "--output-format",
                        "json",
                        "-m",
                        actual_model,
                    ]
                else:
                    # 根據文件：使用 -p 指定 prompt，--output-format json，-m 指定模型
                    cmd = [
                        self.cli_path,
                        "-p",
                        full_prompt_single_line,
                        "--output-format",
                        "json",
                        "-m",
                        actual_model,
                    ]
                
                # 記錄完整命令以便除錯（不記錄完整 prompt，因為可能很長）
                # 構建可讀的命令字串（隱藏 prompt 內容）
                if self._gemini_use_npx:
                    # npx 模式：npx --yes gemini -p [prompt] --output-format json -m model
                    cmd_preview = f"{cmd[0]} {cmd[1]} {cmd[2]} {cmd[3]} [prompt...] {' '.join(cmd[5:])}"
                else:
                    # 直接模式：gemini -p [prompt] --output-format json -m model
                    cmd_preview = f"{cmd[0]} {cmd[1]} [prompt...] {' '.join(cmd[3:])}"
                logger.info(f"Gemini CLI 命令: {cmd_preview}")
            
            # 對於 Gemini CLI（使用 Node.js），抑制 deprecation warnings
            env = os.environ.copy()
            if self.provider == "gemini":
                # 抑制 Node.js deprecation warnings（如 punycode 模組警告）
                env["NODE_NO_WARNINGS"] = "1"
            
            result = subprocess.run(
                cmd,
                input=commit_data_json if self.provider == "claude" else None,  # Claude 用 stdin，Gemini/OpenCode 用參數
                capture_output=True,
                text=True,
                encoding='utf-8',  # 明確指定 UTF-8 編碼
                errors='replace',  # 遇到無法解碼的字元時替換為，而不是拋出異常
                timeout=self.timeout,
                env=env,
            )
            
            logger.info(f"{provider_name} 執行完成 (returncode={result.returncode})")

            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            
            # 對於 OpenCode CLI，輸出是多行 JSON（每行一個 JSON 物件）
            if self.provider == "opencode":
                # 如果 stdout 為空，嘗試從 stderr 讀取（OpenCode 可能將輸出寫到 stderr）
                if not stdout and stderr:
                    logger.info("OpenCode CLI stdout 為空，嘗試從 stderr 讀取輸出")
                    # 檢查 stderr 是否包含 JSON
                    if '{' in stderr or '[' in stderr:
                        stdout = stderr
                        stderr = ""
                        logger.info("從 stderr 找到 JSON 輸出，已切換到 stdout")
                
                # 記錄原始輸出以便除錯
                logger.info(f"OpenCode CLI 原始 stdout 長度: {len(stdout)} 字元")
                logger.info(f"OpenCode CLI 原始 stderr 長度: {len(stderr)} 字元")
                if stdout:
                    logger.info(f"OpenCode CLI stdout 前 500 字元: {stdout[:500]}")
                if stderr:
                    logger.info(f"OpenCode CLI stderr 前 500 字元: {stderr[:500]}")
                
                # 從多行 JSON 中提取所有 type: "text" 的 part.text
                text_parts = []
                all_lines = stdout.split('\n') if stdout else []
                
                for line in all_lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        obj_type = obj.get('type', '')
                        logger.debug(f"OpenCode CLI JSON 物件類型: {obj_type}")
                        
                        if obj_type == 'text' and 'part' in obj:
                            part = obj.get('part', {})
                            if 'text' in part:
                                text_parts.append(part['text'])
                                logger.debug(f"找到 text 片段，長度: {len(part['text'])} 字元")
                        elif obj_type == 'step_finish':
                            # step_finish 表示完成，可以記錄但不需要提取文字
                            logger.info("OpenCode CLI 收到 step_finish 訊號")
                    except json.JSONDecodeError as e:
                        # 記錄無法解析的行以便除錯
                        logger.debug(f"無法解析 JSON 行: {line[:100]}... (錯誤: {e})")
                        continue
                
                # 合併所有文字部分
                if text_parts:
                    stdout = '\n'.join(text_parts)
                    logger.info(f"OpenCode CLI 提取了 {len(text_parts)} 個文字片段，總長度: {len(stdout)} 字元")
                else:
                    logger.warning("OpenCode CLI 沒有找到 type: 'text' 的輸出")
                    # 如果沒有找到 text，但 stdout 有內容，可能是格式不同，嘗試直接使用
                    if stdout and ('{' in stdout or '[' in stdout):
                        logger.info("雖然沒有找到 type: 'text'，但 stdout 包含 JSON，嘗試直接解析")
                    else:
                        stdout = ""
            
            # 對於 Gemini CLI，如果 stdout 為空但 stderr 有內容，可能是輸出到了 stderr
            if self.provider == "gemini" and not stdout and stderr:
                logger.warning("Gemini CLI stdout 為空，但 stderr 有內容，嘗試從 stderr 讀取輸出")
                # 檢查 stderr 是否包含 JSON
                if '{' in stderr or '[' in stderr:
                    stdout = stderr
                    stderr = ""

            if result.returncode != 0:
                # 記錄詳細錯誤資訊
                logger.error(f"{provider_name} 執行失敗 (returncode={result.returncode})")
                logger.error(f"stdout: {stdout[:500] if stdout else '(空)'}")
                logger.error(f"stderr: {stderr[:500] if stderr else '(空)'}")
                
                # 嘗試從 stdout 解析 JSON 錯誤
                error_message = None
                auth_error = False
                
                if stdout:
                    try:
                        # 嘗試解析 stdout 為 JSON
                        stdout_json = json.loads(stdout)
                        if isinstance(stdout_json, dict):
                            # 檢查是否有錯誤資訊
                            if stdout_json.get('is_error') or stdout_json.get('subtype') == 'error':
                                result_text = stdout_json.get('result', '')
                                if 'authentication_error' in result_text or 'OAuth token has expired' in result_text:
                                    auth_error = True
                                    login_cmd = "claude login" if self.provider == "claude" else "gemini login"
                                    error_message = f"{provider_name} 的 OAuth token 已過期。請執行 `{login_cmd}` 重新登入。"
                                elif 'API Error' in result_text:
                                    # 嘗試從 result 中提取 JSON 錯誤
                                    try:
                                        # result 可能是 "API Error: 401 {...}" 格式
                                        if '{' in result_text:
                                            json_start = result_text.find('{')
                                            error_json = json.loads(result_text[json_start:])
                                            if 'error' in error_json and 'message' in error_json['error']:
                                                error_message = f"{provider_name} API 錯誤: {error_json['error']['message']}"
                                                if 'authentication_error' in error_json.get('error', {}).get('type', ''):
                                                    auth_error = True
                                                    login_cmd = "claude login" if self.provider == "claude" else "gemini login"
                                                    error_message = f"{provider_name} 的 OAuth token 已過期。請執行 `{login_cmd}` 重新登入。"
                                    except:
                                        pass
                                    
                                    if not error_message:
                                        error_message = f"{provider_name} API 錯誤: {result_text[:200]}"
                                else:
                                    error_message = result_text[:300] if result_text else None
                    except json.JSONDecodeError:
                        # stdout 不是 JSON，繼續使用原本的處理方式
                        pass
                
                # 構建詳細的錯誤訊息
                if auth_error:
                    login_cmd = "claude login" if self.provider == "claude" else "gemini login"
                    error_parts = [
                        f"❌ {provider_name} 認證失敗",
                        "",
                        "OAuth token 已過期，請重新登入：",
                        "  1. 開啟終端機",
                        f"  2. 執行: {login_cmd}",
                        "  3. 依照指示完成登入",
                        "  4. 重新嘗試分析"
                    ]
                    raise ValueError("\n".join(error_parts))
                
                error_parts = [f"{provider_name} 執行失敗 (退出碼: {result.returncode})"]
                
                if error_message:
                    error_parts.append(f"錯誤訊息: {error_message}")
                elif stderr:
                    # 取 stderr 的前 500 字元（避免訊息過長）
                    stderr_preview = stderr[:500]
                    if len(stderr) > 500:
                        stderr_preview += "..."
                    error_parts.append(f"錯誤訊息: {stderr_preview}")
                
                if stdout and not error_message:
                    # 如果 stdout 有內容但 returncode 不是 0，可能是警告或部分輸出
                    stdout_preview = stdout[:300]
                    if len(stdout) > 300:
                        stdout_preview += "..."
                    error_parts.append(f"輸出: {stdout_preview}")
                
                if not error_message and not stderr and not stdout:
                    error_parts.append("未收到任何錯誤訊息，可能是 CLI 未正確安裝或未登入")
                
                raise ValueError("\n".join(error_parts))
            
            # 解析 JSON 輸出
            try:
                # 記錄完整輸出以便除錯
                logger.info(f"{provider_name} stdout 長度: {len(stdout)} 字元")
                logger.info(f"{provider_name} 完整 stdout:\n{stdout}")
                
                # 嘗試從輸出中提取 JSON（可能包含其他文字）
                output = stdout.strip()
                
                # 如果輸出為空，記錄錯誤
                if not output:
                    logger.error(f"{provider_name} 返回空輸出")
                    raise ValueError(f"{provider_name} 返回空輸出，可能是系統提示詞或輸入格式有問題")
                
                # 清理輸出：移除可能的 dotenv 訊息等前綴
                # Gemini CLI 可能會輸出 [dotenv@...] 等訊息，需要找到實際的 JSON 開始位置
                cleaned_output = output
                if self.provider == "gemini":
                    # 首先嘗試直接尋找 JSON 開始位置（最可靠的方法）
                    json_start_idx = -1
                    for i, char in enumerate(output):
                        if char in ['{', '[']:
                            json_start_idx = i
                            break
                    
                    if json_start_idx > 0:
                        cleaned_output = output[json_start_idx:]
                        logger.info(f"找到 JSON 開始位置（索引 {json_start_idx}），移除前綴文字")
                    else:
                        # 如果找不到 JSON 開始，嘗試過濾掉已知的前綴訊息
                        lines = output.split('\n')
                        filtered_lines = []
                        found_json_start = False
                        
                        for line in lines:
                            # 跳過 dotenv 訊息
                            if '[dotenv@' in line:
                                continue
                            # 記錄 INFO 訊息（模型切換等），但不包含在輸出中
                            if line.startswith('[INFO]'):
                                logger.info(f"Gemini CLI 訊息: {line}")
                                # 檢查是否是模型切換訊息
                                if 'Switched to' in line:
                                    # 提取實際使用的模型名稱
                                    import re
                                    match = re.search(r'Switched to (\S+)', line)
                                    if match:
                                        actual_used_model = match.group(1)
                                        logger.info(f"Gemini CLI 自動切換模型到: {actual_used_model}")
                                continue
                            # 如果這行是 JSON 開始，標記並開始收集
                            stripped = line.strip()
                            if stripped.startswith('{') or stripped.startswith('['):
                                found_json_start = True
                                filtered_lines.append(line)
                            elif found_json_start:
                                # 已經找到 JSON 開始，收集所有後續行
                                filtered_lines.append(line)
                            # 如果還沒找到 JSON 開始，但這行看起來像是系統提示詞標題，跳過
                            elif not found_json_start and (
                                line.strip() == "Here are my core mandates and operational guidelines:" or
                                line.strip().startswith("**Core Mandates:**") or
                                line.strip().startswith("**Operational Guidelines:**") or
                                line.strip().startswith("**") or
                                (line.strip().startswith("-") and not line.strip().startswith("- {"))
                            ):
                                continue
                        
                        if filtered_lines:
                            cleaned_output = '\n'.join(filtered_lines)
                            logger.info(f"過濾後輸出長度: {len(cleaned_output)} 字元（原始: {len(output)} 字元）")
                        else:
                            # 如果過濾後沒有內容，檢查是否輸出被截斷
                            if len(output) < 2000:  # 如果輸出很短，可能是被截斷了
                                logger.warning(f"輸出可能被截斷（長度: {len(output)} 字元），使用原始輸出")
                                logger.warning(f"輸出內容:\n{output}")
                            else:
                                logger.warning("無法找到 JSON 開始位置，使用原始輸出")
                            cleaned_output = output
                
                # 方法 1: 嘗試直接解析整個輸出為 JSON
                try:
                    parsed_output = json.loads(cleaned_output)
                    logger.info("成功直接解析 stdout 為 JSON")
                    
                    # 如果是 Gemini CLI 的 JSON 格式（有 response 欄位）
                    if self.provider == "gemini" and isinstance(parsed_output, dict) and "response" in parsed_output:
                        # Gemini CLI 的 JSON 格式：{"response": "...", "stats": {...}}
                        # 根據文件：response 欄位包含 AI 生成的主要內容
                        response_text = parsed_output.get("response", "")
                        logger.info(f"Gemini CLI 返回的 response 欄位長度: {len(response_text)} 字元")
                        logger.info(f"Gemini CLI 返回的完整 response 內容:\n{response_text}")
                        
                        # 嘗試從 response 中提取 JSON
                        # 方法 1: response 本身就是 JSON 字串
                        try:
                            result = json.loads(response_text)
                            logger.info("成功從 response 欄位解析 JSON")
                        except json.JSONDecodeError:
                            # 方法 2: response 是文字，從中尋找 JSON 區塊
                            json_start = response_text.find('{')
                            json_end = response_text.rfind('}') + 1
                            if json_start != -1 and json_end > json_start:
                                json_str = response_text[json_start:json_end]
                                try:
                                    result = json.loads(json_str)
                                    logger.info("成功從 response 文字中提取 JSON 區塊")
                                except json.JSONDecodeError:
                                    # 方法 3: 檢查是否有 markdown code block
                                    if '```json' in response_text:
                                        json_block_start = response_text.find('```json') + 7
                                        json_block_end = response_text.find('```', json_block_start)
                                        if json_block_end != -1:
                                            json_str = response_text[json_block_start:json_block_end].strip()
                                            result = json.loads(json_str)
                                            logger.info("成功從 response 的 markdown code block 解析 JSON")
                                        else:
                                            raise ValueError("找到 ```json 但沒有找到結束的 ```")
                                    elif '```' in response_text:
                                        code_block_start = response_text.find('```') + 3
                                        code_block_end = response_text.find('```', code_block_start)
                                        if code_block_end != -1:
                                            json_str = response_text[code_block_start:code_block_end].strip()
                                            if json_str.startswith('json\n'):
                                                json_str = json_str[5:]
                                            result = json.loads(json_str)
                                            logger.info("成功從 response 的 code block 解析 JSON")
                                        else:
                                            raise ValueError("找到 ``` 但沒有找到結束的 ```")
                                    else:
                                        raise ValueError(f"無法從 response 欄位中提取 JSON。response 內容（前 1000 字元）:\n{response_text[:1000]}")
                            else:
                                raise ValueError(f"無法在 response 欄位中找到 JSON 格式。response 內容（前 1000 字元）:\n{response_text[:1000]}")
                    else:
                        # Claude CLI 或其他格式，直接使用
                        result = parsed_output
                except json.JSONDecodeError:
                    # 方法 2: 尋找 JSON 區塊（可能被其他文字包圍）
                    # 使用清理後的輸出
                    result = None  # 初始化 result
                    json_start = cleaned_output.find('{')
                    json_end = cleaned_output.rfind('}') + 1
                    
                    if json_start == -1 or json_end == 0:
                        # 方法 3: 檢查是否包含 markdown code block
                        if '```json' in cleaned_output:
                            # 提取 ```json ... ``` 之間的內容
                            json_block_start = cleaned_output.find('```json') + 7
                            json_block_end = cleaned_output.find('```', json_block_start)
                            if json_block_end != -1:
                                json_str = cleaned_output[json_block_start:json_block_end].strip()
                                result = json.loads(json_str)
                                logger.info("成功從 markdown code block 解析 JSON")
                            else:
                                raise ValueError("找到 ```json 但沒有找到結束的 ```")
                        elif '```' in cleaned_output:
                            # 嘗試提取 ``` ... ``` 之間的內容
                            code_block_start = cleaned_output.find('```') + 3
                            code_block_end = cleaned_output.find('```', code_block_start)
                            if code_block_end != -1:
                                json_str = cleaned_output[code_block_start:code_block_end].strip()
                                # 移除可能的語言標記（如 "json"）
                                if json_str.startswith('json\n'):
                                    json_str = json_str[5:]
                                result = json.loads(json_str)
                                logger.info("成功從 code block 解析 JSON")
                            else:
                                raise ValueError("找到 ``` 但沒有找到結束的 ```")
                        else:
                            # 記錄完整輸出以便除錯
                            logger.error(f"無法找到 JSON 格式。完整輸出:\n{cleaned_output[:2000]}")
                            
                            # 對於 Gemini CLI，嘗試從文字輸出中提取 JSON（即使 --output-format json 沒有生效）
                            result = None  # 初始化 result
                            if self.provider == "gemini":
                                # 嘗試找到完整的 JSON（從第一個 { 到最後一個 }）
                                json_start = cleaned_output.find('{')
                                if json_start != -1:
                                    # 從 { 開始，嘗試找到匹配的 }
                                    brace_count = 0
                                    json_end = -1
                                    for i in range(json_start, len(cleaned_output)):
                                        if cleaned_output[i] == '{':
                                            brace_count += 1
                                        elif cleaned_output[i] == '}':
                                            brace_count -= 1
                                            if brace_count == 0:
                                                json_end = i + 1
                                                break
                                    if json_end > json_start:
                                        json_str = cleaned_output[json_start:json_end]
                                        try:
                                            result = json.loads(json_str)
                                            logger.info("成功從文字輸出中提取 JSON（透過括號匹配）")
                                        except json.JSONDecodeError as e:
                                            logger.warning(f"嘗試解析 JSON 失敗: {e}")
                                
                                # 如果仍然沒有找到 JSON
                                if result is None and '{' not in cleaned_output and '[' not in cleaned_output:
                                    # 檢查輸出是否只包含 dotenv 和 INFO 訊息
                                    only_dotenv_info = True
                                    for line in cleaned_output.split('\n'):
                                        line_stripped = line.strip()
                                        if line_stripped and not (
                                            '[dotenv@' in line_stripped or
                                            line_stripped.startswith('[INFO]') or
                                            line_stripped.startswith('Here are my core') or
                                            line_stripped.startswith('**Core Mandates:**') or
                                            line_stripped.startswith('**Operational Guidelines:**')
                                        ):
                                            only_dotenv_info = False
                                            break
                                    
                                    if only_dotenv_info:
                                        raise ValueError(
                                            f"Gemini CLI 只返回了系統訊息，沒有模型回應。\n"
                                            f"輸出內容:\n{cleaned_output[:500]}\n\n"
                                            f"可能原因：\n"
                                            f"1. 模型回應被截斷或超時\n"
                                            f"2. `--output-format json` 沒有生效\n"
                                            f"3. 網路連線問題導致回應不完整\n\n"
                                            f"建議：\n"
                                            f"- 檢查網路連線\n"
                                            f"- 增加超時時間（目前: {self.timeout} 秒）\n"
                                            f"- 檢查 Gemini CLI 版本：`gemini --version`\n"
                                            f"- 嘗試手動執行命令測試：`gemini -p \"test\" --output-format json -m {actual_model}`"
                                        )
                                    else:
                                        raise ValueError(
                                            f"Gemini CLI 沒有返回 JSON 格式。\n"
                                            f"可能原因：\n"
                                            f"1. Gemini CLI 版本不支援 --output-format json（請執行 `gemini --version` 檢查版本）\n"
                                            f"2. 模型沒有遵循指令輸出 JSON 格式\n"
                                            f"3. 輸出被截斷或格式錯誤\n\n"
                                            f"輸出前 1000 字元:\n{cleaned_output[:1000]}\n\n"
                                            f"建議：\n"
                                            f"- 升級 Gemini CLI 到最新版本：`npm update -g @google/gemini-cli`\n"
                                            f"- 確認系統提示詞明確要求輸出 JSON 格式\n"
                                            f"- 嘗試使用不同的模型\n"
                                            f"- 檢查 Gemini CLI 設定檔（~/.gemini/settings.json）中的 output.format 設定"
                                        )
                            
                            # 如果 result 仍然為 None，拋出錯誤
                            if result is None:
                                raise ValueError(
                                    f"無法在輸出中找到 JSON 格式。\n"
                                    f"輸出前 1000 字元:\n{cleaned_output[:1000]}\n\n"
                                    f"請檢查 {provider_name} 的輸出格式是否正確。\n"
                                    f"如果使用 Gemini CLI，請確認：\n"
                                    f"1. 使用了 --output-format json 參數\n"
                                    f"2. 系統提示詞明確要求輸出 JSON 格式\n"
                                    f"3. Gemini CLI 版本支援 JSON 輸出格式"
                                )
                    else:
                        json_str = cleaned_output[json_start:json_end]
                        result = json.loads(json_str)
                        logger.info("成功從輸出中提取 JSON 區塊")
                
                # 記錄實際返回的欄位和完整 JSON 內容
                actual_fields = list(result.keys()) if isinstance(result, dict) else []
                logger.info(f"{provider_name} 返回的 JSON 欄位: {actual_fields}")
                
                # 記錄完整的 JSON 內容（格式化後）
                result_json_str = json.dumps(result, ensure_ascii=False, indent=2)
                logger.info(f"{provider_name} 返回的完整 JSON 內容:\n{result_json_str}")
                
                # 檢查是否是 Claude CLI 的包裝格式（有 'result' 欄位且是字串）
                if isinstance(result, dict) and 'result' in result and isinstance(result.get('result'), str):
                    logger.info("檢測到 Claude CLI 包裝格式，嘗試從 'result' 欄位提取 JSON...")
                    result_text = result['result']
                    
                    # 嘗試從 result 文字中提取 JSON
                    # 方法 1: 尋找 ```json ... ``` 或 ``` ... ```
                    json_data = None
                    
                    if '```json' in result_text:
                        json_start = result_text.find('```json') + 7
                        json_end = result_text.find('```', json_start)
                        if json_end != -1:
                            json_str = result_text[json_start:json_end].strip()
                            try:
                                json_data = json.loads(json_str)
                                logger.info("成功從 result 欄位的 markdown code block 中提取 JSON")
                            except json.JSONDecodeError:
                                pass
                    
                    if json_data is None and '```' in result_text:
                        code_start = result_text.find('```') + 3
                        code_end = result_text.find('```', code_start)
                        if code_end != -1:
                            json_str = result_text[code_start:code_end].strip()
                            # 移除可能的語言標記
                            if json_str.startswith('json\n'):
                                json_str = json_str[5:]
                            try:
                                json_data = json.loads(json_str)
                                logger.info("成功從 result 欄位的 code block 中提取 JSON")
                            except json.JSONDecodeError:
                                pass
                    
                    # 方法 2: 直接尋找 JSON 區塊 { ... }
                    if json_data is None:
                        json_start = result_text.find('{')
                        json_end = result_text.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            json_str = result_text[json_start:json_end]
                            try:
                                json_data = json.loads(json_str)
                                logger.info("成功從 result 欄位中提取 JSON 區塊")
                            except json.JSONDecodeError:
                                pass
                    
                    if json_data:
                        # 使用提取的 JSON 資料
                        result = json_data
                        logger.info(f"成功提取分析結果，欄位: {list(result.keys())}")
                    else:
                        logger.warning("無法從 result 欄位中提取 JSON，result 內容可能是 Markdown 文字")
                        logger.warning(f"result 欄位內容（前 500 字元）:\n{result_text[:500]}")
                
                # 驗證必要欄位
                required_fields = [
                    'summary', 'completed_items', 'technical_details',
                    'blockers', 'next_steps', 'estimated_hours', 'suggested_percent_done'
                ]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    logger.error(f"分析結果缺少必要欄位: {missing_fields}")
                    logger.error(f"實際返回的完整 JSON 內容:\n{result_json_str}")
                    
                    raise ValueError(
                        f"分析結果缺少必要欄位: {', '.join(missing_fields)}\n\n"
                        f"實際返回的欄位: {', '.join(actual_fields) if actual_fields else '(無)'}\n\n"
                        f"請檢查系統提示詞是否正確要求 Claude 返回這些欄位。"
                    )
                
                # 加入分析的 commit 資訊
                result['commits_analyzed'] = [
                    {
                        'hash': c['hash'],
                        'message': c['message'],
                        'date': c['date']
                    }
                    for c in commits
                ]
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失敗。原始輸出: {stdout}")
                raise ValueError(
                    f"無法解析 Claude CLI 的 JSON 輸出: {e}\n"
                    f"原始輸出:\n{stdout}"
                )
        
        except subprocess.TimeoutExpired as e:
            if self.provider == "claude":
                provider_name = "Claude CLI"
            elif self.provider == "gemini":
                provider_name = "Gemini CLI"
            elif self.provider == "opencode":
                provider_name = "OpenCode CLI"
            else:
                provider_name = "AI CLI"
            logger.error(f"{provider_name} 執行超時（超過 {self.timeout} 秒）")
            # 記錄命令（隱藏 prompt 內容）
            if 'cmd' in locals():
                if self.provider == "gemini":
                    if self._gemini_use_npx:
                        cmd_preview = f"{cmd[0]} {cmd[1]} {cmd[2]} {cmd[3]} [prompt...] {' '.join(cmd[5:])}"
                    else:
                        cmd_preview = f"{cmd[0]} {cmd[1]} [prompt...] {' '.join(cmd[3:])}"
                    logger.error(f"命令: {cmd_preview}")
                else:
                    logger.error(f"命令: {' '.join(cmd)}")
            else:
                logger.error("命令: N/A")
            raise ValueError(
                f"{provider_name} 執行超時（超過 {self.timeout} 秒）。\n"
                f"可能原因：\n"
                f"1. 網路連線不穩定\n"
                f"2. 模型回應時間過長\n"
                f"3. 輸入資料過大\n\n"
                f"建議：\n"
                f"- 在設定中增加超時時間（目前: {self.timeout} 秒）\n"
                f"- 檢查網路連線\n"
                f"- 嘗試使用較快的模型（如 gemini-2.5-flash）"
            )
        
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            logger.error(f"分析 commit 時發生錯誤: {e}")
            raise ValueError(f"分析失敗: {e}")
        
        finally:
            # `system_prompt` 變數保留以利未來除錯或擴充（目前不需要臨時檔）
            _ = system_prompt
