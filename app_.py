from kivy.core.window import Window
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.snackbar import StringProperty, Snackbar
from kivymd.uix.label import MDLabel
import os
import re
import cv2
import numpy as np
import pyautogui as pg
from win32api import GetSystemMetrics, GetCursorPos
import subprocess
import threading
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, BaseButton
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics.texture import Texture
from kivy.clock import mainthread
import shutil
from screeninfo import get_monitors
from kivymd.uix.list import OneLineAvatarIconListItem, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from functools import partialmethod, partial

Window.size = (800, 600)

if 'recordings' not in os.listdir(os.getcwd()):
    os.mkdir('recordings')

KV = '''
# kv_start
<ListItemWithCheckboxGroup>:

    IconLeftWidget:
        icon: root.icon

    RightCheckbox:
        id: check_box
        on_press:
            app.cb_handler(root.text, check_box)
<ListItemWithCheckbox>:

    IconLeftWidget:
        icon: root.icon

    RightCheckbox:
        id: check_box
<-Snackbar>:

    MDCard:
        id: box
        size_hint_y: None
        height: dp(73)
        spacing: dp(5)
        padding: dp(10)
        y: -self.height
        x: root.padding
        md_bg_color: get_color_from_hex('323232')
        radius: (5, 5, 5, 5) if root.padding else (0, 0, 0, 0)
        elevation: 11 if root.padding else 0

        MDIconButton:
            pos_hint: {'center_y': .5}
            icon: root.icon
            opposite_colors: True

        BoxLayout:
            spacing: dp(5)
            padding: dp(10)
            orientation: 'vertical'
            MDLabel:
                id: text_bar
                size_hint_y: None
                height: self.texture_size[1]
                text: root.text
                font_size: root.font_size
                theme_text_color: 'Custom'
                text_color: get_color_from_hex('ffffff')
                shorten: True
                shorten_from: 'right'
                pos_hint: {'center_y': .5}
            MDLabel:
                id: text_bar_2
                size_hint_y: None
                height: self.texture_size[1]
                text: root.text_2
                font_size: root.font_size
                theme_text_color: 'Custom'
                text_color: get_color_from_hex('ffffff')
                shorten: True
                shorten_from: 'right'
                pos_hint: {'center_y': .5}
My_Screen_Manager:
    Screen:
        name: 'settings'
        BoxLayout:
            orientation: 'vertical'
            MDToolbar:
                id: toolbar
                title: 'Settings' 
                left_action_items: [['step-backward-2', lambda x: root.go_home()]]
            ScrollView:
                MDList:
                    ListItemWithCheckbox:
                        id: draw_mouse
                        text: 'draw_mouse'
                        icon: 'eye-off'
                        on_release:
                            app.make_active_or_inactive(self.ids.check_box)

                    ListItemWithCheckboxGroup:
                        id: stereo
                        text: 'stereo'
                        icon: 'eye-off'
                        on_release:
                            app.stereo_or_mono(self.ids.check_box, root.ids.mono.ids.check_box)
                    ListItemWithCheckboxGroup:
                        id: mono
                        text: 'mono' 
                        icon: 'eye-off'
                        on_release:
                            app.stereo_or_mono(self.ids.check_box, root.ids.stereo.ids.check_box)




    Screen:
        id: basescreen
        name: 'base_screen'
        BoxLayout:
            orientation: 'vertical'
            MDToolbar:
                title: 'Start recording'
                left_action_items: [['video', lambda x: root.go_to_live()]]

            FloatLayout:
                BoxLayout:
                    padding: [50, 0, 50, 0]
                    MDLabel:
                        text: 'If u skip this field, default file name will be: recording_i'
                        pos_hint: {'center_x': .5, 'center_y': .75}
            FloatLayout:
                MDRaisedButton:
                    id: start_button
                    text: 'Start recording'
                    pos_hint: {'center_x': .5, 'center_y': .5}
                    on_release:
                        app.show_dialog_if_need()
                        app.check_rc() if app.can_stop and app.next_step == 2 else app.make_wanna_stop_true()
                        app.update_can_write_and_prv_text() if app.next_step == 2 else app.method()
            BoxLayout:
                orientation: 'horizontal'
                padding: [50, 0, 50, 0]
                spacing: 100
                pos_hint: {'center_x': .5, 'center_y': .75}
                MDTextField:
                    id: field
                    hint_text: 'File name'
                    on_text_validate:
                        app.show_dialog_if_need()
                        app.check_validate() if app.next_step == 2 else app.method()
                        app.update_can_write_and_prv_text() if app.next_step == 2 else app.method()


                    on_text:
                        app.update_field_text()                
                MDDropDownItem:
                    id: drop_item
                    text: '.mp4'
                    on_release:
                        app.check_menu()
                        app.state = 'start'
            Widget:          


    My_Screen:



<My_Screen_Manager>:
<My_Screen>:
    on_enter:
        self.start_live()
    name: 'live_screen'
    BoxLayout:
        orientation: 'vertical'
        MDToolbar:
            id: toolbar
            title: 'Live translation' 
            left_action_items: [['step-backward-2', lambda x: root.manager.go_home()]]
        Image:
            id: video
            allow_stretch: True
# kv_end
'''


