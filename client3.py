import socket
import threading
import os

HOST = '10.217.23.212'
PORT = 12345

def terima_pesan(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            print(data.decode("utf-8"))
        except:
            break

def terima_berkas(client_socket, nama_berkas):
    try:
        with open(nama_berkas, "wb") as berkas:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                berkas.write(data)
        
        print(f"Berkas {nama_berkas} berhasil diterima dan disimpan di direktori client.")
    except Exception as e:
        print(f"Terjadi kesalahan dalam menerima berkas: {e}")

def kirim_berkas(client_socket, path_berkas):
    tipe_berkas = path_berkas.split(".")[-1].lower()
    ukuran_berkas = os.path.getsize(path_berkas)
    pesan = f"!file {tipe_berkas} {ukuran_berkas}"
    client_socket.send(pesan.encode("utf-8"))

    with open(path_berkas, "rb") as berkas:
        while True:
            data = berkas.read(1024)
            if not data:
                break
            client_socket.send(data)

    print(f"Berkas {path_berkas} berhasil dikirimkan.")

def terima_file(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break

            if data.decode("utf-8").startswith("!file_received"):
                parts = data.decode("utf-8").split(" ", 2)
                pengirim = parts[1]
                filename = parts[2]
                terima_berkas(client_socket, filename)
            else:
                print(data.decode("utf-8"))
        except:
            break

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    # Masukkan nama pengguna dari klien
    nama_pengguna = input("Masukkan nama pengguna Anda: ")
    client_socket.send(nama_pengguna.encode("utf-8"))

    # Masukkan nama grup dari klien
    nama_grup = input("Masukkan nama grup Anda: ")
    client_socket.send(nama_grup.encode("utf-8"))

    thread_terima = threading.Thread(target=terima_pesan, args=(client_socket,))
    thread_terima.start()

    thread_terima_file = threading.Thread(target=terima_file, args=(client_socket,))
    thread_terima_file.start()

    while True:
        pesan = input()

        if pesan == "exit":
            client_socket.send(pesan.encode("utf-8"))
            break
        elif pesan.startswith("@"):
            bagian = pesan.split(" ", 1)
            penerima = bagian[0][1:]
            pesan = bagian[1]
            pesan_lengkap = "@{} {}".format(penerima, pesan)
        elif pesan.startswith("$"):
            bagian = pesan.split(" ", 1)
            grup = bagian[0][1:]
            pesan = bagian[1]
            pesan_lengkap = "${} {}".format(grup, pesan)
        elif pesan.startswith("!file"):
            path_berkas = pesan.split(" ")[1]
            kirim_berkas(client_socket, path_berkas)
            continue
        else:
            pesan_lengkap = pesan

        client_socket.send(pesan_lengkap.encode("utf-8"))

    client_socket.close()

if __name__ == "__main__":
    main()