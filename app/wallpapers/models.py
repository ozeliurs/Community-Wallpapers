from django.db import models
from django.contrib.auth.models import User
import os
from django.utils import timezone
import datetime
import imagehash
from PIL import Image as PILImage
from django.core.exceptions import ValidationError

def get_upload_path(instance, filename):
    """Create a custom upload path for images"""
    # Just save directly to wallpapers folder with original filename
    return os.path.join('wallpapers', filename)

class Image(models.Model):
    """Model for storing uploaded images"""
    image = models.ImageField(upload_to=get_upload_path)
    source_url = models.URLField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    approval_date = models.DateTimeField(null=True, blank=True)
    image_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    
    def __str__(self):
        return f"Image uploaded on {self.upload_date.strftime('%Y-%m-%d %H:%M')}"
    
    def approve(self):
        """Approve the image for public display"""
        self.is_approved = True
        self.approval_date = timezone.now()
        self.save()
    
    def calculate_image_hash(self):
        """Calculate and store the perceptual hash of the image"""
        if not self.image:
            return None
        
        # Open the image
        img = PILImage.open(self.image.path)
        
        # Calculate the perceptual hash - a combination of different hash types
        # for better accuracy
        phash = str(imagehash.phash(img))
        dhash = str(imagehash.dhash(img))
        whash = str(imagehash.whash(img))
        
        # Combine the hashes to create a more robust fingerprint
        combined_hash = f"{phash}_{dhash}_{whash}"
        self.image_hash = combined_hash
        return combined_hash
    
    def save(self, *args, **kwargs):
        # For new instances, check for duplicates
        if not self.pk:  # Only check for new images
            # First, save the image to generate a path
            super().save(*args, **kwargs)
            # Calculate the hash
            self.calculate_image_hash()
            
            # Check for duplicates
            is_duplicate, duplicate_image = self.check_for_duplicates()
            
            if is_duplicate:
                # If duplicate is found, delete the image file to prevent orphaned files
                if self.image and hasattr(self.image, 'path') and os.path.exists(self.image.path):
                    os.remove(self.image.path)
                
                # Delete this object from the database to prevent creating a duplicate entry
                self.delete()
                
                # Raise a validation error with details about the duplicate
                duplicate_info = f" (uploaded on {duplicate_image.upload_date.strftime('%Y-%m-%d')})" if duplicate_image else ""
                raise ValidationError(f"This image appears to be a duplicate or very similar to an existing image{duplicate_info}.")
            
            # Save again with the hash (only if not a duplicate)
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    def check_for_duplicates(self):
        """Check if an image with the same hash already exists
        
        Returns:
            tuple: (is_duplicate, duplicate_image) 
                  is_duplicate is True if a duplicate was found, False otherwise
                  duplicate_image is the first duplicate Image object if found, None otherwise
        """
        if not self.image_hash:
            self.calculate_image_hash()
        
        # Split the combined hash back into components
        phash, dhash, whash = self.image_hash.split('_')
        
        # Check for exact hash matches
        duplicates = Image.objects.filter(image_hash=self.image_hash).exclude(pk=self.pk)
        
        if duplicates.exists():
            # Return True and the first duplicate image
            return True, duplicates.first()
        
        # Check for similar hashes (partial matches)
        # We'll query each hash component separately and then check the similarity
        similar_images = []
        
        for img in Image.objects.exclude(pk=self.pk):
            if not img.image_hash:
                continue
                
            img_phash, img_dhash, img_whash = img.image_hash.split('_')
            
            # Calculate Hamming distance (number of differing bits)
            # Lower distance means more similar images
            phash_distance = sum(c1 != c2 for c1, c2 in zip(phash, img_phash))
            dhash_distance = sum(c1 != c2 for c1, c2 in zip(dhash, img_dhash))
            whash_distance = sum(c1 != c2 for c1, c2 in zip(whash, img_whash))
            
            # Calculate an average similarity score (lower is more similar)
            avg_distance = (phash_distance + dhash_distance + whash_distance) / 3
            
            # If the average distance is below a threshold, consider it a duplicate
            # Threshold of 5 is relatively strict but allows for minor variations
            if avg_distance < 5:
                similar_images.append(img)
        
        if similar_images:
            # Return True and the first similar image
            return True, similar_images[0]
            
        # No duplicates found
        return False, None

class ImageOfTheDay(models.Model):
    """Model for tracking which image is selected for each day"""
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='featured_days')
    date = models.DateField(unique=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Image of the day - {self.date}"
    
    @classmethod
    def select_image_for_today(cls):
        """
        Select a random image for today that:
        1. Is approved
        2. Was not the image of yesterday
        3. Prioritizes images that haven't been featured yet or were featured long ago
        """
        today = timezone.now().date()
        
        # Check if we already have an image for today
        existing = cls.objects.filter(date=today).first()
        if existing:
            return existing
        
        # Get yesterday's image to avoid selecting it again
        yesterday = today - datetime.timedelta(days=1)
        yesterday_image_id = None
        yesterday_image = cls.objects.filter(date=yesterday).first()
        if yesterday_image:
            yesterday_image_id = yesterday_image.image.id
        
        # Get all approved images except yesterday's
        approved_images = Image.objects.filter(is_approved=True)
        if yesterday_image_id:
            approved_images = approved_images.exclude(id=yesterday_image_id)
        
        if not approved_images.exists():
            return None
        
        # Find images that have never been featured
        never_featured = approved_images.exclude(
            id__in=cls.objects.values_list('image__id', flat=True)
        )
        
        if never_featured.exists():
            # Select a random image from never featured
            from random import choice
            selected_image = choice(list(never_featured))
        else:
            # Select the image that was featured longest time ago
            # or the least number of times
            featured_counts = {}
            for img in approved_images:
                featured_counts[img.id] = cls.objects.filter(image=img).count()
            
            min_count = min(featured_counts.values())
            least_featured = [img_id for img_id, count in featured_counts.items() if count == min_count]
            
            from random import choice
            selected_image = Image.objects.get(id=choice(least_featured))
        
        # Create the image of the day record
        return cls.objects.create(image=selected_image, date=today)
