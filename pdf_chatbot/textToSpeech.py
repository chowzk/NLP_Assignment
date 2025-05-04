import pygame
import speech_recognition as sr
import os
from gtts import gTTS
import re

class TTS:
    # Initialize the audio
    pygame.mixer.init()

    @staticmethod
    def text_to_speech(text):
        tts = gTTS(text=text, lang='en')
        filename = "temp.mp3"
        tts.save(filename)

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        os.remove(filename)

    @staticmethod
    def speech_to_text():
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Say something...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            return TTS.format_sentence(text)
        except sr.UnknownValueError:
            print("Sorry, I could not understand what you said.")
            return None
        except sr.RequestError:
            print("Could not request results from Google Speech Recognition.")
            return None

    @staticmethod
    def format_sentence(text):
        text = text.strip()
        if not text:
            return ""

        text = text[0].upper() + text[1:]

        if not re.search(r'[.?!]$', text):
            if TTS.is_question(text):
                text += '?'
            else:
                text += '.'

        return text

    @staticmethod
    def is_question(text):
        question_words = ("who", "what", "when", "where", "why", "how", "can", "do", "does", "is", "are", "will", "did", "should", "could")
        return text.lower().split()[0] in question_words

