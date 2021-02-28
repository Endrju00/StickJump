from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from random import choice
from time import sleep
from kivy.metrics import sp, dp
from kivy.core.audio import SoundLoader
from kivy.storage.jsonstore import JsonStore

from pipe import Pipe
from stickman import StickMan


class Background(Widget):
    floor_texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create textures
        self.floor_texture = Image(source="assets/floor.png").texture
        self.floor_texture.wrap = 'repeat'
        self.floor_texture.uvsize = (Window.width / self.floor_texture.width, -1)

    def scroll_textures(self, time_passed):
        # update pos
        self.floor_texture.uvpos = ((self.floor_texture.uvpos[0] + time_passed * 4) % Window.width, self.floor_texture.uvpos[1])

        # redraw textures
        texture = self.property('floor_texture')
        texture.dispatch(self)


class MainApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pipes = []
        self.GRAVITY = Window.height * 0.8
        self.die_flag = 0
        self.game_active = False
        self.speed = 1
        self.floor_height = Window.height / 9
        self.score = 0
        self.pause = False

        # play sound
        self.soundtrack = SoundLoader.load('sounds/soundtrack.wav')
        self.soundtrack.play()
        self.soundtrack.loop = True
        self.soundtrack.volume = 0.45

        # store data
        self.store = JsonStore('highscore.json')

    # stickman movement
    def move_stickman(self, time_passed):
        stickman = self.root.ids.stickman
        stickman.y = stickman.y + stickman.velocity * time_passed * 5

        if stickman.y <= self.floor_height - stickman.sliding:
            stickman.y = self.floor_height - stickman.sliding
            stickman.velocity = 0
            stickman.double_jump = 0

        if stickman.top > Window.height:
            stickman.top = Window.height
            stickman.velocity = 0
        else:
            stickman.velocity = stickman.velocity - self.GRAVITY * time_passed

        self.check_collision()

        # if window size change
        self.GRAVITY = Window.height * 0.8
        self.floor_height = Window.height / 9

    def update_score(self):
        self.score += 10
        if self.root.ids.score.text[0] != "Y" and self.root.ids.score.text[0] != "N":
            if self.score > 1000:
                temp = round(self.score / 1000, 1)
                self.root.ids.score.text = str(temp) + 'K'
            else:
                self.root.ids.score.text = str(self.score)

    def update_speed(self):
        if self.speed <= 2.5:
            self.speed += 0.00005

    # checking collisions
    def check_collision(self):
        stickman = self.root.ids.stickman
        if stickman.x < -stickman.size[0]:
            if stickman.lifes:
                stickman.pos = (Window.width / 6, self.floor_height)
                stickman.lifes = False
                self.root.ids.lifes.text = "LIFES: 1"
            else:
                self.root.ids.lifes.text = "GAME OVER"
                self.game_over()
        if -stickman.size[0] < stickman.x < Window.width / 6:
            stickman.x += dp(0.5)

        for pipe in self.pipes:
            if pipe.collide_widget(stickman):

                # bottom pipe
                if stickman.y < (pipe.pipe_center - pipe.GAP_SIZE / 2.0):
                    if stickman.x > pipe.x + 3 * pipe.size[0] / 4:
                        stickman.x = pipe.x + 3 * pipe.size[0] / 4
                        stickman.x += pipe.size[0] / 4
                    else:
                        stickman.x = pipe.x - stickman.size[0]
                # top pipe
                if stickman.top > (pipe.pipe_center + pipe.GAP_SIZE / 2.0):
                    stickman.x = pipe.x - stickman.size[0]

    # game is over
    def game_over(self):
        stickman = self.root.ids.stickman
        self.game_active = False
        stickman.game_active = False
        stickman = self.root.ids.stickman
        self.root.ids.start_button.disabled = False
        self.root.ids.start_button.opacity = 1
        self.root.ids.quit_button.disabled = False
        self.root.ids.quit_button.opacity = 1
        self.root.ids.pause_button.disabled = True
        self.speed = 1
        self.root.ids.score.text = "YOUR SCORE: {}".format(self.score)
        self.save_highscore()


        for pipe in self.pipes:
            self.root.remove_widget(pipe)
        self.frames.cancel()
        stickman.stop_current_action()

        stickman.pos = (-2 * stickman.size[1], self.floor_height)
        stickman.lifes = 2
        self.die_flag = 0

    # what to do in next frame
    def next_frame(self, time_passed):
        self.move_stickman(time_passed)
        self.move_pipes(time_passed)
        self.root.ids.background.scroll_textures(time_passed)
        self.update_score()
        self.update_speed()

    # start the game
    def start_game(self):
        if not self.game_active:
            stickman = self.root.ids.stickman
            stickman.pos = (dp(60), self.floor_height)

            self.game_active = True
            stickman.game_active = True
            self.root.ids.pause_button.disabled = False
            self.root.ids.quit_button.disabled = True
            self.root.ids.quit_button.opacity = 0
            self.pipes = []

            self.frames = Clock.schedule_interval(self.next_frame, 1 / 60.)
            self.root.ids.score.text = str(0)
            self.root.ids.lifes.text = "LIFES: 2"
            self.score = 0

            num_pipes = 50
            factor = min(self.speed, 1.1)
            distance_between_pipes = Window.width / (num_pipes - 48) * 2 * factor

            for i in range(num_pipes):
                pipe = Pipe()
                pipe.pipe_center = choice([((self.root.height) / 9), ((self.root.height) / 2), (4 * self.root.height) / 5])
                pipe.size_hint = (None, None)
                pipe.pos = (Window.width + i * distance_between_pipes, self.floor_height)
                pipe.size = (dp(64), self.root.height - self.floor_height)

                self.pipes.append(pipe)
                self.root.add_widget(pipe)

    def move_pipes(self, time_passed):
        for pipe in self.pipes:
            pipe.x -= dp(time_passed * 100 * 6 * self.speed)

        num_pipes = 50
        factor = min(self.speed, 1.1)
        distance_between_pipes = Window.width / (num_pipes - 48) * 2 * factor

        pipe_xs = list(map(lambda pipe: pipe.x, self.pipes))
        right_most_x = max(pipe_xs)

        if right_most_x <= Window.width - distance_between_pipes:
            most_left_pipe = self.pipes[pipe_xs.index(min(pipe_xs))]
            most_left_pipe.x = Window.width

    def mute_sound(self):
        if self.soundtrack.volume > 0:
            self.soundtrack.volume = 0
            self.root.ids.mute_button.text = "UNMUTE"
        else:
            self.soundtrack.volume = 0.45
            self.root.ids.mute_button.text = "MUTE"

    def save_highscore(self):
        actual_highscore = self.store.get('highscore')['score']
        if self.score > actual_highscore:
            self.store.put('highscore', score=self.score)
            self.root.ids.score.text = "NEW HIGHSCORE: {}".format(self.score)
        else:
            self.root.ids.score.text = "YOUR SCORE: {}".format(self.score)

    def pause_game(self):
        stickman = self.root.ids.stickman
        if not self.pause:
            self.root.ids.pause_button.text = "UNPAUSE"
            self.root.ids.score.text = "GAME PAUSED"
            self.frames.cancel()
            stickman.frames.cancel()
            self.pause = True
            stickman.pause = True
        else:
            self.pause = False
            stickman.pause = False
            self.root.ids.pause_button.text = "PAUSE"
            self.frames = Clock.schedule_interval(self.next_frame, 1 / 60.)
            stickman.start_run()


if __name__ == '__main__':
    MainApp().run()
