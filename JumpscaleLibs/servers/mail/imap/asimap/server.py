from .auth import AUTH_SYSTEMS
from .client import PreAuthenticated, Authenticated
from .parse import IMAPClientCommand
from .user_server import IMAPUserServer
from . import parse


from gevent.server import StreamServer

import re
import traceback

sessions = {}


RE_LITERAL_STRING_START = re.compile(r'\{(\d+)\+?\}$')

class Server:
    def __init__(self, address, port, models):
        self.models = models
        self.address = address
        self.port = port
        self.server = StreamServer((self.address, self.port), self.handle)

    def handle_msg(self, socket, msg, client_handler):
        try:
            imap_cmd = IMAPClientCommand(msg)
            imap_cmd.parse()

        except parse.BadCommand as e:
            if imap_cmd.tag is not None:
                if imap_cmd.tag == "DONE":
                    client_handler.do_done(None)
                    return
                msg = b"%s BAD %s\r\n" % (imap_cmd.tag.encode(), str(e).encode("utf8"))
            else:
                msg = b"* BAD %s\r\n" % (msg).encode()
            socket.send(b"%d\n" % len(msg))
            socket.send(msg)
            print(f"Something went wrong: {msg}")
            return
        try:
            client_handler.command(imap_cmd)
        except Exception as e:
            tb = traceback.format_exc()
            msg = f"Exception handling IMAP command {imap_cmd.command}({imap_cmd.tag}) for {e}:\n{tb}"
            print(msg)

        if client_handler.state == "logged_out":
            if socket is not None:
                socket.close()

    def handle(self, socket, address):
        #socket.setblocking(True)
        terminator = "\r\n"
        file = socket.makefile("rw", newline=terminator)
        class Client:
            def __init__(self, socket):
                self.socket = socket

            def push(self, data):
                print(f"S: {data.splitlines()[0].strip()}")
                try:
                    return self.socket.send(data.encode())
                except:
                    if client_handler.state == "logged_out":
                        return
                    raise

            @property
            def rem_addr(self):
                return address[0]

            @property
            def port(self):
                return address[1]

            def __getattr__(self, item):
                return getattr(self.socket, item)

        c = Client(socket)

        reading_string_literal = True
        client_handler = PreAuthenticated(c, AUTH_SYSTEMS['simple_auth'], self.models)
        socket.send(b'* OK [IMAP4REV1 IDLE ID SELECT UNSELECT UIDPLUS LITERAL+ CHILDREN]\r\n')


        while socket is not None:
            if reading_string_literal:
                reading_string_literal = False
                continue

            # data = socket.recv(1024).decode()
            data = file.readline()

            if not data:
                try:
                    socket.send(b"* BAD We do not accept empty messages.\r\n")
                except BrokenPipeError:
                    socket = None
                continue

            print(f"C: {data.strip()}")
            m = RE_LITERAL_STRING_START.search(data.strip())
            if m:
                neededdata = int(m.group(1)) + 2
                reading_string_literal = True
                #file.writelines(["+ Ready for more input"])
                data += file.read(neededdata)
            if not data.endswith('\r\n'):
                data = data + '\r\n'
            self.handle_msg(socket, data, client_handler)
            if isinstance(client_handler, PreAuthenticated) and client_handler.state == 'authenticated':
                client_handler = Authenticated(c, IMAPUserServer(client_handler.user.imap_username, self.models), self.models)
            elif client_handler.state == "logged_out":
                socket.close()
                socket = None
        # Handle client disconnection
        print('Client disconnected')
        client_handler.state = "non_authenticated"
        client_handler.user = None
        if socket:
            socket.close()

    def start(self):
        self.server.serve_forever()

