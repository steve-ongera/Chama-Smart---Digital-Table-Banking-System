"""
Django management command to seed database with realistic Kenyan Chama data
File: main_application/management/commands/seed_data.py

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear  # Clear existing data first
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta
from main_application.models import (
    User, Chama, ChamaMembership, ContributionCycle, Contribution,
    Payout, Loan, LoanRepayment, Meeting, MeetingAttendance,
    Notification, AuditLog
)


class Command(BaseCommand):
    help = 'Seeds the database with realistic Kenyan Chama data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        try:
            with transaction.atomic():
                # Seed data in order of dependencies
                users = self.create_users()
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))
                
                chamas = self.create_chamas(users)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(chamas)} chamas'))
                
                memberships = self.create_memberships(chamas, users)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(memberships)} memberships'))
                
                cycles = self.create_contribution_cycles(chamas, memberships)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(cycles)} contribution cycles'))
                
                contributions = self.create_contributions(cycles, memberships)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(contributions)} contributions'))
                
                payouts = self.create_payouts(cycles, memberships)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(payouts)} payouts'))
                
                loans = self.create_loans(chamas, memberships, users)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(loans)} loans'))
                
                repayments = self.create_loan_repayments(loans, users)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(repayments)} loan repayments'))
                
                meetings = self.create_meetings(chamas, users)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(meetings)} meetings'))
                
                attendance = self.create_attendance(meetings, memberships)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(attendance)} attendance records'))
                
                notifications = self.create_notifications(users, chamas)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(notifications)} notifications'))
                
                audit_logs = self.create_audit_logs(users)
                self.stdout.write(self.style.SUCCESS(f'✓ Created {len(audit_logs)} audit logs'))

            self.stdout.write(self.style.SUCCESS('\n🎉 Database seeding completed successfully!'))
            self.print_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during seeding: {str(e)}'))
            raise

    def clear_data(self):
        """Clear all data from tables"""
        models_to_clear = [
            AuditLog, Notification, MeetingAttendance, Meeting,
            LoanRepayment, Loan, Payout, Contribution,
            ContributionCycle, ChamaMembership, Chama, User
        ]
        for model in models_to_clear:
            count = model.objects.all().delete()[0]
            self.stdout.write(f'  Deleted {count} {model.__name__} records')

    def create_users(self):
        """Create realistic Kenyan users"""
        kenyan_first_names = [
            'Kamau', 'Wanjiru', 'Ochieng', 'Akinyi', 'Kipchoge', 'Chebet',
            'Mwangi', 'Njeri', 'Otieno', 'Awino', 'Kibet', 'Jepchirchir',
            'Karanja', 'Wambui', 'Omondi', 'Adhiambo', 'Kiplagat', 'Jemutai',
            'Njoroge', 'Wangari', 'Onyango', 'Atieno', 'Koech', 'Chepkoech',
            'Githinji', 'Nyambura', 'Okoth', 'Akoth', 'Rotich', 'Chepkemoi',
            'Kariuki', 'Wanjiku', 'Owino', 'Auma', 'Kiprono', 'Chelangat',
            'Mutua', 'Mumbua', 'Odhiambo', 'Akeyo', 'Kimutai', 'Chemutai',
            'Ndungu', 'Wairimu', 'Ouma', 'Anyango', 'Kiptoo', 'Jepkorir'
        ]
        
        kenyan_last_names = [
            'Kimani', 'Omondi', 'Korir', 'Muthoni', 'Otieno', 'Chepkwony',
            'Ndegwa', 'Wanjala', 'Kipkoech', 'Waithaka', 'Owuor', 'Jeptoo',
            'Kamau', 'Otieno', 'Kiptum', 'Mwangi', 'Odhiambo', 'Cherono',
            'Karanja', 'Nyambura', 'Kipruto', 'Ngugi', 'Ouma', 'Jepkemei'
        ]
        
        kenyan_regions = ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Nyeri']
        
        users = []
        roles = ['ADMIN', 'TREASURER', 'SECRETARY', 'MEMBER']
        
        # Create admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@chamasmart.co.ke',
            password='admin123',
            first_name='System',
            last_name='Administrator',
            phone_number='+254712000000',
            national_id='12345678',
            role='ADMIN',
            is_staff=True,
            is_superuser=True,
            is_verified=True,
            two_factor_enabled=True
        )
        users.append(admin)
        
        # Create regular users
        for i in range(50):
            first_name = random.choice(kenyan_first_names)
            last_name = random.choice(kenyan_last_names)
            region = random.choice(kenyan_regions)
            
            username = f"{first_name.lower()}.{last_name.lower()}{i}"
            email = f"{username}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}"
            phone = f"+2547{random.randint(10000000, 99999999)}"
            national_id = f"{random.randint(10000000, 39999999)}"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='Chama@2025',
                first_name=first_name,
                last_name=last_name,
                phone_number=phone,
                national_id=national_id,
                role=random.choice(roles) if i < 15 else 'MEMBER',
                is_verified=random.choice([True, True, True, False]),
                two_factor_enabled=random.choice([True, False]),
                date_of_birth=datetime(
                    random.randint(1970, 2000),
                    random.randint(1, 12),
                    random.randint(1, 28)
                ).date()
            )
            users.append(user)
        
        return users

    def create_chamas(self, users):
        """Create Kenyan-themed chamas"""
        chama_names = [
            'Tuungane Savings Group', 'Pamoja Investment Circle', 'Umoja Women Chama',
            'Harambee Savings Society', 'Bidii Investment Group', 'Tujenge Chama',
            'Uwezo Financial Circle', 'Maendeleo Group', 'Wanawake Wenye Nguvu',
            'Kazi ni Kazi Chama', 'Jitihada Investment Club', 'Unity Welfare Group',
            'Imani Savings Chama', 'Tumaini Financial Group', 'Furaha Investment Circle',
            'Baraka Table Banking', 'Neema Women Group', 'Upendo Savings Society',
            'Amani Investment Chama', 'Jamii Yetu Group', 'Taifa Savings Circle'
        ]
        
        kenyan_locations = [
            'Westlands Community Center', 'Eastleigh Business Hub', 'Karen Shopping Center',
            'Kilimani Social Hall', 'Ngong Road Office', 'South B Community Hall',
            'Roysambu Meeting Room', 'Kasarani Sports Complex', 'Embakasi Business Center',
            'CBD Conference Room', 'Kibera Resource Center', 'Kawangware Social Hall',
            'Langata Community Center', 'Ruaraka Meeting Point', 'Githurai Business Hub'
        ]
        
        kenyan_banks = [
            'Kenya Commercial Bank', 'Equity Bank', 'Cooperative Bank',
            'Barclays Bank Kenya', 'Standard Chartered Kenya', 'Family Bank',
            'KCB Bank', 'DTB Kenya', 'I&M Bank', 'Stanbic Bank Kenya'
        ]
        
        chamas = []
        admins = [u for u in users if u.role in ['ADMIN', 'TREASURER']]
        
        for i, name in enumerate(chama_names[:15]):
            contribution_amounts = [500, 1000, 2000, 3000, 5000, 10000]
            frequency = random.choice(['WEEKLY', 'WEEKLY', 'MONTHLY', 'MONTHLY', 'BIWEEKLY'])
            
            chama = Chama.objects.create(
                name=name,
                description=f"A self-help group focused on financial empowerment and mutual support. "
                           f"We meet regularly to pool resources and support each other's financial goals.",
                registration_number=f"CHM/{2024 + i//5}/{random.randint(1000, 9999)}",
                contribution_amount=Decimal(random.choice(contribution_amounts)),
                contribution_frequency=frequency,
                late_payment_penalty=Decimal('100.00'),
                loan_interest_rate=Decimal(random.choice([5, 8, 10, 12, 15])),
                max_members=random.choice([20, 30, 40, 50]),
                meeting_day=random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']),
                meeting_time=datetime.strptime(random.choice(['10:00', '14:00', '16:00', '18:00']), '%H:%M').time(),
                meeting_location=random.choice(kenyan_locations),
                status='ACTIVE',
                bank_account_name=name,
                bank_account_number=f"{random.randint(1000000000, 9999999999)}",
                bank_name=random.choice(kenyan_banks),
                mpesa_paybill=f"{random.randint(100000, 999999)}",
                mpesa_account_number=f"CHAMA{i+1:03d}",
                created_by=random.choice(admins)
            )
            chamas.append(chama)
        
        return chamas

    def create_memberships(self, chamas, users):
        """Create chama memberships with rotation positions"""
        memberships = []
        available_users = [u for u in users if u.role != 'ADMIN']
        
        for chama in chamas:
            # Each chama gets 10-25 members
            num_members = random.randint(10, min(25, len(available_users)))
            selected_users = random.sample(available_users, num_members)
            
            for position, user in enumerate(selected_users, start=1):
                membership = ChamaMembership.objects.create(
                    chama=chama,
                    user=user,
                    position_in_rotation=position,
                    membership_number=f"{chama.name[:3].upper()}/{position:03d}",
                    status=random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'PENDING']),
                    has_received_payout=position <= (num_members // 3),  # First third have received
                    payout_received_date=(
                        timezone.now().date() - timedelta(days=random.randint(30, 180))
                        if position <= (num_members // 3) else None
                    ),
                    total_contributed=Decimal(random.randint(5000, 50000)),
                    joined_date=timezone.now().date() - timedelta(days=random.randint(30, 365))
                )
                memberships.append(membership)
        
        return memberships

    def create_contribution_cycles(self, chamas, memberships):
        """Create contribution cycles"""
        cycles = []
        
        for chama in chamas:
            chama_members = [m for m in memberships if m.chama == chama and m.status == 'ACTIVE']
            num_cycles = random.randint(3, 8)
            
            for cycle_num in range(1, num_cycles + 1):
                # Calculate dates based on frequency
                if chama.contribution_frequency == 'WEEKLY':
                    days_delta = cycle_num * 7
                elif chama.contribution_frequency == 'BIWEEKLY':
                    days_delta = cycle_num * 14
                else:  # MONTHLY
                    days_delta = cycle_num * 30
                
                start_date = timezone.now().date() - timedelta(days=365 - days_delta)
                end_date = start_date + timedelta(days=7 if chama.contribution_frequency == 'WEEKLY' else 14 if chama.contribution_frequency == 'BIWEEKLY' else 30)
                
                # Determine beneficiary in rotation
                beneficiary_index = (cycle_num - 1) % len(chama_members)
                beneficiary = chama_members[beneficiary_index] if chama_members else None
                
                expected_amount = chama.contribution_amount * len(chama_members)
                collected_amount = expected_amount * Decimal(random.uniform(0.8, 1.0))
                
                status = 'COMPLETED' if cycle_num < num_cycles - 1 else random.choice(['ACTIVE', 'COMPLETED'])
                
                cycle = ContributionCycle.objects.create(
                    chama=chama,
                    cycle_number=cycle_num,
                    start_date=start_date,
                    end_date=end_date,
                    expected_amount=expected_amount,
                    collected_amount=collected_amount if status == 'COMPLETED' else expected_amount * Decimal(random.uniform(0.5, 0.9)),
                    beneficiary=beneficiary,
                    payout_amount=collected_amount * Decimal('0.95') if status == 'COMPLETED' else Decimal('0.00'),
                    payout_date=end_date + timedelta(days=2) if status == 'COMPLETED' else None,
                    status=status
                )
                cycles.append(cycle)
        
        return cycles

    def create_contributions(self, cycles, memberships):
        """Create individual contributions"""
        contributions = []
        payment_methods = ['MPESA', 'MPESA', 'MPESA', 'BANK', 'CASH']
        
        for cycle in cycles:
            chama_members = [m for m in memberships if m.chama == cycle.chama and m.status == 'ACTIVE']
            
            for membership in chama_members:
                # 85% of members contribute on time
                if random.random() < 0.85:
                    payment_date = cycle.start_date + timedelta(days=random.randint(0, 5))
                    late_payment = False
                    penalty = Decimal('0.00')
                else:
                    payment_date = cycle.end_date + timedelta(days=random.randint(1, 5))
                    late_payment = True
                    penalty = cycle.chama.late_payment_penalty
                
                payment_method = random.choice(payment_methods)
                
                contribution = Contribution.objects.create(
                    cycle=cycle,
                    membership=membership,
                    amount=cycle.chama.contribution_amount,
                    payment_method=payment_method,
                    transaction_reference=f"TXN{random.randint(1000000000, 9999999999)}",
                    mpesa_receipt_number=f"QF{random.randint(10000000, 99999999)}" if payment_method == 'MPESA' else '',
                    payment_date=timezone.make_aware(datetime.combine(payment_date, datetime.now().time())),
                    status='COMPLETED' if cycle.status == 'COMPLETED' else random.choice(['COMPLETED', 'PENDING']),
                    late_payment=late_payment,
                    penalty_amount=penalty,
                    recorded_by=cycle.chama.created_by
                )
                contributions.append(contribution)
        
        return contributions

    def create_payouts(self, cycles, memberships):
        """Create payouts for completed cycles"""
        payouts = []
        payment_methods = ['MPESA', 'MPESA', 'BANK', 'BANK']
        
        completed_cycles = [c for c in cycles if c.status == 'COMPLETED' and c.beneficiary]
        
        for cycle in completed_cycles:
            payment_method = random.choice(payment_methods)
            
            payout = Payout.objects.create(
                cycle=cycle,
                membership=cycle.beneficiary,
                amount=cycle.payout_amount,
                payment_method=payment_method,
                transaction_reference=f"PAYOUT{random.randint(1000000000, 9999999999)}",
                mpesa_receipt_number=f"QF{random.randint(10000000, 99999999)}" if payment_method == 'MPESA' else '',
                scheduled_date=cycle.payout_date,
                actual_payment_date=timezone.make_aware(
                    datetime.combine(cycle.payout_date, datetime.now().time())
                ),
                status='COMPLETED',
                approved_by=cycle.chama.created_by,
                approval_date=timezone.make_aware(
                    datetime.combine(cycle.payout_date - timedelta(days=1), datetime.now().time())
                ),
                processed_by=cycle.chama.created_by
            )
            payouts.append(payout)
        
        return payouts

    def create_loans(self, chamas, memberships, users):
        """Create loan applications"""
        loans = []
        loan_purposes = [
            'School fees for children',
            'Medical emergency',
            'Business expansion - retail shop',
            'Rent deposit for new house',
            'Wedding expenses',
            'Funeral expenses',
            'Purchase of motorcycle for boda boda business',
            'Stock purchase for M-Pesa shop',
            'Agricultural inputs - seeds and fertilizer',
            'Home improvement and repairs',
            'Starting poultry farming business',
            'Paying existing debts',
            'Starting tailoring business',
            'Equipment purchase for salon',
            'Stock for hardware shop'
        ]
        
        active_members = [m for m in memberships if m.status == 'ACTIVE']
        
        # Create 30-40 loans
        for i in range(random.randint(30, 40)):
            membership = random.choice(active_members)
            chama = membership.chama
            
            # Loan amounts typically 2-10x monthly contribution
            principal = chama.contribution_amount * Decimal(random.randint(2, 10))
            interest_rate = chama.loan_interest_rate
            repayment_months = random.choice([3, 6, 9, 12, 18])
            
            interest_amount = (principal * interest_rate / 100)
            total_amount = principal + interest_amount
            
            # Get guarantors from same chama
            potential_guarantors = [m for m in active_members if m.chama == chama and m != membership]
            guarantors = random.sample(potential_guarantors, min(2, len(potential_guarantors)))
            
            application_date = timezone.now().date() - timedelta(days=random.randint(1, 180))
            
            status_choices = ['PENDING', 'APPROVED', 'DISBURSED', 'ACTIVE', 'ACTIVE', 'COMPLETED']
            status = random.choice(status_choices)
            
            # Calculate repayment progress
            if status in ['ACTIVE', 'COMPLETED']:
                amount_paid = total_amount * Decimal(random.uniform(0.2, 1.0 if status == 'COMPLETED' else 0.8))
            else:
                amount_paid = Decimal('0.00')
            
            loan = Loan.objects.create(
                chama=chama,
                membership=membership,
                loan_number=f"LOAN/{chama.name[:3].upper()}/{i+1:04d}",
                principal_amount=principal,
                interest_rate=interest_rate,
                interest_amount=interest_amount,
                total_amount=total_amount,
                amount_paid=amount_paid,
                balance=total_amount - amount_paid,
                repayment_period_months=repayment_months,
                application_date=application_date,
                approval_date=application_date + timedelta(days=random.randint(1, 7)) if status != 'PENDING' else None,
                disbursement_date=application_date + timedelta(days=random.randint(7, 14)) if status in ['DISBURSED', 'ACTIVE', 'COMPLETED'] else None,
                expected_completion_date=application_date + timedelta(days=repayment_months * 30),
                actual_completion_date=application_date + timedelta(days=repayment_months * 30 + random.randint(-10, 10)) if status == 'COMPLETED' else None,
                status=status,
                purpose=random.choice(loan_purposes),
                guarantor_1=guarantors[0] if len(guarantors) > 0 else None,
                guarantor_2=guarantors[1] if len(guarantors) > 1 else None,
                approved_by=chama.created_by if status != 'PENDING' else None,
                rejection_reason='' if status != 'REJECTED' else 'Insufficient contribution history'
            )
            loans.append(loan)
        
        return loans

    def create_loan_repayments(self, loans, users):
        """Create loan repayment records"""
        repayments = []
        payment_methods = ['MPESA', 'MPESA', 'BANK', 'DEDUCTION']
        
        active_loans = [l for l in loans if l.status in ['ACTIVE', 'COMPLETED']]
        
        for loan in active_loans:
            # Calculate number of repayments made
            repayment_percentage = float(loan.amount_paid / loan.total_amount) if loan.total_amount > 0 else 0
            num_repayments = int(loan.repayment_period_months * repayment_percentage)
            
            monthly_payment = loan.total_amount / Decimal(loan.repayment_period_months)
            
            for month in range(num_repayments):
                # Vary payment amounts slightly
                payment_amount = monthly_payment * Decimal(random.uniform(0.9, 1.1))
                payment_date = loan.disbursement_date + timedelta(days=30 * (month + 1))
                
                repayment = LoanRepayment.objects.create(
                    loan=loan,
                    amount=payment_amount,
                    payment_method=random.choice(payment_methods),
                    transaction_reference=f"LNREP{random.randint(1000000000, 9999999999)}",
                    payment_date=timezone.make_aware(
                        datetime.combine(payment_date, datetime.now().time())
                    ),
                    status='COMPLETED',
                    recorded_by=loan.chama.created_by,
                    notes=f"Monthly repayment - Month {month + 1}"
                )
                repayments.append(repayment)
        
        return repayments

    def create_meetings(self, chamas, users):
        """Create chama meetings"""
        meetings = []
        
        for chama in chamas:
            # Create 5-10 meetings per chama
            num_meetings = random.randint(5, 10)
            
            for meeting_num in range(1, num_meetings + 1):
                # Schedule meetings in the past
                scheduled_date = timezone.now() - timedelta(days=random.randint(7, 365))
                
                status = random.choice(['COMPLETED', 'COMPLETED', 'COMPLETED', 'SCHEDULED', 'CANCELLED'])
                
                meeting = Meeting.objects.create(
                    chama=chama,
                    title=f"{chama.name} - Monthly Meeting #{meeting_num}",
                    meeting_number=meeting_num,
                    scheduled_date=scheduled_date,
                    actual_start_time=scheduled_date + timedelta(minutes=random.randint(0, 30)) if status == 'COMPLETED' else None,
                    actual_end_time=scheduled_date + timedelta(hours=2, minutes=random.randint(0, 30)) if status == 'COMPLETED' else None,
                    location=chama.meeting_location,
                    agenda=f"1. Opening and prayer\n2. Roll call and apologies\n3. Minutes of previous meeting\n"
                           f"4. Financial report\n5. Loan applications review\n6. AOB\n7. Next meeting date\n8. Closing",
                    minutes=f"Meeting held on {scheduled_date.strftime('%B %d, %Y')}. Present: Various members. "
                           f"Discussed financial status, reviewed loan applications, and planned future activities." if status == 'COMPLETED' else '',
                    status=status,
                    secretary=chama.created_by
                )
                meetings.append(meeting)
        
        return meetings

    def create_attendance(self, meetings, memberships):
        """Create meeting attendance records"""
        attendance_records = []
        
        completed_meetings = [m for m in meetings if m.status == 'COMPLETED']
        
        for meeting in completed_meetings:
            chama_members = [m for m in memberships if m.chama == meeting.chama and m.status == 'ACTIVE']
            
            for membership in chama_members:
                # 75% attendance rate on average
                if random.random() < 0.75:
                    status = 'PRESENT'
                    arrival_time = meeting.actual_start_time + timedelta(minutes=random.randint(-5, 20))
                    if arrival_time > meeting.actual_start_time + timedelta(minutes=15):
                        status = 'LATE'
                else:
                    status = random.choice(['ABSENT', 'ABSENT', 'EXCUSED'])
                    arrival_time = None
                
                attendance = MeetingAttendance.objects.create(
                    meeting=meeting,
                    membership=membership,
                    status=status,
                    arrival_time=arrival_time,
                    notes='Family emergency' if status == 'EXCUSED' else ''
                )
                attendance_records.append(attendance)
        
        return attendance_records

    def create_notifications(self, users, chamas):
        """Create notifications"""
        notifications = []
        
        notification_types = [
            ('CONTRIBUTION_REMINDER', 'Contribution Reminder', 'Your contribution of KES {amount} is due on {date}'),
            ('PAYOUT_NOTIFICATION', 'Payout Scheduled', 'Your payout of KES {amount} has been scheduled for {date}'),
            ('LOAN_APPROVAL', 'Loan Approved', 'Your loan application has been approved. Amount: KES {amount}'),
            ('MEETING_REMINDER', 'Meeting Reminder', 'Reminder: {chama} meeting on {date} at {location}'),
            ('PAYMENT_RECEIVED', 'Payment Confirmed', 'We have received your contribution of KES {amount}'),
            ('LATE_PAYMENT', 'Late Payment Notice', 'Your contribution is overdue. Please pay KES {amount} plus penalty'),
        ]
        
        for user in users[:30]:  # Create notifications for first 30 users
            user_memberships = [m for m in user.memberships.all() if m.status == 'ACTIVE']
            
            for _ in range(random.randint(3, 10)):
                notif_type, title_template, message_template = random.choice(notification_types)
                chama = random.choice(chamas)
                
                # Format notification with realistic data
                title = title_template
                message = message_template.format(
                    amount=random.randint(500, 10000),
                    date=(timezone.now() + timedelta(days=random.randint(1, 30))).strftime('%B %d, %Y'),
                    chama=chama.name,
                    location=chama.meeting_location
                )
                
                sent_date = timezone.now() - timedelta(days=random.randint(0, 30))
                status = random.choice(['SENT', 'SENT', 'READ', 'PENDING'])
                
                notification = Notification.objects.create(
                    user=user,
                    chama=chama if user_memberships else None,
                    notification_type=notif_type,
                    channel=random.choice(['SMS', 'EMAIL', 'IN_APP', 'PUSH']),
                    title=title,
                    message=message,
                    status=status,
                    sent_at=sent_date if status != 'PENDING' else None,
                    read_at=sent_date + timedelta(hours=random.randint(1, 48)) if status == 'READ' else None,
                    metadata={
                        'priority': random.choice(['high', 'normal', 'low']),
                        'category': 'financial'
                    }
                )
                notifications.append(notification)
        
        return notifications

    def create_audit_logs(self, users):
        """Create audit log entries"""
        audit_logs = []
        
        actions = [
            ('CREATE', 'Contribution'),
            ('UPDATE', 'Loan'),
            ('APPROVE', 'Loan'),
            ('PAYMENT', 'Contribution'),
            ('CREATE', 'Payout'),
            ('UPDATE', 'ChamaMembership'),
            ('LOGIN', 'User'),
            ('LOGOUT', 'User'),
            ('EXPORT', 'Report'),
        ]
        
        ip_addresses = [
            '41.90.64.0',  # Kenya Safaricom
            '105.160.0.0',  # Kenya Telkom
            '154.122.0.0',  # Kenya Airtel
            '197.232.0.0',  # Kenya various ISPs
        ]
        
        user_agents = [
            'Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        ]
        
        for user in users[:20]:  # Create logs for first 20 users
            for _ in range(random.randint(10, 30)):
                action, model_name = random.choice(actions)
                
                audit_log = AuditLog.objects.create(
                    user=user,
                    action=action,
                    model_name=model_name,
                    object_id=str(random.randint(1, 1000)),
                    changes={
                        'field': 'status',
                        'old_value': 'PENDING',
                        'new_value': 'COMPLETED'
                    } if action == 'UPDATE' else {},
                    ip_address=random.choice(ip_addresses),
                    user_agent=random.choice(user_agents),
                    timestamp=timezone.now() - timedelta(days=random.randint(0, 90))
                )
                audit_logs.append(audit_log)
        
        return audit_logs

    def print_summary(self):
        """Print database summary"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('DATABASE SUMMARY'))
        self.stdout.write('='*60)
        
        summary_data = [
            ('Users', User.objects.count()),
            ('Chamas', Chama.objects.count()),
            ('Active Chamas', Chama.objects.filter(status='ACTIVE').count()),
            ('Memberships', ChamaMembership.objects.count()),
            ('Active Members', ChamaMembership.objects.filter(status='ACTIVE').count()),
            ('Contribution Cycles', ContributionCycle.objects.count()),
            ('Completed Cycles', ContributionCycle.objects.filter(status='COMPLETED').count()),
            ('Total Contributions', Contribution.objects.count()),
            ('Completed Contributions', Contribution.objects.filter(status='COMPLETED').count()),
            ('Total Contributions Amount', f"KES {Contribution.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0:,.2f}"),
            ('Payouts', Payout.objects.count()),
            ('Completed Payouts', Payout.objects.filter(status='COMPLETED').count()),
            ('Loans', Loan.objects.count()),
            ('Active Loans', Loan.objects.filter(status='ACTIVE').count()),
            ('Loan Repayments', LoanRepayment.objects.count()),
            ('Meetings', Meeting.objects.count()),
            ('Completed Meetings', Meeting.objects.filter(status='COMPLETED').count()),
            ('Attendance Records', MeetingAttendance.objects.count()),
            ('Notifications', Notification.objects.count()),
            ('Audit Logs', AuditLog.objects.count()),
        ]
        
        for label, value in summary_data:
            self.stdout.write(f'{label:.<40} {str(value):>15}')
        
        self.stdout.write('='*60)
        
        # Print sample login credentials
        self.stdout.write('\n' + self.style.WARNING('SAMPLE LOGIN CREDENTIALS'))
        self.stdout.write('='*60)
        self.stdout.write('Admin User:')
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: ChamaAdmin@2025')
        self.stdout.write('  Email: admin@chamasmart.co.ke')
        self.stdout.write('\nRegular Users:')
        self.stdout.write('  Password for all users: Chama@2025')
        self.stdout.write('  Usernames: Check User model in admin panel')
        self.stdout.write('='*60)
        
        # Print sample chamas
        self.stdout.write('\n' + self.style.WARNING('SAMPLE CHAMAS CREATED'))
        self.stdout.write('='*60)
        for chama in Chama.objects.all()[:5]:
            self.stdout.write(f'\n{chama.name}')
            self.stdout.write(f'  Members: {chama.total_members}')
            self.stdout.write(f'  Contribution: KES {chama.contribution_amount:,.2f} ({chama.contribution_frequency})')
            try:
                total_contrib = chama.total_contributions
                self.stdout.write(f'  Total Contributions: KES {total_contrib:,.2f}')
            except Exception as e:
                self.stdout.write(f'  Total Contributions: KES 0.00')
            self.stdout.write(f'  Status: {chama.status}')
        self.stdout.write('='*60 + '\n')


# Additional utility functions for data generation
from django.db.models import Sum

def generate_kenyan_phone():
    """Generate realistic Kenyan phone number"""
    prefixes = ['710', '711', '712', '720', '721', '722', '723', '724', '725', 
                '726', '727', '728', '729', '740', '741', '742', '743', '745', 
                '746', '748', '757', '758', '759', '768', '769', '790', '791', 
                '792', '793', '794', '795', '796', '797', '798', '799']
    return f"+254{random.choice(prefixes)}{random.randint(100000, 999999)}"


def generate_mpesa_transaction():
    """Generate realistic M-Pesa transaction reference"""
    return f"QF{random.randint(10000000, 99999999)}"


def generate_kenyan_id():
    """Generate realistic Kenyan ID number"""
    return f"{random.randint(10000000, 39999999)}"