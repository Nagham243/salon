import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import MessagesModel, MessengerModel, BlockUserModel
from accounts.models import UserProfile, ClubsModel
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from .views import get_user_full_name, get_user_capacity

class chatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.msg_model = None

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        user = self.scope["user"]
        userprofile = UserProfile.objects.get(id=user.userprofile.id)
        userprofile.is_in_chat = True
        userprofile.save()

        self.accept()

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )
        messenger = MessengerModel.objects.get(room_id=self.room_name)
        if messenger.messenger_users.count() == 2:
            msgs_model = MessagesModel.objects.filter(messenger_room=messenger, is_readed=False)
            for i in msgs_model.exclude(sender=user):
                i.is_readed = True
                i.save()
        else:
            room = ClubsModel.objects.get(id=int(self.room_name))
            msgs_model = MessagesModel.objects.filter(messenger=room, is_readed=False)
            for i in msgs_model.exclude(sender=user):
                i.is_readed = True
                i.save()

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'msg_read_all',
                'method':'msg_read_all',
                'user_id': user.id,
            }
        )

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

        user = self.scope["user"]
        userprofile = UserProfile.objects.get(id=user.userprofile.id)
        userprofile.is_in_chat = False
        userprofile.save()

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        method = text_data_json['method']
        user = self.scope["user"]
        userprofile = UserProfile.objects.get(user=user)

        is_private_chat = self.room_name.startswith('i')

        if is_private_chat:
            try:
                messenger = MessengerModel.objects.get(room_id=self.room_name)

                if method == 'send_msg':
                    message = text_data_json['message']
                    msg_model = MessagesModel.objects.create(
                        msg=message,
                        messenger_room=messenger,
                        sender=user
                    )

                    other_user = messenger.messenger_users.exclude(id=user.id).first()

                    full_name = get_user_full_name(user)
                    user_capacity = get_user_capacity(user)

                    msg_model.save()
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'method': method,
                            'full_name': full_name,
                            'user_capacity': user_capacity,
                            'user_id': user.id,
                            'receiver_id': other_user.id if other_user else None,
                            'msg_id': msg_model.id,
                            'message': message,
                            'send_toast': False,
                            'is_active': True,
                            'creation_date': msg_model.creation_date.strftime('%H:%M'),
                        }
                    )

                elif method == 'msg_readed':
                    msg_id = text_data_json['msg_id']
                    msg_model = MessagesModel.objects.get(id=msg_id)
                    msg_model.is_readed = True
                    msg_model.save()
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'msg_readed',
                            'method': method,
                            'user_id': user.id,
                            'msg_id': msg_id,
                        }
                    )

            except MessengerModel.DoesNotExist:
                pass

        else:
            try:
                room = ClubsModel.objects.get(id=self.room_name)

                if method == 'send_msg':
                    receiver = room
                    is_blocked = BlockUserModel.objects.filter(creator=receiver, user=user).exists()

                    if not receiver.chat_enabled and user.userprofile.account_type != '2':
                        async_to_sync(self.channel_layer.group_send)(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'method': 'ChatDisabled',
                            }
                        )
                        return

                    if is_blocked:
                        async_to_sync(self.channel_layer.group_send)(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'method': 'Blocked',
                            }
                        )
                    else:
                        message = text_data_json['message']
                        msg_model = MessagesModel.objects.create(msg=message, messenger=room, sender=user)
                        full_name = get_user_full_name(user)
                        user_capacity = get_user_capacity(user)
                        send_toast = False
                        is_active = True

                        msg_model.save()
                        async_to_sync(self.channel_layer.group_send)(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'method': method,
                                'full_name': full_name,
                                'user_capacity': user_capacity,
                                'user_id': user.id,
                                'receiver_id': receiver.id,
                                'msg_id': msg_model.id,
                                'message': message,
                                'send_toast': send_toast,
                                'is_active': is_active,
                                'creation_date': msg_model.creation_date.strftime('%H:%M'),
                            }
                        )

                elif method == 'msg_readed':
                    msg_id = text_data_json['msg_id']
                    msg_model = MessagesModel.objects.get(id=msg_id)
                    msg_model.is_readed = True
                    msg_model.save()
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'msg_readed',
                            'method': method,
                            'user_id': user.id,
                            'msg_id': msg_id,
                        }
                    )

            except (ClubsModel.DoesNotExist, ValueError):
                pass


    def chat_message(self, event):
            self.send(text_data=json.dumps(event))

    def msg_readed(self, event):
        self.send(text_data=json.dumps(event))

    def msg_read_all(self, event):
        self.send(text_data=json.dumps(event))

    def showToast(self, event):
        self.send(text_data=json.dumps(event))

# code src = https://testdriven.io/blog/django-channels/, https://www.youtube.com/watch?v=cw8-KFVXpTE

