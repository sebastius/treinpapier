import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
import time
import os

# Get the absolute path of the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))


# Vul hier je eigen API-sleutel in
api_key = 'XXX'

# Headers met API-sleutel
headers = {
    'Ocp-Apim-Subscription-Key': api_key
}

Palet = [
    (0, 0, 0, 255),
    (255, 255, 255, 255),
    (255, 0, 0, 255)
]

old_schedule = ['old']

def gettraindata(station="utzl"): #getting station Utrecht Zuilen
    url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures?station={station}"
    response = requests.get(url, headers=headers)

    # Controleer of de API-aanroep succesvol was
    if response.status_code == 200:
        data = response.json()
        return(data)
    else:
        print(f"Fout bij het ophalen van de gegevens: {response.status_code}")

def decodeschedule(data):
    train_schedule = []
    for departure in data['payload']['departures']:
            if 'routeStations' in departure:
                uic_codes = [station['uicCode'] for station in departure['routeStations']]
                if '8400621' in uic_codes: # filtering for Utrecht Centraal
                    plannedtijd_raw = departure['plannedDateTime']
                    plannedtijd = datetime.fromisoformat(plannedtijd_raw[:-5])
                    actueletijd_raw = departure['actualDateTime']
                    actueletijd = datetime.fromisoformat(actueletijd_raw[:-5])
                    verschil = int((actueletijd - plannedtijd).total_seconds() / 60)
                    eindbestemming = departure['direction']
                    treinsoort = departure['product']['longCategoryName']
                    spoor = departure['plannedTrack']
                    if (verschil != 0):
                        vertraging = f"+{verschil}"
                    else:
                        vertraging = ""
                    train_schedule.append({"plantijd": plannedtijd,"actueletijd": actueletijd, "vertraging": verschil, "spoor": spoor, "bestemming": eindbestemming})
                    print(f"Om {plannedtijd.strftime('%H:%M')}{vertraging} vertrekt een {treinsoort} naar {eindbestemming} vanaf spoor {spoor}.")
    return train_schedule

def createimage(train_schedule):
    canvas_width, canvas_height = 296, 152
    canvas = Image.new('RGB', (canvas_width, canvas_height), color=Palet[1])
    draw = ImageDraw.Draw(canvas)

    font = ImageFont.truetype(os.path.join(script_dir,"B612Mono-Regular.ttf"), size=40)  # Use a TrueType font
    titlefont = ImageFont.truetype(os.path.join(script_dir, "B612Mono-Regular.ttf"), size=20)  # Use a TrueType font
    draw.text((0,0),"Trein Zuilen→Centraal", fill=Palet[0], font=titlefont)
   
    if not train_schedule:
         draw.text((0,60),"geen treinen gepland", fill=Palet[2], font=titlefont)
       
    for i, train in enumerate(train_schedule):
        if i == 3:  # Stop after the third item
            break
        draw.text((0,15+(i*45)),train['plantijd'].strftime('%H:%M'), fill=Palet[0], font=font)
        if (train['vertraging']!=0):
            draw.text((140,i*45),f"+{train['vertraging']}", fill=Palet[2], font=font)
    canvas.save(os.path.join(script_dir,'plaatje.jpg'), 'JPEG', quality=100)



    print('image generated')

def uploadimage(filename, server, tag):
 # Save the image as JPEG with maximum quality
    image_path = os.path.join(script_dir,'plaatje.jpg')
    mac = '0000032CA0653E18'
    apip = "192.168.1.162" 
    dither = 0
    # Prepare the HTTP POST request
    url = "http://" + apip + "/imgupload"
    payload = {"dither": dither, "mac": mac}  # Additional POST parameter
    files = {"file": open(image_path, "rb")}  # File to be uploaded

    # Send the HTTP POST request
    try:
        response = requests.post(url, data=payload, files=files)

        # Check the response status
        if response.status_code == 200:
            print(f"{mac} Image uploaded successfully! {image_path}")
        else:
            print(f"{mac} Failed to upload the image.")
    except:
        print(f"{mac} Failed to upload the image.")


    print('succesfully uploaded')

try:
    while True:
        print('checking train things')
        data = gettraindata()
        train_schedule = decodeschedule(data)
        if (old_schedule!=train_schedule):
            createimage(train_schedule)
            old_schedule = train_schedule
            uploadimage('a.jpg', 'bla', 'bla')
        else:
            print('no update neccessary')
        time.sleep(60)
except KeyboardInterrupt:
    print("\nStopped by user.")
