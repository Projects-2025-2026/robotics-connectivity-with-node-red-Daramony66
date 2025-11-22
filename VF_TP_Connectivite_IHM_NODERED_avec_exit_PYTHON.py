from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import threading
import time
import os
import signal

app = Flask(__name__)
CORS(app)  # Active CORS pour toutes les routes

HOST_ROBOT = '127.0.0.1'
PORT_ROBOT = 59002

# Connexion TCP ouverte au démarrage
robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
robot_socket.connect((HOST_ROBOT, PORT_ROBOT))
print(f"Connecté au robot {HOST_ROBOT}:{PORT_ROBOT}")

def shutdown_server_func(func):
    """Fonction pour arrêter le serveur Flask avec délai."""
    if func is None:
        print("Fonction shutdown non disponible, arrêt forcé après délai")
        time.sleep(0.01)  # Attend 1 seconde pour laisser le temps à la réponse d'arriver
        os.kill(os.getpid(), signal.SIGINT)
    else:
        time.sleep(0.01)  # Attend 1 seconde avant d'arrêter proprement
        func()

@app.route('/commande', methods=['POST'])
def commande():
    command = request.data.decode('utf-8').strip()
    print(f"Commande reçue : {command}")

    try:
        robot_socket.sendall(command.encode('utf-8'))
        ack = robot_socket.recv(1024).decode('utf-8')
        print(f"Réponse du robot : {ack}")

        if "EXIT OK" in ack:
            # Ferme la connexion robot proprement
            robot_socket.close()

            # Récupère la fonction d'arrêt du serveur Flask
            shutdown_func = request.environ.get('werkzeug.server.shutdown')

            # Lance l'arrêt du serveur dans un thread pour ne pas bloquer la réponse
            threading.Thread(target=shutdown_server_func, args=(shutdown_func,)).start()

            # Envoie la réponse avant d'arrêter le serveur
            return jsonify({"reponse": ack}), 200

        else:
            # Parsing normal de la réponse du robot
            parts = [p.strip() for p in ack.split(';') if p.strip() != '']
            header = parts[0]
            joint_parts = parts[1:]

            positions = {}
            for jp in joint_parts:
                joint, val = jp.split(':')
                positions[joint] = val

            return jsonify({
                "reponse": header,
                "positions": positions
            }), 200

    except Exception as e:
        print(f"Erreur d'envoi ou parsing : {e}")
        return jsonify({"error": "Erreur lors de l'envoi ou du parsing"}), 500


if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5000) #‼port 5000 par défaut en localhost
    finally:
        print("Arrêt du serveur, fermeture connexion robot")
        try:
            robot_socket.close()
        except:
            pass
