# Neural Machine Translation (seq2seq) for chit-chat

#### Model

```
wget  http://share.ipavlov.mipt.ru:8080/repository/models/chitchat/nmt-chitchat-v0.2.1.tgz
export CHITCHAT_MODEL=<PATH_TO_MODEL>
```

#### Example
```
import nmt.interface as bot
import os


model_path = os.environ.get("CHITCHAT_MODEL")
bot.init(model_path)


bot.interactive_dialogue(prompt = "[Ваш запрос]: ")

```

#### Example of dialogues

> [Ваш запрос]: Добрый день, меня зовут Денис. Мне нужна помощь с новым дизайном Сбербанк Онлайн    

>  done, num sentences 1, time 0s, Tue Sep 19 15:44:34 2017.

> [ NMT ]: Служба технической поддержки Сбербанка , меня зовут Олег , здравствуйте ! Денис , перейдите , пожалуйста , в раздел " Платежи и переводы " , далее " Перейти к списку платежей "


> [Ваш запрос]: Спасибо

>  done, num sentences 1, time 0s, Tue Sep 19 15:44:47 2017.

> [ NMT ]: Денис , уточните , пожалуйста , какие затруднения у Вас появляются с заполнением ?


> [Ваш запрос]: Все решено

>  done, num sentences 1, time 0s, Tue Sep 19 15:44:56 2017.

> [ NMT ]: Какие затруднения у Вас появляются ?


> [Ваш запрос]: Больше никаких, спасибо

>  done, num sentences 1, time 0s, Tue Sep 19 15:45:07 2017.

> [ NMT ]: Вы скопировали платёжное поручение ?


> [Ваш запрос]: Да

>  done, num sentences 1, time 0s, Tue Sep 19 15:45:10 2017.

> [ NMT ]: Уточните , пожалуйста , Вы внесли иную строку по поручению ?


> [Ваш запрос]: Да

>  done, num sentences 1, time 0s, Tue Sep 19 15:45:16 2017.

> [ NMT ]: Работаете в новом дизайне ?


> [Ваш запрос]: Да

>  done, num sentences 1, time 0s, Tue Sep 19 15:45:19 2017.

> [ NMT ]: Данные профиля необходимы для возможности самостоятельной смены пароля на вход в систему в случае его утери . Данные профиля Вы можете заполнить , нажав на стрелку вниз в правом верхнем углу ( рядом с наименованием организации ) и перейдя в раздел " Мой профиль " . Возможно , у Вас остались еще какие-либо вопросы ко мне ? Могу я еще


> [Ваш запрос]: Нет

>  done, num sentences 1, time 0s, Tue Sep 19 15:45:30 2017.

> [ NMT ]: Если у Вас ещё возникнут вопросы по системе Сбербанк Бизнес Онлайн , будем рады Вам помочь . Спасибо за обращение , всего доброго !
