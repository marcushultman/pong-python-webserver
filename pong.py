from tkinter import *
from threading import *
import random

from httpsocketserver import HttpSocketServer

# Init

app = Tk()
app.config(bg='black')

app.overrideredirect(True)
app.width, app.height = app.winfo_screenwidth(), app.winfo_screenheight()
#app.width, app.height = 800, 600
app.geometry("{0}x{1}+0+0".format(app.width, app.height))
background = Frame(app, bg=app.cget('bg'))
background.pack(fill=BOTH, expand=1)

# Middle line
line_size = 0.01
line = Canvas(app, bg=app.cget('bg'), highlightthickness=0)
line.place(relx=0.5, rely=0, relwidth=line_size, relheight=1, anchor=N)
line_id = line.create_line(0, 0, 0, 0, fill="white", dash=(1, 1))

def clamp(value, _min, _max):
    if (value < _min):
        return _min
    if (value > _max):
        return _max
    return value

class Boundry():
    def __init__(self, _min=0, _max=1):
        self.min, self.max = _min, _max

class Player(Frame):
    DEFAULT_WIDTH = 0.02
    DEFAULT_HEIGHT = 0.25
    
    def __init__(self, master, player, height=DEFAULT_HEIGHT, *args, **kwargs):
        Frame.__init__(self, master, *args, **kwargs)
        self.config(bg='white')
        self.place(relx=player, anchor=(E if player else W))
        self.position = 0.5
        self.set_height(height)

        # Score label
        self._score = IntVar(value=0)
        Label(app, textvariable=self._score,
              bg=app.cget('bg'),
              fg='white',
              font=("System", 42)).place(relx=(0.54 if player else 0.46),
                   rely=0.05,
                   anchor=N)

    def set_height(self, height, *args, **kwargs):
        self.height = height
        _min = height / 2.0
        self.boundry = Boundry(_min, 1.0 - _min)
        self.place(relwidth=Player.DEFAULT_WIDTH, relheight=height)
        self.update(self.position)
    
    def update(self, position, *args, **kwargs):
        self.position = clamp(position, self.boundry.min, self.boundry.max)
        self.place(rely=self.position)
    
    def offset(self, amount):
        self.update(self.position + amount)

    def score(self, score=None):
        if score is not None:
            self._score.set(score)
        else:
            self._score.set(self._score.get() + 1)

class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

class Ball(Frame):
    
    DEFAULT_SIZE = 0.02
    
    DEFAULT_SPEED = 0.02
    DEFAULT_FPS = 60
    
    def __init__(self, master, size=DEFAULT_SIZE, speed=DEFAULT_SPEED, *args, **kwargs):
        Frame.__init__(self, master, *args, **kwargs)
        self.config(bg='white')
        self.set_size(size)
        self.speed = speed
        self.timer = None        
        self.restart()
    
    def restart(self, *args, **kwargs):
        if self.timer:
            self.stop()
        self.is_playing = True
        self.position = Vector(0.5, 0.5)
        self.direction = Vector(random.randrange(-1, 2, 2), 0)
        self.place(relx=self.position.x, rely=self.position.y)
        self.start_timer()

    def set_size(self, size=None, *args, **kwargs):
        if size:
            self.size = size
            _xmin = Player.DEFAULT_WIDTH + size / 2.0
            self.xboundry = Boundry(_xmin, 1.0 - _xmin)
        else:
            size = self.size
        aspect_ratio = float(app.width) / float(app.height)
        _ymin = aspect_ratio * size / 2.0
        self.yboundry = Boundry(_ymin, 1.0 - _ymin)
        self.place(relwidth=size, relheight=aspect_ratio * size, anchor=CENTER)

    def set_speed(self, speed, *args, **kwargs):
        self.speed = speed

    def _run(self):
        while not self.timer.stop.wait(1.0 / Ball.DEFAULT_FPS):
            self._update()
    def start_timer(self):
        self.timer = Thread(target=self._run)
        self.timer.stop = Event()
        self.timer.start()
    def stop(self):
        self.timer.stop.set()
    
    def _bounce(self):
        self.direction.x *= -1
        self.direction.y = 2 * random.random() - 1
        self.position.y = clamp(self.position.y, self.yboundry.min, self.yboundry.max)
        
    def _update(self):
        self.position.x += self.direction.x * self.speed
        self.position.y += self.direction.y * self.speed
        if self.position.x <= self.xboundry.min:
            if self.position.y > players[0].position - players[0].boundry.min - self.yboundry.min and self.position.y < players[0].position + players[0].boundry.min + self.yboundry.min:
                self.position.x = self.xboundry.min
                self._bounce()
            else:
                players[1].score()
                self.stop()
                self.is_playing = False
        elif self.position.x >= self.xboundry.max:
            if self.position.y > players[1].position - players[1].boundry.min - self.yboundry.min and self.position.y < players[1].position + players[1].boundry.min + self.yboundry.min:
                self.position.x = self.xboundry.max
                self._bounce()
            else:
                players[0].score()
                self.stop()
                self.is_playing = False
        if self.position.y < self.yboundry.min or self.position.y > self.yboundry.max:
            self.direction.y *= -1
        self.place(relx=self.position.x, rely=self.position.y)


players = [Player(app, 0), Player(app, 1)]
ball = Ball(app)

def pause(*args, **kwargs):
    if ball.is_playing:
        ball.start_timer() if ball.timer.stop.is_set() else ball.stop()

def reset(*args, **kwargs):
    for player in players:
        player.score(0)

# Local input
def key(event):
    if event.keysym == 'Escape':
        app.destroy()
    
    if event.keysym.lower() == 'w':
        players[0].offset(-0.025)
    if event.keysym.lower() == 's':
        players[0].offset(0.025)
    
    if event.keysym == 'Up':
        players[1].offset(-0.025)
    if event.keysym == 'Down':
        players[1].offset(0.025)
    
    if (event.keysym.lower() == 'p' or event.keysym == 'space'):
        pause()
    if event.keysym.lower() == 'r':
        ball.restart()

app.bind('<Key>', key)

# Set up server
server = HttpSocketServer(2, title='Pong')
server.start()

# Remote input
server.set_callback('position', players[0].update, 0)
server.set_callback('position', players[1].update, 1)

server.set_callback('size', players[0].set_height, 0)
server.set_callback('size', players[1].set_height, 1)

server.set_callback('pause', pause)
server.set_callback('play', ball.restart)
server.set_callback('reset', reset)

server.set_callback('exit', app.destroy)

server.set_callback('speed', ball.set_speed)

# Size changed event
def sizechanged(e):
    app.width, app.height = e.width, e.height
    
    line_width = app.width * line_size
    line_xpos = line_width / 2.0
    line.coords(line_id, line_xpos, 0, line_xpos, app.height)
    line.itemconfig(line_id, width=line_width)

    ball.set_size()

background.bind('<Configure>', sizechanged)

# Main loop
app.mainloop()
ball.stop()
server.stop()
