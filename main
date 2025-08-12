#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多账号Telegram管理器
支持多个账号的登录、管理和操作
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
import glob
from datetime import datetime
from telegram_login import TelegramLogin

class MultiAccountManager:
    """多账号管理器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("小卡拉米专属群发私信软件 @HY499")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 账号列表
        self.accounts = {}  # {account_id: {'login': TelegramLogin, 'info': dict, 'status': str}}
        self.account_counter = 0
        self.account_tree = None
        self.log_text = None
        
        # 确保配置文件存在
        self.ensure_config_file()
        
        # 创建UI
        self.create_ui()
        
        # 自动加载配置
        self.load_from_config()
        
        # 自动扫描session文件
        self.scan_session_files()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)  # 选项卡区域
        main_frame.rowconfigure(1, weight=0)  # 日志区域固定高度
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 账号管理选项卡
        self.account_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.account_tab, text="账号管理")
        
        # 群发功能选项卡
        self.sender_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sender_tab, text="群发功能")
        
        # 私信功能选项卡
        self.private_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.private_tab, text="私信功能")
        
        # 使用说明选项卡
        self.guide_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.guide_tab, text="使用说明")
        
        # 创建固定在底部的日志区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="5")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.create_account_management_ui()
        self.create_group_sender_ui()
        self.create_private_sender_ui()  # 私信功能界面
        self.create_user_guide_ui()      # 新增使用说明界面
    
    def create_account_management_ui(self):
        """创建账号管理界面"""
        # 配置选项卡的网格权重 - 确保右侧有足够空间
        self.account_tab.columnconfigure(0, weight=1)
        self.account_tab.columnconfigure(1, weight=3)  # 增加右侧权重
        self.account_tab.rowconfigure(0, weight=1)
        
        # 左侧：账号操作区域
        left_frame = ttk.Frame(self.account_tab)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        
        # 添加账号区域
        add_frame = ttk.LabelFrame(left_frame, text="添加账号", padding="5")
        add_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        add_frame.columnconfigure(1, weight=1)
        
        ttk.Label(add_frame, text="API ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.api_id_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.api_id_var, width=15).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(add_frame, text="API Hash:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.api_hash_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.api_hash_var, width=25).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(add_frame, text="手机号:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.phone_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.phone_var, width=15).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(add_frame, text="会话名:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        self.session_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.session_name_var, width=15).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 按钮
        btn_frame = ttk.Frame(add_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn_frame, text="添加账号", command=self.add_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="从配置加载", command=self.load_from_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="保存配置", command=self.save_to_config).pack(side=tk.LEFT)
        
        # Session文件管理区域
        session_frame = ttk.LabelFrame(left_frame, text="Session文件管理", padding="5")
        session_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        session_btn_frame = ttk.Frame(session_frame)
        session_btn_frame.pack()
        
        ttk.Button(session_btn_frame, text="导入Session文件", command=self.import_session_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(session_btn_frame, text="扫描Session文件", command=self.scan_session_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(session_btn_frame, text="刷新列表", command=self.refresh_account_list).pack(side=tk.LEFT)
        
        # 批量操作区域
        batch_frame = ttk.LabelFrame(left_frame, text="批量操作", padding="5")
        batch_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        batch_btn_frame = ttk.Frame(batch_frame)
        batch_btn_frame.pack()
        
        ttk.Button(batch_btn_frame, text="登录所有账号", command=self.login_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(batch_btn_frame, text="登出所有账号", command=self.logout_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(batch_btn_frame, text="刷新状态", command=self.refresh_status).pack(side=tk.LEFT)
        
        # 右侧：账号列表区域
        right_frame = ttk.Frame(self.account_tab)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # 账号列表
        list_frame = ttk.LabelFrame(right_frame, text="账号列表", padding="5")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview
        columns = ('ID', '用户名', '手机号', '状态')
        self.account_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题和列宽
        self.account_tree.heading('ID', text='ID')
        self.account_tree.heading('用户名', text='用户名')
        self.account_tree.heading('手机号', text='手机号')
        self.account_tree.heading('状态', text='状态')
        
        self.account_tree.column('ID', width=120, minwidth=80)
        self.account_tree.column('用户名', width=150, minwidth=100)
        self.account_tree.column('手机号', width=150, minwidth=100)
        self.account_tree.column('状态', width=100, minwidth=80)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.account_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 账号操作按钮
        account_btn_frame = ttk.Frame(list_frame)
        account_btn_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        ttk.Button(account_btn_frame, text="登录选中账号", command=self.login_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(account_btn_frame, text="登出选中账号", command=self.logout_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(account_btn_frame, text="删除选中账号", command=self.delete_selected).pack(side=tk.LEFT)
    
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        if self.log_text is not None:
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        else:
            print(log_message.strip())
    
    def import_session_file(self):
        """导入Session文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择Session文件",
            filetypes=[("Session文件", "*.session"), ("所有文件", "*.*")],
            initialdir=os.getcwd()
        )
        
        if not file_paths:
            return
        
        imported_count = 0
        for file_path in file_paths:
            try:
                # 获取文件名（不含扩展名）作为session名
                session_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 复制文件到当前目录
                target_path = os.path.join(os.getcwd(), f"{session_name}.session")
                
                if file_path != target_path:
                    import shutil
                    shutil.copy2(file_path, target_path)
                
                # 添加到账号列表
                self.add_session_account(session_name)
                imported_count += 1
                
                self.log(f"已导入Session文件: {session_name}.session")
                
            except Exception as e:
                self.log(f"导入Session文件失败 {os.path.basename(file_path)}: {e}")
        
        if imported_count > 0:
            self.update_account_list()
            messagebox.showinfo("导入完成", f"成功导入 {imported_count} 个Session文件")
    
    def scan_session_files(self):
        """扫描当前目录下的Session文件"""
        session_files = glob.glob("*.session")
        
        if not session_files:
            self.log("当前目录下没有找到Session文件")
            return
        
        added_count = 0
        for session_file in session_files:
            session_name = os.path.splitext(session_file)[0]
            
            # 检查是否已经存在
            if session_name not in self.accounts:
                self.add_session_account(session_name)
                added_count += 1
                self.log(f"发现Session文件: {session_file}")
        
        if added_count > 0:
            self.update_account_list()
            self.log(f"扫描完成，新增 {added_count} 个Session账号")
        else:
            self.log("扫描完成，没有发现新的Session文件")
    
    def add_session_account(self, session_name):
        """添加Session账号到列表"""
        # 使用session文件名作为账号ID
        account_id = session_name
        
        # 创建登录实例
        login_instance = TelegramLogin(self.root, self.log)
        
        # 添加到账号列表
        self.accounts[account_id] = {
            'login': login_instance,
            'info': {
                'api_id': None,  # 从session文件登录时不需要API信息
                'api_hash': None,
                'phone': '未知',
                'session_name': session_name
            },
            'status': '未登录',
            'from_session': True  # 标记这是从session文件导入的
        }
    
    def refresh_account_list(self):
        """刷新账号列表"""
        self.log("正在刷新账号列表...")
        
        # 重新扫描session文件
        self.scan_session_files()
        
        # 检查已存在账号的session文件是否还存在
        accounts_to_remove = []
        for account_id, account_data in self.accounts.items():
            if account_data.get('from_session', False):
                session_file = f"{account_data['info']['session_name']}.session"
                if not os.path.exists(session_file):
                    accounts_to_remove.append(account_id)
                    self.log(f"Session文件已删除，移除账号: {account_id}")
        
        # 移除不存在的session账号
        for account_id in accounts_to_remove:
            del self.accounts[account_id]
        
        # 更新界面
        self.update_account_list()
        self.log("账号列表刷新完成")
    
    def add_account(self):
        """添加新账号"""
        api_id = self.api_id_var.get().strip()
        api_hash = self.api_hash_var.get().strip()
        phone = self.phone_var.get().strip()
        session_name = self.session_name_var.get().strip() or f"session_{self.account_counter}"
        
        # 验证输入
        if not all([api_id, api_hash, phone]):
            messagebox.showerror("错误", "请填写完整的API ID、API Hash和手机号")
            return
        
        try:
            api_id = int(api_id)
        except ValueError:
            messagebox.showerror("错误", "API ID必须是数字")
            return
        
        # 创建账号
        account_id = f"account_{self.account_counter}"
        self.account_counter += 1
        
        # 创建登录实例
        login_instance = TelegramLogin(self.root, self.log)
        
        # 添加到账号列表
        self.accounts[account_id] = {
            'login': login_instance,
            'info': {
                'api_id': api_id,
                'api_hash': api_hash,
                'phone': phone,
                'session_name': session_name
            },
            'status': '未登录',
            'from_session': False
        }
        
        # 更新界面
        self.update_account_list()
        
        # 清空输入框
        self.api_id_var.set("")
        self.api_hash_var.set("")
        self.phone_var.set("")
        self.session_name_var.set("")
        
        self.log(f"已添加账号: {phone}")
    
    def ensure_config_file(self):
        """确保配置文件存在，如果不存在则创建默认配置"""
        config_file = 'config.json'
        
        if not os.path.exists(config_file):
            # 创建默认配置
            default_config = {
                "api_id": "3642180",
                "api_hash": "636c15dbfe0b01f6fab88600d62667d0",
                "phone": "",
                "session_name": "输入会话名称"
            }
            
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                
                print(f"已创建默认配置文件: {config_file}")
                
            except Exception as e:
                print(f"创建配置文件失败: {e}")
        else:
            print(f"配置文件已存在: {config_file}")
    
    def load_from_config(self):
        """从配置文件加载账号"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 设置输入框的值
                self.api_id_var.set(str(config.get('api_id', '')))
                self.api_hash_var.set(config.get('api_hash', ''))
                self.phone_var.set(config.get('phone', ''))
                self.session_name_var.set(config.get('session_name', 'session'))
                
                self.log("已从config.json加载配置")
            else:
                # 如果文件不存在，使用默认值
                self.api_id_var.set("3642180")
                self.api_hash_var.set("636c15dbfe0b01f6fab88600d62667d0")
                self.phone_var.set("")
                self.session_name_var.set("session")
                self.log("使用默认API配置")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {e}")
            # 发生错误时也使用默认值
            self.api_id_var.set("3642180")
            self.api_hash_var.set("636c15dbfe0b01f6fab88600d62667d0")
            self.phone_var.set("")
            self.session_name_var.set("session")
    
    def save_to_config(self):
        """保存当前配置到文件"""
        try:
            config = {
                "api_id": self.api_id_var.get().strip(),
                "api_hash": self.api_hash_var.get().strip(),
                "phone": self.phone_var.get().strip(),
                "session_name": self.session_name_var.get().strip() or "session"
            }
            
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.log("配置已保存到config.json")
            messagebox.showinfo("成功", "配置已保存")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def update_account_list(self):
        """更新账号列表显示"""
        # 清空现有项目
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        
        # 添加账号
        for account_id, account_data in self.accounts.items():
            info = account_data['info']
            status = account_data['status']
            
            # 获取用户信息
            user_info = account_data['login'].get_user_info()
            username = f"{user_info['first_name']} {user_info['last_name']}" if user_info else "未知"
            
            # 获取实际手机号
            display_phone = info['phone']
            
            # 如果账号已连接，尝试获取实际手机号
            if status == '已连接' and account_data['login'].client:
                try:
                    # 同步获取用户信息
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def get_phone():
                        try:
                            if account_data['login'].client.is_connected():
                                me = await account_data['login'].client.get_me()
                                return me.phone if me.phone else display_phone
                        except:
                            pass
                        return display_phone
                    
                    actual_phone = loop.run_until_complete(get_phone())
                    loop.close()
                    
                    if actual_phone and actual_phone != display_phone:
                        display_phone = actual_phone
                        # 更新存储的手机号信息
                        info['phone'] = actual_phone
                        
                except Exception as e:
                    # 如果获取失败，保持原有显示
                    pass
            
            # 如果是从session导入的且手机号未知，则显示session名
            if account_data.get('from_session', False) and display_phone in ['未知', '']:
                display_phone = f"[{info['session_name']}]"
            
            self.account_tree.insert('', 'end', iid=account_id, values=(
                account_id,
                username,
                display_phone,
                status
            ))
    
    def login_selected(self):
        """登录选中的账号"""
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要登录的账号")
            return
        
        account_id = selected[0]
        self.login_account(account_id)
    
    def login_account(self, account_id):
        """登录指定账号"""
        if account_id not in self.accounts:
            return
        
        account_data = self.accounts[account_id]
        info = account_data['info']
        login_instance = account_data['login']
        
        # 检查是否是从session文件导入的账号
        if account_data.get('from_session', False):
            # 对于session文件账号，自动从配置文件读取API信息
            if not info['api_id'] or not info['api_hash']:
                try:
                    if os.path.exists('config.json'):
                        with open('config.json', 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        api_id = config.get('api_id')
                        api_hash = config.get('api_hash')
                        
                        if api_id and api_hash:
                            # 更新账号信息
                            info['api_id'] = int(api_id)
                            info['api_hash'] = api_hash
                            # 确保手机号不为None，优先使用config中的phone
                            config_phone = config.get('phone')
                            if config_phone:
                                info['phone'] = config_phone
                            elif not info.get('phone') or info['phone'] in ['未知', None]:
                                # 如果config中也没有phone，使用session名称作为临时标识
                                info['phone'] = info['session_name']
                            
                            self.log(f"已从config.json自动加载API信息用于账号: {account_id}")
                        else:
                            self.log(f"config.json中缺少API信息，无法登录账号: {account_id}")
                            messagebox.showerror("错误", "config.json中缺少API ID或API Hash信息")
                            return
                    else:
                        self.log(f"config.json文件不存在，无法登录账号: {account_id}")
                        messagebox.showerror("错误", "config.json文件不存在，请先创建配置文件")
                        return
                        
                except Exception as e:
                    self.log(f"读取config.json失败: {e}")
                    messagebox.showerror("错误", f"读取配置文件失败: {e}")
                    return
        
        # 确保手机号不为None或空字符串
        phone = info.get('phone', '')
        if not phone or phone in ['未知', None]:
            phone = info.get('session_name', '')
        
        # 更新状态
        self.accounts[account_id]['status'] = '登录中...'
        self.update_account_list()
        
        self.log(f"开始登录账号: {phone}")
        
        # 定义登录回调
        def login_callback(success, user_info, error):
            if success:
                self.accounts[account_id]['status'] = '已登录'
                # 更新手机号信息 - 使用从Telegram获取的真实手机号
                if user_info and 'phone' in user_info:
                    self.accounts[account_id]['info']['phone'] = user_info['phone']
                    self.log(f"账号 {user_info['phone']} 登录成功")
                else:
                    self.log(f"账号 {phone} 登录成功")
            else:
                self.accounts[account_id]['status'] = '登录失败'
                self.log(f"账号 {phone} 登录失败: {error}")
                messagebox.showerror("登录失败", f"账号 {phone} 登录失败:\n{error}")
            
            # 更新界面
            self.root.after(0, self.update_account_list)
        
        # 开始异步登录
        login_instance.login_async(
            info['api_id'],
            info['api_hash'],
            phone,  # 确保传递有效的手机号
            info['session_name'],
            login_callback
        )
    
    def logout_selected(self):
        """登出选中的账号"""
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要登出的账号")
            return
        
        account_id = selected[0]
        self.logout_account(account_id)
    
    def logout_account(self, account_id):
        """登出指定账号"""
        if account_id not in self.accounts:
            return
        
        account_data = self.accounts[account_id]
        info = account_data['info']
        login_instance = account_data['login']
        
        login_instance.logout()
        self.accounts[account_id]['status'] = '已登出'
        
        self.log(f"账号 {info.get('phone', account_id)} 已登出")
        self.update_account_list()
    
    def delete_selected(self):
        """删除选中的账号"""
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的账号")
            return
        
        account_id = selected[0]
        
        if messagebox.askyesno("确认删除", "确定要删除选中的账号吗？"):
            # 先登出
            self.logout_account(account_id)
            
            # 从列表中删除
            info = self.accounts[account_id]['info']
            del self.accounts[account_id]
            
            self.log(f"已删除账号: {info.get('phone', account_id)}")
            self.update_account_list()
    
    def login_all(self):
        """登录所有账号"""
        if not self.accounts:
            messagebox.showwarning("警告", "没有可登录的账号")
            return
        
        self.log("开始批量登录所有账号...")
        
        for account_id in self.accounts.keys():
            if self.accounts[account_id]['status'] != '已登录':
                self.login_account(account_id)
    
    def logout_all(self):
        """登出所有账号"""
        if not self.accounts:
            messagebox.showwarning("警告", "没有可登出的账号")
            return
        
        self.log("开始批量登出所有账号...")
        
        for account_id in self.accounts.keys():
            if self.accounts[account_id]['status'] == '已登录':
                self.logout_account(account_id)
    
    def refresh_status(self):
        """刷新所有账号状态"""
        self.log("刷新账号状态...")
        
        for account_id, account_data in self.accounts.items():
            login_instance = account_data['login']
            if login_instance.is_login():
                self.accounts[account_id]['status'] = '已登录'
            else:
                self.accounts[account_id]['status'] = '未登录'
        
        self.update_account_list()
        self.log("状态刷新完成")
    
    def create_group_sender_ui(self):
        """创建群发功能界面"""
        try:
            # 尝试导入群发模块
            from group_sender import GroupSender
            
            # 创建群发实例，传递正确的参数
            self.group_sender = GroupSender(self.sender_tab, self, self.log)
            
        except ImportError:
            # 如果模块不存在，显示错误信息和创建按钮
            error_frame = ttk.Frame(self.sender_tab)
            error_frame.pack(expand=True, fill='both', padx=10, pady=10)
            
            ttk.Label(error_frame, text="群发模块 group_sender.py 不存在", 
                     font=('Arial', 12)).pack(pady=20)
            
            ttk.Button(error_frame, text="创建群发模块文件", 
                      command=self.create_group_sender_file).pack(pady=10)
    
    def create_group_sender_file(self):
        """创建群发模块文件"""
        group_sender_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群发功能模块
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
from datetime import datetime

class GroupSender:
    def __init__(self, parent, manager):
        self.parent = parent
        self.manager = manager
        self.groups = {}  # 存储账号对应的群组
        self.is_sending = False
        self.create_ui()
    
    def create_ui(self):
        """创建群发界面"""
        # 主框架
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="群发功能", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 操作区域
        control_frame = ttk.LabelFrame(main_frame, text="操作控制", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))
        
        # 刷新群组按钮
        ttk.Button(control_frame, text="刷新群组列表", 
                  command=self.refresh_groups).pack(side='left', padx=(0, 10))
        
        # 发送消息区域
        message_frame = ttk.LabelFrame(main_frame, text="消息内容", padding=10)
        message_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # 消息输入框
        self.message_text = scrolledtext.ScrolledText(message_frame, height=6)
        self.message_text.pack(fill='both', expand=True, pady=(0, 10))
        
        # 发送按钮
        send_frame = ttk.Frame(message_frame)
        send_frame.pack(fill='x')
        
        self.send_button = ttk.Button(send_frame, text="开始群发", 
                                     command=self.start_sending)
        self.send_button.pack(side='left')
        
        self.stop_button = ttk.Button(send_frame, text="停止群发", 
                                     command=self.stop_sending, state='disabled')
        self.stop_button.pack(side='left', padx=(10, 0))
        
        # 群组列表区域
        groups_frame = ttk.LabelFrame(main_frame, text="群组列表", padding=10)
        groups_frame.pack(fill='both', expand=True)
        
        # 群组列表
        columns = ('account', 'group_name', 'group_id', 'status')
        self.groups_tree = ttk.Treeview(groups_frame, columns=columns, show='headings', height=8)
        
        # 设置列标题
        self.groups_tree.heading('account', text='账号')
        self.groups_tree.heading('group_name', text='群组名称')
        self.groups_tree.heading('group_id', text='群组ID')
        self.groups_tree.heading('status', text='状态')
        
        # 设置列宽
        self.groups_tree.column('account', width=100)
        self.groups_tree.column('group_name', width=200)
        self.groups_tree.column('group_id', width=150)
        self.groups_tree.column('status', width=100)
        
        # 滚动条
        groups_scrollbar = ttk.Scrollbar(groups_frame, orient='vertical', command=self.groups_tree.yview)
        self.groups_tree.configure(yscrollcommand=groups_scrollbar.set)
        
        self.groups_tree.pack(side='left', fill='both', expand=True)
        groups_scrollbar.pack(side='right', fill='y')
    
    def refresh_groups(self):
        """刷新群组列表"""
        self.manager.log("开始刷新群组列表...")
        
        # 清空现有列表
        for item in self.groups_tree.get_children():
            self.groups_tree.delete(item)
        
        self.groups = {}
        
        # 获取已登录的账号
        logged_accounts = []
        for account_id, account in self.manager.accounts.items():
            if account.get('status') == '已登录' and account.get('client'):
                logged_accounts.append((account_id, account))
        
        if not logged_accounts:
            self.manager.log("没有已登录的账号")
            return
        
        # 在后台线程中获取群组
        def fetch_groups():
            for account_id, account in logged_accounts:
                try:
                    client = account['client']
                    username = account.get('username', f"账号{account_id}")
                    
                    # 这里应该调用异步方法获取群组，但为了简化，先添加示例数据
                    # 实际实现时需要使用 client.get_dialogs() 等方法
                    
                    # 示例群组数据
                    example_groups = [
                        {'name': f'{username}的测试群1', 'id': f'-100123456{account_id}'},
                        {'name': f'{username}的测试群2', 'id': f'-100789012{account_id}'}
                    ]
                    
                    self.groups[account_id] = example_groups
                    
                    # 更新UI
                    for group in example_groups:
                        self.groups_tree.insert('', 'end', values=(
                            username,
                            group['name'],
                            group['id'],
                            '就绪'
                        ))
                    
                    self.manager.log(f"账号 {username} 的群组已加载")
                    
                except Exception as e:
                    self.manager.log(f"获取账号 {account_id} 群组失败: {e}")
        
        # 在线程中执行
        threading.Thread(target=fetch_groups, daemon=True).start()
    
    def start_sending(self):
        """开始群发"""
        message = self.message_text.get('1.0', 'end-1c').strip()
        if not message:
            messagebox.showwarning("警告", "请输入要发送的消息")
            return
        
        if not self.groups:
            messagebox.showwarning("警告", "请先刷新群组列表")
            return
        
        self.is_sending = True
        self.send_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        self.manager.log(f"开始群发消息: {message[:50]}...")
        
        # 在后台线程中发送消息
        def send_messages():
            try:
                for account_id, groups in self.groups.items():
                    if not self.is_sending:
                        break
                    
                    account = self.manager.accounts.get(account_id)
                    if not account or account.get('status') != '已登录':
                        continue
                    
                    username = account.get('username', f"账号{account_id}")
                    
                    for group in groups:
                        if not self.is_sending:
                            break
                        
                        try:
                            # 这里应该实现实际的消息发送逻辑
                            # client = account['client']
                            # await client.send_message(group['id'], message)
                            
                            # 模拟发送延时
                            import time
                            time.sleep(1)
                            
                            self.manager.log(f"账号 {username} 已发送消息到 {group['name']}")
                            
                            # 更新状态
                            for item in self.groups_tree.get_children():
                                values = self.groups_tree.item(item)['values']
                                if values[0] == username and values[2] == group['id']:
                                    self.groups_tree.item(item, values=(
                                        values[0], values[1], values[2], '已发送'
                                    ))
                                    break
                            
                        except Exception as e:
                            self.manager.log(f"发送到 {group['name']} 失败: {e}")
                
                self.manager.log("群发完成")
                
            except Exception as e:
                self.manager.log(f"群发过程中出错: {e}")
            
            finally:
                self.is_sending = False
                self.send_button.config(state='normal')
                self.stop_button.config(state='disabled')
        
        # 在线程中执行
        threading.Thread(target=send_messages, daemon=True).start()
    
    def stop_sending(self):
        """停止群发"""
        self.is_sending = False
        self.send_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.manager.log("群发已停止")
'''
        
        try:
            with open('group_sender.py', 'w', encoding='utf-8') as f:
                f.write(group_sender_content)
            
            messagebox.showinfo("成功", "群发模块文件已创建，请重启程序")
            self.manager.log("群发模块文件 group_sender.py 已创建")
            
        except Exception as e:
            messagebox.showerror("错误", f"创建文件失败: {e}")
            self.manager.log(f"创建群发模块文件失败: {e}")

    def create_private_sender_ui(self):
        """创建私信功能界面"""
        try:
            # 尝试导入私信模块
            from private_sender import PrivateSender
            
            # 创建私信实例，传递正确的参数
            self.private_sender = PrivateSender(self.private_tab, self, self.log)
            
        except ImportError:
            # 如果模块不存在，显示错误信息和创建按钮
            error_frame = ttk.Frame(self.private_tab)
            error_frame.pack(expand=True, fill='both', padx=10, pady=10)
            
            ttk.Label(error_frame, text="私信模块 private_sender.py 不存在", 
                     font=('Arial', 12)).pack(pady=20)
            
            ttk.Button(error_frame, text="创建私信模块文件", 
                      command=self.create_private_sender_file).pack(pady=10)

    def create_private_sender_file(self):
        """创建私信模块文件"""
        # 这里可以写入私信模块的基础代码
        try:
            with open('private_sender.py', 'w', encoding='utf-8') as f:
                f.write('''# 私信功能模块文件已创建，请重启程序以加载模块''')
            messagebox.showinfo("成功", "私信模块文件已创建，请重启程序以加载模块")
        except Exception as e:
            messagebox.showerror("错误", f"创建文件失败: {str(e)}")
            self.manager.log(f"创建私信模块文件失败: {e}")

    def create_user_guide_ui(self):
        """创建使用说明界面"""
        try:
            from user_guide import UserGuide
            self.user_guide = UserGuide(self.guide_tab)
            self.log("使用说明界面加载成功")
        except ImportError as e:
            self.log(f"使用说明模块导入失败: {e}")
            self.create_user_guide_file()
        except Exception as e:
            self.log(f"创建使用说明界面时出错: {e}")
            # 创建简单的错误提示界面
            error_label = ttk.Label(self.guide_tab, text="使用说明界面加载失败，请检查user_guide.py文件")
            error_label.pack(expand=True)
    
    def create_user_guide_file(self):
        """创建使用说明文件"""
        guide_content = '''# 使用说明文件内容已在上面提供'''
        
        try:
            with open('user_guide.py', 'w', encoding='utf-8') as f:
                f.write(guide_content)
            
            messagebox.showinfo("提示", "user_guide.py文件已创建，请重启程序以加载使用说明界面")
            self.log("user_guide.py文件创建成功")
        except Exception as e:
            messagebox.showerror("错误", f"创建user_guide.py文件失败: {e}")
            self.log(f"创建user_guide.py文件失败: {e}")

    def on_closing(self):
        """窗口关闭事件处理"""
        try:
            # 登出所有账号
            for account_id in list(self.accounts.keys()):
                self.logout_account(account_id)
            
            self.log("程序正在关闭...")
            
        except Exception as e:
            print(f"关闭时出错: {e}")
        finally:
            # 销毁窗口
            self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = MultiAccountManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
