import io
import json
import math
import os
import random
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from io import BytesIO
from tkinter import *
from tkinter import messagebox, simpledialog, ttk
import cv2
import easyocr
import keyboard
import numpy as np
import pyautogui
import requests
from PIL import Image, ImageGrab, ImageTk

hero_1_var = hero_2_var = hero_3_var = hero_4_var = None
hero1_enabled = hero2_enabled = hero3_enabled = hero4_enabled = None
treasure_event_enabled = None
cake_enabled = None
spell_var = None

# Version du BOT
BOT_VERSION = "0.0.10"


def ping_server(key):
    """Envoie un ping au serveur pour signaler que l'utilisateur est actif."""
    try:
        requests.post(f"{SERVER_URL}/ping", json={"key": key}, timeout=5)
    except:
        pass

def keep_alive():
    """Boucle en arrière-plan qui ping le serveur toutes les 2 minutes tant qu'une licence est chargée."""
    try:
        key = load_license()
        if not key:
            return
        while True:
            ping_server(key)
            time.sleep(120)
    except Exception as e:
        print(f"[KEEP_ALIVE] Erreur: {e}")

def resource_path(relative_path):
    """Résout le chemin d'une ressource, compatible exécution normale et exécutable PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

WEBHOOK_URL = "https://discord.com/api/webhooks/#####"
SERVER_URL = "https://####.pythonanywhere.com"
SERVER_URLL = "https://#####.pythonanywhere.com/upload_screen"
LICENSE_FILE = os.path.join(os.path.abspath("."), "license.json")

def get_hwid():
    """Génère une empreinte unique de la machine (HWID) à partir du MachineGuid, de l'UUID système et du numéro de série de la carte mère, hashés en SHA-256."""
    import subprocess, hashlib, platform

    try:
        mguid = subprocess.check_output(
            r'reg query HKLM\SOFTWARE\Microsoft\Cryptography /v MachineGuid',
            shell=True
        ).decode().split("REG_SZ")[1].strip()
    except:
        mguid = "unknown_mguid"

    try:
        uuid = subprocess.check_output(
            "wmic csproduct get uuid",
            shell=True
        ).decode().split("\n")[1].strip()
    except:
        uuid = "unknown_uuid"

    try:
        baseboard = subprocess.check_output(
            "wmic baseboard get serialnumber",
            shell=True
        ).decode().split("\n")[1].strip()
    except:
        baseboard = "unknown_baseboard"

    raw = f"{mguid}-{uuid}-{baseboard}"
    return hashlib.sha256(raw.encode()).hexdigest()

def save_license(key):
    """Enregistre la clé de licence localement dans license.json."""
    with open(LICENSE_FILE, "w") as f:
        json.dump({"key": key}, f)

def load_license():
    """Charge la clé de licence sauvegardée localement, si elle existe."""
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            return json.load(f).get("key")
    return None

def check_license_with_server(key):
    """Vérifie la clé de licence et la version du bot auprès du serveur (clé + HWID + version envoyés)."""
    import requests
    hwid = get_hwid()
    try:
        response = requests.post(
            f"{SERVER_URL}/check_license",
            json={
                "key": key,
                "hwid": hwid,
                "version": BOT_VERSION,
            },
            timeout=10
        )
        try:
            return response.json()
        except Exception:
            return {"status": "error", "message": "Réponse serveur invalide"}
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de contacter le serveur :\n{e}")
        return {"status": "error", "message": str(e)}

