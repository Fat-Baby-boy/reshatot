import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 65432
MAX_CLIENTS = 20  

clients = {}  # { "name": conn }
server_running = True

def admin_console(server_socket):
    global server_running
    while server_running:
        try:
            cmd = input()
            if cmd == "end-server":
                print("Shutting down server...")
                server_running = False
                for name, conn in clients.items():
                    try:
                        conn.send("SERVER_SHUTDOWN".encode('utf-8'))
                        conn.close()
                    except:
                        pass
                server_socket.close()
                sys.exit()
        except:
            break

def handle_client(conn, addr):
    print(f"New connection attempt from {addr}")
    name = None
    
    try:
        # בדיקת עומס מיידית
        if len(clients) >= MAX_CLIENTS:
            print(f"[REJECT] Server full ({len(clients)}/{MAX_CLIENTS}). Rejecting connection.")
            conn.send("ABORT:Server is full".encode('utf-8'))
            conn.close()
            return
        
        conn.send("PROMPT:Enter Name".encode('utf-8'))
        
        raw_name = conn.recv(1024).decode('utf-8')
        name = raw_name.strip()
        
        # בדיקת כפילות שמות
        for registered_name in clients.keys():
            if registered_name.lower() == name.lower():
                conn.send("ABORT:Name taken".encode('utf-8'))
                conn.close()
                return

        clients[name] = conn
        print(f"User '{name}' registered. Online: {len(clients)}/{MAX_CLIENTS}")
        conn.send(f"Welcome {name}".encode('utf-8'))

        while server_running:
            try:
                data = conn.recv(1024)
            except:
                break
            if not data: break
            
            message = data.decode('utf-8')
            parts = message.split(':', 2)
            command = parts[0]

            if command == "LIST_USERS":
                all_users = ", ".join(clients.keys())
                conn.send(f"SYSTEM:Online users:{all_users}".encode('utf-8'))

            elif command == "CHAT":
                if len(parts) < 3: continue
                target = parts[1]
                content = parts[2]

                if target in clients:
                    clients[target].send(f"CHAT:{name}:{content}".encode('utf-8'))
                else:
                    conn.send(f"SYSTEM:User '{target}' is offline.".encode('utf-8'))

    except Exception as e:
        print(f"Error with user {name}: {e}")
    
    finally:
        if name and name in clients:
            del clients[name]
            print(f"[LOG] User '{name}' disconnected. Online: {len(clients)}/{MAX_CLIENTS}")
        conn.close()

# Main setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print(f"Server is listening (Max {MAX_CLIENTS} clients)...")
threading.Thread(target=admin_console, args=(server,), daemon=True).start()

while server_running:
    try:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except:
        break