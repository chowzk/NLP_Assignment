import pygame
import speech_recognition as sr
import os
from gtts import gTTS

class TTS():
    # Initialize pygame mixer
    pygame.mixer.init()

    def text_to_speech(text):
        tts = gTTS(text=text, lang='en')
        filename = "pdf_chatbot\\temp.mp3"
        tts.save(filename)

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        os.remove(filename)

    def speech_to_text():
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Say something...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understant what you said.")
            return None
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition.")
            return None

        # print(text)
