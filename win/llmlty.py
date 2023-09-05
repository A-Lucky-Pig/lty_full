import os
import sys
from io import StringIO
import asyncio
from typing import Any, Dict, List
from langchain.schema import LLMResult, HumanMessage
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory,ConversationSummaryMemory
from langchain.callbacks.base import BaseCallbackHandler
import datetime
import azurelty
import time
from langchain.llms import OpenAI
import socketsto

class llmLTY():
    def __init__(self, config_data) -> None:
        self.asking = None
        self.callback_handler = None
        self.prompt = None
        self.memory = None
        self.llm = None
        self.tts = None
        self.current_time = None
        self.conversation = None
        self.config_data = config_data
        self.memory_flag = None

    def initial(self, client_out):
        os.environ["OPENAI_API_KEY"] = self.config_data["openai"]["key"]
        os.environ["OPENAI_PROXY"] = self.config_data["proxy"]
        self.current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        client_out.hand_shaking()

        self.tts = azurelty.Azureczz(self.config_data)
        self.tts.intial_azure()

        self.callback_handler = [MyCustomHandler(self.tts)]
        self.llm = ChatOpenAI(streaming=True, callbacks=self.callback_handler, temperature=0)

        self.prompt = ChatPromptTemplate(
                        messages=[
                            SystemMessagePromptTemplate.from_template(
                                self.current_time + self.config_data["openai"]["prompt"]
                            ),
                            # The `variable_name` here is what must align with memory
                            MessagesPlaceholder(variable_name="chat_history"),
                            HumanMessagePromptTemplate.from_template("{question}")
                        ]
                    )
        
        self.flushmemory()
        
        self.input_ask(self.config_data["openai"]["greet"])
    
    def flushmemory(self):
        self.memory = ConversationSummaryMemory(llm=OpenAI(temperature=0),memory_key="chat_history", return_messages=True, max_token_limit=1024)
        self.conversation = LLMChain(
                llm=self.llm,
                prompt=self.prompt,
                verbose=True,
                memory=self.memory
                )
        self.memory_flag = True

    def input_ask(self, asking):
        self.tts.flush_azure()
        self.asking = asking
        self.tts.count += 1
        self.conversation({"question": asking})
        self.azure_speak()

    def azure_speak(self):
        while self.tts.count:
            time.sleep(0.1)

    def close(self):
        self.tts.close_connection()


class MyCustomHandler(BaseCallbackHandler):
    """Async callback handler that can be used to handle callbacks from langchain."""
    def __init__(self, tts) -> None:
        super().__init__()
        self.sentence = ''
        self.tts = tts
        self.fist_count = 0

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        self.sentence = ''

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.sentence += token
        if token in ['。', '；', '？', '！', '：', '~', '…', '.', '?', ':', ';', '!']:
            if self.fist_count == 0 and len(self.sentence) > 5:
                self.tts.azure_tts(self.sentence)
                self.sentence = ''  
                # print(self.sentence)
                self.fist_count += 1
                
            if len(self.sentence) > 25:
                self.tts.azure_tts(self.sentence)
                self.sentence = ''
                # print(self.sentence)
            
        
        # print(token)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when chain ends running."""
        if self.sentence != '':
            self.tts.azure_tts(self.sentence)
            self.sentence = ''
            
        self.tts.completed()
        self.fist_count = 0
        