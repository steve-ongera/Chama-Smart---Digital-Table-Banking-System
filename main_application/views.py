

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.db.models import Sum, Count, Q
from main_application.models import (
    User, Chama, ChamaMembership, Contribution, 
    Loan, Payout, Meeting, Notification, AuditLog
)
from decimal import Decimal


@csrf_protect
@never_cache
def login_view(request):
    """
    Handle user login with role-based redirection
    """
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me', False)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Log the user in
                login(request, user)
                
                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires on browser close
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                
                # Create audit log
                AuditLog.objects.create(
                    user=user,
                    action='LOGIN',
                    model_name='User',
                    object_id=str(user.id),
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
                
                # Success message
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Role-based redirection
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                return redirect('dashboard')
            else:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            
            # Log failed login attempt
            AuditLog.objects.create(
                user=None,
                action='LOGIN',
                model_name='User',
                object_id='FAILED',
                changes={'username': username, 'status': 'failed'},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
    
    return render(request, 'auth/login.html', {
        'page_title': 'Login - Chama Smart'
    })


@csrf_protect
@login_required
def logout_view(request):
    """
    Handle user logout
    """
    # Create audit log before logout
    AuditLog.objects.create(
        user=request.user,
        action='LOGOUT',
        model_name='User',
        object_id=str(request.user.id),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    username = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'Goodbye, {username}! You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Main dashboard - redirects to role-specific dashboard
    """
    user = request.user
    
    # Redirect based on user role
    if user.role == 'ADMIN':
        return admin_dashboard(request)
    elif user.role == 'TREASURER':
        return treasurer_dashboard(request)
    elif user.role == 'SECRETARY':
        return secretary_dashboard(request)
    else:  # MEMBER
        return member_dashboard(request)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncWeek, TruncDate
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json

from .models import (
    Chama, User, ChamaMembership, Contribution, 
    ContributionCycle, Payout, Loan, LoanRepayment,
    Meeting, Notification
)


@login_required
def admin_dashboard(request):
    """
    Enhanced Administrator dashboard with comprehensive analytics
    """
    # Date ranges for filtering
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_90_days = today - timedelta(days=90)
    current_year = today.year
    
    # ============= SYSTEM-WIDE STATISTICS =============
    total_chamas = Chama.objects.count()
    active_chamas = Chama.objects.filter(status='ACTIVE').count()
    suspended_chamas = Chama.objects.filter(status='SUSPENDED').count()
    inactive_chamas = Chama.objects.filter(status='INACTIVE').count()
    
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True).count()
    total_members = ChamaMembership.objects.filter(status='ACTIVE').count()
    pending_memberships = ChamaMembership.objects.filter(status='PENDING').count()
    
    # ============= FINANCIAL STATISTICS =============
    total_contributions = Contribution.objects.filter(
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    contributions_this_month = Contribution.objects.filter(
        status='COMPLETED',
        payment_date__month=today.month,
        payment_date__year=today.year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_payouts = Payout.objects.filter(
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    pending_payouts = Payout.objects.filter(
        status='PENDING'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    active_loans = Loan.objects.filter(status__in=['ACTIVE', 'DISBURSED']).count()
    total_loans_amount = Loan.objects.filter(
        status__in=['ACTIVE', 'DISBURSED']
    ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
    
    pending_loans = Loan.objects.filter(status='PENDING').count()
    defaulted_loans = Loan.objects.filter(status='DEFAULTED').count()
    
    # ============= MONTHLY CONTRIBUTIONS TREND (Bar Chart) =============
    monthly_contributions = Contribution.objects.filter(
        status='COMPLETED',
        payment_date__year=current_year
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    ).order_by('month')
    
    months_labels = []
    monthly_amounts = []
    for item in monthly_contributions:
        months_labels.append(item['month'].strftime('%b %Y'))
        monthly_amounts.append(float(item['total_amount']))
    
    # ============= PAYMENT METHOD DISTRIBUTION (Pie Chart) =============
    payment_methods = Contribution.objects.filter(
        status='COMPLETED'
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    payment_method_labels = [item['payment_method'] for item in payment_methods]
    payment_method_values = [float(item['total']) for item in payment_methods]
    
    # ============= CHAMA STATUS DISTRIBUTION (Donut Chart) =============
    chama_status = Chama.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    chama_status_labels = [item['status'] for item in chama_status]
    chama_status_values = [item['count'] for item in chama_status]
    
    # ============= LOAN STATUS DISTRIBUTION (Donut Chart) =============
    loan_status = Loan.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('principal_amount')
    ).order_by('-count')
    
    loan_status_labels = [item['status'] for item in loan_status]
    loan_status_values = [item['count'] for item in loan_status]
    
    # ============= CONTRIBUTIONS VS PAYOUTS TREND (Line Chart) =============
    last_6_months_contributions = Contribution.objects.filter(
        status='COMPLETED',
        payment_date__gte=last_90_days
    ).annotate(
        week=TruncWeek('payment_date')
    ).values('week').annotate(
        total=Sum('amount')
    ).order_by('week')
    
    last_6_months_payouts = Payout.objects.filter(
        status='COMPLETED',
        actual_payment_date__gte=last_90_days
    ).annotate(
        week=TruncWeek('actual_payment_date')
    ).values('week').annotate(
        total=Sum('amount')
    ).order_by('week')
    
    trend_labels = []
    contributions_trend = []
    payouts_trend = []
    
    for item in last_6_months_contributions:
        trend_labels.append(item['week'].strftime('%b %d'))
        contributions_trend.append(float(item['total']))
    
    payout_dict = {p['week'].strftime('%b %d'): float(p['total']) for p in last_6_months_payouts}
    payouts_trend = [payout_dict.get(label, 0) for label in trend_labels]
    
    # ============= TOP PERFORMING CHAMAS (Bar Chart) =============
    top_chamas = Chama.objects.annotate(
        total_contributions=Sum(
            'cycles__contributions__amount',
            filter=Q(cycles__contributions__status='COMPLETED')
        ),
        member_count=Count('memberships', filter=Q(memberships__status='ACTIVE'))
    ).order_by('-total_contributions')[:10]
    
    top_chamas_labels = [chama.name[:20] for chama in top_chamas]
    top_chamas_values = [float(chama.total_contributions or 0) for chama in top_chamas]
    
    # ============= MEMBER GROWTH TREND (Line Chart) =============
    member_growth = ChamaMembership.objects.filter(
        status='ACTIVE'
    ).annotate(
        month=TruncMonth('joined_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')[:12]
    
    member_growth_labels = [item['month'].strftime('%b %Y') for item in member_growth]
    member_growth_values = [item['count'] for item in member_growth]
    
    # ============= LOAN REPAYMENT RATE =============
    total_loans_value = Loan.objects.filter(
        status__in=['ACTIVE', 'DISBURSED', 'COMPLETED']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    total_repaid = Loan.objects.filter(
        status__in=['ACTIVE', 'DISBURSED', 'COMPLETED']
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    
    repayment_rate = (float(total_repaid) / float(total_loans_value) * 100) if total_loans_value > 0 else 0
    
    # ============= RECENT ACTIVITIES =============
    recent_chamas = Chama.objects.select_related('created_by').order_by('-created_at')[:5]
    pending_loan_requests = Loan.objects.filter(status='PENDING').select_related(
        'membership__user', 'chama'
    ).order_by('-application_date')[:10]
    
    recent_contributions = Contribution.objects.filter(
        status='COMPLETED'
    ).select_related(
        'membership__user', 'cycle__chama'
    ).order_by('-payment_date')[:10]
    
    upcoming_meetings = Meeting.objects.filter(
        status='SCHEDULED',
        scheduled_date__gte=timezone.now()
    ).select_related('chama', 'secretary').order_by('scheduled_date')[:5]
    
    # ============= NOTIFICATIONS =============
    unread_notifications = Notification.objects.filter(
        user=request.user,
        status__in=['PENDING', 'SENT']
    ).count()
    
    # ============= CONTRIBUTION CYCLES STATUS =============
    active_cycles = ContributionCycle.objects.filter(status='ACTIVE').count()
    completed_cycles = ContributionCycle.objects.filter(status='COMPLETED').count()
    
    # ============= PREPARE CONTEXT =============
    context = {
        'page_title': 'Admin Dashboard',
        'user_role': 'Administrator',
        
        # System Stats
        'total_chamas': total_chamas,
        'active_chamas': active_chamas,
        'suspended_chamas': suspended_chamas,
        'inactive_chamas': inactive_chamas,
        'total_users': total_users,
        'verified_users': verified_users,
        'total_members': total_members,
        'pending_memberships': pending_memberships,
        
        # Financial Stats
        'total_contributions': total_contributions,
        'contributions_this_month': contributions_this_month,
        'total_payouts': total_payouts,
        'pending_payouts': pending_payouts,
        'active_loans': active_loans,
        'total_loans_amount': total_loans_amount,
        'pending_loans': pending_loans,
        'defaulted_loans': defaulted_loans,
        'repayment_rate': round(repayment_rate, 2),
        
        # Cycle Stats
        'active_cycles': active_cycles,
        'completed_cycles': completed_cycles,
        
        # Chart Data (JSON serialized for JavaScript)
        'monthly_contributions_labels': json.dumps(months_labels),
        'monthly_contributions_data': json.dumps(monthly_amounts),
        
        'payment_method_labels': json.dumps(payment_method_labels),
        'payment_method_data': json.dumps(payment_method_values),
        
        'chama_status_labels': json.dumps(chama_status_labels),
        'chama_status_data': json.dumps(chama_status_values),
        
        'loan_status_labels': json.dumps(loan_status_labels),
        'loan_status_data': json.dumps(loan_status_values),
        
        'trend_labels': json.dumps(trend_labels),
        'contributions_trend': json.dumps(contributions_trend),
        'payouts_trend': json.dumps(payouts_trend),
        
        'top_chamas_labels': json.dumps(top_chamas_labels),
        'top_chamas_data': json.dumps(top_chamas_values),
        
        'member_growth_labels': json.dumps(member_growth_labels),
        'member_growth_data': json.dumps(member_growth_values),
        
        # Recent Activities
        'recent_chamas': recent_chamas,
        'pending_loan_requests': pending_loan_requests,
        'recent_contributions': recent_contributions,
        'upcoming_meetings': upcoming_meetings,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
def treasurer_dashboard(request):
    """
    Treasurer dashboard with financial management focus
    """
    # Get chamas where user is treasurer or member
    user_chamas = Chama.objects.filter(
        Q(created_by=request.user) | 
        Q(memberships__user=request.user, memberships__status='ACTIVE')
    ).distinct()
    
    # Financial statistics for user's chamas
    total_contributions = Contribution.objects.filter(
        cycle__chama__in=user_chamas,
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    pending_contributions = Contribution.objects.filter(
        cycle__chama__in=user_chamas,
        status='PENDING'
    ).count()
    
    total_payouts = Payout.objects.filter(
        cycle__chama__in=user_chamas,
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    pending_payouts = Payout.objects.filter(
        cycle__chama__in=user_chamas,
        status='PENDING'
    ).count()
    
    # Loan statistics
    pending_loans = Loan.objects.filter(
        chama__in=user_chamas,
        status='PENDING'
    ).select_related('membership__user', 'chama').order_by('-application_date')
    
    active_loans = Loan.objects.filter(
        chama__in=user_chamas,
        status='ACTIVE'
    ).count()
    
    # Recent transactions
    recent_contributions = Contribution.objects.filter(
        cycle__chama__in=user_chamas
    ).select_related(
        'membership__user', 'cycle__chama'
    ).order_by('-payment_date')[:15]
    
    # Upcoming payouts
    upcoming_payouts = Payout.objects.filter(
        cycle__chama__in=user_chamas,
        status__in=['PENDING', 'APPROVED']
    ).select_related(
        'membership__user', 'cycle__chama'
    ).order_by('scheduled_date')[:10]
    
    # Notifications
    unread_notifications = Notification.objects.filter(
        user=request.user,
        status__in=['PENDING', 'SENT']
    ).count()
    
    context = {
        'page_title': 'Treasurer Dashboard',
        'user_role': 'Treasurer',
        'user_chamas': user_chamas,
        'total_contributions': total_contributions,
        'pending_contributions': pending_contributions,
        'total_payouts': total_payouts,
        'pending_payouts': pending_payouts,
        'pending_loans': pending_loans,
        'active_loans': active_loans,
        'recent_contributions': recent_contributions,
        'upcoming_payouts': upcoming_payouts,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'dashboards/treasurer_dashboard.html', context)


@login_required
def secretary_dashboard(request):
    """
    Secretary dashboard with meetings and communication focus
    """
    # Get chamas where user is secretary or member
    user_chamas = Chama.objects.filter(
        Q(created_by=request.user) | 
        Q(memberships__user=request.user, memberships__status='ACTIVE')
    ).distinct()
    
    # Meeting statistics
    upcoming_meetings = Meeting.objects.filter(
        chama__in=user_chamas,
        status='SCHEDULED',
        scheduled_date__gte=timezone.now()
    ).select_related('chama').order_by('scheduled_date')[:10]
    
    completed_meetings = Meeting.objects.filter(
        chama__in=user_chamas,
        status='COMPLETED'
    ).count()
    
    pending_minutes = Meeting.objects.filter(
        chama__in=user_chamas,
        status='COMPLETED',
        minutes=''
    ).count()
    
    # Communication statistics
    total_notifications = Notification.objects.filter(
        chama__in=user_chamas
    ).count()
    
    pending_notifications = Notification.objects.filter(
        chama__in=user_chamas,
        status='PENDING'
    ).count()
    
    # Member statistics
    total_members = ChamaMembership.objects.filter(
        chama__in=user_chamas,
        status='ACTIVE'
    ).count()
    
    pending_members = ChamaMembership.objects.filter(
        chama__in=user_chamas,
        status='PENDING'
    ).select_related('user', 'chama')
    
    # Recent activities
    recent_meetings = Meeting.objects.filter(
        chama__in=user_chamas
    ).select_related('chama').order_by('-scheduled_date')[:10]
    
    # User notifications
    unread_notifications = Notification.objects.filter(
        user=request.user,
        status__in=['PENDING', 'SENT']
    ).count()
    
    context = {
        'page_title': 'Secretary Dashboard',
        'user_role': 'Secretary',
        'user_chamas': user_chamas,
        'upcoming_meetings': upcoming_meetings,
        'completed_meetings': completed_meetings,
        'pending_minutes': pending_minutes,
        'total_notifications': total_notifications,
        'pending_notifications': pending_notifications,
        'total_members': total_members,
        'pending_members': pending_members,
        'recent_meetings': recent_meetings,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'dashboards/secretary_dashboard.html', context)


@login_required
def member_dashboard(request):
    """
    Member dashboard with personal chama information
    """
    # Get user's memberships
    user_memberships = ChamaMembership.objects.filter(
        user=request.user,
        status='ACTIVE'
    ).select_related('chama')
    
    user_chamas = Chama.objects.filter(
        memberships__user=request.user,
        memberships__status='ACTIVE'
    ).distinct()
    
    # Personal financial statistics
    total_contributed = Contribution.objects.filter(
        membership__user=request.user,
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_received = Payout.objects.filter(
        membership__user=request.user,
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Loan information
    my_loans = Loan.objects.filter(
        membership__user=request.user
    ).select_related('chama')
    
    active_loans = my_loans.filter(status='ACTIVE')
    total_loan_balance = active_loans.aggregate(
        total=Sum('balance')
    )['total'] or Decimal('0.00')
    
    # Contribution status
    pending_contributions = Contribution.objects.filter(
        membership__user=request.user,
        status='PENDING'
    ).select_related('cycle__chama')
    
    # Payout information
    upcoming_payouts = Payout.objects.filter(
        membership__user=request.user,
        status__in=['PENDING', 'APPROVED']
    ).select_related('cycle__chama').order_by('scheduled_date')
    
    # Rotation position for each chama
    chama_positions = []
    for membership in user_memberships:
        chama_positions.append({
            'chama': membership.chama,
            'position': membership.position_in_rotation,
            'has_received': membership.has_received_payout,
            'total_members': membership.chama.memberships.filter(status='ACTIVE').count(),
        })
    
    # Upcoming meetings
    upcoming_meetings = Meeting.objects.filter(
        chama__in=user_chamas,
        status='SCHEDULED',
        scheduled_date__gte=timezone.now()
    ).select_related('chama').order_by('scheduled_date')[:5]
    
    # Recent contributions
    recent_contributions = Contribution.objects.filter(
        membership__user=request.user
    ).select_related('cycle__chama').order_by('-payment_date')[:10]
    
    # Notifications
    unread_notifications = Notification.objects.filter(
        user=request.user,
        status__in=['PENDING', 'SENT']
    ).count()
    
    recent_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'page_title': 'My Dashboard',
        'user_role': 'Member',
        'user_memberships': user_memberships,
        'user_chamas': user_chamas,
        'total_contributed': total_contributed,
        'total_received': total_received,
        'my_loans': my_loans,
        'active_loans': active_loans,
        'total_loan_balance': total_loan_balance,
        'pending_contributions': pending_contributions,
        'upcoming_payouts': upcoming_payouts,
        'chama_positions': chama_positions,
        'upcoming_meetings': upcoming_meetings,
        'recent_contributions': recent_contributions,
        'unread_notifications': unread_notifications,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'dashboards/member_dashboard.html', context)


# Utility functions
def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def profile_view(request):
    """
    User profile view
    """
    user = request.user
    
    # Get user's memberships
    memberships = ChamaMembership.objects.filter(
        user=user
    ).select_related('chama').order_by('-created_at')
    
    # Get user's audit logs
    recent_activities = AuditLog.objects.filter(
        user=user
    ).order_by('-timestamp')[:20]
    
    context = {
        'page_title': 'My Profile',
        'memberships': memberships,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'auth/profile.html', context)