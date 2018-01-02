from django import http
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.dispatch.dispatcher import NO_RECEIVERS
from django.views.decorators import http as http_decorators, csrf as csrf_decorators
from . import signals
from .helpers import SimpleTextResponse
import json

class SlackRequestDispatcher(object):
    verification_token = None

    @classmethod
    def as_view(cls, verification_token=None, **initargs):
        verification_token = (
            verification_token or cls.verification_token or
            getattr(settings, 'SLACK_VERIFY_TOKEN', None))
        if verification_token == None:
            raise ImproperlyConfigured(
                'Verification Token is not configured. ' +
                'Assign verification_token of this class or ' +
                'set SLACK_VERIFY_TOKEN in your settings.')

        @csrf_decorators.csrf_exempt
        @http_decorators.require_POST
        def view(request):
            try:
                payload = json.loads(request.POST['payload'])
                token = payload['token']
                callback_id = payload['callback_id']
            except KeyError, ValueError:
                return http.HttpResponseBadRequest(
                    "I cannot deserialize your payload.")

            if token != view.verification_token:
                return http.HttpResponseForbidden(
                    "I cannot verify your token.")

            handler = view.dispatcher_cls(**initargs).dispatch(callback_id)
            if handler == None:
                return SimpleTextResponse(
                    'Sorry, this action is currently not implemented yet.')

            handler.request = request
            handler.payload = payload
            handler.callback_id = callback_id
            return handler.dispatch(request, callback_id, payload)

        view.verification_token = verification_token
        view.dispatcher_cls = cls
        return view

    def dispatch(self, callback_id):
        """
        Derived class shall override this method to determine a handler, which
        is a SlackRequestHandler, for the specified callback_id.
        This method shall return a instance of subclass of SlackRequestHandler
        to handle the request, or return None to reject the request.
        """
        raise NotImplementedError(
            "Implement dispatch() to handle the request from Slack")


class SlackRequestHandler(object):

    def dispatch(self, request, callback_id, payload):
        """
        Determine what triggered this Slack interactive request and dispatch
        the request to the dedicated handler.
        """
        if 'actions' in payload:
            action = payload['actions'][0]
            return self.action(callback_id, action['name'], action['value'])
        elif payload.get('type', None) == 'dialog_submission':
            return self.submission(callback_id, payload['submission'])

        return http.HttpResponseNotFound("Unknown Slack request.")

    def action(self, callback_id, name, value):
        """
        This method is called when Slack's interactive request is triggered
        by an user's action, such as button clicking.
        Return a JsonResponse to handle the request.
        """
        raise NotImplementedError(
            "An 'action' request is received but the handler is not " +
            "implemeted.")

    def submission(self, callback_id, submission):
        """
        This method is called when an user submits the dialog form in Slack.
        Return an empty HttpResponse if the submission is valid or a
        JsonResponse to report errors in the invalid submission.

        The response has to be made in 3 seconds. Additional operations cannot
        be included in the response and have to be performed with separated
        API calls.
        """
        raise NotImplementedError(
            "An 'dialog_submission' request is received but the handler is " +
            "not implemented.")


class SlackAccessMixin(object):

    def dispatch(self, request, callback_id, payload):
        try:
            from social_django.models import UserSocialAuth
            slack_uid = payload['user']['id']
            user = UserSocialAuth.get_social_auth('slack', slack_uid).user
        except ImportError:
            raise ImproperlyConfigured(
                "This mixin cooperates with the package social_django. Make " +
                "sure you are also using that package for auth management.")
        except KeyError, AttributeError:
            pass

        if user != None:
            self.user = user
            request.user = user
        return super(SlackAccessMixin, self).dispatch(
            request, callback_id, payload)

    def handle_no_permission(self):
        """
        This is the handler when the authentication fails. Return a response
        to inform the user about this.
        """
        return SimpleTextResponse(
            "Sorry, I cannot identify your Slack account.")
