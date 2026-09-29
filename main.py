# -*- coding: utf-8 -*- 
"""
AI 文字角色扮演游戏 · v2（含手机系统）
零新依赖：tkinter + requests

文件：
  game_config.json    人设/API/附加规则/主题
  game_world.json     地点树、交通时间、服装
  game_state.json     当前时间/位置/穿着
  game_phone.json     手机：平台、联系人、消息
  memory.json         剧情笔记
  summary.json        自动摘要
  chat_history.json   对话记录
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import json
import os
import datetime
import re

import requests

CONFIG_FILE  = "game_config.json"
WORLD_FILE   = "game_world.json"
STATE_FILE   = "game_state.json"
MEMORY_FILE  = "memory.json"
SUMMARY_FILE = "summary.json"
CHAT_FILE    = "chat_history.json"
PHONE_FILE   = "game_phone.json"
RAW_STREAM_FILE = "raw_stream_log.txt"

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ============================================================
# 默认世界
# ============================================================
DEFAULT_WORLD = {
    "locations": [
        {"id": "loc_office", "name": "公司", "emoji": "🏢", "parent": None,
         "children": ["loc_office_room", "loc_office_meeting", "loc_office_tea"],
         "actions": [], "x": None, "y": None, "bg_image": None},
        {"id": "loc_office_room", "name": "办公室", "emoji": "💼", "parent": "loc_office",
         "children": [],
         "actions": [
             {"type": "dialog", "label": "处理文件", "prompt": "我开始处理桌上的文件"},
             {"type": "dialog", "label": "看看窗外", "prompt": "我望向窗外"},
         ], "x": None, "y": None, "bg_image": None},
        {"id": "loc_office_meeting", "name": "会议室", "emoji": "📊", "parent": "loc_office",
         "children": [],
         "actions": [
             {"type": "dialog", "label": "开会", "prompt": "我在会议室主持了一场会议"},
         ], "x": None, "y": None, "bg_image": None},
        {"id": "loc_office_tea", "name": "茶水间", "emoji": "☕", "parent": "loc_office",
         "children": [],
         "actions": [
             {"type": "dialog", "label": "泡杯咖啡", "prompt": "我在茶水间泡了一杯咖啡"},
         ], "x": None, "y": None, "bg_image": None},

        {"id": "loc_home", "name": "家", "emoji": "🏠", "parent": None,
         "children": ["loc_home_living", "loc_home_kitchen", "loc_home_bedroom", "loc_home_bath"],
         "actions": [], "x": None, "y": None, "bg_image": None},
        {"id": "loc_home_living", "name": "客厅", "emoji": "🛋", "parent": "loc_home",
         "children": [],
         "actions": [
             {"type": "dialog", "label": "看电视", "prompt": "我坐在沙发上看电视"},
         ], "x": None, "y": None, "bg_image": None},
        {"id": "loc_home_kitchen", "name": "厨房", "emoji": "🍳", "parent": "loc_home",
         "children": [],
         "actions": [
             {"type": "dialog", "label": "做点吃的", "prompt": "我走进厨房开始做饭"},
         ], "x": None, "y": None, "bg_image": None},
        {"id": "loc_home_bedroom", "name": "卧室", "emoji": "🛏", "parent": "loc_home",
         "children": [],
         "actions": [
             {"type": "dialog", "label": "躺下休息", "prompt": "我躺在床上"},
             {"type": "outfit", "label": "换衣服", "prompt": ""},
         ], "x": None, "y": None, "bg_image": None},
        {"id": "loc_home_bath", "name": "浴室", "emoji": "🚿", "parent": "loc_home",
         "children": [],
         "actions": [
             {"type": "dialog", "label": "洗个澡", "prompt": "我去洗了个澡"},
         ], "x": None, "y": None, "bg_image": None},

        {"id": "loc_bar", "name": "真爱酒吧", "emoji": "🍺", "parent": None,
         "children": [],
         "actions": [
             {"type": "dialog", "label": "进门", "prompt": "我推门走进真爱酒吧"},
             {"type": "dialog", "label": "点一杯酒", "prompt": "我向吧台要了一杯威士忌"},
         ], "x": None, "y": None, "bg_image": None},
        {"id": "loc_hospital", "name": "医院", "emoji": "🏥", "parent": None,
         "children": [],
         "actions": [
             {"type": "dialog", "label": "挂号", "prompt": "我在医院门口排队挂号"},
         ], "x": None, "y": None, "bg_image": None},
    ],

    "travel_time": {
        "loc_office->loc_home": 30,
        "loc_office->loc_bar": 15,
        "loc_office->loc_hospital": 20,
        "loc_home->loc_bar": 25,
        "loc_home->loc_hospital": 10,
        "loc_bar->loc_hospital": 15,
    },
    "default_travel_time": 20,

    "outfits": [
        {"id": "out_home", "name": "居家休闲", "desc": "白T恤 + 宽松长裤",
         "tags": ["休闲", "居家"], "emoji": "👕", "items": ["白T恤", "宽松长裤"]},
        {"id": "out_suit", "name": "正式西装", "desc": "深灰三件套 + 白衬衫 + 皮鞋",
         "tags": ["正式", "商务"], "emoji": "🤵",
         "items": ["深灰西装", "白衬衫", "领带", "皮鞋"]},
        {"id": "out_casual", "name": "外出便装", "desc": "夹克 + 牛仔裤 + 运动鞋",
         "tags": ["休闲", "外出"], "emoji": "🧥",
         "items": ["夹克", "牛仔裤", "运动鞋"]},
    ],

    "npcs": [],
}

DEFAULT_STATE = {
    "current_location": "loc_home_living",
    "current_time": "2024-09-02 09:00:00",
    "current_outfit": "out_home",
}

DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "temperature": 0.85,
    "max_tokens": 2048,
    "font_family": "Microsoft YaHei",
    "font_size": 13,
    "theme": "深色",
    "system_prompt": "你是一个文字冒险游戏的剧情引擎。请根据玩家的行动推进剧情。",
    "global_extra_prompt": "",
    "recent_limit": 20,
    "summary_trigger": 30,
}

DEFAULT_PHONE = {
    "platforms": [
        {
            "id": "微信",
            "name": "微信",
            "icon": "💬",
            "color": "#07c160",
            "keywords": ["微信", "wechat", "微信号", "加个微信"],
            "contacts": [],
            "groups": []
        }
    ]
}

THEMES = {
    "深色": {
        "bg": "#1e1e1e", "panel": "#252526", "input_bg": "#2d2d30",
        "fg": "#d4d4d4", "user_fg": "#4fc3f7", "ai_fg": "#a5d6a7",
        "sys_fg": "#ffb74d", "btn_bg": "#3c3c3c", "btn_fg": "#e0e0e0",
        "select_bg": "#094771", "map_bg": "#1a1a1a",
    },
    "浅色": {
        "bg": "#f5f5f5", "panel": "#ffffff", "input_bg": "#ffffff",
        "fg": "#212121", "user_fg": "#1565c0", "ai_fg": "#2e7d32",
        "sys_fg": "#e65100", "btn_bg": "#e0e0e0", "btn_fg": "#212121",
        "select_bg": "#bbdefb", "map_bg": "#eaeaea",
    },
    "护眼绿": {
        "bg": "#c7edcc", "panel": "#d8f3dc", "input_bg": "#e8f8ea",
        "fg": "#1b3a1f", "user_fg": "#0d47a1", "ai_fg": "#1b5e20",
        "sys_fg": "#bf360c", "btn_bg": "#a5d6a7", "btn_fg": "#1b3a1f",
        "select_bg": "#80cbc4", "map_bg": "#b8dcc0",
    },
    "羊皮纸": {
        "bg": "#f4ecd8", "panel": "#fbf5e6", "input_bg": "#fffaf0",
        "fg": "#3b2f1e", "user_fg": "#8b4513", "ai_fg": "#556b2f",
        "sys_fg": "#a0522d", "btn_bg": "#e6d9bd", "btn_fg": "#3b2f1e",
        "select_bg": "#d9c7a3", "map_bg": "#e8dfc8",
    },
}

# ============================================================
# 工具
# ============================================================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return json.loads(json.dumps(default))


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_time(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def fmt_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def weekday_of(s):
    return WEEKDAYS[parse_time(s).weekday()]


# 手机标记解析
# 宽松版：结尾标记允许带参数、空格、大小写
_END_PHONE = r"\[\[\s*/\s*PHONE[^\]]*\]\]"
_END_PHONE_IN = r"\[\[\s*/\s*PHONE_IN[^\]]*\]\]"
_END_PHONE_GROUP = r"\[\[\s*/\s*PHONE_GROUP[^\]]*\]\]"

RE_PHONE = re.compile(
    r"\[\[\s*PHONE\s*:\s*([^:\]]+?)\s*:\s*([^\]]+?)\s*\]\](.*?)" + _END_PHONE,
    re.S | re.I)
RE_PHONE_IN = re.compile(
    r"\[\[\s*PHONE_IN\s*:\s*([^:\]]+?)\s*:\s*([^\]]+?)\s*\]\](.*?)" + _END_PHONE_IN,
    re.S | re.I)
RE_NEW_PLATFORM = re.compile(r"\[\[NEW_PLATFORM:([^\]]+)\]\]")
RE_ADD_CONTACT = re.compile(r"\[\[ADD_CONTACT:([^:]+):([^:]+):([^\]]*)\]\]")
RE_PHONE_GROUP = re.compile(
    r"\[\[\s*PHONE_GROUP\s*:\s*([^:]+?)\s*:\s*([^:]+?)\s*:\s*([^\]]+?)\s*\]\](.*?)" + _END_PHONE_GROUP,
    re.S | re.I)
# 兜底版：只有开头，没结尾。匹配到下一个 [[ 或字符串结束为止
RE_PHONE_LOOSE = re.compile(
    r"\[\[\s*PHONE\s*:\s*([^:\]]+?)\s*:\s*([^\]]+?)\s*\]\]([^\n\[]*)",
    re.S | re.I)
RE_PHONE_IN_LOOSE = re.compile(
    r"\[\[\s*PHONE_IN\s*:\s*([^:\]]+?)\s*:\s*([^\]]+?)\s*\]\]([^\n\[]*)",
    re.S | re.I)
RE_PHONE_GROUP_LOOSE = re.compile(
    r"\[\[\s*PHONE_GROUP\s*:\s*([^:]+?)\s*:\s*([^:]+?)\s*:\s*([^\]]+?)\s*\]\]([^\n\[]*)",
    re.S | re.I)

# ============================================================
# 主程序
# ============================================================
class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 文字角色扮演")
        # 自适应窗口大小，避开任务栏
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(1280, sw - 80)
        h = min(840, sh - 120)
        x = (sw - w) // 2
        y = (sh - h) // 2 - 20
        self.root.geometry(f"{w}x{h}+{max(x,0)}+{max(y,0)}")

        self.config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
        self.world  = load_json(WORLD_FILE,  DEFAULT_WORLD)
        self.state  = load_json(STATE_FILE,  DEFAULT_STATE)
        self.memory_note = load_json(MEMORY_FILE, {"note": ""}).get("note", "")
        self.summary_text = load_json(SUMMARY_FILE, {"summary": ""}).get("summary", "")
        self.messages = load_json(CHAT_FILE, [])
        self.phone = load_json(PHONE_FILE, DEFAULT_PHONE)
        # 兼容：老数据没有 groups 字段
        for _p in self.phone.get("platforms", []):
            _p.setdefault("groups", [])

        self.is_generating = False
        self.summarizing = False

        self.font_family = self.config.get("font_family", "Microsoft YaHei")
        self.font_size   = self.config.get("font_size", 13)
        self.theme_name  = self.config.get("theme", "深色")
        self.theme       = THEMES.get(self.theme_name, THEMES["深色"]).copy()

        self.system_prompt        = self.config.get("system_prompt", "")
        self.global_extra_prompt  = self.config.get("global_extra_prompt", "")
        self.recent_limit         = int(self.config.get("recent_limit", 20))
        self.summary_trigger      = int(self.config.get("summary_trigger", 30))

        self.selected_top = self._find_top_of(self.state.get("current_location"))

        # 手机窗口状态
        self._phone_win = None
        self._phone_plat_idx = 0
        self._phone_contact_idx = -1
        self._phone_group_idx = -1
        self._phone_tip_count = 0
        self._phone_last_jump_plat = None

        self.build_ui()
        self.apply_theme()
        self.refresh_map()
        self.refresh_location_panel()
        self.refresh_status()
        self.render_history()
        self._update_action_buttons()

    # ============================================================
    # 数据访问
    # ============================================================
    def get_loc(self, lid):
        for L in self.world["locations"]:
            if L["id"] == lid:
                return L
        return None

    def children_of(self, lid):
        L = self.get_loc(lid)
        if not L:
            return []
        return [self.get_loc(c) for c in L.get("children", []) if self.get_loc(c)]

    def tops(self):
        return [L for L in self.world["locations"] if L.get("parent") is None]

    def _find_top_of(self, lid):
        L = self.get_loc(lid)
        if not L:
            tops = self.tops()
            return tops[0]["id"] if tops else None
        while L.get("parent"):
            L = self.get_loc(L["parent"])
        return L["id"] if L else None

    def travel_minutes(self, a, b):
        if a == b:
            return 0
        top_a = self._find_top_of(a)
        top_b = self._find_top_of(b)
        if top_a == top_b:
            return 0
        tt = self.world.get("travel_time", {})
        for k in (f"{a}->{b}", f"{b}->{a}",
                  f"{top_a}->{top_b}", f"{top_b}->{top_a}"):
            if k in tt:
                try:
                    return int(tt[k])
                except (ValueError, TypeError):
                    pass
        return int(self.world.get("default_travel_time", 20))

    # ============================================================
    # 保存
    # ============================================================
    def save_config(self):
        self.config["font_family"] = self.font_family
        self.config["font_size"] = self.font_size
        self.config["theme"] = self.theme_name
        self.config["system_prompt"] = self.system_prompt
        self.config["global_extra_prompt"] = self.global_extra_prompt
        self.config["recent_limit"] = self.recent_limit
        self.config["summary_trigger"] = self.summary_trigger
        save_json(CONFIG_FILE, self.config)

    def save_world(self):
        save_json(WORLD_FILE, self.world)

    def save_state(self):
        save_json(STATE_FILE, self.state)

    def save_memory(self):
        save_json(MEMORY_FILE, {"note": self.memory_note})

    def save_summary(self):
        save_json(SUMMARY_FILE, {"summary": self.summary_text})

    def save_chat(self):
        save_json(CHAT_FILE, self.messages)

    def save_phone(self):
        save_json(PHONE_FILE, self.phone)

    # ============================================================
    # UI
    # ============================================================
    def build_ui(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side="top", fill="x", padx=6, pady=4)

        self.btn_setting = tk.Button(toolbar, text="⚙ 设置", command=self.open_settings)
        self.btn_note = tk.Button(toolbar, text="📌 笔记", command=self.open_note_window)
        self.btn_phone = tk.Button(toolbar, text="📱 手机", command=self.open_phone_window)
        self.btn_outfits = tk.Button(toolbar, text="👕 服装库", command=self.open_outfit_editor)
        self.btn_theme = tk.Button(toolbar, text="🎨 配色", command=self.cycle_theme)

        self.btn_del_user = tk.Button(toolbar, text="🗑 删我的", command=self.delete_my_last)
        self.btn_regen    = tk.Button(toolbar, text="🔄 重生成", command=self.regenerate_last_ai)
        self.btn_del_ai   = tk.Button(toolbar, text="🗑 删AI+我的", command=self.delete_ai_and_after)

        self.btn_clear = tk.Button(toolbar, text="🗑 清空对话", command=self.clear_chat)
        self.btn_save  = tk.Button(toolbar, text="💾 导出", command=self.export_chat)

        for b in (self.btn_setting, self.btn_note, self.btn_phone, self.btn_outfits, self.btn_theme,
                  self.btn_del_user, self.btn_regen, self.btn_del_ai,
                  self.btn_clear, self.btn_save):
            b.pack(side="left", padx=3)

        self.status_label = tk.Label(toolbar, text="就绪")
        self.status_label.pack(side="right", padx=10)

        main = tk.PanedWindow(self.root, orient="horizontal", sashwidth=6)
        main.pack(fill="both", expand=True, padx=6, pady=4)

        left = tk.Frame(main)
        main.add(left, minsize=220, width=250)

        tk.Label(left, text="🗺 城市地图").pack(anchor="w", padx=6, pady=(6, 2))
        self.map_tops_frame = tk.Frame(left)
        self.map_tops_frame.pack(fill="x", padx=6, pady=(0, 6))

        tk.Label(left, text="📍 当前地点的子区域").pack(anchor="w", padx=6, pady=(6, 2))
        self.map_children_frame = tk.Frame(left)
        self.map_children_frame.pack(fill="x", padx=6, pady=(0, 6))

        tk.Frame(left, height=1).pack(fill="x", padx=6, pady=6)
        tk.Button(left, text="📝 编辑地图", command=self.open_map_editor).pack(fill="x", padx=6, pady=(0, 6))

        right = tk.Frame(main)
        main.add(right, minsize=600)

        self.info_label = tk.Label(right, text="", anchor="w", justify="left")
        self.info_label.pack(fill="x", padx=6, pady=(4, 4))

        self.actions_frame = tk.Frame(right)
        self.actions_frame.pack(fill="x", padx=6, pady=(0, 6))

        chat_frame = tk.Frame(right)
        chat_frame.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        self.chat_display = tk.Text(chat_frame, wrap="word", state="disabled",
                                    padx=12, pady=10, relief="flat", cursor="arrow")
        sb = ttk.Scrollbar(chat_frame, command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.chat_display.pack(side="left", fill="both", expand=True)

        bottom = tk.Frame(right)
        bottom.pack(fill="x", padx=6, pady=(0, 6))
        self.input_text = tk.Text(bottom, height=4, wrap="word")
        self.input_text.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.input_text.bind("<Control-Return>", lambda e: (self.send_message(), "break"))

        btn_box = tk.Frame(bottom)
        btn_box.pack(side="right", fill="y")
        self.btn_send = tk.Button(btn_box, text="发送\n(Ctrl+Enter)",
                                  command=self.send_message, width=14)
        self.btn_send.pack(fill="both", expand=True)

    # ============================================================
    # 地图渲染
    # ============================================================
    def refresh_map(self):
        for w in self.map_tops_frame.winfo_children():
            w.destroy()
        for w in self.map_children_frame.winfo_children():
            w.destroy()

        current = self.state.get("current_location")
        current_top = self._find_top_of(current)

        for L in self.tops():
            is_cur_top = (L["id"] == current_top)
            mark = "▶" if is_cur_top else "  "
            text = f"{mark} {L['emoji']} {L['name']}"
            b = tk.Button(self.map_tops_frame, text=text, anchor="w",
                          command=lambda lid=L["id"]: self.select_top(lid))
            b.pack(fill="x", pady=1)
            if is_cur_top:
                b.configure(relief="sunken")

        children = self.children_of(current_top) if current_top else []
        if not children:
            tk.Label(self.map_children_frame, text="（无子区域）",
                     font=("", 8)).pack(anchor="w")
        for c in children:
            is_cur = (c["id"] == current)
            mark = "●" if is_cur else "○"
            text = f"{mark} {c['emoji']} {c['name']}"
            b = tk.Button(self.map_children_frame, text=text, anchor="w",
                          command=lambda lid=c["id"]: self.go_location(lid))
            b.pack(fill="x", pady=1)
            if is_cur:
                b.configure(relief="sunken")

    def select_top(self, lid):
        L = self.get_loc(lid)
        if not L:
            return
        if self._find_top_of(self.state.get("current_location")) == lid:
            return
        target = L["id"]
        if L.get("children"):
            first = self.get_loc(L["children"][0])
            if first:
                target = first["id"]
        self.go_location(target)

    def go_location(self, lid):
        old = self.state.get("current_location")
        if old == lid:
            return
        minutes = self.travel_minutes(old, lid)
        # 更新程序内部时间（不显示，只记录）
        if minutes > 0:
            try:
                cur = parse_time(self.state["current_time"])
                cur += datetime.timedelta(minutes=minutes)
                self.state["current_time"] = fmt_time(cur)
            except Exception:
                pass
        self.state["current_location"] = lid
        self.save_state()

        self.refresh_map()
        self.refresh_location_panel()
        self.refresh_status()

        old_loc = self.get_loc(old)
        new_loc = self.get_loc(lid)
        if not (old_loc and new_loc):
            return

        # 判断是同建筑内移动还是跨顶层
        top_old = self._find_top_of(old)
        top_new = self._find_top_of(lid)
        same_building = (top_old == top_new and top_old is not None)

        # 取顶层名字（跨建筑移动时用）
        top_old_loc = self.get_loc(top_old)
        top_new_loc = self.get_loc(top_new)
        top_old_name = top_old_loc["name"] if top_old_loc else old_loc["name"]
        top_new_name = top_new_loc["name"] if top_new_loc else new_loc["name"]

        if same_building:
            # 同建筑内：只填入输入框，不自动发送
            if minutes > 0:
                tip = f"（我离开{old_loc['name']}，前往{new_loc['name']}，路上花了约{minutes}分钟）"
            else:
                tip = f"（我从{old_loc['name']}走到{new_loc['name']}）"
            self._fill_input(tip)
        else:
            # 跨顶层：用顶层地名，自动发送
            if minutes > 0:
                tip = f"（我离开{top_old_name}，前往{top_new_name}，路上花了约{minutes}分钟）"
            else:
                tip = f"（我离开{top_old_name}，前往{top_new_name}）"
            self._auto_send(tip)

    # ============================================================
    # 自动发送消息（移动时用，不走输入框）
    # ============================================================
    def _auto_send(self, text):
        """自动发送一条消息给 AI（不走输入框）"""
        if self.is_generating:
            self.set_status("⚠ AI 正在生成中，移动消息未自动发送")
            return
        key = self.config.get("api_key", "").strip()
        base = self.config.get("base_url", "").strip()
        model = self.config.get("model", "").strip()
        if not key or not base or not model:
            return

        self.messages.append({"role": "user", "content": text})
        self.append_chat("你", text, "user")
        self.save_chat()

        self.is_generating = True
        self.btn_send.configure(state="disabled")
        self._update_action_buttons()
        self.set_status("生成中…")
        threading.Thread(target=self._request_stream, daemon=True).start()

    # ============================================================
    # 地点面板 + 状态
    # ============================================================
    def refresh_location_panel(self):
        for w in self.actions_frame.winfo_children():
            w.destroy()

        lid = self.state.get("current_location")
        L = self.get_loc(lid)
        if not L:
            return

        actions = L.get("actions", [])
        if not actions:
            tk.Label(self.actions_frame,
                     text="（此地点暂无快捷动作，直接在下方输入框描述你的行动）",
                     font=("", 9)).pack(anchor="w")

        for a in actions:
            label = f"{a.get('label', '动作')}"
            b = tk.Button(self.actions_frame, text=label,
                          command=lambda act=a: self.do_action(act))
            b.pack(side="left", padx=3, pady=2)

    def do_action(self, action):
        t = action.get("type", "dialog")
        if t == "dialog":
            self._fill_input(action.get("prompt", ""))
        elif t == "outfit":
            self.open_outfit_picker()
        else:
            self._fill_input(action.get("prompt", ""))

    def _fill_input(self, text):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", text)
        self.input_text.focus_set()

    def refresh_status(self):
        lid = self.state.get("current_location")
        L = self.get_loc(lid)
        loc_name = L["name"] if L else "?"
        if L and L.get("parent"):
            P = self.get_loc(L["parent"])
            if P:
                loc_name = f"{P['name']} · {L['name']}"

        out = None
        for o in self.world.get("outfits", []):
            if o["id"] == self.state.get("current_outfit"):
                out = o
                break
        out_text = f"{out['emoji']} {out['name']}（{out['desc']}）" if out else "（未设置）"

        # 时间字段照常维护（存 JSON），但界面不显示
        self.info_label.configure(
            text=f"📍 {loc_name}    👕 {out_text}"
        )

    # ============================================================
    # 换装
    # ============================================================
    def open_outfit_picker(self):
        win = tk.Toplevel(self.root)
        win.title("👕 换衣服")
        win.geometry("460x500")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="选择一套穿上：").pack(anchor="w", padx=10, pady=(10, 4))

        # ===== 可滚动区 =====
        # 用 Canvas + Frame 实现滚动
        container = tk.Frame(win)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 让 scroll_frame 宽度跟随 canvas
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # 鼠标滚轮
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        # Linux 兼容
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 把服装按钮放进 scroll_frame
        for o in self.world.get("outfits", []):
            is_cur = (o["id"] == self.state.get("current_outfit"))
            txt = f"{o['emoji']} {o['name']} - {o['desc']}"
            if is_cur:
                txt += "  ✔ 当前"
            b = tk.Button(scroll_frame, text=txt, anchor="w",
                          command=lambda oid=o["id"]: self._pick_outfit(oid, win))
            b.pack(fill="x", pady=2)

        # ===== 底部按钮 =====
        bf = tk.Frame(win)
        bf.pack(fill="x", pady=(0, 8))
        tk.Button(bf, text="取消", command=lambda: self._close_outfit_picker(win)).pack()

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x,0)}+{max(y,0)}")

    def _close_outfit_picker(self, win):
        """关闭换装窗，同时解绑鼠标滚轮"""
        try:
            win.unbind_all("<MouseWheel>")
            win.unbind_all("<Button-4>")
            win.unbind_all("<Button-5>")
        except Exception:
            pass
        win.destroy()

    def _pick_outfit(self, oid, win):
        self.state["current_outfit"] = oid
        self.save_state()
        out = None
        for o in self.world.get("outfits", []):
            if o["id"] == oid:
                out = o
                break
        self.refresh_status()
        self._fill_input(f"我换上了{out['name']}（{out['desc']}）" if out else "我换了一身衣服")
        self._close_outfit_picker(win)

    # ============================================================
    # 主题
    # ============================================================
    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg"])

        def recolor(w):
            cls = w.winfo_class()
            try:
                if cls in ("Frame", "PanedWindow", "Toplevel"):
                    w.configure(bg=t["bg"])
                elif cls == "Label":
                    w.configure(bg=t["bg"], fg=t["fg"])
                elif cls == "Button":
                    w.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                activebackground=t["select_bg"], activeforeground=t["btn_fg"],
                                relief="flat", bd=1, padx=6, pady=2)
                elif cls == "Text":
                    w.configure(bg=t["input_bg"], fg=t["fg"],
                                insertbackground=t["fg"], selectbackground=t["select_bg"])
            except tk.TclError:
                pass
            for c in w.winfo_children():
                recolor(c)

        recolor(self.root)

        self.chat_display.configure(bg=t["panel"], fg=t["fg"])
        self.chat_display.tag_configure("user_name",
            foreground=t["user_fg"], font=(self.font_family, self.font_size, "bold"))
        self.chat_display.tag_configure("ai_name",
            foreground=t["ai_fg"], font=(self.font_family, self.font_size, "bold"))
        self.chat_display.tag_configure("sys_name",
            foreground=t["sys_fg"], font=(self.font_family, self.font_size, "bold"))
        self.chat_display.tag_configure("body",
            foreground=t["fg"], font=(self.font_family, self.font_size))
        self.chat_display.tag_configure("phone_tip",
            foreground=t["user_fg"],
            font=(self.font_family, self.font_size, "underline"))

    def cycle_theme(self):
        names = list(THEMES.keys())
        i = names.index(self.theme_name) if self.theme_name in names else 0
        self.theme_name = names[(i + 1) % len(names)]
        self.theme = THEMES[self.theme_name].copy()
        self.apply_theme()
        self.save_config()
        self.set_status(f"主题：{self.theme_name}")

    # ============================================================
    # 对话：请求
    # ============================================================
    def _build_phone_protocol(self):
        """手机协议追加到 system message"""
        plat_lines = []
        for p in self.phone.get("platforms", []):
            plat_lines.append(f"平台：{p['name']}")
            for g in p.get("groups", []):
                member_names = []
                for mid in g.get("member_ids", []):
                    for c in p.get("contacts", []):
                        if c["id"] == mid:
                            member_names.append(c["name"])
                            break
                plat_lines.append(f"  群「{g['name']}」成员：{','.join(member_names)}")
        plat_block = "\n".join(plat_lines) if plat_lines else "  （暂无）"

        return (
            "【手机通讯协议】\n"
            "当剧情中出现手机相关的互动时，请严格使用以下标记（标记不会显示给玩家）：\n"
            "\n"
            "私聊对方回复你刚发的消息，用：\n"
            "[[PHONE:平台名:联系人名]]内容[[/PHONE]]\n"
            "\n"
            "私聊对方主动给你发消息，用：\n"
            "[[PHONE_IN:平台名:联系人名]]内容[[/PHONE_IN]]\n"
            "\n"
            "群成员在群里发言，用：\n"
            "[[PHONE_GROUP:平台名:群名:发言人名]]内容[[/PHONE_GROUP]]\n"
            "玩家发出的群消息前缀是 [手机·平台·群「群名」]。\n"
            "收到后你让 1 到 3 个群成员各回一条，每条都用 [[PHONE_GROUP:...]] 标记。\n"
            "发言人必须是该群成员，性格要符合。\n"
            "\n"
            "剧情中提到一个新平台，用：\n"
            "[[NEW_PLATFORM:平台名]]\n"
            "\n"
            "剧情中互加该平台好友，用：\n"
            "[[ADD_CONTACT:平台名:联系人名:角色id]]\n"
            "角色id可留空，写成 [[ADD_CONTACT:平台名:联系人名:]]\n"
            "\n"
            "当前已存在的平台及群：\n"
            f"{plat_block}\n"
            "\n"
            "【重要规则】\n"
            "玩家说我看某平台的私信或消息时：\n"
            "用一句话叙述，例如：你点开墨渊，未读消息不少。\n"
            "然后用 [[PHONE_IN:平台:联系人]]消息[[/PHONE_IN]] 逐条列出消息。\n"
            "不要在叙述里重复消息内容。\n"
            "\n"
            "玩家说给某某发消息时：\n"
            "用一句话叙述，例如：你给林晚发了条微信。\n"
            "对方的回复用 [[PHONE:平台:联系人]]内容[[/PHONE]]。\n"
            "\n"
            "玩家在群里发消息时（前缀 [手机·平台·群「群名」]）：\n"
            "用一句话叙述，例如：你在律所群里发了消息。\n"
            "硬性要求：必须用 [[PHONE_GROUP:平台:群名:成员名]]内容[[/PHONE_GROUP]] 标记对方的具体发言。\n"
            "至少 1 条、最多 3 条。\n"
            "禁止只写叙述不输出标记，例如苏念回了一句这种概括不算。\n"
            "\n"
            "玩家发了一张图时（前缀带 [图片：描述]）：\n"
            "按描述理解图片内容，自然地回应。\n"
            "同样要用 [[PHONE:...]] 或 [[PHONE_GROUP:...]] 标记对方的回复。\n"
            "不要把 [图片：...] 当普通文字复述。\n"
            "\n"
            "【格式强制】\n"
            "禁止使用任何 Markdown 语法：不要 # 标题，不要 ** 加粗，不要 ` 反引号，不要 - 或 * 列表，不要 --- 分隔线。全部纯文本。\n"
            "\n"
            "示例：\n"
            "玩家输入：[手机·微信·群「律所群」] 明天开会改到下午三点\n"
            "你的回复：你在群里发了消息。"
            "[[PHONE_GROUP:微信:律所群:林晚]]收到，我调整一下日程[[/PHONE_GROUP]]"
            "[[PHONE_GROUP:微信:律所群:叶梅]]啊？我下午有客户，能不能四点[[/PHONE_GROUP]]"
        )

    def _build_system_message(self):
        lid = self.state.get("current_location")
        L = self.get_loc(lid)
        loc_full = L["name"] if L else "?"
        if L and L.get("parent"):
            P = self.get_loc(L["parent"])
            if P:
                loc_full = f"{P['name']} · {L['name']}"

        out = None
        for o in self.world.get("outfits", []):
            if o["id"] == self.state.get("current_outfit"):
                out = o
                break
        out_text = f"{out['name']}（{out['desc']}）" if out else "（未设置）"

        parts = []
        if self.system_prompt:
            parts.append(self.system_prompt)
        if self.global_extra_prompt:
            parts.append("【全局附加规则/风格要求】\n" + self.global_extra_prompt)
        parts.append(self._build_phone_protocol())
        parts.append(f"【当前位置】{loc_full}")
        parts.append(f"【当前穿着】{out_text}")
        if self.summary_text:
            parts.append("【前情提要·自动摘要】\n" + self.summary_text)
        if self.memory_note:
            parts.append("【玩家手记·剧情笔记】\n" + self.memory_note)
        return "\n\n".join(parts)

    def send_message(self):
        if self.is_generating:
            return
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            return

        key = self.config.get("api_key", "").strip()
        base = self.config.get("base_url", "").strip()
        model = self.config.get("model", "").strip()
        if not key or not base or not model:
            messagebox.showwarning("提示", "请先在『设置』里填写 API Key / Base URL / 模型")
            return

        self.input_text.delete("1.0", "end")
        self.messages.append({"role": "user", "content": text})
        self.append_chat("你", text, "user")
        self.save_chat()

        self.is_generating = True
        self.btn_send.configure(state="disabled")
        self._update_action_buttons()
        self.set_status("生成中…")
        threading.Thread(target=self._request_stream, daemon=True).start()

    def _request_stream(self):
        key = self.config.get("api_key", "").strip()
        base = self.config.get("base_url", "").strip().rstrip("/")
        model = self.config.get("model", "").strip()
        temperature = float(self.config.get("temperature", 0.85))
        max_tokens = int(self.config.get("max_tokens", 2048))

        recent = self.messages[-self.recent_limit:] if self.recent_limit > 0 else self.messages

        url = f"{base}/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": self._build_system_message()}] + recent,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        self.root.after(0, self._start_ai_block)
        full = ""
        raw_stream_chunks = []       # ★ 记录原始 chunk
        finish_seen = False          # ★ 是否收到 [DONE]
        status_code = None           # ★ HTTP 状态码
        try:
            with requests.post(url, headers=headers, json=payload,
                               stream=True, timeout=60) as resp:
                status_code = resp.status_code       # ★ 记录
                if resp.status_code != 200:
                    err = f"\n[HTTP {resp.status_code}] {resp.text[:300]}\n"
                    self.root.after(0, self._append_ai_chunk, err)
                    self.root.after(0, lambda: self.set_status(f"HTTP {resp.status_code}"))
                    return

                for raw in resp.iter_lines(decode_unicode=False):
                    if not raw:
                        continue
                    try:
                        line = raw.decode("utf-8", errors="replace").strip()
                    except Exception:
                        continue
                    # ★ 记录原始行（截断到 500 字）
                    raw_stream_chunks.append(line[:500] + "\n")
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        finish_seen = True           # ★ 记录
                        break
                    try:
                        obj = json.loads(data)

                        # ★ 检查 finish_reason（是否被审核截断）
                        choices = obj.get("choices", [])
                        if choices:
                            fr = choices[0].get("finish_reason")
                            if fr and fr != "stop":
                                raw_stream_chunks.append(f"[finish_reason={fr}]\n")
                                if fr == "sensitive":
                                    msg = "\n\n⚠ 内容被平台审核截断（sensitive）\n"
                                    self.root.after(0, self._append_ai_chunk, msg)
                                    self.root.after(0, lambda: self.set_status("审核截断"))
                                elif fr == "length":
                                    msg = "\n\n⚠ 输出长度达到上限（max_tokens）\n"
                                    self.root.after(0, self._append_ai_chunk, msg)
                                    self.root.after(0, lambda: self.set_status("长度截断"))

                        delta = obj["choices"][0].get("delta", {})
                        piece = delta.get("content")
                        if piece:
                            full += piece
                            # 流式显示时也剥掉手机标记（部分显示）
                            display_piece = self._strip_phone_for_display(piece, streaming=True)
                            if display_piece:
                                self.root.after(0, self._append_ai_chunk, display_piece)
                        # ★ 记录 reasoning_content（如果有）
                        reason = delta.get("reasoning_content")
                        if reason:
                            raw_stream_chunks.append(f"[思考]{reason[:200]}\n")
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

            if full:
                # 完整处理
                self._post_process_ai_reply(full)

            self.root.after(0, self._maybe_summarize)
            self.root.after(0, lambda: self.set_status("就绪"))
        except requests.exceptions.Timeout:
            self.root.after(0, self._append_ai_chunk, "\n[错误] 请求超时\n")
            self.root.after(0, lambda: self.set_status("超时"))
        except requests.exceptions.RequestException as e:
            self.root.after(0, self._append_ai_chunk, f"\n[网络错误] {e}\n")
            self.root.after(0, lambda: self.set_status("网络错误"))
        except Exception as e:
            self.root.after(0, self._append_ai_chunk, f"\n[错误] {e}\n")
            self.root.after(0, lambda: self.set_status("错误"))
        finally:
            # ★ 写原始流日志
            try:
                with open(RAW_STREAM_FILE, "a", encoding="utf-8") as _f:
                    _f.write("\n" + "=" * 70 + "\n")
                    _f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                    _f.write(f"model={model}  status={status_code}\n")
                    _f.write(f"max_tokens={max_tokens}  "
                             f"recent_limit={self.recent_limit}\n")
                    _f.write(f"finish_seen={finish_seen}  full_len={len(full)}\n")
                    _f.write("-" * 70 + "\n")
                    _f.write("[完整输出]\n")
                    _f.write(full + "\n")
                    _f.write("-" * 70 + "\n")
                    _f.write("[原始 chunk]\n")
                    _f.write("".join(raw_stream_chunks) if raw_stream_chunks else "（无）")
                    _f.write("\n" + "=" * 70 + "\n")
            except Exception:
                pass
            self.root.after(0, self._finish_generation)

    # --------- 手机标记处理 ---------
    def _strip_phone_for_display(self, text, streaming=False):
        """流式显示时，删掉 [[...]] 标记"""
        # 标准版（有闭合）
        text = RE_PHONE.sub("", text)
        text = RE_PHONE_IN.sub("", text)
        text = RE_PHONE_GROUP.sub("", text)
        # 兜底版（无闭合）
        text = RE_PHONE_LOOSE.sub("", text)
        text = RE_PHONE_IN_LOOSE.sub("", text)
        text = RE_PHONE_GROUP_LOOSE.sub("", text)
        # 其他
        text = RE_NEW_PLATFORM.sub("", text)
        text = RE_ADD_CONTACT.sub("", text)

        if streaming:
            # 剥掉未闭合的 [[ 开头
            text = re.sub(r"\[\[[^\]]*$", "", text)
            text = re.sub(r"\[\[\s*/\s*PHONE[^\]]*$", "", text)
            text = re.sub(r"\[\[\s*/\s*PHONE[^\]]*\]?$", "", text)
            text = re.sub(r"\[\[\s*/\s*PHONE_IN[^\]]*$", "", text)
            text = re.sub(r"\[\[\s*/\s*PHONE_GROUP[^\]]*$", "", text)
            # 剥掉 AI 编的"—— 📱 N 条新消息 ——"提示行
            text = re.sub(r"——\s*📱\s*\d+\s*条新消息（[^）]*）\s*——", "", text)
        return text

    def _post_process_ai_reply(self, full_text):
        """全文到齐后：解析手机内容、群聊、新平台、加联系人，然后存主对话"""
        # ★ 保存 AI 原始输出到日志文件
        try:
            with open("raw_ai_log.txt", "a", encoding="utf-8") as _log:
                _log.write("\n" + "=" * 70 + "\n")
                _log.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                _log.write(full_text + "\n")
                _log.write("=" * 70 + "\n")
        except Exception:
            pass

        phone_hits = []
        phone_in_hits = []
        group_hits = []

        # 标记已匹配的区间，防止兜底重复
        used_spans = []

        def _overlap(s, e):
            for a, b in used_spans:
                if s < b and e > a:
                    return True
            return False

        def _add_hit(hits, plat, name_or_sender, content, s, e, extra=None):
            content = content.strip()
            if not content:
                return
            if extra is not None:
                hits.append((plat.strip(), name_or_sender.strip(), extra.strip(), content))
            else:
                hits.append((plat.strip(), name_or_sender.strip(), content))
            used_spans.append((s, e))

        # 1. 私聊回复（标准版，有闭合）
        for m in RE_PHONE.finditer(full_text):
            _add_hit(phone_hits, m.group(1), m.group(2), m.group(3),
                     m.start(), m.end())

        # 2. 私聊主动发起（标准版）
        for m in RE_PHONE_IN.finditer(full_text):
            _add_hit(phone_in_hits, m.group(1), m.group(2), m.group(3),
                     m.start(), m.end())

        # 3. 群聊（标准版）
        for m in RE_PHONE_GROUP.finditer(full_text):
            plat = m.group(1); group = m.group(2); sender = m.group(3); content = m.group(4)
            content = content.strip()
            if not content:
                continue
            if not _overlap(m.start(), m.end()):
                group_hits.append((plat.strip(), group.strip(), sender.strip(), content))
                used_spans.append((m.start(), m.end()))

        # 4. 兜底：私聊回复（无闭合）
        for m in RE_PHONE_LOOSE.finditer(full_text):
            if _overlap(m.start(), m.end()):
                continue
            _add_hit(phone_hits, m.group(1), m.group(2), m.group(3),
                     m.start(), m.end())

        # 5. 兜底：私聊主动发起（无闭合）
        for m in RE_PHONE_IN_LOOSE.finditer(full_text):
            if _overlap(m.start(), m.end()):
                continue
            _add_hit(phone_in_hits, m.group(1), m.group(2), m.group(3),
                     m.start(), m.end())

        # 6. 兜底：群聊（无闭合）
        for m in RE_PHONE_GROUP_LOOSE.finditer(full_text):
            if _overlap(m.start(), m.end()):
                continue
            plat = m.group(1); group = m.group(2); sender = m.group(3); content = m.group(4)
            content = content.strip()
            if not content:
                continue
            group_hits.append((plat.strip(), group.strip(), sender.strip(), content))
            used_spans.append((m.start(), m.end()))

        # 写入手机
        for plat_name, contact_name, content in phone_hits:
            self._phone_receive(plat_name, contact_name, content, is_initiative=False)
        for plat_name, contact_name, content in phone_in_hits:
            self._phone_receive(plat_name, contact_name, content, is_initiative=True)
        for plat_name, group_name, sender, content in group_hits:
            self._phone_group_receive(plat_name, group_name, sender, content)

        # 4. 新平台
        for pname in RE_NEW_PLATFORM.findall(full_text):
            self._phone_maybe_new_platform(pname.strip())

        # 5. 加联系人
        for plat_name, cname, npc_id in RE_ADD_CONTACT.findall(full_text):
            self._phone_maybe_add_contact(plat_name.strip(), cname.strip(), npc_id.strip())

        # 6. 主对话显示
        clean = self._strip_phone_for_display(full_text, streaming=False)
        # ★ 剥掉 AI 自己编的 "—— 📱 N 条新消息 ——"（防止假提示）
        clean = re.sub(r"——\s*📱\s*\d+\s*条新消息（[^）]*）\s*——", "", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

        # 生成提示行
        total_msgs = len(phone_hits) + len(phone_in_hits) + len(group_hits)
        if total_msgs > 0:
            plat_set = set()
            for p, _, _ in phone_hits + phone_in_hits:
                plat_set.add(p)
            for p, _, _, _ in group_hits:
                plat_set.add(p)
            plat_str = "、".join(plat_set)
            tip = f"\n\n—— 📱 {total_msgs} 条新消息（{plat_str}） ——"
            clean = clean + tip
            self._phone_last_jump_plat = list(plat_set)[0] if plat_set else None

        if clean:
            self.messages.append({"role": "assistant", "content": clean})
            self.save_chat()
            self.root.after(0, self.render_history)

    def _start_ai_block(self):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "AI：", "ai_name")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _append_ai_chunk(self, piece):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", piece, "body")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _finish_generation(self):
        self.is_generating = False
        self.btn_send.configure(state="normal")
        self._update_action_buttons()
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def append_chat(self, name, text, tag):
        self.chat_display.configure(state="normal")
        tag_name = {"user": "user_name", "ai": "ai_name", "system": "sys_name"}.get(tag, "body")
        self.chat_display.insert("end", f"{name}：", tag_name)
        self.chat_display.insert("end", text + "\n\n", "body")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def render_history(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        # 每次重渲染，重置手机提示标签
        self._phone_tip_count = 0

        for m in self.messages:
            if m["role"] == "user":
                self.chat_display.insert("end", "你：", "user_name")
            else:
                self.chat_display.insert("end", "AI：", "ai_name")

            content = m["content"]
            # 判断是否含"📱 N 条新消息"提示
            tip_match = re.search(r"—— 📱 (\d+) 条新消息（([^）]+)） ——", content)
            if tip_match:
                before = content[:tip_match.start()].rstrip()
                self.chat_display.insert("end", before + "\n\n", "body")

                # 插入可点击的标签
                tip_id = f"phone_tip_{self._phone_tip_count}"
                self._phone_tip_count += 1
                plat_names = tip_match.group(2)
                tip_text = f"📱 {tip_match.group(1)} 条新消息（{plat_names}）  [点此查看]"
                self.chat_display.insert("end", tip_text + "\n\n", (tip_id, "phone_tip"))

                # 绑定点击事件
                self.chat_display.tag_bind(
                    tip_id, "<Button-1>",
                    lambda e, p=plat_names: self._phone_jump_to(p.split("、")[0])
                )
                # 鼠标悬停手型
                self.chat_display.tag_bind(
                    tip_id, "<Enter>",
                    lambda e: self.chat_display.configure(cursor="hand2")
                )
                self.chat_display.tag_bind(
                    tip_id, "<Leave>",
                    lambda e: self.chat_display.configure(cursor="arrow")
                )
            else:
                self.chat_display.insert("end", content + "\n\n", "body")

        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _phone_jump_to(self, plat_name):
        """点击提示标签 → 打开手机并切到指定平台"""
        self.open_phone_window()
        # 等窗口创建好，再切平台
        def switch():
            plats = self.phone.get("platforms", [])
            for i, p in enumerate(plats):
                if p["name"] == plat_name or p.get("id") == plat_name:
                    self._phone_plat_idx = i
                    self._phone_contact_idx = -1
                    self._phone_refresh_all()
                    return
        self.root.after(100, switch)

    # ============================================================
    # 三个删除按钮
    # ============================================================
    def _last_index_of(self, role):
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i]["role"] == role:
                return i
        return -1

    def _update_action_buttons(self):
        busy = self.is_generating
        has_ai   = self._last_index_of("assistant") >= 0
        has_user = self._last_index_of("user") >= 0

        def st(ok):
            return "normal" if (ok and not busy) else "disabled"

        try:
            self.btn_del_user.configure(state=st(has_user))
            self.btn_regen.configure(state=st(has_ai))
            self.btn_del_ai.configure(state=st(has_ai))
        except AttributeError:
            pass

    def delete_my_last(self):
        if self.is_generating:
            return
        idx = self._last_index_of("user")
        if idx < 0:
            messagebox.showinfo("提示", "还没有你说过的话")
            return
        preview = self.messages[idx]["content"][:40]
        if not messagebox.askyesno("确认删除",
            f"将删除你说过的话，以及它之后的所有 AI 回复：\n\n「{preview}…」\n\n确定吗？"):
            return
        removed = len(self.messages) - idx
        del self.messages[idx:]
        self.save_chat()
        self.render_history()
        self._update_action_buttons()
        self.set_status(f"🗑 已删除你的最后一条（连带 {removed-1} 条 AI 回复）")

    def regenerate_last_ai(self):
        if self.is_generating:
            return
        idx = self._last_index_of("assistant")
        if idx < 0:
            messagebox.showinfo("提示", "还没有 AI 回复可重生成")
            return
        has_user_before = any(self.messages[i]["role"] == "user" for i in range(idx))
        if not has_user_before:
            messagebox.showwarning("提示", "缺少上下文，无法重生成")
            return
        del self.messages[idx]
        self.save_chat()
        self.render_history()
        self.is_generating = True
        self.btn_send.configure(state="disabled")
        self._update_action_buttons()
        self.set_status("🔄 重生成中…")
        threading.Thread(target=self._request_stream, daemon=True).start()

    def delete_ai_and_after(self):
        if self.is_generating:
            return
        idx = self._last_index_of("assistant")
        if idx < 0:
            messagebox.showinfo("提示", "还没有 AI 回复可删")
            return
        after_users = [i for i in range(idx+1, len(self.messages)) if self.messages[i]["role"] == "user"]
        preview = self.messages[idx]["content"][:40]
        if after_users:
            msg = f"将删除最后一条 AI 回复，以及它之后你说的 {len(after_users)} 条消息：\n\n「{preview}…」\n\n确定吗？"
        else:
            msg = f"将删除最后一条 AI 回复：\n\n「{preview}…」\n\n确定吗？"
        if not messagebox.askyesno("确认删除", msg):
            return
        del self.messages[idx:]
        self.save_chat()
        self.render_history()
        self._update_action_buttons()
        self.set_status("🗑 已删除")

    # ============================================================
    # 自动摘要
    # ============================================================
    def _maybe_summarize(self):
        if self.summarizing:
            return
        if len(self.messages) < self.summary_trigger:
            return
        if len(self.messages) % self.summary_trigger != 0:
            return
        self.summarizing = True
        self.set_status("📝 后台生成摘要…")
        threading.Thread(target=self._do_summarize, daemon=True).start()

    def _do_summarize(self):
        try:
            key = self.config.get("api_key", "").strip()
            base = self.config.get("base_url", "").strip().rstrip("/")
            model = self.config.get("model", "").strip()
            if not key or not base or not model:
                return
            batch = self.messages[-self.summary_trigger:]
            text_block = "\n".join([
                f"{'你' if m['role']=='user' else 'AI'}：{m['content']}"
                for m in batch
            ])
            old = self.summary_text.strip()
            prompt = (
                "你是剧情档案员。请把下面的新对话压缩成简洁的剧情摘要，"
                "然后与旧摘要合并成一段总摘要。保留关键人物、事件、转折、伏笔，"
                "删掉无关闲聊。300字以内，中文。\n\n"
                f"【旧摘要】\n{old if old else '（无）'}\n\n"
                f"【新对话】\n{text_block}\n\n"
                "只输出合并后的摘要正文，不要任何标题。"
            )
            resp = requests.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.3, "max_tokens": 600},
                timeout=40,
            )
            if resp.status_code == 200:
                try:
                    _data = json.loads(resp.content.decode("utf-8", errors="replace"))
                    s = _data["choices"][0]["message"]["content"].strip()
                except Exception:
                    self.done.emit("近期对话平淡。")
                    return
                if s:
                    self.summary_text = s
                    self.root.after(0, self.save_summary)
                    self.root.after(0, lambda: self.set_status("📝 摘要已更新"))
        except Exception as e:
            self.root.after(0, lambda: self.set_status(f"摘要失败: {e}"))
        finally:
            self.summarizing = False

    # ============================================================
    # 剧情笔记
    # ============================================================
    def open_note_window(self):
        win = tk.Toplevel(self.root)
        win.title("📌 剧情笔记")
        win.geometry("600x600")
        win.transient(self.root)
        tk.Label(win, text="剧情笔记（AI 每次请求都会看到）").pack(anchor="w", padx=8, pady=(8, 2))
        text = tk.Text(win, wrap="word", undo=True)
        text.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        text.insert("1.0", self.memory_note)
        row = tk.Frame(win)
        row.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(row, text="➕ 快速追加", command=lambda: self._quick_append(text)).pack(side="left", padx=2)
        tk.Button(row, text="🗑 清空", command=lambda: text.delete("1.0", "end")).pack(side="left", padx=2)
        tk.Button(row, text="💾 保存", command=lambda: self._save_note(text, win)).pack(side="right", padx=2)
        tk.Button(row, text="取消", command=win.destroy).pack(side="right", padx=2)

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x,0)}+{max(y,0)}")

    def _quick_append(self, text_widget):
        entry = simpledialog.askstring("追加笔记", "写点什么（自动加时间戳）：",
                                       parent=text_widget.winfo_toplevel())
        if not entry or not entry.strip():
            return
        stamp = datetime.datetime.now().strftime("[%m-%d %H:%M]")
        cur = text_widget.get("1.0", "end").rstrip()
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", (cur + "\n" + f"{stamp} {entry.strip()}") if cur else f"{stamp} {entry.strip()}")
        text_widget.see("end")

    def _save_note(self, text_widget, win):
        self.memory_note = text_widget.get("1.0", "end").strip()
        self.save_memory()
        self.set_status(f"📌 笔记已保存（{len(self.memory_note)} 字）")
        win.destroy()

    def clear_chat(self):
        if not messagebox.askyesno("确认",
            "确定清空对话吗？\n\n会清空：聊天区 + chat_history.json\n保留：笔记 + 摘要 + 世界 + 状态 + 手机"):
            return
        self.messages.clear()
        self.save_chat()
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self._update_action_buttons()
        self.set_status("已清空")

    def export_chat(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本", "*.txt"), ("Markdown", "*.md"), ("全部", "*.*")],
            initialfile="chat_log.txt",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 角色设定\n" + self.system_prompt + "\n\n")
            if self.global_extra_prompt:
                f.write("# 全局附加提示词\n" + self.global_extra_prompt + "\n\n")
            if self.summary_text:
                f.write("# 自动摘要\n" + self.summary_text + "\n\n")
            if self.memory_note:
                f.write("# 剧情笔记\n" + self.memory_note + "\n\n")
            f.write("# 对话记录\n")
            for m in self.messages:
                who = "你" if m["role"] == "user" else "AI"
                f.write(f"\n{who}：{m['content']}\n")
            # 手机记录
            f.write("\n\n# 手机记录\n")
            for p in self.phone.get("platforms", []):
                f.write(f"\n## {p['icon']} {p['name']}\n")
                for c in p.get("contacts", []):
                    f.write(f"\n### 与 {c['name']}\n")
                    for m in c.get("messages", []):
                        who = "你" if m.get("from") == "me" else c["name"]
                        f.write(f"{who}：{m.get('text','')}\n")
        self.set_status(f"已导出：{os.path.basename(path)}")

    def set_status(self, text):
        self.status_label.configure(text=text)

    # ============================================================
    # 📱 手机系统
    # ============================================================
    def open_phone_window(self):
        if self._phone_win and self._phone_win.winfo_exists():
            self._phone_win.lift()
            self._phone_refresh_all()
            return

        win = tk.Toplevel(self.root)
        self._phone_win = win
        win.title("📱 手机")
        win.geometry("880x600")
        win.transient(self.root)

        top = tk.Frame(win)
        top.pack(fill="x", padx=6, pady=(6, 2))
        self.plat_tabs_frame = tk.Frame(top)
        self.plat_tabs_frame.pack(side="left", fill="x", expand=True)
        tk.Button(top, text="➕ 平台", command=self._phone_add_platform).pack(side="right", padx=2)
        tk.Button(top, text="✏️", width=3, command=self._phone_edit_platform).pack(side="right", padx=1)
        tk.Button(top, text="🗑", width=3, command=self._phone_del_platform).pack(side="right", padx=1)

        body = tk.Frame(win)
        body.pack(fill="both", expand=True, padx=6, pady=6)

        left = tk.Frame(body, width=220)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        # ===== 联系人区 =====
        tk.Label(left, text="📇 联系人").pack(anchor="w")
        self.contact_listbox = tk.Listbox(left, exportselection=False, height=8)
        self.contact_listbox.pack(fill="x", pady=(2, 4))
        self.contact_listbox.bind("<<ListboxSelect>>", lambda e: self._phone_on_contact_select())

        cbtn = tk.Frame(left)
        cbtn.pack(fill="x")
        tk.Button(cbtn, text="➕ 加人", command=self._phone_add_contact).pack(side="left", padx=1)
        tk.Button(cbtn, text="✏️", width=3, command=self._phone_edit_contact).pack(side="left", padx=1)
        tk.Button(cbtn, text="🗑", width=3, command=self._phone_del_contact).pack(side="left", padx=1)

        cbtn2 = tk.Frame(left)
        cbtn2.pack(fill="x", pady=(2, 0))
        tk.Button(cbtn2, text="📎 复制到其他平台",
                  command=self._phone_copy_contact).pack(fill="x", padx=1)

        # ===== 群聊区 =====
        tk.Label(left, text="👥 群聊").pack(anchor="w", pady=(8, 0))
        self.group_listbox = tk.Listbox(left, exportselection=False, height=8)
        self.group_listbox.pack(fill="x", pady=(2, 4))
        self.group_listbox.bind("<<ListboxSelect>>", lambda e: self._phone_on_group_select())

        gbtn = tk.Frame(left)
        gbtn.pack(fill="x")
        tk.Button(gbtn, text="➕ 建群", command=self._phone_add_group).pack(side="left", padx=1)
        tk.Button(gbtn, text="👥", width=3,
                  command=self._phone_manage_members).pack(side="left", padx=1)
        tk.Button(gbtn, text="🗑", width=3,
                  command=self._phone_del_group).pack(side="left", padx=1)

        right = tk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.phone_chat_label = tk.Label(right, text="（未选择联系人）", anchor="w")
        self.phone_chat_label.pack(fill="x")
        self.phone_chat_display = tk.Text(right, wrap="word", state="disabled",
                                          padx=8, pady=6, height=20)
        self.phone_chat_display.pack(fill="both", expand=True, pady=(2, 4))
        self.phone_chat_display.tag_configure("name",
            font=(self.font_family, max(8, self.font_size - 2), "bold"))
        self.phone_chat_display.tag_configure("body",
            font=(self.font_family, self.font_size))

        input_row = tk.Frame(right)
        input_row.pack(fill="x")

        # 📎 按钮（在左侧）
        tk.Button(input_row, text="📎\n发图", command=self._phone_send_image, width=6
                  ).pack(side="left", fill="y", padx=(0, 4))

        self.phone_input = tk.Text(input_row, height=3, wrap="word")
        self.phone_input.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.phone_input.bind("<Control-Return>", lambda e: (self._phone_send(), "break"))
        tk.Button(input_row, text="发送\n(Ctrl+Enter)", command=self._phone_send, width=12
                  ).pack(side="right", fill="y")

        self._phone_refresh_all()

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x,0)}+{max(y,0)}")

    # --------- 刷新 ---------
    def _phone_refresh_all(self):
        if not self._phone_win or not self._phone_win.winfo_exists():
            return
        self._phone_refresh_tabs()
        self._phone_refresh_contacts()
        self._phone_refresh_chat()

    def _phone_refresh_tabs(self):
        for w in self.plat_tabs_frame.winfo_children():
            w.destroy()
        plats = self.phone.get("platforms", [])
        if not plats:
            tk.Label(self.plat_tabs_frame, text="（没有平台，点右边 ➕ 新建）").pack(side="left")
            return
        for i, p in enumerate(plats):
            is_cur = (i == self._phone_plat_idx)
            text = f"{p.get('icon','💬')} {p['name']}"
            b = tk.Button(self.plat_tabs_frame, text=text,
                          command=lambda idx=i: self._phone_switch_platform(idx))
            b.pack(side="left", padx=2)
            if is_cur:
                b.configure(relief="sunken")

    def _phone_switch_platform(self, idx):
        plats = self.phone.get("platforms", [])
        if idx < 0 or idx >= len(plats):
            return
        self._phone_plat_idx = idx
        self._phone_contact_idx = -1
        self._phone_group_idx = -1
        self._phone_refresh_all()

    def _phone_cur_platform(self):
        plats = self.phone.get("platforms", [])
        if not plats:
            return None
        if self._phone_plat_idx >= len(plats):
            self._phone_plat_idx = 0
        return plats[self._phone_plat_idx]

    def _phone_cur_contact(self):
        p = self._phone_cur_platform()
        if not p:
            return None
        contacts = p.get("contacts", [])
        if self._phone_contact_idx < 0 or self._phone_contact_idx >= len(contacts):
            return None
        return contacts[self._phone_contact_idx]

    def _phone_refresh_contacts(self):
        # 联系人
        self.contact_listbox.delete(0, "end")
        p = self._phone_cur_platform()
        if not p:
            return
        for c in p.get("contacts", []):
            note = c.get("note", "")
            text = f"{c['name']}" + (f"  ({note})" if note else "")
            self.contact_listbox.insert("end", text)
        if 0 <= self._phone_contact_idx < self.contact_listbox.size():
            self.contact_listbox.selection_set(self._phone_contact_idx)

        # 群聊
        # 群聊
        self.group_listbox.delete(0, "end")
        for g in p.get("groups", []):
            n = len(g.get("member_ids", []))
            if n > 0:
                text = f"{g.get('icon','👥')} {g['name']}  ({n}人)"
            else:
                text = f"{g.get('icon','👥')} {g['name']}"
            self.group_listbox.insert("end", text)
        if 0 <= self._phone_group_idx < self.group_listbox.size():
            self.group_listbox.selection_set(self._phone_group_idx)

    def _phone_refresh_chat(self):
        self.phone_chat_display.configure(state="normal")
        self.phone_chat_display.delete("1.0", "end")
        p = self._phone_cur_platform()
        if not p:
            self.phone_chat_label.configure(text="（没有平台）")
            self.phone_chat_display.configure(state="disabled")
            return

        # 判断是群还是单人
        g = self._phone_cur_group()
        c = self._phone_cur_contact()

        if g:
            # 群聊模式
            self.phone_chat_label.configure(
                text=f"[{p['name']}] 群「{g['name']}」（{len(g.get('member_ids',[]))}人）"
            )
            for m in g.get("messages", []):
                if m.get("from") == "me":
                    who = "你"
                else:
                    who = m.get("sender_name") or m.get("from") or "?"
                self.phone_chat_display.insert("end", f"{who}\n", "name")
                if m.get("type") == "image":
                    self.phone_chat_display.insert("end", "🖼 [图片] ", "name")
                self.phone_chat_display.insert("end", m.get("text", "") + "\n\n", "body")
        elif c:
            # 私聊模式
            self.phone_chat_label.configure(text=f"[{p['name']}] 与 {c['name']} 的对话")
            for m in c.get("messages", []):
                who = "你" if m.get("from") == "me" else c["name"]
                self.phone_chat_display.insert("end", f"{who}\n", "name")
                if m.get("type") == "image":
                    self.phone_chat_display.insert("end", "🖼 [图片] ", "name")
                self.phone_chat_display.insert("end", m.get("text", "") + "\n\n", "body")
        else:
            self.phone_chat_label.configure(text=f"[{p['name']}] （未选择联系人或群）")

        self.phone_chat_display.configure(state="disabled")
        self.phone_chat_display.see("end")

    def _phone_on_contact_select(self):
        sel = self.contact_listbox.curselection()
        if not sel:
            return
        self._phone_contact_idx = sel[0]
        self._phone_group_idx = -1                    # ★ 清除群选中
        self.group_listbox.selection_clear(0, "end")  # ★ 清除群列表框选中
        self._phone_refresh_chat()

    # ============================================================
    # 群聊相关
    # ============================================================
    def _phone_cur_group(self):
        p = self._phone_cur_platform()
        if not p:
            return None
        groups = p.get("groups", [])
        if self._phone_group_idx < 0 or self._phone_group_idx >= len(groups):
            return None
        return groups[self._phone_group_idx]

    def _phone_on_group_select(self):
        sel = self.group_listbox.curselection()
        if not sel:
            return
        self._phone_group_idx = sel[0]
        self._phone_contact_idx = -1
        self.contact_listbox.selection_clear(0, "end")
        self._phone_refresh_chat()

    def _phone_add_group(self):
        p = self._phone_cur_platform()
        if not p:
            messagebox.showinfo("提示", "先选一个平台", parent=self._phone_win)
            return
        if not p.get("contacts"):
            messagebox.showinfo("提示", "此平台还没有联系人，先加人", parent=self._phone_win)
            return

        name = simpledialog.askstring("新建群聊", "群名称：", parent=self._phone_win)
        if not name or not name.strip():
            return
        name = name.strip()
        if any(g["name"] == name for g in p.get("groups", [])):
            messagebox.showinfo("提示", f"「{name}」群已存在", parent=self._phone_win)
            return

        # 选成员
        member_ids = self._phone_pick_members(p, title=f"选择群成员（{name}）")
        if not member_ids:
            messagebox.showinfo("提示", "至少要选一个成员", parent=self._phone_win)
            return

        group = {
            "id": "grp_" + str(abs(hash(name + p["name"])) % 10**8),
            "name": name,
            "icon": "👥",
            "member_ids": member_ids,
            "messages": []
        }
        p.setdefault("groups", []).append(group)
        self.save_phone()
        self._phone_group_idx = len(p["groups"]) - 1
        self._phone_contact_idx = -1
        self._phone_refresh_all()

    def _phone_pick_members(self, platform, title="选择成员"):
        """弹窗多选成员，返回 member_ids 列表（或 None）"""
        contacts = platform.get("contacts", [])
        if not contacts:
            return None

        dlg = tk.Toplevel(self._phone_win)
        dlg.title(title)
        dlg.geometry("380x480")
        dlg.transient(self._phone_win)
        dlg.grab_set()

        tk.Label(dlg, text="勾选要加入的成员：").pack(anchor="w", padx=10, pady=(10, 4))

        lb = tk.Listbox(dlg, selectmode=tk.MULTIPLE, exportselection=False)
        lb.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        for c in contacts:
            note = c.get("note", "")
            text = f"{c['name']}" + (f"  ({note})" if note else "")
            lb.insert("end", text)

        result = {"ids": None}

        def ok():
            sel = lb.curselection()
            ids = []
            for i in sel:
                ids.append(contacts[i]["id"])
            result["ids"] = ids
            dlg.destroy()

        bf = tk.Frame(dlg)
        bf.pack(fill="x", padx=10, pady=8)
        tk.Button(bf, text="确定", command=ok, width=10).pack(side="right", padx=4)
        tk.Button(bf, text="取消", command=dlg.destroy, width=10).pack(side="right", padx=4)

        dlg.update_idletasks()
        x = self._phone_win.winfo_x() + (self._phone_win.winfo_width() - dlg.winfo_width()) // 2
        y = self._phone_win.winfo_y() + (self._phone_win.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
        dlg.wait_window()
        return result["ids"]

    def _phone_manage_members(self):
        """管理选中群的成员：加人 / 踢人"""
        p = self._phone_cur_platform()
        g = self._phone_cur_group()
        if not p or not g:
            messagebox.showinfo("提示", "先选一个群", parent=self._phone_win)
            return

        dlg = tk.Toplevel(self._phone_win)
        dlg.title(f"管理群成员 - {g['name']}")
        dlg.geometry("420x500")
        dlg.transient(self._phone_win)
        dlg.grab_set()

        tk.Label(dlg, text=f"群「{g['name']}」的成员（勾选表示在群里）：",
                 font=("", 11)).pack(anchor="w", padx=10, pady=(10, 4))

        # 所有联系人 + 勾选状态
        all_contacts = p.get("contacts", [])
        member_set = set(g.get("member_ids", []))

        lb = tk.Listbox(dlg, selectmode=tk.MULTIPLE, exportselection=False)
        lb.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        for i, c in enumerate(all_contacts):
            mark = "✔ " if c["id"] in member_set else "  "
            lb.insert("end", f"{mark}{c['name']}")
            if c["id"] in member_set:
                lb.selection_set(i)

        def apply():
            sel = set(lb.curselection())
            new_ids = [all_contacts[i]["id"] for i in sel]
            if not new_ids:
                messagebox.showinfo("提示", "群里至少要留一个人", parent=dlg)
                return
            g["member_ids"] = new_ids
            self.save_phone()
            self._phone_refresh_all()
            dlg.destroy()

        bf = tk.Frame(dlg)
        bf.pack(fill="x", padx=10, pady=8)
        tk.Button(bf, text="💾 保存", command=apply, width=10).pack(side="right", padx=4)
        tk.Button(bf, text="取消", command=dlg.destroy, width=10).pack(side="right", padx=4)

        dlg.update_idletasks()
        x = self._phone_win.winfo_x() + (self._phone_win.winfo_width() - dlg.winfo_width()) // 2
        y = self._phone_win.winfo_y() + (self._phone_win.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{max(x,0)}+{max(y,0)}")

    def _phone_del_group(self):
        p = self._phone_cur_platform()
        g = self._phone_cur_group()
        if not p or not g:
            return
        if not messagebox.askyesno("确认", f"删除群「{g['name']}」？",
                                   parent=self._phone_win):
            return
        p["groups"] = [x for x in p["groups"] if x is not g]
        self.save_phone()
        self._phone_group_idx = -1
        self._phone_refresh_all()

    def _phone_send_group(self, text):
        """在群里发消息（第一批只记录，第二批接 AI）"""
        p = self._phone_cur_platform()
        g = self._phone_cur_group()
        if not p or not g:
            return
        if self.is_generating:
            messagebox.showinfo("提示", "AI 正在生成中，稍等", parent=self._phone_win)
            return

        now = self.state.get("current_time", "")
        g.setdefault("messages", []).append({
            "from": "me", "text": text, "time": now
        })
        self.save_phone()
        self._phone_refresh_chat()
        # 第二批接 AI
        self.set_status(f"📱 [{p['name']}·{g['name']}] 已发送（第二批会接 AI 回复）")

    # --------- emoji 面板 ---------
    def _phone_pick_emoji(self, parent, default="💬"):
        dlg = tk.Toplevel(parent)
        dlg.title("选择 Emoji")
        dlg.geometry("460x360")
        dlg.transient(parent)
        dlg.grab_set()

        groups = {
            "通讯": ["💬", "📱", "📞", "✉️", "📧", "📨", "📩", "☎️", "📟", "📠", "🗨️", "💭"],
            "社交": ["👥", "👤", "💑", "💏", "🤝", "🎉", "💃", "🕺", "🎵", "📷", "🎬", "🎤"],
            "其他": ["❤️", "🔥", "⭐", "🌈", "✨", "🌸", "🍃", "☀️", "🌙", "⚡", "💎", "🎁"],
        }

        state = {"val": default}
        top = tk.Frame(dlg)
        top.pack(fill="x", padx=8, pady=6)
        tk.Label(top, text="当前：").pack(side="left")
        preview = tk.Label(top, text=default, font=("", 24))
        preview.pack(side="left", padx=8)
        entry_var = tk.StringVar(value=default)
        tk.Entry(top, textvariable=entry_var, width=6, font=("", 16)).pack(side="left")
        def upd(*a):
            preview.configure(text=entry_var.get() or " ")
        entry_var.trace_add("write", upd)

        tab = ttk.Notebook(dlg)
        tab.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        for gname, items in groups.items():
            f = tk.Frame(tab)
            tab.add(f, text=f" {gname} ")
            grid = tk.Frame(f)
            grid.pack(fill="both", expand=True, padx=4, pady=4)
            r, c = 0, 0
            for em in items:
                b = tk.Button(grid, text=em, font=("", 18), width=2,
                              command=lambda e=em: (entry_var.set(e), upd()))
                b.grid(row=r, column=c, padx=2, pady=2)
                c += 1
                if c >= 8:
                    c = 0
                    r += 1

        bf = tk.Frame(dlg)
        bf.pack(fill="x", padx=8, pady=(0, 8))
        def ok():
            state["val"] = entry_var.get().strip() or default
            dlg.destroy()
        def cancel():
            state["val"] = None
            dlg.destroy()
        tk.Button(bf, text="确定", command=ok, width=10).pack(side="right", padx=4)
        tk.Button(bf, text="取消", command=cancel, width=10).pack(side="right", padx=4)

        dlg.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dlg.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
        dlg.wait_window()
        return state["val"]

    # --------- 平台增删改 ---------
    def _phone_add_platform(self):
        win = self._phone_win
        name = simpledialog.askstring("新增平台", "平台名（比如：墨渊、QQ）：", parent=win)
        if not name or not name.strip():
            return
        name = name.strip()
        for p in self.phone.get("platforms", []):
            if p["name"] == name:
                messagebox.showinfo("提示", f"平台「{name}」已存在", parent=win)
                return
        icon = self._phone_pick_emoji(win, default="💬") or "💬"
        kw = simpledialog.askstring("关键词",
            "用于识别此平台的关键词，逗号分隔（可留空）：",
            initialvalue=name, parent=win) or ""
        keywords = [k.strip() for k in kw.split(",") if k.strip()]
        new_plat = {
            "id": name, "name": name, "icon": icon,
            "color": "#5b8def", "keywords": keywords, "contacts": []
        }
        self.phone.setdefault("platforms", []).append(new_plat)
        self.save_phone()
        self._phone_plat_idx = len(self.phone["platforms"]) - 1
        self._phone_contact_idx = -1
        self._phone_refresh_all()

    def _phone_edit_platform(self):
        p = self._phone_cur_platform()
        if not p:
            return
        win = self._phone_win
        new_name = simpledialog.askstring("改平台名", "新名称：", initialvalue=p["name"], parent=win)
        if new_name is None:
            return
        new_name = new_name.strip()
        if not new_name:
            return
        if new_name != p["name"]:
            for q in self.phone.get("platforms", []):
                if q is p:
                    continue
                if q["name"] == new_name:
                    messagebox.showwarning("提示", f"已有平台叫「{new_name}」", parent=win)
                    return
            p["name"] = new_name
            p["id"] = new_name
        new_icon = self._phone_pick_emoji(win, default=p.get("icon", "💬"))
        if new_icon:
            p["icon"] = new_icon
        kw = simpledialog.askstring("改关键词", "关键词，逗号分隔：",
                                    initialvalue=",".join(p.get("keywords", [])), parent=win)
        if kw is not None:
            p["keywords"] = [k.strip() for k in kw.split(",") if k.strip()]
        self.save_phone()
        self._phone_refresh_all()

    def _phone_del_platform(self):
        p = self._phone_cur_platform()
        if not p:
            return
        if len(self.phone.get("platforms", [])) <= 1:
            messagebox.showinfo("提示", "至少保留一个平台", parent=self._phone_win)
            return
        if not messagebox.askyesno("确认",
            f"删除平台「{p['name']}」？\n\n它的 {len(p.get('contacts',[]))} 个联系人也会一起删。",
            parent=self._phone_win):
            return
        self.phone["platforms"] = [x for x in self.phone["platforms"] if x is not p]
        self.save_phone()
        self._phone_plat_idx = 0
        self._phone_contact_idx = -1
        self._phone_refresh_all()

    # --------- 联系人增删改 ---------
    def _phone_add_contact(self):
        p = self._phone_cur_platform()
        if not p:
            messagebox.showinfo("提示", "先选一个平台", parent=self._phone_win)
            return
        win = self._phone_win
        name = simpledialog.askstring("新增联系人", "对方名字：", parent=win)
        if not name or not name.strip():
            return
        name = name.strip()
        if any(c["name"] == name for c in p.get("contacts", [])):
            messagebox.showinfo("提示", f"「{name}」已在此平台", parent=win)
            return
        note = simpledialog.askstring("备注（可留空）", "备注：", parent=win) or ""
        npc_id = simpledialog.askstring(
            "关联NPC id（可留空）",
            "若这个联系人对应游戏里的某个角色，填它的 id；不填则视为纯联系人。",
            parent=win) or ""
        contact = {
            "id": "cnt_" + str(abs(hash(name + p["name"])) % 10**8),
            "name": name, "npc_id": npc_id.strip(), "note": note.strip(),
            "messages": []
        }
        p.setdefault("contacts", []).append(contact)
        self.save_phone()
        self._phone_contact_idx = len(p["contacts"]) - 1
        self._phone_refresh_all()

    def _phone_edit_contact(self):
        c = self._phone_cur_contact()
        if not c:
            return
        win = self._phone_win
        new_name = simpledialog.askstring("改名字", "新名字：", initialvalue=c["name"], parent=win)
        if new_name is not None and new_name.strip():
            c["name"] = new_name.strip()
        new_note = simpledialog.askstring("改备注", "备注：", initialvalue=c.get("note", ""), parent=win)
        if new_note is not None:
            c["note"] = new_note.strip()
        new_npc = simpledialog.askstring("关联NPC id", "NPC id（可留空）：",
                                         initialvalue=c.get("npc_id", ""), parent=win)
        if new_npc is not None:
            c["npc_id"] = new_npc.strip()
        self.save_phone()
        self._phone_refresh_all()

    def _phone_del_contact(self):
        p = self._phone_cur_platform()
        c = self._phone_cur_contact()
        if not p or not c:
            return
        if not messagebox.askyesno("确认", f"删除联系人「{c['name']}」？",
                                   parent=self._phone_win):
            return
        p["contacts"] = [x for x in p["contacts"] if x is not c]
        self.save_phone()
        self._phone_contact_idx = -1
        self._phone_refresh_all()

    def _phone_copy_contact(self):
        """把当前联系人复制到另一个平台"""
        src_p = self._phone_cur_platform()
        src_c = self._phone_cur_contact()
        if not src_p or not src_c:
            messagebox.showinfo("提示", "先选一个联系人", parent=self._phone_win)
            return

        # 列出其他平台
        others = [p for p in self.phone.get("platforms", []) if p is not src_p]
        if not others:
            # 只有当前一个平台 → 让你现场建一个新的
            if not messagebox.askyesno(
                "没有其他平台",
                f"当前只有「{src_p['name']}」一个平台。\n\n要新建一个平台再把「{src_c['name']}」加进去吗？",
                parent=self._phone_win):
                return
            self._phone_add_platform()
            others = [p for p in self.phone.get("platforms", []) if p is not src_p]
            if not others:
                return

        # 弹窗选目标平台
        dlg = tk.Toplevel(self._phone_win)
        dlg.title("复制到其他平台")
        dlg.geometry("340x360")
        dlg.transient(self._phone_win)
        dlg.grab_set()

        tk.Label(dlg, text=f"把「{src_c['name']}」加到哪个平台？",
                 font=("", 11)).pack(anchor="w", padx=10, pady=(10, 4))

        lb = tk.Listbox(dlg, height=8)
        lb.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        for p in others:
            lb.insert("end", f"{p.get('icon','💬')} {p['name']}")

        # 新名字（默认跟原名一样）
        tk.Label(dlg, text="在新平台里的名字（可改）：").pack(anchor="w", padx=10)
        name_var = tk.StringVar(value=src_c["name"])
        tk.Entry(dlg, textvariable=name_var, width=30).pack(fill="x", padx=10, pady=(0, 6))

        # 是否复制历史记录
        copy_hist = tk.BooleanVar(value=False)
        tk.Checkbutton(dlg, text="同时复制聊天记录", variable=copy_hist).pack(anchor="w", padx=10)

        result = {"plat": None}

        def ok():
            sel = lb.curselection()
            if not sel:
                messagebox.showinfo("提示", "请选择一个平台", parent=dlg)
                return
            result["plat"] = others[sel[0]]
            dlg.destroy()

        bf = tk.Frame(dlg)
        bf.pack(fill="x", padx=10, pady=8)
        tk.Button(bf, text="确定", command=ok, width=10).pack(side="right", padx=4)
        tk.Button(bf, text="取消", command=dlg.destroy, width=10).pack(side="right", padx=4)

        dlg.update_idletasks()
        x = self._phone_win.winfo_x() + (self._phone_win.winfo_width() - dlg.winfo_width()) // 2
        y = self._phone_win.winfo_y() + (self._phone_win.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
        dlg.wait_window()

        target_p = result["plat"]
        if not target_p:
            return

        new_name = name_var.get().strip() or src_c["name"]

        # 目标平台里已经有同名？
        existing = self._phone_find_contact(target_p, new_name)
        if existing:
            if not messagebox.askyesno(
                "已存在",
                f"「{target_p['name']}」里已经有「{new_name}」了。\n\n要用当前信息覆盖吗？",
                parent=self._phone_win):
                return
            # 覆盖
            existing["npc_id"] = src_c.get("npc_id", "")
            if src_c.get("note"):
                existing["note"] = src_c["note"]
            if copy_hist.get():
                existing["messages"] = list(src_c.get("messages", []))
            self.save_phone()
            self.set_status(f"📎 已更新「{target_p['name']}」里的「{new_name}」")
        else:
            # 新建
            new_c = {
                "id": "cnt_" + str(abs(hash(new_name + target_p["name"])) % 10**8),
                "name": new_name,
                "npc_id": src_c.get("npc_id", ""),
                "note": src_c.get("note", ""),
                "messages": list(src_c.get("messages", [])) if copy_hist.get() else []
            }
            target_p.setdefault("contacts", []).append(new_c)
            self.save_phone()
            self.set_status(f"📎 已把「{new_name}」加入「{target_p['name']}」")

        # 切到目标平台
        for i, p in enumerate(self.phone.get("platforms", [])):
            if p is target_p:
                self._phone_plat_idx = i
                break
        # 选中刚加/更新的联系人
        target_contacts = target_p.get("contacts", [])
        for i, c in enumerate(target_contacts):
            if c["name"] == new_name:
                self._phone_contact_idx = i
                break

        self._phone_refresh_all()

    # --------- 联系人查找/创建（供 AI 回流用） ---------
    def _phone_find_platform(self, plat_name):
        for p in self.phone.get("platforms", []):
            if p["name"] == plat_name or p.get("id") == plat_name:
                return p
        return None

    def _phone_find_contact(self, plat, contact_name):
        """精确匹配优先；失败则做模糊匹配（忽略标点、空格，允许前缀匹配）"""
        if not contact_name:
            return None
        contacts = plat.get("contacts", [])
        # 1. 精确
        for c in contacts:
            if c["name"] == contact_name:
                return c
        # 2. 去掉常见分隔符后精确比
        def norm(s):
            return s.replace("·", "").replace("・", "").replace(" ", "").replace(".", "").replace("_", "")
        target = norm(contact_name)
        for c in contacts:
            if norm(c["name"]) == target:
                return c
        # 3. 前缀匹配：AI 写的名字是已有联系人的前缀，或反之
        #    比如 AI 写"阿凯"，已有"阿凯·同城" → 命中
        #    或 AI 写"阿凯·同城"，已有"阿凯" → 命中
        for c in contacts:
            n = norm(c["name"])
            if n.startswith(target) or target.startswith(n):
                # 至少要求 2 个字，避免 "阿" 命中所有带"阿"的名字
                if len(target) >= 2 and len(n) >= 2:
                    return c
        return None

    def _phone_create_platform(self, name, icon="💬"):
        p = {
            "id": name, "name": name, "icon": icon,
            "color": "#5b8def", "keywords": [name], "contacts": []
        }
        self.phone.setdefault("platforms", []).append(p)
        self.save_phone()
        return p

    def _phone_create_contact(self, plat, name, npc_id=""):
        c = {
            "id": "cnt_" + str(abs(hash(name + plat["name"])) % 10**8),
            "name": name, "npc_id": npc_id, "note": "",
            "messages": []
        }
        plat.setdefault("contacts", []).append(c)
        self.save_phone()
        return c

    # --------- 发送 / 接收 ---------
    def _phone_send(self):
        p = self._phone_cur_platform()
        if not p:
            messagebox.showinfo("提示", "先选一个平台", parent=self._phone_win)
            return
        if self.is_generating:
            messagebox.showinfo("提示", "AI 正在生成中，稍等", parent=self._phone_win)
            return

        text = self.phone_input.get("1.0", "end").strip()
        if not text:
            return

        key = self.config.get("api_key", "").strip()
        base = self.config.get("base_url", "").strip()
        model = self.config.get("model", "").strip()
        if not key or not base or not model:
            messagebox.showwarning("提示", "请先在『设置』里填写 API Key", parent=self._phone_win)
            return

        g = self._phone_cur_group()
        c = self._phone_cur_contact()

        if g:
            # 群聊
            self.phone_input.delete("1.0", "end")
            now = self.state.get("current_time", "")
            g.setdefault("messages", []).append({
                "from": "me", "text": text, "time": now
            })
            self.save_phone()
            self._phone_refresh_chat()

            main_text = f"[手机·{p['name']}·群「{g['name']}」] {text}"
            self.messages.append({"role": "user", "content": main_text})
            self.append_chat("你", main_text, "user")
            self.save_chat()

            self.is_generating = True
            self.btn_send.configure(state="disabled")
            self._update_action_buttons()
            self.set_status(f"📱 群「{g['name']}」发送中…")
            threading.Thread(target=self._request_stream, daemon=True).start()
        elif c:
            # 私聊
            self.phone_input.delete("1.0", "end")
            now = self.state.get("current_time", "")
            c.setdefault("messages", []).append({
                "from": "me", "text": text, "time": now
            })
            self.save_phone()
            self._phone_refresh_chat()

            prefix = f"[手机·{p['name']}→{c['name']}] "
            main_text = prefix + text
            self.messages.append({"role": "user", "content": main_text})
            self.append_chat("你", main_text, "user")
            self.save_chat()

            self.is_generating = True
            self.btn_send.configure(state="disabled")
            self._update_action_buttons()
            self.set_status("📱 手机消息发送中…")
            threading.Thread(target=self._request_stream, daemon=True).start()
        else:
            messagebox.showinfo("提示", "先选一个联系人或群", parent=self._phone_win)


    def _phone_send_image(self):
        """发送图片（描述式）：弹窗输入描述 + 可选上传本地图片"""
        p = self._phone_cur_platform()
        if not p:
            messagebox.showinfo("提示", "先选一个平台", parent=self._phone_win)
            return
        if self.is_generating:
            messagebox.showinfo("提示", "AI 正在生成中，稍等", parent=self._phone_win)
            return

        g = self._phone_cur_group()
        c = self._phone_cur_contact()
        if not g and not c:
            messagebox.showinfo("提示", "先选一个联系人或群", parent=self._phone_win)
            return

        target = f"群「{g['name']}」" if g else c["name"]

        # 弹窗
        dlg = tk.Toplevel(self._phone_win)
        dlg.title(f"发送图片给 {target}")
        dlg.geometry("480x380")
        dlg.transient(self._phone_win)
        dlg.grab_set()

        tk.Label(dlg, text=f"目标：{target}", font=("", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

        # 图片预览区
        preview_frame = tk.Frame(dlg, height=140)
        preview_frame.pack(fill="x", padx=10, pady=(0, 6))
        preview_frame.pack_propagate(False)
        preview_label = tk.Label(preview_frame, text="（可选：选择一张本地图片作预览）",
                                 bg="#333", fg="#aaa")
        preview_label.pack(fill="both", expand=True)

        img_path_var = tk.StringVar(value="")

        def choose_image():
            path = filedialog.askopenfilename(
                title="选择图片",
                filetypes=[("图片", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("全部", "*.*")],
                parent=dlg
            )
            if not path:
                return
            try:
                from PIL import Image, ImageTk
                img = Image.open(path)
                img.thumbnail((300, 130))
                tkimg = ImageTk.PhotoImage(img)
                preview_label.configure(image=tkimg, text="")
                preview_label.image = tkimg
                img_path_var.set(path)
            except ImportError:
                # 没装 Pillow，只存路径不预览
                preview_label.configure(text=f"已选择：{os.path.basename(path)}\n（未安装 Pillow，无预览）")
                img_path_var.set(path)
            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片：{e}", parent=dlg)

        tk.Button(dlg, text="🖼 选择本地图片", command=choose_image).pack(anchor="w", padx=10, pady=(0, 4))

        tk.Label(dlg, text="图片描述（必填，AI 只看到这段文字）：").pack(anchor="w", padx=10)
        desc_text = tk.Text(dlg, height=5, wrap="word")
        desc_text.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        desc_text.focus_set()

        result = {"ok": False, "desc": "", "img_path": ""}

        def send():
            desc = desc_text.get("1.0", "end").strip()
            if not desc:
                messagebox.showwarning("提示", "请填写图片描述", parent=dlg)
                return
            result["ok"] = True
            result["desc"] = desc
            result["img_path"] = img_path_var.get().strip()
            dlg.destroy()

        bf = tk.Frame(dlg)
        bf.pack(fill="x", padx=10, pady=8)
        tk.Button(bf, text="📤 发送", command=send, width=10).pack(side="right", padx=4)
        tk.Button(bf, text="取消", command=dlg.destroy, width=10).pack(side="right", padx=4)

        dlg.update_idletasks()
        x = self._phone_win.winfo_x() + (self._phone_win.winfo_width() - dlg.winfo_width()) // 2
        y = self._phone_win.winfo_y() + (self._phone_win.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
        dlg.wait_window()

        if not result["ok"]:
            return

        desc = result["desc"]
        img_path = result["img_path"]

        # 存图片到 data/images/
        saved_path = ""
        if img_path and os.path.exists(img_path):
            try:
                img_dir = os.path.join("data", "images")
                os.makedirs(img_dir, exist_ok=True)
                ext = os.path.splitext(img_path)[1] or ".png"
                import uuid as _uuid
                fname = str(_uuid.uuid4())[:8] + ext
                saved_path = os.path.join(img_dir, fname)
                import shutil
                shutil.copy2(img_path, saved_path)
            except Exception:
                saved_path = ""

        now = self.state.get("current_time", "")
        msg = {
            "from": "me",
            "type": "image",
            "text": desc,
            "image_path": saved_path,
            "time": now
        }

        # 写入手机记录
        if g:
            g.setdefault("messages", []).append(msg)
            self.save_phone()
            self._phone_refresh_chat()
            main_text = f"[手机·{p['name']}·群「{g['name']}」] [图片：{desc}]"
        else:
            c.setdefault("messages", []).append(msg)
            self.save_phone()
            self._phone_refresh_chat()
            main_text = f"[手机·{p['name']}→{c['name']}] [图片：{desc}]"

        # 主对话流
        self.messages.append({"role": "user", "content": main_text})
        self.append_chat("你", main_text, "user")
        self.save_chat()

        # 触发 AI
        self.is_generating = True
        self.btn_send.configure(state="disabled")
        self._update_action_buttons()
        self.set_status("📱 图片发送中…")
        threading.Thread(target=self._request_stream, daemon=True).start()



    def _phone_receive(self, plat_name, contact_name, content, is_initiative=False):
        """AI 说对方在手机里回复了（或主动发）→ 写进手机记录"""
        if not plat_name or not contact_name or not content:
            return
        plat = self._phone_find_platform(plat_name)
        if not plat:
            plat = self._phone_create_platform(plat_name)
        contact = self._phone_find_contact(plat, contact_name)
        if not contact:
            contact = self._phone_create_contact(plat, contact_name)
        now = self.state.get("current_time", "")
        contact.setdefault("messages", []).append({
            "from": "them", "text": content, "time": now
        })
        self.save_phone()
        self.root.after(0, self._phone_refresh_all)
        tag = "主动发来" if is_initiative else "回复"
        self.root.after(0, lambda: self.set_status(f"📱 {plat_name} · {contact_name} {tag}"))

    def _phone_group_receive(self, plat_name, group_name, sender_name, content):
        """AI 说群成员发言 → 写进群记录（群不存在时自动创建）"""
        if not plat_name or not group_name or not content:
            return
        plat = self._phone_find_platform(plat_name)
        if not plat:
            plat = self._phone_create_platform(plat_name)
        # 找群
        group = None
        for g in plat.get("groups", []):
            if g["name"] == group_name:
                group = g
                break
        if not group:
            # ★ 群不存在 → 自动创建
            group = {
                "id": "grp_" + str(abs(hash(group_name + plat["name"])) % 10**8),
                "name": group_name,
                "icon": "👥",
                "member_ids": [],
                "messages": []
            }
            plat.setdefault("groups", []).append(group)
            self.save_phone()
            self.root.after(0, lambda: self.set_status(
                f"📱 自动创建群「{group_name}」（{plat_name}）"
            ))

        # 找发言人的 contact id
        sender_id = None
        for c in plat.get("contacts", []):
            if c["name"] == sender_name:
                sender_id = c["id"]
                break

        now = self.state.get("current_time", "")
        group.setdefault("messages", []).append({
            "from": sender_id or "unknown",
            "sender_name": sender_name,
            "text": content,
            "time": now
        })
        self.save_phone()
        self.root.after(0, self._phone_refresh_all)
        self.root.after(0, lambda: self.set_status(
            f"📱 [{plat_name}·{group_name}] {sender_name} 发言"
        ))


    def _phone_maybe_new_platform(self, plat_name):
        """AI 提到新平台 → 弹窗问"""
        if not plat_name:
            return
        if self._phone_find_platform(plat_name):
            return

        def ask():
            ok = messagebox.askyesno(
                "新平台",
                f"AI 提到了新平台「{plat_name}」。\n\n要把它加入手机吗？"
            )
            if ok:
                plat = self._phone_create_platform(plat_name)
                self.root.after(0, self._phone_refresh_all)
                self.set_status(f"📱 已加入平台「{plat_name}」")

        self.root.after(0, ask)

    def _phone_maybe_add_contact(self, plat_name, contact_name, npc_id):
        """AI 说要加联系人 → 弹窗问"""
        if not plat_name or not contact_name:
            return

        def ask():
            plat = self._phone_find_platform(plat_name)
            if not plat:
                # 平台没有？先建平台（不弹窗）
                plat = self._phone_create_platform(plat_name)
            if self._phone_find_contact(plat, contact_name):
                return
            ok = messagebox.askyesno(
                "新联系人",
                f"要在「{plat_name}」里添加联系人「{contact_name}」吗？"
                + (f"\n\n关联角色：{npc_id}" if npc_id else "")
            )
            if ok:
                self._phone_create_contact(plat, contact_name, npc_id)
                self.root.after(0, self._phone_refresh_all)
                self.set_status(f"📱 已加入联系人「{contact_name}」")

        self.root.after(0, ask)

    # ============================================================
    # 服装库编辑器
    # ============================================================
    def open_outfit_editor(self):
        win = tk.Toplevel(self.root)
        win.title("👕 服装库")
        win.geometry("640x620")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="服装列表（双击编辑）").pack(anchor="w", padx=8, pady=(8, 2))

        lb = tk.Listbox(win, height=14)
        lb.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        def refresh():
            lb.delete(0, "end")
            cur = self.state.get("current_outfit", "")
            for o in self.world.get("outfits", []):
                mark = "✔ " if o["id"] == cur else "  "
                tags = "/".join(o.get("tags", []))
                lb.insert("end", f"{mark}{o.get('emoji','👕')} {o['name']} — {o['desc']}  [{tags}]")

        def get_sel_idx():
            sel = lb.curselection()
            return sel[0] if sel else -1

        def pick_emoji(parent_win, default="👕"):
            dlg = tk.Toplevel(parent_win)
            dlg.title("选择 Emoji")
            dlg.geometry("460x360")
            dlg.transient(parent_win)
            dlg.grab_set()

            groups = {
                "衣服": ["👕", "👔", "👖", "👗", "👘", "👙", "🩳", "🧥", "🥼", "🧣", "🧤", "🧦"],
                "鞋包": ["👞", "👟", "👠", "👡", "👢", "🥿", "🩴", "👜", "👝", "🎒", "🧳", "💼"],
                "配饰": ["🎩", "🧢", "👒", "⛑", "💍", "💎", "⌚", "🕶", "👓", "🎀", "🌂", "☂"],
                "风格": ["🤵", "👰", "🩱", "🩲", "🦺", "🥻", "💃", "🕺", "🧖", "🧘", "🏃", "🎭"],
                "其他": ["❤️", "🔥", "⭐", "🌈", "✨", "💫", "🌸", "🍃", "❄️", "☀️", "🌙", "⚡"],
            }

            state = {"val": default}
            top = tk.Frame(dlg)
            top.pack(fill="x", padx=8, pady=6)
            tk.Label(top, text="当前：").pack(side="left")
            preview = tk.Label(top, text=default, font=("", 24))
            preview.pack(side="left", padx=8)
            entry_var = tk.StringVar(value=default)
            tk.Entry(top, textvariable=entry_var, width=6, font=("", 16)).pack(side="left")
            def upd(*a):
                preview.configure(text=entry_var.get() or " ")
            entry_var.trace_add("write", upd)

            tab = ttk.Notebook(dlg)
            tab.pack(fill="both", expand=True, padx=8, pady=(0, 6))
            for gname, items in groups.items():
                f = tk.Frame(tab)
                tab.add(f, text=f" {gname} ")
                grid = tk.Frame(f)
                grid.pack(fill="both", expand=True, padx=4, pady=4)
                r, c = 0, 0
                for em in items:
                    b = tk.Button(grid, text=em, font=("", 18), width=2,
                                  command=lambda e=em: (entry_var.set(e), upd()))
                    b.grid(row=r, column=c, padx=2, pady=2)
                    c += 1
                    if c >= 8:
                        c = 0
                        r += 1

            bf = tk.Frame(dlg)
            bf.pack(fill="x", padx=8, pady=(0, 8))
            def ok():
                state["val"] = entry_var.get().strip() or default
                dlg.destroy()
            def cancel():
                state["val"] = None
                dlg.destroy()
            tk.Button(bf, text="确定", command=ok, width=10).pack(side="right", padx=4)
            tk.Button(bf, text="取消", command=cancel, width=10).pack(side="right", padx=4)

            dlg.update_idletasks()
            x = parent_win.winfo_x() + (parent_win.winfo_width() - dlg.winfo_width()) // 2
            y = parent_win.winfo_y() + (parent_win.winfo_height() - dlg.winfo_height()) // 2
            dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
            dlg.wait_window()
            return state["val"]

        def edit_dialog(title, outfit=None):
            dlg = tk.Toplevel(win)
            dlg.title(title)
            dlg.geometry("480x460")
            dlg.transient(win)
            dlg.grab_set()

            pad = {"padx": 8, "pady": 4}

            row_emoji = tk.Frame(dlg)
            row_emoji.pack(fill="x", **pad)
            tk.Label(row_emoji, text="Emoji：").pack(side="left")
            emo_var = tk.StringVar(value=(outfit or {}).get("emoji", "👕"))
            emo_show = tk.Label(row_emoji, textvariable=emo_var, font=("", 22), width=3)
            emo_show.pack(side="left", padx=6)
            def choose_emoji():
                v = pick_emoji(dlg, default=emo_var.get())
                if v:
                    emo_var.set(v)
            tk.Button(row_emoji, text="选择…", command=choose_emoji).pack(side="left")

            tk.Label(dlg, text="名称：").pack(anchor="w", **pad)
            name_var = tk.StringVar(value=(outfit or {}).get("name", ""))
            tk.Entry(dlg, textvariable=name_var, width=52).pack(fill="x", padx=8)

            tk.Label(dlg, text="描述（如：深灰三件套 + 皮鞋）：").pack(anchor="w", **pad)
            desc_var = tk.StringVar(value=(outfit or {}).get("desc", ""))
            tk.Entry(dlg, textvariable=desc_var, width=52).pack(fill="x", padx=8)

            tk.Label(dlg, text="风格标签（逗号分隔）：").pack(anchor="w", **pad)
            tags_var = tk.StringVar(value=",".join((outfit or {}).get("tags", [])))
            tk.Entry(dlg, textvariable=tags_var, width=52).pack(fill="x", padx=8)

            tk.Label(dlg, text="单品清单（每行一个）：").pack(anchor="w", **pad)
            items_text = tk.Text(dlg, height=6, wrap="word")
            items_text.pack(fill="both", expand=True, padx=8, pady=(0, 4))
            items_text.insert("1.0", "\n".join((outfit or {}).get("items", [])))

            result = {"val": None}

            def ok():
                name = name_var.get().strip()
                desc = desc_var.get().strip()
                if not name:
                    messagebox.showwarning("提示", "名称不能为空", parent=dlg)
                    return
                if not desc:
                    messagebox.showwarning("提示", "描述不能为空", parent=dlg)
                    return
                tags = [t.strip() for t in tags_var.get().split(",") if t.strip()]
                items = [x.strip() for x in items_text.get("1.0", "end").split("\n") if x.strip()]
                result["val"] = {
                    "emoji": emo_var.get() or "👕",
                    "name": name, "desc": desc,
                    "tags": tags, "items": items,
                }
                dlg.destroy()

            bf = tk.Frame(dlg)
            bf.pack(fill="x", padx=8, pady=8)
            tk.Button(bf, text="确定", command=ok, width=10).pack(side="right", padx=4)
            tk.Button(bf, text="取消", command=dlg.destroy, width=10).pack(side="right", padx=4)

            dlg.update_idletasks()
            x = win.winfo_x() + (win.winfo_width() - dlg.winfo_width()) // 2
            y = win.winfo_y() + (win.winfo_height() - dlg.winfo_height()) // 2
            dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
            dlg.wait_window()
            return result["val"]

        def add_outfit():
            data = edit_dialog("新增服装")
            if not data:
                return
            existing_ids = {o["id"] for o in self.world.get("outfits", [])}
            n = 1
            while f"out_{n}" in existing_ids:
                n += 1
            data["id"] = f"out_{n}"
            self.world.setdefault("outfits", []).append(data)
            self.save_world()
            refresh()

        def edit_outfit():
            i = get_sel_idx()
            if i < 0:
                return
            old = self.world["outfits"][i]
            data = edit_dialog(f"编辑服装 - {old['name']}", outfit=old)
            if not data:
                return
            data["id"] = old["id"]
            self.world["outfits"][i] = data
            self.save_world()
            refresh()

        def del_outfit():
            i = get_sel_idx()
            if i < 0:
                return
            o = self.world["outfits"][i]
            wearing = (self.state.get("current_outfit") == o["id"])
            msg = f"删除服装「{o['name']}」？"
            if wearing:
                msg += "\n\n⚠ 你当前正穿着它，删除后需重新选一套。"
            if not messagebox.askyesno("确认", msg, parent=win):
                return
            del self.world["outfits"][i]
            if wearing:
                if self.world["outfits"]:
                    self.state["current_outfit"] = self.world["outfits"][0]["id"]
                else:
                    self.state["current_outfit"] = ""
                self.save_state()
                self.refresh_status()
            self.save_world()
            refresh()

        def wear_now():
            i = get_sel_idx()
            if i < 0:
                return
            o = self.world["outfits"][i]
            self.state["current_outfit"] = o["id"]
            self.save_state()
            self.refresh_status()
            refresh()
            self.set_status(f"👕 已穿上「{o['name']}」")

        lb.bind("<Double-Button-1>", lambda e: edit_outfit())

        row = tk.Frame(win)
        row.pack(fill="x", padx=8, pady=(0, 4))
        tk.Button(row, text="➕ 新增", command=add_outfit).pack(side="left", padx=2)
        tk.Button(row, text="✏️ 编辑", command=edit_outfit).pack(side="left", padx=2)
        tk.Button(row, text="🗑 删除", command=del_outfit).pack(side="left", padx=2)

        row2 = tk.Frame(win)
        row2.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(row2, text="👕 立即穿上选中", command=wear_now).pack(side="left", padx=2)
        tk.Button(row2, text="关闭", command=win.destroy).pack(side="right", padx=2)

        refresh()

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x,0)}+{max(y,0)}")

    # ============================================================
    # 地图编辑器
    # ============================================================
    def open_map_editor(self):
        win = tk.Toplevel(self.root)
        win.title("📝 地图编辑")
        win.geometry("820x680")
        win.transient(self.root)
        win.grab_set()

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        tab_loc = tk.Frame(nb)
        nb.add(tab_loc, text="  📍 地点  ")

        tk.Label(tab_loc, text="地点列表（双击编辑名称/Emoji）").pack(anchor="w", padx=8, pady=(8, 2))

        lb = tk.Listbox(tab_loc, height=12)
        lb.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        def refresh_locs():
            lb.delete(0, "end")
            for L in self.world["locations"]:
                prefix = "    " if L.get("parent") else ""
                lb.insert("end", f"{prefix}{L['emoji']} {L['name']}   [{L['id']}]")

        def get_selected():
            sel = lb.curselection()
            if not sel:
                return None
            return self.world["locations"][sel[0]]

        def pick_emoji(parent_win, default="📍"):
            dlg = tk.Toplevel(parent_win)
            dlg.title("选择 Emoji")
            dlg.geometry("480x380")
            dlg.transient(parent_win)
            dlg.grab_set()

            emoji_groups = {
                "建筑": ["🏠", "🏢", "🏬", "🏭", "🏨", "🏥", "🏦", "🏫", "⛪", "🏛", "🏰", "🏯"],
                "生活": ["🛋", "🛏", "🚿", "🍳", "🪑", "🚽", "🧺", "🪟", "🚪", "🛁", "🧴", "🧹"],
                "场所": ["🍺", "🍽", "☕", "🍷", "🎭", "🎬", "🎤", "🎮", "📚", "🏋", "⚽", "🌳"],
                "交通": ["🚗", "🚕", "🚌", "🚇", "🚄", "✈️", "🚢", "🚲", "🛵", "🚶", "🛣", "🚦"],
                "其他": ["💼", "📊", "💰", "💊", "📱", "🖥", "⌚", "🎁", "❤️", "⭐", "🌈", "🔥"],
            }

            state = {"val": default}
            top = tk.Frame(dlg)
            top.pack(fill="x", padx=8, pady=6)
            tk.Label(top, text="当前：").pack(side="left")
            preview = tk.Label(top, text=default, font=("", 24))
            preview.pack(side="left", padx=8)
            entry_var = tk.StringVar(value=default)
            tk.Entry(top, textvariable=entry_var, width=6, font=("", 16)).pack(side="left")
            def upd(*a):
                preview.configure(text=entry_var.get() or " ")
            entry_var.trace_add("write", upd)

            tab = ttk.Notebook(dlg)
            tab.pack(fill="both", expand=True, padx=8, pady=(0, 6))
            for gname, items in emoji_groups.items():
                f = tk.Frame(tab)
                tab.add(f, text=f" {gname} ")
                grid = tk.Frame(f)
                grid.pack(fill="both", expand=True, padx=4, pady=4)
                r, c = 0, 0
                for em in items:
                    b = tk.Button(grid, text=em, font=("", 18), width=2,
                                  command=lambda e=em: (entry_var.set(e), upd()))
                    b.grid(row=r, column=c, padx=2, pady=2)
                    c += 1
                    if c >= 8:
                        c = 0
                        r += 1

            bf = tk.Frame(dlg)
            bf.pack(fill="x", padx=8, pady=(0, 8))
            def ok():
                state["val"] = entry_var.get().strip() or default
                dlg.destroy()
            def cancel():
                state["val"] = None
                dlg.destroy()
            tk.Button(bf, text="确定", command=ok, width=10).pack(side="right", padx=4)
            tk.Button(bf, text="取消", command=cancel, width=10).pack(side="right", padx=4)

            dlg.update_idletasks()
            x = parent_win.winfo_x() + (parent_win.winfo_width() - dlg.winfo_width()) // 2
            y = parent_win.winfo_y() + (parent_win.winfo_height() - dlg.winfo_height()) // 2
            dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
            dlg.wait_window()
            return state["val"]

        def edit_loc():
            L = get_selected()
            if not L:
                return
            new_name = simpledialog.askstring("改名", "名称：", initialvalue=L["name"], parent=win)
            if new_name is not None and new_name.strip():
                L["name"] = new_name.strip()
            new_emoji = pick_emoji(win, default=L["emoji"])
            if new_emoji:
                L["emoji"] = new_emoji
            self.save_world()
            refresh_locs()

        def add_loc():
            name = simpledialog.askstring("新增地点", "名称：", parent=win)
            if not name or not name.strip():
                return
            emoji = pick_emoji(win, default="📍") or "📍"
            is_top = messagebox.askyesno("层级", "作为顶层地点？（否 = 需要选父地点）")
            parent = None
            if not is_top:
                tops = self.tops()
                if not tops:
                    messagebox.showwarning("提示", "还没有任何顶层地点")
                    return
                names = [f"{t['emoji']} {t['name']}" for t in tops]
                sel = simpledialog.askstring(
                    "父地点",
                    "输入父地点编号（0起）：\n" + "\n".join(f"{i}. {n}" for i, n in enumerate(names)),
                    parent=win)
                try:
                    parent = tops[int(sel)]["id"]
                except Exception:
                    messagebox.showwarning("错误", "无效的父地点")
                    return
            new_id = "loc_" + str(len(self.world["locations"]) + 1) + "_" + str(abs(hash(name)) % 10000)
            self.world["locations"].append({
                "id": new_id, "name": name.strip(), "emoji": emoji,
                "parent": parent, "children": [], "actions": [],
                "x": None, "y": None, "bg_image": None
            })
            if parent:
                P = self.get_loc(parent)
                if P and new_id not in P["children"]:
                    P["children"].append(new_id)
            self.save_world()
            refresh_locs()

        def del_loc():
            L = get_selected()
            if not L:
                return
            if not messagebox.askyesno("确认", f"删除「{L['name']}」？"):
                return
            if L.get("parent"):
                P = self.get_loc(L["parent"])
                if P and L["id"] in P["children"]:
                    P["children"].remove(L["id"])
            self.world["locations"] = [x for x in self.world["locations"] if x["id"] != L["id"]]
            self.save_world()
            refresh_locs()

        def edit_actions():
            L = get_selected()
            if not L:
                messagebox.showinfo("提示", "请先选择一个地点")
                return
            self._open_actions_editor(L, win)
            self.save_world()

        lb.bind("<Double-Button-1>", lambda e: edit_loc())

        row = tk.Frame(tab_loc)
        row.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(row, text="➕ 新增", command=add_loc).pack(side="left", padx=2)
        tk.Button(row, text="✏️ 编辑", command=edit_loc).pack(side="left", padx=2)
        tk.Button(row, text="🎬 编辑动作", command=edit_actions).pack(side="left", padx=2)
        tk.Button(row, text="🗑 删除", command=del_loc).pack(side="left", padx=2)

        refresh_locs()

        # ========== Tab 2: 交通时间 ==========
        tab_travel = tk.Frame(nb)
        nb.add(tab_travel, text="  🚗 交通时间  ")

        tk.Label(tab_travel,
                 text="只填顶层地点之间的耗时（分钟）。同建筑内子地点之间默认 0 分钟。\n"
                      "留空 = 使用默认值。改一格，对称格会自动跟随。",
                 justify="left").pack(anchor="w", padx=8, pady=(8, 4))

        row_def = tk.Frame(tab_travel)
        row_def.pack(fill="x", padx=8, pady=(0, 6))
        tk.Label(row_def, text="默认耗时（分钟）：").pack(side="left")
        default_var = tk.StringVar(value=str(self.world.get("default_travel_time", 20)))
        tk.Entry(row_def, textvariable=default_var, width=8).pack(side="left")

        matrix_frame = tk.Frame(tab_travel)
        matrix_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        tops = self.tops()
        entries = {}

        def build_matrix():
            for w in matrix_frame.winfo_children():
                w.destroy()
            entries.clear()

            tk.Label(matrix_frame, text="", width=10, borderwidth=1, relief="solid"
                     ).grid(row=0, column=0, sticky="nsew")
            for j, t in enumerate(tops):
                tk.Label(matrix_frame, text=f"{t['emoji']}\n{t['name']}", width=10,
                         borderwidth=1, relief="solid").grid(row=0, column=j + 1, sticky="nsew")
            for i, a in enumerate(tops):
                tk.Label(matrix_frame, text=f"{a['emoji']} {a['name']}", width=10,
                         borderwidth=1, relief="solid").grid(row=i + 1, column=0, sticky="nsew")
                for j, b in enumerate(tops):
                    if a["id"] == b["id"]:
                        tk.Label(matrix_frame, text="—", width=6,
                                 borderwidth=1, relief="solid", bg="#888"
                                 ).grid(row=i + 1, column=j + 1, sticky="nsew")
                        continue
                    key1 = f"{a['id']}->{b['id']}"
                    key2 = f"{b['id']}->{a['id']}"
                    tt = self.world.get("travel_time", {})
                    val = tt.get(key1, tt.get(key2, ""))
                    e = tk.Entry(matrix_frame, width=6, justify="center")
                    e.insert(0, str(val))
                    e.grid(row=i + 1, column=j + 1, sticky="nsew", padx=1, pady=1)
                    entries[(a["id"], b["id"])] = e

            def _sync_sym(aid, bid):
                src = entries.get((aid, bid))
                dst = entries.get((bid, aid))
                if src is None or dst is None:
                    return
                v = src.get()
                dst.delete(0, "end")
                dst.insert(0, v)

            def _make_sync(aid, bid):
                def cb(event=None):
                    _sync_sym(aid, bid)
                return cb

            for (aid, bid), e in entries.items():
                if aid == bid:
                    continue
                e.bind("<FocusOut>", _make_sync(aid, bid))
                e.bind("<Return>", _make_sync(aid, bid))

        build_matrix()

        def save_travel():
            try:
                self.world["default_travel_time"] = max(0, int(default_var.get()))
            except Exception:
                pass
            new_tt = {}
            for (aid, bid), e in entries.items():
                if aid == bid:
                    continue
                v = e.get().strip()
                if not v:
                    continue
                try:
                    mins = int(v)
                except ValueError:
                    continue
                if mins < 0:
                    continue
                new_tt[f"{aid}->{bid}"] = mins
            self.world["travel_time"] = new_tt
            self.save_world()
            msg = f"交通时间已保存（{len(new_tt)} 条）\n\n"
            for k, v in list(new_tt.items())[:8]:
                msg += f"  {k} = {v} 分钟\n"
            if len(new_tt) > 8:
                msg += f"  ... 共 {len(new_tt)} 条"
            messagebox.showinfo("已保存", msg)

        row2 = tk.Frame(tab_travel)
        row2.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(row2, text="💾 保存交通表", command=save_travel).pack(side="left", padx=4)
        tk.Button(row2, text="🔄 重建表格", command=build_matrix).pack(side="left", padx=4)

        tk.Button(win, text="关闭", command=lambda: (self.refresh_map(),
                                                     self.refresh_location_panel(),
                                                     self.refresh_status(),
                                                     win.destroy())).pack(pady=(0, 8))

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x,0)}+{max(y,0)}")

    # ============================================================
    # 动作编辑器
    # ============================================================
    def _open_actions_editor(self, location, parent_win):
        win = tk.Toplevel(parent_win)
        win.title(f"🎬 编辑动作 - {location['name']}")
        win.geometry("560x500")
        win.transient(parent_win)
        win.grab_set()

        tk.Label(win, text="此地点可用的动作按钮（点一下会填入输入框）").pack(anchor="w", padx=8, pady=(8, 2))

        lb = tk.Listbox(win, height=12)
        lb.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        def refresh():
            lb.delete(0, "end")
            for a in location.get("actions", []):
                t = a.get("type", "dialog")
                tp = {"dialog": "💬", "outfit": "👕"}.get(t, "❓")
                lb.insert("end", f"{tp} {a.get('label','?')}   →  {a.get('prompt','')[:40]}")

        def get_sel_idx():
            sel = lb.curselection()
            return sel[0] if sel else -1

        def add_action():
            label = simpledialog.askstring("新增动作", "按钮文字（例如：躺下休息）：", parent=win)
            if not label or not label.strip():
                return
            t = simpledialog.askstring(
                "动作类型",
                "类型：\n"
                "  dialog = 普通动作（填入一句话给 AI）\n"
                "  outfit = 换装（弹出换装窗）\n\n"
                "输入 dialog 或 outfit：",
                initialvalue="dialog", parent=win)
            t = (t or "dialog").strip().lower()
            if t not in ("dialog", "outfit"):
                t = "dialog"

            prompt = ""
            if t == "dialog":
                prompt = simpledialog.askstring(
                    "动作内容", "点击后填入输入框的文字：",
                    initialvalue=f"我{label}", parent=win) or ""

            location.setdefault("actions", []).append({
                "type": t, "label": label.strip(), "prompt": prompt
            })
            self.save_world()
            refresh()

        def edit_action():
            i = get_sel_idx()
            if i < 0:
                return
            a = location["actions"][i]
            new_label = simpledialog.askstring("改按钮文字", "按钮文字：",
                                               initialvalue=a.get("label", ""), parent=win)
            if new_label is not None and new_label.strip():
                a["label"] = new_label.strip()
            if a.get("type") == "dialog":
                new_prompt = simpledialog.askstring("改填入文字", "填入输入框的文字：",
                                                    initialvalue=a.get("prompt", ""), parent=win)
                if new_prompt is not None:
                    a["prompt"] = new_prompt
            self.save_world()
            refresh()

        def del_action():
            i = get_sel_idx()
            if i < 0:
                return
            if not messagebox.askyesno("确认", f"删除动作「{location['actions'][i].get('label')}」？"):
                return
            del location["actions"][i]
            self.save_world()
            refresh()

        def move_up():
            i = get_sel_idx()
            if i <= 0:
                return
            acts = location["actions"]
            acts[i - 1], acts[i] = acts[i], acts[i - 1]
            self.save_world()
            refresh()
            lb.selection_clear(0, "end")
            lb.selection_set(i - 1)

        def move_down():
            i = get_sel_idx()
            acts = location.get("actions", [])
            if i < 0 or i >= len(acts) - 1:
                return
            acts[i + 1], acts[i] = acts[i], acts[i + 1]
            self.save_world()
            refresh()
            lb.selection_clear(0, "end")
            lb.selection_set(i + 1)

        row = tk.Frame(win)
        row.pack(fill="x", padx=8, pady=(0, 4))
        tk.Button(row, text="➕ 新增", command=add_action).pack(side="left", padx=2)
        tk.Button(row, text="✏️ 编辑", command=edit_action).pack(side="left", padx=2)
        tk.Button(row, text="🗑 删除", command=del_action).pack(side="left", padx=2)

        row2 = tk.Frame(win)
        row2.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(row2, text="⬆ 上移", command=move_up).pack(side="left", padx=2)
        tk.Button(row2, text="⬇ 下移", command=move_down).pack(side="left", padx=2)
        tk.Button(row2, text="关闭", command=win.destroy).pack(side="right", padx=2)

        refresh()

        win.update_idletasks()
        x = parent_win.winfo_x() + (parent_win.winfo_width() - win.winfo_width()) // 2
        y = parent_win.winfo_y() + (parent_win.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x,0)}+{max(y,0)}")

    # ============================================================
    # 模型列表
    # ============================================================
    def _refresh_models(self, base_url, api_key, combo_widget):
        """从 API 拉取可用模型列表，填充到下拉框"""
        base_url = (base_url or "").strip().rstrip("/")
        api_key = (api_key or "").strip()
        if not base_url:
            messagebox.showwarning("提示", "请先填写 Base URL")
            return
        if not api_key:
            messagebox.showwarning("提示", "请先填写 API Key")
            return

        url = f"{base_url}/models"
        headers = {"Authorization": f"Bearer {api_key}"}

        def worker():
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    self.root.after(0, lambda: messagebox.showerror(
                        "获取失败",
                        f"HTTP {resp.status_code}\n{resp.text[:200]}"
                    ))
                    return
                data = resp.json()
                if isinstance(data, dict):
                    items = data.get("data", [])
                else:
                    items = data
                ids = []
                for it in items:
                    if isinstance(it, dict):
                        mid = it.get("id")
                        if mid:
                            ids.append(mid)
                    elif isinstance(it, str):
                        ids.append(it)
                ids.sort()

                def apply():
                    if not ids:
                        messagebox.showinfo("提示", "接口返回的模型列表为空")
                        return
                    combo_widget["values"] = ids
                    cur = combo_widget.get().strip()
                    if cur and cur in ids:
                        combo_widget.set(cur)
                    else:
                        combo_widget.set(ids[0])
                    self.set_status(f"✅ 获取到 {len(ids)} 个模型")

                self.root.after(0, apply)
            except requests.exceptions.Timeout:
                self.root.after(0, lambda: messagebox.showerror("获取失败", "请求超时"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("获取失败", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    # ============================================================
    # 设置
    # ============================================================
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.geometry("660x640")
        win.transient(self.root)
        win.grab_set()

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        tab_api = tk.Frame(nb)
        nb.add(tab_api, text="  API / 参数  ")
        pad = {"padx": 8, "pady": 4}

        tk.Label(tab_api, text="API Key").grid(row=0, column=0, sticky="e", **pad)
        api_key_var = tk.StringVar(value=self.config.get("api_key", ""))
        tk.Entry(tab_api, textvariable=api_key_var, width=56, show="*").grid(row=0, column=1, **pad)

        tk.Label(tab_api, text="Base URL").grid(row=1, column=0, sticky="e", **pad)
        base_url_var = tk.StringVar(value=self.config.get("base_url", ""))
        tk.Entry(tab_api, textvariable=base_url_var, width=56).grid(row=1, column=1, **pad)

        tk.Label(tab_api, text="模型").grid(row=2, column=0, sticky="e", **pad)
        model_frame = tk.Frame(tab_api)
        model_frame.grid(row=2, column=1, sticky="w", **pad)
        model_var = tk.StringVar(value=self.config.get("model", ""))
        model_combo = ttk.Combobox(model_frame, textvariable=model_var, width=42)
        model_combo.pack(side="left")
        # 把当前模型放进去，至少有个选项
        model_combo["values"] = [self.config.get("model", "")]
        tk.Button(model_frame, text="🔄 获取模型列表",
                  command=lambda: self._refresh_models(base_url_var.get(), api_key_var.get(), model_combo)
                  ).pack(side="left", padx=(4, 0))

        tk.Label(tab_api, text="Temperature").grid(row=3, column=0, sticky="e", **pad)
        temp_var = tk.DoubleVar(value=self.config.get("temperature", 0.85))
        tk.Scale(tab_api, variable=temp_var, from_=0.0, to=2.0, resolution=0.05,
                 orient="horizontal", length=320).grid(row=3, column=1, sticky="w", **pad)

        tk.Label(tab_api, text="Max Tokens").grid(row=4, column=0, sticky="e", **pad)
        max_tokens_var = tk.StringVar(value=str(self.config.get("max_tokens", 2048)))
        tk.Entry(tab_api, textvariable=max_tokens_var, width=12).grid(row=4, column=1, sticky="w", **pad)

        tk.Label(tab_api, text="对话发送条数").grid(row=5, column=0, sticky="e", **pad)
        recent_var = tk.StringVar(value=str(self.recent_limit))
        tk.Entry(tab_api, textvariable=recent_var, width=12).grid(row=5, column=1, sticky="w", **pad)

        tk.Label(tab_api, text="摘要触发条数").grid(row=6, column=0, sticky="e", **pad)
        trigger_var = tk.StringVar(value=str(self.summary_trigger))
        tk.Entry(tab_api, textvariable=trigger_var, width=12).grid(row=6, column=1, sticky="w", **pad)

        tk.Label(tab_api, text="字体").grid(row=7, column=0, sticky="e", **pad)
        font_var = tk.StringVar(value=self.font_family)
        tk.Entry(tab_api, textvariable=font_var, width=22).grid(row=7, column=1, sticky="w", **pad)

        tk.Label(tab_api, text="字号").grid(row=8, column=0, sticky="e", **pad)
        size_var = tk.IntVar(value=self.font_size)
        tk.Scale(tab_api, variable=size_var, from_=8, to=32, orient="horizontal",
                 length=220).grid(row=8, column=1, sticky="w", **pad)

        tk.Label(tab_api, text="主题").grid(row=9, column=0, sticky="e", **pad)
        theme_var = tk.StringVar(value=self.theme_name)
        ttk.Combobox(tab_api, textvariable=theme_var, values=list(THEMES.keys()),
                     state="readonly", width=16).grid(row=9, column=1, sticky="w", **pad)

        tab_sys = tk.Frame(nb)
        nb.add(tab_sys, text="  🎭 剧情 / 角色设定  ")
        tk.Label(tab_sys, text="剧情背景 / 角色设定（主界面不显示）").pack(anchor="w", padx=8, pady=(8, 2))
        sys_text = tk.Text(tab_sys, wrap="word", undo=True)
        sys_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        sys_text.insert("1.0", self.system_prompt)

        tab_extra = tk.Frame(nb)
        nb.add(tab_extra, text="  🌐 全局附加提示词  ")
        tk.Label(tab_extra, text="全局附加提示词（主界面不显示）").pack(anchor="w", padx=8, pady=(8, 2))
        extra_text = tk.Text(tab_extra, wrap="word", undo=True)
        extra_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        extra_text.insert("1.0", self.global_extra_prompt)

        tab_sum = tk.Frame(nb)
        nb.add(tab_sum, text="  📝 自动摘要  ")
        tk.Label(tab_sum, text="当前累积摘要（可手动修改）").pack(anchor="w", padx=8, pady=(8, 2))
        sum_text = tk.Text(tab_sum, wrap="word", undo=True)
        sum_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        sum_text.insert("1.0", self.summary_text)

        # ===== 数据管理 Tab =====
        tab_data = tk.Frame(nb)
        nb.add(tab_data, text="  💾 数据  ")

        tk.Label(tab_data, text="数据文件位置：",
                 font=("", 10, "bold")).pack(anchor="w", padx=8, pady=(10, 2))
        tk.Label(tab_data, text=os.path.abspath("."),
                 fg="#888888").pack(anchor="w", padx=8)

        tk.Label(tab_data, text="",
                 font=("", 6)).pack()

        tk.Label(tab_data, text="当前存档数据：",
                 font=("", 10, "bold")).pack(anchor="w", padx=8, pady=(8, 2))

        stats_frame = tk.Frame(tab_data)
        stats_frame.pack(fill="x", padx=16, pady=(0, 6))

        def _stats_row(parent, label, value):
            row = tk.Frame(parent)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=value, anchor="w").pack(side="left")

        _stats_row(stats_frame, "对话条数", str(len(self.messages)))
        _stats_row(stats_frame, "笔记字数", str(len(self.memory_note)))
        _stats_row(stats_frame, "摘要字数", str(len(self.summary_text)))
        _stats_row(stats_frame, "地点数", str(len(self.world.get("locations", []))))
        _stats_row(stats_frame, "服装数", str(len(self.world.get("outfits", []))))
        _stats_row(stats_frame, "手机平台", str(len(self.phone.get("platforms", []))))
        total_contacts = sum(len(p.get("contacts", [])) for p in self.phone.get("platforms", []))
        _stats_row(stats_frame, "手机联系人", str(total_contacts))

        tk.Label(tab_data, text="",
                 font=("", 10)).pack()

        tk.Label(tab_data, text="⚠ 以下操作不可撤销，请先备份：",
                 fg="#cc6666", font=("", 10, "bold")).pack(anchor="w", padx=8, pady=(6, 4))

        def reset_dialog(title, description, delete_files, reset_in_memory, refresh_ui=True):
            """通用重置弹窗"""
            if not messagebox.askyesno(
                title,
                f"{description}\n\n确定吗？",
                parent=win
            ):
                return
            # 二次确认
            if not messagebox.askyesno(
                "再次确认",
                "真的要执行吗？此操作不可撤销。",
                parent=win
            ):
                return
            # 删文件
            for f in delete_files:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception as e:
                    messagebox.showerror("删除失败", f"{f}\n{e}", parent=win)
                    return
            # 重置内存
            reset_in_memory()
            # 刷新 UI
            if refresh_ui:
                self.refresh_map()
                self.refresh_location_panel()
                self.refresh_status()
                self.render_history()
                self._update_action_buttons()
                if self._phone_win and self._phone_win.winfo_exists():
                    self._phone_refresh_all()
            win.destroy()
            messagebox.showinfo("完成", "已重置。", parent=self.root)

        def reset_chat_only():
            """只清对话 + 摘要"""
            reset_dialog(
                "清空对话与摘要",
                "将清空：\n"
                "  · 对话记录（chat_history.json）\n"
                "  · 自动摘要（summary.json）\n\n"
                "保留：人设、地图、服装、手机、笔记、API",
                [CHAT_FILE, SUMMARY_FILE],
                lambda: (
                    self.messages.clear(),
                    setattr(self, "summary_text", ""),
                    self.save_chat(),
                    self.save_summary(),
                )
            )

        def reset_phone():
            """只清手机"""
            reset_dialog(
                "重置手机数据",
                "将清空：\n"
                "  · 所有平台、联系人、聊天记录（game_phone.json）\n\n"
                "手机将恢复为只有「微信」一个空平台。",
                [PHONE_FILE],
                lambda: (
                    setattr(self, "phone", json.loads(json.dumps(DEFAULT_PHONE))),
                    self.save_phone(),
                )
            )

        def reset_notes():
            """只清笔记"""
            reset_dialog(
                "清空剧情笔记",
                "将清空：\n"
                "  · memory.json 里的所有笔记",
                [MEMORY_FILE],
                lambda: (
                    setattr(self, "memory_note", ""),
                    self.save_memory(),
                )
            )

        def reset_state():
            """只重置时间和位置"""
            reset_dialog(
                "重置时间与位置",
                "将重置：\n"
                "  · 游戏时间回到初始\n"
                "  · 位置回到初始地点\n"
                "  · 穿着回到初始服装\n\n"
                "剧情、笔记、手机不受影响。",
                [STATE_FILE],
                lambda: (
                    setattr(self, "state", json.loads(json.dumps(DEFAULT_STATE))),
                    self.save_state(),
                    setattr(self, "selected_top",
                            self._find_top_of(self.state.get("current_location")))
                )
            )

        def reset_world():
            """重置世界（地图 + 服装）"""
            reset_dialog(
                "重置地图与服装",
                "将重置：\n"
                "  · 所有地点、子地点、动作（回到默认地图）\n"
                "  · 所有服装（回到默认 3 套）\n\n"
                "对话、手机、笔记不受影响。",
                [WORLD_FILE],
                lambda: (
                    setattr(self, "world", json.loads(json.dumps(DEFAULT_WORLD))),
                    self.save_world(),
                )
            )

        def reset_all():
            """彻底重置（含 API 与人设）"""
            reset_dialog(
                "⚠ 彻底重置（不可撤销）",
                "将清空所有文件：\n"
                "  · 对话、摘要、笔记、手机\n"
                "  · 地图、服装、时间、位置\n"
                "  · 人设、附加规则、API Key、主题\n\n"
                "一切回到程序刚装好时的状态。",
                [CONFIG_FILE, WORLD_FILE, STATE_FILE,
                 MEMORY_FILE, SUMMARY_FILE, CHAT_FILE, PHONE_FILE],
                lambda: (
                    setattr(self, "config", json.loads(json.dumps(DEFAULT_CONFIG))),
                    setattr(self, "world", json.loads(json.dumps(DEFAULT_WORLD))),
                    setattr(self, "state", json.loads(json.dumps(DEFAULT_STATE))),
                    setattr(self, "phone", json.loads(json.dumps(DEFAULT_PHONE))),
                    setattr(self, "messages", []),
                    setattr(self, "memory_note", ""),
                    setattr(self, "summary_text", ""),
                    setattr(self, "system_prompt", DEFAULT_CONFIG["system_prompt"]),
                    setattr(self, "global_extra_prompt", ""),
                    setattr(self, "recent_limit", 20),
                    setattr(self, "summary_trigger", 30),
                    setattr(self, "theme_name", "深色"),
                    setattr(self, "theme", THEMES["深色"].copy()),
                    setattr(self, "font_family", "Microsoft YaHei"),
                    setattr(self, "font_size", 13),
                    self.save_config(),
                    self.save_world(),
                    self.save_state(),
                    self.save_phone(),
                    self.save_chat(),
                    self.save_memory(),
                    self.save_summary(),
                    self.apply_theme(),
                    setattr(self, "selected_top",
                            self._find_top_of(self.state.get("current_location")))
                )
            )

        # 按钮排列
        row_r1 = tk.Frame(tab_data)
        row_r1.pack(fill="x", padx=8, pady=3)
        tk.Button(row_r1, text="🗑 清空对话与摘要", width=20,
                  command=reset_chat_only).pack(side="left", padx=2)
        tk.Button(row_r1, text="📱 重置手机", width=16,
                  command=reset_phone).pack(side="left", padx=2)

        row_r2 = tk.Frame(tab_data)
        row_r2.pack(fill="x", padx=8, pady=3)
        tk.Button(row_r2, text="📌 清空笔记", width=20,
                  command=reset_notes).pack(side="left", padx=2)
        tk.Button(row_r2, text="🕐 重置时间位置", width=16,
                  command=reset_state).pack(side="left", padx=2)

        row_r3 = tk.Frame(tab_data)
        row_r3.pack(fill="x", padx=8, pady=3)
        tk.Button(row_r3, text="🗺 重置地图与服装", width=20,
                  command=reset_world).pack(side="left", padx=2)

        tk.Label(tab_data, text="",
                 font=("", 8)).pack()

        tk.Button(tab_data, text="⚠ 彻底重置（所有数据）",
                  fg="#cc3333", font=("", 10, "bold"),
                  command=reset_all).pack(pady=(6, 8))

        # ===== 底部按钮 =====
        bf = tk.Frame(win)
        bf.pack(fill="x", padx=8, pady=(0, 8))

        def save():
            self.config["api_key"] = api_key_var.get().strip()
            self.config["base_url"] = base_url_var.get().strip()
            self.config["model"] = model_var.get().strip()
            try:
                self.config["temperature"] = float(temp_var.get())
            except Exception:
                pass
            try:
                self.config["max_tokens"] = int(max_tokens_var.get())
            except Exception:
                pass
            try:
                self.recent_limit = max(2, int(recent_var.get()))
            except Exception:
                pass
            try:
                self.summary_trigger = max(5, int(trigger_var.get()))
            except Exception:
                pass

            self.font_family = font_var.get().strip() or "Microsoft YaHei"
            self.font_size = int(size_var.get())
            self.theme_name = theme_var.get()
            self.theme = THEMES[self.theme_name].copy()

            self.system_prompt = sys_text.get("1.0", "end").strip()
            self.global_extra_prompt = extra_text.get("1.0", "end").strip()
            self.summary_text = sum_text.get("1.0", "end").strip()

            self.save_config()
            self.save_summary()
            self.apply_theme()
            self.render_history()
            self._update_action_buttons()
            self.set_status("设置已保存")
            win.destroy()

        tk.Button(bf, text="💾 保存", command=save, width=12).pack(side="right", padx=6)
        tk.Button(bf, text="取消", command=win.destroy, width=12).pack(side="right", padx=6)

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x,0)}+{max(y,0)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()