class RightCheckbox(IRightBodyTouch, MDCheckbox):
    '''Custom right container.'''


class ListItemWithCheckbox(OneLineAvatarIconListItem):
    '''Custom list item.'''

    icon = StringProperty("android")


class ListItemWithCheckboxGroup(OneLineAvatarIconListItem):
    '''Custom list item.'''

    icon = StringProperty("android")


class My_Screen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stop = False
        self.my_image = ''
        self.my_texture = ''

    def start_live(self):
        self.stop = False
        if not self.my_image:
            resolution = (get_monitors()[0].width, get_monitors()[0].height)
            self.my_image = self.ids.video
            self.my_texture = Texture.create(resolution)
            self.my_texture.flip_vertical()
            self.my_image.texture = self.my_texture
            self.my_image.texture_size = list(resolution)
        threading.Thread(target=self.make_live, daemon=True).start()

    def make_live(self):
        while True:
            data = np.array(pg.screenshot())
            self.buffer = data.reshape(-1)
            self.update_texture()
            if self.stop:
                break

    @mainthread
    def update_texture(self):
        self.my_texture.blit_buffer(self.buffer, colorfmt="rgb")
        self.my_image.canvas.ask_update()

    def on_leave(self, *args):
        self.stop = True


class My_Screen_Manager(ScreenManager):
    def go_home(self, dir_=None):
        self.transition.direction = dir_ if dir_ != None else 'right'
        self.current = 'base_screen'

    def go_to_live(self, dir_=None):
        self.transition.direction = dir_ if dir_ != None else 'left'
        self.current = 'live_screen'


class CustomSnackbar(Snackbar):
    icon = StringProperty()
    text_2 = StringProperty()


