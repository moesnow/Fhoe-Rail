import time
import os
import cv2 as cv
import numpy as np
import pyautogui
import win32api
import win32con
import win32gui
import random
import atexit
from datetime import datetime
from PIL import ImageGrab
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key as KeyboardKey

from .config import ConfigurationManager
from .exceptions import Exception
from .log import log
from .mini_asu import ASU
from .switch_window import switch_window
from .pause import Pause

class Calculated:
    def __init__(self):
        self.cfg = ConfigurationManager()
        atexit.register(self.error_stop)
        win32api.SetConsoleCtrlHandler(self.error_stop, True)
        self._config = None
        self._last_updated = None
        self.keyboard = KeyboardController()
        self.ASU = ASU()
        self.hwnd = win32gui.FindWindow("UnityWndClass", "崩坏：星穹铁道")
        self.winrect = ()  # 截图窗口范围
        self.have_monthly_pass = False  # 标志是否领取完月卡
        self.monthly_pass_success = False  # 标志是否成功执行月卡检测
        self.temp_screenshot = ()  # 初始化临时截图
        self.last_check_time = None  # 月卡检测时间
        
        # 识别图片初始化
        self.main_ui = cv.imread("./picture/finish_fighting.png")
        self.doubt_ui = cv.imread("./picture/doubt.png")
        self.warn_ui = cv.imread("./picture/warn.png")
        self.finish2_ui = cv.imread("./picture/finish_fighting2.png")
        self.finish2_1_ui = cv.imread("./picture/finish_fighting2_1.png")
        self.finish2_2_ui = cv.imread("./picture/finish_fighting2_2.png")
        self.finish3_ui = cv.imread("./picture/finish_fighting3.png")
        self.finish4_ui = cv.imread("./picture/finish_fighting4.png")
        self.finish5_ui = cv.imread("./picture/finish_fighting5.png")
        
        self.attack_once = False  # 检测fighting时仅攻击一次，避免连续攻击
        self.esc_btn = KeyboardKey.esc  # esc键
        self.shift_btn = KeyboardKey.shift_l  # shift左键
        self.alt_btn = KeyboardKey.alt_l  # alt左键
        
        self.total_fight_time = 0  # 总计战斗时间
        self.error_fight_cnt = 0  # 异常战斗<3秒的计数
        self.error_fight_threshold = 3  # 异常战斗为战斗时间<3秒
        self.tatol_save_time = 0  # 疾跑节约时间
        self.total_fight_cnt = 0  # 战斗次数计数
        self.total_no_fight_cnt = 0  # 非战斗次数计数
    
    def error_stop(self, signum=None, frame=None):
        for i in [self.shift_btn, self.alt_btn]:
            self.keyboard.release(i)

    def _check_window_visibility(self, depth=0):
        """
        检查窗口是否可见
        """
        if not self.hwnd:
            self.get_hwnd()
        if self.hwnd and win32gui.IsWindowVisible(self.hwnd):
            return True
        else:
            if depth >= 3:
                log.info("尝试次数过多，程序退出。")
                return False
            cnt = 1
            while cnt < 3:
                time.sleep(1)
                log.info(f'窗口不可见或窗口句柄无效，窗口句柄为：{self.hwnd}，尝试重新查找窗口 {cnt} 次')
                self.get_hwnd()
                if self.hwnd:
                    switch_window()
                    return True
                else:
                    cnt += 1
            else:
                # 等待用户输入回车键继续
                input("未找到星铁窗口，请打开星铁，进入游戏界面后，输入回车键继续")
                time.sleep(1)
                return self._check_window_visibility(depth + 1)

    def get_hwnd(self, hwnd_max_retries=10):
        for _ in range(hwnd_max_retries):
            try:
                self.hwnd = win32gui.FindWindow("UnityWndClass", "崩坏：星穹铁道")
                if self.hwnd:
                    return
                time.sleep(2)
            except Exception as e:
                log.info(f'查找窗口失败，{e}')
                time.sleep(2)

        raise Exception("无法找到窗口，已达到最大重试次数")

    def get_rect(self, hwnd=None):
        """
        获取窗口截图的范围
        """
        if hwnd is None:
            if self.hwnd is None:
                self.get_hwnd()
            hwnd = self.hwnd
        if hwnd:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            self.winrect = (left, top, right, bottom)
        
        return left, top, right, bottom

    def click(self, points, slot=0):
        """
        说明：
            点击指定屏幕坐标
        参数：
            :param points: 坐标
        """
        x, y = int(points[0]), int(points[1])
        if not slot:
            log.info(f"点击坐标{(x, y)}")
        else:
            log.info(f"点击坐标{(x, y)}，坐标来源图片匹配度{slot:.3f}")
        self.mouse_press(x, y)

    def keyboard_press(self, key_name: str, delay: float=0): 
        """
        按下键盘后延迟抬起
        """
        self.keyboard.press(key_name)
        time.sleep(delay)
        self.keyboard.release(key_name)

    def mouse_press(self, x, y, end_x=None, end_y=None, delay: float = 0.05):
        """
        说明：
            鼠标点击
        参数：
            :param x: 起始点相对坐标x
            :param y: 起始点相对坐标y
            :param end_x: 目标终点相对坐标x，默认为 None
            :param end_y: 目标终点相对坐标y，默认为 None
            :param delay: 鼠标点击与抬起之间的延迟（秒）
        """
        # 如果没有提供目标终点的坐标，则默认终点为初始点击位置
        if end_x is None:
            end_x = x
        if end_y is None:
            end_y = y
        win32api.SetCursorPos((x, y))
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(delay)
        win32api.SetCursorPos((end_x, end_y))
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def mouse_drag(self, x, y, end_x, end_y):
        """
        说明：
            鼠标按下后拖动
        """
        left, top, right, bottom =self.get_rect()
        pyautogui.moveTo(left + x, top + y)
        pyautogui.mouseDown()
        pyautogui.moveTo(left + end_x, top + end_y, duration=0.2)
        pyautogui.mouseUp()
        time.sleep(1)

    def mouse_press_alt(self, x, y, delay: float=0.4):
        """
        说明：
            按下alt同时鼠标点击指定坐标
        参数：
            :param x:相对坐标x
            :param y:相对坐标y
        """
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        self.mouse_press(x, y, delay)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)

    def relative_click(self, points):
        """
        说明：
            点击相对坐标
        参数：
            :param points: 百分比坐标，100为100%
        """
        if self._check_window_visibility():
            left, top, right, bottom = self.get_rect()
            # real_width = self.cfg.CONFIG["real_width"]  # 暂时没用
            # real_height = self.cfg.CONFIG["real_height"]  # 暂时没用
            x, y = int(left + (right - left) / 100 * points[0]), int(top + (bottom - top) / 100 * points[1])
            log.info((x, y))
            self.mouse_press_alt(x, y)

    def click_center(self):
        """
        点击游戏窗口中心位置
        """
        if self._check_window_visibility():
            left, top, right, bottom = self.get_rect()
            x, y = int((left + right) / 2), int((top + bottom) / 2)
            self.mouse_press(x, y)

    def cal_screenshot(self):
        """
        计算窗口截图范围
        """
        left, top, right, bottom = self.get_rect()
        # 计算初始边框
        width = right - left
        height = bottom - top
        other_border = (width - 1920) // 2
        up_border = height - 1080 - other_border
        # 计算窗口截图范围
        screenshot_left = left + other_border
        screenshot_top = top + up_border
        screenshot_right = right - other_border
        screenshot_bottom = bottom - other_border
        
        return screenshot_left, screenshot_top, screenshot_right, screenshot_bottom

    def match_screenshot(self, screenshot, prepared, left, top):
        """
        说明：
            比对screenshot与prepared，返回匹配值与位置
        参数：
            :param screenshot:屏幕截图图片
            :param prepared:比对图片
            :param left:截图左侧坐标，用于计算真实位置
            :param top:截图上方坐标，用于计算真实位置
        """
        result = cv.matchTemplate(screenshot, prepared, cv.TM_CCORR_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
        return {
            "screenshot": screenshot,
            "min_val": min_val,
            "max_val": max_val,
            "min_loc": (min_loc[0] + left, min_loc[1] + top),
            "max_loc": (max_loc[0] + left, max_loc[1] + top),
        }

    def have_screenshot(self, prepared, offset=(0,0,0,0), threshold=0.90):
        """
        说明：
            验证图片是否符合要求
        """
        result_dict = self.scan_screenshot(prepared, offset)
        max_val = result_dict['max_val']
        if max_val > threshold:
            log.info(f'找到图片，匹配值：{max_val:.3f}')
            return True
        else:
            return False

    def take_screenshot(self, offset=(0,0,0,0), max_retries=50, retry_interval=2):
        """
        说明：
            获取游戏窗口的屏幕截图
        参数：
            :param offset: 左、上、右、下，正值为向右或向下偏移
            :param max_retries: 最大重试次数
            :param retry_interval: 重试间隔（秒）
        """
        if self._check_window_visibility():
            screenshot_left, screenshot_top, screenshot_right, screenshot_bottom = self.cal_screenshot()
            
            # 计算偏移截图范围
            new_left = screenshot_left + offset[0]
            new_top = screenshot_top + offset[1]
            new_right = screenshot_right + offset[2]
            new_bottom = screenshot_bottom + offset[3]
            # 偏移有效则使用偏移值
            if all([new_left < new_right, new_top < new_bottom]):
                screenshot_left, screenshot_top, screenshot_right, screenshot_bottom = new_left, new_top, new_right, new_bottom
            else:
                log.info(f'截图区域无效，偏移值错误({offset[0]},{offset[1]},{offset[2]},{offset[3]})，将使用窗口截图')
            
            retries = 0
            while retries <= max_retries:
                try:
                    picture = ImageGrab.grab((screenshot_left, screenshot_top, screenshot_right, screenshot_bottom), all_screens=True)
                    screenshot = np.array(picture)
                    screenshot = cv.cvtColor(screenshot, cv.COLOR_BGR2RGB)
                    self.temp_screenshot = screenshot, screenshot_left, screenshot_top, screenshot_right, screenshot_bottom
                    return screenshot, screenshot_left, screenshot_top, screenshot_right, screenshot_bottom
                except Exception as e:
                    log.info(f"截图失败，原因: {str(e)}，等待 {retry_interval} 秒后重试")
                    retries += 1
                    time.sleep(retry_interval)
            raise RuntimeError(f"截图尝试失败，已达到最大重试次数 {max_retries} 次）")

    def scan_screenshot(self, prepared, offset=(0,0,0,0)) -> dict:
        """
        说明：
            比对图片
        参数：
            :param prepared: 比对图片地址
            :param offset: 左、上、右、下，正值为向右或向下偏移
        """
        screenshot, left, top, right, bottom = self.take_screenshot(offset=offset)
        
        return self.match_screenshot(screenshot, prepared, left, top)

    def scan_temp_screenshot(self, prepared):
        """
        说明：
            使用临时截图数据进行扫描匹配
        参数：
            :param prepared: 比对图片地址
        """
        if not self.temp_screenshot:
            self.take_screenshot()
        
        screenshot, left, top, right, bottom = self.temp_screenshot
        
        return self.match_screenshot(screenshot, prepared, left, top)

    def calculated(self, result, shape):
        mat_top, mat_left = result["max_loc"]
        prepared_height, prepared_width, prepared_channels = shape

        x = int((mat_top + mat_top + prepared_width) / 2)
        y = int((mat_left + mat_left + prepared_height) / 2)

        return x, y

    def img_trans_bitwise(self, target_path):
        """
        颜色反转
        """
        original_target = cv.imread(target_path)
        inverted_target = cv.bitwise_not(original_target)
        result = self.scan_screenshot(inverted_target)
        return inverted_target, result
        
    def img_bitwise_check(self, target_path):
        """
        比对颜色反转
        """
        original_target = cv.imread(target_path)
        target,  result_inverted = self.img_trans_bitwise(target_path)
        result_original = self.scan_screenshot(original_target)
        log.info(f"颜色反转后的匹配值为：{result_inverted['max_val']}")
        if result_original["max_val"] > result_inverted["max_val"]:
            return True
        else:
            return False
    
    def click_target_above_threshold(self, target, threshold, offset):
        """
        尝试点击匹配度大于阈值的目标图像。
        参数:
            :param target: 目标图像
            :param threshold: 匹配阈值
            :param offset: 左、上、右、下，正值为向右或向下偏移
        返回:
            :return: 是否点击成功
        """
        result = self.scan_screenshot(target, offset)
        if result["max_val"] > threshold:
            points = self.calculated(result, target.shape)
            self.click(points, result['max_val'])
            return True
        return False


    def click_target(self, target_path, threshold, flag=True, timeout=30, offset=(0,0,0,0)):
        """
        说明：
            点击指定图片
        参数：
            :param target_path:图片地址
            :param threshold:匹配阈值
            :param flag:True为一定要找到图片
            :param timeout: 最大搜索时间（秒）
            :param offset: 左、上、右、下，正值为向右或向下偏移
        返回：
            :return 是否点击成功
        """
        # 定义目标图像与颜色反转后的图像
        original_target = cv.imread(target_path)
        inverted_target = cv.bitwise_not(original_target)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.click_target_above_threshold(original_target, threshold, offset):
                return True
            if time.time() - start_time > 5:  # 如果超过5秒，同时匹配原图像和颜色反转后的图像
                if self.click_target_above_threshold(inverted_target, threshold, offset):
                    log.info("阴阳变转")
                    return True
            if not flag:  # 是否一定要找到
                return False
            time.sleep(1)  # 添加短暂延迟避免性能消耗
        else:
            log.info(f"查找图片超时 {target_path}")
            return False
            
    def click_target_with_alt(self, target_path, threshold, flag=True):
        """
        说明：
            按下alt，点击指定图片，释放alt
        参数：
            :param target_path:图片地址
            :param threshold:匹配阈值
            :param flag:True为一定要找到图片
        """
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        self.click_target(target_path, threshold, flag)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)

    def detect_fight_status(self, timeout=5):
        start_time = time.time()
        action_executed = False
        self.attack_once = False
        log.info("开始识别是否进入战斗")
        while time.time() - start_time < timeout:
            main_result = self.scan_screenshot(self.main_ui, offset=(0,0,-1630,-800))
            doubt_result = self.scan_temp_screenshot(self.doubt_ui)
            warn_result = self.scan_temp_screenshot(self.warn_ui)
            if main_result['max_val'] < 0.9:
                return True
            elif doubt_result["max_val"] > 0.92:
                action_executed = self.click_action(is_warning=False)
            # elif warn_result["max_val"] > 0.9:
            #     action_executed = self.click_action(is_warning=True)
            if action_executed:
                return action_executed
            time.sleep(0.5)
        log.info(f"结束识别，识别时长{timeout}秒，此处可能无敌人")
        return False

    def click_action(self, is_warning, timeout=8):
        if is_warning:
            log.info("识别到警告，等待怪物开战")
        else:
            log.info("识别到疑问，等待怪物开战")

        time.sleep(2)
        if not self.attack_once:
            self.click_center()
            self.attack_once = True
        start_time = time.time()
        while time.time() - start_time < timeout:
            main_result = self.scan_screenshot(self.main_ui)
            if main_result['max_val'] < 0.9:
                return True
            time.sleep(0.5)

    def fight_error_cnt(self, elapsed_time: int):
        """
        检测异常战斗
        """
        if elapsed_time < self.error_fight_threshold:
            self.error_fight_cnt += 1
        
    def fight_elapsed(self):
        """战斗时间

        返回：
            是否识别到敌人
        """
        detect_fight_status_time = self.cfg.CONFIG.get("detect_fight_status_time", 15)
        fight_status = self.detect_fight_status(timeout=detect_fight_status_time)
        if not fight_status:
            # 结束识别，此处可能无敌人
            return False

        start_time = time.time()
        log.info(f"战斗开始")
        not_auto = cv.imread("./picture/auto.png")
        not_auto_c = cv.imread("./picture/not_auto.png")
        auto_switch = False
        auto_switch_clicked = False
        auto_check_cnt = 0
        screenshot_auto_check = None
        while True:
            result = self.scan_screenshot(self.main_ui)
            elapsed_time = time.time() - start_time
            if result["max_val"] > 0.92:
                points = self.calculated(result, self.main_ui.shape)
                log.info(f"识别点位{points}")
                self.total_fight_time += elapsed_time
                self.fight_error_cnt(elapsed_time)
                elapsed_minutes = int(elapsed_time // 60)
                elapsed_seconds = elapsed_time % 60
                formatted_time = f"{elapsed_minutes}分钟{elapsed_seconds:.2f}秒"
                self.total_fight_cnt += 1
                colored_message = (f"战斗完成,单场用时\033[1;92m『{formatted_time}』\033[0m")
                log.info(colored_message)
                match_details = f"匹配度: {result['max_val']:.2f} ({points[0]}, {points[1]})"
                log.info(match_details)

                self.rotate()
                while not self.on_main_interface(timeout=2):
                    time.sleep(0.1)
                time.sleep(1)
                return True

            if not auto_switch and elapsed_time > 5:
                not_auto_result = self.scan_screenshot(not_auto)
                if not_auto_result["max_val"] > 0.95:
                    pyautogui.press('v')
                    log.info("开启自动战斗")
                    time.sleep(1)
                    auto_switch_clicked = True
    
                auto_switch = True
            
            if elapsed_time > 10 and auto_check_cnt < 2:
                if screenshot_auto_check is None:
                    screenshot_auto_check, *_ = self.take_screenshot(offset=(40,20,-1725,-800))
                if elapsed_time > 15:
                    if auto_check_cnt == 0:
                        first_auto_check = self.on_interface(check_list=[screenshot_auto_check],timeout=1,threshold=0.97,offset=(40,20,-1725,-800),allow_log=False)
                        auto_check_cnt += 1
                    if elapsed_time > 20 and first_auto_check and auto_check_cnt == 1:
                        auto_check_cnt += 1
                        if self.on_interface(check_list=[screenshot_auto_check],timeout=1,threshold=0.97,offset=(40,20,-1725,-800),allow_log=False):
                            pyautogui.press('v')
                            log.info("开启自动战斗（通过行动条识别）")
                            time.sleep(1)
                            auto_switch_clicked = True

            if auto_switch_clicked and auto_switch and elapsed_time > 10:
                not_auto_result_c = self.scan_screenshot(not_auto_c)
                while not_auto_result_c["max_val"] > 0.95:
                    log.info(f"开启自动战斗，识别'C'，匹配值：{not_auto_result_c['max_val']}")
                    pyautogui.press('v')
                    time.sleep(2)
                    not_auto_result_c = self.scan_screenshot(not_auto_c)

            if elapsed_time > 90:
                # self.click_target("./picture/auto.png", 0.98, False)
                self.click_target("./picture/continue_fighting.png", 0.98, False)
                self.click_target("./picture/defeat.png", 0.98, False)
                # self.click_target("./picture/map_4-2_point_3.png", 0.98, False)
                # self.click_target("./picture/orientation_close.png", 0.98, False)
                if elapsed_time > 600:
                    log.info("战斗超时")
                    return True
            time.sleep(0.5)

    def fighting(self):
        self.click_center()
        fight_status = self.fight_elapsed()

        if not fight_status:
            self.total_no_fight_cnt += 1
            log.info(f'未进入战斗')
            time.sleep(0.5)


    def fightE(self, value):
        """
        使用'E'攻击，补充秘技点数
        """
        image_A = cv.imread("./picture/eat.png")
        pyautogui.press('e')
        start_time = time.time()
        result_A = None
        time.sleep(1)
        while result_A is None and time.time() - start_time < 3:
            result_A = self.scan_screenshot(image_A)
        if result_A is not None and result_A["max_val"] > 0.9:
            time.sleep(1)
            round_disable = cv.imread("./picture/round_disable.png")
            if self.on_interface(check_list=[round_disable], timeout=5, interface_desc='无法购买', threshold=0.95):
                allow_buy = False
            else:
                self.click_target("./picture/round.png", 0.9, timeout=8)
                allow_buy = True
            main_result = self.scan_screenshot(self.main_ui)
            while main_result['max_val'] < 0.9:
                self.keyboard_press(self.esc_btn)
                time.sleep(1)
                main_result = self.scan_screenshot(self.main_ui)
            if allow_buy:
                pyautogui.press('e')
            time.sleep(1)

        if value == 1:
            self.click_center()
            fight_status = self.fight_elapsed()
            if not fight_status:
                log.info(f'未进入战斗')
        elif value == 2:
            pass

        time.sleep(0.5)



    def rotate(self):
        if self.need_rotate:
            self.keyboard_press('w')
            time.sleep(0.7)
            self.ASU.screen = self.take_screenshot()[0]
            ang = self.ang - self.ASU.get_now_direc()
            ang = (ang + 900) % 360 - 180
            self.mouse_move(ang * 10.2)
    
    def check_f_img(self, timeout=60):
        """
        检查F的交互类型。
        
        :return: tuple, 包含三个元素：(是否使用绝对时间, 绝对时间的值（秒）, 是否允许按下F)
        """
        images = {
            'target': cv.imread("./picture/sw.png"),
            'dream_pop': cv.imread("./picture/F_DreamPop.png"),
            'teleport': cv.imread("./picture/F_Teleport.png"),
            'space_anchor': cv.imread("./picture/F_SpaceAnchor.png")
        }
        
        start_time = time.time()
        log.info("扫描'F'图标")

        default_delay = 10
        found_images = {}

        while time.time() - start_time < timeout:
            for count , (name, img) in enumerate(images.items(), start = 1):
                result = self.scan_screenshot(img) if count == 1 else self.scan_temp_screenshot(img)
                if result['max_val'] > 0.96:
                    found_images[name] = result['max_val']
                    log.info(f"扫描'F'：{name}，匹配度：{result['max_val']:.3f}")

            if len(found_images) == 2 or ('target' in found_images and time.time() - start_time >= 2):
                break

            time.sleep(0.5)

        return self.analyze_found_images(found_images, default_delay)

    def analyze_found_images(self, found_images, default_delay):
        """
        分析找到的图片，决定下一步

        :param found_images: dict, 找到的图片及其匹配度
        :param default_delay: int, 默认延迟时间
        :return: tuple, 包含三个元素：(是否使用绝对时间, 绝对时间的值（秒）, 是否允许按下F)
        """
        use_absolute_time = True
        delay = default_delay
        allow_press_f = True
        if 'target' in found_images:
            if 'dream_pop' in found_images:
                log.info('扫描到 梦泡充能')
                delay = 3
            elif 'teleport' in found_images:
                log.info('扫描到 入画')
                use_absolute_time = False
                delay = 0
            elif 'space_anchor' in found_images:
                log.info('扫描到 界域定锚')
                use_absolute_time = False
                delay = 0
                allow_press_f = False
            else:
                log.info("扫描到 'F'")
        else:
            log.info("扫描失败！")

        return use_absolute_time, delay, allow_press_f

    def auto_map(self, map, old=True, normal_run=False, rotate=False, dev=False, last_point=''):
        self.pause = Pause(dev=dev)
        map_version = self.cfg.CONFIG.get("map_version", "default")
        self.ASU.screen = self.take_screenshot()[0]
        self.ang = self.ASU.get_now_direc()
        self.need_rotate = rotate
        now = datetime.now()
        today_weekday_str = now.strftime('%A')
        map_data = self.cfg.read_json_file(f"map/{map_version}/{map}.json")
        map_filename = map
        self.fighting_count = sum(1 for map in map_data["map"] if "fighting" in map and map["fighting"] == 1)
        self.current_fighting_index = 0
        total_map_count = len(map_data['map'])
        self.first_role_check()  # 1号位为跑图角色
        dev_restart = True  # 初始化开发者重开
        while dev_restart:
            dev_restart = False  # 不进行重开
            for map_index, map_value in enumerate(map_data["map"]):
                press_key = self.pause.check_pause(dev, last_point)
                if press_key:
                    if press_key == 'F8':
                        pass
                    else:
                        dev_restart = True  # 检测到需要重开
                        switch_window()
                        time.sleep(1)
                        if press_key == 'F9':
                            self.click_target("picture\\transfer.png", 0.93)
                            self.run_mapload_check()
                        if press_key == 'F10':
                            pass
                        map_data = self.cfg.read_json_file(f"map/{map_version}/{map}.json")  # 重新读取最新地图文件
                        break
                log.info(f"执行{map_filename}文件:{map_index + 1}/{total_map_count} {map_value}")
                key, value = next(iter(map_value.items()))
                self.monthly_pass_check()  # 行进前识别是否接近月卡时间
                self._last_step_run = False  # 初始化上一次为走路
                if key == "space" or key == "r": 
                    self.handle_space_or_r(value, key)
                elif key == "f":
                    self.handle_f()
                elif key == "check" and value == 1:
                    self.handle_check(today_weekday_str)
                elif key == "mouse_move":
                    self.mouse_move(value)
                elif key == "fighting":
                    self.handle_fighting(value)
                elif key == "scroll":
                    self.scroll(value)
                elif key == "shutdown":
                    self.handle_shutdown()
                elif key == "e":
                    self.handle_e(value)  # 用E进入战斗
                elif key == "esc":
                    self.handle_esc(value)
                else:
                    self.handle_move(value, key, normal_run)

    def handle_space_or_r(self, value, key):
        random_interval = random.uniform(0.3, 0.7)
        num_repeats = int(value / random_interval)
        for _ in range(num_repeats):
            self.keyboard_press(key)
            time.sleep(random_interval)
        remaining_time = value - (num_repeats * random_interval)
        if remaining_time > 0:
            time.sleep(remaining_time)


    def handle_f(self):
        use_time, delay, allow_f = self.check_f_img()
        if allow_f:
            if use_time:
                self.keyboard_press('f', delay=0.1)
                log.info(f"按下'F'，等待{delay}秒")
                time.sleep(delay)
            else:
                self.keyboard_press('f', delay=0.1)
                log.info(f"按下'F'，等待主界面检测")
                time.sleep(2)  # 2 秒后开始检测主界面
                self.on_main_interface()
                time.sleep(2)  # 等待 2 秒加载人物
        else:
            log.info(f"检测到非正常'F'情况，不执行并跳过'F'")
                

    def handle_check(self, today_weekday_str):
        today_weekday_num = datetime.now().weekday()
        if today_weekday_num in [1, 4, 6]:  # 1代表周二，6代表周日
            log.info(f"{today_weekday_str}，周二五日，尝试购买")
        else:
            log.info(f"{today_weekday_str}，非周二五日，跳过")

    def handle_fighting(self, value):
        if value == 1:  # 战斗
            self.current_fighting_index += 1
            if self.cfg.CONFIG.get("auto_final_fight_e", False) and self.current_fighting_index == self.fighting_count:
                log.info(f"地图最后一个fighting:1，改为使用e")
                self.handle_e(value)
            else:
                self.fighting()
        elif value == 2:  # 打障碍物
            self.click(win32api.GetCursorPos())
            time.sleep(1)
        else:
            raise Exception(f"map数据错误, fighting参数异常")

    def handle_e(self, value):
        if value == 1:  
            self.fightE(value=1)
        elif value == 2:
            self.fightE(value=2)

    def handle_esc(self, value):
        if value == 1:
            win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
            time.sleep(random.uniform(0.09, 0.15))
            win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(3)
        else:
            raise Exception(f"map数据错误, esc参数只能为1")

    def handle_move(self, value, key, normal_run=False):
        if normal_run:
            log.info(f"强制关闭疾跑normal_run:{normal_run}")
        self.keyboard.press(key)
        start_time = time.perf_counter()
        allow_run = self.cfg.CONFIG.get("auto_run_in_map", False)
        add_time = True
        run_in_road = False
        while time.perf_counter() - start_time < value:
            if value > 2 and time.perf_counter() - start_time > 1 and not run_in_road and allow_run and not normal_run:
                self.keyboard.press(self.shift_btn)
                run_in_road = True
                temp_value = value
                value = round((value - 1) / 1.53, 4) + 1
                self.tatol_save_time += (temp_value - value)
                self._last_step_run = True
            elif value <= 1 and allow_run and add_time and self._last_step_run:
                value = value + 0.07
                add_time = False
                self._last_step_run = False
            elif value <= 2:
                self._last_step_run = False
            pass
        self.keyboard.release(self.shift_btn)
        self.keyboard.release(key)
        if allow_run:
            time.sleep(0.03)

    def mouse_move(self, x):
        scaling = 1.0
        dx = int(x * scaling)
        i = int(dx / 200)
        last = dx - i * 200

        # 视角移动的步长
        step = 200 if dx > 0 else -200

        for _ in range(abs(i)):
            win32api.mouse_event(1, step, 0)  # 进行视角移动
            time.sleep(0.1)

        if last != 0:
            win32api.mouse_event(1, last, 0)  # 进行视角移动

        time.sleep(0.5)

    def monthly_pass_check(self):
        # 获取当前时间
        current_time = datetime.now()

        # 如果当前时间在3点55分到4点之间，则等待直到4点
        if current_time.hour == 3 and 55 <= current_time.minute < 60:
            while datetime.now().hour == 3:
                time.sleep(2)
            else:
                current_time = datetime.now()  # 等待后重新赋值当前时间

        # 如果是首次运行或者距离上次检查已经过了凌晨4点且日期发生了变更，则需要执行一次月卡检查
        if self.last_check_time is None or \
                (self.last_check_time.date() < current_time.date() and current_time.hour >= 4) or \
                (self.last_check_time.hour < 4 and current_time.hour >= 4):
            # 如果当前时间大于上次检查时间，则执行一次月卡检查
            if self.last_check_time is None or current_time > self.last_check_time:
                self.try_click_pass()
            
            # 更新上次检查时间
            self.last_check_time = current_time
            log.info(f"月卡检查时间更新至：{self.last_check_time}")

    def monthly_pass(self):
        """
        说明：
            点击月卡。首先检查当前时间是否接近目标时间（凌晨4点前后），然后执行月卡点击操作。
            仅在while循环至少成功运行一次后，不再重复执行。
        """
        if self.monthly_pass_success:  # 月卡检查已完成，不再重复执行
            return
        
        start_time = time.time()
        target_time_str = datetime.now().strftime('%Y-%m-%d') + " 04:00:00"
        target_time_stamp = int(time.mktime(time.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")))
        current_time_stamp = int(start_time)
        time_period = current_time_stamp - target_time_stamp

        if -300 < time_period <= 300:  # 接近4点5分钟时开始等待点击月卡，超过4点5分钟内会点击月卡
            if -300 < time_period < 0:
                time.sleep(abs(time_period))  # 等待4点
            time.sleep(5)  # 延时，等待动画可能的加载
            self.try_click_pass()

    def try_click_pass(self, threshold=0.92, max_click_attempts=2):
        """
        说明：
            尝试点击月卡。
        """
        log.info("判断是否存在月卡")
        target = cv.imread("./picture/finish_fighting.png")
        result = self.scan_screenshot(target)
        if result["max_val"] > 0.92:
            points = self.calculated(result, target.shape)
            log.info(f"识别点位{points}")
            match_details = f"识别到此刻正在主界面，无月卡，图片匹配度: {result['max_val']:.2f} ({points[0]}, {points[1]})"
            log.info(match_details)
            self.monthly_pass_success = True  # 月卡检查完成，无月卡
            return

        log.info("准备点击月卡")
        monthly_pass_pic = cv.imread("./picture/monthly_pass_pic.png")
        result_monthly_pass = self.scan_screenshot(monthly_pass_pic)

        count = 0
        attempts_made = False

        while not self.have_monthly_pass and count < max_click_attempts:  # 月卡需要点击两次，1次领取，1次完成
            if result_monthly_pass["max_val"] > threshold:
                log.info("点击月卡")
                points_monthly_pass = self.calculated(result_monthly_pass, monthly_pass_pic.shape)
                self.click(points_monthly_pass)
                match_monthly_pass = f"识别到月卡，图片匹配度: {result_monthly_pass['max_val']:.2f} ({points_monthly_pass[0]}, {points_monthly_pass[1]})"
                log.info(match_monthly_pass)
                time.sleep(4)  # 等待动画修正到4秒
                attempts_made = True
                count += 1
                if count == max_click_attempts:
                    self.have_monthly_pass = True
                    break
            else:
                match_no_pass = f"找不到与月卡图片相符的图，图片匹配度：{result_monthly_pass['max_val']:.2f} 需要 > {threshold}"
                log.info(match_no_pass)
                self.monthly_pass_success = True  # 月卡检查，找不到与月卡图片相符的图
                break
            time.sleep(0.1)  # 稍微等待再次尝试

        if attempts_made:
            self.monthly_pass_success = True  # 月卡检查，已领取

    def scroll(self, clicks: float, arg1, _):
        """
        说明：
            控制鼠标滚轮滚动
        参数：
            :param clicks 滚动单位，正数为向上滚动
        """
        pyautogui.scroll(clicks)
        time.sleep(0.5)

    def blackscreen_check(self, threshold=10):
        """
        说明：
            检测是否黑屏
        """
        screenshot = cv.cvtColor(self.take_screenshot()[0], cv.COLOR_BGR2GRAY)
        current_param = cv.mean(screenshot)[0]
        if current_param < threshold:
            log.info(f'当前黑屏，值为{current_param:.3f} < {threshold}')
            return True

        return False

    def is_blackscreen(self, threshold=10):
        screenshot = cv.cvtColor(self.take_screenshot()[0], cv.COLOR_BGR2GRAY)

        if cv.mean(screenshot)[0] < threshold:  # 如果平均像素值小于阈值
            return True
        else:
            image_folder = "./picture/"
            finish_fighting_images = [f for f in os.listdir(image_folder) if f.startswith("finish_fighting")]
            attempts = 0
            max_attempts_ff1 = 3
            while attempts < max_attempts_ff1:
                for image_name in finish_fighting_images:
                    target = cv.imread(os.path.join(image_folder, image_name))
                    result = self.scan_screenshot(target)
                    if result and result["max_val"] > 0.9:
                        log.info(f"匹配到{image_name}，匹配度{result['max_val']:.3f}")
                        return False  # 如果匹配度大于0.9，表示不是黑屏，返回False
                attempts += 1
                time.sleep(2)  # 等待2秒再尝试匹配

        return True  # 如果未匹配到指定的图像，返回True

    def run_blackscreen_cal_time(self):
        """
        说明：
            黑屏时间
        """
        start_time = time.time()  
        while self.is_blackscreen():
            time.sleep(1)
        end_time = time.time()  # 记录黑屏加载完成的时间
        loading_time = end_time - start_time + 1
        
        return loading_time

    def run_mapload_check(self, error_count=0, max_error_count=10, threshold = 0.9):
        """
        说明：
            计算地图加载时间
        """
        start_time = time.time()
        target = cv.imread('./picture/map_load.png')
        time.sleep(1)  # 短暂延迟后开始判定是否为地图加载or黑屏跳转
        while error_count < max_error_count:
            result = self.scan_screenshot(target)
            if result and result['max_val'] > 0.95:
                log.info(f"检测到地图加载map_load，匹配度{result['max_val']}")
                if self.on_main_interface(check_list=[self.main_ui, self.finish2_ui, self.finish2_1_ui, self.finish2_2_ui, self.finish3_ui], timeout=10, threshold=threshold):
                    break
            elif self.blackscreen_check():
                self.run_blackscreen_cal_time()
                break
            elif self.on_main_interface(check_list=[self.main_ui, self.finish2_ui, self.finish2_1_ui, self.finish2_2_ui, self.finish3_ui], threshold=threshold):
                time.sleep(1)
                if self.on_main_interface(check_list=[self.main_ui, self.finish2_ui, self.finish2_1_ui, self.finish2_2_ui, self.finish3_ui], threshold=threshold):
                    log.info(f"连续检测到主界面，地图加载标记为结束")
                    break
            elif self.on_interface(check_list=[self.finish5_ui], timeout=3, interface_desc='模拟宇宙积分奖励界面'):
                time.sleep(1)
                if self.on_interface(check_list=[self.finish5_ui], timeout=3, interface_desc='模拟宇宙积分奖励界面'):
                    log.info(f"连续检测到模拟宇宙积分奖励界面，地图加载标记为结束")
                    break
            else:
                error_count += 1
                time.sleep(1)
                log.info(f'未查询到地图加载状态{error_count}次，加载图片匹配值{result["max_val"]:.3f}')
        else:
            log.info(f'加载地图超时，已重试{error_count}次，强制执行下一步')
        end_time = time.time()
        loading_time = end_time - start_time
        if error_count < max_error_count:
            log.info(f'地图载毕，用时 {loading_time:.1f} 秒')
        time.sleep(1)  # 增加1秒等待防止人物未加载错轴

    def run_dreambuild_check(self, error_count=0, max_error_count=10):
        """
        说明：
            筑梦模块移动模块加载时间
        """
        start_time = time.time()
        target = cv.imread('./picture/finish_fighting.png')
        time.sleep(3)  # 短暂延迟后开始判定
        while error_count < max_error_count:
            result = self.scan_screenshot(target)
            if result["max_val"] > 0.9:
                break
            else:
                error_count += 1
                time.sleep(1)
        end_time = time.time()
        loading_time = end_time - start_time
        if error_count >= max_error_count:
            log.info(f'移动模块加载超时，用时 {loading_time:.1f} 秒，识别图片匹配值{result["max_val"]:.3f}')
        else:
            log.info(f'移动模块成功，用时 {loading_time:.1f} 秒')
        time.sleep(0.5)  #短暂延迟后开始下一步

    def back_to_main(self):
        """
        检测并回到主界面
        """
        while not self.on_main_interface(timeout=2):  # 检测是否出现左上角灯泡，即主界面检测
            pyautogui.press('esc')
            time.sleep(2)
    
    def on_main_interface(self, check_list=[], timeout=60, threshold=0.9, offset=(0,0,0,0), allow_log=True):
        """
        说明：
            检测主页面
        参数：
            :param check_list:检测图片列表，默认检测左上角地图的灯泡，遍历检测
            :param timeout:超时时间（秒），超时后返回False
            :param threshold:识别阈值，默认0.9
        返回：
            是否在主界面
        """
        if check_list == []:
            check_list = [self.main_ui]
            offset=(0,0,-1630,-800)
        interface_desc = '游戏主界面，非战斗/传送/黑屏状态'
        
        return self.on_interface(check_list=check_list, timeout=timeout, interface_desc=interface_desc, threshold=threshold, offset=offset, allow_log=allow_log)

    def on_interface(self, check_list=[], timeout=60, interface_desc='', threshold=0.9, offset=(0,0,0,0),allow_log=True):
        """
        说明：
            检测check_list中的图片是否在某个页面
        参数：
            :param check_list:检测图片列表，默认为检测[self.main_ui]主界面左上角灯泡
            :param timeout:超时时间（秒），超时后返回False
            :param interface_desc:界面名称或说明，用于日志输出
        返回：
            是否在check_list存在的界面
        """
        start_time = time.time()
        if check_list == []:
            check_list = [self.main_ui]
        
        temp_max_val = []
        while time.time() - start_time < timeout:
            for index, img in enumerate(check_list):
                result = self.scan_screenshot(img, offset=offset)
                if result["max_val"] > threshold:
                    if allow_log:
                        log.info(f"检测到{interface_desc}，耗时 {(time.time() - start_time):.1f} 秒")
                        log.info(f"检测图片序号为{index}，匹配度{result['max_val']:.3f}，匹配位置为{result['max_loc']}")
                    return True
                else:
                    temp_max_val.append(result['max_val'])
                    time.sleep(0.2)
        else:
            if allow_log:
                log.info(f"在 {timeout} 秒 的时间内未检测到{interface_desc}，相似图片最高匹配值{max(temp_max_val):.3f}")
            return False

    def handle_shutdown(self):
        if self.cfg.CONFIG.get("auto_shutdown", False):
            log.info("下班喽！I'm free!")
            os.system("shutdown /s /f /t 0")
        else:
            log.info("锄地结束！")
    
    def allow_buy_item(self):
        """
        购买物品检测
        """
        round_disable = cv.imread("./picture/round_disable.png")
        if self.on_interface(check_list=[round_disable], timeout=5, interface_desc='无法购买', threshold=0.95):
            return False
        else:
            return True
    
    def first_role_check(self):
        """
        按下'1'，确认队伍中的1号位属于跑图角色
        """
        log.info("开始判断1号位")
        image, *_ = self.take_screenshot(offset=(1670,339,-160,-739))
        image_hsv = cv.cvtColor(image, cv.COLOR_RGB2HSV)

        # 定义HSV颜色范围
        color_ranges = [
            (np.array([28, 49, 253]), np.array([32, 189, 255])),
            (np.array([114, 240, 216]), np.array([116, 246, 226]))
        ]

        # 检查符合条件的像素
        for lower, upper in color_ranges:
            pixels = cv.inRange(image_hsv, lower, upper)
            if np.any(pixels):
                pyautogui.press('1')
                log.info("设置1号位为跑图角色")
                break