from django import template
from django.utils.text import mark_safe
from django.conf import settings

register = template.Library()

@register.simple_tag
def google_analytics():
    try:
        analytics_id = settings.GOOGLE_ANALYTICS_ID
    except:
        return ''

    return mark_safe("""
    <script>
      (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
      (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
      m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
      })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

      ga('create', '%s', 'auto');
      ga('send', 'pageview');

    </script>
    """ % analytics_id)