class Test(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_stop = True
        self.wanna_stop = False
        self.can_write = True
        self.prv_text = ''

        self.frame = '30'
        self.draw_mouse = '1'
        self.size = get_monitors()[0]
        self.size = f'{self.size.width}x{self.size.height}'
        self.audio_chanel = 'stereo'
        self.file_name = ['', '']
        # frame, draw, video_size, audio_inputs(chanel_1, audio_1, chanel_2, audio_2), file_name

        self.command = 'ffmpeg -y -rtbufsize 200M -f gdigrab -thread_queue_size 1024 -probesize 10M -framerate {} -draw_mouse {} -video_size {} -i desktop -f dshow -channel_layout {} -thread_queue_size 1024 -i audio="{}" -f dshow -channel_layout {} -thread_queue_size 1024 -i audio="{}" -c:v libx264 -preset ultrafast -tune zerolatency -crf 25 -c:a aac -ac 2 -b:a 128k -filter_complex "[0]format=yuv420p[v];[1][2]amix=inputs=2[a]" -map [v] -map [a] -movflags +faststart {}'
        self.start_button = ''
        self.field = ''
        self.container = ''

        self.next_step = 0
        self.prv_dialog_file = ''
        self.dialog_text = 'File {} already exists.'
        BaseButton()
        buttons = [MDFlatButton(text="CANCEL", text_color=self.theme_cls.primary_color),
                   MDFlatButton(text="OK", text_color=self.theme_cls.primary_color)]
        buttons[0].bind(on_release=lambda *args: self.dialog_process(0))
        buttons[1].bind(on_release=lambda *args: self.dialog_process(1))
        self.dialog = MDDialog(title='Rewrite the file?', text=self.dialog_text, buttons=buttons, auto_dismiss=False)

        # self.screen_size = (GetSystemMetrics(0), GetSystemMetrics(1))
        self.screen = Builder.load_string(KV)
        menu_items = [{"icon": "file", "text": f"{i}"} for i in ['.mp4', '.avi', '.mov', '.mp4v']]
        self.menu = MDDropdownMenu(
            caller=self.screen.ids.drop_item,
            items=menu_items,
            position="auto",
            width_mult=4)
        self.menu.bind(on_release=self.set_item)

    def on_start(self):
        self.root.ids.stereo.ids.check_box.active = True
        self.root.ids.draw_mouse.ids.check_box.active = True
        self.start_button = self.root.ids['start_button']
        self.field = self.root.ids['field']
        self.container = self.root.ids['basescreen']

    def make_active_or_inactive(self, item):
        item.active = True if not item.active else False

    def cb_handler(self, hlp, item):
        item2 = self.root.ids.stereo.ids.check_box if hlp == 'mono' else self.root.ids.mono.ids.check_box
        if not item.active:
            item.active = False
            item2.active = True
        else:
            item.active = True
            item2.active = False

    def stereo_or_mono(self, item, item2, item3=None):
        if item.active:
            item.active = False
            item2.active = True
        else:
            item.active = True
            item2.active = False

    def method(self):
        pass

    def dialog_process(self, action):
        if action:
            self.next_step += 1
        self.dialog.dismiss()

    def update_field_text(self):
        if not self.can_stop:
            self.field.text = self.prv_text

    def update_can_write_and_prv_text(self):
        if self.start_button.text == 'Stop recording':
            self.can_write = False
            if self.field.text != '':
                self.prv_text = self.field.text
        elif self.start_button.text == 'Start recording':
            self.can_write = True

    def make_wanna_stop_true(self):
        self.wanna_stop = True

    def transparent_circle(self, img, center, radius, color, thickness):
        center = tuple(map(int, center))
        rgb = [255 * c for c in color[:3]]  # convert to 0-255 scale for OpenCV
        alpha = color[-1]
        radius = int(radius)
        if thickness > 0:
            pad = radius + 2 + thickness
        else:
            pad = radius + 3
        roi = slice(center[1] - pad, center[1] + pad), slice(center[0] - pad, center[0] + pad)

        try:
            overlay = img[roi].copy()
            cv2.circle(img, center, radius, rgb, thickness=thickness, lineType=cv2.LINE_AA)
            opacity = alpha
            cv2.addWeighted(src1=img[roi], alpha=opacity, src2=overlay, beta=1. - opacity, gamma=0, dst=img[roi])
        except Exception as e:
            print(e)

    def start_recording(self):
        self.can_stop = False
        self.wanna_stop = False
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(f'{os.path.join("recordings", "".join(["tmp", ".mp4v"]))}',
                              fourcc, 20.0, (self.screen_size))

        while True:
            data = cv2.cvtColor(np.array(pg.screenshot()), cv2.COLOR_BGR2RGB)
            _xs, _ys = GetCursorPos()
            self.transparent_circle(data, (_xs, _ys), 20, (0, 255, 255, 0.5), -1)
            out.write(data)
            if self.wanna_stop:
                cv2.destroyAllWindows()
                out.release()
                break
        if self.file_name[-1] != '.mp4v':
            self.add_and_start_progressbar(self.file_name[-1])
            subprocess.call(f'python video_encoder.py -n {self.file_name[0]} -ex {self.file_name[-1]}')
            self.delete_progressbar()
        else:
            shutil.copy(os.path.join("recordings", "".join(["tmp", ".mp4v"])),
                        os.path.join("recordings", "".join([self.file_name[0], ".mp4v"])))

        self.start_button.text = 'Start recording'
        self.update_can_write_and_prv_text()
        self.snackbar_show(0)
        self.can_stop = True

    def show_dialog_if_need(self):
        if self.next_step == 1:
            if ''.join([self.field.text.strip(),
                        self.file_name[-1] if self.file_name[-1] else '.mp4']) == self.prv_dialog_file:
                print('OK')
                self.next_step += 1
            else:
                print('Wrong file')
                self.next_step = 0
                ex = self.file_name[-1] if self.file_name[-1] else '.mp4'
                file_name = ''.join([self.field.text.strip(), ex])
                if file_name in os.listdir('recordings'):
                    print('Wrong file in recordings')
                    self.prv_dialog_file = file_name
                    self.dialog.text = self.dialog_text.format(file_name)
                    self.dialog.open()
                else:
                    print('Valid wrong file')
                    self.next_step = 2

        else:
            ex = self.file_name[-1] if self.file_name[-1] else '.mp4'
            if self.start_button.text == 'Start recording':
                file_name = ''.join([self.field.text.strip(), ex])
                if file_name in os.listdir('recordings'):
                    self.prv_dialog_file = file_name
                    self.dialog.text = self.dialog_text.format(file_name)
                    self.dialog.open()
                else:
                    self.next_step = 2

    def add_and_start_progressbar(self, ex):
        progress_bar = MDProgressBar(type='determinate', running_duration=1,
                                     catching_duration=1.5,
                                     pos_hint={'center_y': .75})
        md_label = MDLabel(text=f'Converting .mp4v to {ex}', halign='center', pos_hint={'center_y': .80})
        self.container.add_widget(progress_bar)
        self.container.add_widget(md_label)
        progress_bar.start()
        self.root.ids['progressbar'] = progress_bar
        self.root.ids['md_label'] = md_label

    def delete_progressbar(self):
        self.container.remove_widget(self.root.ids['progressbar'])
        self.container.remove_widget(self.root.ids['md_label'])

    def set_item(self, instance_menu, instance_menu_item):
        self.file_name[-1] = instance_menu_item.text
        self.screen.ids.drop_item.set_item(instance_menu_item.text)
        self.menu.dismiss()

    def check_menu(self):
        if self.start_button.text == 'Start recording':
            self.menu.open()

    def check_rc(self):
        self.next_step = 0
        if self.start_button.text == 'Start recording':
            self.can_stop = False
            self.start_button.text = 'Stop recording'
            self.update_can_write_and_prv_text()
            if self.field.text.strip() != '':
                self.file_name[0] = self.field.text.strip()
            else:
                self.file_name[0] = self.get_name()
                self.prv_text = self.file_name[0]
                self.field.text = self.file_name[0]
            if not self.file_name[-1]:
                self.file_name[-1] = '.mp4'
            self.snackbar_show(1)
            t = threading.Thread(target=self.start_recording, daemon=True)
            t.start()

    def check_validate(self):
        self.next_step = 0
        if self.start_button.text == 'Start recording':
            self.can_stop = False
            self.start_button.text = 'Stop recording'
            self.update_can_write_and_prv_text()
            if self.field.text.strip() != '':
                self.file_name[0] = self.field.text.strip()
            else:
                self.file_name[0] = self.get_name()
                self.prv_text = self.file_name[0]
                self.field.text = self.file_name[0]
            if not self.file_name[-1]:
                self.file_name[-1] = '.mp4'
            t = threading.Thread(target=self.start_recording)
            t.start()
            self.snackbar_show(1)

    def snackbar_show(self, start):
        file_name = ''.join(self.file_name)
        if start:
            text = 'Recording has been started'
            text_2 = f'File name: {file_name}'
        else:
            text = 'Recording has been stopped'
            text_2 = f'File name: {file_name}'
        CustomSnackbar(
            text=text,
            text_2=text_2,
            icon="information",
            padding="20dp",
        ).show()

    def get_name(self):
        suffixes = '|'.join(['mp4', 'mov', 'avi', 'mp4v'])
        pattern = re.compile(fr"(^recording_\d+)(\.{suffixes}$)")
        data = [i for i in os.listdir('recordings') if pattern.match(i)]
        values = []
        for i in data:
            i = re.findall(r'(.*)(\..*)', i)[0][0]
            values.append(int(''.join(re.findall(r'\d*', i))))
        if values != list():
            return f'recording_{max(values) + 1}'
        return 'recording_0'

    def build(self):
        self.title = 'video recording app'
        return self.screen


Test().run()
