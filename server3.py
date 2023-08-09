import socket
import threading

HOST = '10.217.23.212'
PORT = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print("Server mendengarkan pada {}:{}".format(HOST, PORT))

# Dictionary untuk menyimpan nama pengguna, nama grup, dan soket klien
clients = {}
lock = threading.Lock()


def handle_client(client_socket, client_address):
    try:
        # Minta nama pengguna dan nama grup dari klien
        client_socket.send("Masukkan nama pengguna Anda: ".encode("utf-8"))
        username = client_socket.recv(1024).decode("utf-8").strip()

        # Minta nama grup dari klien
        client_socket.send("Masukkan nama grup Anda: ".encode("utf-8"))
        groupname = client_socket.recv(1024).decode("utf-8").strip()

        print("Pengguna {} dari grup {} terhubung dari {}:{}".format(username, groupname, client_address[0], client_address[1]))

        with lock:
            clients[username] = (client_socket, groupname)  # Simpan nama pengguna dan nama grup sebagai tuple

        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            # Periksa apakah server ingin menutup
            if data.decode("utf-8").lower() == "exit":
                raise KeyboardInterrupt  # Timbulkan pengecualian untuk menutup server
            elif data.decode("utf-8").startswith("$"):
                # Pesan grup: teruskan pesan ke semua klien dalam grup yang sama
                parts = data.decode("utf-8").split(" ", 1)
                recipient_group = parts[0][1:]
                message = parts[1]
                if recipient_group == groupname:
                    message = "[Grup {} dari {}] {}".format(groupname, username, message)
                    with lock:
                        for client, client_group in clients.values():
                            if client_group == groupname:
                                client.send(message.encode("utf-8"))
                else:
                    # Siarkan ke semua klien dari grup yang berbeda
                    message = "[Pesan Siaran Grup {} dari {}] {}".format(groupname, username, message)
                    with lock:
                        for client, client_group in clients.values():
                            if client_group != groupname:
                                client.send(message.encode("utf-8"))
            elif data.decode("utf-8").startswith("@"):
                # Unicast: teruskan pesan ke pengguna yang ditentukan
                parts = data.decode("utf-8").split(" ", 1)
                recipient = parts[0][1:]
                message = parts[1]
                if recipient in clients:
                    recipient_socket, _ = clients[recipient]
                    message = "[Unicast dari {}] {}".format(username, message)
                    recipient_socket.send(message.encode("utf-8"))
            elif data.decode("utf-8").startswith("*Broadcast"):
                # Siarkan ke semua klien dari grup yang berbeda
                message = "[Pesan Siaran dari {}] {}".format(username, data.decode("utf-8")[10:])  # Hapus "*Broadcast" dari pesan
                with lock:
                    for client, client_group in clients.values():
                        client.send(message.encode("utf-8"))
            elif data.decode("utf-8").startswith("!file"):
                # Menerima file dari klien lain
                parts = data.decode("utf-8").split(" ", 2)
                file_type = parts[1]
                file_size = int(parts[2])
                filename = f"{username}.{file_type}"
                with open(filename, "wb") as file:
                    remaining_bytes = file_size
                    while remaining_bytes > 0:
                        file_data = client_socket.recv(min(remaining_bytes, 1024))
                        if not file_data:
                            break
                        file.write(file_data)
                        remaining_bytes -= len(file_data)
                print(f"Menerima file {filename} dari {username}")
                # Siarkan informasi file diterima ke semua klien
                message = f"!file_received {username} {filename}"
                with lock:
                    for client, client_group in clients.values():
                        client.send(message.encode("utf-8"))
                # Send file back to the sender (client) as well
                client_socket.send(message.encode("utf-8"))
            else:
                pass

    except KeyboardInterrupt:
        print("Server ditutup...")
    except:
        pass
    finally:
        # Jika koneksi terputus, tutup soket klien dan hapus dari daftar
        with lock:
            if username in clients:
                del clients[username]
        client_socket.close()


def main():
    try:
        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print("Menutup semua koneksi...")
        with lock:
            for client, _ in clients.values():
                client.close()

    server_socket.close()
    print("Server ditutup.")


if __name__ == "__main__":
    main()
