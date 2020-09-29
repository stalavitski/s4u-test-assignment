from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from account.models import Account
from scheduledpayment.models import Payment, ScheduledPayment
from transfer.models import Transfer


class PaymentTest(TestCase):
    fixtures = [
        '0001_customer.json',
        '0001_account.json',
        '0001_scheduled_payments.json',
        '0001_transfers.json'
    ]

    def setUp(self):
        super().setUp()

        self.account1 = Account.objects.get(pk=1)
        self.account2 = Account.objects.get(pk=2)
        self.scheduled_payment = ScheduledPayment.objects.get(pk=1)
        self.transfer = Transfer.objects.get(pk=1)

    # clean tests
    def test__clean__raise_exception__when_payment_failed_and_reason_is_not_specified(self):
        with self.assertRaises(ValidationError) as context:
            payment = Payment(
                is_successful=False,
                reason=None,
                scheduled_payment=self.scheduled_payment
            )
            payment.clean()

        self.assertIn('If the payment is not successful, reason is required.', context.exception)

    def test__clean__raise_exception__when_payment_failed_and_transfer_is_specified(self):
        with self.assertRaises(ValidationError) as context:
            payment = Payment(
                is_successful=False,
                reason='test',
                scheduled_payment=self.scheduled_payment,
                transfer=self.transfer
            )
            payment.clean()

        self.assertIn('If the payment is not successful, transfer must be empty.', context.exception)

    def test__clean__raise_exception__when_payment_successful_and_reason_is_specified(self):
        with self.assertRaises(ValidationError) as context:
            payment = Payment(
                is_successful=True,
                reason='test',
                scheduled_payment=self.scheduled_payment,
                transfer=self.transfer
            )
            payment.clean()

        self.assertIn('If the payment is successful, reason must be empty.', context.exception)

    def test__clean__raise_exception__when_payment_successful_and_transfer_is_not_specified(self):
        with self.assertRaises(ValidationError) as context:
            payment = Payment(
                is_successful=True,
                scheduled_payment=self.scheduled_payment
            )
            payment.clean()

        self.assertIn('If the payment is successful, transfer is required.', context.exception)

    def test__clean__doesnt_raise_exception__when_payment_is_failed_and_valid(self):
        payment = Payment(
            is_successful=False,
            reason='test',
            scheduled_payment=self.scheduled_payment
        )
        payment.clean()
        payment.save()
        self.assertIsNotNone(payment.pk)

    def test__clean__doesnt_raise_exception__when_payment_is_successful_and_valid(self):
        payment = Payment(
            is_successful=True,
            scheduled_payment=self.scheduled_payment,
            transfer=self.transfer
        )
        payment.clean()
        payment.save()
        self.assertIsNotNone(payment.pk)

    # make_payment tests
    def test__make_payment__success__for_valid_accounts(self):
        payment = Payment.make_payment(self.scheduled_payment)

        self.assertTrue(payment.is_successful)

    def test__make_payment__failure__for_insufficient_funds(self):
        self.account1.balance = self.scheduled_payment.amount - Decimal('0.01')
        self.account1.save()

        payment = Payment.make_payment(self.scheduled_payment)

        self.assertFalse(payment.is_successful)
        self.assertEqual(payment.reason, 'Insufficient funds.')


class ScheduledPaymentTestCase(TestCase):
    fixtures = [
        '0001_customer.json',
        '0001_account.json',
        '0001_scheduled_payments.json'
    ]

    def setUp(self):
        super().setUp()

        self.account1 = Account.objects.get(pk=1)
        self.account2 = Account.objects.get(pk=2)
        self.scheduled_payment1 = ScheduledPayment.objects.get(pk=1)
        self.scheduled_payment2 = ScheduledPayment.objects.get(pk=2)

    # clean tests
    def test__clean__raise_exception__when_accounts_are_the_same(self):
        with self.assertRaises(ValidationError):
            scheduled_payment = ScheduledPayment(
                amount=Decimal('10'),
                day=1,
                from_account=self.account1,
                to_account=self.account1
            )
            scheduled_payment.clean()

    def test__clean__doesnt_raise_exception__when_accounts_are_different(self):
        scheduled_payment = ScheduledPayment(
            amount=Decimal('10'),
            day=1,
            from_account=self.account1,
            to_account=self.account2
        )
        scheduled_payment.clean()
        scheduled_payment.save()
        self.assertIsNotNone(scheduled_payment.pk)

    # get_scheduled_payments tests
    def test__get_scheduled_payments__return_payments__if_scheduled_for_today(self):
        today_date = date.today()
        self.scheduled_payment1.day = today_date.day
        self.scheduled_payment1.save()
        self.scheduled_payment2.day = today_date.day
        self.scheduled_payment2.save()

        scheduled_payments = ScheduledPayment.get_scheduled_payments()

        self.assertEqual(scheduled_payments.count(), 2)

    def test__get_scheduled_payments__return_payments__if_last_day(self):
        short_month_date = date(2020, 2, 29)
        self.scheduled_payment1.day = 29
        self.scheduled_payment1.save()
        self.scheduled_payment2.day = 31
        self.scheduled_payment2.save()

        scheduled_payments = ScheduledPayment.get_scheduled_payments(short_month_date)

        self.assertEqual(scheduled_payments.count(), 2)

    def test__get_scheduled_payments__doesnt_return_payments__if_nothing_scheduled(self):
        first_day_date = date(2020, 9, 1)
        self.scheduled_payment1.day = 2
        self.scheduled_payment1.save()
        self.scheduled_payment2.day = 5
        self.scheduled_payment2.save()

        scheduled_payments = ScheduledPayment.get_scheduled_payments(first_day_date)

        self.assertEqual(scheduled_payments.count(), 0)
