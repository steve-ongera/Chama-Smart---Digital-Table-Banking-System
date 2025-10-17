from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import (
    User, Chama, ChamaMembership, ContributionCycle, Contribution,
    Payout, Loan, LoanRepayment, Meeting, MeetingAttendance,
    Notification, AuditLog
)


# Custom Admin Site Configuration
admin.site.site_header = "Chama Smart Admin"
admin.site.site_title = "Chama Smart"
admin.site.index_title = "Chama Management System"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User Admin with custom fields"""
    
    list_display = [
        'username', 'get_full_name_display', 'email', 'phone_number', 
        'role', 'is_verified', 'two_factor_enabled', 'is_active', 'date_joined'
    ]
    list_filter = [
        'role', 'is_verified', 'two_factor_enabled', 'is_active', 
        'is_staff', 'date_joined'
    ]
    search_fields = ['username', 'email', 'phone_number', 'first_name', 'last_name']
    readonly_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 
                      'national_id', 'date_of_birth', 'profile_picture')
        }),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 
                      'is_verified', 'two_factor_enabled', 'groups', 'user_permissions')
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 
                      'password2', 'role', 'is_staff', 'is_active'),
        }),
    )
    
    def get_full_name_display(self, obj):
        return obj.get_full_name() or '-'
    get_full_name_display.short_description = 'Full Name'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()


@admin.register(Chama)
class ChamaAdmin(admin.ModelAdmin):
    """Chama Admin with financial summaries"""
    
    list_display = [
        'name', 'contribution_amount', 'contribution_frequency', 
        'get_member_count', 'get_total_contributions', 'status', 
        'created_by', 'created_at'
    ]
    list_filter = ['status', 'contribution_frequency', 'created_at']
    search_fields = ['name', 'registration_number', 'created_by__username']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'get_member_count',
        'get_total_contributions', 'get_active_loans'
    ]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description', 'registration_number', 'status')
        }),
        (_('Financial Settings'), {
            'fields': ('contribution_amount', 'contribution_frequency', 
                      'late_payment_penalty', 'loan_interest_rate', 'max_members')
        }),
        (_('Meeting Details'), {
            'fields': ('meeting_day', 'meeting_time', 'meeting_location'),
            'classes': ('collapse',)
        }),
        (_('Banking Information'), {
            'fields': ('bank_account_name', 'bank_account_number', 'bank_name',
                      'mpesa_paybill', 'mpesa_account_number'),
            'classes': ('collapse',)
        }),
        (_('Documents'), {
            'fields': ('constitution_document',),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('get_member_count', 'get_total_contributions', 'get_active_loans'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member_count(self, obj):
        count = obj.memberships.filter(status='ACTIVE').count()
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            count
        )
    get_member_count.short_description = 'Active Members'
    
    def get_total_contributions(self, obj):
        total = obj.contributions.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or 0
        return format_html(
            '<span style="color: blue; font-weight: bold;">KES {:,.2f}</span>',
            total
        )
    get_total_contributions.short_description = 'Total Contributions'
    
    def get_active_loans(self, obj):
        count = obj.loans.filter(status='ACTIVE').count()
        total = obj.loans.filter(status='ACTIVE').aggregate(
            total=Sum('balance')
        )['total'] or 0
        return format_html(
            '{} loans (KES {:,.2f})',
            count, total
        )
    get_active_loans.short_description = 'Active Loans'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('created_by').prefetch_related('memberships')


@admin.register(ChamaMembership)
class ChamaMembershipAdmin(admin.ModelAdmin):
    """Membership Admin with contribution tracking"""
    
    list_display = [
        'membership_number', 'get_member_name', 'chama', 
        'position_in_rotation', 'status', 'has_received_payout',
        'total_contributed', 'joined_date'
    ]
    list_filter = ['status', 'has_received_payout', 'chama', 'joined_date']
    search_fields = [
        'membership_number', 'user__username', 'user__email', 
        'chama__name', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = [
        'id', 'total_contributed', 'created_at', 'updated_at',
        'get_contribution_summary'
    ]
    
    fieldsets = (
        (_('Membership Details'), {
            'fields': ('chama', 'user', 'membership_number', 
                      'position_in_rotation', 'status')
        }),
        (_('Payout Information'), {
            'fields': ('has_received_payout', 'payout_received_date')
        }),
        (_('Financial Summary'), {
            'fields': ('total_contributed', 'get_contribution_summary'),
            'classes': ('collapse',)
        }),
        (_('Additional Info'), {
            'fields': ('joined_date', 'exit_date', 'notes'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member_name(self, obj):
        return obj.user.get_full_name()
    get_member_name.short_description = 'Member'
    get_member_name.admin_order_field = 'user__first_name'
    
    def get_contribution_summary(self, obj):
        completed = obj.contributions.filter(status='COMPLETED').count()
        pending = obj.contributions.filter(status='PENDING').count()
        return format_html(
            'Completed: <b>{}</b> | Pending: <b>{}</b>',
            completed, pending
        )
    get_contribution_summary.short_description = 'Contribution Summary'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'chama')


@admin.register(ContributionCycle)
class ContributionCycleAdmin(admin.ModelAdmin):
    """Contribution Cycle Admin"""
    
    list_display = [
        'cycle_number', 'chama', 'get_beneficiary', 'start_date', 
        'end_date', 'get_collection_progress', 'status'
    ]
    list_filter = ['status', 'chama', 'start_date']
    search_fields = ['chama__name', 'beneficiary__user__username']
    readonly_fields = [
        'id', 'collected_amount', 'get_collection_progress',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_('Cycle Information'), {
            'fields': ('chama', 'cycle_number', 'start_date', 'end_date', 'status')
        }),
        (_('Financial Details'), {
            'fields': ('expected_amount', 'collected_amount', 'get_collection_progress')
        }),
        (_('Beneficiary & Payout'), {
            'fields': ('beneficiary', 'payout_amount', 'payout_date')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_beneficiary(self, obj):
        if obj.beneficiary:
            return obj.beneficiary.user.get_full_name()
        return '-'
    get_beneficiary.short_description = 'Beneficiary'
    
    def get_collection_progress(self, obj):
        if obj.expected_amount > 0:
            percentage = (obj.collected_amount / obj.expected_amount) * 100
            color = 'green' if percentage >= 100 else 'orange' if percentage >= 50 else 'red'
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 5px;">'
                '<div style="width: {}%; background-color: {}; padding: 2px 5px; '
                'border-radius: 5px; text-align: center; color: white; font-weight: bold;">'
                '{:.1f}%</div></div>',
                min(percentage, 100), color, percentage
            )
        return '-'
    get_collection_progress.short_description = 'Collection Progress'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('chama', 'beneficiary__user')


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    """Contribution Admin with payment tracking"""
    
    list_display = [
        'transaction_reference', 'get_member', 'get_chama', 
        'amount', 'payment_method', 'payment_date', 'status',
        'late_payment'
    ]
    list_filter = [
        'status', 'payment_method', 'late_payment', 
        'payment_date', 'cycle__chama'
    ]
    search_fields = [
        'transaction_reference', 'mpesa_receipt_number',
        'membership__user__username', 'membership__user__email'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        (_('Contribution Details'), {
            'fields': ('cycle', 'membership', 'amount', 'status')
        }),
        (_('Payment Information'), {
            'fields': ('payment_method', 'transaction_reference', 
                      'mpesa_receipt_number', 'payment_date')
        }),
        (_('Late Payment'), {
            'fields': ('late_payment', 'penalty_amount')
        }),
        (_('Additional Info'), {
            'fields': ('notes', 'recorded_by'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member(self, obj):
        return obj.membership.user.get_full_name()
    get_member.short_description = 'Member'
    
    def get_chama(self, obj):
        return obj.cycle.chama.name
    get_chama.short_description = 'Chama'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'membership__user', 'cycle__chama', 'recorded_by'
        )


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    """Payout Admin"""
    
    list_display = [
        'transaction_reference', 'get_member', 'get_chama',
        'amount', 'scheduled_date', 'status', 'get_approval_status'
    ]
    list_filter = ['status', 'payment_method', 'scheduled_date']
    search_fields = [
        'transaction_reference', 'mpesa_receipt_number',
        'membership__user__username'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'approval_date',
        'actual_payment_date'
    ]
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        (_('Payout Details'), {
            'fields': ('cycle', 'membership', 'amount', 'scheduled_date', 'status')
        }),
        (_('Payment Information'), {
            'fields': ('payment_method', 'transaction_reference', 
                      'mpesa_receipt_number', 'actual_payment_date')
        }),
        (_('Approval'), {
            'fields': ('approved_by', 'approval_date', 'processed_by')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member(self, obj):
        return obj.membership.user.get_full_name()
    get_member.short_description = 'Member'
    
    def get_chama(self, obj):
        return obj.cycle.chama.name
    get_chama.short_description = 'Chama'
    
    def get_approval_status(self, obj):
        if obj.status == 'APPROVED':
            return format_html(
                '<span style="color: green;">✓ Approved</span>'
            )
        elif obj.status == 'PENDING':
            return format_html(
                '<span style="color: orange;">⏳ Pending</span>'
            )
        return obj.status
    get_approval_status.short_description = 'Approval'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'membership__user', 'cycle__chama', 'approved_by', 'processed_by'
        )


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Loan Admin with repayment tracking"""
    
    list_display = [
        'loan_number', 'get_member', 'get_chama', 'principal_amount',
        'get_repayment_progress', 'status', 'application_date'
    ]
    list_filter = ['status', 'chama', 'application_date']
    search_fields = [
        'loan_number', 'membership__user__username',
        'membership__user__email'
    ]
    readonly_fields = [
        'id', 'interest_amount', 'total_amount', 'balance',
        'created_at', 'updated_at', 'get_repayment_summary'
    ]
    date_hierarchy = 'application_date'
    
    fieldsets = (
        (_('Loan Information'), {
            'fields': ('chama', 'membership', 'loan_number', 'status', 'purpose')
        }),
        (_('Financial Details'), {
            'fields': ('principal_amount', 'interest_rate', 'interest_amount',
                      'total_amount', 'amount_paid', 'balance', 'repayment_period_months')
        }),
        (_('Important Dates'), {
            'fields': ('application_date', 'approval_date', 'disbursement_date',
                      'expected_completion_date', 'actual_completion_date')
        }),
        (_('Guarantors'), {
            'fields': ('guarantor_1', 'guarantor_2'),
            'classes': ('collapse',)
        }),
        (_('Approval'), {
            'fields': ('approved_by', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        (_('Repayment Summary'), {
            'fields': ('get_repayment_summary',),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member(self, obj):
        return obj.membership.user.get_full_name()
    get_member.short_description = 'Member'
    
    def get_chama(self, obj):
        return obj.chama.name
    get_chama.short_description = 'Chama'
    
    def get_repayment_progress(self, obj):
        if obj.total_amount > 0:
            percentage = (obj.amount_paid / obj.total_amount) * 100
            color = 'green' if percentage >= 100 else 'orange' if percentage >= 50 else 'red'
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 5px;">'
                '<div style="width: {}%; background-color: {}; padding: 2px 5px; '
                'border-radius: 5px; text-align: center; color: white; font-weight: bold;">'
                '{:.1f}%</div></div>',
                min(percentage, 100), color, percentage
            )
        return '-'
    get_repayment_progress.short_description = 'Repayment Progress'
    
    def get_repayment_summary(self, obj):
        repayments = obj.repayments.filter(status='COMPLETED')
        count = repayments.count()
        total = repayments.aggregate(total=Sum('amount'))['total'] or 0
        return format_html(
            'Payments Made: <b>{}</b><br>Total Repaid: <b>KES {:,.2f}</b><br>'
            'Balance: <b>KES {:,.2f}</b>',
            count, total, obj.balance
        )
    get_repayment_summary.short_description = 'Repayment Summary'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'membership__user', 'chama', 'approved_by'
        ).prefetch_related('repayments')


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    """Loan Repayment Admin"""
    
    list_display = [
        'transaction_reference', 'get_loan_number', 'get_member',
        'amount', 'payment_method', 'payment_date', 'status'
    ]
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = [
        'transaction_reference', 'loan__loan_number',
        'loan__membership__user__username'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        (_('Repayment Details'), {
            'fields': ('loan', 'amount', 'status')
        }),
        (_('Payment Information'), {
            'fields': ('payment_method', 'transaction_reference', 'payment_date')
        }),
        (_('Additional Info'), {
            'fields': ('notes', 'recorded_by'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_loan_number(self, obj):
        return obj.loan.loan_number
    get_loan_number.short_description = 'Loan Number'
    
    def get_member(self, obj):
        return obj.loan.membership.user.get_full_name()
    get_member.short_description = 'Member'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'loan__membership__user', 'recorded_by'
        )


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Meeting Admin"""
    
    list_display = [
        'meeting_number', 'chama', 'title', 'scheduled_date',
        'get_attendance_rate', 'status'
    ]
    list_filter = ['status', 'chama', 'scheduled_date']
    search_fields = ['title', 'chama__name', 'agenda']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'get_attendance_summary'
    ]
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        (_('Meeting Details'), {
            'fields': ('chama', 'title', 'meeting_number', 'status')
        }),
        (_('Schedule'), {
            'fields': ('scheduled_date', 'actual_start_time', 
                      'actual_end_time', 'location')
        }),
        (_('Agenda & Minutes'), {
            'fields': ('agenda', 'minutes')
        }),
        (_('Attendance'), {
            'fields': ('get_attendance_summary',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'secretary', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_attendance_rate(self, obj):
        total = obj.attendance.count()
        if total > 0:
            present = obj.attendance.filter(status='PRESENT').count()
            percentage = (present / total) * 100
            return format_html('{}/{} ({:.1f}%)', present, total, percentage)
        return '-'
    get_attendance_rate.short_description = 'Attendance'
    
    def get_attendance_summary(self, obj):
        total = obj.attendance.count()
        present = obj.attendance.filter(status='PRESENT').count()
        absent = obj.attendance.filter(status='ABSENT').count()
        late = obj.attendance.filter(status='LATE').count()
        excused = obj.attendance.filter(status='EXCUSED').count()
        
        return format_html(
            'Total: <b>{}</b> | Present: <b style="color: green;">{}</b> | '
            'Absent: <b style="color: red;">{}</b> | Late: <b>{}</b> | '
            'Excused: <b>{}</b>',
            total, present, absent, late, excused
        )
    get_attendance_summary.short_description = 'Attendance Summary'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('chama', 'secretary').prefetch_related('attendance')


@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(admin.ModelAdmin):
    """Meeting Attendance Admin"""
    
    list_display = [
        'get_member', 'get_meeting', 'status', 'arrival_time'
    ]
    list_filter = ['status', 'meeting__chama', 'meeting__scheduled_date']
    search_fields = [
        'membership__user__username', 'meeting__title'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Attendance Details'), {
            'fields': ('meeting', 'membership', 'status', 'arrival_time')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member(self, obj):
        return obj.membership.user.get_full_name()
    get_member.short_description = 'Member'
    
    def get_meeting(self, obj):
        return f"{obj.meeting.chama.name} - {obj.meeting.title}"
    get_meeting.short_description = 'Meeting'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'membership__user', 'meeting__chama'
        )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification Admin"""
    
    list_display = [
        'title', 'user', 'notification_type', 'channel',
        'status', 'created_at'
    ]
    list_filter = [
        'notification_type', 'channel', 'status', 'created_at'
    ]
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['id', 'sent_at', 'read_at', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Notification Details'), {
            'fields': ('user', 'chama', 'notification_type', 'channel', 'status')
        }),
        (_('Content'), {
            'fields': ('title', 'message')
        }),
        (_('Timing'), {
            'fields': ('sent_at', 'read_at'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'chama')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit Log Admin - Read Only"""
    
    list_display = [
        'timestamp', 'user', 'action', 'model_name',
        'object_id', 'ip_address'
    ]
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = [
        'user__username', 'model_name', 'object_id', 'ip_address'
    ]
    readonly_fields = [
        'id', 'user', 'action', 'model_name', 'object_id',
        'changes', 'ip_address', 'user_agent', 'timestamp'
    ]
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('Audit Details'), {
            'fields': ('user', 'action', 'model_name', 'object_id', 'timestamp')
        }),
        (_('Changes'), {
            'fields': ('changes',)
        }),
        (_('Request Info'), {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')