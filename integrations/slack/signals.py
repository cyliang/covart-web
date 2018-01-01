from django.dispatch import Signal

slack_request = Signal(providing_args=[
    'callback_id', 'actions', 'payload', 'request'
])
"""
A signal fired for each incoming Slack request.
Receivers intending to handle the request shall return a HttpResponse instance;
otherwise, return other values for ignoring.
"""
