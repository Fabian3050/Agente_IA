import os
import json
import logging
import threading
import time
from typing import Callable, Any, Dict, Optional

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
if RABBITMQ_URL.endswith("//"):
    RABBITMQ_URL = RABBITMQ_URL[:-1]


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

        message = json.dumps(payload, default=str)
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


def consume_messages(
    queue_name: str,
    callback: Callable[[Dict[str, Any]], None],
    stop_event: Optional[threading.Event] = None
):
    """
    Escucha y procesa continuamente mensajes de RabbitMQ en bucle con reconexión automática.
    """
    import pika
    while not (stop_event and stop_event.is_set()):
        try:
            parameters = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)

            def on_message(ch, method, properties, body):
                try:
                    payload = json.loads(body.decode("utf-8"))
                    callback(payload)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as ex:
                    logger.error(f"[RabbitMQ] Error procesando mensaje de '{queue_name}': {ex}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(queue=queue_name, on_message_callback=on_message)
            logger.info(f"[RabbitMQ] Consumidor activo escuchando en '{queue_name}'...")
            channel.start_consuming()
        except Exception as e:
            logger.warning(f"[RabbitMQ] Conexión interrumpida en cola '{queue_name}': {e}. Reintentando en 5s...")
            time.sleep(5)


def start_background_consumer(
    queue_name: str,
    callback: Callable[[Dict[str, Any]], None]
) -> threading.Thread:
    """
    Inicia un hilo demonio que consume la cola en segundo plano.
    """
    thread = threading.Thread(
        target=consume_messages,
        args=(queue_name, callback),
        daemon=True,
        name=f"RabbitConsumer-{queue_name}"
    )
    thread.start()
    return thread
