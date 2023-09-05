from socket import *
import llmlty
import asyncio
import socketsto
import json
import sounddevice as sd
from scipy.io.wavfile import read
import os
import threading
import azurelty
import time

def play_wav(file_path, sleep_in, sleep_out):
    try:
        time.sleep(sleep_in)
        sd.default.device[1] = 6
        fs, data = read(file_path)
        sd.play(data, fs)
        sd.wait()
        time.sleep(sleep_out)
    except Exception as e:
        print(f"Wrong File:{e}")

async def main():
    with open("S:/Code/LangChain/confg.json", "r",encoding='utf-8') as jsonfile:
        config_data = json.load(jsonfile)
    
    initial_wav = os.path.join(config_data["abs_path"], config_data["sound_files"]["initial"])
    start_wav = os.path.join(config_data["abs_path"], config_data["sound_files"]["start"])
    stop_wav = os.path.join(config_data["abs_path"], config_data["sound_files"]["stop"])

    client_out = socketsto.SocketsTo(config_data['self_IP'], config_data['self_PORT'], config_data['proxy'])
    llm = llmlty.llmLTY(config_data)
    
    client_out.connect_with()

    client_out.sending('wait')
    thread = threading.Thread(target=play_wav, args=(initial_wav,0,0,))
    thread.start()
    # print("kkk")
    llm.initial(client_out)
    while client_out.connect_flag:
        client_out.sending('initialed')
        client_out.wake_up()
        llm.flushmemory()
        while llm.memory_flag:
            thread = threading.Thread(target=play_wav, args=(start_wav,2,0))
            thread.start()
            client_out.receving()
            if not client_out.connect_flag:
                break
            else:
                client_out.sending('wait')
                thread = threading.Thread(target=play_wav, args=(stop_wav,1.5,0))
                thread.start()
                if client_out.recvdata.__contains__('再见'):
                    llm.memory_flag = False
                    client_out.sending('loopout')
                    llm.input_ask(client_out.recvdata)
                else:
                    llm.input_ask(client_out.recvdata)
                    client_out.sending('finish')
    
    llm.close()

asyncio.run(main())
