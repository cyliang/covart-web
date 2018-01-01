from django import http
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.dispatch.dispatcher import NO_RECEIVERS
from django.views.decorators import http as http_decorators, csrf as csrf_decorators
from . import signals
import json

def SimpleTextResponse(text):
    return http.JsonResponse({
        'response_type': 'ephemeral',
        'replace_original': False,
        'text': text,
    })

def slack_interaction(verification_token=None):
    token = verification_token or getattr(settings, 'SLACK_VERIFY_TOKEN', None)
    if token == None:
        raise ImproperlyConfigured('Set SLACK_VERIFY_TOKEN in your settings.')

    @csrf_decorators.csrf_exempt
    @http_decorators.require_POST
    def view(request):
        try:
            payload = json.loads(request.POST['payload'])
            token = payload['token']
            callback_id = payload['callback_id']
        except KeyError, ValueError:
            return http.HttpResponseBadRequest("Can't deserialize the payload.")

        if token != view.verification_token:
            return http.HttpResponseForbidden("Fail to verify the token.")

        # Send signal manually to make sure the request is processed only once.
        signal = signals.slack_request
        sender = None

        for receiver in signal._live_receivers(sender):
            response = receiver(signal=signal, sender=sender,
                callback_id=callback_id,
                payload=payload,
                request=request,
            )

            if isinstance(response, http.HttpResponse):
                return response

        return SimpleTextResponse(
            'Sorry, this action is currently not implemented yet.')

    view.verification_token = token
    return view
