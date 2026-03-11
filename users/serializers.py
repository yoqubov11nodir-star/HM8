from rest_framework import serializers, status
from .models import CodeVerifiy, CustomUser, VIA_EMAIL, VIA_PHONE, CODE_VERIFIY, DONE
from rest_framework.exceptions import ValidationError
from shared.utility import check_email_or_phone
from django.db.models import Q
from django.core.mail import send_mail

class SignupSerialzier(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_status = serializers.CharField(read_only=True)
    auth_type = serializers.CharField(read_only=True)

    def __init__(self, instance=None, data=..., **kwargs):
        super().__init__(instance, data, **kwargs)
        self.fields['email_or_phone'] = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'auth_status', 'auth_type']

    def create(self, validated_data):
      
        user_input = self.context['request'].data.get('email_or_phone')
        data = self.auth_validate(user_input)
        
        user = CustomUser.objects.create_user(**data)
        
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

        user.save()
        return user

    def validate(self, attrs):
        user_input = self.context['request'].data.get('email_or_phone')
        self.auth_validate(user_input)
        self.validate_email_or_phone(user_input)
        return attrs

    @staticmethod
    def auth_validate(user_input):
        user_input_type = check_email_or_phone(user_input)
        if user_input_type == 'phone':
            return {'auth_type': VIA_PHONE, 'phone_number': user_input}
        elif user_input_type == 'email':
            return {'auth_type': VIA_EMAIL, 'email': user_input}
        return None

    def validate_email_or_phone(self, email_or_phone):
        if CustomUser.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone)).exists():
            raise ValidationError(detail="Bu email yoki telefon raqam bilan oldin ro'yxatdan o'tilgan.")
        return email_or_phone
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['message'] = 'Kodingiz yuborildi'
        data['refresh'] = instance.token()['refresh']
        data['access'] = instance.token()['access']
        return data
    
class UserChangeInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        return attrs
    
    def validate_username(self, value):
        if not value.isalnum() and '_' not in value:
            raise ValidationError("Username faqat harf, raqam va pastki chiziqdan iborat bo'lishi kerak.")
        
        if len(value) < 5:
            raise ValidationError("Username kamida 5 ta belgidan iborat bo'lishi kerak.")

        if CustomUser.objects.filter(username=value).exists():
            raise ValidationError("Bu username band. Iltimos, boshqasini tanlang.")
        
        return value

    def validate_first_name(self, value):
        if any(char.isdigit() for char in value):
            raise ValidationError("Ismda raqamlar ishlatilishi mumkin emas.")
        
        return value.strip()

    def validate_last_name(self, value):
        if any(char.isdigit() for char in value):
            raise ValidationError("Familiyada raqamlar ishlatilishi mumkin emas.")
        
        return value.strip()

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name')
        instance.last_name = validated_data.get('last_name')
        instance.username = validated_data.get('username')
        instance.password.set_password(validated_data.get('password'))
        if instance.auth_status != CODE_VERIFIY:
            raise ValidationError({"message": "Siz hali tasdiqlanmagansiz", "status": status.HTTP_400_BAD_REQUEST})
        instance.auth_status = DONE
        instance.save()

        return instance