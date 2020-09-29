from decimal import Decimal

from django.db import models, transaction
from django.db.models import F

from account.models import Account


class InsufficientBalance(Exception):
    pass


class InvalidAccount(Exception):
    pass


class InvalidAmount(Exception):
    pass


class Transfer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    from_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_in')
    to_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_out')
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    @staticmethod
    @transaction.atomic
    def do_transfer(from_account: Account, to_account: Account, amount: Decimal) -> 'Transfer':
        """
        Transfer the amount of money from one account to another.

        :param from_account: Sender account.
        :param to_account: Recipient account.
        :param amount: The amount of money for transfer.
        :return: An object containing information about the transfer.
        """
        if amount <= 0:
            raise InvalidAmount('The transfer amount should be greater than 0.')

        updated = Account.objects.filter(
            balance__gte=amount,
            pk=from_account.pk
        ).update(balance=F('balance') - amount)

        if not updated:
            raise InsufficientBalance(
                'The balance on the sender account should be greater than or equal to the amount.'
            )

        updated = Account.objects.filter(pk=to_account.pk).update(balance=F('balance') + amount)

        if not updated:
            raise InvalidAccount(
                'Recipient account has been removed before transfer has been accepted.'
            )

        return Transfer.objects.create(
            from_account=from_account,
            to_account=to_account,
            amount=amount
        )


'''
Account / transfer schema evolution

- To correctly store information about transfers, I'd prefer to create choices field in the Transfer
model that will indicated options like (internal, inbound, outbound, withdraw) depends on transfer type.
- Account should be modified to store data about inbound, outbound and withdraw operations. 
Currently fields in Account schema are not valid for external connections. 
We can make additional Model like ExternalAccount (for example), that will store data about external account.
This model must store data like bank_name/atm_address/card_number anything that is acceptable and available
in the banking world.
Make a field in the Account model referred to the ExternalAccount.
Make other fields not required if field that mention above is not empty. 
Create accounts for each external operation with ExternalAccount reference.
'''