import azure.cognitiveservices.speech as speechsdk
import numpy as np
import os 

class Azureczz():
    def __init__(self, config_data) -> None:
        self.speech_synthesizer = None
        self.connection = None
        self.finish_flag = False
        self.count = 0
        # self.times = 0
        self.speech_config = None
        self.audio_config = None
        self.name = config_data["azure"]["name"]
        self.pitch = config_data["azure"]["pitch"]
        self.leading_silence = config_data["azure"]["leading_silence"]
        self.volume = config_data["azure"]["volume"]
        self.speech_key = config_data["azure"]["speech_key"]
        self.speech_region = config_data["azure"]["speech_region"]
    
    def finish(self, result):
        self.count -= 1
        print(self.count)
        # if self.count <= 0:
        #     self.finish_flag = True

    def azure_tts_wrap(self, text):
        ssml_start_string = "<speak xmlns=\"http://www.w3.org/2001/10/synthesis\" xmlns:mstts=\"http://www.w3.org/2001/mstts\" xmlns:emo=\"http://www.w3.org/2009/10/emotionml\" version=\"1.0\" xml:lang=\"zh-CN\">"

        # speaker_set = "<voice name=\"zh-CN-XiaoshuangNeural\" leadingsilence-exact=\"200ms\">" # 说话人

        # prosody_rate = "<prosody rate=\"+10.00%\" volume=\"+00.00%\" pitch=\"+00.00%\">" # 语速 音量 语调

        speaker_set = "<voice name=\"" + self.name + "\" leadingsilence-exact=\"" + self.leading_silence + "\">" # 说话人

        text_length = (len(text) - 1) / 10
        if text_length < 0.8:
            speak_rate = (1 - np.log(text_length) / np.abs(np.log(0.1))) * 20
        elif text_length >= 0.8:
            speak_rate = - (1 - np.log(text_length) / np.abs(np.log(0.1))) * 15
        elif text_length == 1:
            speak_rate = 0
        else:
            speak_rate = - (np.log(text_length + 2) /  np.log(100)) * 50

        if speak_rate > 0:
            speak_rate = '+' + str(np.round(speak_rate, 2))
        else:
            speak_rate = str(np.round(speak_rate, 2))
        
        # print(speak_rate)

        prosody_rate = "<prosody rate=\"" + speak_rate + "%\" volume=\"" + self.volume + "\" pitch=\"" + self.pitch + "\">" # 语速 音量 语调

        # print(prosody_rate)
        sentence = text # 文本

        ssml_end_string = "</prosody></voice></speak>"

        ssml_string = ssml_start_string + speaker_set + prosody_rate + sentence + ssml_end_string

        # print(ssml_string)

        return ssml_string

    def azure_tts(self, sentence):
        try:
            print(sentence, self.finish_flag, self.count)
            self.speech_synthesizer.speak_text(sentence)
            speechresult = self.speech_synthesizer.speak_ssml_async(self.azure_tts_wrap(sentence))
        except Exception as res:
            print(res)
    
    def completed(self):
        # print("到点了")
        self.speech_synthesizer.synthesis_completed.connect(self.finish)

    def open_connection(self):
        self.connection.open(True)

    def close_connection(self):
        self.connection.open(False)

    def intial_azure(self):
        try:
            self.speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.speech_region)
            self.speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
            self.audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

            self.flush_azure()

            self.connection = speechsdk.Connection.from_speech_synthesizer(self.speech_synthesizer)
            
            self.open_connection()

            # print(self.speech_key, self.speech_region, os.environ.get("SPEECH_KEY"), os.environ.get("SPEECH_REGION"))
            
        except Exception as res:
            print(res)
        

    def flush_azure(self):
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(self.speech_config, audio_config=self.audio_config)
        self.count = 0
    

