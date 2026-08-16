import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

DEFAULT_COLORS = {
    "bg": (0.09, 0.09, 0.15, 1),
    "empty": (0.19, 0.20, 0.27, 1),
    "text": (0.80, 0.84, 0.96, 1),
    2: (0.96, 0.88, 0.86, 1),
    4: (0.95, 0.80, 0.80, 1),
    8: (0.96, 0.66, 0.50, 1),
    16: (0.93, 0.83, 0.62, 1),
    32: (0.65, 0.85, 0.58, 1),
    64: (0.55, 0.84, 0.79, 1),
    128: (0.57, 0.84, 0.89, 1),
    256: (0.49, 0.77, 0.89, 1),
    512: (0.54, 0.68, 0.96, 1),
    1024: (0.78, 0.63, 0.96, 1),
    2048: (0.96, 0.74, 0.90, 1),
}

class RootLayout(BoxLayout):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        self.touch_start_pos = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_start_pos = touch.pos
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.touch_start_pos:
            dx = touch.x - self.touch_start_pos[0]
            dy = touch.y - self.touch_start_pos[1]
            min_swipe = 40  # المسافة الأدنى للسحب
            
            if abs(dx) > min_swipe or abs(dy) > min_swipe:
                if abs(dx) > abs(dy):
                    if dx > 0:
                        self.app.make_move('Right')
                    else:
                        self.app.make_move('Left')
                else:
                    if dy > 0:
                        self.app.make_move('Up')
                    else:
                        self.app.make_move('Down')
            self.touch_start_pos = None
        return super().on_touch_up(touch)

