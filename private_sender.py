#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
私信功能模块 - 基于群发功能的私信版本
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import asyncio
import os
import glob
from telethon import TelegramClient
import json
from datetime import datetime

class PrivateSender:
    """私信功能类"""
    
    def __init__(self, parent_frame, account_manager, log_callback):
        self.parent_frame = parent_frame
        self.account_manager = account_manager
        self.log_callback = log_callback
        
        # 私信状态
        self.is_sending = False
        self.session_clients = {}  # 存储session客户端
        self.account_info = {}     # 存储账号信息（手机号等）
        self.loop = None  # 共享事件循环
        self.loop_thread = None  # 事件循环线程
        self.account_tasks = {}    # 存储每个账号的任务
        
        # 启动事件循环线程
        self._start_event_loop()
        
        # 创建UI
        self.create_ui()
    
    def log_with_timestamp(self, message, account_id=None, phone=None):
        """带时间戳的日志记录方法"""
        timestamp = datetime.now().strftime("%Y年%m月%d日%H时%M分%S秒")
        
        if account_id is not None and phone is not None:
            # 格式化为类似日志示例的格式
            formatted_message = f"[{timestamp}] {message} - 账号{account_id}({phone})"
        else:
            formatted_message = f"[{timestamp}] {message}"
        
        # 调用传入的日志回调函数
        if self.log_callback:
            self.log_callback(formatted_message)
    
    def _start_event_loop(self):
        """启动独立的事件循环线程"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # 等待循环启动
        while self.loop is None:
            time.sleep(0.01)
    
    def create_ui(self):
        """创建私信界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent_frame, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="多账号轮流私信功能", font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 5))
        
        # 功能说明
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill='x', pady=(0, 5))
        
        info_text = "💡 功能说明：每个目标用户只接收一次消息，由多个账号轮流发送，避免重复骚扰"
        info_label = ttk.Label(info_frame, text=info_text, font=('Arial', 9), foreground='blue')
        info_label.pack(anchor='w')
        
        # 创建左右主要分栏
        main_container = ttk.Frame(main_frame)
        main_container.pack(fill='both', expand=True)
        
        # 配置左右分栏权重（左侧40%，右侧60%）
        main_container.columnconfigure(0, weight=2)  # 左侧权重2
        main_container.columnconfigure(1, weight=3)  # 右侧权重3
        
        # 左侧容器：消息内容 + 用户管理功能
        left_container = ttk.Frame(main_container)
        left_container.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        
        # 消息输入区域
        message_frame = ttk.LabelFrame(left_container, text="消息内容", padding="5")
        message_frame.pack(fill='x', pady=(0, 5))
        
        # 消息文本框
        self.message_text = scrolledtext.ScrolledText(message_frame, height=3)
        self.message_text.pack(fill='both', expand=True, pady=(0, 5))
        
        # 发送设置
        settings_frame = ttk.Frame(message_frame)
        settings_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(settings_frame, text="轮数:").pack(side='left')
        self.rounds_var = tk.StringVar(value="1")
        rounds_entry = ttk.Entry(settings_frame, textvariable=self.rounds_var, width=6)
        rounds_entry.pack(side='left', padx=(2, 8))
        
        ttk.Label(settings_frame, text="轮次间隔(秒):").pack(side='left')
        self.delay_var = tk.StringVar(value="300")
        delay_entry = ttk.Entry(settings_frame, textvariable=self.delay_var, width=6)
        delay_entry.pack(side='left', padx=(2, 8))
        
        # 在 create_ui 方法的设置区域添加
        ttk.Label(settings_frame, text="发送间隔(秒):").pack(side='left')
        self.send_interval_var = tk.StringVar(value="5")
        send_interval_entry = ttk.Entry(settings_frame, textvariable=self.send_interval_var, width=6)
        send_interval_entry.pack(side='left', padx=(2, 8))
        
        # 发送按钮
        button_frame = ttk.Frame(message_frame)
        button_frame.pack(fill='x')
        
        self.send_button = ttk.Button(button_frame, text="📧 开始轮流私信", command=self.start_auto_sending, style='Accent.TButton')
        self.send_button.pack(side='left', padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="⏹ 停止", command=self.stop_sending, state='disabled')
        self.stop_button.pack(side='left')
        
        # 用户管理区域
        user_frame = ttk.LabelFrame(left_container, text="目标用户管理", padding="5")
        user_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        # 用户输入说明
        user_info_text = "目标用户（每行一个用户名或手机号，每个用户只会收到一次消息）:"
        ttk.Label(user_frame, text=user_info_text).pack(anchor='w', pady=(0, 2))
        
        # 用户输入框
        self.users_text = scrolledtext.ScrolledText(user_frame, height=6, wrap=tk.WORD)
        self.users_text.pack(fill='both', expand=True, pady=(0, 5))
        
        # 用户管理按钮
        user_buttons_frame = ttk.Frame(user_frame)
        user_buttons_frame.pack(fill='x', pady=(5, 0))
        
        # 第一行按钮
        button_row1 = ttk.Frame(user_buttons_frame)
        button_row1.pack(fill='x', pady=(0, 2))
        
        self.scan_button = ttk.Button(button_row1, text="🔍 扫描Session", command=self.scan_sessions)
        self.scan_button.pack(side='left', fill='x', expand=True, padx=(0, 2))
        
        self.connect_button = ttk.Button(button_row1, text="🔌 连接账号", command=self.connect_all_sessions)
        self.connect_button.pack(side='left', fill='x', expand=True, padx=(2, 0))
        
        # 第二行按钮
        button_row2 = ttk.Frame(user_buttons_frame)
        button_row2.pack(fill='x')
        
        self.clear_button = ttk.Button(button_row2, text="🗑 清空用户", command=self.clear_users)
        self.clear_button.pack(side='left', fill='x', expand=True, padx=(0, 2))
        
        self.validate_button = ttk.Button(button_row2, text="✅ 验证用户", command=self.validate_users)
        self.validate_button.pack(side='left', fill='x', expand=True, padx=(2, 0))
        
        # 右侧：账号状态区域
        status_frame = ttk.LabelFrame(main_container, text="账号状态", padding="3")
        status_frame.grid(row=0, column=1, sticky='nsew')
        
        # 状态列表
        columns = ('account_id', 'session', 'phone', 'users_count', 'current_user', 'status')
        self.status_tree = ttk.Treeview(status_frame, columns=columns, show='headings', height=15)
        
        self.status_tree.heading('account_id', text='账号')
        self.status_tree.heading('session', text='Session')
        self.status_tree.heading('phone', text='手机号')
        self.status_tree.heading('users_count', text='用户数')
        self.status_tree.heading('current_user', text='当前用户')
        self.status_tree.heading('status', text='状态')
        
        # 调整列宽
        self.status_tree.column('account_id', width=60)
        self.status_tree.column('session', width=100)
        self.status_tree.column('phone', width=120)
        self.status_tree.column('users_count', width=60)
        self.status_tree.column('current_user', width=150)
        self.status_tree.column('status', width=150)
        
        # 滚动条
        status_scrollbar = ttk.Scrollbar(status_frame, orient='vertical', command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_tree.pack(side='left', fill='both', expand=True)
        status_scrollbar.pack(side='right', fill='y')
        
        # 进度条（放在底部）
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill='x', pady=(5, 0))
        
        self.progress_var = tk.StringVar(value="就绪 - 点击'一键私信'开始")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, font=('Arial', 9))
        progress_label.pack(pady=(3, 2))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=(0, 3))
    
    def clear_users(self):
        """清空用户列表"""
        self.users_text.delete('1.0', tk.END)
        self.log_with_timestamp("已清空用户列表")
    
    def validate_users(self):
        """验证用户列表"""
        users_content = self.users_text.get('1.0', tk.END).strip()
        if not users_content:
            messagebox.showwarning("警告", "请先输入目标用户")
            return
        
        users = [user.strip() for user in users_content.split('\n') if user.strip()]
        self.log_with_timestamp(f"验证用户列表，共 {len(users)} 个用户")
        
        for i, user in enumerate(users, 1):
            self.log_with_timestamp(f"用户 {i}: {user}")
    
    def start_auto_sending(self):
        """开始轮流私信 - 自动完成所有步骤"""
        if self.is_sending:
            messagebox.showwarning("警告", "私信正在进行中，请等待完成或停止后再试")
            return
        
        # 获取消息内容
        message = self.message_text.get('1.0', tk.END).strip()
        if not message:
            messagebox.showerror("错误", "请输入要发送的消息内容")
            return
        
        # 获取目标用户
        users_content = self.users_text.get('1.0', tk.END).strip()
        if not users_content:
            messagebox.showerror("错误", "请输入目标用户")
            return
        
        # 获取发送参数
        try:
            rounds = int(self.rounds_var.get())
            delay = int(self.delay_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字参数")
            return
        
        # 解析用户列表
        target_users = [user.strip() for user in users_content.split('\n') if user.strip()]
        
        self.log_with_timestamp(f"开始轮流私信流程，目标用户: {len(target_users)} 个")
        
        # 在新线程中执行异步操作
        def run_async():
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._auto_full_workflow(message, target_users, rounds, delay),
                    self.loop
                )
        
        threading.Thread(target=run_async, daemon=True).start()
    
    async def _auto_full_workflow(self, message, target_users, rounds, delay):
        """自动完成完整的私信流程"""
        try:
            self.is_sending = True
            self.send_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.progress_bar.start()
            
            # 步骤1: 扫描Session文件
            self.progress_var.set("步骤1/4: 扫描Session文件...")
            await self._scan_sessions_async()
            
            # 步骤2: 连接所有账号
            self.progress_var.set("步骤2/4: 连接账号...")
            await self._connect_sessions_async()
            
            # 步骤3: 开始轮流私信
            self.progress_var.set("步骤3/4: 开始轮流私信...")
            # 添加缺失的account_delay参数，设置为2秒（用户间隔）
            await self._concurrent_send_workflow(message, target_users, rounds, delay, 2)
            
            # 步骤4: 完成
            self.progress_var.set("步骤4/4: 私信完成")
            self.log_with_timestamp("轮流私信流程完成")
            
        except Exception as e:
            self.log_with_timestamp(f"私信流程出错: {str(e)}")
        finally:
            self.sending_finished()
    
    def scan_sessions(self):
        """扫描Session文件"""
        self.log_with_timestamp("开始扫描Session文件...")
        
        def run_async():
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(self._scan_sessions_async(), self.loop)
        
        threading.Thread(target=run_async, daemon=True).start()
    
    async def _scan_sessions_async(self):
        """异步扫描Session文件"""
        try:
            session_files = glob.glob("*.session")
            self.log_with_timestamp(f"找到 {len(session_files)} 个session文件")
            
            for session_file in session_files:
                session_name = session_file.replace('.session', '')
                if session_name not in self.session_clients:
                    self.account_info[session_name] = {
                        'session_name': session_name,
                        'phone': '未知',
                        'status': '未连接'
                    }
                    self.log_with_timestamp(f"发现Session: {session_name}")
            
            self.update_status_display()
            
        except Exception as e:
            self.log_with_timestamp(f"扫描Session文件出错: {str(e)}")
    
    def connect_all_sessions(self):
        """连接所有Session"""
        self.log_with_timestamp("开始连接所有Session...")
        
        def run_async():
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(self._connect_sessions_async(), self.loop)
        
        threading.Thread(target=run_async, daemon=True).start()
    
    async def _connect_sessions_async(self):
        """异步连接所有Session"""
        try:
            for session_name in self.account_info.keys():
                if session_name not in self.session_clients:
                    try:
                        # 创建客户端
                        client = TelegramClient(session_name, api_id=3642180, api_hash='636c15dbfe0b01f6fab88600d52667d0')
                        await client.connect()
                        
                        if await client.is_user_authorized():
                            self.session_clients[session_name] = client
                            
                            # 获取用户信息
                            me = await client.get_me()
                            phone = me.phone if me.phone else '未知'
                            
                            self.account_info[session_name].update({
                                'phone': phone,
                                'status': '已连接',
                                'user_id': me.id,
                                'username': me.username
                            })
                            
                            self.log_with_timestamp(f"账号连接成功: {session_name} ({phone})")
                        else:
                            self.account_info[session_name]['status'] = '未授权'
                            self.log_with_timestamp(f"账号未授权: {session_name}")
                            
                    except Exception as e:
                        self.account_info[session_name]['status'] = f'连接失败: {str(e)}'
                        self.log_with_timestamp(f"连接失败 {session_name}: {str(e)}")
                
                self.update_status_display()
                await asyncio.sleep(1)  # 避免连接过快
            
            connected_count = len(self.session_clients)
            self.log_with_timestamp(f"连接完成，成功连接 {connected_count} 个账号")
            
        except Exception as e:
            self.log_with_timestamp(f"连接Session出错: {str(e)}")
    
    async def _concurrent_send_workflow(self, message, target_users, rounds, delay, account_delay):
        """并发私信工作流程 - 优化版：每个用户只收到一次消息"""
        try:
            if not self.session_clients:
                self.log_with_timestamp("没有可用的已连接账号")
                return
            
            available_accounts = list(self.session_clients.items())
            total_users = len(target_users)
            total_accounts = len(available_accounts)
            
            self.log_with_timestamp(f"开始私信，账号数: {total_accounts}, 目标用户: {total_users}, 轮数: {rounds}")
            self.log_with_timestamp(f"分配策略: 每个用户只接收一次消息，由不同账号轮流发送")
            
            for round_num in range(1, rounds + 1):
                if not self.is_sending:
                    break
                
                self.log_with_timestamp(f"开始第 {round_num} 轮私信")
                
                # 为每个用户分配一个账号
                tasks = []
                for user_index, user_target in enumerate(target_users):
                    if not self.is_sending:
                        break
                    
                    # 轮流分配账号
                    account_index = user_index % total_accounts
                    session_name, client = available_accounts[account_index]
                    
                    # 在 _concurrent_send_workflow 方法中
                    # 计算发送延迟（避免同时发送）
                    send_delay = user_index * 5  # 将间隔从2秒增加到5秒
                    
                    task = asyncio.create_task(
                        self._single_user_send_task(session_name, client, message, user_target, round_num, send_delay)
                    )
                    tasks.append(task)
                
                # 等待本轮所有任务完成
                await asyncio.gather(*tasks, return_exceptions=True)
                
                if round_num < rounds and self.is_sending:
                    self.log_with_timestamp(f"第 {round_num} 轮完成，等待 {delay} 秒后开始下一轮")
                    await asyncio.sleep(delay)
            
            self.log_with_timestamp("所有轮次私信任务完成")
            
        except Exception as e:
            self.log_with_timestamp(f"私信工作流程出错: {str(e)}")
    
    async def _single_user_send_task(self, session_name, client, message, user_target, round_num, send_delay):
        """单个用户的私信任务"""
        try:
            # 等待发送延迟
            if send_delay > 0:
                await asyncio.sleep(send_delay)
            
            if not self.is_sending:  # 检查是否被停止
                return
            
            phone = self.account_info.get(session_name, {}).get('phone', '未知')
            
            # 更新状态显示
            self.account_info[session_name]['current_user'] = user_target
            self.account_info[session_name]['status'] = f'私信中 (轮次{round_num})'
            self.update_status_display()
            
            try:
                # 发送私信
                await client.send_message(user_target, message)
                
                self.log_with_timestamp(f"私信发送成功 -> {user_target} (轮次{round_num})", session_name, phone)
                
                # 更新状态
                self.account_info[session_name]['status'] = '发送成功'
                
            except Exception as e:
                self.log_with_timestamp(f"私信发送失败 -> {user_target}: {str(e)}", session_name, phone)
                self.account_info[session_name]['status'] = f'发送失败: {str(e)[:20]}'
            
            # 发送完成后清空当前用户
            self.account_info[session_name]['current_user'] = '-'
            self.update_status_display()
            
        except Exception as e:
            self.log_with_timestamp(f"用户任务出错 {user_target}: {str(e)}", session_name, phone)
            self.account_info[session_name]['status'] = f'任务出错: {str(e)[:20]}'
            self.account_info[session_name]['current_user'] = '-'
            self.update_status_display()
    
    def update_status_display(self):
        """更新状态显示"""
        try:
            # 清空现有项目
            for item in self.status_tree.get_children():
                self.status_tree.delete(item)
            
            # 添加账号信息
            for i, (session_name, info) in enumerate(self.account_info.items(), 1):
                users_count = len(self.users_text.get('1.0', tk.END).strip().split('\n')) if self.users_text.get('1.0', tk.END).strip() else 0
                current_user = info.get('current_user', '-')
                status = info.get('status', '未知')
                phone = info.get('phone', '未知')
                
                self.status_tree.insert('', 'end', values=(
                    i, session_name, phone, users_count, current_user, status
                ))
        except Exception as e:
            self.log_with_timestamp(f"更新状态显示出错: {str(e)}")
    
    def stop_sending(self):
        """停止私信"""
        self.is_sending = False
        self.log_with_timestamp("正在停止私信...")
        
        # 取消所有任务
        for session_name, task in self.account_tasks.items():
            if not task.done():
                task.cancel()
        
        self.account_tasks.clear()
        self.sending_finished()
    
    def sending_finished(self):
        """私信完成后的清理工作"""
        self.is_sending = False
        self.send_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress_bar.stop()
        self.progress_var.set("就绪 - 点击'一键私信'开始")
        
        # 更新所有账号状态为就绪
        for session_name in self.account_info:
            if self.account_info[session_name]['status'] not in ['未连接', '连接失败']:
                self.account_info[session_name]['status'] = '就绪'
                self.account_info[session_name]['current_user'] = '-'
        
        self.update_status_display()
    
    def __del__(self):
        """析构函数，清理资源"""
        try:
            if self.loop and not self.loop.is_closed():
                self.loop.call_soon_threadsafe(self.loop.stop)
        except:
            pass
