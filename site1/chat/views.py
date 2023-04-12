from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, pagination
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User
from .models import Thread, Message
from .serializers import ThreadSerializer, MessageSerializer
from django.db.models import Count


class ThreadViewSet(viewsets.ModelViewSet):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer

    @action(detail=False, methods=['post'], url_path='create_or_get')
    def create_or_get_thread(self, request):
        participants = request.data.get('participants', [])

        if len(participants) != 2:
            return Response({"detail": "A thread must have exactly 2 participants."}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(id__in=participants)

        if users.count() != 2:
            return Response({"detail": "One or both users not found."}, status=status.HTTP_404_NOT_FOUND)

        thread = Thread.objects.filter(participants__in=participants).annotate(
            participants_count=Count("participants")
        ).filter(participants_count=2)

        if thread.exists():
            thread = thread.first()
        else:
            thread = Thread.objects.create()
            thread.participants.set(users)
            thread.save()

        serializer = self.get_serializer(thread)
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        thread = get_object_or_404(Thread, pk=pk)
        thread.delete()
        return Response({"message": f"Thread ID {pk} was successfully deleted"},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def threads_for_user(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        threads = Thread.objects.filter(participants=user)

        paginator = pagination.LimitOffsetPagination()
        paginated_threads = paginator.paginate_queryset(threads, request)

        serializer = self.get_serializer(paginated_threads, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    @action(detail=False, methods=['post'], url_path='create')
    def create_message(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='thread/(?P<thread_id>[^/.]+)')
    def messages_for_thread(self, request, thread_id):
        thread = get_object_or_404(Thread, id=thread_id)
        messages = Message.objects.filter(thread=thread)

        paginator = pagination.LimitOffsetPagination()
        paginated_messages = paginator.paginate_queryset(messages, request)

        serializer = self.get_serializer(paginated_messages, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='mark_read')
    def mark_message_read(self, request, pk=None):
        message = get_object_or_404(Message, pk=pk)
        message.is_read = True
        message.save()
        serializer = self.get_serializer(message)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='unread_count/(?P<user_id>[^/.]+)')
    def unread_count_for_user(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        unread_messages = Message.objects.filter(thread__participants=user, is_read=False).exclude(sender=user)
        count = unread_messages.count()
        return Response({"unread_count": count})
