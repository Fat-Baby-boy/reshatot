import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, Checkbutton, BooleanVar
import sys
import subprocess
import random

# --- הגדרות עיצוב ---
BG_COLOR = "#121212"
MSG_LIST_BG = "#1E1E1E"
MY_MSG_COLOR = "#005C4B"
OTHER_MSG_COLOR = "#202C33"
TEXT_COLOR = "#E9EDEF"
BTN_COLOR = "#00A884"
NOTIF_COLOR = "#007AFF"
FONT_MAIN = ("Helvetica", 12)
FONT_BOLD = ("Helvetica", 12, "bold")

HOST = '127.0.0.1'
PORT = 65432

# ==============================================================================
#  EASTER EGG CODE
# ==============================================================================
class AliceBot:
    RESPONSES = {
        "hello": ["Hi there!", "Hello!", "Greetings, human.", "Hey!"],
        "hi": ["Hello!", "Hi!", "Hey there."],
        "how are you": ["I'm just a bot, but I'm functioning perfectly.", "My circuits are running smooth.", "I am code, I have no feelings, but thanks for asking!"],
        "what are you": ["I am a Python script disguised as a human named Alice.", "I am an Easter Egg in this code."],
        "bye": ["Goodbye!", "See ya!", "Terminating conversation... just kidding, bye!"],
        "lol": ["Haha!", "That is funny.", "Lol indeed."],
        "time": ["Time is an illusion for a computer.", "Check your clock, I'm busy calculating."],
    }

    @staticmethod
    def get_reply(message):
        msg_lower = message.lower()
        for key in AliceBot.RESPONSES:
            if key in msg_lower:
                return random.choice(AliceBot.RESPONSES[key])
        return random.choice(["I see.", "Interesting...", "Tell me more.", "Can you explain that?"])
# ==============================================================================

class ChatClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("360x640")
        self.root.title("ChatApp")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(True, True)

        self.client_socket = None
        self.username = ""
        self.current_chat_partner = None 
        self.chat_history = {} 
        self.running = True
        self.auto_refresh_var = BooleanVar(value=True) 

        self.build_login_screen()
        
        self.notification_label = tk.Label(self.root, text="", bg=NOTIF_COLOR, fg="white", 
                                           font=("Helvetica", 10, "bold"), padx=10, pady=8,
                                           bd=2, relief="raised")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def start_auto_refresh(self):
        if self.running and self.client_socket and self.auto_refresh_var.get():
            try:
                self.client_socket.send("LIST_USERS".encode('utf-8'))
            except:
                pass
            self.root.after(3000, self.start_auto_refresh)

    def manual_refresh(self):
        if self.client_socket:
            self.client_socket.send("LIST_USERS".encode('utf-8'))
            self.show_notification("Refreshing list...")

    def toggle_auto_refresh(self):
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
            self.show_notification("Auto-refresh ON")
        else:
            self.show_notification("Auto-refresh OFF")

    def show_notification(self, text):
        self.notification_label.config(text=text)
        self.notification_label.lift()
        self.notification_label.place(relx=0.5, y=20, anchor="n", width=340)
        
        if hasattr(self, '_notif_timer'):
            self.root.after_cancel(self._notif_timer)
        self._notif_timer = self.root.after(3500, lambda: self.notification_label.place_forget())

    def clear_screen(self):
        for widget in self.root.winfo_children():
            if widget != self.notification_label:
                widget.destroy()

    def build_login_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Welcome", font=("Helvetica", 24, "bold"), bg=BG_COLOR, fg=BTN_COLOR).pack(pady=50)
        
        tk.Label(self.root, text="Enter your name:", bg=BG_COLOR, fg="white").pack(pady=5)
        self.entry_name = tk.Entry(self.root, font=FONT_MAIN, bg=MSG_LIST_BG, fg="white", insertbackground="white")
        self.entry_name.pack(pady=10, ipadx=50, ipady=5)
        self.entry_name.bind('<Return>', lambda event: self.connect_to_server())

        tk.Button(self.root, text="Connect", font=FONT_BOLD, bg=BTN_COLOR, fg="white", command=self.connect_to_server, bd=0).pack(pady=20, ipadx=40, ipady=10)
        tk.Button(self.root, text="+ Open New Client", font=("Helvetica", 10), bg="#333", fg="white", command=self.spawn_new_client, bd=0).pack(side=tk.BOTTOM, pady=20)

    def spawn_new_client(self):
        subprocess.Popen([sys.executable, __file__])

    def connect_to_server(self):
        name = self.entry_name.get().strip()
        if not name: return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            
            initial_msg = self.client_socket.recv(1024).decode('utf-8')
            
            if initial_msg.startswith("ABORT:"):
                reason = initial_msg.split(":")[1]
                messagebox.showerror("Access Denied", f"Connection Rejected: {reason}")
                self.root.destroy()
                sys.exit()
            
            self.client_socket.send(name.encode('utf-8'))
            
            self.username = name
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            self.show_contacts_screen()
            self.start_auto_refresh()

        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {e}")

    def show_contacts_screen(self):
        self.current_chat_partner = None 
        self.clear_screen()
        
        header = tk.Frame(self.root, bg=MSG_LIST_BG)
        header.pack(fill=tk.X, ipady=10)
        tk.Label(header, text=f"Hello, {self.username}", font=FONT_BOLD, bg=MSG_LIST_BG, fg="white").pack(side=tk.TOP, pady=5)

        controls_frame = tk.Frame(header, bg=MSG_LIST_BG)
        controls_frame.pack(side=tk.TOP, fill=tk.X)

        cb = tk.Checkbutton(controls_frame, text="Auto-Refresh", variable=self.auto_refresh_var, 
                            bg=MSG_LIST_BG, fg="white", selectcolor="black", activebackground=MSG_LIST_BG,
                            command=self.toggle_auto_refresh)
        cb.pack(side=tk.LEFT, padx=20)

        tk.Button(controls_frame, text="↻ Manual Refresh", bg="#333", fg="white", bd=0, font=("Helvetica", 9),
                  command=self.manual_refresh).pack(side=tk.RIGHT, padx=20)

        self.contacts_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.contacts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- תוספת: רענון אוטומטי במעבר למסך זה ---
        if self.client_socket:
             self.client_socket.send("LIST_USERS".encode('utf-8'))
        # ------------------------------------------

    def update_contact_list(self, users_str):
        if self.current_chat_partner is not None: return 

        for widget in self.contacts_frame.winfo_children(): widget.destroy()
        
        users = [u.strip() for u in users_str.split(",")]
        found = False
        for user in users:
            if user.lower() != self.username.lower() and user:
                found = True
                btn = tk.Button(self.contacts_frame, text=f"👤  {user}", font=FONT_MAIN, bg=MSG_LIST_BG, fg="white", anchor="w", bd=0, padx=20,
                                command=lambda u=user: self.open_chat_with(u))
                btn.pack(fill=tk.X, pady=2, ipady=10)
        
        if not found:
            tk.Label(self.contacts_frame, text="No users online.", bg=BG_COLOR, fg="gray").pack(pady=20)

    def open_chat_with(self, partner_name):
        self.current_chat_partner = partner_name
        self.clear_screen()
        
        header = tk.Frame(self.root, bg=MSG_LIST_BG, height=60)
        header.pack(fill=tk.X)
        tk.Button(header, text="< Back", bg=MSG_LIST_BG, fg="#007AFF", bd=0, font=FONT_BOLD, command=self.show_contacts_screen).pack(side=tk.LEFT, padx=10)
        tk.Label(header, text=partner_name, font=FONT_BOLD, bg=MSG_LIST_BG, fg="white").pack(side=tk.LEFT, padx=10)

        self.chat_area = scrolledtext.ScrolledText(self.root, bg=BG_COLOR, fg=TEXT_COLOR, font=FONT_MAIN, state='disabled')
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_area.tag_config('me', foreground=TEXT_COLOR, background=MY_MSG_COLOR, justify='right', lmargin1=50)
        self.chat_area.tag_config('partner', foreground=TEXT_COLOR, background=OTHER_MSG_COLOR, justify='left', rmargin=50)

        if partner_name in self.chat_history:
            for sender, msg in self.chat_history[partner_name]:
                tag = 'me' if sender == 'Me' else 'partner'
                self.append_message_to_ui(msg, tag)

        input_frame = tk.Frame(self.root, bg=MSG_LIST_BG)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.msg_entry = tk.Entry(input_frame, bg="#2A3942", fg="white", font=FONT_MAIN, bd=0, insertbackground="white")
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10, ipady=5)
        self.msg_entry.bind('<Return>', lambda event: self.send_message())
        tk.Button(input_frame, text="➤", bg=BTN_COLOR, fg="white", font=FONT_BOLD, bd=0, command=self.send_message).pack(side=tk.RIGHT, padx=10)

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if msg and self.current_chat_partner:
            self.client_socket.send(f"CHAT:{self.current_chat_partner}:{msg}".encode('utf-8'))
            self.save_to_history(self.current_chat_partner, "Me", msg)
            self.append_message_to_ui(msg, 'me')
            self.msg_entry.delete(0, tk.END)

    def save_to_history(self, partner, sender, msg):
        if partner not in self.chat_history:
            self.chat_history[partner] = []
        self.chat_history[partner].append((sender, msg))

    def append_message_to_ui(self, message, tag):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"\n {message} \n", tag)
        self.chat_area.insert(tk.END, " ", "small_space") 
        self.chat_area.yview(tk.END)
        self.chat_area.config(state='disabled')

    def on_close(self):
        self.running = False
        try: self.client_socket.close()
        except: pass
        self.root.destroy()
        sys.exit()

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data: break
                
                message = data.decode('utf-8')

                if message.startswith("SYSTEM:Online users:"):
                    users_str = message.split(":", 2)[2]
                    if self.current_chat_partner is None:
                        self.root.after(0, self.update_contact_list, users_str)

                elif message.startswith("CHAT:"):
                    parts = message.split(":", 2)
                    sender = parts[1]
                    content = parts[2]

                    self.save_to_history(sender, sender, content)

                    if self.username.lower() == "alice" and sender.lower() != "alice":
                        bot_response = AliceBot.get_reply(content)
                        def send_bot_reply():
                            self.client_socket.send(f"CHAT:{sender}:{bot_response}".encode('utf-8'))
                            self.save_to_history(sender, "Me", bot_response)
                            if self.current_chat_partner == sender:
                                self.append_message_to_ui(bot_response, 'me')
                        self.root.after(1500, send_bot_reply)

                    if self.current_chat_partner == sender:
                        self.root.after(0, self.append_message_to_ui, content, 'partner')
                    else:
                        preview = content[:25] + "..." if len(content) > 25 else content
                        self.root.after(0, self.show_notification, f"{sender}: {preview}")

                elif message.startswith("SYSTEM:"):
                    clean = message.split("SYSTEM:")[1]
                    if "Online users" not in clean:
                         self.root.after(0, self.show_notification, clean)
                    
            except Exception as e:
                print("Error:", e)
                break

if __name__ == "__main__":
    ChatClientGUI()