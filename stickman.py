from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.image import Image
from kivy.clock import Clock, ClockEvent
from kivy.core.window import Window


class StickMan(Image):
    velocity = NumericProperty(0)
    lifes = BooleanProperty(True)
    double_jump = NumericProperty(0)
    frames = 0
    sliding = NumericProperty(0)
    game_active = BooleanProperty(False)

    # start some action
    def start_run(self):
        self.frames = Clock.schedule_interval(self.run, 1 / 40.)

    def start_slide(self):
        self.sliding = 0
        self.frames = Clock.schedule_interval(self.slide, 1 / 20.)

    def start_jump(self):
        self.frames = Clock.schedule_interval(self.jump, 1 / 16.)

    # stop current action
    def stop_current_action(self):
        self.sliding = 0
        if self.frames:
            self.frames.cancel()

    # action
    def jump(self, time_passed):
        frame = int(self.source[13:14])
        if frame >= 7:
            self.source = 'assets/jumpi/7.png'
        else:
            frame += 1
            self.source = 'assets/jumpi/{}.png'.format(frame)

    def run(self, time_passed):
        frame = int(self.source[13:14])
        if frame == 9:
            frame = 1
        else:
            frame += 1
        self.source = 'assets/runin/{}.png'.format(frame)

    def slide(self, time_passed):
        frame = int(self.source[13:14])
        if frame >= 5:
            self.source = 'assets/slide/5.png'
        else:
            frame += 1
            self.source = 'assets/slide/{}.png'.format(frame)

    # events
    def on_touch_down(self, touch):
        if self.game_active:
            if touch.pos[1] > Window.width / 9:
                if touch.pos[0] > Window.width / 2:
                    self.size = (182 * (Window.height / 5 / 211), Window.height / 5)
                    self.stop_current_action()
                    self.start_jump()
                    self.double_jump += 1
                    if self.double_jump <= 2:
                        self.velocity = Window.height * 0.32
                else:
                    self.stop_current_action()
                    self.source = 'assets/slide/1.png'
                    self.size = (Window.height / 5, 118 * (Window.height / 5 / 191))
                    self.start_slide()

        super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.pos[1] > Window.width / 9:
            if touch.pos[0] < Window.width / 2:
                self.stop_current_action()
                self.size = (182 * (Window.height / 5 / 211), Window.height / 5)
                self.start_run()
            else:
                self.size = (182 * (Window.height / 5 / 211), Window.height / 5)
                self.stop_current_action()
                self.start_run()

        super().on_touch_up(touch)
