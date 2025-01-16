import json
from channels.generic.websocket import AsyncWebsocketConsumer

class HospitalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.hospital_id = self.scope['url_route']['kwargs']['hospital_id']
        self.room_group_name = f'hospital_{self.hospital_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        data = text_data_json.get('data')

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'hospital_message',
                'message_type': message_type,
                'data': data
            }
        )

    # Receive message from room group
    async def hospital_message(self, event):
        message_type = event['message_type']
        data = event['data']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': message_type,
            'data': data
        }))