class Game2048App(App):
    def build(self):
        self.title = "Mohamed's 2048"
        self.grid_size = 4
        self.score = 0
        self.high_scores = {"3x3": 0, "4x4": 0, "5x5": 0}
        self.last_state = None
        self.can_undo = False
        self.game_over = False

        self.root = RootLayout(self, orientation='vertical', padding=10, spacing=10)
        
        with self.root.canvas.before:
            Color(*DEFAULT_COLORS["bg"])
            self.bg_rect = Rectangle(size=Window.size, pos=self.root.pos)
        self.root.bind(size=self._update_bg, pos=self._update_bg)

        # Header Controls
        self.header = BoxLayout(size_hint_y=0.12, spacing=5)
        
        self.score_label = Label(text="Score: 0", font_size='15sp', bold=True, color=DEFAULT_COLORS["text"])
        self.high_score_label = Label(text="Best: 0", font_size='15sp', bold=True, color=(0.96, 0.66, 0.50, 1))
        
        self.btn_undo = Button(text="Undo", size_hint_x=0.2, on_press=lambda x: self.undo_move())
        self.btn_reset = Button(text="New", size_hint_x=0.2, on_press=lambda x: self.start_game())
        
        self.size_spinner = Spinner(text="4x4", values=["3x3", "4x4", "5x5"], size_hint_x=0.25)
        self.size_spinner.bind(text=self.change_size)

        self.header.add_widget(self.score_label)
        self.header.add_widget(self.high_score_label)
        self.header.add_widget(self.btn_undo)
        self.header.add_widget(self.btn_reset)
        self.header.add_widget(self.size_spinner)
        self.root.add_widget(self.header)

        # Board Container
        self.board_container = BoxLayout(size_hint_y=0.88)
        self.root.add_widget(self.board_container)

        Window.bind(on_keyboard=self.on_keyboard)
        self.setup_board()
        self.start_game()
        return self.root

    def _update_bg(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def setup_board(self):
        self.board_container.clear_widgets()
        self.grid_layout = GridLayout(cols=self.grid_size, rows=self.grid_size, spacing=5, padding=5)
        
        self.tiles = {}
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                lbl = Label(
                    text="",
                    font_size=f'{28 if self.grid_size < 5 else 22}sp',
                    bold=True,
                    color=(0.1, 0.1, 0.1, 1)
                )
                with lbl.canvas.before:
                    Color(*DEFAULT_COLORS["empty"])
                    lbl.bg_rect = Rectangle(size=lbl.size, pos=lbl.pos)
                lbl.bind(size=self._update_tile_bg, pos=self._update_tile_bg)
                self.tiles[(r, c)] = lbl
                self.grid_layout.add_widget(lbl)

        self.board_container.add_widget(self.grid_layout)

    def _update_tile_bg(self, instance, value):
        instance.bg_rect.size = instance.size
        instance.bg_rect.pos = instance.pos

    def change_size(self, spinner, text):
        self.grid_size = int(text[0])
        self.setup_board()
        self.start_game()

    def start_game(self):
        self.grid_data = [[0] * self.grid_size for _ in range(self.grid_size)]
        self.score = 0
        self.last_state = None
        self.can_undo = False
        self.game_over = False
        self.update_score()
        self.add_new_tile()
        self.add_new_tile()
        self.update_board()

    def add_new_tile(self):
        empty = [(r, c) for r in range(self.grid_size) for c in range(self.grid_size) if self.grid_data[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.grid_data[r][c] = 2 if random.random() < 0.9 else 4

    def update_score(self):
        mode_key = f"{self.grid_size}x{self.grid_size}"
        if self.score > self.high_scores[mode_key]:
            self.high_scores[mode_key] = self.score
        self.score_label.text = f"Score: {self.score}"
        self.high_score_label.text = f"Best: {self.high_scores[mode_key]}"

    def update_board(self):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                val = self.grid_data[r][c]
                lbl = self.tiles[(r, c)]
                lbl.text = str(val) if val != 0 else ""
                bg_color = DEFAULT_COLORS.get(val, DEFAULT_COLORS[2048]) if val != 0 else DEFAULT_COLORS["empty"]
                lbl.canvas.before.clear()
                with lbl.canvas.before:
                    Color(*bg_color)
                    lbl.bg_rect = Rectangle(size=lbl.size, pos=lbl.pos)

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        keys = {273: 'Up', 274: 'Down', 276: 'Left', 275: 'Right', 122: 'Up', 115: 'Down', 113: 'Left', 100: 'Right'}
        if key in keys:
            self.make_move(keys[key])
            return True
        return False

    def undo_move(self):
        if self.can_undo and self.last_state:
            self.grid_data, self.score = self.last_state
            self.can_undo = False
            self.update_board()
            self.update_score()

    def make_move(self, direction):
        if self.game_over:
            return
        prev = ([row[:] for row in self.grid_data], self.score)
        moved = self.process_move(direction)
        if moved:
            self.last_state = prev
            self.can_undo = True
            self.add_new_tile()
            self.update_board()
            self.update_score()
            if self.check_game_over():
                self.game_over = True
                self.show_game_over()

    def process_move(self, direction):
        rotated = self.grid_data
        if direction == 'Up': rotated = self.rotate(rotated, 3)
        elif direction == 'Right': rotated = self.rotate(rotated, 2)
        elif direction == 'Down': rotated = self.rotate(rotated, 1)

        new_grid, moved = self.compress_and_merge(rotated)

        if direction == 'Up': new_grid = self.rotate(new_grid, 1)
        elif direction == 'Right': new_grid = self.rotate(new_grid, 2)
        elif direction == 'Down': new_grid = self.rotate(new_grid, 3)

        self.grid_data = new_grid
        return moved

    def compress_and_merge(self, grid):
        new_grid, moved = [], False
        for row in grid:
            nz = [v for v in row if v != 0]
            merged, skip = [], False
            for i in range(len(nz)):
                if skip:
                    skip = False
                    continue
                if i + 1 < len(nz) and nz[i] == nz[i + 1]:
                    merged.append(nz[i] * 2)
                    self.score += nz[i] * 2
                    skip = True
                else:
                    merged.append(nz[i])
            merged += [0] * (self.grid_size - len(merged))
            if merged != row: moved = True
            new_grid.append(merged)
        return new_grid, moved

    def rotate(self, grid, times):
        for _ in range(times):
            grid = [list(row) for row in zip(*grid[::-1])]
        return grid

    def check_game_over(self):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid_data[r][c] == 0: return False
                if c + 1 < self.grid_size and self.grid_data[r][c] == self.grid_data[r][c + 1]: return False
                if r + 1 < self.grid_size and self.grid_data[r][c] == self.grid_data[r + 1][c]: return False
        return True

    def show_game_over(self):
        view = ModalView(size_hint=(0.8, 0.4))
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box.add_widget(Label(text="hahahahahaha you've lost", font_size='18sp', color=(1, 0.4, 0.4, 1)))
        btn = Button(text="Retry", size_hint_y=0.4, on_press=lambda x: (view.dismiss(), self.start_game()))
        box.add_widget(btn)
        view.add_widget(box)
        view.open()

if __name__ == '__main__':
    Game2048App().run()
