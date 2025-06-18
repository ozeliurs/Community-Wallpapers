from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse

from .models import Image, ImageOfTheDay
from .forms import ImageUploadForm, ImageURLForm

class HomeView(ListView):
    """Home page view showing the most recently approved images"""
    model = Image
    template_name = 'wallpapers/home.html'
    context_object_name = 'images'
    paginate_by = 12
    
    def get_queryset(self):
        return Image.objects.filter(is_approved=True).order_by('-approval_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get today's featured image
        image_of_the_day = ImageOfTheDay.select_image_for_today()
        context['image_of_the_day'] = image_of_the_day
        return context

class ImageDetailView(DetailView):
    """Detail view for a single image"""
    model = Image
    template_name = 'wallpapers/image_detail.html'
    context_object_name = 'image'
    
    def get_queryset(self):
        # For non-staff users, only show approved images
        if self.request.user.is_staff:
            return Image.objects.all()
        return Image.objects.filter(is_approved=True)

def upload_image(request):
    """View for uploading images from a file"""
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save()
            if image:
                messages.success(request, 'Your image has been uploaded and is pending approval.')
                return redirect('image_detail', pk=image.pk)
            else:
                # If save returned None, it means no image was created (e.g., a duplicate)
                # The form's non_field_errors will contain the error message
                pass
        
        # If there are non-field errors (like captcha failures or duplicates), display them
        for error in form.non_field_errors():
            messages.error(request, error)
    else:
        form = ImageUploadForm()
    
    return render(request, 'wallpapers/upload.html', {
        'form': form,
        'upload_type': 'file'
    })

def upload_image_url(request):
    """View for uploading images from a URL"""
    if request.method == 'POST':
        form = ImageURLForm(request.POST)
        if form.is_valid():
            try:
                image = form.save()
                if image:
                    messages.success(request, 'Your image has been uploaded from URL and is pending approval.')
                    return redirect('image_detail', pk=image.pk)
                else:
                    # If save returned None, it means no image was created (e.g., a duplicate)
                    # The form's non_field_errors will contain the error message
                    pass
            except Exception as e:
                messages.error(request, f'Error downloading image: {e}')
        
        # If there are non-field errors (like captcha failures or duplicates), display them
        for error in form.non_field_errors():
            messages.error(request, error)
    else:
        form = ImageURLForm()
    
    return render(request, 'wallpapers/upload.html', {
        'form': form,
        'upload_type': 'url'
    })

@method_decorator(staff_member_required, name='dispatch')
class PendingReviewListView(ListView):
    """Admin view for listing images pending review"""
    model = Image
    template_name = 'wallpapers/pending_review.html'
    context_object_name = 'images'
    paginate_by = 20
    
    def get_queryset(self):
        return Image.objects.filter(is_approved=False).order_by('upload_date')

@staff_member_required
def approve_image(request, pk):
    """Admin view for approving an image"""
    image = get_object_or_404(Image, pk=pk)
    image.approve()
    messages.success(request, f'Image has been approved.')
    return redirect('pending_review')

def image_of_the_day(request):
    """View for displaying the image of the day"""
    image_of_day = ImageOfTheDay.select_image_for_today()
    
    if not image_of_day:
        return render(request, 'wallpapers/no_image_of_the_day.html')
    
    return render(request, 'wallpapers/image_of_the_day.html', {
        'image_of_the_day': image_of_day
    })

def image_of_the_day_api(request):
    """API endpoint for getting the image of the day"""
    image_of_day = ImageOfTheDay.select_image_for_today()
    
    if not image_of_day:
        return JsonResponse({'error': 'No approved images available'}, status=404)
    
    return JsonResponse({
        'date': image_of_day.date,
        'image': {
            'id': image_of_day.image.id,
            'url': request.build_absolute_uri(image_of_day.image.image.url)
        }
    })

def image_of_the_day_direct(request):
    """Direct image of the day endpoint - returns the raw image file
    
    This allows direct access to the image file without HTML wrapping,
    making it suitable for curl requests like: curl <url>/image-of-the-day.jpeg
    """
    from django.http import HttpResponse, Http404
    from django.views.decorators.cache import cache_control
    import os
    
    image_of_day = ImageOfTheDay.select_image_for_today()
    
    if not image_of_day:
        raise Http404("No image of the day available")
    
    # Get the file path
    image_file = image_of_day.image.image.path
    
    # Get the file extension
    _, ext = os.path.splitext(image_file)
    
    # Map file extension to MIME type
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    content_type = content_type_map.get(ext.lower(), 'application/octet-stream')
    
    # Read the file content
    with open(image_file, 'rb') as f:
        image_data = f.read()
    
    # Return the raw image with appropriate content type
    response = HttpResponse(image_data, content_type=content_type)
    
    # Add cache control headers (optional, to improve performance)
    response['Cache-Control'] = 'max-age=3600'  # Cache for 1 hour
    
    return response
