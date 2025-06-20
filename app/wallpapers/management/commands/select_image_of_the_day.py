from django.core.management.base import BaseCommand
from wallpapers.models import ImageOfTheDay

class Command(BaseCommand):
    help = 'Selects an image of the day if one is not already selected for today'

    def handle(self, *args, **options):
        image_of_day = ImageOfTheDay.select_image_for_today()
        
        if image_of_day:
            self.stdout.write(self.style.SUCCESS(
                f'Successfully selected "{image_of_day.image.title}" as the image of the day for {image_of_day.date}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'No image could be selected for today. Make sure you have approved images in the system.'
            ))
