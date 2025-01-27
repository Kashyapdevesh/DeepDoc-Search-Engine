import pika

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'test_queue'


def consume_message():
    """Consume the test message from RabbitMQ."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Declare queue
    channel.queue_declare(queue=QUEUE_NAME)

    def callback(ch, method, properties, body):
        print(f"✅ Received: {body.decode()}")
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge message

    # Consume message
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)

    print("🔄 Waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    consume_message()
