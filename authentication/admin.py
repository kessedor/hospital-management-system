from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Hospital, Staff, Patient,
    InventoryCategory, InventoryItem, InventoryTransaction
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Additional info', {'fields': ('user_type', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )
    list_display = ('username', 'email', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def save_model(self, request, obj, form, change):
        if not change:  # Only for new users
            if obj.user_type == 'HOSPITAL':
                obj.is_staff = True  # Give staff status to hospital users
        super().save_model(request, obj, form, change)

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_number', 'total_beds', 'available_beds', 'emergency_status')
    list_filter = ('emergency_status', 'created_at')
    search_fields = ('name', 'registration_number', 'address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'registration_number', 'address', 'primary_phone')
        }),
        ('Capacity Information', {
            'fields': ('total_beds', 'available_beds')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Status', {
            'fields': ('emergency_status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(user_type='HOSPITAL')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'employee_id', 'role', 'department', 'status')
    list_filter = ('role', 'department', 'status', 'joining_date')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id')
    readonly_fields = ('created_at', 'updated_at')

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(user_type='STAFF')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'patient_id', 'status', 'blood_group', 'admission_date')
    list_filter = ('status', 'blood_group', 'gender', 'admission_date')
    search_fields = ('user__first_name', 'user__last_name', 'patient_id')
    readonly_fields = ('created_at', 'updated_at')

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(user_type='PATIENT')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'hospital', 'category', 'quantity', 'unit')
    list_filter = ('hospital', 'category', 'criticality', 'created_at')
    search_fields = ('name', 'description', 'hospital__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('hospital', 'category', 'name', 'description')
        }),
        ('Stock Information', {
            'fields': ('quantity', 'unit', 'minimum_stock', 'criticality')
        }),
        ('Financial Information', {
            'fields': ('unit_price',),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('expiry_date', 'supplier_info', 'storage_location', 'last_ordered_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'transaction_type', 'quantity', 'performed_by', 'transaction_date')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('item__name', 'notes', 'reference_number')
    readonly_fields = ('transaction_date', 'previous_quantity', 'new_quantity')
    fieldsets = (
        ('Transaction Information', {
            'fields': ('item', 'transaction_type', 'quantity', 'performed_by')
        }),
        ('Additional Information', {
            'fields': ('notes', 'reference_number')
        }),
        ('Transaction Details', {
            'fields': ('transaction_date', 'previous_quantity', 'new_quantity'),
            'classes': ('collapse',)
        }),
    )