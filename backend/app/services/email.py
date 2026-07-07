"""
Envoi d'e-mails (aujourd'hui : uniquement le lien d'appairage d'une caméra
téléphone).

Utilise `smtplib` (bibliothèque standard) plutôt qu'une dépendance tierce. Le
serveur SMTP est configuré via les variables d'environnement (voir
`app.config.Settings`) ; si `SMTP_HOST` n'est pas renseigné, l'envoi est
refusé avec un message explicite plutôt que d'échouer silencieusement.
"""
import smtplib
from email.message import EmailMessage

from app.config import settings


def send_pairing_email(to_email: str, camera_name: str, pairing_link: str) -> None:
    """
    Envoie le lien d'appairage d'une caméra téléphone par e-mail.

    Lève une exception si le SMTP n'est pas configuré ou si l'envoi échoue ;
    à charge de l'appelant de la transformer en réponse HTTP appropriée.
    """
    if not settings.SMTP_HOST:
        raise RuntimeError("Aucun serveur SMTP configure (SMTP_HOST est vide).")

    message = EmailMessage()
    message["Subject"] = f"Lien de connexion - camera {camera_name}"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        "Bonjour,\n\n"
        f"Ouvrez ce lien sur le navigateur du telephone a utiliser comme camera "
        f'"{camera_name}", puis appuyez sur "Start streaming" :\n\n'
        f"{pairing_link}\n\n"
        "Ce lien reste valide tant que la camera existe dans le systeme."
    )

    # Port 465 is implicit TLS (the connection is encrypted from the first
    # byte) : STARTTLS on a plaintext SMTP() connection doesn't apply there
    # and fails against any server actually listening for TLS on that port.
    smtp_class = smtplib.SMTP_SSL if settings.SMTP_PORT == 465 else smtplib.SMTP
    with smtp_class(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS and settings.SMTP_PORT != 465:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
