from gtts import gTTS
from playsound import playsound
from threadpool import threadpool


def out(text, wait=True):
    if wait:
        out_(text).result()
    else:
        out_(text)


@threadpool
def out_(text):
    print(text)
    if text:
        speech = gTTS(text=text, lang="nl", slow=False)
        speech.save("speech.mp3")
        playsound("speech.mp3")
