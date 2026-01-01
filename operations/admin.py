from django.contrib import admin
from .models import Mission, MissionSubmission, Attendance, TrainingSession

admin.site.register(Mission)
admin.site.register(MissionSubmission)
admin.site.register(Attendance)
admin.site.register(TrainingSession)