import io
import time
import webbrowser

import cv2
import pyautogui
import pyperclip
import win32clipboard
from PIL import Image


PHONE_NUMBER = "SEU_NUMERO_DE_TELEFONE_AQUI"  # Substitua pelo número de telefone com código do país, ex: "5511999999999"
WHATSAPP_MESSAGE = "Presenca detectada na frente da camera."
MOTION_AREA_THRESHOLD = 10000
ALERT_COOLDOWN_SECONDS = 60
NO_MOTION_RESET_FRAMES = 30
SNAPSHOT_PATH = "deteccao.jpg"


def copy_image_to_clipboard(image_path):
    image = Image.open(image_path)
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def send_whatsapp_message(phone_number, message, image_path):
    cv2.imwrite(image_path, captured_frame)
    copy_image_to_clipboard(image_path)

    webbrowser.open(f"https://web.whatsapp.com/send?phone={phone_number}")
    time.sleep(18)  # aguarda o WhatsApp Web carregar

    pyautogui.hotkey("ctrl", "v")   # cola a imagem no chat
    time.sleep(3)                   # aguarda o preview aparecer

    pyperclip.copy(message)         # copia a legenda para o clipboard
    pyautogui.hotkey("ctrl", "v")   # cola a legenda no campo de caption
    time.sleep(1)
    pyautogui.press("enter")        # envia


video = cv2.VideoCapture(0)
first_frame = None
last_alert_time = 0
alert_sent_for_current_presence = False
frames_without_motion = 0
captured_frame = None

while True:
    check, frame = video.read()
    if not check:
        break

    status = 0

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if first_frame is None:
        first_frame = gray
        continue

    delta_frame = cv2.absdiff(first_frame, gray)
    threshold_frame = cv2.threshold(delta_frame, 30, 255, cv2.THRESH_BINARY)[1]
    threshold_frame = cv2.dilate(threshold_frame, None, iterations=2)

    cnts, _ = cv2.findContours(
        threshold_frame.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    for contour in cnts:
        if cv2.contourArea(contour) < MOTION_AREA_THRESHOLD:
            continue

        status = 1
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

    if status == 1:
        frames_without_motion = 0
        current_time = time.time()
        can_send_alert = current_time - last_alert_time >= ALERT_COOLDOWN_SECONDS

        if not alert_sent_for_current_presence and can_send_alert:
            captured_frame = frame.copy()
            send_whatsapp_message(PHONE_NUMBER, WHATSAPP_MESSAGE, SNAPSHOT_PATH)
            last_alert_time = current_time
            alert_sent_for_current_presence = True
    else:
        frames_without_motion += 1
        if frames_without_motion >= NO_MOTION_RESET_FRAMES:
            alert_sent_for_current_presence = False

    label = "Presenca detectada" if status == 1 else "Sem presenca"
    color = (0, 0, 255) if status == 1 else (0, 255, 0)
    cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("Detector de Presenca", frame)

    key = cv2.waitKey(1)
    if key == ord("q"):
        break

video.release()
cv2.destroyAllWindows()
