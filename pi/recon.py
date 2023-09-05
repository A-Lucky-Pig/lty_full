import sys
import sherpa_ncnn
from socket import *
import threading
import asyncio
import re
import struct
import socketsto
import time
import sounddevice as sd
import queue
import os

def create_recognizer(model_path, rule1, rule2, rule3):
    # Please replace the model files if needed.
    # See https://k2-fsa.github.io/sherpa/ncnn/pretrained_models/index.html
    # for download links.
    recognizer = sherpa_ncnn.Recognizer(
        tokens=os.path.join(model_path, 'tokens.txt'),
        encoder_param=os.path.join(model_path, 'encoder_jit_trace-pnnx.ncnn.param'),
        encoder_bin=os.path.join(model_path, 'encoder_jit_trace-pnnx.ncnn.bin'),
        decoder_param=os.path.join(model_path, 'decoder_jit_trace-pnnx.ncnn.param'),
        decoder_bin=os.path.join(model_path, 'decoder_jit_trace-pnnx.ncnn.bin'),
        joiner_param=os.path.join(model_path, 'joiner_jit_trace-pnnx.ncnn.param'),
        joiner_bin=os.path.join(model_path, 'joiner_jit_trace-pnnx.ncnn.bin'),
        num_threads=4,
        decoding_method="modified_beam_search",
        enable_endpoint_detection=True,
        rule1_min_trailing_silence=rule1,
        rule2_min_trailing_silence=rule2,
        rule3_min_utterance_length=rule3,
    )
    return recognizer

def soc_recv(server_in, comu_queue):
    while True:
        server_in.receving()
        back_message = server_in.recvdata
        # print("已收到"+back_message)
        if back_message.__contains__('loopout') or back_message.__contains__('exit'):
            break
        if back_message.__contains__('finish'):
            time.sleep(3)
        try:
            comu_queue.put(back_message)
        except Exception as res:
            print(res)

def start_recon(server_in, config_data):
    comu_queue = queue.Queue(maxsize=1000)

    soc_thread = threading.Thread(target=soc_recv, args=(server_in,comu_queue))
    soc_thread.start()
    comu_queue.put('finish')

    recognizer = create_recognizer(config_data['sherpa-ncnn']['path'], config_data['sherpa-ncnn']['rule1'],config_data['sherpa-ncnn']['rule2'], config_data['sherpa-ncnn']['rule3'])

    sample_rate = recognizer.sample_rate
    samples_per_read = int(0.1 * sample_rate)  # 0.1 second = 100 ms
    last_result = ""
    segment_id = 0
    flag = True
    zt = 0 # 0 wait 1 finish
    print("Started! Please speak")
    with sd.InputStream(channels=1, dtype="float32", samplerate=sample_rate) as s:
        while flag: 
            if not comu_queue.empty():
                tempstr = comu_queue.get()
                if tempstr.__contains__('wait'):
                    zt = 0
                elif tempstr.__contains__('finish'):
                    zt = 1
            
            samples, _ = s.read(samples_per_read)  # a blocking read
            samples = samples.reshape(-1)
            recognizer.accept_waveform(sample_rate, samples)

            is_endpoint = recognizer.is_endpoint

            result = recognizer.text

            if result and (last_result != result):
                last_result = result
                # print("\r{}:{}".format(segment_id, result), end="", flush=True)

            if is_endpoint:
                # print(zt)
                if result:
                    print("\r{}:{}".format(segment_id, result), flush=True)
                    segment_id += 1
                    if zt:
                        server_in.sending(result)
                if result.__contains__('关机'):
                    flag = False
                    server_in.sending('exit')
                    time.sleep(1)
                    server_in.client_close()
                    server_in.server_close()
                if result.__contains__('再见'):
                    flag = False
                    time.sleep(1)
                recognizer.reset()

def sherpa(server_in, config_data):
    server_in.sending('wake')
    
    devices = sd.query_devices()
    print(devices)
    device_input_index = 0
    for t in devices:
        if t['name'] == 'default':
            break
        device_input_index += 1
#    target_device_idx = int(input('your want device index:'))
    sd.default.device[0] = device_input_index
    default_input_device_idx = sd.default.device[0]
    print(f'Use default device: {devices[default_input_device_idx]["name"]}')
    start_recon(server_in, config_data)