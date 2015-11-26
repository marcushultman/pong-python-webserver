from threading import Thread
import tornado.web
import tornado.websocket
import tornado.ioloop
import json

server_title = None

slots = None

global_callback = dict()
client_callback = dict()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    # Accept all connections
    def check_origin(self, origin):
        return True
    
    # A client connected
    def open(self):
        if len(slots):
            self.client_id = slots.pop()
            print('Client connected [{0}]'.format(self.client_id))
            data = { 'server_title': server_title, 'client_id': self.client_id }
            self.write_message(json.dumps(data))
            return
        self.close(code=4001, reason='Server is full!')
        
    
    # A client sent a message
    def on_message(self, message):
        try:
            data = json.loads(message)
            print('Message [{0}] :{1}'.format(self.client_id, data))
            
            action_id = data['action']

            if action_id in global_callback:
                global_callback[action_id](data.get('data'))
            elif action_id in client_callback:
                client_callback[action_id][self.client_id](data.get('data'))
        except:
            pass
    
    def on_close(self):
        if hasattr(self, 'client_id'):
            slots.add(self.client_id)
            print('Client disconnected [{0}]'.format(self.client_id))


class HttpSocketServer():

    PORT = 8080

    def __init__(self, num_clients, title=None):
        global slots
        slots = set(range(num_clients))
        global server_title
        server_title = title

    def start(self, port=None):
        if port is None:
            port = HttpSocketServer.PORT
        Thread(target=self._run_server, args=(port,)).start()
        print('Running webserver on port:', port)

    def stop(self):
        tornado.ioloop.IOLoop.instance().stop()

    def _run_server(self, *args):
        application = tornado.web.Application([
            (r'/', MainHandler),
            (r'/socket', WebSocketHandler),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': './static/'})
        ])
        application.listen(args[0])
        tornado.ioloop.IOLoop.instance().start()
        tornado.ioloop.IOLoop.instance().close(True)
        print('Webserver stopped.')

    def set_callback(self, action_id, action_callback, client=None):
        if client is not None:
            client_callback.setdefault(action_id, dict())[client] = action_callback
        else:
            global_callback[action_id] = action_callback

# debug
if __name__ == "__main__":
    server = HttpSocketServer(1)
    server.start()
    try:
        while 1:
            pass
    except KeyboardInterrupt:
        pass
    server.stop()
