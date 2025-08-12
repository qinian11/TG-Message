#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram登录模块
独立的登录类，支持验证码输入和二级密码
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
import json
import os

class CodeInputDialog:
    """验证码输入对话框"""
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("输入验证码")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # 创建界面
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="请输入收到的验证码:", font=('Arial', 10)).pack(pady=(0, 10))
        
        self.code_var = tk.StringVar()
        self.code_entry = ttk.Entry(main_frame, textvariable=self.code_var, font=('Arial', 12), width=20)
        self.code_entry.pack(pady=(0, 15))
        self.code_entry.focus()
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT)
        
        # 绑定回车键
        self.code_entry.bind('<Return>', lambda e: self.ok_clicked())
        
    def ok_clicked(self):
        code = self.code_var.get().strip()
        if code:
            self.result = code
            self.dialog.destroy()
        else:
            messagebox.showwarning("警告", "请输入验证码")
    
    def cancel_clicked(self):
        self.dialog.destroy()
    
    def get_code(self):
        self.dialog.wait_window()
        return self.result

class PasswordInputDialog:
    """二级密码输入对话框"""
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("输入二级密码")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # 创建界面
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="请输入二级密码:", font=('Arial', 10)).pack(pady=(0, 10))
        
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, 
                                      font=('Arial', 12), width=20, show="*")
        self.password_entry.pack(pady=(0, 15))
        self.password_entry.focus()
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT)
        
        # 绑定回车键
        self.password_entry.bind('<Return>', lambda e: self.ok_clicked())
        
    def ok_clicked(self):
        password = self.password_var.get().strip()
        if password:
            self.result = password
            self.dialog.destroy()
        else:
            messagebox.showwarning("警告", "请输入二级密码")
    
    def cancel_clicked(self):
        self.dialog.destroy()
    
    def get_password(self):
        self.dialog.wait_window()
        return self.result

