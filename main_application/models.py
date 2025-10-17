from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class User(AbstractUser):
    """Extended User model for Chama members"""
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('TREASURER', 'Treasurer'),
        ('SECRETARY', 'Secretary'),
        ('MEMBER', 'Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15, unique=True)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"


class Chama(models.Model):
    """Main Chama/Group model"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Bi-Weekly'),
        ('MONTHLY', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    registration_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    contribution_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('100.00'))]
    )
    contribution_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    late_payment_penalty = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    loan_interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Annual interest rate in percentage"
    )
    max_members = models.PositiveIntegerField(default=50)
    meeting_day = models.CharField(max_length=20, blank=True)
    meeting_time = models.TimeField(null=True, blank=True)
    meeting_location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    constitution_document = models.FileField(upload_to='constitutions/', null=True, blank=True)
    bank_account_name = models.CharField(max_length=200, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    mpesa_paybill = models.CharField(max_length=20, blank=True)
    mpesa_account_number = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='chamas_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chamas'
        verbose_name = _('Chama')
        verbose_name_plural = _('Chamas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def total_members(self):
        return self.memberships.filter(status='ACTIVE').count()
    
    @property
    def total_contributions(self):
        return self.contributions.filter(status='COMPLETED').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')


class ChamaMembership(models.Model):
    """Membership relationship between Users and Chamas"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('WITHDRAWN', 'Withdrawn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    position_in_rotation = models.PositiveIntegerField()
    membership_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    joined_date = models.DateField(auto_now_add=True)
    exit_date = models.DateField(null=True, blank=True)
    has_received_payout = models.BooleanField(default=False)
    payout_received_date = models.DateField(null=True, blank=True)
    total_contributed = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chama_memberships'
        verbose_name = _('Chama Membership')
        verbose_name_plural = _('Chama Memberships')
        unique_together = [['chama', 'user'], ['chama', 'position_in_rotation']]
        ordering = ['chama', 'position_in_rotation']
        indexes = [
            models.Index(fields=['chama', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.chama.name} (Position: {self.position_in_rotation})"


class ContributionCycle(models.Model):
    """Represents a contribution cycle/round"""
    
    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='cycles')
    cycle_number = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2)
    collected_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    beneficiary = models.ForeignKey(
        ChamaMembership, 
        on_delete=models.PROTECT, 
        related_name='beneficiary_cycles',
        null=True,
        blank=True
    )
    payout_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payout_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contribution_cycles'
        verbose_name = _('Contribution Cycle')
        verbose_name_plural = _('Contribution Cycles')
        unique_together = [['chama', 'cycle_number']]
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['chama', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.chama.name} - Cycle {self.cycle_number}"


class Contribution(models.Model):
    """Individual member contributions"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('MPESA', 'M-Pesa'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('CARD', 'Card Payment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle = models.ForeignKey(ContributionCycle, on_delete=models.CASCADE, related_name='contributions')
    membership = models.ForeignKey(ChamaMembership, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_reference = models.CharField(max_length=100, unique=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    payment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    late_payment = models.BooleanField(default=False)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='recorded_contributions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contributions'
        verbose_name = _('Contribution')
        verbose_name_plural = _('Contributions')
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['cycle', 'membership', 'status']),
            models.Index(fields=['transaction_reference']),
            models.Index(fields=['payment_date']),
        ]
    
    def __str__(self):
        return f"{self.membership.user.get_full_name()} - {self.amount} ({self.payment_date.date()})"


class Payout(models.Model):
    """Tracks payouts to members"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('MPESA', 'M-Pesa'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle = models.OneToOneField(ContributionCycle, on_delete=models.PROTECT, related_name='payout')
    membership = models.ForeignKey(ChamaMembership, on_delete=models.PROTECT, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_reference = models.CharField(max_length=100, unique=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    scheduled_date = models.DateField()
    actual_payment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='approved_payouts',
        null=True,
        blank=True
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='processed_payouts',
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payouts'
        verbose_name = _('Payout')
        verbose_name_plural = _('Payouts')
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['membership', 'status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['transaction_reference']),
        ]
    
    def __str__(self):
        return f"Payout to {self.membership.user.get_full_name()} - {self.amount}"


class Loan(models.Model):
    """Member loan management"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DISBURSED', 'Disbursed'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('DEFAULTED', 'Defaulted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='loans')
    membership = models.ForeignKey(ChamaMembership, on_delete=models.CASCADE, related_name='loans')
    loan_number = models.CharField(max_length=50, unique=True)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    repayment_period_months = models.PositiveIntegerField()
    application_date = models.DateField(auto_now_add=True)
    approval_date = models.DateField(null=True, blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    expected_completion_date = models.DateField()
    actual_completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    purpose = models.TextField()
    guarantor_1 = models.ForeignKey(
        ChamaMembership, 
        on_delete=models.PROTECT, 
        related_name='guaranteed_loans_1',
        null=True,
        blank=True
    )
    guarantor_2 = models.ForeignKey(
        ChamaMembership, 
        on_delete=models.PROTECT, 
        related_name='guaranteed_loans_2',
        null=True,
        blank=True
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='approved_loans',
        null=True,
        blank=True
    )
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'loans'
        verbose_name = _('Loan')
        verbose_name_plural = _('Loans')
        ordering = ['-application_date']
        indexes = [
            models.Index(fields=['membership', 'status']),
            models.Index(fields=['chama', 'status']),
            models.Index(fields=['loan_number']),
        ]
    
    def __str__(self):
        return f"Loan {self.loan_number} - {self.membership.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.interest_amount:
            self.interest_amount = (self.principal_amount * self.interest_rate / 100)
        if not self.total_amount:
            self.total_amount = self.principal_amount + self.interest_amount
        if not self.balance:
            self.balance = self.total_amount - self.amount_paid
        super().save(*args, **kwargs)


class LoanRepayment(models.Model):
    """Tracks loan repayments"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('MPESA', 'M-Pesa'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('DEDUCTION', 'Payout Deduction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_reference = models.CharField(max_length=100)
    payment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='recorded_repayments')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'loan_repayments'
        verbose_name = _('Loan Repayment')
        verbose_name_plural = _('Loan Repayments')
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['loan', 'payment_date']),
            models.Index(fields=['transaction_reference']),
        ]
    
    def __str__(self):
        return f"Repayment {self.amount} for {self.loan.loan_number}"


