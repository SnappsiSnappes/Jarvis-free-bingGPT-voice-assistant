import random
from enum import Enum


class Emotion(Enum):
    NEUTRAL = "Normal"
    ANGRY = "Angry"
    GLEE = "Glee"
    HAPPY = "Happy"
    SAD = "Sad"
    WORRIED = "Worried"
    THINKING = "Focused"
    ANNOYED = "Annoyed"
    SURPRISED = "Surprised"
    SKEPTIC = "Skeptic"
    FRUSTRATED = "Frustrated"
    UNIMPRESSED = "Unimpressed"
    SLEEPY = "Sleepy"
    SUSPICIOUS = "Suspicious"
    SQUINT = "Squint"
    FURIOUS = "Furious"
    SCARED = "Scared"
    AWE = "Awe"


class EmotionState:
    """
    Управляет текущим состоянием эмоции и логикой переходов.
    """

    def __init__(self):
        self.current = Emotion.NEUTRAL

    def set(self, emotion: Emotion):
        """Установить новую эмоцию и вернуть её."""
        self.current = emotion
        return self.current

    def get_next_idle(self) -> Emotion:
        """
        Выбирает следующую эмоцию для режима простоя.
        Исключаем текущее состояние, выбираем случайную из остальных.
        """
        choices = [e for e in Emotion if e != self.current and e != Emotion.THINKING]
        next_emotion = random.choice(choices)
        self.current = next_emotion
        return next_emotion

    def get_thinking(self) -> Emotion:
        """
        Возвращает состояние мысли (используется при обработке запроса).
        """
        self.current = Emotion.THINKING
        return self.current
