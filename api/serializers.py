# api/serializers.py

from rest_framework import serializers
from .models import User

# This serializer will handle creating a new user
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')

    class Meta:
        model = User
        # Removed 'username' from the fields tuple as email is the primary identifier
        fields = ('first_name', 'last_name', 'email', 'phone', 'dob', 'password', 'password2')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            # dob is optional by default for DateField with allow_null=True/required=False
            # but we need to handle its absence in the create method
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Safely get 'dob' from validated_data, will be None if not provided
        dob = validated_data.get('dob')

        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            dob=dob, # Use the safely retrieved dob value
            password=validated_data['password']
        )
        return user

# This serializer will return user data after a successful login
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'dob', 'membership_type', 'is_active_annual_member', 'annual_membership_expiry_date')