class Meeting(models.Model):
    """Chama meetings tracking"""
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='meetings')
    title = models.CharField(max_length=200)
    meeting_number = models.PositiveIntegerField()
    scheduled_date = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255)
    agenda = models.TextField()
    minutes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    secretary = models.ForeignKey(User, on_delete=models.PROTECT, related_name='meetings_recorded')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'meetings'
        verbose_name = _('Meeting')
        verbose_name_plural = _('Meetings')
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['chama', 'status']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.chama.name} - Meeting {self.meeting_number}"


class MeetingAttendance(models.Model):
    """Tracks meeting attendance"""
    
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('EXCUSED', 'Excused'),
        ('LATE', 'Late'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendance')
    membership = models.ForeignKey(ChamaMembership, on_delete=models.CASCADE, related_name='attendance')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABSENT')
    arrival_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'meeting_attendance'
        verbose_name = _('Meeting Attendance')
        verbose_name_plural = _('Meeting Attendance')
        unique_together = [['meeting', 'membership']]
        indexes = [
            models.Index(fields=['meeting', 'status']),
        ]
    
    def __str__(self):
        return f"{self.membership.user.get_full_name()} - {self.meeting.title}"


class Notification(models.Model):
    """System notifications"""
    
    TYPE_CHOICES = [
        ('CONTRIBUTION_REMINDER', 'Contribution Reminder'),
        ('PAYOUT_NOTIFICATION', 'Payout Notification'),
        ('LOAN_APPROVAL', 'Loan Approval'),
        ('LOAN_REJECTION', 'Loan Rejection'),
        ('MEETING_REMINDER', 'Meeting Reminder'),
        ('PAYMENT_RECEIVED', 'Payment Received'),
        ('LATE_PAYMENT', 'Late Payment'),
        ('GENERAL', 'General'),
    ]
    
    CHANNEL_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('IN_APP', 'In-App'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('READ', 'Read'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='notifications', null=True)
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"


class AuditLog(models.Model):
    """Audit trail for security and compliance"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('PAYMENT', 'Payment'),
        ('EXPORT', 'Export'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.model_name} by {self.user}"