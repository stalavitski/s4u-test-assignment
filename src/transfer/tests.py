from decimal import Decimal

from django.test import TestCase

from account.models import Account
from transfer.models import InsufficientBalance, InvalidAmount, Transfer


class TransferTest(TestCase):
    fixtures = [
        '0001_customer.json',
        '0001_account.json'
    ]

    def setUp(self):
        super(TransferTest, self).setUp()

        self.account1 = Account.objects.get(pk=1)
        self.account2 = Account.objects.get(pk=2)

    # do_transfer tests
    def test__do_transfer__success__for_valid_accounts(self):
        Transfer.do_transfer(self.account1, self.account2, Decimal(100))

        self.account1.refresh_from_db()
        self.account2.refresh_from_db()

        self.assertEqual(self.account1.balance, 900)
        self.assertEqual(self.account2.balance, 1100)
        self.assertTrue(Transfer.objects.filter(
            from_account=self.account1,
            to_account=self.account2,
            amount=100,
        ).exists())

    def test__do_transfer__raises_exception__for_zero_amount(self):
        with self.assertRaises(InvalidAmount):
            Transfer.do_transfer(self.account1, self.account2, Decimal(0))

    def test__do_transfer__raises_exception__for_negative_amount(self):
        with self.assertRaises(InvalidAmount):
            Transfer.do_transfer(self.account1, self.account2, Decimal(-0.01))

    def test__do_transfer__raises_exception__for_insufficient_balance(self):
        with self.assertRaises(InsufficientBalance):
            Transfer.do_transfer(self.account1, self.account2, Decimal(1001))
