from django import http
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, NON_FIELD_ERRORS
from django.dispatch.dispatcher import NO_RECEIVERS
from django.views.decorators import http as http_decorators, csrf as csrf_decorators
from django.forms import widgets, fields
from . import signals, Slack
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
            self.slack_method = 'action'
            return self.action(callback_id, action['name'], action['value'])
        elif payload.get('type', None) == 'dialog_submission':
            self.slack_method = 'submission'
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


class SlackFormMixin(object):
    """
    This mixin can be directly append on a FormView.
    It display the form on Slack with a dialog.

    It does not load the model object. To do this, use SlackModelFormMixin,
    SlackUpdateMixin, or SlackCreateMixin instead.
    """
    dialog_title = "Dialog Title"
    submit_label = None

    def action(self, callback_id, name, value):
        """
        This mixin assumes you want to open the Slack dialog on any action.

        Override this method to change this behavior. For example, you can
        return another response for some interaction.
        """
        self.open_dialog()
        return http.HttpResponse()

    def submission(self, callback_id, submission):
        """
        Velidate the form and perform the original action for valid/invalid
        submission. Note that the original response from form_valid is ignored.
        """
        form = self.get_form()

        if form.is_valid():
            # Do the original action, ignoring the returned response
            self.form_valid(form)

            # Return empty response to inform Slack the submission is valid.
            return http.HttpResponse()
        else:
            # Do the original action, ignoring the returned response
            self.form_invalid(form)

            # Return error message to Slack.
            return http.JsonResponse({'errors': [
                {
                    'name': field,
                    'error': error[0],
                }
                for field, error in form.errors
                if field != NON_FIELD_ERRORS
            ]})

    def get_form_kwargs(self):
        kwargs = super(SlackFormMixin, self).get_form_kwargs()

        if self.slack_method == 'action':
            kwargs.pop('files', None)
            kwargs.pop('data', None)
        elif self.slack_method == 'submission':
            kwargs['data'] = self.payload['submission']
        else:
            raise ValueError(
                "Unknown Slack method, which shall be either 'action' or " +
                "'submission'.")

        return kwargs

    def open_dialog(self):
        dialog={
            'callback_id': self.callback_id,
            'title': self.get_dialog_title(),
            'elements': list(self.get_form_fields()),
        }

        submit_label = self.get_submit_label()
        if submit_label != None:
            dialog['submit_label'] = submit_label

        slack = Slack()
        slack('dialog.open',
            trigger_id=self.payload['trigger_id'],
            dialog=dialog,
        )

    def get_dialog_title(self):
        if len(self.dialog_title) > 24:
            raise ImproperlyConfigured(
                "The dialog title is too long. " +
                "Slack allows 24 characters only.")
        return self.dialog_title

    def get_submit_label(self):
        if self.submit_label == None:
            return None
        if len(self.submit_label) > 24 or ' ' in self.submit_label:
            raise ImproperlyConfigured(
                "The submit label of the dialog is too long or contains more " +
                "than one word. Only 24 characters and single word are allowed")
        return self.submit_label

    def get_form_fields(self):
        form = self.get_form()
        if len(form.fields) > 5:
            raise ValueError(
                "The form contains more than 5 fields and this is not " +
                "allowed by Slack's dialog")

        for field in form:
            element = {
                'label': field.label[:24],
                'name': field.html_name,
                'optional': not field.field.required,
                'value': unicode(field.value()),
            }
            widget = field.field.widget

            if isinstance(field.field, fields.BooleanField):
                # Boolean field
                element.update({
                    'type': 'select',
                    'placeholder': field.help_text[:150],
                    'optional': False,
                    'options': [
                        {'label': 'Yes', 'value': 'True'},
                        {'label': 'No', 'value': 'False'},
                    ],
                })
            elif isinstance(widget, widgets.ChoiceWidget):
                if widget.allow_multiple_selected:
                    raise ValueError("Multiple selection is not supported")

                element.update({
                    'type': 'select',
                    'placeholder': field.help_text[:150],
                    'options': [
                        {'label': label[:75], 'value': value}
                        for value, label in widget.choices
                    ],
                })
            elif isinstance(widget, (widgets.Textarea, widgets.Input)):
                element.update({
                    'type': 'text',
                    'max_length': min(
                        getattr(field.field, 'max_length', None) or 150,
                        500),
                    'min_length': max(
                        getattr(field.field, 'min_length', None) or 1,
                        1),
                    'hint': field.help_text[:150],
                    'placeholder': field.label[:150],
                })

                if isinstance(widget, widgets.Textarea):
                    element['type'] = 'textarea'
                elif widget.input_type == 'text':
                    pass
                elif widget.input_type in ('email', 'number', 'url', 'tel'):
                    element['subtype'] = widget.input_type
                else:
                    raise ValueError("Input type is not supported by Slack.")
            else:
                raise ValueError("Field is currently not supported.")

            yield element


class SlackModelFormMixin(SlackFormMixin):

    def get_object(self):
        raise NotImplementedError("This method shall be reimplemented")


class SlackCreateMixin(SlackModelFormMixin):

    def action(self, callback_id, name, value):
        self.object = None
        return super(SlackCreateMixin, self).action(callback_id, name, value)

    def submission(self, callback_id, submission):
        self.object = None
        return super(SlackCreateMixin, self).submission(callback_id, submission)


class SlackUpdateMixin(SlackModelFormMixin):

    def action(self, callback_id, name, value):
        self.object = self.get_object()
        return super(SlackUpdateMixin, self).action(callback_id, name, value)

    def submission(self, callback_id, submission):
        self.object = self.get_object()
        return super(SlackUpdateMixin, self).submission(callback_id, submission)
