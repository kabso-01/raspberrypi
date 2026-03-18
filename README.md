# Dependencies to install:
# sudo apt-get update
# sudo apt-get install python3-pip
# sudo apt-get install bluez
# pip3 install pybluez

import bluetooth
import time

def list_available_devices():
    print("Recherche des appareils Bluetooth...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
    
    print("Appareils trouvés:")
    for addr, name in nearby_devices:
        print(f"Adresse : {addr}, Nom : {name}")
    return nearby_devices

def send_data(address, data):
    # Créer un socket Bluetooth
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    try:
        print("Tentative de connexion...")
        sock.connect((address, 1))  # Port 1, modifiez-le si nécessaire
        print(f"Connecté à {address}")
        
        print("Envoi de données...")
        sock.send(data)
        print(f"Données envoyées: {data}")

    except bluetooth.btcommon.BluetoothError as e:
        print(f"Erreur de connexion: {e}")
    finally:
        sock.close()  # Fermer la connexion

if __name__ == "__main__":
    # Lister les appareils disponibles
    devices = list_available_devices()
    
    # Remplacez ceci par l'adresse MAC de votre casque
    quest_address = "00:00:00:00:00:00"  # Remplacez par l'adresse de votre casque
    message = "Bonjour, Meta Quest!"
    
    # Vérifier si l'adresse du casque est dans la liste
    if any(addr == quest_address for addr, name in devices):
        send_data(quest_address, message)
    else:
        print("Le casque Meta Quest n'a pas été trouvé. Vérifiez l'adresse et réessayez.")
Instructions pour exécuter le script :
Installer les dépendances : Exécutez les commandes en commentaires au début du code dans votre terminal.
Remplacer l'adresse MAC : Dans la ligne quest_address, remplacez "00:00:00:00:00:00" par l'adresse Bluetooth de votre casque Meta Quest 3. Vous pouvez obtenir cette adresse en exécutant la fonction list_available_devices(), qui affichera tous les appareils Bluetooth à portée.
Exécuter le script : Une fois que vous avez mis à jour l'adresse MAC, exécutez le script avec :
bash


python3 bluetooth_sender.py