from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from .forms import MessageForm
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone

User = get_user_model()

# Create your views here.

@login_required
def inbox(request):
    messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'messaging/inbox.html', {'messages': messages})

@login_required
def send_message(request, recipient_id):
    recipient = get_object_or_404(User, pk=recipient_id)
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, recipient)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.recipient = recipient
            message.save()
            return redirect('messaging:conversation', conversation_id=conversation.id)
    else:
        form = MessageForm()
    return render(request, 'messaging/send_message.html', {'form': form, 'recipient': recipient})

@login_required
def view_message(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if request.user not in message.conversation.participants.all():
        return redirect('messaging:inbox')
    message.is_read = True
    message.save()
    return render(request, 'messaging/view_message.html', {'message': message})

@login_required
def sent_messages(request):
    messages = Message.objects.filter(sender=request.user).order_by('-created_at')
    return render(request, 'messaging/sent_messages.html', {'messages': messages})

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    # Ensure user is either sender or recipient
    if request.user != message.sender and request.user != message.recipient:
        messages.error(request, "You don't have permission to view this message.")
        return redirect('messaging:inbox')
    
    # Mark message as read if user is recipient
    if request.user == message.recipient and not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
    
    # Handle reply form
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.recipient = message.sender if request.user == message.recipient else message.recipient
            reply.conversation = message.conversation
            reply.save()
            messages.success(request, "Reply sent successfully!")
            return redirect('messaging:message_detail', message_id=message.id)
    else:
        form = MessageForm()
    
    context = {
        'message': message,
        'form': form,
    }
    return render(request, 'messaging/message_detail.html', context)

@login_required
def conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        return redirect('messaging:inbox')
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    return render(request, 'messaging/conversation.html', {'conversation': conversation, 'messages': messages})