class TelegramLogin:
    """Telegram登录管理类"""
    
    def __init__(self, parent_window=None, log_callback=None):
        self.parent_window = parent_window
        self.log_callback = log_callback or self._default_log
        self.client = None
        self.event_loop = None
        self.login_thread = None
        self.is_logged_in = False
        self.user_info = None
        
    def _default_log(self, message):
        """默认日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def login_async(self, api_id, api_hash, phone, session_name="session", callback=None):
        """异步登录（在新线程中执行）"""
        self.login_callback = callback
        
        # 在新线程中运行异步登录
        self.login_thread = threading.Thread(
            target=self._run_async_login,
            args=(api_id, api_hash, phone, session_name),
            daemon=True
        )
        self.login_thread.start()
    
    def _run_async_login(self, api_id, api_hash, phone, session_name):
        """在新线程中运行异步登录"""
        try:
            # 创建新的事件循环
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            # 运行异步登录
            result = self.event_loop.run_until_complete(
                self._do_login_async(api_id, api_hash, phone, session_name)
            )
            
            # 调用回调函数
            if self.login_callback:
                self.login_callback(True, result, None)
                
        except Exception as e:
            # 调用回调函数报告错误
            if self.login_callback:
                self.login_callback(False, None, str(e))
        finally:
            # 安全关闭事件循环
            self._cleanup_async_resources()
    
    def _cleanup_async_resources(self):
        """清理异步资源"""
        try:
            if self.event_loop and not self.event_loop.is_closed():
                # 取消所有待处理的任务
                pending_tasks = asyncio.all_tasks(self.event_loop)
                for task in pending_tasks:
                    task.cancel()
                
                # 等待任务完成或取消
                if pending_tasks:
                    self.event_loop.run_until_complete(
                        asyncio.gather(*pending_tasks, return_exceptions=True)
                    )
                
                # 关闭事件循环
                self.event_loop.close()
                
        except Exception as e:
            self.log_callback(f"清理异步资源时出错: {e}")
        finally:
            self.event_loop = None
    
    async def _do_login_async(self, api_id, api_hash, phone, session_name):
        """执行异步登录操作"""
        try:
            self.log_callback(f"创建Telegram客户端 (API ID: {api_id})")
            
            # 创建客户端
            self.client = TelegramClient(session_name, api_id, api_hash)
            
            self.log_callback("正在连接到Telegram服务器...")
            
            # 连接客户端
            await self.client.connect()
            
            # 检查是否已经登录
            if not await self.client.is_user_authorized():
                self.log_callback("需要进行身份验证")
                
                # 发送验证码
                self.log_callback("正在发送验证码...")
                await self.client.send_code_request(phone)
                
                # 获取验证码
                self.log_callback("等待用户输入验证码")
                code = await self._get_code_async()
                
                if not code:
                    self.log_callback("用户取消了验证码输入")
                    return None
                
                self.log_callback(f"正在验证验证码: {code}")
                
                try:
                    # 尝试使用验证码登录
                    await self.client.sign_in(phone, code)
                    
                except SessionPasswordNeededError:
                    # 需要二级密码
                    self.log_callback("检测到二级密码保护，需要输入密码")
                    
                    password = await self._get_password_async()
                    
                    if not password:
                        self.log_callback("用户取消了二级密码输入")
                        return None
                    
                    self.log_callback("正在验证二级密码...")
                    await self.client.sign_in(password=password)
                    
                except PhoneCodeInvalidError:
                    self.log_callback("验证码无效")
                    raise Exception("输入的验证码无效，请重试")
            
            self.log_callback("检查授权状态...")
            
            # 检查是否已授权
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                username = me.username if me.username else "无用户名"
                
                self.user_info = {
                    'id': me.id,
                    'first_name': me.first_name,
                    'last_name': me.last_name or '',
                    'username': username,
                    'phone': phone,
                    'session_name': session_name
                }
                
                self.is_logged_in = True
                
                self.log_callback(f"登录成功！")
                self.log_callback(f"用户名: {me.first_name} {me.last_name or ''}")
                self.log_callback(f"用户ID: {me.id}")
                self.log_callback(f"用户名: @{username}")
                
                return self.user_info
            else:
                self.log_callback("登录失败：未能获得授权")
                raise Exception("未能获得Telegram授权")
            
        except Exception as e:
            # 重新抛出异常，让外层处理
            raise e
        finally:
            # 确保客户端正确断开连接
            if self.client and self.client.is_connected():
                await self.client.disconnect()
    
    async def _get_code_async(self):
        """异步获取验证码"""
        if not self.parent_window:
            # 如果没有父窗口，使用控制台输入
            return input("请输入验证码: ")
        
        result = [None]
        event = threading.Event()
        
        def show_dialog():
            try:
                dialog = CodeInputDialog(self.parent_window)
                result[0] = dialog.get_code()
            finally:
                event.set()
        
        # 在主线程中显示对话框
        if self.parent_window:
            self.parent_window.after(0, show_dialog)
        
        # 异步等待对话框完成
        while not event.is_set():
            await asyncio.sleep(0.1)
        
        return result[0]
    
    async def _get_password_async(self):
        """异步获取二级密码"""
        if not self.parent_window:
            # 如果没有父窗口，使用控制台输入
            import getpass
            return getpass.getpass("请输入二级密码: ")
        
        result = [None]
        event = threading.Event()
        
        def show_dialog():
            try:
                dialog = PasswordInputDialog(self.parent_window)
                result[0] = dialog.get_password()
            finally:
                event.set()
        
        # 在主线程中显示对话框
        if self.parent_window:
            self.parent_window.after(0, show_dialog)
        
        # 异步等待对话框完成
        while not event.is_set():
            await asyncio.sleep(0.1)
        
        return result[0]
    
    def logout(self):
        """登出"""
        try:
            if self.client:
                # 检查是否有现有的事件循环
                try:
                    current_loop = asyncio.get_running_loop()
                    # 如果有运行中的循环，使用 create_task
                    if current_loop and not current_loop.is_closed():
                        # 在当前循环中创建任务
                        task = current_loop.create_task(self.client.disconnect())
                        # 不等待完成，让它在后台执行
                    else:
                        raise RuntimeError("No running loop")
                except RuntimeError:
                    # 没有运行中的事件循环，创建新的
                    try:
                        # 检查 disconnect 是否返回协程
                        disconnect_result = self.client.disconnect()
                        if asyncio.iscoroutine(disconnect_result) or asyncio.isfuture(disconnect_result):
                            temp_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(temp_loop)
                            try:
                                temp_loop.run_until_complete(disconnect_result)
                            finally:
                                temp_loop.close()
                                asyncio.set_event_loop(None)
                        else:
                            # 如果不是协程，直接忽略
                            pass
                    except Exception as disconnect_error:
                        self.log_callback(f"断开连接时出错: {disconnect_error}")
            
            self.is_logged_in = False
            self.user_info = None
            self.client = None
            self.log_callback("已登出")
            
        except Exception as e:
            self.log_callback(f"登出时出错: {e}")
    
    def get_user_info(self):
        """获取用户信息"""
        return self.user_info if self.is_logged_in else None
    
    def is_login(self):
        """检查是否已登录"""
        return self.is_logged_in
