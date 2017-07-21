from . import models

def weekly_update():
    models.MeetingHistory.rotate_next_meeting()
