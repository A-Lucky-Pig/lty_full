import os
import json
import snowboydecoder
import sys
import signal
import recon
import threading
import queue
import time
import alsaaudio
import sounddevice as sd 
import sherpa_ncnn
import asyncio
import re
import struct
import socketsto

running = True

class recon_thread(threading.Thread):
    def __init__(self, que, server_in, config_data):
        super().__init__()
        self.que = que
        self.server_in = server_in
        self.config_data = config_data
        
    def run(self) -> None:
        self.que.put(1)
        recon.sherpa(self.server_in, self.config_data)
        self.que.get()
        self.que.task_done()  
    
class detect_thread(threading.Thread):
    def __init__(self, que, sensitivity, hotwords_path):
        super().__init__()
        self.interrupted = False
        self.que = que
        self.sensitivity = sensitivity
        self.hotwords_path = hotwords_path

    def get_hotwords(self):
        words_list = os.listdir(self.hotwords_path)
        hot_words = [os.path.join(self.hotwords_path , s) for s in words_list]
        hot_words.sort()
        return hot_words

    #定义一个函数detectedCallback，用来在检测到热词时进行处理
    def detectedCallback(self):
        print('正在录制音频...', flush=True)
        self.que.get()
        self.interrupted = True
    
    def exitdetectedCallback(self):
        global running
        print('关机中...', flush=True)
        self.que.get()
        running = False
        self.interrupted = True

    def interrupt_callback(self):
        return self.interrupted

    def run(self) -> None:
        self.que.put(1)
        models = self.get_hotwords()
        m_num = len(models)

        #创建热词检测器对象detector，设置灵敏度
        detector = snowboydecoder.HotwordDetector(models, sensitivity = self.sensitivity)
        print('正在监听... 按Ctrl+C退出')

        #主循环, jarvis.umdl 里面包含两个词，好坑...
        detector.start(detected_callback=[self.detectedCallback, self.detectedCallback, self.exitdetectedCallback, self.detectedCallback, self.detectedCallback],
                    interrupt_check=self.interrupt_callback,
                    sleep_time=0.03)

        #结束检测器
        print('结束snowboy')
        detector.terminate()
        self.que.task_done()

if __name__ == "__main__":

    with open("confg.json", "r",encoding='utf-8') as jsonfile:
        config_data = json.load(jsonfile)

    que = queue.Queue(maxsize=100)
    server_pi = socketsto.SocketsTo(config_data['self_IP'], config_data['self_PORT'], config_data['proxy'])
    server_pi.server_in()
    server_pi.sending('start')

    server_pi.connect_flag = True

    while server_pi.connect_flag:
        while True:
            server_pi.receving()
            if server_pi.recvdata.__contains__('initialed'):
                break
        d_thread = detect_thread(que, config_data['snowboy_hotwords']['sensitivity'], config_data['snowboy_hotwords']['path'])
        d_thread.start()
        que.join()
        if not running:
            server_pi.sending('exit')
            server_pi.client_close()
            server_pi.server_close()
            break
        elif que.empty() and running:
            r_thread = recon_thread(que,server_pi, config_data)
            r_thread.start()
            que.join()
            # print(que.empty())