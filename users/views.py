from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework import permissions, status
from .serializers import SignupSerialzier
from .models import CustomUser, NEW, CODE_VERIFIY, DONE, PHOTO_DONE, VIA_EMAIL, VIA_PHONE
from rest_framework.views import APIView
from datetime import datetime
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.core.mail import send_mail

class SignUpView(CreateAPIView):
    permission_classes = (permissions.AllowAny, )
    serializer_class = SignupSerialzier
    queryset = CustomUser.objects.all()

class CodeVerify(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        user = request.user
        code = self.request.data.get('code')
        codes = self.verify_codes.filter(code = code, expiration_time__gte = datetime.now(), is_active=True)

        if not code.exists():
            raise ValidationError({"message": "Kodingiz xato yoki eskirgan", "status": status.HTTP_400_BAD_REQUEST})
        else:
            codes.update(is_active=True)

        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIY
            user.save()

        response_data = {
            "message": "Kod Tasdiqlandi",
            "status": status.HTTP_200_OK,
            "access": user.token()['access'],
            "refresh": user.token()['refresh']
        }
        return Response(response_data)

class GetNewCode(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        user = request.user     
        code = user.verify_codes.filter(expiration_time__gte = datetime.now(), is_active=False)
        
        if code.exists():
            raise ValidationError({"message": "Sizda hali active kod bor", "status": status.HTTP_400_BAD_REQUEST})
        else:
            if user.auth_type == VIA_EMAIL:
                code = user.generate_code(VIA_EMAIL)
                send_mail(
                    subject="Tasdiqlash kodi",
                    message=f"Sizning tasdiqlash kodingiz: {code}",
                    from_email="yoqubov11nodir@gmail.com",
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            elif user.auth_type == VIA_PHONE:
                code = user.generate_code(VIA_PHONE)
                print(f"SMS code for {user.phone_number}: {code}")
        
        response_data = {
            "message": "Kod yuborildi",
            "status": status.HTTP_201_CREATED,
        }
        return Response(response_data)