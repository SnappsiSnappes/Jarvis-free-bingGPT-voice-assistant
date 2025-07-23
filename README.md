# Jarvis-Pi — голосовой ассистент и «мозг» для персонального робота

> Русскоязычный оффлайн-ассистент с горячей перезагрузкой плагинов, поддержкой локальной LLM через Ollama, выводом состояния на OLED через ESP32/WebSocket и расширяемым фреймворком скиллов.

---

## Содержание

1. [Возможности](#возможности)
2. [Структура проекта](#структура-проекта)
3. [Аппаратные требования](#аппаратные-требования)
4. [Установка на Raspberry Pi OS](#установка-на-raspberry-pi-os)
5. [Подключение ESP32 + OLED](#подключение-esp32--oled)
6. [Пример кода для Arduino IDE](#пример-кода-для-arduino-ide)
7. [Разработка своих скиллов](#разработка-своих-скиллов)
8. [Roadmap и дальнейшее развитие](#roadmap-и-дальнейшее-развитие)
9. [Лицензия](#лицензия)

---

## Возможности

* Активация по ключевой фразе «Джарвис» (Picovoice Porcupine + Google-STT)
* Оффлайн-STT Vosk (`model_small`)
* Натуральный TTS Piper-TTS с разбиением по 180 символам
* Горячая перезагрузка скиллов из `/skills` через `jarvis_skills.py`
* Fuzzy-распознавание команд (RapidFuzz)
* БД-лаунчер приложений/сайтов (SQLite + `working_getter_from_db.py`)
* Интеграция с локальной LLM (Ollama, отдельный процесс)
* Вывод состояния (время, погода, произвольные тексты) на OLED-дисплей через ESP32+WebSocket

---

## Структура проекта

```
.
├── ai_launch_no_PVC.py    # главный event-loop, менеджер процессов и диспетчер скиллов
├── display/               # драйверы для вывода (console.py, websocket.py)
├── skills/                # плагины-скиллы (time_ru.py, weather_ru.py, ...)
├── working_tts.py         # адаптер Piper-TTS
├── working_getter_from_db.py
├── requirements.txt
└── README.md
```

---

## Аппаратные требования

| Компонент |          Минимум         |        Рекомендовано       |
| :-------: | :----------------------: | :------------------------: |
|    SBC    |   Raspberry Pi 5 (8 GB)  |    + активное охлаждение   |
|  Питание  |          5 V 3 A         |  Power-bank 5 V 20000 mAh  |
|  Микрофон |       USB-гарнитура      |     ReSpeaker 2-Mic HAT    |
|  Дисплей  | ESP32 + OLED 0.96″ (I²C) | SPI IPS 1.3–2″ или HDMI 5″ |
|  Динамик  |     3.5 мм / I²S amp     |       3 Вт + mini‑amp      |

---

## Установка на Raspberry Pi OS (64‑bit)

```bash
# 1. Клонируем репозиторий
git clone https://github.com/yourname/jarvis-pi.git
cd jarvis-pi

# 2. Системные зависимости
sudo apt update
sudo apt install -y python3-pip portaudio19-dev libasound2-dev

py -3.10 -m venv venv
# 3. Python-библиотеки
pip3 install -r requirements.txt

# 4. Копируем модель Piper
mkdir -p piper && cp ru-RU-irina-medium.* piper/

# 5. Настройка микрофона
#   Откройте config.ini и в секции [MIC] укажите microphone_index
nano config.ini

# 6. Запуск
python3 ai_launch_no_PVC.py
```

---

## Подключение ESP32 + OLED

1. В Arduino IDE установите библиотеки: `WebSockets`, `ArduinoJson`, `U8g2`.
2. Скопируйте скетч из раздела ниже и загрузите на ESP32 (плата: ESP32 Dev Module).
3. Убедитесь, что ESP32 и Raspberry Pi в одной Wi‑Fi сети.
4. Jarvis слушает WebSocket на порту 8765.

При старте в Serial Monitor увидите:

```
[WS] connected
```

— сразу же на OLED отобразится текущее время, погода и актуальный текст.

---

## Система эмоций

> Полностью модульная, декомпозирована на **manager ↔ state ↔ driver**.

### 1. `emotion/state.py`

* Перечисление `Emotion` (`NEUTRAL`, `HAPPY`, `THINKING`, `ANGRY`, `SAD`, …)
* Таблица «idle‑эмоций» и их весов

### 2. `emotion/manager.py`

* Синглтон‑класс, подписывается на события `events.broker`
* Алгоритм:

  * при простое каждые *N* секунд публикует новую эмоцию из idle‑списка
  * на `user_query_started` → `THINKING`
  * на `user_query_ended`   → пауза 1 с → новую idle‑эмоцию

### 3. `emotion/drivers.py`

* **WebSocketEmotionDriver** — адаптер к `display`‑слою: переводит `Emotion → DisplayItem(kind="emotion")` и высылает клиентам.

Такое разделение позволяет в будущем:

* добавлять датчики (температура, освещённость, столкновение) — просто публикуем событие → manager сам решит, какую эмоцию поставить
* заменить драйвер глазами на TFT или гэросток — достаточно другой driver‑класс

### 4. Серийный API для скиллов

Любой python‑скилл может переключить эмоцию:

```python
from emotion import publish_emotion
publish_emotion(Emotion.HAPPY)
```

---

## Пример кода для Arduino IDE

```cpp
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <U8g2lib.h>

#include "Face.h"

#include <map>
#include <string>
#include <functional>

// Настройки Wi-Fi / WS
const char* WIFI_SSID     = "Redmi_A33D";
const char* WIFI_PASSWORD = "88882222";
const char* WS_HOST       = "192.168.31.125";
const uint16_t WS_PORT    = 8765;
const char* WS_PATH       = "/";

// OLED-дисплей
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);
WebSocketsClient webSocket;

// GLOBALS
Face *face;


// Определяем тип: метод Expression без аргументов
using ExprFn = std::function<void()>;

// Глобальный map
std::map<String, ExprFn> emotionFns;

// ——————————————————————————————
// Оверлей для времени/погоды/текста
String currentTime, currentWeather, currentMainText;
bool textVisible = false;
unsigned long lastTextMillis = 0;
const unsigned long TEXT_DISPLAY_TIMEOUT = 5000;

struct Region { uint8_t x,y,w,h; };
const Region TIME_R    = {  0,  0, 60, 16 };
const Region WEATHER_R = {100,  0, 28, 16 };
const Region MAIN_R    = {  0, 16,128, 48 };

void renderOverlay() {
  if (currentTime.length()) {
    u8g2.setFont(u8g2_font_5x8_t_cyrillic);
    u8g2.drawUTF8(TIME_R.x, TIME_R.y + 8, currentTime.c_str());
  }
  if (currentWeather.length()) {
    u8g2.setFont(u8g2_font_5x8_t_cyrillic);
    u8g2.drawUTF8(WEATHER_R.x, WEATHER_R.y + 8, currentWeather.c_str());
  }
  if (textVisible && currentMainText.length()) {
    static String lines[10];
    int n = 0;
    String word, line;
    for (int i = 0; i <= currentMainText.length(); ++i) {
      char c = i < currentMainText.length() ? currentMainText[i] : ' ';
      if (c==' '||c=='\n') {
        if (word.length()) {
          String cand = line.length() ? line + ' ' + word : word;
          if (u8g2.getUTF8Width(cand.c_str()) <= MAIN_R.w) {
            line = cand;
          } else {
            lines[n++] = line;
            line = word;
          }
          word = "";
        }
        if (c=='\n') {
          lines[n++] = line;
          line = "";
        }
      } else {
        word += c;
      }
    }
    if (line.length()) lines[n++] = line;
    int y = MAIN_R.y + 40;
    u8g2.setFont(u8g2_font_5x8_t_cyrillic);
    for (int i = 0; i < n; ++i) {
      u8g2.drawUTF8(MAIN_R.x, y, lines[i].c_str());
      y += 10;
    }
  }
}

// WS-callback с логами
void webSocketEvent(WStype_t t, uint8_t* p, size_t l) {
  if (t != WStype_TEXT) return;
  Serial.print("[WS] got TEXT ("); Serial.print(l); Serial.println(" bytes)");
  Serial.write(p, l);
  Serial.println();

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, p, l);
  if (err) {
    Serial.print("[WS] JSON error: "); Serial.println(err.c_str());
    return;
  }

  const char* kind = doc["kind"];
  const char* txt  = doc["payload"];
  Serial.print("[WS] Parsed kind=\""); Serial.print(kind);
  Serial.print("\" payload=\""); Serial.print(txt); Serial.println("\"");

  if (!strcmp(kind,"time")) {
    currentTime = txt;
    Serial.print("[EMO] time updated: "); Serial.println(currentTime);
  }
  else if (!strcmp(kind,"weather")) {
    currentWeather = txt;
    Serial.print("[EMO] weather updated: "); Serial.println(currentWeather);
  }
  else if (!strcmp(kind,"text")) {
    currentMainText = txt;
    textVisible = true;
    lastTextMillis = millis();
    Serial.print("[EMO] main text: "); Serial.println(currentMainText);
  }
  else if (!strcmp(kind,"emotion")) {
    Serial.print("[EMO] Requested emotion: "); Serial.println(txt);

    if (!strcmp(kind,"emotion")) {
      onEmotionReceived(txt);
    }
    else {
      Serial.println("[EMO] Unknown emotion key!");
    }
  }
}

void onEmotionReceived(const char* txt) {
  auto it = emotionFns.find(txt);
  if (it != emotionFns.end()) {
    it->second();  // вызываем нужный лямбда-обёртанка
    Serial.print("[EMO] Called "); Serial.println(txt);
  } else {
    Serial.print("[EMO] Unknown emotion: "); Serial.println(txt);
  }
}

void setup() {
  Serial.begin(115200);
  u8g2.begin();

  emotionFns["normal"]      = [&]() { face->Expression.GoTo_Normal(); };
  emotionFns["angry"]       = [&]() { face->Expression.GoTo_Angry(); };
  emotionFns["glee"]        = [&]() { face->Expression.GoTo_Glee(); };
  emotionFns["happy"]       = [&]() { face->Expression.GoTo_Happy(); };
  emotionFns["sad"]         = [&]() { face->Expression.GoTo_Sad(); };
  emotionFns["worried"]     = [&]() { face->Expression.GoTo_Worried(); };  
  emotionFns["focused"]     = [&]() { face->Expression.GoTo_Focused(); };
  emotionFns["Annoyed"]     = [&]() { face->Expression.GoTo_Annoyed(); };
  emotionFns["surprised"]   = [&]() { face->Expression.GoTo_Surprised(); };
  emotionFns["skeptic"]     = [&]() { face->Expression.GoTo_Skeptic(); };
  emotionFns["frustrated"]  = [&]() { face->Expression.GoTo_Frustrated(); };
  emotionFns["unimpressed"] = [&]() { face->Expression.GoTo_Unimpressed(); };
  emotionFns["sleepy"]      = [&]() { face->Expression.GoTo_Sleepy(); };
  emotionFns["suspicious"]  = [&]() { face->Expression.GoTo_Suspicious(); };
  emotionFns["squint"]      = [&]() { face->Expression.GoTo_Squint(); };
  emotionFns["furious"]     = [&]() { face->Expression.GoTo_Furious(); };
  emotionFns["scared"]      = [&]() { face->Expression.GoTo_Scared(); };
  emotionFns["awe"]         = [&]() { face->Expression.GoTo_Awe(); };  

  // Инициализируем лицо и поведение
  face = new Face(/* screenWidth = */ 128, /* screenHeight = */ 64, /* eyeSize = */ 40);
  face->Expression.GoTo_Normal();
  face->RandomBehavior = false;
  face->RandomBlink = true;
  face->Blink.Timer.SetIntervalMillis(5000);
  face->RandomLook = true;

  // Wi-Fi + WebSocket
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) delay(100);
  webSocket.begin(WS_HOST, WS_PORT, WS_PATH);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
}

void loop() {
  webSocket.loop();

  if (textVisible && millis() - lastTextMillis > TEXT_DISPLAY_TIMEOUT) {
    textVisible = false;
    Serial.println("[EMO] MAIN text timeout, hiding text");
  }
  //face->Update();
  static unsigned long last = 0;
  if (millis() - last > 100) {
    last = millis();
    u8g2.firstPage();
    do {
      face->Update();
      renderOverlay();
    } while (u8g2.nextPage());
  }
}
```

---

## Разработка своих скиллов

В папке `/skills` создайте Python-файл:

```python
PATTERNS = ["привет", "здравствуй"]
def handle(text: str) -> str:
    return "Привет, создатель!"
```

Скилл автоматически подхватится и будет вызываться по fuzzy-совпадению.

---

## Roadmap и лицензия

* v0.5: ESP32 + OLED через WebSocket
* v1.0: ROS, indoor SLAM

**MIT License**.
