import os
import json
import logging
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")


def publish_event(queue_name: str, payload: Dict[str, Any]) -> bool:
    """
    Publica un evento JSON en la cola de RabbitMQ.
    Si RabbitMQ no está disponible, emite log sin bloquear el flujo principal.
    """
    try:
        import pika
        parameters = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)

        message = json.dumps(payload)
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # mensaje persistente
        )
        connection.close()
        logger.info(f"[RabbitMQ] Publicado en '{queue_name}': {payload.get('item_id', '')}")
        return True
    except Exception as e:
        logger.warning(f"[RabbitMQ] No se pudo publicar en '{queue_name}': {e}")
        return False

