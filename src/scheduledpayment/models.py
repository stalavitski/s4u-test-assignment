import logging
from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext as _

from transfer.models import InsufficientBalance, Transfer

logger = logging.getLogger(__name__)


class ScheduledPayment(models.Model):
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField(auto_now_add=True)
    day = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])
    from_account = models.ForeignKey('account.Account', models.CASCADE, related_name='scheduled_payments_in')
    to_account = models.ForeignKey('account.Account', models.CASCADE, related_name='scheduled_payments_out')

    def clean(self) -> None:
        if self.from_account == self.to_account:
            raise ValidationError(
                _('Accounts should be different from each other (from_account, to_account).'),
                code='self_transfer'
            )

    @staticmethod
    def get_scheduled_payments(payment_date: date = None) -> 'QuerySet[ScheduledPayment]':
        """
        Get scheduled payments according to the payment_date.

        :param payment_date: (optional) Date to run against scheduled payments. Defaults to today.
        :return: Scheduled payments according to the payment_date.
        """
        payment_date = payment_date if payment_date else date.today()
        first_day, last_day = monthrange(payment_date.year, payment_date.month)

        # If payment_date is the last day of the month, process payments where day >= payment_date.day
        if last_day == payment_date.day:
            return ScheduledPayment.objects.filter(day__gte=payment_date.day)
        else:
            return ScheduledPayment.objects.filter(day=payment_date.day)


class Payment(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    reason = models.CharField(max_length=255, null=True)
    scheduled_payment = models.ForeignKey(ScheduledPayment, models.CASCADE, related_name='payments')
    transfer = models.OneToOneField(Transfer, models.CASCADE, null=True, related_name='payment')

    def clean(self) -> None:
        if not self.is_successful and not self.reason:
            raise ValidationError(
                _('If the payment is not successful, reason is required.'),
                code='missing_reason'
            )

        if not self.is_successful and self.transfer:
            raise ValidationError(
                _('If the payment is not successful, transfer must be empty.'),
                code='success_reason'
            )

        if self.is_successful and self.reason:
            raise ValidationError(
                _('If the payment is successful, reason must be empty.'),
                code='success_reason'
            )

        if self.is_successful and not self.transfer:
            raise ValidationError(
                _('If the payment is successful, transfer is required.'),
                code='success_reason'
            )

    @staticmethod
    def make_payment(scheduled_payment: ScheduledPayment) -> 'Payment':
        """
        Make payment based on the ScheduledPayment data.

        :param scheduled_payment: An object containing information about the scheduled payment.
        :return: An object containing information about payment attempt.
        """
        try:
            transfer = Transfer.do_transfer(
                scheduled_payment.from_account,
                scheduled_payment.to_account,
                scheduled_payment.amount
            )
        except InsufficientBalance as e:
            logger.error(e)
            return Payment.objects.create(
                is_successful=False,
                reason='Insufficient funds.',
                scheduled_payment=scheduled_payment
            )
        else:
            payment = Payment.objects.create(scheduled_payment=scheduled_payment, transfer=transfer)
            logger.info('Payment #{} has been successfully transferred.'.format(payment.id))
            return payment
