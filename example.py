from nmt.interface import Agents
import os


model_path = os.environ.get("CHITCHAT_MODEL")
ckpt_name = os.environ.get("CHITCHAT_CKPT") #Optional, it can be not defined
embeddings_model = os.environ.get("CHITCHAT_UMBED_MODEL") #Optional, it can be not defined

agents = Agents(model_path, ckpt_name = ckpt_name, embedding_generator_path=embeddings_model) # if ckpt_name is None bot gets last ckpt

agent_id = '0' # Id for new agent
# agents.deploy_agent(id = agent_id, reset = True) # if reset is True and agent is exist then agent context will be reseted. Reset is True by default.
# msg = 'Здравствуйте , Подскажите , веду  бух учёт на Эльбе . Контур . Сохранил платёжные поручения для уплаты страховых платежей , сохранил их в текстовом формате  ( так сохраняет сама программа ), а в банк не могу импортировать . пишет , что в файле нет необходимых реквизитов , хотя года открываешь текстовый файл вся информация присутствует . Спасибо .'
# print(agents.send(msg,agent_id)) # Id is 0 by default. If agent is not exist then it will be created.

agents.interactive_dialogue(prompt = "[Ваш запрос]: ", agent_id = agent_id) # Id is 0 by default.
