"""Pluggable Notification Channels."""
import abc
import logging

logger = logging.getLogger(__name__)

class NotificationChannel(abc.ABC):
    @abc.abstractmethod
    async def send(self, recipient: str, message: str, metadata: dict = None) -> dict:
        pass

class WhatsAppChannel(NotificationChannel):
    async def send(self, recipient: str, message: str, metadata: dict = None) -> dict:
        logger.info(f"Mock sending WhatsApp to {recipient}: {message[:20]}...")
        return {"status": "success", "channel": "whatsapp", "recipient": recipient}

class EmailChannel(NotificationChannel):
    async def send(self, recipient: str, message: str, metadata: dict = None) -> dict:
        logger.info(f"Mock sending Email to {recipient}: {message[:20]}...")
        return {"status": "success", "channel": "email", "recipient": recipient}

class WebhookChannel(NotificationChannel):
    async def send(self, recipient: str, message: str, metadata: dict = None) -> dict:
        logger.info(f"Mock sending Webhook to {recipient}: {message[:20]}...")
        return {"status": "success", "channel": "webhook", "recipient": recipient}

class NotificationDispatcher:
    def __init__(self):
        self.channels = {
            "whatsapp": WhatsAppChannel(),
            "email": EmailChannel(),
            "webhook": WebhookChannel()
        }

    async def dispatch(self, channel_name: str, recipient: str, message: str, metadata: dict = None):
        channel = self.channels.get(channel_name)
        if not channel:
            raise ValueError(f"Channel {channel_name} not found.")
        return await channel.send(recipient, message, metadata)
