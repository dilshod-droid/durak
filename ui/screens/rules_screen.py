"""
ui/screens/rules_screen.py — Qoidalar Ekrani
Accordion uslubida scrollable qoidalar.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.scrollview   import ScrollView
from kivy.uix.label        import Label
from kivy.uix.widget       import Widget
from kivy.uix.behaviors    import ButtonBehavior
from kivy.graphics         import Color, Rectangle, RoundedRectangle, Line
from kivy.animation        import Animation
from kivy.app              import App
from ui.components.luxury_button import LuxuryButton
from core.constants        import COLORS, FONT_SIZES

RULES_DATA = [
    (
        'Dasta tarkibi',
        '• 36 ta karta (6 dan Tuzgacha)\n'
        '• 4 xil mast: ♠ Pika, ♥ Qo\'r, ♦ Karo, ♣ Treff\n'
        '• Qiymatlar ustunligi: 6 < 7 < 8 < 9 < 10 < J < Q < K < A\n'
        '• Kozir — boshqa barcha mastlarni bo\'ysundiruvchi eng kuchli mast'
    ),
    (
        'O\'yin boshlash',
        '• O\'yin boshida dasta yaxshilab aralashtiriladi\n'
        '• Oxirgi karta ochiq qo\'yiladi — uning masti KOZIR bo\'ladi\n'
        '• Eng kichik kozir kartasiga ega o\'yinchi birinchi bo\'lib hujum qiladi\n'
        '• Har bir o\'yinchiga 6 tadan karta tarqatiladi'
    ),
    (
        'Hujum qoidalari',
        '• Hujumchi 1 ta karta tashlaydi\n'
        '• Himoyachi uni yopishi kerak:\n'
        '  — Bir xil mastdagi kattaroq qiymat BILAN\n'
        '  — Yoki istalgan KOZIR mast BILAN\n'
        '• Yopa olmasa → barcha kartalarni o\'ziga oladi → navbat o\'ziga o\'tmaydi'
    ),
    (
        'Podkidnoy (qo\'shimcha hujum)',
        '• Hujumchi qo\'shimcha karta tashlishi mumkin, agar:\n'
        '  — Stoldagi kartaning qiymati qo\'lda mavjud bo\'lsa\n'
        '  — Stoldagi kartalar soni himoyachining qo\'lidan oshmasa\n'
        '• Maksimal 6 ta juft bo\'lishi mumkin'
    ),
    (
        'Navbat va to\'ldirish',
        '• Himoyachi barchasini yopsa → stoldagi kartalar chetga olinadi (bita)\n'
        '• Himoyalanganidan keyin hujum navbati himoyachiga o\'tadi\n'
        '• Har tur oxirida qo\'lda 6 dan kam karta bo\'lsa → dastadan olinadi\n'
        '• To\'ldirish tartibi: birinchi hujumchi o\'zini to\'ldiradi, so\'ng himoyachi'
    ),
    (
        'O\'yin tugashi',
        '• Dasta tugasa VA qo\'lda karta qolmasa → G\'OLIB bo\'lasiz!\n'
        '• Oxirgi qo\'lidagi karta bilan qolgan o\'yinchi → DURAK (mag\'lub bo\'ladi)\n'
        '• Ikkalasi ham bir vaqtda kartasini tugatsa → DURAK o\'yinda yo\'q (durang)'
    ),
    (
        'Kozir nima?',
        '• Kozir — o\'yin boshida aniqlangan alohida mast\n'
        '• Kozir kartasi istalgan oddiy kartani yengadi\n'
        '• Kattaroq kozir kichik kozirni yengadi\n'
        '• Kozir belgi o\'yin ekranida pastda ko\'rsatiladi'
    ),
]


class RulesScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built = False
        self._items = []

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True

    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        with self.canvas.before:
            Color(*COLORS['background'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda *a: setattr(self._bg, 'pos', self.pos),
            size=lambda *a: setattr(self._bg, 'size', self.size)
        )

        # Sarlavha
        root.add_widget(Label(
            text='QOIDALAR', font_size=FONT_SIZES['h1'], bold=True,
            color=COLORS['gold'], size_hint=(1, None), height=50,
            pos_hint={'x': 0, 'top': 1}, halign='center',
        ))

        # Scroll area
        scroll = ScrollView(
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
            bar_width=4, bar_color=COLORS['gold'][:3] + (0.4,),
        )
        root.add_widget(scroll)

        col = BoxLayout(
            orientation='vertical', spacing=8,
            padding=[20, 68, 20, 20],
            size_hint_y=None,
        )
        col.bind(minimum_height=col.setter('height'))
        scroll.add_widget(col)

        for title, body in RULES_DATA:
            item = _AccordionItem(title=title, body=body)
            col.add_widget(item)
            self._items.append(item)

        col.add_widget(Widget(size_hint_y=None, height=12))
        back_btn = LuxuryButton(text='Orqaga', style='secondary')
        back_btn.bind(on_release=lambda *a: self._go_back())
        col.add_widget(back_btn)

    def _go_back(self):
        App.get_running_app().navigate_to('main_menu', direction='right')


class _AccordionItem(BoxLayout):
    def __init__(self, title: str, body: str, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None,
                         spacing=0, **kwargs)
        self._expanded = False
        self._title    = title
        self._body_text = body

        # Header
        self._header = _AccordionHeader(title=title)
        self._header.bind(on_release=lambda *a: self._toggle())
        self.add_widget(self._header)

        # Body
        self._body_widget = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=0,
            opacity=0,
            padding=[16, 8, 16, 12],
        )
        self._body_lbl = Label(
            text=body,
            font_size=FONT_SIZES['small'],
            color=COLORS['text_primary'],
            halign='left',
            valign='top',
            size_hint_y=None,
        )
        self._body_lbl.bind(
            width=lambda inst, w: setattr(inst, 'text_size', (w, None))
        )
        self._body_lbl.bind(
            texture_size=lambda inst, ts: setattr(inst, 'height', ts[1])
        )
        self._body_widget.add_widget(self._body_lbl)
        self._body_widget.bind(
            minimum_height=self._body_widget.setter('height')
        )
        self.add_widget(self._body_widget)

        self.height = self._header.height
        self.bind(pos=self._draw_bg, size=self._draw_bg)

    def _toggle(self):
        self._expanded = not self._expanded
        self._header.set_expanded(self._expanded)

        if self._expanded:
            self._body_lbl.texture_update()
            body_h = self._body_lbl.texture_size[1] + 20
            self._body_widget.height = body_h
            Animation(opacity=1, duration=0.2).start(self._body_widget)
            Animation(height=self._header.height + body_h, duration=0.2).start(self)
        else:
            Animation(opacity=0, height=0, duration=0.2).start(self._body_widget)
            Animation(height=self._header.height, duration=0.2).start(self)
        self._draw_bg()

    def _draw_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
            Color(*COLORS['gold'][:3], 0.2 if not self._expanded else 0.6)
            Line(rounded_rectangle=[self.x, self.y,
                                     self.width, self.height, 10], width=1.0)


class _AccordionHeader(ButtonBehavior, BoxLayout):
    def __init__(self, title: str, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.size_hint_y = None
        self.height = 48
        self.padding = [14, 0]
        self._expanded = False

        self._lbl = Label(
            text=title, font_size=FONT_SIZES['body'], bold=True,
            color=COLORS['text_primary'], halign='left',
        )
        self._lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))

        self._arrow = Label(
            text='+', font_size=FONT_SIZES['h3'], bold=True,
            color=COLORS['gold'], size_hint_x=None, width=24,
        )
        self.add_widget(self._lbl)
        self.add_widget(self._arrow)

    def set_expanded(self, val: bool):
        self._expanded = val
        self._arrow.text = '-' if val else '+'
        self._lbl.color = COLORS['gold'] if val else COLORS['text_primary']

    def on_press(self):
        Animation(opacity=0.7, duration=0.05).start(self)

    def on_release(self):
        Animation(opacity=1.0, duration=0.08).start(self)
