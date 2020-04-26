from celery import shared_task
from django_telegram.imports import *
import Butlers
import traceback

@shared_task
def send_message_model(cls_path, id, retries=0):
    cls = load_from_path(cls_path)
    print('Sending %s id: %d.' % (str(cls_path), id))
    msg_model = cls.objects.get(id=id)

    try:
        msg_model.send_message()
    except Exception as e:
        if retries >= 5:
            Butlers.butlers_telegram.message_jeremy(
                'Failed to send driver message 5 times %s, %d \n\n %s' % (cls.__name__, id, traceback.format_exc()))
        else:
            msg_model.clear_send()
            send_message_model.apply_async(args=[cls_path, id, retries + 1], queue='telegram_queue', countdown=5)