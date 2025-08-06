# main.py
# -*- coding: utf-8 -*-
import customtkinter as ctk
from ui import NovelGeneratorGUI
from proxy_manager import proxy_manager

def main():
    # 在程序启动时配置代理
    proxy_manager.configure(
        http_proxy="http://127.0.0.1:10808",
        https_proxy="http://127.0.0.1:10808", 
        enabled=True
    )

    # 测试代理连接
    if proxy_manager.test_proxy():
        print("✅ 代理配置成功")
    else:
        print("❌ 代理连接失败")

    app = ctk.CTk()
    gui = NovelGeneratorGUI(app)
    app.mainloop()

if __name__ == "__main__":
    main()
