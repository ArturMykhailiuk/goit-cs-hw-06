from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import urllib.parse
import mimetypes
import pathlib
import datetime
import multiprocessing
import socketserver
from pymongo import MongoClient


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/contact':
            self.send_html_file('contact.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 5000))
        client_socket.sendall(data)
        print('Дані надіслано')
        client_socket.close()
        
        self.send_response(302)
        self.send_header('Location', '/message.html')
        self.end_headers()
    

def run_http():
    http = socketserver.TCPServer(('', 3000), HttpHandler)
    try:
        print('HTTP-сервер стартував і очікує на підключення...')
        http.serve_forever()     
    except KeyboardInterrupt:
        http.server_close()
        
def run_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5000))
    server_socket.listen(1)
    print('Socket-сервер стартував і очікує на підключення...')
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f'Підключення від Socket-клієнта {addr}')
        
        try:
        # Отримання даних форми
            data = client_socket.recv(1024).decode()
            data_parse = urllib.parse.unquote_plus(data)
            data_dict = {"date":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}
            data_dict.update( {key: value for key, value in [el.split('=') for el in data_parse.split('&')]})
            print(f'Дані отримано: {data_dict}')
            work_with_mongo(data_dict)
        except KeyboardInterrupt:
            client_socket.close()

def work_with_mongo(data_dict):
    client = MongoClient('localhost', 27017)
    db = client['MYBASE']

    # Отримуємо колекцію 'users'
    collection = db['users187']

    # Вставляємо новий документ
    user = {
        'name': 'John Doe',
        'email': 'johndoe@example.com',
        'age': 30
    }
    result = collection.insert_one(user)
    print('Inserted document with ID:', result.inserted_id)

if __name__ == '__main__':
    # Запуск процесу для HTTP-серверу
    http_process = multiprocessing.Process(target=run_http)
    http_process.start()
    
    # Запуск процесу для Socket-серверу 
    socket_process = multiprocessing.Process(target=run_socket)
    socket_process.start()
    
    try:
        # Очікування завершення процесів
        http_process.join()
        socket_process.join()
    except KeyboardInterrupt:
        http_process.terminate()
        socket_process.terminate()
        print("HTTP та Socket процеси завершено після натискання Ctrl+C.")