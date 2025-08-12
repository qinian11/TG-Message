#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群发功能模块 - 完整优化版（中文日志 + FloodWait 自动等待 + 冻结跳过 + 随机延时）
使用说明：
- 将本文件保存为 group_sender.py，程序中会导入。
- 需要已有 session 文件 和 config.json（包含 api_id & api_hash）。
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import asyncio
import os
import glob
from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
import json
from datetime import datetime
import random
import traceback

class GroupSender:
    """群发功能类 - 完整优化版"""
    def __init__(self, parent_frame, account_manager, log_callback):
        self.parent_frame = parent_frame
        self.account_manager = account_manager
        self.log_callback = log_callback

        # 状态
        self.is_sending = False
        self.session_clients = {}   # { session_name: TelegramClient }
        self.account_groups = {}    # { session_name: [group dicts] }
        self.account_info = {}      # { session_name: {'account_id', 'phone', 'session_file'} }
        self.loop = None
        self.loop_thread = None
        self.account_tasks = {}     # { session_name: asyncio.Task }

        # 启动事件循环线程
        self._start_event_loop()

        # UI
        self.create_ui()

    # --------------------- 日志辅助 ---------------------
    def log_with_timestamp(self, message, account_id=None, phone=None):
        """带时间戳的日志记录（中文）"""
        timestamp = datetime.now().strftime("%Y年%m月%d日%H时%M分%S秒")
        if account_id is not None and phone is not None:
            formatted = f"[{timestamp}] {message} - 账号{account_id}({phone})"
        else:
            formatted = f"[{timestamp}] {message}"
        if self.log_callback:
            self.log_callback(formatted)

    def _start_event_loop(self):
        """在独立线程中运行 asyncio loop"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        # 等待 loop 就绪
        while self.loop is None:
            time.sleep(0.01)

    # --------------------- UI ---------------------
    def create_ui(self):
        """创建界面（保留你原样式）"""
        main_frame = ttk.Frame(self.parent_frame, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="多账号并发群发功能（已优化）", font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 5))

        main_container = ttk.Frame(main_frame)
        main_container.pack(fill='both', expand=True)
        main_container.columnconfigure(0, weight=2)
        main_container.columnconfigure(1, weight=3)

        # 左侧（消息 + 加群）
        left_container = ttk.Frame(main_container)
        left_container.grid(row=0, column=0, sticky='nsew', padx=(0,5))

        # 消息区
        message_frame = ttk.LabelFrame(left_container, text="消息内容", padding="5")
        message_frame.pack(fill='x', pady=(0,5))
        self.message_text = scrolledtext.ScrolledText(message_frame, height=3)
        self.message_text.pack(fill='both', expand=True, pady=(0,5))

        settings_frame = ttk.Frame(message_frame)
        settings_frame.pack(fill='x', pady=(0,5))
        ttk.Label(settings_frame, text="轮数:").pack(side='left')
        self.rounds_var = tk.StringVar(value="1")
        ttk.Entry(settings_frame, textvariable=self.rounds_var, width=6).pack(side='left', padx=(2,8))
        ttk.Label(settings_frame, text="轮次间隔(s):").pack(side='left')
        self.delay_var = tk.StringVar(value="200")
        ttk.Entry(settings_frame, textvariable=self.delay_var, width=6).pack(side='left', padx=(2,8))
        ttk.Label(settings_frame, text="账号间隔(s):").pack(side='left')
        self.account_delay_var = tk.StringVar(value="10")
        ttk.Entry(settings_frame, textvariable=self.account_delay_var, width=6).pack(side='left', padx=(2,0))

        button_frame = ttk.Frame(message_frame)
        button_frame.pack(fill='x')
        self.send_button = ttk.Button(button_frame, text="🚀 一键群发", command=self.start_auto_sending)
        self.send_button.pack(side='left', padx=(0,5))
        self.stop_button = ttk.Button(button_frame, text="⏹ 停止", command=self.stop_sending, state='disabled')
        self.stop_button.pack(side='left')

        # 加群区
        join_frame = ttk.LabelFrame(left_container, text="加群功能", padding="5")
        join_frame.pack(fill='both', expand=True, pady=(0,5))
        ttk.Label(join_frame, text="群组链接/ID (每行一条):").pack(anchor='w', pady=(0,2))
        self.group_input = tk.Text(join_frame, height=4, wrap=tk.WORD)
        self.group_input.pack(fill='both', expand=True, pady=(0,5))
        options_frame = ttk.Frame(join_frame); options_frame.pack(fill='x', pady=(0,5))
        self.join_all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="所有账号加群", variable=self.join_all_var).pack(anchor='w')
        self.auto_approve_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="自动通过申请（需具有管理员接口）", variable=self.auto_approve_var).pack(anchor='w')

        join_buttons_frame = ttk.Frame(join_frame); join_buttons_frame.pack(fill='x', pady=(5,0))
        row1 = ttk.Frame(join_buttons_frame); row1.pack(fill='x', pady=(0,2))
        self.join_button = ttk.Button(row1, text="🔗 一键加群", command=self.start_join_groups); self.join_button.pack(side='left', fill='x', expand=True, padx=(0,2))
        self.scan_button = ttk.Button(row1, text="🔍 扫描Session", command=self.scan_sessions); self.scan_button.pack(side='left', fill='x', expand=True, padx=(2,0))
        row2 = ttk.Frame(join_buttons_frame); row2.pack(fill='x')
        self.connect_button = ttk.Button(row2, text="🔌 连接账号", command=self.connect_all_sessions); self.connect_button.pack(side='left', fill='x', expand=True, padx=(0,2))
        self.groups_button = ttk.Button(row2, text="📋 获取群组", command=self.get_all_groups); self.groups_button.pack(side='left', fill='x', expand=True, padx=(2,0))

        # 右侧 状态
        status_frame = ttk.LabelFrame(main_container, text="账号状态", padding="3")
        status_frame.grid(row=0, column=1, sticky='nsew')
        columns = ('account_id','session','phone','groups','current_group','status')
        self.status_tree = ttk.Treeview(status_frame, columns=columns, show='headings', height=15)
        for col, text in zip(columns, ['账号','Session','手机号','群数','当前群组','状态']):
            self.status_tree.heading(col, text=text)
        self.status_tree.column('account_id', width=60); self.status_tree.column('session', width=100)
        self.status_tree.column('phone', width=120); self.status_tree.column('groups', width=60)
        self.status_tree.column('current_group', width=180); self.status_tree.column('status', width=150)
        status_scrollbar = ttk.Scrollbar(status_frame, orient='vertical', command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=status_scrollbar.set)
        self.status_tree.pack(side='left', fill='both', expand=True); status_scrollbar.pack(side='right', fill='y')

        # 进度
        progress_frame = ttk.Frame(main_frame); progress_frame.pack(fill='x', pady=(5,0))
        self.progress_var = tk.StringVar(value="就绪 - 点击'一键群发'开始")
        ttk.Label(progress_frame, textvariable=self.progress_var, font=('Arial',9)).pack(pady=(3,2))
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate'); self.progress_bar.pack(fill='x', pady=(0,3))

    # --------------------- 自动工作流 ---------------------
    def start_auto_sending(self):
        """一键群发：扫描 -> 连接 -> 获取群组 -> 并发群发"""
        if self.is_sending:
            messagebox.showwarning("警告", "群发已在进行中")
            return

        message = self.message_text.get(1.0, tk.END).strip()
        if not message:
            messagebox.showwarning("警告", "请输入要发送的消息")
            return

        try:
            rounds = int(self.rounds_var.get())
            delay = int(self.delay_var.get())
            account_delay = int(self.account_delay_var.get())
        except ValueError:
            messagebox.showerror("错误", "轮数和间隔必须是数字")
            return

        if rounds <= 0 or delay < 0 or account_delay < 0:
            messagebox.showerror("错误", "轮数必须大于0，间隔不能为负数")
            return

        self.is_sending = True
        self.send_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.start()
        self.progress_var.set("正在执行自动群发流程...")

        future = asyncio.run_coroutine_threadsafe(
            self._auto_full_workflow(message, rounds, delay, account_delay),
            self.loop
        )

        def _checker():
            if future.done():
                try:
                    future.result()
                except Exception as e:
                    self.log_with_timestamp(f"自动群发过程出错：{str(e)}")
                finally:
                    self.sending_finished()
            else:
                self.parent_frame.after(100, _checker)
        _checker()

    async def _auto_full_workflow(self, message, rounds, delay, account_delay):
        """扫描 -> 连接 -> 获取群组 -> 并发发送"""
        try:
            self.progress_var.set("正在扫描Session文件...")
            self.log_with_timestamp("开始自动群发流程：扫描Session文件")
            await self._scan_sessions_async()
            if not self.account_info:
                self.log_with_timestamp("未找到可用的 Session 文件")
                return

            self.progress_var.set("正在连接账号...")
            self.log_with_timestamp("连接所有账号中...")
            await self._connect_sessions_async()
            if not self.session_clients:
                self.log_with_timestamp("没有成功连接的账号")
                return

            self.progress_var.set("正在获取群组列表...")
            self.log_with_timestamp("获取群组列表中...")
            await self._get_groups_async()

            # 检查是否至少有一个账号有群组
            available_accounts = [s for s, g in self.account_groups.items() if s in self.session_clients and g]
            if not available_accounts:
                self.log_with_timestamp("没有找到可用的群组")
                return

            self.progress_var.set("开始群发消息...")
            self.log_with_timestamp(f"找到 {len(available_accounts)} 个可用账号，开始群发")
            await self._concurrent_send_workflow(message, rounds, delay, account_delay)

        except Exception as e:
            self.log_with_timestamp(f"自动群发流程出错：{str(e)}\n{traceback.format_exc()}")

    # --------------------- 扫描 / 连接 / 获取群组 ---------------------
    def scan_sessions(self):
        """手动触发扫描Session"""
        if self.is_sending:
            return
        future = asyncio.run_coroutine_threadsafe(self._scan_sessions_async(), self.loop)
        def _c():
            if future.done():
                try: future.result()
                except Exception as e: self.log_with_timestamp(f"扫描Session失败：{e}")
            else:
                self.parent_frame.after(100, _c)
        _c()

    async def _scan_sessions_async(self):
        """异步扫描当前目录下的 .session 文件"""
        try:
            self.account_info.clear()
            self.status_tree.delete(*self.status_tree.get_children())
            session_files = glob.glob("*.session")
            if not session_files:
                self.log_with_timestamp("未找到任何 Session 文件")
                return

            aid = 1

            def insert_tree_item(sn, aid_value):
                self.status_tree.insert('', 'end', values=(aid_value, sn, '待连接', '0', '', '已扫描'))

            for sf in session_files:
                name = sf[:-8] if sf.endswith('.session') else os.path.splitext(sf)[0]
                self.account_info[name] = {'account_id': aid, 'phone': '待连接', 'session_file': sf}
                # UI 添加，使用局部函数替代 lambda 捕获变量
                self.parent_frame.after(0, insert_tree_item, name, aid)
                aid += 1

            self.log_with_timestamp(f"扫描完成，找到 {len(session_files)} 个 Session 文件")
        except Exception as e:
            self.log_with_timestamp(f"扫描Session文件出错：{str(e)}")
    def connect_all_sessions(self):
        """手动连接所有 Session"""
        if self.is_sending:
            return
        future = asyncio.run_coroutine_threadsafe(self._connect_sessions_async(), self.loop)
        def _c():
            if future.done():
                try: future.result()
                except Exception as e: self.log_with_timestamp(f"连接Session失败：{e}")
            else:
                self.parent_frame.after(100, _c)
        _c()

    async def _connect_sessions_async(self):
        """异步连接所有 session（使用 config.json 的 api_id/api_hash）"""
        try:
            cfg = 'config.json'
            if not os.path.exists(cfg):
                self.log_with_timestamp("config.json 文件不存在，无法连接账号")
                return
            with open(cfg, 'r', encoding='utf-8') as f:
                config = json.load(f)
            api_id = config.get('api_id'); api_hash = config.get('api_hash')
            if not api_id or not api_hash:
                self.log_with_timestamp("config.json 中缺少 API 信息")
                return

            for session_name, info in list(self.account_info.items()):
                # 跳过已连接
                if session_name in self.session_clients:
                    continue
                try:
                    client = TelegramClient(session_name, api_id, api_hash)
                    await client.connect()
                    if await client.is_user_authorized():
                        me = await client.get_me()
                        phone = me.phone if hasattr(me, 'phone') and me.phone else '未知'
                        self.account_info[session_name]['phone'] = phone
                        self.session_clients[session_name] = client
                        # 更新 UI
                        for item in self.status_tree.get_children():
                            values = list(self.status_tree.item(item)['values'])
                            if values[1] == session_name:
                                values[2] = phone; values[5] = '已连接'
                                self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                                break
                        self.log_with_timestamp("账号连接成功", info['account_id'], phone)
                    else:
                        await client.disconnect()
                        self.log_with_timestamp(f"Session {session_name} 未授权（需手动登录）")
                        for item in self.status_tree.get_children():
                            values = list(self.status_tree.item(item)['values'])
                            if values[1] == session_name:
                                values[5] = '未授权'
                                self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                                break
                except Exception as e:
                    self.log_with_timestamp(f"连接 {session_name} 失败：{str(e)}")
                    for item in self.status_tree.get_children():
                        values = list(self.status_tree.item(item)['values'])
                        if values[1] == session_name:
                            values[5] = '连接失败'
                            self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                            break
            self.log_with_timestamp(f"连接完成，成功连接 {len(self.session_clients)} 个账号")
        except Exception as e:
            self.log_with_timestamp(f"连接Session过程出错：{str(e)}")

    def get_all_groups(self):
        """手动触发：获取所有已连接账号的群组"""
        if self.is_sending:
            return
        future = asyncio.run_coroutine_threadsafe(self._get_groups_async(), self.loop)
        def _c():
            if future.done():
                try: future.result()
                except Exception as e: self.log_with_timestamp(f"获取群组失败：{e}")
            else:
                self.parent_frame.after(100, _c)
        _c()

    async def _get_groups_async(self):
        """异步获取群组和频道列表"""
        try:
            for session_name, client in list(self.session_clients.items()):
                if not client.is_connected():
                    continue
                try:
                    dialogs = await client.get_dialogs()
                    groups = []
                    for dialog in dialogs:
                        try:
                            is_group = getattr(dialog, 'is_group', False)
                            is_channel = getattr(dialog, 'is_channel', False)
                            if is_group or is_channel:
                                groups.append({
                                    'id': dialog.id,
                                    'title': getattr(dialog, 'title', '未知'),
                                    'username': getattr(dialog.entity, 'username', None) if hasattr(dialog, 'entity') else None
                                })
                        except Exception:
                            continue
                    self.account_groups[session_name] = groups
                    # 更新 UI
                    for item in self.status_tree.get_children():
                        values = list(self.status_tree.item(item)['values'])
                        if values[1] == session_name:
                            values[3] = str(len(groups)); values[5] = f'已获取{len(groups)}个群组'
                            self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                            break
                    aid = self.account_info[session_name]['account_id']
                    phone = self.account_info[session_name]['phone']
                    self.log_with_timestamp(f"获取到 {len(groups)} 个群组", aid, phone)
                except Exception as e:
                    self.log_with_timestamp(f"获取 {session_name} 群组失败：{str(e)}")
        except Exception as e:
            self.log_with_timestamp(f"获取群组过程出错：{str(e)}")

    # --------------------- 加群（优化版） ---------------------
    def start_join_groups(self):
        """触发一键加群"""
        if self.is_sending:
            messagebox.showwarning("警告", "群发进行中，无法执行加群")
            return
        group_input = self.group_input.get("1.0", tk.END).strip()
        if not group_input:
            messagebox.showwarning("警告", "请输入群组链接或 ID")
            return
        links = [l.strip() for l in group_input.splitlines() if l.strip()]
        if not links:
            messagebox.showwarning("警告", "请输入有效的群组链接或 ID")
            return
        if not self.session_clients:
            messagebox.showwarning("警告", "没有已连接的账号，请先连接账号")
            return

        self.log_with_timestamp(f"开始加群操作，共 {len(links)} 个群组，{len(self.session_clients)} 个账号")
        future = asyncio.run_coroutine_threadsafe(self._join_groups_async(links), self.loop)
        def _c():
            if future.done():
                try: future.result(); self.log_with_timestamp("加群操作完成")
                except Exception as e: self.log_with_timestamp(f"加群操作失败：{e}")
            else:
                self.parent_frame.after(100, _c)
        _c()

    async def _join_groups_async(self, group_links):
        """异步加群（中文化 + FloodWait 自动等待 + 冻结跳过 + 随机延时）"""
        try:
            join_all = self.join_all_var.get()
            for link in group_links:
                if not self.is_sending and self.send_button['state'] == 'disabled':
                    # 如果处于整体群发流程中（被 start_auto_sending 标记），保持 is_sending True，
                    # 单独按 "一键加群" 时 is_sending 通常为 False。
                    pass
                self.log_with_timestamp(f"开始处理群组：{link}")
                # 选定的客户端集合
                if join_all:
                    selected = list(self.session_clients.items())
                else:
                    selected = list(self.session_clients.items())[:1]

                for session_name, client in selected:
                    # 当用户在全自动流程中调用，is_sending 代表整体流程，仍然允许加群。
                    phone = self.account_info.get(session_name, {}).get('phone', '未知')
                    account_id = self.account_info.get(session_name, {}).get('account_id')

                    # 检查 client 状态
                    if not client or not client.is_connected():
                        self.log_with_timestamp("客户端未连接或已断开，跳过该账号", account_id, phone)
                        continue

                    try:
                        # 处理 t.me 链接 / 私有邀请 / username / id
                        if link.startswith('https://t.me/') or link.startswith('http://t.me/'):
                            username = link.rstrip('/').split('/')[-1]
                            # 私密邀请（+开头）或 joinchat/hash
                            if username.startswith('+') or username.startswith('joinchat') or len(username) > 32:
                                # 私有邀请或 joinchat
                                from telethon.tl import functions
                                invite_hash = username.lstrip('+')
                                await client(functions.messages.ImportChatInviteRequest(invite_hash))
                            else:
                                # 公开群用户名
                                from telethon.tl import functions
                                await client(functions.channels.JoinChannelRequest(username))
                        else:
                            # 直接 @username 或 id
                            target = link
                            if target.startswith('@'):
                                target = target[1:]
                                from telethon.tl import functions
                                await client(functions.channels.JoinChannelRequest(target))
                            else:
                                # 尝试按 id 加入（有时需 JoinChannelRequest）
                                try:
                                    from telethon.tl import functions
                                    await client(functions.channels.JoinChannelRequest(int(target)))
                                except Exception:
                                    from telethon.tl import functions
                                    await client(functions.channels.JoinChannelRequest(target))

                        self.log_with_timestamp("✅ 成功加入群组", account_id, phone)
                        # 模拟真实行为：短延时
                        await asyncio.sleep(random.randint(2,5))

                    except FloodWaitError as e:
                        # 自动等待 FloodWait 指定的秒数
                        self.log_with_timestamp(f"⏳ 触发 FloodWait，需等待 {e.seconds} 秒后继续", account_id, phone)
                        # 若用户取消，则直接返回
                        total_wait = e.seconds + 1
                        for _ in range(total_wait):
                            if not self.is_sending:
                                break
                            await asyncio.sleep(1)
                        # 继续尝试下一个账号/下一个群
                        continue

                    except RPCError as e:
                        em = str(e)
                        # 冻结方法权限（ImportChatInviteRequest 等被禁）
                        if "FROZEN_METHOD_INVALID" in em or "FROZEN" in em:
                            self.log_with_timestamp("🚫 加群权限已被冻结，跳过该账号", account_id, phone)
                            break  # 跳过当前账号继续下一个账号
                        # 某些 RPC 会表明已发送申请
                        if "You have successfully requested to join this chat or channel" in em or "already requested" in em:
                            self.log_with_timestamp("📩 已发送加群申请，等待管理员批准", account_id, phone)
                            continue
                        # 其它 RPC 错误记录并继续
                        self.log_with_timestamp(f"❌ 加群失败（RPC错误）：{em}", account_id, phone)
                        continue

                    except Exception as e:
                        em = str(e)
                        if "You have successfully requested to join this chat or channel" in em:
                            self.log_with_timestamp("📩 已发送加群申请，等待管理员批准", account_id, phone)
                        else:
                            self.log_with_timestamp(f"❌ 加群失败：{em}", account_id, phone)
                        continue

                    # 账号间随机延时，降低风控概率
                    await asyncio.sleep(random.randint(3,8))
        except Exception as e:
            self.log_with_timestamp(f"❗ 加群过程出现异常：{str(e)}\n{traceback.format_exc()}")

    # --------------------- 并发群发（优化版） ---------------------
    def start_sending(self):
        """手动开始群发（如果需要单独使用）"""
        if self.is_sending:
            messagebox.showwarning("警告", "群发已在进行中")
            return
        message = self.message_text.get(1.0, tk.END).strip()
        if not message:
            messagebox.showwarning("警告", "请输入要发送的消息")
            return
        try:
            rounds = int(self.rounds_var.get())
            delay = int(self.delay_var.get())
            account_delay = int(self.account_delay_var.get())
        except ValueError:
            messagebox.showerror("错误", "轮数和间隔必须是数字")
            return
        if rounds <= 0 or delay < 0 or account_delay < 0:
            messagebox.showerror("错误", "轮数必须大于0，间隔不能为负数")
            return

        # 检查是否有可用账号和群组
        available = [s for s,g in self.account_groups.items() if s in self.session_clients and g]
        if not available:
            messagebox.showwarning("警告", "没有可用的账号或群组，请先连接账号并获取群组")
            return

        self.is_sending = True
        self.send_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.start()
        self.progress_var.set("并发群发中...")

        future = asyncio.run_coroutine_threadsafe(
            self._concurrent_send_workflow(message, rounds, delay, account_delay),
            self.loop
        )

        def _c():
            if future.done():
                try: future.result()
                except Exception as e: self.log_with_timestamp(f"群发过程出错：{e}\n{traceback.format_exc()}")
                finally: self.sending_finished()
            else:
                self.parent_frame.after(100, _c)
        _c()

    async def _concurrent_send_workflow(self, message, rounds, delay, account_delay):
        """并发驱动：为每个账号创建任务并发执行"""
        try:
            # 收集可用账号
            available_accounts = [s for s, groups in self.account_groups.items() if s in self.session_clients and groups]
            if not available_accounts:
                self.log_with_timestamp("没有可用的账号可供发送")
                return

            tasks = []
            for i, session_name in enumerate(available_accounts):
                start_delay = i * account_delay
                task = asyncio.create_task(self._account_send_task(session_name, message, rounds, delay, start_delay))
                tasks.append(task)
                self.account_tasks[session_name] = task

            # 等待所有完成（允许某些任务返回异常）
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # 记录异常
            for r in results:
                if isinstance(r, Exception):
                    self.log_with_timestamp(f"某账号任务异常：{str(r)}")
            self.log_with_timestamp("所有账号群发任务完成")
        except Exception as e:
            self.log_with_timestamp(f"并发群发出错：{str(e)}\n{traceback.format_exc()}")

    async def _account_send_task(self, session_name, message, rounds, delay, start_delay):
        """单个账号的发送任务：多轮 + 群组遍历 + 错误分类（中文化）"""
        try:
            if start_delay and start_delay > 0:
                await asyncio.sleep(start_delay)
            if not self.is_sending:
                return

            client = self.session_clients.get(session_name)
            groups = self.account_groups.get(session_name, [])
            info = self.account_info.get(session_name, {})
            account_id = info.get('account_id', 0)
            phone = info.get('phone', '未知')

            if not client or not client.is_connected() or not groups:
                self.log_with_timestamp("客户端未准备就绪或群组为空，跳过该账号", account_id, phone)
                return

            self.log_with_timestamp("开始群发任务 - 加载群组中", account_id, phone)

            for round_i in range(1, rounds + 1):
                if not self.is_sending:
                    break
                for idx, group in enumerate(groups, start=1):
                    if not self.is_sending:
                        break
                    title = group.get('title', '未知群组')
                    gid = group.get('id')
                    username = group.get('username')
                    group_link = f"https://t.me/{username}" if username else f"群组ID:{gid}"

                    # 更新 UI 状态
                    for item in self.status_tree.get_children():
                        values = list(self.status_tree.item(item)['values'])
                        if values[1] == session_name:
                            values[4] = title
                            values[5] = f'发送中({idx}/{len(groups)})'
                            self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                            break
                    try:
                        entity = await client.get_entity(gid)
                        if not entity.broadcast:
                            await client.send_message(entity, message)
                            self.log_with_timestamp(
                                f"账号:{account_id} 群总数{len(groups)} 运行:{idx} - \"{group_link}\" - 已发送",
                                account_id, phone)
                            # 更新 UI
                        for item in self.status_tree.get_children():
                            values = list(self.status_tree.item(item)['values'])
                            if values[1] == session_name:
                                values[5] = f'✓ 成功({idx}/{len(groups)})'
                                self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                                break
                        else:
                            self.log_with_timestamp(f"跳过频道 {entity.title}（ID {gid}）", account_id, phone)
                            # 可以更新UI为“跳过频道”状态，或者不更新
                        # 短延时
                        await asyncio.sleep(random.randint(2,5))
                    except FloodWaitError as e:
                        self.log_with_timestamp(f"⏳ 触发发送 FloodWait，需等待 {e.seconds} 秒", account_id, phone)
                        # 等待期间响应取消
                        total_wait = e.seconds + 1
                        for _ in range(total_wait):
                            if not self.is_sending:
                                break
                            await asyncio.sleep(1)
                        continue

                    except RPCError as e:
                        em = str(e)
                        # 常见情况中文化处理
                        if "CHAT_WRITE_FORBIDDEN" in em or "banned from sending" in em:
                            err_desc = "禁言（无法在该群发送消息），详情可联系 @SpamBot"
                        elif "USER_BANNED_IN_CHANNEL" in em:
                            err_desc = "被群组封禁"
                        elif "CHAT_ADMIN_REQUIRED" in em:
                            err_desc = "需要管理员权限"
                        elif "MESSAGE_TOO_LONG" in em:
                            err_desc = "消息过长"
                        elif "FLOOD_WAIT" in em:
                            err_desc = "发送频率限制"
                        elif "PEER_ID_INVALID" in em:
                            err_desc = "群组ID无效"
                        elif "You don't have permission to send messages" in em:
                            err_desc = "您没有在此聊天中发送消息的权限"
                        elif "AUTH_KEY_UNREGISTERED" in em:
                            err_desc = "账号未授权"
                        elif "PEER_FLOOD" in em or "USER_DEACTIVATED_BAN" in em:
                            err_desc = "账号触发反垃圾/限制，已跳过"
                        else:
                            err_desc = f"RPC错误：{em}"

                        self.log_with_timestamp(f"❌ 发送失败：{err_desc}", account_id, phone)
                        # 更新UI失败状态
                        for item in self.status_tree.get_children():
                            values = list(self.status_tree.item(item)['values'])
                            if values[1] == session_name:
                                values[5] = f'✗ 失败({idx}/{len(groups)})'
                                self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                                break
                        # 某些严重限制建议跳过账号
                        if "PEER_FLOOD" in em or "USER_DEACTIVATED_BAN" in em:
                            break
                        continue

                    except Exception as e:
                        em = str(e)
                        self.log_with_timestamp(f"❌ 发送失败：{em}", account_id, phone)
                        for item in self.status_tree.get_children():
                            values = list(self.status_tree.item(item)['values'])
                            if values[1] == session_name:
                                values[5] = f'✗ 失败({idx}/{len(groups)})'
                                self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                                break
                        continue

                    # 群组间稳定间隔（可调整）
                    if self.is_sending and idx < len(groups):
                        await asyncio.sleep(random.randint(5,10))

                # 轮次间休息
                if round_i < rounds and self.is_sending:
                    self.log_with_timestamp(f"账号:{account_id} 完成本轮，休息 {delay} 秒", account_id, phone)
                    for _ in range(delay):
                        if not self.is_sending:
                            break
                        await asyncio.sleep(1)

            # 完成
            if self.is_sending:
                self.log_with_timestamp(f"账号:{account_id} 群发任务已完成", account_id, phone)
                for item in self.status_tree.get_children():
                    values = list(self.status_tree.item(item)['values'])
                    if values[1] == session_name:
                        values[5] = '✓ 已完成'
                        self.parent_frame.after(0, lambda v=values, i=item: self.status_tree.item(i, values=v))
                        break

        except asyncio.CancelledError:
            self.log_with_timestamp(f"账号任务被取消：{session_name}")
        except Exception as e:
            self.log_with_timestamp(f"账号 {session_name} 发送任务出错：{str(e)}\n{traceback.format_exc()}")

    # --------------------- 停止 / 清理 ---------------------
    def stop_sending(self):
        """停止群发（会尝试取消所有正在运行的任务）"""
        # 将标志设为 False，任务会在检查 is_sending 时响应
        self.is_sending = False
        self.log_with_timestamp("用户手动停止群发")
        # 取消 asyncio 任务
        for session_name, task in list(self.account_tasks.items()):
            try:
                if not task.done():
                    task.cancel()
            except Exception:
                pass
        # 不立即断连客户端，保留连接以便后续操作；如果需要，可以添加断连逻辑
        self.sending_finished()

    def sending_finished(self):
        """群发完成后的 UI & 状态清理"""
        self.is_sending = False
        self.send_button.config(state='normal')
        self.stop_button.config(state='disabled')
        try:
            self.progress_bar.stop()
        except Exception:
            pass
        self.progress_var.set("群发完成")
        self.account_tasks.clear()

    def __del__(self):
        """析构时尝试停止 loop 与断开客户端"""
        try:
            # 停止 loop
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass
        # 尝试断连 clients
        for client in list(self.session_clients.values()):
            try:
                if client and client.is_connected():
                    try:
                        # best-effort disconnect
                        asyncio.run_coroutine_threadsafe(client.disconnect(), asyncio.get_event_loop()).result(timeout=5)
                    except Exception:
                        try:
                            client.disconnect()
                        except Exception:
                            pass
            except Exception:
                pass