def show_license_window():
    """Affiche la fenêtre de connexion par licence et gère les différents statuts retournés par le serveur (valide, HWID incompatible, révoquée, expirée, mise à jour requise)."""
    saved_key = load_license()

    import threading

    def submit_license():
        """Valide la clé de licence saisie et lance l'application selon le statut retourné par le serveur."""
        key = entry_key.get().strip()
        if not key:
            messagebox.showwarning("Error", "Please enter your license key.")
            return

        result = check_license_with_server(key)
        status = result.get("status", "error")

        if status == "ok":
            save_license(key)
            messagebox.showinfo("Success", "License successfully validated")

            login.destroy()

            import tkinter
            tkinter._default_root = None

            start_main_app()

        elif status == "hwid_mismatch":
            messagebox.showerror("Invalid License", "This key is already used on another machine.")

        elif status == "revoked":
            messagebox.showerror("Revoked License", "This license has been disabled.")

        elif status == "expired":
            messagebox.showerror("Expired License", "This license has expired.")

        elif status == "update_required":
            url = result.get("url", "https://discord.gg/####")
            messagebox.showerror(
                "Update Required",
                f"⚠️ This version of the bot is outdated.\n"
                f"Please download the latest version here:\n{url}"
            )
            login.destroy()
            sys.exit(0)

        else:
            messagebox.showerror("Error", f"Invalid or unrecognized key.\n\n{result}")



    def open_discord():
        """Ouvre le lien d'invitation Discord dans le navigateur par défaut."""
        webbrowser.open("https://discord.gg/#####")

    def get_online_users():
        """Récupère le nombre d'utilisateurs actuellement en ligne depuis le serveur."""
        try:
            r = requests.get(f"{SERVER_URL}/online_users", timeout=5)
            if r.status_code == 200:
                return r.json().get("online", 0)
        except:
            pass
        return "?"

    login = Tk()
    icon = resource_path("img/cocobot.ico")
    login.iconbitmap(icon)
    login.title(f"COCOBOT v{BOT_VERSION} Login")
    login.geometry("580x420")
    login.configure(bg="#1e1e2f")
    login.resizable(False, False)

    w, h = 580, 420
    x = (login.winfo_screenwidth() // 2) - (w // 2)
    y = (login.winfo_screenheight() // 2) - (h // 2)
    login.geometry(f"{w}x{h}+{x}+{y}")

    container = Frame(login, bg="#0f0f17")
    container.pack(expand=True, fill="both")
    header = Frame(container, bg="#0f0f17")
    header.pack(fill="x", side="top", pady=(15, 0))

    try:
        logo_path = resource_path("img/cocobot.png")
        logo_img = Image.open(logo_path)
        logo_img.thumbnail((65, 65), Image.LANCZOS)
        logo_tk = ImageTk.PhotoImage(logo_img)
        logo_label = Label(header, image=logo_tk, bg="#0f0f17")
        logo_label.image = logo_tk
        logo_label.pack(side="left", padx=(20, 10))
    except Exception as e:
        print("Failed to load CocoBot logo:", e)

    title_frame = Frame(header, bg="#0f0f17")
    title_frame.pack(side="left", anchor="w")
    Label(
        title_frame,
        text="CocoBot",
        font=("Segoe UI", 16, "bold"),
        fg="white",
        bg="#0f0f17"
    ).pack(anchor="w")
    Label(
        title_frame,
        text=f"Version {BOT_VERSION}",
        font=("Segoe UI", 9),
        fg="#888",
        bg="#0f0f17"
    ).pack(anchor="w")

    Label(
        container,
        text="Sign in with your license key",
        font=("Segoe UI", 11),
        fg="#AAA",
        bg="#0f0f17"
    ).pack(pady=(40, 10))

    entry_key = Entry(
        container,
        width=35,
        font=("Segoe UI", 12),
        bg="#1e1e2f",
        fg="white",
        insertbackground="white",
        relief="flat",
        justify="center"
    )
    entry_key.pack(ipady=8, pady=(0, 20))
    if saved_key:
        entry_key.insert(0, saved_key)

    btn_login = Button(
        container,
        text="Login",
        command=submit_license,
        font=("Segoe UI", 12, "bold"),
        bg="#3b57ff",
        fg="white",
        activebackground="#546dff",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        bd=0
    )
    btn_login.pack(pady=(0, 25), ipadx=20, ipady=6)
    online_users = get_online_users()
    Label(
        container,
        text=f"🟢 {online_users} user(s) online",
        font=("Segoe UI", 9),
        fg="#4cd964",
        bg="#0f0f17"
    ).pack()

    footer = Frame(container, bg="#0f0f17")
    footer.pack(fill="x", side="bottom", pady=10)

    Label(
        footer,
        text="© 2026 CocoBot",
        font=("Segoe UI", 8),
        fg="#666",
        bg="#0f0f17"
    ).pack(side="left", padx=15)

    try:
        discord_path = resource_path("img/discord.png")
        discord_img = Image.open(discord_path)
        discord_img.thumbnail((36, 36), Image.LANCZOS)
        discord_tk = ImageTk.PhotoImage(discord_img)
        discord_btn = Label(footer, image=discord_tk, bg="#0f0f17", cursor="hand2")
        discord_btn.image = discord_tk
        discord_btn.pack(side="right", padx=15)
        discord_btn.bind("<Button-1>", lambda e: open_discord())
    except Exception as e:
        print("Failed to load Discord logo:", e)

    try:
        login.attributes("-alpha", 1.0)
    except:
        pass

    login.mainloop()




import cv2
import numpy as np
import time
import pyautogui
from tkinter import messagebox
import cv2
import numpy as np
import time
import pyautogui
from tkinter import messagebox


def main_app():
    """Crée la fenêtre principale du bot avec tous les onglets (Config, Heroes, Stats, Profil)."""

    global fenetre, slots_var, number_var, wall_cost_var, click_wall_enabled
    global gold_var, elixir_var, dark_var, gold_stat, elixir_stat, dark_stat
    global victory_stat, defeat_stat, stars_stat, time_stat, current_profile
    global log_var, wall_stat, uptime_running, uptime_seconds
    global profiles_listbox, ocr_search_var
    global hero_1_var, hero_2_var, hero_3_var, hero_4_var
    global hero1_enabled, hero2_enabled, hero3_enabled, hero4_enabled
    global treasure_event_enabled
    global cake_enabled
    global spell_var

    fenetre = Tk()
    fenetre.title(f"CocoBot v{BOT_VERSION}")
    fenetre.geometry("450x420")
    fenetre.configure(bg="#1e1e2f")
    fenetre.attributes("-topmost", True)
    fenetre.attributes("-alpha", 1)
    icon = resource_path("img/cocobot.ico")
    fenetre.iconbitmap(icon)
    keyboard.add_hotkey("f1", lambda: stop_bot())

    ocr_search_var = StringVar(fenetre)
    global webhook_var
    webhook_var = StringVar(fenetre, value=load_webhook())
    wall_stat = IntVar(fenetre, value=0)
    stars_stat = IntVar(fenetre, value=0)
    victory_stat = IntVar(fenetre, value=0)
    defeat_stat = IntVar(fenetre, value=0)
    current_profile = StringVar(fenetre, value="")
    gold_stat = IntVar(fenetre, value=0)
    elixir_stat = IntVar(fenetre, value=0)
    dark_stat = IntVar(fenetre, value=0)
    time_stat = StringVar(fenetre, value="00:00:00")

    uptime_running = False
    uptime_seconds = 0

    wall_cost_var = StringVar(fenetre, value="")
    treasure_event_enabled = BooleanVar(fenetre, value=False)
    click_wall_enabled = BooleanVar(fenetre, value=False)
    slots_var = StringVar(fenetre, value="")
    gold_var = StringVar(fenetre, value="")
    elixir_var = StringVar(fenetre, value="")
    dark_var = StringVar(fenetre, value="")
    number_var = StringVar(fenetre, value="")
    log_var = StringVar(fenetre, value="Bot: Off")
    hero_1_var = StringVar(fenetre, value="")
    hero_2_var = StringVar(fenetre, value="")
    hero_3_var = StringVar(fenetre, value="")
    hero_4_var = StringVar(fenetre, value="")
    spell_var = StringVar(fenetre, value="")
    hero1_enabled = IntVar(fenetre, value=0)
    hero2_enabled = IntVar(fenetre, value=0)
    hero3_enabled = IntVar(fenetre, value=0)
    hero4_enabled = IntVar(fenetre, value=0)
    cake_enabled = BooleanVar(fenetre, value=False)

    def load_icon(name, size=(24, 24)):
        """Charge une image depuis le dossier img et la redimensionne pour l'interface."""
        path = resource_path(f"img/{name}")
        img = Image.open(path).resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    fenetre.geometry("470x400")
    fenetre.configure(bg="#1e1e2f")

    style = ttk.Style()
    style.theme_use("clam")

    style.configure("TLabel", background="#1e1e2f", foreground="#ffffff", font=("Segoe UI", 11))
    style.configure("TButton", background="#2e2e3f", foreground="#ffffff", font=("Segoe UI", 11, "bold"))
    style.configure("TEntry", fieldbackground="#2e2e3f", foreground="#ffffff")
    style.configure("TLabelframe", background="#1e1e2f", foreground="#ffffff", font=("Segoe UI", 12, "bold"))
    style.configure("TLabelframe.Label", background="#1e1e2f", foreground="#ffffff", font=("Segoe UI", 12, "bold"))

    style.configure(
        "Dark.TNotebook",
        background="#1e1e2f",
        borderwidth=0
    )
    style.configure(
        "Dark.TNotebook.Tab",
        background="#1e1e2f",
        foreground="#ffffff",
        padding=[10, 5],
        font=("Segoe UI", 10, "bold")
    )
    style.map(
        "Dark.TNotebook.Tab",
        background=[
            ("selected", "#25253a"),
            ("!selected", "#1e1e2f")
        ],
        foreground=[
            ("selected", "#ffffff"),
            ("!selected", "#cccccc")
        ]
    )

    notebook = ttk.Notebook(fenetre, style="Dark.TNotebook")
    notebook.pack(fill=BOTH, expand=True, padx=15, pady=15)

    tab_config = ttk.Frame(notebook)
    style = ttk.Style()
    style.configure("Custom.TFrame", background="#1e1e2f")

    tab_config = ttk.Frame(notebook, style="Custom.TFrame")
    notebook.add(tab_config, text="Config")

    style = ttk.Style()
    style.configure("Stats.TFrame", background="#1e1e2f")

    tab_stats = ttk.Frame(notebook, style="Stats.TFrame")
    notebook.add(tab_stats, text="Stats")

    config_frame = ttk.LabelFrame(tab_config, text="CONFIGURATION", padding=15)
    config_frame.pack(fill=X, pady=10)

    config_frame = ttk.LabelFrame(tab_config, text="CONFIGURATION", padding=10)
    config_frame.pack(fill=X, padx=10, pady=10)

    left_frame = ttk.Frame(config_frame)
    left_frame.grid(row=0, column=0, padx=10, pady=5, sticky=N)

    ttk.Label(left_frame, text="Slot (1-11)").grid(row=0, column=0, sticky=W, pady=5)
    ttk.Entry(left_frame, textvariable=slots_var, width=12).grid(row=0, column=1, padx=5)

    ttk.Label(left_frame, text="Count per Slot").grid(row=1, column=0, sticky=W, pady=5)
    ttk.Entry(left_frame, textvariable=number_var, width=12).grid(row=1, column=1, padx=5)

    ttk.Label(left_frame, text="Spell Slot").grid(row=2, column=0, sticky=W, pady=5)
    ttk.Entry(left_frame, textvariable=spell_var, width=12).grid(row=2, column=1, padx=5)

    ttk.Label(left_frame, text="Wall cost").grid(row=3, column=0, sticky=W, pady=5)
    ttk.Entry(left_frame, textvariable=wall_cost_var, width=12).grid(row=3, column=1, padx=5)

    style.configure("Dark.TCheckbutton", background="#1e1e2f", foreground="white", font=("Segoe UI", 10))
    ttk.Checkbutton(left_frame, text="Enable Upgrade", variable=click_wall_enabled, style="Dark.TCheckbutton").grid(row=4, column=0, padx=5)
    ttk.Checkbutton(left_frame, text="Treasure Event", variable=treasure_event_enabled, style="Dark.TCheckbutton").grid(row=4, column=1, padx=5)
    ttk.Checkbutton(left_frame, text="Cake", variable=cake_enabled, style="Dark.TCheckbutton").grid(row=4, column=2, padx=5)

    right_frame = ttk.Frame(config_frame)
    right_frame.grid(row=0, column=1, padx=20, pady=5, sticky=N)

    webhook_frame = ttk.Frame(tab_stats)
    webhook_frame.pack(fill=X, pady=(20, 0), padx=10)

    ttk.Label(webhook_frame, text="WEBHOOK:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=5)
    webhook_entry = ttk.Entry(webhook_frame, textvariable=webhook_var, width=40)
    webhook_entry.pack(side=LEFT, padx=5)

    def save_webhook_event(*_):
        """Sauvegarde le webhook dès que le champ texte change."""
        save_webhook(webhook_var.get())
        write_log(f"🔗 Webhook sauvegardé : {webhook_var.get()}")

    webhook_var.trace_add("write", save_webhook_event)
    info_img = load_icon("i.png", (15, 15))
    buttonnn = Button(
        webhook_frame,
        image=info_img,
        bg="#1e1e2f",
        activebackground="#1e1e2f",
        borderwidth=0,
        highlightthickness=0,
        takefocus=False,
        width=30,
        command=lambda: messagebox.showinfo(
            "Discord Webhook",
            "To get your webhook:\n Go to Server Settings > Integrations > Webhooks"
        )
    )
    buttonnn.pack(side=LEFT, padx=5)

    webhook_frame.image = info_img

    gold_icon = load_icon("gold.png")
    elixir_icon = load_icon("elixir.png")
    dark_icon = load_icon("dark.png")

    fenetre.icons = [gold_icon, elixir_icon, dark_icon]

    ttk.Label(right_frame, text="Gold ≥", background="#1e1e2f").grid(row=0, column=1, sticky=W, pady=5)
    ttk.Entry(right_frame, textvariable=gold_var, width=12).grid(row=0, column=2, padx=5)

    ttk.Label(right_frame, text="Elixir ≥", background="#1e1e2f").grid(row=1, column=1, sticky=W, pady=5)
    ttk.Entry(right_frame, textvariable=elixir_var, width=12).grid(row=1, column=2, padx=5)

    ttk.Label(right_frame, text="Dark ≥", background="#1e1e2f").grid(row=2, column=1, sticky=W, pady=5)
    ttk.Entry(right_frame, textvariable=dark_var, width=12).grid(row=2, column=2, padx=5)

    startstop_frame = ttk.LabelFrame(tab_config, text="Actions", padding=10)
    startstop_frame.pack(fill=X, padx=10, pady=10)

    ttk.Button(startstop_frame, text="Start", command=start_bot).grid(row=0, column=0, padx=5, pady=5, sticky=W)
    ttk.Button(startstop_frame, text="Stop", command=stop_bot).grid(row=0, column=1, padx=5, pady=5, sticky=W)

    ttk.Label(startstop_frame, textvariable=log_var, foreground="#00FFFF").grid(row=0, column=2, padx=10, sticky=W)

    tab_profiles = ttk.Frame(notebook, style="Custom.TFrame")
    notebook.add(tab_profiles, text="Profil")

    profiles_frame = ttk.LabelFrame(tab_profiles, text="Profil Setting", padding=15)
    profiles_frame.pack(fill=BOTH, expand=True, pady=10, padx=10)

    profiles_listbox = Listbox(
        profiles_frame,
        height=8,
        exportselection=False,
        bg="#393959",
        fg="white",
        selectbackground="#25253a",
        selectforeground="white",
        highlightthickness=0,
        borderwidth=0,
        activestyle="none"
    )

    profiles_listbox.grid(row=0, column=0, rowspan=6, padx=10, pady=5, sticky="ns")
    scrollbar = ttk.Scrollbar(profiles_frame, orient=VERTICAL, command=profiles_listbox.yview)
    scrollbar.grid(row=0, column=1, rowspan=6, sticky="ns")
    profiles_listbox.config(yscrollcommand=scrollbar.set)

    def refresh_profiles_listbox():
        """Réaffiche la liste des profils et surligne le profil actif."""
        profiles_listbox.delete(0, END)
        configs = load_all_configs()

        for name in sorted(configs.keys()):
            profiles_listbox.insert(END, name)

        for i in range(profiles_listbox.size()):
            item_name = profiles_listbox.get(i)
            if item_name == current_profile.get():
                profiles_listbox.itemconfig(i, bg="#25253a", fg="white")
            else:
                profiles_listbox.itemconfig(i, bg="#393959", fg="white")

        profiles_listbox.config(
            selectbackground="#25253a",
            selectforeground="white",
            activestyle="none"
        )

        profiles_listbox.selection_clear(0, END)

    def load_selected_profile(*_):
        """Charge la configuration du profil sélectionné dans les champs de l'interface."""
        global current_profile
        try:
            name = current_profile.get().strip()
            configs = load_all_configs()

            if name not in configs:
                write_log(f"⚠️ Profil '{name}' introuvable.")
                return

            cfg = configs[name]

            if "heroes" not in cfg:
                cfg["heroes"] = {
                    "hero1": {"enabled": 0, "delay": 0},
                    "hero2": {"enabled": 0, "delay": 0},
                    "hero3": {"enabled": 0, "delay": 0},
                    "hero4": {"enabled": 0, "delay": 0},
                }
                save_all_configs(configs)
                write_log(f"🧩 Section 'heroes' ajoutée automatiquement au profil '{name}'.")

            slots_var.set(cfg.get("slots", slots_var.get()))
            number_var.set(cfg.get("number", number_var.get()))
            gold_var.set(cfg.get("gold", gold_var.get()))
            elixir_var.set(cfg.get("elixir", elixir_var.get()))
            dark_var.set(cfg.get("dark", dark_var.get()))
            wall_cost_var.set(cfg.get("wall_cost", wall_cost_var.get()))
            click_wall_enabled.set(cfg.get("click_wall_enabled", click_wall_enabled.get()))

            heroes = cfg.get("heroes", {})

            hero1_data = heroes.get("hero1") or {}
            hero2_data = heroes.get("hero2") or {}
            hero3_data = heroes.get("hero3") or {}
            hero4_data = heroes.get("hero4") or {}

            hero1_enabled.set(hero1_data.get("enabled", hero1_enabled.get()))
            hero2_enabled.set(hero2_data.get("enabled", hero2_enabled.get()))
            hero3_enabled.set(hero3_data.get("enabled", hero3_enabled.get()))
            hero4_enabled.set(hero4_data.get("enabled", hero4_enabled.get()))

            hero_1_var.set(hero1_data.get("delay", hero_1_var.get()))
            hero_2_var.set(hero2_data.get("delay", hero_2_var.get()))
            hero_3_var.set(hero3_data.get("delay", hero_3_var.get()))
            hero_4_var.set(hero4_data.get("delay", hero_4_var.get()))

            write_log(f"⚙️ Profil '{name}' chargé avec succès.")

        except Exception as e:
            write_log(f"⚠️ Erreur lors du chargement du profil: {e}")

    def highlight_current_profile():
        """Met en couleur le profil actuellement chargé dans la liste."""
        for i in range(profiles_listbox.size()):
            name = profiles_listbox.get(i)
            if name == current_profile.get():
                profiles_listbox.itemconfig(i, bg="lightgreen", fg="white")
            else:
                profiles_listbox.itemconfig(i, bg="#393959", fg="white")

    def create_profile():
        """Crée un nouveau profil à partir des valeurs actuelles de l'interface."""
        global current_profile
        global hero_1_var, hero_2_var, hero_3_var, hero_4_var
        global hero1_enabled, hero2_enabled, hero3_enabled, hero4_enabled

        name = simpledialog.askstring("Create Profile", "Name of the new profile:")
        if not name:
            return
        configs = load_all_configs()
        if name in configs:
            messagebox.showerror("Error", "This profile already exists!")
            return

        configs[name] = {
            "slots": slots_var.get(),
            "number": number_var.get(),
            "gold": gold_var.get(),
            "elixir": elixir_var.get(),
            "dark": dark_var.get(),
            "wall_cost": wall_cost_var.get(),
            "click_wall_enabled": click_wall_enabled.get(),
            "heroes": {
                "hero1": {"delay": hero_1_var.get(), "enabled": hero1_enabled.get()},
                "hero2": {"delay": hero_2_var.get(), "enabled": hero2_enabled.get()},
                "hero3": {"delay": hero_3_var.get(), "enabled": hero3_enabled.get()},
                "hero4": {"delay": hero_4_var.get(), "enabled": hero4_enabled.get()},
            }
        }

        save_all_configs(configs)
        write_log(f"💾 Profile '{name}' created.")
        current_profile.set(name)
        refresh_profiles_listbox()

    def delete_profile():
        """Supprime le profil sélectionné dans la liste, après confirmation."""
        global current_profile
        global hero_1_var, hero_2_var, hero_3_var, hero_4_var
        global hero1_enabled, hero2_enabled, hero3_enabled, hero4_enabled

        selection = profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("Error", "No profile selected.")
            return
        name = profiles_listbox.get(selection[0])
        if messagebox.askyesno("Delete Profile", f"Delete profile '{name}'?"):
            configs = load_all_configs()
            if name in configs:
                del configs[name]
                save_all_configs(configs)
                write_log(f"🗑️ Profile '{name}' deleted.")
                if current_profile.get() == name:
                    current_profile.set("")
                refresh_profiles_listbox()

    def rename_profile():
        """Renomme le profil sélectionné dans la liste."""
        global current_profile
        global hero_1_var, hero_2_var, hero_3_var, hero_4_var
        global hero1_enabled, hero2_enabled, hero3_enabled, hero4_enabled

        selection = profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("Error", "No profile selected.")
            return
        old_name = profiles_listbox.get(selection[0])
        new_name = simpledialog.askstring("Rename Profile", f"Rename '{old_name}' to:")
        if not new_name:
            return
        configs = load_all_configs()
        if new_name in configs:
            messagebox.showerror("Error", "A profile with this name already exists!")
            return
        configs[new_name] = configs.pop(old_name)
        save_all_configs(configs)
        write_log(f"✏️ Profile '{old_name}' renamed to '{new_name}'.")
        if current_profile.get() == old_name:
            current_profile.set(new_name)
            refresh_profiles_listbox()

    def save_current_profile():
        """Écrase le profil actif avec les valeurs actuelles de l'interface."""
        global current_profile
        global hero1_enabled, hero2_enabled, hero3_enabled, hero4_enabled
        global hero_1_var, hero_2_var, hero_3_var, hero_4_var

        try:
            name = current_profile.get().strip()
            if not name:
                messagebox.showwarning("Error", "No active profile to save.")
                return

            configs = load_all_configs()

            configs[name] = {
                "slots": slots_var.get(),
                "number": number_var.get(),
                "gold": gold_var.get(),
                "elixir": elixir_var.get(),
                "dark": dark_var.get(),
                "wall_cost": wall_cost_var.get(),
                "click_wall_enabled": click_wall_enabled.get(),
                "heroes": {
                    "hero1": {"enabled": hero1_enabled.get(), "delay": hero_1_var.get()},
                    "hero2": {"enabled": hero2_enabled.get(), "delay": hero_2_var.get()},
                    "hero3": {"enabled": hero3_enabled.get(), "delay": hero_3_var.get()},
                    "hero4": {"enabled": hero4_enabled.get(), "delay": hero_4_var.get()},
                }
            }

            save_all_configs(configs)
            write_log(f"💾 Profile '{name}' saved successfully.")

        except Exception as e:
            write_log(f"⚠️ Erreur sauvegarde profil: {e}")
        update_profile_dropdown()

    def load_profile_from_listbox():
        """Sélectionne, charge et surligne le profil choisi depuis l'onglet Profil."""
        global current_profile
        global hero_1_var, hero_2_var, hero_3_var, hero_4_var
        global hero1_enabled, hero2_enabled, hero3_enabled, hero4_enabled

        selection = profiles_listbox.curselection()
        if not selection:
            messagebox.showwarning("Error", "No profile selected.")
            return
        name = profiles_listbox.get(selection[0])
        current_profile.set(name)
        load_selected_profile()
        highlight_current_profile()
        write_log(f"⚙️ Profile '{name}' loaded from the Profiles tab.")

    refresh_profiles_listbox()

    style = ttk.Style()
    style.theme_use("clam")

    style.configure("TLabelframe", background="#1e1e2f", foreground="#FFFFFF", borderwidth=1)
    style.configure("TLabelframe.Label", background="#1e1e2f", foreground="#FFFFFF")
    style.configure("TFrame", background="#1e1e2f")
    style.configure("TLabel", background="#1e1e2f", foreground="#FFFFFF")

    stat_frame = ttk.Frame(tab_stats, padding=15, style="Custom.TFrame")
    stat_frame.pack(fill=X, pady=10)

    gold_icon = load_icon("gold.png")
    elixir_icon = load_icon("elixir.png")
    dark_icon = load_icon("dark.png")
    uptime_icon = load_icon("uptime.png")
    wall_icon = load_icon("wall_Icon.png")
    win = load_icon("win.png")
    stars = load_icon("stars.png")
    losse = load_icon("losse.png")
    fenetre.icons = [gold_icon, elixir_icon, dark_icon, uptime_icon, wall_icon, win, stars, losse]

    loot_frame = ttk.LabelFrame(stat_frame, text="LOOT STATS", padding=10)
    loot_frame.grid(row=0, column=0, padx=10, sticky="nsew")

    Label(loot_frame, image=gold_icon, bg="#1e1e2f").grid(row=0, column=0, padx=6)
    ttk.Label(loot_frame, text="Gold :", foreground="#FFD700").grid(row=0, column=1, sticky=W, padx=5)
    ttk.Label(loot_frame, textvariable=gold_stat, foreground="#FFD700").grid(row=0, column=2, sticky=W, padx=5)

    Label(loot_frame, image=elixir_icon, bg="#1e1e2f").grid(row=1, column=0, padx=6)
    ttk.Label(loot_frame, text="Elixir :", foreground="#DD56D0").grid(row=1, column=1, sticky=W, padx=5)
    ttk.Label(loot_frame, textvariable=elixir_stat, foreground="#DD56D0").grid(row=1, column=2, sticky=W, padx=5)

    Label(loot_frame, image=dark_icon, bg="#1e1e2f").grid(row=2, column=0, padx=6)
    ttk.Label(loot_frame, text="Dark :", foreground="#FFFFFF").grid(row=2, column=1, sticky=W, padx=5)
    ttk.Label(loot_frame, textvariable=dark_stat, foreground="#FFFFFF").grid(row=2, column=2, sticky=W, padx=5)

    Label(loot_frame, image=wall_icon, bg="#1e1e2f").grid(row=3, column=0, padx=6)
    ttk.Label(loot_frame, text="Wall :", foreground="#FFA500").grid(row=3, column=1, sticky=W, padx=5)
    ttk.Label(loot_frame, textvariable=wall_stat, foreground="#FFA500").grid(row=3, column=2, sticky=W, padx=5)

    Label(loot_frame, image=uptime_icon, bg="#1e1e2f").grid(row=4, column=0, padx=6)
    ttk.Label(loot_frame, text="Uptime :", foreground="#00FFAA").grid(row=4, column=1, sticky=W, padx=5)
    ttk.Label(loot_frame, textvariable=time_stat, foreground="#00FFAA").grid(row=4, column=2, sticky=W, padx=5)

    raid_frame = ttk.LabelFrame(stat_frame, text="RAID STATS", padding=10)
    raid_frame.grid(row=0, column=1, padx=10, sticky="nsew")

    Label(raid_frame, image=win, bg="#1e1e2f").grid(row=0, column=0, padx=6)
    ttk.Label(raid_frame, text="Wins :", foreground="#00FF00").grid(row=0, column=1, sticky=W, padx=5)
    ttk.Label(raid_frame, textvariable=victory_stat, foreground="#00FF00").grid(row=0, column=2, sticky=W, padx=5)

    Label(raid_frame, image=losse, bg="#1e1e2f").grid(row=1, column=0, padx=6)
    ttk.Label(raid_frame, text="Losses :", foreground="#FF3333").grid(row=1, column=1, sticky=W, padx=5)
    ttk.Label(raid_frame, textvariable=defeat_stat, foreground="#FF3333").grid(row=1, column=2, sticky=W, padx=5)

    Label(raid_frame, image=stars, bg="#1e1e2f").grid(row=2, column=0, padx=6)
    ttk.Label(raid_frame, text="Stars :", foreground="#FFD700").grid(row=2, column=1, sticky=W, padx=5)
    ttk.Label(raid_frame, textvariable=stars_stat, foreground="#FFD700").grid(row=2, column=2, sticky=W, padx=5)

    tab_heroes = ttk.Frame(notebook, style="Custom.TFrame")
    notebook.insert(1, tab_heroes, text="Heroes")

    heroes_frame = ttk.LabelFrame(tab_heroes, text="HEROES ABILITIES", padding=15)
    heroes_frame.pack(fill=X, padx=10, pady=10)

    hero1_icon = load_icon("hero_1.png", size=(48, 48))
    hero2_icon = load_icon("hero_2.png", size=(48, 48))
    hero3_icon = load_icon("hero_3.png", size=(48, 48))
    hero4_icon = load_icon("hero_4.png", size=(48, 48))
    info_img = load_icon("i.png", (15, 15))
    fenetre.icons += [hero1_icon, hero2_icon, hero3_icon, hero4_icon, info_img]

    Label(heroes_frame, image=hero1_icon, bg="#1e1e2f").grid(row=0, column=0, padx=6, pady=6)
    ttk.Entry(heroes_frame, textvariable=hero_1_var, width=20).grid(row=0, column=1, padx=5, pady=6, sticky=W)
    Button(
        heroes_frame,
        image=info_img,
        bg="#1e1e2f",
        activebackground="#1e1e2f",
        borderwidth=0,
        highlightthickness=0,
        takefocus=False,
        width=18,
        command=lambda: messagebox.showinfo("Hero 1", "Enter the time for the activation of abilities")
    ).grid(row=0, column=2, padx=5, pady=6)
    Checkbutton(heroes_frame, variable=hero1_enabled, bg="#1e1e2f", activebackground="#1e1e2f").grid(row=0, column=3, padx=5)

    Label(heroes_frame, image=hero2_icon, bg="#1e1e2f").grid(row=1, column=0, padx=6, pady=6)
    ttk.Entry(heroes_frame, textvariable=hero_2_var, width=20).grid(row=1, column=1, padx=5, pady=6, sticky=W)
    Button(
        heroes_frame,
        image=info_img,
        bg="#1e1e2f",
        activebackground="#1e1e2f",
        borderwidth=0,
        highlightthickness=0,
        takefocus=False,
        width=18,
        command=lambda: messagebox.showinfo("Hero 2", "Enter the time for the activation of abilities")
    ).grid(row=1, column=2, padx=5, pady=6)
    Checkbutton(heroes_frame, variable=hero2_enabled, bg="#1e1e2f", activebackground="#1e1e2f").grid(row=1, column=3, padx=5)

    Label(heroes_frame, image=hero3_icon, bg="#1e1e2f").grid(row=2, column=0, padx=6, pady=6)
    ttk.Entry(heroes_frame, textvariable=hero_3_var, width=20).grid(row=2, column=1, padx=5, pady=6, sticky=W)
    Button(
        heroes_frame,
        image=info_img,
        bg="#1e1e2f",
        activebackground="#1e1e2f",
        borderwidth=0,
        highlightthickness=0,
        takefocus=False,
        width=18,
        command=lambda: messagebox.showinfo("Hero 3", "Enter the time for the activation of abilities")
    ).grid(row=2, column=2, padx=5, pady=6)
    Checkbutton(heroes_frame, variable=hero3_enabled, bg="#1e1e2f", activebackground="#1e1e2f").grid(row=2, column=3, padx=5)

    Label(heroes_frame, image=hero4_icon, bg="#1e1e2f").grid(row=3, column=0, padx=6, pady=6)
    ttk.Entry(heroes_frame, textvariable=hero_4_var, width=20).grid(row=3, column=1, padx=5, pady=6, sticky=W)
    Button(
        heroes_frame,
        image=info_img,
        bg="#1e1e2f",
        activebackground="#1e1e2f",
        borderwidth=0,
        highlightthickness=0,
        takefocus=False,
        width=18,
        command=lambda: messagebox.showinfo("Hero 4", "Enter the time for the activation of abilities")
    ).grid(row=3, column=2, padx=5, pady=6)
    Checkbutton(heroes_frame, variable=hero4_enabled, bg="#1e1e2f", activebackground="#1e1e2f").grid(row=3, column=3, padx=5)
    ttk.Button(profiles_frame, text="Create", command=create_profile).grid(row=0, column=2, padx=10, pady=5, sticky="ew")
    ttk.Button(profiles_frame, text="Rename", command=rename_profile).grid(row=1, column=2, padx=10, pady=5, sticky="ew")
    ttk.Button(profiles_frame, text="Delete", command=delete_profile).grid(row=2, column=2, padx=10, pady=5, sticky="ew")
    ttk.Button(profiles_frame, text="Load", command=load_profile_from_listbox).grid(row=3, column=2, padx=10, pady=5, sticky="ew")
    ttk.Button(profiles_frame, text="Save changes", command=save_current_profile).grid(row=4, column=2, padx=10, pady=5, sticky="ew")

    update_uptime()
    write_log("Application lancée avec onglets et AFK checker.")


def start_main_app():
    """Lance le bot principal une fois la licence validée."""
    threading.Thread(target=keep_alive, daemon=True).start()

    global fenetre
    main_app()

    write_log("[INIT] Boucle principale Tkinter démarrée.")
    write_log(f"[DEBUG] Fenêtre active ? -> {fenetre.winfo_exists()}")
    fenetre.mainloop()


gold_accum = 0
elixir_accum = 0
CONFIG_PATH = os.path.join(os.path.abspath("."), "config.json")
current_profile = None
WEBHOOK_CONFIG = os.path.join(os.path.abspath("."), "webhook.json")


def save_webhook(url):
    """Enregistre l'URL du webhook Discord dans webhook.json."""
    with open(WEBHOOK_CONFIG, "w", encoding="utf-8") as f:
        json.dump({"webhook": url}, f, indent=4)


def load_webhook():
    """Récupère l'URL du webhook Discord sauvegardée, ou une chaîne vide si absente."""
    if os.path.exists(WEBHOOK_CONFIG):
        with open(WEBHOOK_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f).get("webhook", "")
    return ""


def load_all_configs():
    """Charge tous les profils sauvegardés depuis config.json."""
    global current_profile
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_all_configs(configs):
    """Écrit tous les profils dans config.json."""
    global current_profile
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=4, ensure_ascii=False)


def update_profile_dropdown():
    """Met à jour la liste des profils affichés dans l'interface."""
    configs = load_all_configs()
    profile_names = sorted(configs.keys())

    profiles_listbox.delete(0, END)

    for name in profile_names:
        profiles_listbox.insert(END, name)

    if current_profile.get() not in profile_names:
        current_profile.set(profile_names[0] if profile_names else "Default")


log_lock = threading.Lock()
log_file_path = resource_path("bot_log.txt")


def write_log(msg):
    """Affiche un message dans la console et l'ajoute au fichier de log avec l'heure."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    try:
        print(line.strip())
    except:
        pass
    with log_lock:
        try:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(line)
        except:
            pass


last_webhook_time = 0
WEBHOOK_COOLDOWN = 30

import requests
from datetime import datetime


def send_discord_stats():
    """Envoie un résumé des statistiques (butin, murs, victoires) sur Discord via webhook."""
    global webhook_var, gold_stat, elixir_stat, dark_stat
    global victory_stat, defeat_stat, stars_stat, wall_stat, time_stat

    WEBHOOK_URL = webhook_var.get()
    if not WEBHOOK_URL:
        write_log("❌ Aucun webhook défini, envoi Discord annulé.")
        return

    uptime = time_stat.get() if time_stat.get() else "00:00:00"

    embed = {
        "username": "COCOBOT",
        "avatar_url": "https://i.imgur.com/Bna7ve9.png",
        "embeds": [
            {
                "title": "⚡ COCOBOT AutoFarm Live Stats",
                "color": 0x2ecc71,
                "thumbnail": {"url": "https://i.imgur.com/Bna7ve9.png"},
                "fields": [
                    {
                        "name": "⏳ UPTIME",
                        "value": f"```{uptime}```",
                        "inline": False
                    },
                    {
                        "name": "🧱 WALLS UPGRADED",
                        "value": f"```Number: {wall_stat.get()}```",
                        "inline": False
                    },
                    {
                        "name": "📦 TOTAL LOOTED",
                        "value": (
                            f"```🟡 Gold: {gold_stat.get():,}\n"
                            f"🟣 Elixir: {elixir_stat.get():,}\n"
                            f"⚫ Dark: {dark_stat.get():,}```"
                        ),
                        "inline": False
                    },
                    {
                        "name": "🛡 BATTLE STATS",
                        "value": (
                            f"```🗡 Total Attacks: {victory_stat.get() + defeat_stat.get()}\n"
                            f"🏆 Wins: {victory_stat.get()}\n"
                            f"💀 Losses: {defeat_stat.get()}\n"
                            f"⭐ Stars: {stars_stat.get()}```"
                        ),
                        "inline": False
                    },
                ],
                "footer": {
                    "text": f"COCOBOT v{BOT_VERSION} • AutoFarm System",
                    "icon_url": "https://i.imgur.com/Bna7ve9.png"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }

    try:
        requests.post(WEBHOOK_URL, json=embed)
        write_log("✅ Stats envoyées sur Discord (embed stylé) !")
    except Exception as e:
        write_log(f"❌ Erreur envoi webhook : {e}")


def check_white_dominance():
    """Regarde 3 zones de l'écran pour compter le nombre d'étoiles obtenues (zone blanche = étoile)."""
    zones = [
        ((711, 211, 804 - 711, 260 - 211), "Zone 1"),
        ((907, 227, 926 - 907, 237 - 227), "Zone 2"),
        ((1108, 280, 1175 - 1108, 289 - 280), "Zone 3"),
    ]
    results = []
    dominant_count = 0
    for (x, y, w, h), label in zones:
        img = pyautogui.screenshot(region=(x, y, w, h))
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        white_pixels = np.sum(gray > 150)
        total_pixels = gray.size
        white_ratio = white_pixels / total_pixels
        is_white_dominant = white_ratio > 0.4
        result_text = f"{label}: {'✅ Oui' if is_white_dominant else '❌ Non'} ({white_ratio*100:.1f}%)"
        results.append(result_text)
        write_log(result_text)
        if is_white_dominant:
            dominant_count += 1

    if dominant_count > 0:
        stars_stat.set(stars_stat.get() + dominant_count)
        write_log(f"⭐ Stars détectées : +{dominant_count} → Total = {stars_stat.get()}")

        victory_stat.set(victory_stat.get() + 1)
        write_log("🏆 Victoire détectée → compteur Victory +1")

    else:
        write_log("❌ Aucune zone blanche dominante détectée.")

        defeat_stat.set(defeat_stat.get() + 1)
        write_log("⚔️ Défaite détectée → compteur Defeat +1")


def start_heroes_click():
    """Prépare les délais d'activation de chaque héros coché et lance les clics."""
    global hero_1_var, hero_2_var, hero_3_var, hero_4_var
    global hero1_enabled, hero2_enabled, hero3_enabled, hero4_enabled

    hero_delays = {}

    if hero1_enabled.get() == 1:
        hero_delays["hero1"] = int(hero_1_var.get()) if str(hero_1_var.get()).isdigit() else 0
    if hero2_enabled.get() == 1:
        hero_delays["hero2"] = int(hero_2_var.get()) if str(hero_2_var.get()).isdigit() else 0
    if hero3_enabled.get() == 1:
        hero_delays["hero3"] = int(hero_3_var.get()) if str(hero_3_var.get()).isdigit() else 0
    if hero4_enabled.get() == 1:
        hero_delays["hero4"] = int(hero_4_var.get()) if str(hero_4_var.get()).isdigit() else 0

    if not hero_delays:
        write_log("⚠️ Aucun héros sélectionné pour l'activation.")
        return

    write_log("[🚀] Starting hero activation timing...")
    time.sleep(0.5)
    click_heroes(hero_delays)


def click_heroes(hero_delays):
    """Clique sur chaque héros à l'écran au moment défini dans hero_delays (en secondes)."""
    heroes = ["hero1", "hero2", "hero3", "hero4"]
    threshold = 0.6

    templates = {}
    for hero in heroes:
        hero_templates = []

        for i in range(1, 6):
            path = resource_path(f"img/{hero}_{i}.png")
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is not None:
                hero_templates.append(img)
        if not hero_templates:
            path = resource_path(f"img/{hero}.png")
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is not None:
                hero_templates.append(img)
            else:
                write_log(f"⚠️ Template not found: {path}")

        templates[hero] = hero_templates

    write_log("🚀 Starting hero activation timing...")
    start_time = time.time()
    clicked = {h: False for h in heroes}

    while not all(clicked.values()):
        now = time.time() - start_time

        for hero in heroes:
            delay = hero_delays.get(hero, 0)
            if not clicked[hero] and now >= delay:
                hero_templates = templates.get(hero, [])
                if not hero_templates:
                    clicked[hero] = True
                    continue

                template = random.choice(hero_templates)

                try:
                    screenshot = ImageGrab.grab()
                    screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)

                    if max_val >= threshold:
                        x, y = max_loc
                        h, w = template.shape[:2]

                        cx = x + random.randint(int(w * 0.2), int(w * 0.8))
                        cy = y + random.randint(int(h * 0.2), int(h * 0.8))

                        pyautogui.click(cx, cy)
                        write_log(f"✅ {hero} clicked at t={now:.1f}s (confidence={max_val:.2f}) | Click: ({cx}, {cy})")

                    else:
                        write_log(f"❌ {hero} not found at t={now:.1f}s (max_val={max_val:.2f})")

                except Exception as e:
                    write_log(f"❌ Error processing {hero}: {e}")

                clicked[hero] = True

        time.sleep(0.2)


def process_wall_loop_auto():
    """Lance les améliorations de mur en boucle tant qu'il reste assez de ressources."""
    global running, gold_accum, elixir_accum

    if not running:
        write_log("🛑 Bot arrêté avant le début de la boucle d'amélioration de mur.")
        return

    try:
        wall_cost = int(wall_cost_var.get())
    except:
        write_log("❌ Erreur : coût du mur invalide.")
        return

    write_log("🏰 Démarrage de la boucle d'amélioration des murs...")

    while running:
        if gold_accum < wall_cost and elixir_accum < wall_cost:
            write_log("⛔ Ressources insuffisantes pour continuer l'amélioration.")
            break

        process_wall_loop_debug()
        time.sleep(0.4)

    write_log("🔚 Fin de la boucle d'amélioration de mur.")


reader = easyocr.Reader(['fr', 'en'])


def process_wall_loop_debug():
    """Cherche un mur au coût demandé à l'écran (OCR), clique dessus et lance l'amélioration."""
    global running, gold_accum, elixir_accum, wall_stat

    import re

    if not running:
        write_log("🛑 Bot arrêté avant amélioration de mur.")
        return

    try:
        wall_cost = int(wall_cost_var.get())
    except Exception as e:
        write_log(f"❌ Erreur lecture wall_cost: {e}")
        return

    x_init = random.randint(881, 1006)
    y_init = random.randint(38, 69)

    safe_click(x_init, y_init)

    write_log(f"Clic initial en ({x_init},{y_init}) pour ouvrir la vue principale.")

    pyautogui.moveTo(980, 400, duration=0.2)

    time.sleep(random.uniform(0.2, 0.4))

    found = False

    wall_cost_str = str(wall_cost)

    for attempt in range(20):

        time.sleep(0.4)

        if not running:
            return

        screen = pyautogui.screenshot(region=(0, 0, 1920, 1080))

        screen_rgb = cv2.cvtColor(np.array(screen), cv2.COLOR_BGR2RGB)

        result = cv2.matchTemplate(screen_rgb, templates["wall"], cv2.TM_CCOEFF_NORMED)

        yloc, xloc = np.where(result >= 0.85)

        if len(xloc) == 0:
            write_log(f"[Attempt {attempt+1}] Aucun mur détecté → scroll")
            pyautogui.scroll(-500)
            time.sleep(0.4)
            continue

        for (px, py) in zip(xloc, yloc):

            wall_x = px + sizes["wall"][0] // 2
            wall_y = py + sizes["wall"][1] // 2

            write_log(f"[Scan] Nouveau mur détecté en ({wall_x},{wall_y})")

            try:
                ocr_x = 800
                ocr_y = int(wall_y - 15)
                ocr_w = 550
                ocr_h = 50

                cost_img = pyautogui.screenshot(region=(ocr_x, ocr_y, ocr_w, ocr_h))

                cost_np = cv2.cvtColor(np.array(cost_img), cv2.COLOR_RGB2BGR)

                gray = cv2.cvtColor(cost_np, cv2.COLOR_BGR2GRAY)

                gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

                _, thr = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

                ocr_result = reader.readtext(thr, detail=0, allowlist='0123456789 ')

                ocr_text = " ".join(ocr_result)

                digits = re.sub(r"[^\d]", "", ocr_text)

                write_log(f"→ OCR brut: '{ocr_text}' | chiffres: '{digits}' | cible: {wall_cost}")

            except Exception as e:
                write_log(f"Erreur OCR : {e}")
                continue

            matched = False

            if digits == wall_cost_str:
                matched = True
            elif wall_cost_str in digits:
                matched = True
            elif digits.endswith(wall_cost_str):
                matched = True

            if matched:
                write_log(f"🎯 Mur correct trouvé avec OCR='{digits}' -> clic")
                safe_click(wall_x, wall_y)
                found = True
                break

        if found:
            break

        pyautogui.scroll(-500)

        time.sleep(0.5)

    if not found:
        write_log("❌ Aucun mur correspondant au coût recherché après 20 tentatives.")
        return

    time.sleep(0.4)

    if gold_accum >= wall_cost and elixir_accum >= wall_cost:
        choice = random.choice(["gold", "elixir"])
    elif gold_accum >= wall_cost:
        choice = "gold"
    elif elixir_accum >= wall_cost:
        choice = "elixir"
    else:
        write_log("⛔ Aucune ressource suffisante, abandon.")
        return

    write_log(f"🧪 Ressource utilisée : {choice.upper()}")

    screen2 = pyautogui.screenshot(region=(0, 0, 1920, 1080))

    screen2_rgb = cv2.cvtColor(np.array(screen2), cv2.COLOR_BGR2RGB)

    result_up = cv2.matchTemplate(screen2_rgb, templates["up"], cv2.TM_CCOEFF_NORMED)

    yloc_up, xloc_up = np.where(result_up >= 0.85)

    buttons_raw = []

    for (px, py) in zip(xloc_up, yloc_up):
        up_x = int(px + sizes["up"][0] // 2)
        up_y = int(py + sizes["up"][1] // 2)
        buttons_raw.append((up_x, up_y))

    # on enlève les doublons trop proches les uns des autres
    buttons = []

    for bx, by in buttons_raw:
        is_new = True
        for (cx, cy) in buttons:
            if abs(bx - cx) < 50 and abs(by - cy) < 50:
                is_new = False
                break
        if is_new:
            buttons.append((bx, by))

    if len(buttons) < 2:
        write_log("❌ Impossible de trouver les deux boutons 'up'.")
        return

    buttons_sorted = sorted(buttons, key=lambda b: b[0])

    btn_gold = buttons_sorted[0]
    btn_elixir = buttons_sorted[1]

    write_log(f"📍 Bouton OR en {btn_gold} | Bouton ELIXIR en {btn_elixir}")

    if choice == "gold":
        x_btn, y_btn = btn_gold
        gold_accum -= wall_cost
    else:
        x_btn, y_btn = btn_elixir
        elixir_accum -= wall_cost

    write_log(f"➡ Clic sur le bouton {choice.upper()} sélectionné ({x_btn},{y_btn})")

    safe_click(x_btn, y_btn)

    write_log(f"🏗️ Bouton {choice.upper()} cliqué ({x_btn},{y_btn})")

    time.sleep(0.4)

    x_confirm = random.randint(1200, 1479)
    y_confirm = random.randint(890, 993)

    safe_click(x_confirm, y_confirm)

    wall_stat.set(wall_stat.get() + 1)

    write_log(f"🏰 Mur amélioré ! Total murs = {wall_stat.get()}")


def debug_wall():
    """Version de test : cherche et clique un mur au bon coût sans vérifier les ressources."""
    import re
    try:
        wall_cost = int(wall_cost_var.get())
    except Exception as e:
        write_log(f"❌ Erreur lecture wall_cost: {e}")
        return

    x_init = random.randint(881, 1006)
    y_init = random.randint(38, 69)
    safe_click(x_init, y_init)
    write_log(f"Clic initial en ({x_init},{y_init}) pour ouvrir la vue principale.")
    pyautogui.moveTo(980, 400, duration=0.2)
    time.sleep(random.uniform(0.2, 0.4))

    found = False
    for attempt in range(20):
        time.sleep(0.4)

        screen = pyautogui.screenshot(region=(0, 0, 1920, 1080))
        screen_rgb = cv2.cvtColor(np.array(screen), cv2.COLOR_BGR2RGB)
        result = cv2.matchTemplate(screen_rgb, templates["wall"], cv2.TM_CCOEFF_NORMED)
        yloc, xloc = np.where(result >= 0.85)

        if len(xloc) == 0:
            write_log(f"[Attempt {attempt+1}] Aucun mur détecté → scroll")
            pyautogui.scroll(-500)
            time.sleep(0.4)
            continue

        for (px, py) in zip(xloc, yloc):
            wall_x = px + sizes["wall"][0] // 2
            wall_y = py + sizes["wall"][1] // 2
            write_log(f"[Scan] Mur détecté en ({wall_x},{wall_y})")

            try:
                ocr_x = 800
                ocr_y = int(wall_y - 15)
                ocr_w = 550
                ocr_h = 50

                cost_img = pyautogui.screenshot(region=(ocr_x, ocr_y, ocr_w, ocr_h))
                cost_np = cv2.cvtColor(np.array(cost_img), cv2.COLOR_RGB2BGR)

                gray = cv2.cvtColor(cost_np, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                _, thr = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

                ocr_result = reader.readtext(thr, detail=0, allowlist='0123456789 ')
                ocr_text = " ".join(ocr_result)
                digits = re.sub(r"[^\d]", "", ocr_text)
                detected_cost = int(digits) if digits else None
                write_log(f"→ OCR brut: '{ocr_text}' | nettoyé: {detected_cost} | Coût cible: {wall_cost}")

            except Exception as e:
                write_log(f"Erreur OCR : {e}")
                continue

            wall_cost_str = str(wall_cost)
            detected_str = str(detected_cost) if detected_cost else ""

            if detected_cost == wall_cost or detected_str.startswith(wall_cost_str[:5]):
                write_log("🎯 Mur correct trouvé → clic")
                safe_click(wall_x, wall_y)
                found = True
                break

        if found:
            break

        pyautogui.scroll(-500)
        time.sleep(0.5)

    if found:
        write_log("✅ debug_wall terminé : mur trouvé et cliqué.")
    else:
        write_log("❌ debug_wall terminé : aucun mur correspondant trouvé après 20 tentatives.")


reader = easyocr.Reader(['en'], gpu=False)

template_paths = {
    "attack": resource_path("img/attack_button.png"),
    "find_match": resource_path("img/find_a_match.png"),
    "end": resource_path("img/end.png"),
    "return_home": resource_path("img/return_home.png"),
    "return_home1": resource_path("img/return_home1.png"),
    "star_bonus": resource_path("img/star_bonus.png"),
    "afk": resource_path("img/afk.png"),
    "wall": resource_path("img/wall.PNG"),
    "hero1": resource_path("img/hero1.png"),
    "hero2": resource_path("img/hero2.png"),
    "hero3": resource_path("img/hero3.png"),
    "hero4": resource_path("img/hero4.png"),
    "x": resource_path("img/x.png"),
    "up": resource_path("img/up.png"),
    "claim": resource_path("img/claim.png"),
    "cake": resource_path("img/cake.png"),
    "confcake": resource_path("img/confcake.png")
}

templates = {}
sizes = {}

# points de clic utilisés selon la direction du drag (haut ou bas de la base)
ATTACK_POINTS = {
    "down": [
        (387, 508), (453, 463), (505, 427), (549, 397), (615, 345),
        (684, 295), (737, 252), (779, 224), (823, 189), (861, 159), (894, 141)
    ],
    "up": [
        (809, 764), (772, 734), (736, 705), (704, 683), (674, 659),
        (635, 632), (594, 600), (559, 574), (522, 542), (484, 511),
        (454, 489), (414, 458), (375, 432), (339, 403), (286, 366),
        (252, 343), (224, 332)
    ]
}

for key, path in template_paths.items():
    img = cv2.imread(resource_path(path), cv2.IMREAD_COLOR)
    if img is None:
        write_log(f"⚠ Impossible de charger {path}")
    templates[key] = img
    if img is not None:
        sizes[key] = (img.shape[1], img.shape[0])

running = False
bot_thread = None
afk_thread = None
click_lock = threading.Lock()

slots_coords = {
    1: (335, 995), 2: (453, 995), 3: (609, 995), 4: (727, 995),
    5: (837, 995), 6: (963, 995), 7: (1075, 995), 8: (1221, 995),
    9: (1339, 995), 10: (1455, 995), 11: (1585, 995)
}

SCREEN_CENTER = (960, 540)


def wait_for_multiple_images(template1, w1, h1, template2, w2, h2, threshold=0.8, timeout=400, click_when_found=False):
    """Attend qu'une des deux images (return_home ou return_home1) apparaisse à l'écran."""
    write_log("🕓 Waiting for 'return_home' or 'return_home1' to appear...")
    start_time = time.time()

    while running and (time.time() - start_time < timeout):
        try:
            screenshot = pyautogui.screenshot()
            screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            result1 = cv2.matchTemplate(screen, template1, cv2.TM_CCOEFF_NORMED)
            _, max_val1, _, max_loc1 = cv2.minMaxLoc(result1)

            result2 = cv2.matchTemplate(screen, template2, cv2.TM_CCOEFF_NORMED)
            _, max_val2, _, max_loc2 = cv2.minMaxLoc(result2)

            if max_val1 >= threshold or max_val2 >= threshold:
                if max_val1 >= max_val2:
                    x, y = max_loc1
                    cx, cy = x + w1 // 2, y + h1 // 2
                    found = "return_home"
                    val = max_val1
                else:
                    x, y = max_loc2
                    cx, cy = x + w2 // 2, y + h2 // 2
                    found = "return_home1"
                    val = max_val2

                write_log(f"✅ Image '{found}' detected (val={val:.3f}) at ({cx},{cy})")

                if click_when_found:
                    time.sleep(0.2)
                    safe_click(cx, cy)
                    write_log(f"🖱️ Click performed on '{found}'")

                return (cx, cy)

        except Exception as e:
            write_log(f"❌ Error in wait_for_multiple_images: {e}")

        time.sleep(0.3)

    write_log("⏱️ Timeout — no image detected.")
    return None


def parse_number_string(number_string):
    """Transforme la chaîne 'Count per Slot' (ex: '3 5 2') en liste d'entiers [3, 5, 2]."""
    parts = number_string.strip().split()
    if not parts:
        raise ValueError("La chaîne Number est vide")
    return [int(p) for p in parts if p.strip().isdigit()]


def safe_click(x, y, duration=0.2, jitter=5):
    """Clique à un endroit avec un petit décalage aléatoire pour paraître plus humain."""
    with click_lock:
        rx = x + random.randint(-jitter, jitter)
        ry = y + random.randint(-jitter, jitter)
        pyautogui.moveTo(rx, ry, duration=duration)
        pyautogui.click()
    write_log(f"Clic sécurisé en ({rx},{ry}) [origine=({x},{y})]")
    time.sleep(0.1)


def center_scroll_and_drag(drag_distance=400):
    """Dézoome au centre de l'écran puis fait un drag vers le haut ou le bas (direction aléatoire)."""
    directions = ["down", "up"]
    direction = random.choice(directions)

    screen_w, screen_h = pyautogui.size()
    center_x, center_y = screen_w // 2, screen_h // 2

    pyautogui.moveTo(center_x, center_y, duration=0.15)
    for _ in range(3):
        pyautogui.scroll(-120)
        time.sleep(0.12)

    if direction == "down":
        end_x, end_y = center_x, center_y + drag_distance
    else:
        end_x, end_y = center_x, center_y - drag_distance

    try:
        pyautogui.mouseDown(center_x, center_y)
        pyautogui.moveTo(end_x, end_y, duration=0.7)
        pyautogui.mouseUp()
    except Exception as e:
        write_log(f"Erreur drag center -> {e}")

    write_log(f"🖱 Drag effectué vers : {direction.upper()}")
    return direction


def detect_and_click(template, w, h, threshold=0.8):
    """Cherche une image à l'écran en boucle et clique dessus dès qu'elle est trouvée."""
    global running
    write_log("Recherche du template visuel...")
    while running:
        try:
            screenshot = pyautogui.screenshot()
            screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                x, y = max_loc
                cx = x + w // 2
                cy = y + h // 2
                write_log(f"Template trouvé (val={max_val:.3f}) -> clic en ({cx},{cy})")
                time.sleep(random.uniform(0.1, 0.4))
                safe_click(cx, cy)
                return cx, cy
        except Exception as e:
            write_log(f"Erreur detect_and_click: {e}")
        time.sleep(0.2)
    return None


def wait_for_image_to_appear(template, w, h, threshold=0.8, timeout=400, click_when_found=False):
    """Attend qu'une image donnée apparaisse à l'écran, avec un délai maximum."""
    write_log("Attente de l'apparition de l'image...")
    start_time = time.time()
    while running and (time.time() - start_time < timeout):
        try:
            screenshot = pyautogui.screenshot()
            screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val >= threshold:
                x, y = max_loc
                cx = x + w // 2
                cy = y + h // 2
                write_log(f"Image détectée (val={max_val:.3f}) à ({cx},{cy})")
                if click_when_found:
                    time.sleep(0.2)
                    safe_click(cx, cy)
                    write_log("→ Clic effectué sur l'image détectée")
                return (cx, cy)
        except Exception as e:
            write_log(f"Erreur wait_for_image_to_appear: {e}")
        time.sleep(0.3)
    return None


def click_n_times_on_points(points_list, n, delay_between=0.05, jitter=2, is_last_slot=False, direction="down"):
    """Clique n fois en piochant dans une liste de points (ou dans un cercle si c'est le dernier slot/sort)."""
    if n <= 0:
        return

    if is_last_slot:
        screen_w, screen_h = pyautogui.size()
        center_x = screen_w // 2
        center_y = screen_h // 2
        if direction == "up":
            center_y -= 125
        radius = 250

        write_log(f"⚠ Spell slot mode -> clics dans un rayon de {radius}px autour du centre ({center_x},{center_y}) x{n}")
        for i in range(n):
            if not running:
                break

            angle = random.uniform(0, 2 * 3.14159)
            dist = random.uniform(0, radius)
            x_click = int(center_x + dist * math.cos(angle)) + random.randint(-jitter, jitter)
            y_click = int(center_y + dist * math.sin(angle)) + random.randint(-jitter, jitter)

            try:
                safe_click(x_click, y_click, 0.05)
                write_log(f"Spell Clic {i+1}/{n} -> ({x_click},{y_click}) [angle={angle:.2f}, dist={dist:.0f}]")
            except Exception as e:
                write_log(f"Erreur click spell (clic {i+1}): {e}")
            time.sleep(delay_between)
        return

    if not points_list:
        write_log("⚠️ click_n_times_on_points: liste de points vide")
        return

    write_log(f"Début {n} clics sur une liste de {len(points_list)} points")
    for i in range(n):
        if not running:
            break
        x_base, y_base = random.choice(points_list)
        x_click = x_base + random.randint(-jitter, jitter)
        y_click = y_base + random.randint(-jitter, jitter)
        try:
            safe_click(x_click, y_click, 0.05)
            write_log(f"Clic {i+1}/{n} -> ({x_click},{y_click}) [base=({x_base},{y_base})]")
        except Exception as e:
            write_log(f"Erreur click_n_times_on_points (clic {i+1}): {e}")
        time.sleep(delay_between)


import random
import time
import pyautogui


def selectionner_slots(dummy_attack_point=None, delay_between_clicks=0.05, delay_between_slots=0.5, dezoom_times=3):
    """Place les troupes slot par slot selon la config, puis lance l'activation des héros."""
    try:
        try:
            n_slots = int(safe_get_var(slots_var) or 0)
        except Exception:
            write_log("⚠️ Impossible de lire 'slots' (conversion).")
            return

        counts_raw = safe_get_var(number_var) or ""
        try:
            counts = parse_number_string(counts_raw)
        except Exception:
            write_log("⚠️ parse_number_string a échoué, utilisez 'number' au format attendu.")
            return

        if n_slots <= 0:
            write_log("⚠️ Aucun slot configuré (slots <= 0).")
            return

        if not counts:
            write_log("⚠️ Aucun nombre dans 'number' (counts vide).")
            return

        time.sleep(1)

        for _ in range(dezoom_times):
            screen_width, screen_height = pyautogui.size()
            pyautogui.moveTo(screen_width // 2, screen_height // 2)
            pyautogui.scroll(-120)
            time.sleep(0.12)

        direction = center_scroll_and_drag()
        points_for_direction = ATTACK_POINTS.get(direction, ATTACK_POINTS.get("down", []))
        write_log(f"→ Direction choisie: {direction} (points={len(points_for_direction)})")

        for i in range(1, n_slots + 1):
            if not running:
                return

            sx, sy = slots_coords.get(i, (None, None))
            if sx is None:
                write_log(f"⚠️ Coord slot {i} introuvable, skip.")
                continue

            safe_click(sx, sy)
            write_log(f"Slot {i} cliqué à ({sx}, {sy})")

            n_clicks = counts[i - 1] if (i - 1) < len(counts) else counts[-1]
            is_last = (i == n_slots)

            spell_slots_raw = safe_get_var(spell_var) or ""
            try:
                spell_slots_list = [int(x) for x in spell_slots_raw.strip().split() if x.strip().isdigit()]
            except:
                spell_slots_list = []

            is_spell = (i in spell_slots_list)

            if is_spell:
                click_n_times_on_points(points_for_direction, n_clicks, delay_between=delay_between_clicks, jitter=5, is_last_slot=True, direction=direction)
            else:
                click_n_times_on_points(points_for_direction, n_clicks, delay_between=delay_between_clicks, jitter=5, is_last_slot=False)

            time.sleep(delay_between_slots)

        write_log("→ Tous les slots ont été traités avec les nouveaux points d'attaque.")

        time.sleep(3)
        write_log("⚔️ Activation des héros en cours...")
        start_heroes_click()
        write_log("✅ Activation des héros terminée.")

    except Exception as e:
        write_log(f"Erreur selectionner_slots: {e}")


def ocr_end_screen_stats(debug=False):
    """Lit le butin (or, élixir, dark) affiché sur l'écran de fin de combat."""
    time.sleep(0.3)
    zones = [
        ((78, 128), (233, 156)),
        ((74, 170), (219, 202)),
        ((74, 217), (192, 248))
    ]

    screenshot = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    results = []

    hsv_ranges = [
        ((18, 40, 150), (45, 255, 255)),
        ((135, 30, 90), (180, 255, 255)),
        ((0, 0, 180), (179, 45, 255))
    ]

    for i, ((x1, y1), (x2, y2)) in enumerate(zones):
        crop = img[y1:y2, x1:x2].copy()

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        lower, upper = hsv_ranges[i]
        mask = cv2.inRange(hsv, lower, upper)

        if cv2.countNonZero(mask) < 100:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)

        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(mask, kernel, iterations=1)
        masked = cv2.bitwise_and(crop, crop, mask=dilated)

        gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        enhanced = cv2.bilateralFilter(enhanced, 5, 40, 40)

        inv = 255 - enhanced
        _, thr = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        h, w = thr.shape
        y_pad = max(0, int(h * 0.1))
        thr = cv2.copyMakeBorder(thr, y_pad, y_pad, 0, 0, cv2.BORDER_CONSTANT, value=255)
        resized = cv2.resize(thr, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

        try:
            text = reader.readtext(resized, detail=0, paragraph=True, allowlist='0123456789 ')
        except TypeError:
            text = reader.readtext(resized, detail=0, paragraph=True)

        joined = " ".join(text).strip()
        if debug:
            print(f"[zone{i}] OCR brut => '{joined}'")

        digits = "".join(ch for ch in joined if ch.isdigit())
        if len(digits) < 2 or len(digits) > 9:
            digits = "0"

        try:
            val = int(digits)
        except:
            val = 0

        results.append(val)

        if debug:
            print(f"[zone{i}] ✅ Nettoyé : {val}")

    return results


def ocr_return_home_zones():
    """Lit les 3 zones de texte (or, élixir, dark) de l'écran return_home."""
    global gold_stat, elixir_stat, dark_stat
    global victory_stat, defeat_stat, stars_stat, wall_stat

    zones = [
        ((743, 443), (1137, 500)),
        ((743, 520), (1137, 580)),
        ((743, 585), (1137, 652))
    ]
    results = []

    screenshot = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    _, screen = cv2.threshold(screen, 150, 255, cv2.THRESH_BINARY)

    for idx, ((x1, y1), (x2, y2)) in enumerate(zones):
        crop = screen[y1:y2, x1:x2]
        text = reader.readtext(crop, detail=0, paragraph=True)

        extracted = " ".join(text).strip()
        results.append(extracted)

        write_log(f"[OCR] Zone {idx} → '{extracted}'")

    return results


def format_time(s):
    """Convertit un nombre de secondes en chaîne HH:MM:SS."""
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def update_uptime():
    """Incrémente le compteur d'uptime chaque seconde tant que le bot tourne."""
    global uptime_seconds
    if uptime_running:
        uptime_seconds += 1
        time_stat.set(format_time(uptime_seconds))
    fenetre.after(1000, update_uptime)


def safe_get_var(tk_var):
    """Lit une variable Tkinter depuis un autre thread sans planter l'interface."""
    result = [None]
    event = threading.Event()

    def read_var():
        result[0] = tk_var.get()
        event.set()

    try:
        fenetre.after(0, read_var)
        event.wait(timeout=1)
        return result[0]
    except Exception as e:
        write_log(f"Erreur safe_get_var: {e}")
        return None


def ocr_to_int(s):
    """Convertit un texte OCR en nombre entier, renvoie 0 si le texte est vide ou invalide."""
    if not s:
        return 0
    digits = "".join(filter(str.isdigit, s))
    return int(digits) if digits else 0


def wait_for_triple_images(template1, w1, h1, template2, w2, h2, template3, w3, h3, threshold=0.8, timeout=400, click_when_found=False):
    """Attend qu'une des trois images (claim, return_home, return_home1) apparaisse à l'écran."""
    write_log("🕓 Waiting for one of the three images to appear...")
    start_time = time.time()

    while running and (time.time() - start_time < timeout):
        try:
            screenshot = pyautogui.screenshot()
            screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            result1 = cv2.matchTemplate(screen, template1, cv2.TM_CCOEFF_NORMED)
            _, max_val1, _, max_loc1 = cv2.minMaxLoc(result1)

            result2 = cv2.matchTemplate(screen, template2, cv2.TM_CCOEFF_NORMED)
            _, max_val2, _, max_loc2 = cv2.minMaxLoc(result2)

            result3 = cv2.matchTemplate(screen, template3, cv2.TM_CCOEFF_NORMED)
            _, max_val3, _, max_loc3 = cv2.minMaxLoc(result3)

            best_val = max(max_val1, max_val2, max_val3)

            if best_val >= threshold:
                if best_val == max_val1:
                    x, y, w, h = *max_loc1, w1, h1
                    name = "template1"
                elif best_val == max_val2:
                    x, y, w, h = *max_loc2, w2, h2
                    name = "template2"
                else:
                    x, y, w, h = *max_loc3, w3, h3
                    name = "template3"

                cx, cy = x + w // 2, y + h // 2
                write_log(f"✅ Image '{name}' detected (val={best_val:.3f}) at ({cx},{cy})")

                if click_when_found:
                    time.sleep(0.2)
                    safe_click(cx, cy)

                return (cx, cy, name)

        except Exception as e:
            write_log(f"❌ Error in wait_for_triple_images: {e}")

        time.sleep(0.3)

    write_log("⏱️ Timeout reached — no image detected.")
    return None


def start_bot():
    """Démarre la boucle principale du bot (attaque en boucle) dans un thread séparé."""
    global running, bot_thread
    if running:
        return
    running = True
    global uptime_running
    uptime_running = True
    log_var.set("Bot: Running...")
    write_log("Bot démarré.")
    try:
        fenetre.update_idletasks()
        debug_inputs = {
            "slots": slots_var.get(),
            "number": number_var.get(),
            "wall_cost": wall_cost_var.get(),
            "click_wall_enabled": click_wall_enabled.get(),
            "gold_min": gold_var.get(),
            "elixir_min": elixir_var.get(),
            "dark_min": dark_var.get(),
        }
        write_log("🔍 Vérification des entrées utilisateur au démarrage :")
        for k, v in debug_inputs.items():
            write_log(f"   {k} = {v}")
    except Exception as e:
        write_log(f"⚠️ Erreur lors de la lecture des variables UI : {e}")
    global afk_thread
    if afk_thread is None or not afk_thread.is_alive():
        afk_thread = threading.Thread(target=afk_checker, daemon=True)
        afk_thread.start()
        write_log("🧠 Thread AFK démarré.")

    def bot_sequence():
        """Boucle principale : lance une attaque, lit les stats, place les troupes et recommence."""
        global running, gold_accum, elixir_accum
        global gold_stat, elixir_stat, dark_stat
        global victory_stat, defeat_stat, stars_stat, wall_stat
        while running:
            try:
                x = random.randint(35, 173)
                y = random.randint(906, 1044)
                write_log(f"Clic aléatoire sur la zone 'Attack' en ({x}, {y})")
                safe_click(x, y)
                time.sleep(0.2)

                x = random.randint(100, 442)
                y = random.randint(700, 805)
                write_log(f"Clic aléatoire sur la zone 'Find a Match' en ({x}, {y})")
                safe_click(x, y)
                time.sleep(random.uniform(0.3, 0.6))

                if safe_get_var(cake_enabled):
                    screenshot = pyautogui.screenshot()
                    screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                    result = cv2.matchTemplate(screen, templates["cake"], cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    if max_val >= 0.8:
                        cx = max_loc[0] + random.randint(int(sizes["cake"][0] * 0.2), int(sizes["cake"][0] * 0.8))
                        cy = max_loc[1] + random.randint(int(sizes["cake"][1] * 0.2), int(sizes["cake"][1] * 0.8))
                        safe_click(cx, cy)
                        write_log(f"🎂 Cake cliqué en ({cx},{cy}) (confidence={max_val:.2f})")
                        time.sleep(0.4)
                        conf_coords = wait_for_image_to_appear(templates["confcake"], *sizes["confcake"], threshold=0.8, timeout=5, click_when_found=True)
                        if conf_coords:
                            write_log("✅ confcake détecté et cliqué !")
                        else:
                            write_log("⚠️ confcake non détecté après le cake.")
                    else:
                        write_log("🎂 Cake non détecté à l'écran.")

                x = random.randint(1475, 1768)
                y = random.randint(893, 941)
                write_log(f"Clic aléatoire sur le bouton de confirmation en ({x}, {y})")
                safe_click(x, y)
                time.sleep(random.uniform(0.3, 0.6))

                if not wait_for_image_to_appear(templates["end"], *sizes["end"], threshold=0.8, timeout=60):
                    write_log("Image end.png non détectée, arrêt du bot.")
                    running = False
                    uptime_running = False
                    return

                time.sleep(0.3)
                write_log("Fin de combat détectée -> OCR des stats en cours...")

                while running:
                    try:
                        end_stats = ocr_end_screen_stats()
                    except Exception as e:
                        write_log(f"Erreur OCR fin de combat: {e}")
                        end_stats = [0, 0, 0]

                    try:
                        gold_ocr, elixir_ocr, dark_ocr = [
                            int("".join(filter(str.isdigit, str(x)))) if x is not None else 0
                            for x in (end_stats + [0, 0, 0])[:3]
                        ]
                    except Exception as e:
                        write_log(f"Erreur traitement OCR: {e}")
                        gold_ocr, elixir_ocr, dark_ocr = 0, 0, 0

                    try:
                        seuil_gold = int(safe_get_var(gold_var) or 0)
                        seuil_elixir = int(safe_get_var(elixir_var) or 0)
                        seuil_dark = int(safe_get_var(dark_var) or 0)
                    except Exception as e:
                        write_log(f"Erreur parsing seuils depuis l'interface: {e}")
                        seuil_gold = seuil_elixir = seuil_dark = 0

                    write_log(
                        f"[OCR] loot => Gold={gold_ocr}, Elixir={elixir_ocr}, Dark={dark_ocr} | "
                        f"Seuils => G≥{seuil_gold}, E≥{seuil_elixir}, D≥{seuil_dark}"
                    )

                    if (gold_ocr < seuil_gold) or (elixir_ocr < seuil_elixir) or (dark_ocr < seuil_dark):
                        write_log("⚠ Ressources insuffisantes → clic de relance.")
                        bx = random.randint(1667, 1891)
                        by = random.randint(773, 867)
                        safe_click(bx, by)
                        write_log(f"Clic relance effectué en ({bx},{by})")
                        time.sleep(0.3)

                        if not wait_for_image_to_appear(templates["end"], *sizes["end"], threshold=0.8, timeout=60):
                            write_log("⚠ end.png non revenu après clic de relance → arrêt.")
                            running = False
                            uptime_running = False
                            return

                        time.sleep(0.3)
                        continue
                    else:
                        write_log("✅ Ressources suffisantes → passage à l'attaque.")
                        break
                selectionner_slots()
                write_log("Attente du bouton return_home.png...")
                if treasure_event_enabled.get():
                    write_log("🎁 Treasure Event activé → attente de claim.png, return_home ou return_home1")
                    coords = wait_for_triple_images(
                        templates["claim"], *sizes["claim"],
                        templates["return_home"], *sizes["return_home"],
                        templates["return_home1"], *sizes["return_home1"],
                        threshold=0.8, timeout=250, click_when_found=False
                    )
                    treasure_claimed = coords is not None and coords[2] == "template1"
                else:
                    coords = wait_for_multiple_images(
                        templates["return_home"], *sizes["return_home"],
                        templates["return_home1"], *sizes["return_home1"],
                        threshold=0.8, timeout=250, click_when_found=False
                    )
                    treasure_claimed = False

                time.sleep(0.3)

                if coords:
                    time.sleep(0.3)
                    infos = ocr_return_home_zones()
                    write_log(f"[OCR RAW] → {infos}")

                    gold = ocr_to_int(infos[0] if len(infos) > 0 else "")
                    elixir = ocr_to_int(infos[1] if len(infos) > 1 else "")
                    dark = ocr_to_int(infos[2] if len(infos) > 2 else "")

                    write_log(f"[OCR PARSED] Gold={gold} | Elixir={elixir} | Dark={dark}")
                    write_log(f"[UI BEFORE] Gold={gold_stat.get()} | Elixir={elixir_stat.get()} | Dark={dark_stat.get()}")

                    fenetre.after(0, lambda v=gold: gold_stat.set(gold_stat.get() + v))
                    fenetre.after(0, lambda v=elixir: elixir_stat.set(elixir_stat.get() + v))
                    fenetre.after(0, lambda v=dark: dark_stat.set(dark_stat.get() + v))

                    fenetre.after(150, lambda: write_log(
                        f"[UI AFTER] Gold={gold_stat.get()} | Elixir={elixir_stat.get()} | Dark={dark_stat.get()}"
                    ))

                    gold_accum += gold
                    elixir_accum += elixir
                    write_log(f"[ACCUM] → Gold={gold_accum}, Elixir={elixir_accum}")

                    time.sleep(0.4)

                    check_white_dominance()
                    time.sleep(0.4)

                    rx = random.randint(843, 1072)
                    ry = random.randint(880, 969)
                    safe_click(rx, ry)
                    write_log(f"→ Bouton return_home cliqué en ({rx},{ry})")

                    if treasure_event_enabled.get() and treasure_claimed:
                        write_log("🎁 Treasure Event → séquence de clics")
                        time.sleep(0.5)

                        for i in range(4):
                            cx = random.randint(880, 1030)
                            cy = random.randint(900, 950)
                            safe_click(cx, cy)
                            write_log(f"🎁 Clic treasure {i+1}/4 en ({cx},{cy})")
                            time.sleep(random.uniform(0.2, 0.5))

                        time.sleep(random.uniform(0.5, 0.7))

                        fx = random.randint(830, 1094)
                        fy = random.randint(860, 935)
                        safe_click(fx, fy)
                        write_log(f"🎁 Clic final treasure en ({fx},{fy})")

                    bonus_coords = wait_for_image_to_appear(
                        templates["star_bonus"], *sizes["star_bonus"],
                        threshold=0.8, timeout=5, click_when_found=True
                    )
                    if bonus_coords:
                        write_log("→ Bouton star_bonus détecté et cliqué !")

                    if click_wall_enabled.get():
                        wall_cost = int(wall_cost_var.get()) if wall_cost_var.get() else 0
                        if gold_accum >= wall_cost or elixir_accum >= wall_cost:
                            write_log(f"💪 Assez de ressources pour upgrade mur (coût={wall_cost}) → lancement process_wall_loop()")
                            time.sleep(1.5)
                            process_wall_loop_auto()
                        else:
                            write_log(f"⛔ Pas assez de ressources pour upgrade mur (Gold={gold_accum}, Elixir={elixir_accum}, Coût={wall_cost}) → skip")
                    send_discord_stats()

                else:
                    write_log("⚠ Bouton return_home non détecté (timeout).")

            except Exception as e:
                write_log(f"Erreur dans bot_sequence: {e}")

    bot_thread = threading.Thread(target=bot_sequence, daemon=True)
    bot_thread.start()


def stop_bot():
    """Arrête le bot proprement."""
    global running
    running = False
    log_var.set("Bot: Stopped")
    write_log("Bot stoppé.")
    global uptime_running
    uptime_running = False


def afk_checker():
    """Vérifie régulièrement si le popup AFK est apparu et le ferme automatiquement."""
    global running, bot_thread
    while True:
        if running:
            coords = wait_for_image_to_appear(templates["afk"], *sizes["afk"], threshold=0.8, timeout=0.2, click_when_found=False)
            if coords:
                write_log("AFK détecté ! Clic...")
                safe_click(*coords)
                time.sleep(10)
                if bot_thread is not None and not bot_thread.is_alive():
                    start_bot()
        time.sleep(0.3)


if __name__ == "__main__":
    show_license_window()
    sys.exit(0)