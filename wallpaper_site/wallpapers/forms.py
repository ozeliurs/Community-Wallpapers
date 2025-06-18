from django import forms
from .models import Image
import requests
from io import BytesIO
from django.core.files.images import ImageFile
from PIL import Image as PILImage
from .utils import verify_captcha
from django.utils import timezone
from django.core.exceptions import ValidationError

ASPECT_RATIO = 16 / 9
ASPECT_RATIO_MARGIN = 0.3

class ImageUploadForm(forms.ModelForm):
    """Form for uploading images from a file"""
    captcha_token = forms.CharField(widget=forms.HiddenInput(), required=True)
    
    class Meta:
        model = Image
        fields = ['image']
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Check image dimensions using PIL
            img = PILImage.open(image)
            width, height = img.size
            
            # Check minimum resolution (1920x1080)
            if width < 1920 or height < 1080:
                raise forms.ValidationError(
                    f'Image resolution is too low ({width}x{height}). Minimum required is 1920x1080.'
                )
            
            # Check aspect ratio (16:9)
            aspect_ratio = width / height
            
            # Allow for a small margin of error
            if abs(aspect_ratio - ASPECT_RATIO) > ASPECT_RATIO_MARGIN:
                raise forms.ValidationError(
                    f'Image aspect ratio is {aspect_ratio:.2f}, but must be 16:9 (1.78) +- {ASPECT_RATIO_MARGIN}.'
                )
                
        return image
    
    def clean(self):
        cleaned_data = super().clean()
        captcha_token = cleaned_data.get('captcha_token')
        
        if not captcha_token:
            raise forms.ValidationError('Captcha verification is required')
        
        if not verify_captcha(captcha_token):
            raise forms.ValidationError('Captcha verification failed')
        
        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        try:
            if commit:
                instance.save()
            return instance
        except ValidationError as e:
            # Add the error to the form
            self.add_error(None, str(e))
            # Return None to indicate no object was created
            return None

class ImageURLForm(forms.Form):
    """Form for uploading images from a URL"""
    image_url = forms.URLField(help_text="Enter the URL of the image you want to upload")
    captcha_token = forms.CharField(widget=forms.HiddenInput(), required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        captcha_token = cleaned_data.get('captcha_token')
        
        if not captcha_token:
            raise forms.ValidationError('Captcha verification is required')
        
        if not verify_captcha(captcha_token):
            raise forms.ValidationError('Captcha verification failed')
        
        return cleaned_data
    
    def clean_image_url(self):
        """Validate that the URL points to an image and meets resolution/aspect ratio requirements"""
        url = self.cleaned_data['image_url']
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Open the image to check dimensions
            img = PILImage.open(BytesIO(response.content))
            img.verify()  # Verify it's an image
            
            # Re-open the image after verify() to get dimensions
            img = PILImage.open(BytesIO(response.content))
            width, height = img.size
            
            # Check minimum resolution (1920x1080)
            if width < 1920 or height < 1080:
                raise forms.ValidationError(
                    f'Image resolution is too low ({width}x{height}). Minimum required is 1920x1080.'
                )
            
            # Check aspect ratio (16:9)
            aspect_ratio = width / height
            
            # Allow for a small margin of error
            if abs(aspect_ratio - ASPECT_RATIO) > ASPECT_RATIO_MARGIN:
                raise forms.ValidationError(
                    f'Image aspect ratio is {aspect_ratio:.2f}, but must be 16:9 (1.78) +- {ASPECT_RATIO_MARGIN}.'
                )
                
            return url
        except requests.exceptions.RequestException as e:
            raise forms.ValidationError(f"Error downloading image: {e}")
        except forms.ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise forms.ValidationError(f"Invalid image URL: {e}")
    
    def save(self):
        """Download the image from URL and create an Image instance"""
        url = self.cleaned_data.get('image_url')
        
        # Download the image
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Extract filename from URL
        import os
        from urllib.parse import urlparse
        
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # If filename is empty or invalid, use a generic name
        if not filename or '.' not in filename:
            filename = f"image_from_url_{timezone.now().strftime('%Y%m%d%H%M%S')}.jpg"
        
        # Create Image instance
        img_io = BytesIO(response.content)
        img_file = ImageFile(img_io, name=filename)
        
        image = Image(image=img_file, source_url=url)
        try:
            image.save()
            return image
        except ValidationError as e:
            # Add the error to the form
            self.add_error(None, str(e))
            # Return None to indicate no object was created
            return None
