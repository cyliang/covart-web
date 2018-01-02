from django.http import JsonResponse

class SimpleTextResponse(JsonResponse):
    """
    A helper to have a quick ephemeral text response to an interactive action.
    """

    def __init__(self, text, *args, **kwargs):
        super(SimpleTextResponse, self).__init__({
            'response_type': 'ephemeral',
            'replace_original': False,
            'text': text,
        }, *args, **kwargs)

