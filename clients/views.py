from django.contrib.auth import logout
# Create your views here.
from rest_framework.exceptions import AuthenticationFailed

from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from clients.token_blacklist import add_to_blacklist, is_token_revoked
from .models import  Project, User
from .serializers import  ProjectSerializer, UserImageSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer
from rest_framework.views import APIView
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework_jwt.utils import jwt_decode_handler

@api_view(['POST'])
def user_registration_view(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomObtainTokenView(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = response.data['token']
        decoded_token = jwt_decode_handler(token)
        user_id = decoded_token['user_id']
        user = User.objects.get(pk=user_id)
        return Response({'token': token, 'username': user.username})
    
    
class LogoutView(APIView):
    def post(self, request):
        token = request.data.get('token')  # Get the token from the request body

        if token:
            if is_token_revoked(token):  # Check if the token is already revoked
                return Response({'detail': 'Token already revoked'}, status=400)

            add_to_blacklist(token)  # Add the token to the blacklist or mark it as revoked
            logout(request)
            return Response({'detail': 'Logout successful'})
        else:
            return Response({'detail': 'Token not provided'}, status=400)



class VerifyTokenView(APIView):
    def post(self, request):
        

        token = request.data.get('token')  # Get the token from the request body

        if not token:
            return Response({'authenticated': False, 'message': 'Token not provided'}, status=status.HTTP_400_BAD_REQUEST)  # Get the token from the request body

        if token and is_token_revoked(token):  # Check if the token is in the blacklist
            return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({'authenticated': True})

class UserFileView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        return self.handle_request(request, 'POST')

    def get(self, request, format=None):
        return self.handle_request(request, 'GET')

    def put(self, request, format=None):
        return self.handle_request(request, 'PUT')

    def delete(self, request, format=None):
        return self.handle_request(request, 'DELETE')

    def handle_request(self, request, method):
        try:
            self.authenticate(request)
        except AuthenticationFailed as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserImageSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            image = request.FILES.get('image')

            if method == 'POST':
                user.image = image
                
            elif method == 'PUT':
                if user.image:
                    user.image.delete()  # Delete the existing image
                user.image = image
            elif method == 'DELETE':
                if user.image:
                    user.image.delete()
                    user.image = None

            user.save()

            context = {
                'user': user.username,
                'image': user.get_image_url
            }
            return Response(context)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]  # Get the token from the Authorization header

        try:
            payload = jwt_decode_handler(token)
            decoded_token = jwt_decode_handler(token)
            user_id = decoded_token['user_id']
            user = User.objects.get(pk=user_id)
            request.user = user
        except Exception as e:
            raise AuthenticationFailed('Invalid token.')


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer