I

1.	En quoi HTTP convient-il bien à cette application ?
Donner des exemples d’actions qui fonctionnent très bien avec un modèle requête/réponse.
HTTP convient bien à cette application car on exploite une action qui vient de l’utilisateur : par exemple, ce modèle fonctionne bien pour la création d’un profil (requête = formulaire d’inscription, réponse = confirmation), recherche de message ( requête, envoyer des critères et réponse = liste correspondante)
2. Quelles limites apparaissent si l’on veut une vraie messagerie “vivante” ?
Le serveur ne parle pas à l’utilisateur si celui-ci ne demande rien.
•	comment savoir immédiatement qu’un nouveau message est arrivé ?
L’utilisateur de la messagerie devra rafraîchir constamment sa page.
•	comment mettre à jour automatiquement l’interface sans recharger la page ?
Le serveur est incapable d’envoyer de nouvelles données pour rafraîchir la vue.
•	comment notifier en direct qu’un message a été lu ?
Sans requête de l’utilisateur cela est impossible avec ce serveur.

3. Quelle solution pourrait-on introduire ensuite ?
Expliquer en quelques lignes pourquoi WebSocket serait une évolution naturelle pour ajouter du temps réel.
Le WebSocket maintient la connexion active après chaque réponse, contrairement à http. Ainsi, dès qu’un message arrive dans la base de données, le serveur peut l’envoyer instantanément au destinataire (receiver) sans requête. On s’approche de la vraie messagerie en répondant aux problèmes rencontrés précédemment. 


II
vos choix de modélisation,
les routes disponibles,
les limites de votre solution HTTP.
Modélisation : 
L’application repose sur le framework FastAPI et la bibliothèque SQLModel. Pour le SQL, j’ai défini 2 tables principales (User et Message), elles sont reliées par des relations un-à-plusieurs » qui permettent aux utilisateurs d’envoyer plusieurs messages. Ensuite, Pydantic permet de vérifier que les données reçues son correctes. Par exemple EmailStr empêche la création d’un compte avec une adresse mail invalide. 
Routes disponibles : 
Gestion des utilisateurs : POST/users enregistre un nouvel utilisateur. GET/users liste tous les utilisateurs inscrits
Gestion des messages : POST/messages : pour envoyer un message. GET/users/{id}/inbox : Affiche les messages reçus. GET/messages/{id} : permet de consulter un message précis. PATCH/messages/{id}/read : marque un message comme lu une fois ouvert.

Limites de la solution HTTP : Comme vu plus haut la solution repose sur un modèle de Requête et réponse ce qui pose plusieurs problèmes : le serveur ne peut pas envoyer d’information à l’utilisateur. Il n’y a donc pas de direct, les messages ne sont pas reçus en direct.

J’ai donc intégré le WebSocket que nous avions commencé à écrire en cours.
