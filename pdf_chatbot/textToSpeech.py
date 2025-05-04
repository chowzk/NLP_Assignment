import pygame
import speech_recognition as sr
import os
from gtts import gTTS
import re
import pydub as AudioSegment
import time

class TTS:
    @staticmethod
    def text_to_speech(text):
        """Convert text to speech and save as MP3 in static directory."""
        try:
            tts = gTTS(text=text, lang='en')
            timestamp = int(time.time() * 1000)
            audio_file = f"static/temp_audio_{timestamp}.mp3"
            tts.save(audio_file)
            return audio_file
        except Exception as e:
            raise Exception(f"Error generating speech: {str(e)}")

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
        """Format the transcribed text."""
        if not text:
            return ""
        text = text.strip()
        text = text[0].upper() + text[1:]
        if not re.search(r'[.?!]$', text):
            if TTS.is_question(text):
                text += '?'
            else:
                text += '.'
        return text

    @staticmethod
    def is_question(text):
        """Check if the text is a question."""
        question_words = ("who", "what", "when", "where", "why", "how", "can", "do", "does", "is", "are", "will", "did", "should", "could")
        return text.lower().split()[0] in question_words
    
    @staticmethod
    def speech_to_text_from_file(file_path):
        """Convert WAV audio file to text."""
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            return TTS.format_sentence(text)
        except sr.UnknownValueError:
            print("Sorry, I could not understand what you said.")
            return None
        except sr.RequestError:
            print("Could not request results from Google Speech Recognition.")
            return None
        except Exception as e:
            raise Exception(f"Error processing audio file: {str(e)}")
        